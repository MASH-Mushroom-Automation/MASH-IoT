"""
MASH IoT Gateway - OTA Update Manager

Checks GitHub Releases for new versions, manages downloads, and orchestrates
the update process with A/B rollback support.

Uses unauthenticated GitHub API (60 requests/hour limit).
"""

import os
import json
import re
import logging
import subprocess
import tempfile
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# GitHub repository configuration
GITHUB_OWNER = "MASH-Mushroom-Automation"
GITHUB_REPO = "MASH-IoT"
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"

# Paths
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_UPDATE_STATE_FILE = os.path.join(_PROJECT_ROOT, 'update_state.json')
_OTA_SCRIPT = os.path.join(_PROJECT_ROOT, '..', 'scripts', 'ota_update.sh')

# Cache duration for update checks (1 hour)
CHECK_INTERVAL_SECONDS = 3600

# In-memory cache
_last_check_result = None
_last_check_time = None


def _parse_version(version_str):
    """Parse version string (e.g. '2.3.0' or 'v2.3.0') into comparable tuple."""
    try:
        cleaned = version_str.lstrip('v')
        return tuple(int(x) for x in cleaned.split('.'))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def is_version_newer(remote_version, local_version):
    """Check if remote version is newer than local version."""
    return _parse_version(remote_version) > _parse_version(local_version)


def _parse_priority_from_body(body):
    """
    Extract priority level from release body text.
    Looks for 'Priority: high|medium|low' line in the changelog content.
    """
    if not body:
        return "medium"

    match = re.search(r'Priority:\s*(high|medium|low)', body, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return "medium"


def get_update_state():
    """Read the update state from disk."""
    default_state = {
        "current_version": None,
        "last_check": None,
        "last_update": None,
        "update_status": "stable",
        "backup_version": None,
        "unstable_versions": [],
        "update_in_progress": False,
    }

    try:
        if os.path.exists(_UPDATE_STATE_FILE):
            with open(_UPDATE_STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in default_state.items():
                    if key not in state:
                        state[key] = value
                return state
    except Exception as e:
        logger.error(f"[OTA] Failed to read update state: {e}")

    return default_state


def save_update_state(state):
    """Write the update state to disk."""
    try:
        with open(_UPDATE_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"[OTA] Failed to save update state: {e}")
        return False


def check_for_update(force=False):
    """
    Check GitHub Releases API for a newer version.

    Args:
        force: If True, bypass the cache and check immediately.

    Returns:
        dict with update info, or None if no update available.
        {
            'available': True/False,
            'version': '2.4.0',
            'name': 'Release Name',
            'priority': 'high|medium|low',
            'download_url': 'https://...',
            'changelog': 'Release body text',
            'published_at': '2026-02-11T...',
        }
    """
    global _last_check_result, _last_check_time

    # Return cached result if within interval
    if not force and _last_check_time and _last_check_result:
        elapsed = (datetime.now() - _last_check_time).total_seconds()
        if elapsed < CHECK_INTERVAL_SECONDS:
            logger.debug(f"[OTA] Using cached check result ({int(elapsed)}s old)")
            return _last_check_result

    try:
        import urllib.request
        import urllib.error
        import base64

        from app.core.version import VERSION

        # Load GitHub credentials from environment
        github_username = os.getenv('GITHUB_USERNAME')
        github_token = os.getenv('GITHUB_TOKEN')

        url = f"{GITHUB_API_BASE}/releases/latest"
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/vnd.github.v3+json')
        req.add_header('User-Agent', f'MASH-IoT-Gateway/{VERSION}')

        # Add authentication for private repos
        if github_username and github_token:
            credentials = f"{github_username}:{github_token}"
            encoded = base64.b64encode(credentials.encode()).decode()
            req.add_header('Authorization', f'Basic {encoded}')
            logger.debug("[OTA] Using authenticated GitHub API request")
        else:
            logger.warning("[OTA] No GitHub credentials found in .env, using unauthenticated request")

        logger.info(f"[OTA] Checking for updates at {url}")

        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))

        tag_name = data.get('tag_name', '')
        remote_version = tag_name.lstrip('v')
        release_name = data.get('name', '')
        body = data.get('body', '')
        published_at = data.get('published_at', '')

        # Find the rpi_gateway tarball in release assets
        download_url = None
        for asset in data.get('assets', []):
            asset_name = asset.get('name', '')
            if 'rpi_gateway' in asset_name and asset_name.endswith('.tar.gz'):
                download_url = asset.get('browser_download_url')
                break

        # Check if this version is already flagged as unstable
        state = get_update_state()
        unstable = state.get('unstable_versions', [])
        if remote_version in unstable:
            logger.info(f"[OTA] Version {remote_version} was previously flagged as unstable, skipping")
            result = {'available': False, 'reason': 'flagged_unstable', 'version': remote_version}
            _last_check_result = result
            _last_check_time = datetime.now()
            return result

        # Compare versions
        if not is_version_newer(remote_version, VERSION):
            logger.info(f"[OTA] Already on latest version ({VERSION})")
            result = {'available': False, 'reason': 'up_to_date', 'version': VERSION}
            _last_check_result = result
            _last_check_time = datetime.now()

            # Update last check time in state
            state['last_check'] = datetime.now().isoformat()
            save_update_state(state)

            return result

        # New version available
        priority = _parse_priority_from_body(body)

        result = {
            'available': True,
            'version': remote_version,
            'name': release_name,
            'priority': priority,
            'download_url': download_url,
            'changelog': body,
            'published_at': published_at,
        }

        logger.info(f"[OTA] Update available: v{remote_version} ({release_name}) [priority: {priority}]")

        _last_check_result = result
        _last_check_time = datetime.now()

        # Update last check time in state
        state['last_check'] = datetime.now().isoformat()
        save_update_state(state)

        return result

    except urllib.error.HTTPError as e:
        logger.error(f"[OTA] GitHub API error: {e.code} {e.reason}")
        return {'available': False, 'reason': 'api_error', 'error': str(e)}

    except urllib.error.URLError as e:
        logger.error(f"[OTA] Network error checking for updates: {e.reason}")
        return {'available': False, 'reason': 'network_error', 'error': str(e.reason)}

    except Exception as e:
        logger.error(f"[OTA] Unexpected error checking for updates: {e}")
        return {'available': False, 'reason': 'error', 'error': str(e)}


def download_update(download_url):
    """
    Download a release tarball to a temporary directory.

    Args:
        download_url: URL of the .tar.gz asset to download.

    Returns:
        Path to the downloaded file, or None on failure.
    """
    if not download_url:
        logger.error("[OTA] No download URL provided")
        return None

    try:
        import urllib.request
        import base64

        from app.core.version import VERSION

        # Load GitHub credentials
        github_username = os.getenv('GITHUB_USERNAME')
        github_token = os.getenv('GITHUB_TOKEN')

        # Create temp directory for download
        temp_dir = tempfile.mkdtemp(prefix='mash_update_')
        filename = os.path.basename(download_url)
        filepath = os.path.join(temp_dir, filename)

        logger.info(f"[OTA] Downloading update from {download_url}")
        logger.info(f"[OTA] Saving to {filepath}")

        req = urllib.request.Request(download_url)
        req.add_header('User-Agent', f'MASH-IoT-Gateway/{VERSION}')
        req.add_header('Accept', 'application/octet-stream')

        # Add authentication for private repo assets
        if github_username and github_token:
            credentials = f"{github_username}:{github_token}"
            encoded = base64.b64encode(credentials.encode()).decode()
            req.add_header('Authorization', f'Basic {encoded}')

        with urllib.request.urlopen(req, timeout=120) as response:
            with open(filepath, 'wb') as f:
                # Read in chunks to avoid memory issues
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)

        file_size = os.path.getsize(filepath)
        logger.info(f"[OTA] Download complete: {filename} ({file_size} bytes)")

        return filepath

    except Exception as e:
        logger.error(f"[OTA] Download failed: {e}")
        return None


def install_update(tarball_path, target_version):
    """
    Execute the OTA update script with the downloaded tarball.
    This runs ota_update.sh which handles backup, extraction, and health check.

    Args:
        tarball_path: Path to the downloaded .tar.gz file.
        target_version: Version string being installed.

    Returns:
        dict with 'success' bool and 'message' string.
    """
    state = get_update_state()

    # Prevent concurrent updates
    if state.get('update_in_progress'):
        return {'success': False, 'message': 'An update is already in progress'}

    # Mark update as in progress
    state['update_in_progress'] = True
    save_update_state(state)

    try:
        if not os.path.isfile(_OTA_SCRIPT):
            raise FileNotFoundError(f"OTA script not found: {_OTA_SCRIPT}")

        if not os.path.isfile(tarball_path):
            raise FileNotFoundError(f"Tarball not found: {tarball_path}")

        logger.info(f"[OTA] Starting update to v{target_version}")
        logger.info(f"[OTA] Running: bash {_OTA_SCRIPT} {tarball_path} {target_version}")

        # Run the OTA script
        result = subprocess.run(
            ['bash', _OTA_SCRIPT, tarball_path, target_version],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        # Update state based on result
        state['update_in_progress'] = False

        if result.returncode == 0:
            state['current_version'] = target_version
            state['last_update'] = datetime.now().isoformat()
            state['update_status'] = 'stable'
            save_update_state(state)

            logger.info(f"[OTA] Update to v{target_version} completed successfully")
            return {
                'success': True,
                'message': f'Updated to v{target_version} successfully',
                'output': result.stdout,
            }
        else:
            # Update failed -- script should have already rolled back
            state['update_status'] = 'rolled_back'
            unstable = state.get('unstable_versions', [])
            if target_version not in unstable:
                unstable.append(target_version)
            state['unstable_versions'] = unstable
            save_update_state(state)

            logger.error(f"[OTA] Update failed, rolled back. stderr: {result.stderr}")
            return {
                'success': False,
                'message': f'Update to v{target_version} failed and was rolled back',
                'output': result.stdout,
                'error': result.stderr,
            }

    except subprocess.TimeoutExpired:
        state['update_in_progress'] = False
        save_update_state(state)
        logger.error("[OTA] Update script timed out after 5 minutes")
        return {'success': False, 'message': 'Update timed out after 5 minutes'}

    except Exception as e:
        state['update_in_progress'] = False
        save_update_state(state)
        logger.error(f"[OTA] Update error: {e}")
        return {'success': False, 'message': str(e)}


def clear_unstable_flag(version):
    """Remove a version from the unstable list (allow re-trying an update)."""
    state = get_update_state()
    unstable = state.get('unstable_versions', [])
    if version in unstable:
        unstable.remove(version)
        state['unstable_versions'] = unstable
        save_update_state(state)
        logger.info(f"[OTA] Cleared unstable flag for v{version}")
        return True
    return False

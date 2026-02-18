"""
MASH IoT Gateway - Version Constants

Semantic Versioning: MAJOR.MINOR.PATCH
- MAJOR: Breaking changes (API changes, serial protocol changes)
- MINOR: New features (backward compatible)
- PATCH: Bug fixes, small improvements

Last updated: 2026-02-11
"""

import os

# Version Components
MAJOR = 2
MINOR = 7
PATCH = 0

# Formatted Versions
VERSION = f"{MAJOR}.{MINOR}.{PATCH}"
FULL_VERSION = f"v{VERSION}"

# Release Info
RELEASE_DATE = "2026-02-18"
RELEASE_NAME = "Analytics API Endpoints"

# API Compatibility
MIN_MOBILE_APP_VERSION = "1.0.0"
MIN_ARDUINO_VERSION = "1.0.0"
ARDUINO_SERIAL_PROTOCOL_VERSION = "1.0"

# Feature Flags
FEATURES = {
    'wifi_manager': True,            # - NetworkManager-based provisioning
    'ml_models': True,               # - Isolation Forest + Decision Tree
    'firebase_sync': True,            # - Realtime DB + Admin SDK (client-side listener)
    'backend_api_sync': True,        # - REST API client with JWT
    'mdns_discovery': False,          # - Local network discovery
    'offline_first_db': True,        # - SQLite with sync queue
    'web_dashboard': True,           # - Flask Blueprint web UI
    'version_api': True,             # - Version endpoint for frontend
    'manual_controls': True,         # - Override automation
    'ota_updates': True,             # - GitHub Release OTA updates with A/B rollback
    'sensor_warmup': True,           # - Initial calibration period
    'smart_humidifier': False,        # - Predictive cycle manager
    'screen_management': True,       # - HDMI power control
    'mqtt_fallback': False,          # - Partial (client exists, not integrated)
    'systemd_service': True,         # - Scripts available, manual setup
    'chromium_kiosk': True,          # - Scripts available, manual setup
    'advanced_recovery': True,       # - I2C recovery + hardware WDT
    'per_version_changelogs': True,  # - File-based changelogs with on-demand API
    'stateful_alerts': True,         # - Active alerts with acknowledgement
    'qr_code_pairing': True,         # - QR code device connection for mobile app
}

# Hardware Requirements
MIN_PYTHON_VERSION = "3.9"
SUPPORTED_PLATFORMS = ["linux", "darwin"]  # RPi (Linux) and macOS for testing

# Serial Protocol
SERIAL_BAUD_RATE = 9600
SERIAL_PROTOCOL = "json"
SENSOR_READ_INTERVAL = 5  # seconds

# ---------------------------------------------------------------------------
# Changelog Registry
# ---------------------------------------------------------------------------
# Compact metadata for each release. Changelog content is stored in separate
# files under changelogs/vX.Y.Z.md -- loaded on demand to save memory.
#
# Priority levels (for future OTA update notifications):
#   high   - Required update, user cannot skip
#   medium - Recommended update, can be postponed (reminded after 24h)
#   low    - Optional update, can be skipped
# ---------------------------------------------------------------------------

CHANGELOG_REGISTRY = [
    {"version": "2.7.0", "date": "2026-02-18", "name": "Analytics API Endpoints", "priority": "medium"},
    {"version": "2.6.0", "date": "2026-02-17", "name": "QR Code Device Pairing", "priority": "medium"},
    {"version": "2.5.0", "date": "2026-02-11", "name": "Stateful Alerts & Notifications", "priority": "medium"},
    {"version": "2.4.0", "date": "2026-02-11", "name": "Multi-Device Sync & OTA UI", "priority": "medium"},
    {"version": "2.3.2", "date": "2026-02-11", "name": "Settings UI Overhaul", "priority": "medium"},
    {"version": "2.3.1", "date": "2026-02-11", "name": "OTA & Asset System", "priority": "medium"},
    {"version": "2.3.0", "date": "2026-02-11", "name": "Version Management", "priority": "medium"},
    {"version": "2.2.2", "date": "2026-02-11", "name": "I2C Recovery", "priority": "high"},
    {"version": "2.2.1", "date": "2026-02-11", "name": "Heartbeat Stability", "priority": "medium"},
    {"version": "2.2.0", "date": "2026-02-11", "name": "Smart Retry Logic", "priority": "medium"},
    {"version": "2.1.5", "date": "2026-02-10", "name": "Firebase Sync Improvements", "priority": "medium"},
    {"version": "2.1.4", "date": "2026-02-10", "name": "Configuration Management Improvements", "priority": "low"},
    {"version": "2.1.3", "date": "2026-02-10", "name": "Changelog Modal and Documentation", "priority": "low"},
    {"version": "2.1.2", "date": "2026-02-10", "name": "Firebase Fixes and System Controls", "priority": "medium"},
    {"version": "2.1.1", "date": "2026-02-10", "name": "Firebase Config Fix and Sync Status", "priority": "medium"},
    {"version": "2.1.0", "date": "2026-02-10", "name": "Firebase Realtime Database Integration", "priority": "medium"},
    {"version": "2.0.0", "date": "2026-02-09", "name": "Complete IoT Gateway", "priority": "high"},
    {"version": "1.1.0", "date": "2026-02-05", "name": "Feature Enhancements", "priority": "medium"},
    {"version": "1.0.0", "date": "2026-02-03", "name": "Initial Release", "priority": "high"},
]

# Path to changelog files directory
_CHANGELOGS_DIR = os.path.join(os.path.dirname(__file__), 'changelogs')


def get_version_info():
    """Get version information as dictionary."""
    return {
        'version': VERSION,
        'major': MAJOR,
        'minor': MINOR,
        'patch': PATCH,
        'release_date': RELEASE_DATE,
        'release_name': RELEASE_NAME,
        'features': FEATURES,
    }


def get_version_headers():
    """Get version headers for API requests."""
    return {
        'X-Device-Version': VERSION,
        'X-Device-Type': 'rpi-gateway',
        'X-Serial-Protocol': ARDUINO_SERIAL_PROTOCOL_VERSION,
    }


def is_mobile_compatible(mobile_version: str) -> bool:
    """Check if mobile app version is compatible with this gateway."""
    return _is_version_compatible(mobile_version, MIN_MOBILE_APP_VERSION)


def is_arduino_compatible(arduino_version: str) -> bool:
    """Check if Arduino firmware version is compatible."""
    return _is_version_compatible(arduino_version, MIN_ARDUINO_VERSION)


def _is_version_compatible(current: str, minimum: str) -> bool:
    """Check if current version meets minimum requirement."""
    try:
        current_parts = [int(x) for x in current.split('.')]
        min_parts = [int(x) for x in minimum.split('.')]

        # Check MAJOR version (must match)
        if current_parts[0] != min_parts[0]:
            return False

        # Check MINOR version (current must be >= minimum)
        if len(current_parts) > 1 and len(min_parts) > 1:
            if current_parts[1] < min_parts[1]:
                return False

        return True
    except (ValueError, IndexError):
        return False


def _parse_version(version_str: str):
    """Parse version string into comparable tuple."""
    try:
        return tuple(int(x) for x in version_str.split('.'))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def get_changelog_registry():
    """Get the lightweight changelog registry (metadata only, no content)."""
    return CHANGELOG_REGISTRY


def get_changelog(version=None):
    """
    Get changelog content for a specific version.

    Args:
        version: Version string (e.g. '2.2.2'). Defaults to current version.

    Returns:
        dict with version metadata and content, or None if not found.
    """
    if version is None:
        version = VERSION

    # Find entry in registry
    entry = None
    for item in CHANGELOG_REGISTRY:
        if item['version'] == version:
            entry = item
            break

    if entry is None:
        return None

    # Read changelog file
    content = _read_changelog_file(version)

    return {
        'version': entry['version'],
        'date': entry['date'],
        'name': entry['name'],
        'priority': entry.get('priority', 'low'),
        'content': content,
    }


def get_changelogs_since(since_version: str):
    """
    Get all changelogs newer than the given version.
    Used for OTA update popups to show "what's new since your version".

    Args:
        since_version: Version string to compare against (exclusive).

    Returns:
        List of changelog dicts (newest first), each with content.
    """
    since_tuple = _parse_version(since_version)
    results = []

    for entry in CHANGELOG_REGISTRY:
        entry_tuple = _parse_version(entry['version'])
        if entry_tuple > since_tuple:
            content = _read_changelog_file(entry['version'])
            results.append({
                'version': entry['version'],
                'date': entry['date'],
                'name': entry['name'],
                'priority': entry.get('priority', 'low'),
                'content': content,
            })

    return results


def get_changelogs(limit=None):
    """
    Get the most recent changelogs with content.

    Args:
        limit: Maximum number of changelogs to return. None for all.

    Returns:
        List of changelog dicts (newest first), each with content.
    """
    entries = CHANGELOG_REGISTRY[:limit] if limit else CHANGELOG_REGISTRY
    results = []

    for entry in entries:
        content = _read_changelog_file(entry['version'])
        results.append({
            'version': entry['version'],
            'date': entry['date'],
            'name': entry['name'],
            'priority': entry.get('priority', 'low'),
            'content': content,
        })

    return results


def _read_changelog_file(version: str) -> str:
    """Read a changelog file from the changelogs directory."""
    filepath = os.path.join(_CHANGELOGS_DIR, f'v{version}.md')
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return f"Changelog for v{version} not available."
    except Exception:
        return f"Error reading changelog for v{version}."


# Backward compatibility: CHANGELOG as a lazy-loaded string
# Concatenates all changelog files into one string (like the old format)
_changelog_cache = None

def _get_full_changelog():
    """Build full changelog string from all per-version files (backward compat)."""
    global _changelog_cache
    if _changelog_cache is not None:
        return _changelog_cache

    parts = []
    for entry in CHANGELOG_REGISTRY:
        content = _read_changelog_file(entry['version'])
        parts.append(content)

    _changelog_cache = '\n\n---\n\n'.join(parts)
    return _changelog_cache

# Lazy-evaluated on first access
CHANGELOG = _get_full_changelog


if __name__ == "__main__":
    print(f"MASH IoT Gateway {FULL_VERSION}")
    print(f"Release Date: {RELEASE_DATE}")
    print(f"Release Name: {RELEASE_NAME}")
    print("\nFeatures:")
    for feature, enabled in FEATURES.items():
        status = "ON" if enabled else "OFF"
        print(f"  [{status}] {feature}")
    print(f"\nCompatibility:")
    print(f"  Min Mobile App: {MIN_MOBILE_APP_VERSION}")
    print(f"  Min Arduino: {MIN_ARDUINO_VERSION}")
    print(f"  Serial Protocol: {ARDUINO_SERIAL_PROTOCOL_VERSION}")
    print(f"\nChangelog Registry: {len(CHANGELOG_REGISTRY)} versions")
    for entry in CHANGELOG_REGISTRY[:3]:
        print(f"  v{entry['version']} ({entry['date']}) - {entry['name']} [{entry['priority']}]")
    if len(CHANGELOG_REGISTRY) > 3:
        print(f"  ... and {len(CHANGELOG_REGISTRY) - 3} more")

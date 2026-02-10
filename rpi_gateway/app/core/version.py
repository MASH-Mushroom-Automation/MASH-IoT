"""
MASH IoT Gateway - Version Constants

Semantic Versioning: MAJOR.MINOR.PATCH
- MAJOR: Breaking changes (API changes, serial protocol changes)
- MINOR: New features (backward compatible)
- PATCH: Bug fixes, small improvements

Last updated: 2026-02-11
"""

# Version Components
MAJOR = 2
MINOR = 2
PATCH = 1

# Formatted Versions
VERSION = f"{MAJOR}.{MINOR}.{PATCH}"
FULL_VERSION = f"v{VERSION}"

# Release Info
RELEASE_DATE = "2026-02-11"
RELEASE_NAME = "Heartbeat Stability"

# API Compatibility
MIN_MOBILE_APP_VERSION = "1.0.0"
MIN_ARDUINO_VERSION = "1.0.0"
ARDUINO_SERIAL_PROTOCOL_VERSION = "1.0"

# Feature Flags
FEATURES = {
    'ml_automation': True,           # - Isolation Forest + Decision Tree
    'wifi_provisioning': True,       # - NetworkManager-based provisioning
    'firebase_sync': True,            # - Realtime DB + Admin SDK (client-side listener)
    'backend_api_sync': True,        # - REST API client with JWT
    'mdns_discovery': False,          # - Local network discovery
    'offline_first_db': True,        # - SQLite with sync queue
    'web_dashboard': True,           # - Flask Blueprint web UI
    'version_api': True,             # - Version endpoint for frontend
    'manual_controls': True,         # - Override automation
    'sensor_warmup': True,           # - Initial calibration period
    'smart_humidifier': False,        # - Predictive cycle manager
    'screen_management': True,       # - HDMI power control
    'mqtt_fallback': False,          # - Partial (client exists, not integrated)
    'systemd_service': True,         # - Scripts available, manual setup
    'chromium_kiosk': True,          # - Scripts available, manual setup
    'ota_updates': False,            # - Not implemented
    'advanced_recovery': False,      # - Basic error handling only
}

# Hardware Requirements
MIN_PYTHON_VERSION = "3.9"
SUPPORTED_PLATFORMS = ["linux", "darwin"]  # RPi (Linux) and macOS for testing

# Serial Protocol
SERIAL_BAUD_RATE = 9600
SERIAL_PROTOCOL = "json"
SENSOR_READ_INTERVAL = 5  # seconds


def get_version_info():
    """Get version information as dictionary"""
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
    """Get version headers for API requests"""
    return {
        'X-Device-Version': VERSION,
        'X-Device-Type': 'rpi-gateway',
        'X-Serial-Protocol': ARDUINO_SERIAL_PROTOCOL_VERSION,
    }


def is_mobile_compatible(mobile_version: str) -> bool:
    """Check if mobile app version is compatible with this gateway"""
    return _is_version_compatible(mobile_version, MIN_MOBILE_APP_VERSION)


def is_arduino_compatible(arduino_version: str) -> bool:
    """Check if Arduino firmware version is compatible"""
    return _is_version_compatible(arduino_version, MIN_ARDUINO_VERSION)


def _is_version_compatible(current: str, minimum: str) -> bool:
    """Check if current version meets minimum requirement"""
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


# Changelog
CHANGELOG = """
v2.2.1 (2026-02-11) - Heartbeat Stability

Fixed backend API PATCH spam and Arduino watchdog recovery for continuous operation.

Fixed:
 - Removed redundant send_sensor_data() from on_sensor_data callback (#IOT-102)
   Firebase RTDB handles real-time data; backend only needs periodic heartbeat.
 - Fixed check_connection() timing bug where last_connection_check was set before
   response validation, preventing backoff from engaging on failures.
 - Arduino watchdog now auto-recovers when serial communication resumes (#IOT-100)
   Previously required USB replug to restore actuator control after timeout.
 - Reduced WATCHDOG_TIMEOUT from 600s to 60s (RPi keepalive sends every 15s).

New:
 - Arduino emits {"watchdog":"recovered"} JSON on recovery from timeout
 - RPi serial_comm detects recovery signal and auto-restores relay states
 - SafetyWatchdog tracks recovery count and downtime duration

---

v2.2.0 (2026-02-11) - Smart Retry Logic

Implemented exponential backoff for backend API requests to reduce server load and prevent request spam on connection failures.

New Features:
 - Exponential backoff retry logic (10s, 30s, 1min, 5min, 10min max)
 - Intelligent connection state management with retry tracking
 - Helper methods: _calculate_retry_delay(), _reset_retry_state(), _is_in_backoff_period()
 - Detailed logging for retry state transitions

Improved:
 - Backend API client now respects retry intervals after failures
 - Reduced unnecessary API requests during persistent connection issues
 - Better logging showing retry count and next retry time
 - Connection check logic optimized to prevent spam

Fixed:
 - Excessive PATCH requests to backend on connection failures (issue #IOT-102)
 - 400 error spam from repeated failed requests
 - Server load from IoT devices making constant retry attempts

Technical:
 - Firebase streaming remains unaffected by backend retry logic
 - Retry state automatically resets on successful connection
 - Maximum backoff capped at 10 minutes to prevent indefinite delays

---

v2.1.5 (2026-02-10) - Firebase Sync Improvements

Fixed Firebase sync toggle to work across all clients and added debugging tools.

Added:
 - Server-side Firebase sync preference (affects all dashboards)
 - /api/firebase-sync/status endpoint (GET - check sync state)
 - /api/firebase-sync/toggle endpoint (POST - toggle sync for all clients)
 - /api/debug/firebase endpoint (diagnostic information)
 - Detailed Firebase upload logging with success/error tracking

Fixed:
 - Sync toggle now works across multiple browser instances
 - Removed localStorage dependency for sync state
 - Fixed async syntax errors in dashboard Firebase initialization

Improved:
 - Firebase upload now checks user preference before attempting
 - Better error handling with traceback logging
 - Clearer log messages for Firebase operations

---

v2.1.4 (2026-02-10) - Configuration Management Improvements

Improved configuration management with dynamic versioning and environment variable precedence.

Added:
 - Dynamic firmware_version injection from version.py (no manual updates needed)
 - Environment variable precedence (.env overrides config.yaml)
 - _override_config_from_env() method in MASHOrchestrator
 - DEVICE_ID_UUID in .env for Neon DB UUID
 - Clear comments distinguishing device ID vs serial number usage

Improved:
 - Configuration loading now respects environment variables
 - Firmware version always in sync with version.py
 - Clearer separation: UUID for backend API, serial for Firebase/UI

Documentation:
 - Explained Firebase data isolation per device
 - Documented ID vs serial number usage patterns
 - Clarified config.yaml precedence rules

---

v2.1.3 (2026-02-10) - Changelog Modal and Documentation

Added changelog viewer and updated documentation for Firebase architecture.

Added:
 - Changelog modal in Settings page
 - "View Changelog" button in About section
 - GET /api/changelog endpoint
 - Responsive modal design with animations

Improved:
 - Settings page UX with scrollable changelog viewer
 - Modal closes on outside click or ESC key
 - Loading spinner while fetching changelog

Documentation:
 - Explained Firebase RTDB vs Neon DB architecture
 - Firebase auto-creates structure on first write
 - Device ID authentication pattern documented

---

v2.1.2 (2026-02-10) - Firebase Fixes and System Controls

Critical bug fix and new system management features.

Fixed:
 - Firebase SDK loading race condition (wrapped in DOMContentLoaded)
 - "Sync: Failed" error now resolved

Added:
 - Reboot Device button in Settings with confirmation dialog
 - Shutdown Device button in Settings with confirmation dialog
 - Firebase Realtime Sync toggle in Settings (enable/disable via localStorage)
 - System control API endpoints: /api/system/reboot and /api/system/shutdown

Improved:
 - Settings page organization with Sync Settings section
 - User can now disable Firebase sync without code changes
 - System control buttons use proper confirmation modals

Technical:
 - Added subprocess import in routes.py for system commands
 - Requires sudoers NOPASSWD for reboot/shutdown commands

---

v2.1.1 (2026-02-10) - Firebase Config Fix and Sync Status

Bug fix release with improved Firebase configuration and status indicator clarity.

Fixed:
 - Corrected Firebase credentials from eCommerce (mash web app) to IoT-specific config
 - Firebase connection now uses MASH Grower project credentials

Improved:
 - Renamed "Cloud:" status indicator to "Sync:" for clarity
 - Added real-time Firebase connection status monitoring
 - Sync status updates to "Online" when Firebase connects successfully
 - Added error handling to show "Offline" or "Failed" states
 - Changed icon from cloud to sync (fa-sync)

---

v2.1.0 (2026-02-10) - Firebase Realtime Database Integration

Added real-time sensor data updates via Firebase Realtime Database for instant dashboard synchronization.

New Features:
 - Firebase SDK integration in web templates (compat version 10.14.1)
 - Real-time sensor value updates on dashboard without page refresh
 - Device ID injection from Flask to Firebase listener
 - Unique element IDs for all sensor cards (fruiting-temp, spawning-co2, etc.)
 - Console logging for Firebase sync debugging

Improved:
 - Dashboard responsiveness with live data streaming
 - User experience with instant feedback on sensor changes

Known Limitations:
 - Firebase Web API Key must be manually configured (placeholder in dashboard.html)
 - Requires Firebase project with Realtime Database enabled at asia-southeast1

---

v2.0.0 (2026-02-09) - New features and UI improvements

Major Milestone: Complete IoT Gateway Implementation

New Features:
- Version API endpoint (/api/version) for frontend display
- Enhanced settings page with version info
- Device identity management system
- User preferences persistence
- Comprehensive error handling across all modules
- Production-ready Flask Blueprint architecture
- Multi-room actuator state management
- Real-time connection status indicators
- WiFi mode detection and QR code generation
- Sensor warmup period with countdown

Improved:
- Refactored web routes with proper separation
- Enhanced logging with contextual tags
- Better NetworkManager permission handling
- Improved serial protocol reliability
- Optimized database query performance
- Consolidated configuration management

Setup Scripts Available:
- zen.sh - Update and Setup orchestrator
- setup_os.sh - Complete OS configuration
- setup_kiosk.sh - Chromium kiosk mode setup
- setup_mdns.sh - mDNS service configuration
- install_dependencies.sh - Python packages
- fix_networkmanager_permissions.sh - WiFi permissions
- diagnose_connection.py - Connection troubleshooting
- test_arduino.py - Hardware validation

Documentation:
- FIREBASE_INTEGRATION_GUIDE.md
- FIREBASE_QUICK_START.md
- QUICK_REFERENCE.md

Breaking Changes:
- Updated API response format for consistency
- Changed configuration structure in config.yaml
- Renamed environment variables (see .env.example)

Known Limitations:
- MQTT client not fully integrated (fallback mode)
- OTA firmware updates not implemented
- Advanced failure recovery mechanisms minimal

In Progress:
- mDNS service advertising for device discovery
- Firebase Realtime Database sync enhancements

---

v1.1.0 (2026-02-05) - Feature Enhancements

Added:
- mDNS advertiser module
- Device activation workflow
- Identity management utilities
- Passive fan controller
- Enhanced web UI components

Fixed:
- WiFi disconnect edge cases
- Serial reconnection logic
- Firebase authentication flow

---

v1.0.0 (2026-02-03) - Initial Release

First stable release of MASH IoT Gateway

Core Features:
- Flask web server with Blueprint architecture
- USB Serial communication with Arduino (JSON protocol at 9600 baud)
- WiFi provisioning via NetworkManager (nmcli)
- SQLite offline-first database with sync queue
- Firebase Realtime Database integration
- Firebase Admin SDK for authentication
- Backend REST API client with JWT auth
- ML automation engine (Isolation Forest + Decision Tree)
- Smart humidifier cycle manager (prevents overshoot)
- HDMI screen power management
- Manual actuator control with override tracking
- Dual-sensor support (SCD41 via hardware + software I2C)
- Safety watchdog (60s timeout)
- Real-time dashboard with condition indicators

Hardware Support:
- Raspberry Pi 3/4 (Linux armv7l/aarch64)
- Arduino Uno R3 (USB serial)
- SCD41 CO2 sensors (dual chamber)
- 8-channel relay module (active-low)

API Endpoints:
• GET /api/latest_data - Sensor readings and states
• POST /api/control_actuator - Manual actuator control
• POST /api/set_auto_mode - Toggle automation
• GET /api/wifi-scan - Available networks
• POST /api/wifi-connect - Connect to WiFi
• GET /api/wifi-mode - Current WiFi status
• GET /provisioning/info - Device provisioning state

Tested Platforms:
- Raspberry Pi OS (Bookworm)
- Ubuntu 22.04 (development)
- Windows 10/11 (limited testing)
"""


if __name__ == "__main__":
    print(f"MASH IoT Gateway {FULL_VERSION}")
    print(f"Release Date: {RELEASE_DATE}")
    print(f"Release Name: {RELEASE_NAME}")
    print("\nFeatures:")
    for feature, enabled in FEATURES.items():
        status = "✅" if enabled else "⚠️"
        print(f"  {status} {feature}")
    print(f"\nCompatibility:")
    print(f"  Min Mobile App: {MIN_MOBILE_APP_VERSION}")
    print(f"  Min Arduino: {MIN_ARDUINO_VERSION}")
    print(f"  Serial Protocol: {ARDUINO_SERIAL_PROTOCOL_VERSION}")

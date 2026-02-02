"""
MASH IoT Gateway - Version Constants

Semantic Versioning: MAJOR.MINOR.PATCH
- MAJOR: Breaking changes (API changes, serial protocol changes)
- MINOR: New features (backward compatible)
- PATCH: Bug fixes, small improvements

Last updated: 2026-02-03
"""

# Version Components
MAJOR = 1
MINOR = 0
PATCH = 0

# Formatted Versions
VERSION = f"{MAJOR}.{MINOR}.{PATCH}"
FULL_VERSION = f"v{VERSION}"

# Release Info
RELEASE_DATE = "2026-02-03"
RELEASE_NAME = "Initial Release"

# API Compatibility
MIN_MOBILE_APP_VERSION = "1.0.0"
MIN_ARDUINO_VERSION = "1.0.0"
ARDUINO_SERIAL_PROTOCOL_VERSION = "1.0"

# Feature Flags
FEATURES = {
    'ml_automation': True,
    'wifi_provisioning': True,
    'firebase_sync': True,
    'backend_api_sync': True,
    'mqtt_fallback': False,  # Not implemented yet
    'systemd_service': False,  # Manual setup required
    'chromium_kiosk': False,  # Not implemented yet
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
v1.0.0 (2026-02-03) - Initial Release

Features:
✅ Flask web server with Blueprint architecture
✅ USB Serial communication with Arduino (JSON protocol)
✅ WiFi provisioning via NetworkManager (nmcli)
✅ SQLite offline-first database
✅ Firebase Admin SDK integration
✅ Backend API client
✅ ML automation engine (Isolation Forest + Decision Tree)
✅ Smart humidifier cycle manager
✅ HDMI screen power management

In Progress:
🔨 systemd auto-start service

Missing:
⚠️ MQTT integration
⚠️ Chromium kiosk mode
⚠️ Advanced error recovery
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

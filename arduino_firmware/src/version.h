/**
 * MASH IoT Firmware - Version Constants
 * 
 * Semantic Versioning: MAJOR.MINOR.PATCH
 * - MAJOR: Breaking changes (serial protocol changes)
 * - MINOR: New features (new sensors, actuators)
 * - PATCH: Bug fixes, optimizations
 * 
 * Last updated: 2026-02-03
 */

#ifndef VERSION_H
#define VERSION_H

// Version Components
#define VERSION_MAJOR 1
#define VERSION_MINOR 0
#define VERSION_PATCH 0

// Formatted Version String
#define VERSION_STRING "1.0.0"
#define FULL_VERSION "v1.0.0"

// Release Info
#define RELEASE_DATE "2026-02-03"
#define RELEASE_NAME "Initial Release"

// Hardware Configuration
#define HARDWARE_BOARD "Arduino Uno R3"
#define SENSOR_TYPE "SCD41"
#define SENSOR_COUNT 2
#define RELAY_COUNT 8

// Serial Protocol
#define SERIAL_PROTOCOL_VERSION "1.0"
#define SERIAL_BAUD_RATE 9600
#define SERIAL_DATA_FORMAT "8N1"  // 8 data bits, no parity, 1 stop bit

// Compatibility
#define MIN_RPI_VERSION "1.0.0"

// Feature Flags
#define FEATURE_DUAL_SENSORS 1
#define FEATURE_RELAY_CONTROL 1
#define FEATURE_SAFETY_WATCHDOG 1
#define FEATURE_JSON_PROTOCOL 1
#define FEATURE_OTA_UPDATES 0  // Not implemented

// Timing Constants
#define SENSOR_READ_INTERVAL 5000    // 5 seconds
#define WATCHDOG_TIMEOUT 60000       // 60 seconds
#define RELAY_DEBOUNCE_MS 100        // 100ms debounce

// I2C Configuration
#define SCD41_ADDRESS 0x62
#define FRUITING_I2C_SDA A4          // Hardware I2C
#define FRUITING_I2C_SCL A5
#define SPAWNING_I2C_SDA 10          // Software I2C
#define SPAWNING_I2C_SCL 11

// Function to get version info over serial
void printVersionInfo() {
    Serial.println(F("=== MASH IoT Firmware ==="));
    Serial.print(F("Version: "));
    Serial.println(F(VERSION_STRING));
    Serial.print(F("Release Date: "));
    Serial.println(F(RELEASE_DATE));
    Serial.print(F("Hardware: "));
    Serial.println(F(HARDWARE_BOARD));
    Serial.print(F("Sensors: "));
    Serial.print(SENSOR_COUNT);
    Serial.print(F("x "));
    Serial.println(F(SENSOR_TYPE));
    Serial.print(F("Relays: "));
    Serial.println(RELAY_COUNT);
    Serial.print(F("Serial Protocol: "));
    Serial.println(F(SERIAL_PROTOCOL_VERSION));
    Serial.print(F("Baud Rate: "));
    Serial.println(SERIAL_BAUD_RATE);
    Serial.println(F("========================"));
}

// Changelog
const char CHANGELOG[] PROGMEM = R"(
v1.0.0 (2026-02-03) - Initial Release

Features:
- Dual SCD41 sensor support
  * Fruiting room: Hardware I2C (A4/A5)
  * Spawning room: Software I2C (D10/D11)
- 8-channel relay control (active-low)
- JSON sensor data transmission (5s interval)
- JSON command reception and parsing
- Safety watchdog (60s timeout)
- Auto-relay shutdown on serial disconnect

Missing:
- OTA firmware updates
)";

#endif // VERSION_H

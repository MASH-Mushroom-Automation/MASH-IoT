# M.A.S.H. IoT - Arduino Firmware Documentation

## Overview
This firmware runs on an Arduino Uno/Mega to control mushroom cultivation rooms. It manages two SCD41 environmental sensors (CO2, temperature, humidity) and an 8-channel relay module for actuators.

## Hardware Architecture

### Three-Room System
1. **Fruiting Room** - Sensor + 5 actuators
2. **Spawning Room** - Sensor + 1 actuator  
3. **Device Room** - 1 actuator (no sensors)

### Sensors (SCD41 CO2/Temp/Humidity)
| Room | Sensor | I2C Type | Pins | Notes |
|------|--------|----------|------|-------|
| Fruiting | SCD41 #1 | Hardware I2C | A4 (SDA), A5 (SCL) | Via Grove Hub |
| Spawning | SCD41 #2 | Software I2C | D10 (SDA), D11 (SCL) | SoftWire library |

### Actuators (8-Channel Relay Module - Active LOW)
| IN# | Pin | Actuator | Room | Voltage | Notes |
|-----|-----|----------|------|---------|-------|
| IN1 | D2 | Mist Maker | Fruiting | 45V AC | Humidifier |
| IN2 | D3 | Humidifier Fan | Fruiting | 12V AC | Circulates mist |
| IN3 | D4 | Exhaust Fan | Fruiting | 24V AC | Removes CO2 |
| IN4 | D5 | Intake Fan | Fruiting | 12V AC | Fresh air blower |
| IN5 | D6 | Exhaust Fan | Spawning | 12V | Passive w/ flush |
| IN6 | D7 | Exhaust Fan | Device | 12V | Passive cooling |
| IN7 | D8 | LED Lights | Fruiting | 5V AC | Grow lights |
| IN8 | D9 | Reserved | - | - | Future expansion |

**Active LOW Logic:** Write `LOW` to turn relay ON, `HIGH` to turn OFF.

## Serial Communication Protocol

### Arduino → Raspberry Pi (Sensor Data)
**Format:** JSON over USB Serial (9600 baud, 8N1)  
**Interval:** Every 5 seconds

```json
{
  "fruiting": {"temp": 23.5, "humidity": 85.0, "co2": 800},
  "spawning": {"temp": 24.0, "humidity": 90.0, "co2": 1200},
  "device": {"status": "no_sensors"}
}
```

**Error Handling:**
```json
{"fruiting": {"error": "invalid_reading"}}
```

### Raspberry Pi → Arduino (Control Commands)
**Format:** JSON commands (newline-terminated)

```json
{"actuator": "MIST_MAKER", "state": "ON"}
{"actuator": "FRUITING_EXHAUST_FAN", "state": "OFF"}
```

**Available Actuators:**
- `MIST_MAKER`
- `HUMIDIFIER_FAN`
- `FRUITING_EXHAUST_FAN`
- `FRUITING_INTAKE_FAN`
- `SPAWNING_EXHAUST_FAN`
- `DEVICE_EXHAUST_FAN`
- `FRUITING_LED`
- `RESERVED`

**States:** `ON` or `OFF`

## Safety Features

### Watchdog Timer
- **Timeout:** 10 seconds without serial data
- **Action:** Shuts down ALL relays (writes HIGH to all pins)
- **Purpose:** Prevents equipment damage if RPi crashes

### Anomaly Filtering
- **Moving Average Filter:** 5-sample window for temp/humidity
- **Range Validation:**
  - Temperature: -10°C to 60°C
  - Humidity: 0% to 100%
  - CO2: 400 to 5000 ppm
- **Fallback:** Returns last valid reading if current read fails

### Startup Behavior
- All relays initialize to OFF state (HIGH)
- 2-second sensor warmup period
- Serial port wait loop (for native USB boards)

## Building & Flashing

### PlatformIO (Recommended)
```bash
cd arduino_firmware
pio run              # Compile
pio run -t upload    # Flash to Arduino
pio device monitor   # Serial monitor
```

### Arduino IDE
1. Install libraries:
   - ArduinoJson (v6+)
   - Sensirion I2C SCD4x
   - Sensirion Core
   - SoftWire
2. Set board: Arduino Uno/Mega
3. Upload `src/main.cpp`

## File Structure
```
src/
├── main.cpp       # Main loop (sensor reads + command handling)
├── sensors.cpp/h  # SCD41 dual-sensor management
├── actuators.cpp/h # Relay control logic
├── safety.cpp/h   # Watchdog timer
└── config.h       # Pin definitions & constants
```

## Development Notes

### Dual I2C Setup (Critical)
Both SCD41 sensors use address **0x62**, differentiated by I2C bus:
- **Sensor 1:** Hardware I2C (`Wire` library)
- **Sensor 2:** Software I2C (`SoftWire` library on D10/D11)

**Why not I2C address change?** SCD41 has a fixed address (0x62).

### Passive vs Flush Exhaust
**Spawning/Device exhaust fans:**
- **Passive:** Run on timed intervals (controlled by RPi logic)
- **Flush:** Bypass timer when CO2 threshold exceeded (RPi sends immediate command)

This logic is implemented on the **Raspberry Pi side**, not Arduino.

## Troubleshooting

### Sensor Read Failures
**Symptom:** JSON shows `"error": "invalid_reading"`  
**Causes:**
1. Sensor not connected (check I2C wiring)
2. SoftWire pins incorrect (verify D10/D11 for Sensor 2)
3. Sensor warming up (wait 5+ seconds after boot)

**Debug:** Open Serial Monitor (9600 baud), look for:
```
[ERROR] Failed to start Fruiting sensor (HW I2C)
[WARNING] Fruiting sensor out of range
```

### Relays Not Switching
**Symptom:** No click sound, actuator stays OFF  
**Causes:**
1. Active-low logic inverted (should write LOW to turn ON)
2. Wrong pin mapping (check `config.h` vs physical wiring)
3. Relay module power supply disconnected (needs 5V VCC)

**Test:** Send command via Serial Monitor:
```
{"actuator":"MIST_MAKER","state":"ON"}
```
You should hear a click and see LED on relay module.

### Watchdog Triggering
**Symptom:** Relays shut off every 10 seconds  
**Cause:** RPi not sending commands (watchdog timeout)  
**Fix:** Ensure RPi serial communication is active. Arduino expects data at least once per 10 seconds.

## Wiring Diagram

### Hardware I2C (Fruiting Sensor)
```
SCD41 #1 → Grove Hub → Arduino
   VCC → 5V
   GND → GND
   SDA → A4
   SCL → A5
```

### Software I2C (Spawning Sensor)
```
SCD41 #2 → Arduino (direct connection)
   VCC → 5V
   GND → GND
   SDA → D10
   SCL → D11
```

### Relay Module
```
8-CH Relay → Arduino
   VCC → 5V
   GND → GND
   IN1 → D2 (Mist Maker)
   IN2 → D3 (Humidifier Fan)
   IN3 → D4 (Fruiting Exhaust)
   IN4 → D5 (Fruiting Intake)
   IN5 → D6 (Spawning Exhaust)
   IN6 → D7 (Device Exhaust)
   IN7 → D8 (LED Lights)
   IN8 → D9 (Reserved)
```

## Changelog

### v2.0 (January 2026)
- ✅ Refactored for actual hardware (3 rooms, 8 relays)
- ✅ Enabled second SCD41 sensor (Software I2C)
- ✅ Updated relay pin mappings (IN1-IN8)
- ✅ JSON-based commands (replaced text-based)
- ✅ Added Device room support
- ✅ Renamed actuators for clarity

### v1.0 (Initial)
- Single sensor operation
- Text-based commands
- 6 relay support only

## License
MIT License - See root LICENSE file

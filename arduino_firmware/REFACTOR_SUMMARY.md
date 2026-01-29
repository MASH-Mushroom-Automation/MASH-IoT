# Arduino Firmware Refactoring Summary

## Changes Made

### 1. Hardware Pin Mapping Update ([config.h](src/config.h))
**Before:** Generic pin assignments without clear hardware mapping  
**After:** Explicit 8-relay module mapping matching physical IN1-IN8 layout

```cpp
// NEW MAPPING
#define RELAY_MIST_MAKER_PIN 2        // IN1: Fruiting Humidifier 45V
#define RELAY_HUMIDIFIER_FAN_PIN 3    // IN2: Fruiting Fan 12V
#define RELAY_FRUITING_EXHAUST_PIN 4  // IN3: Fruiting Exhaust 24V
#define RELAY_FRUITING_INTAKE_PIN 5   // IN4: Fruiting Intake 12V
#define RELAY_SPAWNING_EXHAUST_PIN 6  // IN5: Spawning Exhaust 12V
#define RELAY_DEVICE_EXHAUST_PIN 7    // IN6: Device Exhaust 12V
#define RELAY_LED_LIGHTS_PIN 8        // IN7: Fruiting LED 5V
#define RELAY_RESERVED_PIN 9          // IN8: Reserved
```

### 2. Actuator Enum Refactoring ([actuators.h](src/actuators.h))
**Changed:** Renamed all actuators to match real hardware  
**Added:** Device room exhaust fan support

```cpp
enum ActuatorType {
    MIST_MAKER,            // Renamed from HUMIDIFIER
    HUMIDIFIER_FAN,        // New name for clarity
    FRUITING_EXHAUST_FAN,  // Existing
    FRUITING_INTAKE_FAN,   // Renamed from FRUITING_BLOWER_FAN
    SPAWNING_EXHAUST_FAN,  // Existing
    DEVICE_EXHAUST_FAN,    // NEW - Device room support
    FRUITING_LED,          // Existing
    RESERVED               // NEW - Future expansion
};
```

### 3. Dual Sensor Implementation ([sensors.cpp/h](src/sensors.cpp))
**Status:** ✅ FULLY ENABLED  
**Before:** Second sensor commented out  
**After:** Both SCD41 sensors operational with dual I2C

```cpp
// Fruiting Room: Hardware I2C (A4/A5)
SensirionI2CScd4x scd41_fruiting;

// Spawning Room: Software I2C (D10/D11)
SoftWire softWire(SOFTWARE_SDA_PIN, SOFTWARE_SCL_PIN);
SensirionI2CScd4x scd41_spawning;
```

**Filters:** Both sensors now have moving average filters enabled

### 4. JSON Output Update ([main.cpp](src/main.cpp))
**Added:** Device room status in JSON payload  
**Format:** 3-room structure instead of 2

```json
{
  "fruiting": {"temp": 23.5, "humidity": 85.0, "co2": 800},
  "spawning": {"temp": 24.0, "humidity": 90.0, "co2": 1200},
  "device": {"status": "no_sensors"}
}
```

### 5. Command Parsing ([main.cpp](src/main.cpp))
**Updated:** String-to-enum mapping for new actuator names

```cpp
// Command format: {"actuator": "MIST_MAKER", "state": "ON"}
ActuatorType stringToActuatorType(const char* str) {
    if (strcmp(str, "MIST_MAKER") == 0) return MIST_MAKER;
    if (strcmp(str, "HUMIDIFIER_FAN") == 0) return HUMIDIFIER_FAN;
    if (strcmp(str, "FRUITING_EXHAUST_FAN") == 0) return FRUITING_EXHAUST_FAN;
    if (strcmp(str, "FRUITING_INTAKE_FAN") == 0) return FRUITING_INTAKE_FAN;
    if (strcmp(str, "SPAWNING_EXHAUST_FAN") == 0) return SPAWNING_EXHAUST_FAN;
    if (strcmp(str, "DEVICE_EXHAUST_FAN") == 0) return DEVICE_EXHAUST_FAN;
    if (strcmp(str, "FRUITING_LED") == 0) return FRUITING_LED;
    if (strcmp(str, "RESERVED") == 0) return RESERVED;
    return (ActuatorType)-1;
}
```

## Hardware Configuration Summary

### Sensors
- **Fruiting Room:** SCD41 on Hardware I2C (A4/A5) via Grove Hub
- **Spawning Room:** SCD41 on Software I2C (D10/D11) direct connection
- **Device Room:** No sensors (exhaust fan only)

### Actuators (8-Channel Relay - Active LOW)
```
Fruiting Room (5 actuators):
  ├─ IN1 (D2): Mist Maker (45V)
  ├─ IN2 (D3): Humidifier Fan (12V)
  ├─ IN3 (D4): Exhaust Fan (24V)
  ├─ IN4 (D5): Intake Fan (12V)
  └─ IN7 (D8): LED Lights (5V)

Spawning Room (1 actuator):
  └─ IN5 (D6): Exhaust Fan (12V) - Passive w/ Flush

Device Room (1 actuator):
  └─ IN6 (D7): Exhaust Fan (12V) - Passive

Reserved:
  └─ IN8 (D9): Future expansion
```

## Communication Protocol Changes

### Sensor Data (Unchanged)
- Still JSON format every 5 seconds
- Added `"device"` key in payload

### Commands (Updated Names)
**Old Commands:**
```json
{"actuator": "HUMIDIFIER", "state": "ON"}
{"actuator": "FRUITING_BLOWER_FAN", "state": "ON"}
```

**New Commands:**
```json
{"actuator": "MIST_MAKER", "state": "ON"}
{"actuator": "FRUITING_INTAKE_FAN", "state": "ON"}
{"actuator": "DEVICE_EXHAUST_FAN", "state": "ON"}
```

## Raspberry Pi Integration Impact

### What Changed for RPi Code
1. **Actuator Names:** Update all command strings to new names
2. **JSON Parsing:** Expect 3 rooms in sensor data (fruiting, spawning, device)
3. **Device Room:** New room type to handle in logic engine

### Example RPi Command Update
```python
# OLD
serial_port.write(b'{"actuator":"HUMIDIFIER","state":"ON"}\n')

# NEW
serial_port.write(b'{"actuator":"MIST_MAKER","state":"ON"}\n')
```

## Safety Features (Unchanged)
- Watchdog timer: 10s timeout → shutdown all relays
- Moving average filters: 5-sample window
- Range validation: Temp (-10°C to 60°C), Humidity (0-100%), CO2 (400-5000ppm)
- Active-LOW relay logic: HIGH = OFF, LOW = ON

## Testing Checklist

### Before Integration
- [ ] Compile firmware: `pio run`
- [ ] Upload to Arduino: `pio run -t upload`
- [ ] Check serial output: `pio device monitor`
- [ ] Verify 3-room JSON structure
- [ ] Test each relay with manual commands

### After RPi Connection
- [ ] Update RPi actuator name strings
- [ ] Verify device room handling in logic engine
- [ ] Test passive exhaust timing
- [ ] Test flush exhaust override

## Files Modified
1. **config.h** - Pin mappings, I2C definitions
2. **actuators.h** - Enum updated with 8 actuators
3. **actuators.cpp** - Updated pin getters, shutdown logic
4. **sensors.h** - Uncommented second sensor variables
5. **sensors.cpp** - Enabled SoftWire I2C, readSensor2()
6. **main.cpp** - 3-room JSON, updated command parsing

## Documentation Added
- **FIRMWARE.md** - Comprehensive hardware guide
- **REFACTOR_SUMMARY.md** - This file

## Next Steps
1. Test compile firmware
2. Flash to Arduino and verify serial output
3. Update Raspberry Pi code to match new actuator names
4. Update `rpi_gateway/config/config.yaml` with device room thresholds
5. Test full integration with RPi

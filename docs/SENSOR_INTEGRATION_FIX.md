# Sensor Integration Fix & Diagnostics

## Issues Found

### 1. ✅ FIXED: MushroomAI Method Signature Error
**Error:** `MushroomAI.process_sensor_reading() takes 2 positional arguments but 3 were given`

**Problem:**
- `main.py` was calling: `ai.process_sensor_reading(room, sensor_reading)` for each room
- `logic_engine.py` expects: `ai.process_sensor_reading(room_data)` with ALL rooms at once

**Fixed in:** `rpi_gateway/app/main.py`

**Changes:**
```python
# OLD (WRONG):
for room in ['fruiting', 'spawning']:
    commands = self.ai.process_sensor_reading(room, sensor_reading)

# NEW (CORRECT):
valid_rooms = {'fruiting': {...}, 'spawning': {...}}
commands = self.ai.process_sensor_reading(valid_rooms)
```

**Additional improvements:**
- Filters out invalid readings before processing
- Skips automation if all sensors have errors
- Better error logging with traceback

---

### 2. ⚠️ TO INVESTIGATE: Invalid Sensor Readings

**Error:** `[ARDUINO] Fruiting sensor error: invalid_reading`  
**Error:** `[ARDUINO] Spawning sensor error: invalid_reading`

**Possible causes:**
1. **Multiplexer not connected yet** - You mentioned you haven't connected it to Arduino
2. **Sensors still warming up** - SCD41 needs ~5 seconds after power-on
3. **Wiring issues** - Check VIN/GND connections
4. **I2C bus conflict** - Both sensors at same address without multiplexer

---

## Current Status

### Arduino Firmware
✅ **Already supports both sensors!**
- Reads Sensor 1 (Fruiting) via Hardware I2C
- Reads Sensor 2 (Spawning) via Software I2C OR multiplexer
- Sends JSON with both rooms: `{"fruiting": {...}, "spawning": {...}}`
- Sends `"error": "invalid_reading"` when sensor fails validation

### Raspberry Pi Gateway  
✅ **Now properly handles two sensors!**
- Parses JSON with both fruiting and spawning rooms
- Room-specific data access: `arduino.get_fruiting_room_data()`
- Filters out invalid readings before automation
- Passes all valid rooms to MushroomAI at once

---

## How to Diagnose Sensor Issues

### Option 1: Use Diagnostic Sketch (Recommended)

1. **Upload diagnostic firmware:**
   ```bash
   cd arduino_firmware
   # Temporarily rename main.cpp
   mv src/main.cpp src/main.cpp.backup
   mv src/diagnostics.cpp src/main.cpp
   
   # Upload
   pio run -t upload
   
   # Monitor
   pio device monitor
   ```

2. **Expected output:**
   ```
   ========================================
     M.A.S.H. IoT - Sensor Diagnostics
   ========================================
   
   [TEST 1] Checking for TCA9548A multiplexer...
     ✓ MULTIPLEXER DETECTED at 0x70
       Will use Hardware I2C for both sensors
   
   [TEST 2A] Fruiting Room Sensor (MUX Channel 0):
     ✓ Sensor started, waiting 5 seconds for first reading...
     ✓ SENSOR WORKING!
       Temperature: 23.5°C
       Humidity:    85.0%
       CO2:         800 ppm
   
   [TEST 2B] Spawning Room Sensor (MUX Channel 1):
     ✓ Sensor started, waiting 5 seconds for first reading...
     ✓ SENSOR WORKING!
       Temperature: 24.0°C
       Humidity:    90.0%
       CO2:         1200 ppm
   ```

3. **Restore main firmware:**
   ```bash
   mv src/main.cpp src/diagnostics.cpp
   mv src/main.cpp.backup src/main.cpp
   pio run -t upload
   ```

### Option 2: Check Serial Output

Monitor the Arduino serial output with normal firmware:

```bash
cd arduino_firmware
pio device monitor
```

**Look for:**
- `[OK] TCA9548A multiplexer detected!` - Multiplexer is working
- `[WARN] Multiplexer not detected, falling back to SoftWire mode` - No multiplexer
- `[OK] Both sensors initialized via multiplexer` - Success!
- `[ERROR] Failed to start Fruiting sensor` - Sensor 1 problem
- `[ERROR] Failed to start Spawning sensor` - Sensor 2 problem

### Option 3: Test from Raspberry Pi

```bash
python3 scripts/test_arduino.py
```

If you see:
```
🍄 Fruiting Room: No data
🌱 Spawning Room: No data
```

Then the Arduino is sending `"error": "invalid_reading"` for both sensors.

---

## Hardware Checklist

### Multiplexer Connection (Not Connected Yet)
- [ ] TCA9548A **SDA** → Arduino **A4**
- [ ] TCA9548A **SCL** → Arduino **A5**
- [ ] TCA9548A **VIN** → Arduino **5V**
- [ ] TCA9548A **GND** → Arduino **GND**

### Sensor Connections (Already Done)
- [x] Fruiting SCD41 → Multiplexer **SD0/SC0** (Channel 0)
- [x] Spawning SCD41 → Multiplexer **SD1/SC1** (Channel 1)
- [x] Both sensors' VIN/GND → Multiplexer VIN/GND

### What to Do Next

1. **Connect the multiplexer to Arduino:**
   - SDA → A4
   - SCL → A5
   - VIN → 5V
   - GND → GND

2. **Upload diagnostic sketch** to verify both sensors work

3. **Upload main firmware** and check serial monitor

4. **Test from Raspberry Pi** with `python3 scripts/test_arduino.py`

---

## Expected Behavior After Fix

### When Working Correctly:

**Arduino Serial Monitor:**
```
{"fruiting":{"temp":23.5,"humidity":85.0,"co2":800},"spawning":{"temp":24.0,"humidity":90.0,"co2":1200}}
```

**Raspberry Pi Logs:**
```
[SERIAL] ✓ Connected to Arduino on /dev/ttyACM0 @ 9600 baud
[DATA] Received sensor data at 1769715072.19
[AUTO] Sent command: FRUITING_EXHAUST_FAN_ON
[AUTO] Sent command: HUMIDIFIER_ON
```

**Test Script Output:**
```
🍄 Fruiting Room:
   Temperature: 23.5°C
   Humidity:    85.0%
   CO2:         800 ppm

🌱 Spawning Room:
   Temperature: 24.0°C
   Humidity:    90.0%
   CO2:         1200 ppm
```

---

## Summary

| Issue | Status | Action Required |
|-------|--------|-----------------|
| MushroomAI signature error | ✅ Fixed | None - already updated |
| Invalid sensor readings | ⚠️ To fix | Connect multiplexer to Arduino |
| Auto-reconnect | ✅ Fixed | None - working |
| Room-specific data | ✅ Ready | None - already implemented |

**Next steps:**
1. Connect multiplexer to Arduino
2. Upload diagnostic sketch to verify sensors
3. Upload main firmware
4. Test with `python3 scripts/test_arduino.py`

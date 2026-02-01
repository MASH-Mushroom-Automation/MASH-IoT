# Actuator Control Bug Fix

## Problem Description
Actuators would turn ON when commanded but immediately turn OFF after a few seconds.

## Root Causes Found

### 1. **Duplicate Serial Handling Code (CRITICAL)**
**Location:** [main.cpp](c:/Users/Ryzen/Desktop/ThesisDev/Mobile IoT/MASH-IoT/arduino_firmware/src/main.cpp) lines 70-130

**Issue:**
- The main loop had TWO serial handling sections:
  - Line 76: `handleSerialCommands()` - Proper JSON parser
  - Lines 115-130: Duplicate/dead code that called non-existent `actuators.executeCommand()`

**Impact:**
- The duplicate code section never updated the watchdog heartbeat
- This caused the watchdog to think the RPi was disconnected
- After 10 seconds, watchdog would trigger `actuators.shutdownAll()`
- All relays would turn OFF regardless of user commands

### 2. **Missing Watchdog Heartbeat**
**Location:** [main.cpp](c:/Users/Ryzen/Desktop/ThesisDev/Mobile IoT/MASH-IoT/arduino_firmware/src/main.cpp#L147)

**Issue:**
- `handleSerialCommands()` function didn't call `watchdog.heartbeat()` when receiving data
- Watchdog timeout was set to 10 seconds in [config.h](c:/Users/Ryzen/Desktop/ThesisDev/Mobile IoT/MASH-IoT/arduino_firmware/src/config.h#L43)
- If Python didn't send commands frequently enough, watchdog would timeout

**Impact:**
- Even valid commands would be ignored after 10 seconds
- System would enter safety shutdown mode

### 3. **Inconsistent Command Format (Python Side)**
**Location:** [routes.py](c:/Users/Ryzen/Desktop/ThesisDev/Mobile IoT/MASH-IoT/rpi_gateway/app/web/routes.py#L443)

**Issue:**
- Web route was sending old-style commands: `MIST_MAKER_ON`
- Arduino firmware expected JSON: `{"actuator": "MIST_MAKER", "state": "ON"}`
- The `send_command()` function in [serial_comm.py](c:/Users/Ryzen/Desktop/ThesisDev/Mobile IoT/MASH-IoT/rpi_gateway/app/core/serial_comm.py#L164) tried to convert, but this added complexity

## Fixes Applied

### Fix 1: Remove Duplicate Serial Code (Arduino)
**File:** [main.cpp](c:/Users/Ryzen/Desktop/ThesisDev/Mobile IoT/MASH-IoT/arduino_firmware/src/main.cpp#L115-L130)

**Action:** Removed lines 115-130 (duplicate serial handling section)

**Before:**
```cpp
// ==================== TASK 2: LISTEN FOR COMMANDS ====================
while (Serial.available() > 0) {
    char c = Serial.read();
    watchdog.heartbeat();
    if (c == '\n' || c == '\r') {
        if (bufferIndex > 0) {
            serialBuffer[bufferIndex] = '\0';
            actuators.executeCommand(serialBuffer);  // This method doesn't exist!
            bufferIndex = 0;
        }
    } else if (bufferIndex < 127) {
        serialBuffer[bufferIndex++] = c;
    }
}
```

**After:**
```cpp
// Removed - handleSerialCommands() already handles this
```

### Fix 2: Add Watchdog Heartbeat to Serial Handler (Arduino)
**File:** [main.cpp](c:/Users/Ryzen/Desktop/ThesisDev/Mobile IoT/MASH-IoT/arduino_firmware/src/main.cpp#L147)

**Action:** Added `watchdog.heartbeat()` call when any serial data is received

**Before:**
```cpp
void handleSerialCommands() {
    static int bufferPos = 0;
    while (Serial.available() > 0) {
        char incomingChar = Serial.read();
        // No watchdog update!
        ...
    }
}
```

**After:**
```cpp
void handleSerialCommands() {
    static int bufferPos = 0;
    while (Serial.available() > 0) {
        char incomingChar = Serial.read();
        
        // Update watchdog heartbeat on ANY serial data received
        watchdog.heartbeat();
        
        ...
    }
}
```

### Fix 3: Use JSON Format Consistently (Python)
**File:** [routes.py](c:/Users/Ryzen/Desktop/ThesisDev/Mobile IoT/MASH-IoT/rpi_gateway/app/web/routes.py#L443-L447)

**Action:** Changed to send JSON format directly instead of old-style commands

**Before:**
```python
command = f'{arduino_actuator}_{state}'  # e.g., "MIST_MAKER_ON"
success = serial_comm.send_command(command)
```

**After:**
```python
import json
json_cmd = json.dumps({"actuator": arduino_actuator, "state": state})
success = serial_comm.send_command(json_cmd)
```

### Fix 4: Simplify send_command Function (Python)
**File:** [serial_comm.py](c:/Users/Ryzen/Desktop/ThesisDev/Mobile IoT/MASH-IoT/rpi_gateway/app/core/serial_comm.py#L164-L203)

**Action:** Removed command format conversion logic since we now always send JSON

**Before:**
```python
def send_command(self, command: str) -> bool:
    # Check if it's JSON or old-style command
    if command.startswith('{'):
        cmd_with_newline = f"{command}\n".encode('utf-8')
    else:
        # Convert old-style to JSON
        parts = command.rsplit('_', 1)
        if len(parts) == 2:
            actuator_name, state = parts
            json_cmd = json.dumps({"actuator": actuator_name, "state": state})
            cmd_with_newline = f"{json_cmd}\n".encode('utf-8')
        ...
```

**After:**
```python
def send_command(self, command: str) -> bool:
    """Send a JSON command string to the Arduino."""
    # Simply add newline and encode
    cmd_with_newline = f"{command}\n".encode('utf-8')
    self.serial_conn.write(cmd_with_newline)
    self.serial_conn.flush()
    ...
```

## Testing the Fix

### Upload New Firmware:
```bash
cd MASH-IoT/arduino_firmware
pio run -t upload
```

### Restart Python Backend:
```bash
cd MASH-IoT
python3 rpi_gateway/app/main.py
```

### Test Actuator Controls:
1. Open web interface
2. Go to Controls page
3. Turn ON any actuator (e.g., Mist Maker)
4. **Expected:** Actuator stays ON
5. **Previous bug:** Would turn OFF after ~10 seconds
6. Wait 15-20 seconds to verify it stays ON

### Monitor Arduino Serial Output:
```
[CMD] Set MIST_MAKER to ON
[CMD] Set MIST_MAKER to OFF
[WATCHDOG] Connection restored  # Should NOT see "TIMEOUT"
```

## Technical Details

### Watchdog Behavior:
- **Timeout:** 10 seconds without serial data
- **Check Interval:** Every 1 second
- **Action on Timeout:** Call `actuators.shutdownAll()` (sets all relays to OFF)
- **Reset:** Any serial data resets the timer

### JSON Command Format:
```json
{
  "actuator": "MIST_MAKER",
  "state": "ON"
}
```

**Valid Actuator Names:**
- `MIST_MAKER`
- `HUMIDIFIER_FAN`
- `FRUITING_EXHAUST_FAN`
- `FRUITING_INTAKE_FAN`
- `SPAWNING_EXHAUST_FAN`
- `DEVICE_EXHAUST_FAN`
- `FRUITING_LED`
- `RESERVED`

**Valid States:**
- `ON` - Turn relay ON (digitalWrite LOW for active-low relays)
- `OFF` - Turn relay OFF (digitalWrite HIGH for active-low relays)

## Why This Happened

The bug was introduced when the firmware was refactored to use JSON commands. The old serial handling code (lines 115-130) was left in place by mistake, creating a conflict:

1. User clicks "Turn ON Mist Maker" on web interface
2. Python sends JSON: `{"actuator": "MIST_MAKER", "state": "ON"}\n`
3. Arduino receives it in `handleSerialCommands()` at line 76
4. Actuator turns ON successfully
5. **BUG:** Watchdog not being updated in `handleSerialCommands()`
6. After 10 seconds, watchdog times out
7. Watchdog calls `actuators.shutdownAll()`
8. All relays turn OFF immediately

## Files Modified

1. **arduino_firmware/src/main.cpp**
   - Removed duplicate serial handling code (lines 115-130)
   - Added `watchdog.heartbeat()` in `handleSerialCommands()`

2. **rpi_gateway/app/web/routes.py**
   - Changed `/api/control_actuator` endpoint to send JSON format
   - Added `import json` statement

3. **rpi_gateway/app/core/serial_comm.py**
   - Simplified `send_command()` to expect JSON format
   - Removed command format conversion logic

## Prevention

To prevent similar issues in the future:

1. **Always update watchdog** when receiving serial data
2. **Use consistent command formats** across all code
3. **Remove dead/duplicate code** during refactoring
4. **Test with delays** - Verify actuators stay ON for >10 seconds
5. **Monitor serial output** - Check for watchdog timeout messages

## Related Documentation

- [Arduino Firmware Architecture](c:/Users/Ryzen/Desktop/ThesisDev/Mobile IoT/MASH-IoT/arduino_firmware/FIRMWARE.md)
- [Serial Communication Protocol](c:/Users/Ryzen/Desktop/ThesisDev/Mobile IoT/MASH-IoT/rpi_gateway/app/core/serial_comm.py)
- [Safety Watchdog Implementation](c:/Users/Ryzen/Desktop/ThesisDev/Mobile IoT/MASH-IoT/arduino_firmware/src/safety.cpp)

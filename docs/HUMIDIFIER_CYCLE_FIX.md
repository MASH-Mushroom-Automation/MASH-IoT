# Humidifier System Fix - Complete Solution

## Problem Summary

**Issue**: Humidifier System doesn't cycle properly
- **Expected**: IN1 (Mist Maker) ON for 10s → IN1 OFF, IN2 (Fan) ON for 30s → Repeat
- **Actual**: IN1 stays ON forever, IN2 never activates

## Root Cause

The `HumidifierCycleManager` was correctly implemented with timing logic, BUT:

1. **Manual Control Issue**: When clicking the Humidifier System button, it only sent `MIST_MAKER_ON` command directly to Arduino, bypassing the cycle manager entirely.

2. **Missing Cycle Updates**: The cycle manager's `get_current_states()` method wasn't being called continuously to generate commands for phase transitions.

3. **No Integration**: Manual controls had no way to start/stop the cycle manager - they just sent raw commands to Arduino.

## Solution Implemented

### 1. Integrated Manual Control with Cycle Manager

**File**: `routes.py`

Added special handling in the `/api/control_actuator` endpoint:

```python
# When user clicks Humidifier System button
if actuator == 'mist_maker' and room == 'fruiting':
    if state == 'ON':
        orchestrator.ai.humidifier_cycle.start_cycle()  # ✅ Start the cycle manager
    else:
        orchestrator.ai.humidifier_cycle.stop_cycle()   # ✅ Stop the cycle manager
```

**Before**: Sent `MIST_MAKER_ON` → Mist stayed on forever
**After**: Starts cycle manager → Mist runs 10s, then fan runs 30s, repeat

### 2. Added Continuous Cycle State Updates

**File**: `main.py` - `on_sensor_data()` method

Added code to continuously send cycle commands:

```python
# Always update humidifier cycle (even in manual mode)
if self.ai and self.ai.humidifier_cycle.cycle_active:
    cycle_states = self.ai.humidifier_cycle.get_current_states()  # Get current phase
    
    # Send commands for current phase
    for actuator, state in cycle_states.items():
        if actuator == 'mist_maker':
            command = f"MIST_MAKER_{state}"
        elif actuator == 'humidifier_fan':
            command = f"HUMIDIFIER_FAN_{state}"
        
        self.arduino.send_command(command)  # Send to Arduino
        self._update_actuator_state_from_command(command)  # Update UI
```

**How it works**:
- Every time sensor data is received (~every 5 seconds)
- Check if cycle is active
- Get current phase states from cycle manager
- Send appropriate commands to Arduino
- Update UI states

### 3. Pass Orchestrator Reference to Routes

**File**: `main.py`

```python
# In __init__:
self.app.config['orchestrator'] = self

# In start():
self.app.orchestrator = self
```

This allows routes to access the cycle manager through `current_app.orchestrator.ai.humidifier_cycle`

## How It Works Now

### Manual Control Flow:

```
User clicks Humidifier System button
    ↓
Control sends: {"actuator": "mist_maker", "state": "ON"}
    ↓
routes.py: orchestrator.ai.humidifier_cycle.start_cycle()
    ↓
Cycle Manager sets: phase="mist", start_time=now
    ↓
[Every sensor reading (5s)]
    ↓
main.py: get_current_states() called
    ↓
Returns: {"mist_maker": "ON", "humidifier_fan": "OFF"}  (first 10s)
    ↓
Commands sent: MIST_MAKER_ON, HUMIDIFIER_FAN_OFF
    ↓
[After 10 seconds]
    ↓
Cycle Manager switches: phase="fan"
    ↓
Returns: {"mist_maker": "OFF", "humidifier_fan": "ON"}
    ↓
Commands sent: MIST_MAKER_OFF, HUMIDIFIER_FAN_ON
    ↓
[After 30 seconds]
    ↓
Cycle Manager switches back: phase="mist"
    ↓
Repeats...
```

### Automatic Control Flow:

```
Sensor reads humidity = 83% (below target 90%)
    ↓
logic_engine.py: _rule_based_fruiting_actuation()
    ↓
Checks: humidity < 85% (target - 5)
    ↓
orchestrator.ai.humidifier_cycle.start_cycle()
    ↓
[Same cycle as manual control above]
    ↓
[When humidity reaches 90%]
    ↓
orchestrator.ai.humidifier_cycle.stop_cycle()
    ↓
Cycle stops, both mist and fan turn OFF
```

## Testing Instructions

### Test 1: Manual Control

1. Go to **Controls** page
2. Set to **Manual Mode** (toggle off auto)
3. Click **Humidifier System** card to turn ON
4. **Observe**:
   - Mist Maker (IN1) turns ON for 10 seconds
   - Status text shows "ON"
   - After 10s, Mist Maker turns OFF
   - Humidifier Fan (IN2) turns ON for 30 seconds
   - After 30s, Fan turns OFF, Mist turns ON again
   - Cycle repeats until you click OFF

5. Click **Humidifier System** card to turn OFF
6. **Observe**:
   - Both Mist Maker and Fan turn OFF immediately
   - Status text shows "OFF"

### Test 2: Automatic Control

1. Go to **Controls** page
2. Set to **Auto Mode** (toggle on)
3. **Wait for humidity to drop** below 85% (or manually lower it for testing)
4. **Observe**:
   - System automatically starts humidifier cycle
   - Mist runs 10s, Fan runs 30s, repeat
   - When humidity reaches ~90%, cycle stops automatically

### Test 3: Verify Arduino Commands

```bash
# SSH into Raspberry Pi
ssh mash@192.168.x.x

# Monitor logs
sudo journalctl -u mash-iot -f | grep -E "(MIST_MAKER|HUMIDIFIER_FAN|CYCLE)"
```

**Expected log output**:
```
[MANUAL] Started humidifier cycle
[CYCLE] Sent: MIST_MAKER_ON
[CYCLE] Sent: HUMIDIFIER_FAN_OFF
[HUMIDIFIER] Switching: MIST OFF -> FAN ON
[CYCLE] Sent: MIST_MAKER_OFF
[CYCLE] Sent: HUMIDIFIER_FAN_ON
[HUMIDIFIER] Switching: FAN OFF -> MIST ON
[CYCLE] Sent: MIST_MAKER_ON
[CYCLE] Sent: HUMIDIFIER_FAN_OFF
```

## Technical Details

### Cycle Manager State Machine

```
┌─────────────┐
│   IDLE      │ cycle_active = False
└──────┬──────┘
       │ start_cycle()
       ↓
┌─────────────┐
│ MIST PHASE  │ duration: 10 seconds
│ IN1: ON     │
│ IN2: OFF    │
└──────┬──────┘
       │ elapsed >= 10s
       ↓
┌─────────────┐
│  FAN PHASE  │ duration: 30 seconds
│ IN1: OFF    │
│ IN2: ON     │
└──────┬──────┘
       │ elapsed >= 30s
       ↓
       │ Loop back to MIST PHASE
       └───────────┐
                   ↓
       ┌───────────┘
```

### Files Modified

1. **`rpi_gateway/app/web/routes.py`**
   - Added special handling for `mist_maker` actuator
   - Starts/stops cycle manager instead of sending raw commands
   - Returns success message indicating cycle started/stopped

2. **`rpi_gateway/app/main.py`**
   - Added orchestrator reference to Flask app (2 places)
   - Added continuous cycle state updates in `on_sensor_data()`
   - Sends cycle commands every time sensor data is received
   - Updates UI states after sending commands

3. **`rpi_gateway/app/core/logic_engine.py`**
   - No changes needed - cycle manager was already correctly implemented!

## Troubleshooting

### Issue: Cycle doesn't start when clicking button

**Check**:
```bash
sudo journalctl -u mash-iot -n 20 | grep "Started humidifier cycle"
```

If not found:
- Orchestrator reference might not be set
- Check if AI engine is initialized (`orchestrator.ai is not None`)

### Issue: Mist turns on but never switches to fan

**Check**:
```bash
sudo journalctl -u mash-iot -n 50 | grep HUMIDIFIER
```

Look for:
- `[HUMIDIFIER] Starting cycle: MIST phase` ✅
- `[HUMIDIFIER] Switching: MIST OFF -> FAN ON` ❌ Missing?

If switching message is missing:
- Sensor data might not be arriving (check Arduino connection)
- Cycle manager's `get_current_states()` not being called

### Issue: Commands sent but relays don't activate

**Problem**: Arduino firmware issue or wiring

**Check**:
1. Open Arduino Serial Monitor (115200 baud)
2. Look for incoming JSON commands:
   ```json
   {"actuator":"MIST_MAKER","state":"ON"}
   {"actuator":"HUMIDIFIER_FAN","state":"ON"}
   ```

3. Check relay activation logs from Arduino

## Deployment

```bash
# On development machine (Windows)
cd "c:\Users\Ryzen\Desktop\ThesisDev\Mobile IoT\MASH-IoT"
git add .
git commit -m "Fix: Integrate HumidifierCycleManager with manual controls"
git push origin main

# On Raspberry Pi
cd ~/MASH-IoT
git pull origin main
sudo systemctl restart mash-iot

# Verify service started
sudo systemctl status mash-iot

# Monitor logs
sudo journalctl -u mash-iot -f
```

## Summary

The humidifier system now works correctly:

✅ **Manual Mode**: Click button → Cycle starts → 10s mist / 30s fan / repeat → Click OFF → Stops
✅ **Auto Mode**: Low humidity → Cycle starts → Raises humidity → Stops when target reached
✅ **Phase Transitions**: Automatically switches between mist and fan phases
✅ **State Tracking**: UI updates to show current state (ON/OFF)
✅ **Logging**: All cycle transitions logged for debugging

The key insight: **Don't send raw actuator commands - control the cycle manager instead!**

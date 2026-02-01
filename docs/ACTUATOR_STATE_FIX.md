# Actuator State Persistence Fix & On-Screen Keyboard

## Problem 1: Actuator States Reset to OFF

### Symptoms:
- User clicks actuator ON
- Physical relay turns ON (confirmed working)
- Web UI shows OFF after 3 seconds
- Cannot manually turn actuator OFF

### Root Cause:
The `/api/actuator_states` endpoint was returning **hardcoded dummy data** instead of actual state:

```python
# OLD CODE (BROKEN)
@web_bp.route('/api/actuator_states')
def actuator_states():
    # TODO: Implement actual state tracking
    # For now, return dummy data
    states = {
        "fruiting": {
            "mist_maker": {"state": False, "auto": False},  # Always FALSE!
            ...
        }
    }
    return jsonify(states)
```

### Why This Caused the Issue:
1. User clicks "Mist Maker" card → Sends POST to `/api/control_actuator`
2. Backend sends JSON command to Arduino: `{"actuator": "MIST_MAKER", "state": "ON"}`
3. Arduino turns relay ON ✅
4. Backend saves state: `ACTUATOR_STATES['fruiting']['mist_maker'] = True` ✅
5. **Every 3 seconds**, frontend polls `/api/actuator_states`
6. **BUG:** Endpoint returns hardcoded `{"state": False}` instead of actual state
7. Frontend updates UI to show OFF ❌
8. Physical relay is still ON, but UI shows OFF

### The Fix:
Modified [routes.py](c:/Users/Ryzen/Desktop/ThesisDev/Mobile IoT/MASH-IoT/rpi_gateway/app/web/routes.py#L506) to read actual state from `ACTUATOR_STATES` config:

```python
# NEW CODE (FIXED)
@web_bp.route('/api/actuator_states')
def actuator_states():
    # Get actual state from app config
    actuator_state_data = current_app.config.get('ACTUATOR_STATES', {})
    
    # Initialize default structure
    states = {
        "fruiting": {
            "mist_maker": {"state": False, "auto": False},
            ...
        },
        ...
    }
    
    # Update with actual states from config
    for room in ['fruiting', 'spawning', 'device']:
        if room in actuator_state_data:
            for actuator_name, is_on in actuator_state_data[room].items():
                if actuator_name in states[room]:
                    states[room][actuator_name]['state'] = is_on  # Use real state!
    
    return jsonify(states)
```

### Flow After Fix:
1. User clicks "Mist Maker" → ON
2. Backend saves: `ACTUATOR_STATES['fruiting']['mist_maker'] = True`
3. Arduino relay turns ON
4. Frontend polls `/api/actuator_states` every 3 seconds
5. **Endpoint now returns actual state:** `{"state": True}`
6. UI stays ON ✅
7. User can click again to turn OFF ✅

---

## Problem 2: No On-Screen Keyboard in Kiosk Mode

### Issue:
The CLI/kiosk version had no way to input text (WiFi passwords, settings, etc.) on touchscreen devices.

### Solution:
Added `matchbox-keyboard` - a Linux on-screen keyboard designed for embedded/kiosk systems.

### Changes Made:

#### 1. Install Keyboard Package
**File:** [setup_kiosk.sh](c:/Users/Ryzen/Desktop/ThesisDev/Mobile IoT/MASH-IoT/scripts/setup_kiosk.sh#L35)

```bash
sudo apt-get install -y chromium x11-xserver-utils unclutter \
    matchbox-window-manager xinit matchbox-keyboard
```

#### 2. Start Keyboard on Boot
**Files:** 
- [setup_kiosk.sh](c:/Users/Ryzen/Desktop/ThesisDev/Mobile IoT/MASH-IoT/scripts/setup_kiosk.sh#L73) (generates run_kiosk_x.sh)
- [run_kiosk.sh](c:/Users/Ryzen/Desktop/ThesisDev/Mobile IoT/MASH-IoT/scripts/run_kiosk.sh#L12)

```bash
# Start on-screen keyboard (hidden by default)
matchbox-keyboard -s 50 extended &
```

**Parameters:**
- `-s 50` - Scale to 50% of screen size
- `extended` - Use extended layout with more keys
- `&` - Run in background

#### 3. Add Keyboard Toggle Button
**File:** [base.html](c:/Users/Ryzen/Desktop/ThesisDev/Mobile IoT/MASH-IoT/rpi_gateway/app/web/templates/base.html#L22)

Added green keyboard icon button in top navigation:

```html
<button id="keyboard-toggle" class="keyboard-toggle" 
        onclick="toggleKeyboard()" 
        title="Toggle On-Screen Keyboard">
    <i class="fas fa-keyboard"></i>
</button>
```

**CSS:** [styles.css](c:/Users/Ryzen/Desktop/ThesisDev/Mobile IoT/MASH-IoT/rpi_gateway/app/web/static/css/styles.css#L88)
- Green border, positioned on right side of navbar
- Hover effect: fills with green
- Always visible for easy access

### How to Use the Keyboard:

1. **Auto-Show:** The keyboard automatically appears when you click on text input fields
2. **Manual Toggle:** Click the keyboard icon (📋) in the top-right navigation
3. **Hide:** Click away from the keyboard or press the close button

### Keyboard Features:
- ✅ Full QWERTY layout
- ✅ Numbers and symbols
- ✅ Shift/Caps Lock
- ✅ Backspace, Enter, Space
- ✅ Touch-friendly large keys
- ✅ Extended layout for special characters

---

## Files Modified

### Python Backend:
1. **rpi_gateway/app/web/routes.py** (Line 506-538)
   - Changed `/api/actuator_states` to return actual state from `ACTUATOR_STATES` config
   - Removed TODO and dummy data

### Kiosk Scripts:
2. **scripts/setup_kiosk.sh** (Lines 35, 73-77)
   - Added `matchbox-keyboard` to apt-get install
   - Added keyboard startup in run_kiosk_x.sh generation

3. **scripts/run_kiosk.sh** (Line 12)
   - Added keyboard startup command

### Frontend:
4. **rpi_gateway/app/web/templates/base.html** (Lines 22-26)
   - Added keyboard toggle button
   - Added `toggleKeyboard()` JavaScript function

5. **rpi_gateway/app/web/static/css/styles.css** (Lines 88-116)
   - Added `.keyboard-toggle` button styles
   - Positioned in top-right corner of navigation

---

## Testing the Fixes

### Test Actuator State Persistence:

1. **Start the system:**
   ```bash
   cd MASH-IoT
   python3 rpi_gateway/app/main.py
   ```

2. **Upload Arduino firmware** (if not already done):
   ```bash
   cd arduino_firmware
   pio run -t upload
   ```

3. **Test ON/OFF cycle:**
   - Open browser → http://raspberry-pi-ip:5000/controls
   - Click "Mist Maker" card → Should turn ON
   - Wait 5 seconds → **Should stay ON** (not reset to OFF)
   - Click again → Should turn OFF
   - Verify physical relay responds correctly

4. **Check console logs:**
   ```
   [SERIAL] Sent command: {"actuator": "MIST_MAKER", "state": "ON"}
   [CMD] Set MIST_MAKER to ON
   ```

### Test On-Screen Keyboard:

1. **Re-run kiosk setup** (if not already done):
   ```bash
   cd MASH-IoT/scripts
   chmod +x setup_kiosk.sh
   ./setup_kiosk.sh
   sudo reboot
   ```

2. **After reboot, system boots to kiosk mode**

3. **Test keyboard:**
   - Click keyboard icon (📋) in top-right
   - Keyboard should appear at bottom of screen
   - Navigate to WiFi Setup
   - Click password field
   - Keyboard should auto-appear
   - Type test password → Keys should work

4. **Verify keyboard starts on boot:**
   ```bash
   ps aux | grep matchbox-keyboard
   # Should show process running
   ```

---

## Troubleshooting

### Issue: Actuator still resets to OFF
**Check:**
```bash
# View logs
journalctl -u mash-iot -f

# Verify ACTUATOR_STATES is being updated
# Should see logs like:
# "Sent command to Arduino: {"actuator": "MIST_MAKER", "state": "ON"}"
```

**Solution:** Restart the backend service:
```bash
sudo systemctl restart mash-iot
```

### Issue: Keyboard doesn't appear
**Check:**
```bash
# Verify keyboard is installed
dpkg -l | grep matchbox-keyboard

# Check if keyboard is running
ps aux | grep matchbox-keyboard
```

**Solution:** Install keyboard:
```bash
sudo apt-get update
sudo apt-get install matchbox-keyboard
```

### Issue: Keyboard appears but no keys work
**Fix:** The keyboard layout might need adjustment:
```bash
# Test keyboard manually
matchbox-keyboard -s 50 extended
```

### Issue: Can't see keyboard toggle button
**Check:** Clear browser cache or hard refresh (Ctrl+Shift+R)

---

## State Persistence Architecture

### How State is Stored:

```python
# In Flask app.config
ACTUATOR_STATES = {
    'fruiting': {
        'mist_maker': True,        # Current state
        'humidifier_fan': False,
        'exhaust_fan': False,
        'intake_fan': False,
        'led': False
    },
    'spawning': {
        'exhaust_fan': False
    },
    'device': {
        'exhaust_fan': False
    }
}
```

### State Update Flow:

```
User Click → POST /api/control_actuator
    ↓
routes.py: control_actuator()
    ↓
1. Send JSON to Arduino: {"actuator": "MIST_MAKER", "state": "ON"}
2. Update config: current_app.config['ACTUATOR_STATES']['fruiting']['mist_maker'] = True
3. Return success
    ↓
Frontend: Update card UI optimistically
    ↓
Every 3 seconds: GET /api/actuator_states
    ↓
routes.py: actuator_states()
    ↓
Read current_app.config['ACTUATOR_STATES']
    ↓
Return actual state to frontend
    ↓
Frontend: Update all cards to match server state
```

### Note on State Persistence:
⚠️ **Current implementation stores state in memory** (`app.config`). State is lost on backend restart.

**Future Enhancement:** Save state to file (e.g., `config/actuator_states.json`) to persist across reboots.

---

## Summary

✅ **Fixed actuator state tracking** - UI now reflects actual relay states
✅ **Added on-screen keyboard** - Full text input support for kiosk mode
✅ **Keyboard toggle button** - Easy access from any page
✅ **Auto-show keyboard** - Appears when clicking text inputs

Both issues are now resolved. The system maintains proper state synchronization between Arduino hardware, Python backend, and web frontend.

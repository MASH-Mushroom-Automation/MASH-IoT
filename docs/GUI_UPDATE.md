# M.A.S.H. IoT - GUI & Auto Control Update Documentation

## Overview
This update introduces a modern grid card UI for actuator controls, automatic control modes, passive fan timing, and future multiplexer support.

---

## 1. Grid Card Toggle UI ✅

### What Changed
Replaced traditional toggle switches with **interactive grid cards** that act as full toggle buttons.

### Features
- **Click entire card to toggle** - No more tiny switches
- **Visual feedback** - Cards change color when ON (green gradient)
- **Status badges** - Shows AUTO/TIMED/FLUSH modes
- **Voltage indicators** - Display power requirements (5V, 12V, 24V, 45V)
- **Room organization** - Separate sections for Fruiting, Spawning, Device rooms
- **Responsive grid** - Auto-adjusts to screen size

### Files Modified
- [templates/controls.html](rpi_gateway/app/web/templates/controls.html) - New grid card HTML structure
- [static/css/styles.css](rpi_gateway/app/web/static/css/styles.css) - Grid card styles with animations
- [static/js/controls.js](rpi_gateway/app/web/static/js/controls.js) - NEW: Card click handling & status polling

### Visual Design

```
┌─────────────────────────────────────────────────┐
│ ■ Automatic Control  [Toggle]                  │
│ Auto mode handles timed intervals and sensors   │
└─────────────────────────────────────────────────┘

Fruiting Room
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│  💧    │ │  🌀    │ │  💨    │ │  💨    │ │  💡    │
│ Mist   │ │ Hum    │ │Exhaust │ │Intake  │ │ LED    │
│ Maker  │ │ Fan    │ │  Fan   │ │  Fan   │ │Lights  │
│ 45V    │ │ 12V    │ │  24V   │ │  12V   │ │  5V    │
│  OFF   │ │  OFF   │ │  OFF   │ │  OFF   │ │  ON    │
│        │ │        │ │        │ │        │ │🤖 TIMED│
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

---

## 2. Auto Control System ✅

### Master Auto/Manual Toggle
Located at top of controls page:
- **Auto Mode ON** → All cards disabled for manual control, automation runs
- **Manual Mode ON** → Full manual control, auto timers paused

### Auto Control Indicators
Cards show badges when under automatic control:
- **🤖 AUTO** - Sensor-based automation (humidity, CO2 triggers)
- **🕐 TIMED** - Clock/interval-based control (passive fans, LED schedule)
- **⚡ FLUSH** - Emergency override mode (high CO2)

### API Endpoints
#### Toggle Auto Mode
```http
POST /api/set_auto_mode
Content-Type: application/json

{
  "enabled": true
}
```

#### Get Actuator States
```http
GET /api/actuator_states

Response:
{
  "fruiting": {
    "mist_maker": {"state": false, "auto": false},
    "exhaust_fan": {"state": true, "auto": true}
  },
  "spawning": {
    "exhaust_fan": {"state": true, "auto": true, "mode": "flush"}
  }
}
```

---

## 3. Passive Fan Controller ✅

### Purpose
Handles timed exhaust fans for rooms without active sensors (spawning/device).

### Module
[passive_fan_controller.py](rpi_gateway/app/core/passive_fan_controller.py)

### Configuration (config.yaml)
```yaml
passive_fans:
  spawning_exhaust:
    enabled: true
    interval_minutes: 30      # Run every 30 minutes
    duration_seconds: 120     # Run for 2 minutes
    flush_mode:               # Override passive timing
      enabled: true
      co2_trigger: 2000       # Trigger when CO2 > 2000 ppm
      duration_seconds: 300   # Flush for 5 minutes
  
  device_exhaust:
    enabled: true
    mode: "clock"             # Options: "interval" or "clock"
    schedule:                 # Run at specific times
      - "08:00"
      - "12:00"
      - "16:00"
      - "20:00"
    duration_seconds: 180     # Run for 3 minutes
```

### Operation Modes

#### 1. Interval Mode (Spawning)
- Runs fan every X minutes
- Example: Every 30 min → ON for 2 min → OFF until next cycle
- **Passive operation** for stable CO2 environments

#### 2. Clock Mode (Device)
- Runs fan at scheduled times
- Example: 8 AM, 12 PM, 4 PM, 8 PM
- **Predictable cooling** for device room

#### 3. Flush Mode (Spawning Override)
- **Triggered by sensor**: CO2 > threshold
- **Bypasses interval timing**
- Runs continuously until CO2 drops or timeout
- Visual indicator: **⚡ FLUSH** badge (animated)

### Usage Example
```python
from app.core.passive_fan_controller import PassiveFanController

# Initialize with config and actuator callback
controller = PassiveFanController(config, actuator_control_func)

# Start background thread
controller.start()

# Trigger flush mode manually
controller.trigger_flush('spawning', {'co2': 2500, 'temp': 25, 'humidity': 90})

# Get status
status = controller.get_status()
# Returns: {'spawning_exhaust': {'enabled': True, 'flush_mode': True, ...}}
```

---

## 4. Multiplexer Support (Future-Ready) ✅

### Problem
Current setup uses:
- **Sensor 1 (Fruiting)**: Hardware I2C (A4/A5) via Grove Base Shield
- **Sensor 2 (Spawning)**: Software I2C (D10/D11) - less reliable, GPIO-hungry

### Solution
Use **TCA9548A I2C Multiplexer** to connect both sensors to Hardware I2C.

### Implementation Status
🟡 **Code Ready** - Multiplexer support added with automatic fallback  
🔴 **Hardware Pending** - TCA9548A not connected yet

### How It Works
#### Current Mode (SoftWire)
```cpp
// sensors.cpp
SoftWire softWire(SOFTWARE_SDA_PIN, SOFTWARE_SCL_PIN);  // D10/D11
SensirionI2CScd4x scd41_spawning;
```

#### Future Mode (Multiplexer)
```cpp
// Uncomment this when TCA9548A is connected:
#define USE_MULTIPLEXER

// Code will:
// 1. Detect multiplexer at 0x70
// 2. Switch MUX channels to read each sensor
// 3. Fall back to SoftWire if MUX not found
```

### Wiring (Future)
```
Raspberry Pi / Arduino
       |
   Hardware I2C (A4/A5)
       |
   TCA9548A Multiplexer (0x70)
       ├─ Channel 0 → SCD41 Fruiting
       ├─ Channel 1 → SCD41 Spawning
       └─ Channels 2-7 → (Available)
```

### Enabling Multiplexer
1. Connect TCA9548A to Arduino (A4/A5)
2. Connect both SCD41 sensors to multiplexer
3. Open `arduino_firmware/src/sensors.cpp`
4. **Uncomment**: `#define USE_MULTIPLEXER`
5. Upload firmware

**Fallback Guarantee**: If multiplexer not detected, system automatically uses SoftWire mode.

### Benefits
✅ Both sensors on reliable Hardware I2C  
✅ Frees up GPIO pins (D10/D11)  
✅ Up to 8 sensors supported (expansion)  
✅ No code changes needed - just hardware swap

---

## 5. Updated Actuator Mappings

### Arduino Firmware Names → Web UI Names

| Arduino Command | Web UI Name | Room |
|----------------|-------------|------|
| `MIST_MAKER` | `mist_maker` | Fruiting |
| `HUMIDIFIER_FAN` | `humidifier_fan` | Fruiting |
| `FRUITING_EXHAUST_FAN` | `exhaust_fan` | Fruiting |
| `FRUITING_INTAKE_FAN` | `intake_fan` | Fruiting |
| `SPAWNING_EXHAUST_FAN` | `exhaust_fan` | Spawning |
| `DEVICE_EXHAUST_FAN` | `exhaust_fan` | Device |
| `FRUITING_LED` | `led` | Fruiting |

### Command Format (Arduino)
```json
{"actuator": "MIST_MAKER", "state": "ON"}
{"actuator": "SPAWNING_EXHAUST_FAN", "state": "OFF"}
```

### API Call Format (Web UI)
```json
{"room": "fruiting", "actuator": "mist_maker", "state": "ON"}
{"room": "spawning", "actuator": "exhaust_fan", "state": "OFF"}
```

---

## 6. File Structure

```
rpi_gateway/
├── app/
│   ├── core/
│   │   ├── passive_fan_controller.py  ← NEW: Passive fan timing
│   │   ├── logic_engine.py
│   │   └── serial_comm.py
│   ├── web/
│   │   ├── routes.py                  ← UPDATED: New API endpoints
│   │   ├── static/
│   │   │   ├── css/
│   │   │   │   └── styles.css         ← UPDATED: Grid card styles
│   │   │   └── js/
│   │   │       ├── main.js
│   │   │       └── controls.js        ← NEW: Card toggle logic
│   │   └── templates/
│   │       └── controls.html          ← UPDATED: Grid card UI
│   └── config/
│       └── config.yaml                ← UPDATED: Passive fan config

arduino_firmware/
└── src/
    ├── sensors.cpp                    ← UPDATED: Multiplexer support
    └── sensors.h                      ← UPDATED: MUX function declarations
```

---

## 7. Testing Checklist

### UI Testing
- [ ] Open `/controls` page in browser
- [ ] Toggle auto mode switch (cards should disable)
- [ ] Click each actuator card (should toggle ON/OFF)
- [ ] Verify status badges appear (AUTO/TIMED)
- [ ] Check responsive layout on mobile

### Backend Testing
```bash
# Test auto mode API
curl -X POST http://localhost:5000/api/set_auto_mode \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'

# Test actuator control
curl -X POST http://localhost:5000/api/control_actuator \
  -H "Content-Type: application/json" \
  -d '{"room":"fruiting","actuator":"mist_maker","state":"ON"}'

# Get actuator states
curl http://localhost:5000/api/actuator_states
```

### Passive Fan Testing
```python
# In Python console
from app.core.passive_fan_controller import PassiveFanController
from app.core.logic_engine import config

def test_actuator(room, actuator, state):
    print(f"{room} {actuator} → {state}")

controller = PassiveFanController(config, test_actuator)
controller.start()

# Wait 30 minutes and verify spawning fan runs
# Check device fan runs at scheduled times
```

### Arduino Testing (Multiplexer)
```cpp
// Upload firmware WITHOUT #define USE_MULTIPLEXER
// Verify: "[OK] Spawning sensor initialized (Software I2C)"

// Uncomment #define USE_MULTIPLEXER and re-upload
// WITHOUT TCA9548A connected:
// Verify: "[WARN] Multiplexer not detected, falling back to SoftWire mode"

// WITH TCA9548A connected:
// Verify: "[OK] TCA9548A multiplexer detected!"
// Verify: "[OK] Both sensors initialized via multiplexer"
```

---

## 8. Migration Notes

### From Old to New UI
**Old**: Toggle switches with labels  
**New**: Grid cards (full-card click)

**Old**: Manual control only  
**New**: Auto/Manual mode toggle

**Old**: No passive fan support  
**New**: Timed interval & clock-based fans

### Backward Compatibility
✅ Arduino firmware unchanged (except multiplexer prep)  
✅ Old routes still work (`/api/control_actuator`)  
✅ Config fallbacks to defaults if keys missing

---

## 9. Known Limitations

1. **Actuator State Persistence**
   - Current: States reset on RPi reboot
   - Future: Store in SQLite database

2. **Passive Fan Collision**
   - If manual command sent during passive run, may cause conflict
   - Future: Add mutex locks

3. **Multiplexer Sensor Reading**
   - Multiplexer adds ~10ms delay per sensor
   - Not an issue for 5-second read intervals

---

## 10. Future Enhancements

### Phase 2
- [ ] Actuator state history chart
- [ ] Customizable passive fan schedules (Web UI)
- [ ] Mobile app notifications (flush mode triggered)

### Phase 3
- [ ] Voice control integration (Alexa/Google Home)
- [ ] Multi-user access control
- [ ] Energy consumption tracking (relay ON time)

---

## Summary

✅ **Grid Card UI** - Modern, touch-friendly controls  
✅ **Auto Control** - Toggle between manual/automatic modes  
✅ **Passive Fans** - Interval & clock-based exhaust control  
✅ **Flush Mode** - Emergency CO2 override for spawning room  
✅ **Multiplexer Ready** - Easy upgrade path for dual sensors  
✅ **3-Room Support** - Fruiting, Spawning, Device rooms  

**Next Steps**: Test UI, integrate passive fan controller into main orchestrator, order TCA9548A multiplexer!

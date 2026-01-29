# Quick Integration Guide - Passive Fan Controller

## How to Integrate Passive Fan Controller into Main Orchestrator

### Step 1: Update main.py

```python
# rpi_gateway/app/main.py

from app.core.passive_fan_controller import PassiveFanController

# In your orchestrator setup:
def setup_orchestrator():
    # ... existing setup ...
    
    # Initialize passive fan controller
    passive_controller = PassiveFanController(
        config=config,
        actuator_callback=lambda room, actuator, state: serial_comm.control_actuator(room, actuator, state)
    )
    
    # Start background thread
    passive_controller.start()
    
    # Store in Flask app context
    app.passive_controller = passive_controller
    
    return passive_controller
```

### Step 2: Integrate Flush Mode with Sensor Loop

```python
# In your sensor reading loop:

def process_sensor_data(sensor_data):
    # ... existing processing ...
    
    # Check if spawning needs flush mode
    if 'spawning' in sensor_data:
        spawning_data = sensor_data['spawning']
        
        # Trigger flush check
        passive_controller = app.passive_controller
        if passive_controller:
            passive_controller.trigger_flush('spawning', spawning_data)
```

### Step 3: Update Serial Communication

Make sure your serial_comm module has the control method:

```python
# app/core/serial_comm.py

def control_actuator(self, room: str, actuator: str, state: str) -> bool:
    """
    Send actuator control command to Arduino.
    
    Args:
        room: 'fruiting', 'spawning', or 'device'
        actuator: 'exhaust_fan', 'mist_maker', etc.
        state: 'ON' or 'OFF'
    """
    # Map to Arduino command names
    actuator_map = {
        ('fruiting', 'mist_maker'): 'MIST_MAKER',
        ('fruiting', 'humidifier_fan'): 'HUMIDIFIER_FAN',
        ('fruiting', 'exhaust_fan'): 'FRUITING_EXHAUST_FAN',
        ('fruiting', 'intake_fan'): 'FRUITING_INTAKE_FAN',
        ('fruiting', 'led'): 'FRUITING_LED',
        ('spawning', 'exhaust_fan'): 'SPAWNING_EXHAUST_FAN',
        ('device', 'exhaust_fan'): 'DEVICE_EXHAUST_FAN'
    }
    
    arduino_cmd = actuator_map.get((room, actuator))
    if not arduino_cmd:
        logger.error(f"Unknown actuator: {room}/{actuator}")
        return False
    
    command = f'{{"actuator":"{arduino_cmd}","state":"{state}"}}\n'
    return self.send_command(command)
```

### Step 4: Test It!

```bash
# Start the RPi gateway
cd rpi_gateway
python -m app.main

# You should see in logs:
# [INFO] Passive fan controller started
# [INFO] Starting spawning exhaust fan (first run)
# [INFO] Starting device exhaust fan (scheduled: 08:00)
```

### Step 5: Monitor Flush Mode

Watch for high CO2 in spawning room:
```
[WARN] FLUSH MODE TRIGGERED: Spawning CO2 = 2100 ppm > 2000 ppm
[INFO] Spawning exhaust_fan → ON
[INFO] Flush mode ended: CO2 = 1850 ppm
[INFO] Spawning exhaust_fan → OFF
```

---

## Config Example

```yaml
# config/config.yaml

system:
  auto_mode: true

passive_fans:
  spawning_exhaust:
    enabled: true
    interval_minutes: 30
    duration_seconds: 120
    flush_mode:
      enabled: true
      co2_trigger: 2000
      duration_seconds: 300
  
  device_exhaust:
    enabled: true
    mode: "clock"
    schedule: ["08:00", "12:00", "16:00", "20:00"]
    duration_seconds: 180
```

---

## Troubleshooting

**Problem**: Fans not running on schedule  
**Solution**: Check `passive_controller.get_status()` - verify last_run and next_run times

**Problem**: Flush mode not triggering  
**Solution**: Verify sensor data includes CO2 value and config has flush_mode.enabled = true

**Problem**: Manual control overrides passive timing  
**Solution**: Expected behavior when auto_mode = false. Toggle auto mode in UI.

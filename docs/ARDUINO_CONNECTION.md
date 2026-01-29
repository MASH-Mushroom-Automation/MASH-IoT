# M.A.S.H. IoT - Arduino Connection Guide

## Hardware Setup

### Multiplexer Configuration
You now have the TCA9548A I2C multiplexer connected:

**Multiplexer → Arduino:**
- SDA → Pin A4
- SCL → Pin A5  
- VIN → 5V
- GND → GND

**Sensors → Multiplexer:**
- Fruiting Room SCD41 → SD0/SC0 (Channel 0)
- Spawning Room SCD41 → SD1/SC1 (Channel 1)

**Power:**
- Both sensors' VIN/GND connected to multiplexer VIN/GND ✓

### Arduino Firmware
The firmware **auto-detects** the multiplexer:
- If TCA9548A detected → Uses Hardware I2C only
- If not detected → Falls back to SoftWire mode

**Enable multiplexer mode** in `arduino_firmware/src/sensors.cpp`:
```cpp
#define USE_MULTIPLEXER  // Line 22 - NOW ENABLED
```

## Raspberry Pi Connection

### Auto-Detection (Recommended)
The RPi gateway **automatically finds** the Arduino USB port:

```python
# In rpi_gateway/app/main.py - already configured!
arduino = ArduinoSerialComm(auto_reconnect=True)
arduino.connect(auto_detect=True)  # Scans for Arduino
```

### Find Arduino Port Manually
```bash
# Method 1: Using our script
python3 scripts/find_arduino.py

# Method 2: Linux command
ls -l /dev/ttyACM* /dev/ttyUSB*

# Method 3: Watch kernel messages
dmesg | grep -i "tty"
```

## Auto-Reconnect Feature

The system **automatically reconnects** if Arduino disconnects:

- **Detection:** Checks connection every loop cycle
- **Retry interval:** 5 seconds
- **Logs:** `[SERIAL] Connection lost. Attempting to reconnect...`

**Test it:** Unplug Arduino while system is running → It will reconnect when you plug it back in!

## Using Room-Specific Data

### In Your Code
```python
from app.core.serial_comm import ArduinoSerialComm

# Initialize connection
arduino = ArduinoSerialComm(auto_reconnect=True)
arduino.connect(auto_detect=True)

# Get data for specific rooms
fruiting = arduino.get_fruiting_room_data()
# Returns: {'temp': 23.5, 'humidity': 85.0, 'co2': 800}

spawning = arduino.get_spawning_room_data()  
# Returns: {'temp': 24.0, 'humidity': 90.0, 'co2': 1200}

# Check connection status
if arduino.is_arduino_connected():
    print("Arduino is online")
```

### In Flask Routes (Web UI)
```python
from flask import Blueprint, jsonify

@web_bp.route('/api/sensors/fruiting')
def get_fruiting_sensors():
    arduino = current_app.serial_comm
    data = arduino.get_fruiting_room_data()
    
    if data:
        return jsonify({
            'temperature': data['temp'],
            'humidity': data['humidity'],
            'co2': data['co2']
        })
    else:
        return jsonify({'error': 'No data available'}), 503

@web_bp.route('/api/sensors/spawning')
def get_spawning_sensors():
    arduino = current_app.serial_comm
    data = arduino.get_spawning_room_data()
    
    if data:
        return jsonify({
            'temperature': data['temp'],
            'humidity': data['humidity'],
            'co2': data['co2']
        })
    else:
        return jsonify({'error': 'No data available'}), 503
```

### In Logic Engine (Automation)
```python
def check_fruiting_conditions(arduino):
    """Check if fruiting room needs intervention."""
    data = arduino.get_fruiting_room_data()
    
    if not data:
        return []  # No commands if no data
    
    commands = []
    
    # CO2 control
    if data['co2'] > 900:
        commands.append('FRUITING_EXHAUST_FAN_ON')
    elif data['co2'] < 700:
        commands.append('FRUITING_EXHAUST_FAN_OFF')
    
    # Humidity control
    if data['humidity'] < 85:
        commands.append('HUMIDIFIER_ON')
    elif data['humidity'] > 95:
        commands.append('HUMIDIFIER_OFF')
    
    return commands
```

## Testing Connection

### Quick Test
```bash
# Test connection and view live data
python3 scripts/test_arduino.py
```

**Output:**
```
[Packet #1] Received at 14:32:05
----------------------------------------
🍄 Fruiting Room:
   Temperature: 23.5°C
   Humidity:    85.0%
   CO2:         800 ppm

🌱 Spawning Room:
   Temperature: 24.0°C
   Humidity:    90.0%
   CO2:         1200 ppm
----------------------------------------

[Status Check] 🟢 CONNECTED
```

### Monitor System Logs
```bash
# View backend logs (includes serial communication)
journalctl -u mash-iot -f

# Filter only Arduino messages
journalctl -u mash-iot -f | grep SERIAL
```

## Kiosk Mode (Boot to Dashboard)

### Setup (One-Time)
```bash
# Run setup script
bash scripts/setup_kiosk.sh

# Reboot
sudo reboot
```

**What happens:**
1. RPi boots to **console** (no desktop loaded)
2. M.A.S.H. backend starts automatically
3. X server launches **only Chromium** in fullscreen
4. Dashboard opens at `http://localhost:5000`

**No desktop = Faster boot + Lower memory usage!**

### Control Services
```bash
# Backend
sudo systemctl start mash-iot      # Start
sudo systemctl stop mash-iot       # Stop
sudo systemctl status mash-iot     # Check status

# Kiosk
sudo systemctl start mash-kiosk    # Start kiosk
sudo systemctl stop mash-kiosk     # Stop kiosk

# Logs
journalctl -u mash-iot -f          # Backend logs
journalctl -u mash-kiosk -f        # Kiosk logs
```

### Exit Kiosk Mode
**During operation:** Press `Alt+F4` to close Chromium

**Disable kiosk:**
```bash
sudo systemctl disable mash-kiosk
sudo reboot
```

## Troubleshooting

### Arduino Not Detected
```bash
# 1. Scan for Arduino
python3 scripts/find_arduino.py

# 2. Check permissions
sudo usermod -a -G dialout $USER
# Then logout and login

# 3. Check USB connection
dmesg | tail -20
# Should show: "ttyACM0: USB ACM device"

# 4. Test with screen
screen /dev/ttyACM0 9600
# Press Ctrl+A then K to exit
```

### Connection Keeps Dropping
- **Bad USB cable:** Try a different cable (data, not power-only)
- **Power issue:** Use powered USB hub if Arduino restarts
- **Interference:** Keep USB cable away from relay module

### No Data from Sensors
```bash
# Upload firmware
cd arduino_firmware
pio run -t upload

# Monitor serial output
pio device monitor

# Should see JSON every 5 seconds:
# {"fruiting": {"temp": 23.5, "humidity": 85, "co2": 800}}
```

### Kiosk Not Starting
```bash
# Check if backend is running
sudo systemctl status mash-iot

# Check if backend is accessible
curl http://localhost:5000

# Check kiosk service
sudo systemctl status mash-kiosk

# View errors
journalctl -u mash-kiosk -n 50
```

### Dashboard Not Loading
```bash
# Check Flask is running
ps aux | grep python

# Check port 5000
sudo netstat -tlnp | grep 5000

# Test locally
curl http://localhost:5000

# Check firewall (if accessing remotely)
sudo ufw allow 5000
```

## Serial Communication Protocol

### Arduino → Raspberry Pi (JSON)
```json
{
  "fruiting": {
    "temp": 23.5,
    "humidity": 85.0,
    "co2": 800
  },
  "spawning": {
    "temp": 24.0,
    "humidity": 90.0,
    "co2": 1200
  },
  "timestamp": 1738291200
}
```

### Raspberry Pi → Arduino (Plain Text)
```
FRUITING_EXHAUST_FAN_ON\n
HUMIDIFIER_OFF\n
FRUITING_LED_ON\n
```

**Available Commands:**
- `FRUITING_EXHAUST_FAN_ON/OFF`
- `FRUITING_BLOWER_FAN_ON/OFF`
- `HUMIDIFIER_FAN_ON/OFF`
- `HUMIDIFIER_ON/OFF`
- `FRUITING_LED_ON/OFF`
- `SPAWNING_EXHAUST_FAN_ON/OFF`

## Connection Status API

### Check Connection in Code
```python
if arduino.is_arduino_connected():
    # Arduino is online
    data = arduino.get_fruiting_room_data()
else:
    # Arduino is offline (will auto-reconnect)
    print("Waiting for Arduino to reconnect...")
```

### Web UI Status Endpoint
```python
@web_bp.route('/api/status')
def system_status():
    arduino = current_app.serial_comm
    
    return jsonify({
        'arduino_connected': arduino.is_arduino_connected(),
        'port': arduino.port,
        'auto_reconnect': arduino.auto_reconnect,
        'last_data_time': arduino.latest_data.get('timestamp')
    })
```

## Quick Reference

| Task | Command |
|------|---------|
| Find Arduino port | `python3 scripts/find_arduino.py` |
| Test connection | `python3 scripts/test_arduino.py` |
| Upload firmware | `cd arduino_firmware && pio run -t upload` |
| Setup kiosk | `bash scripts/setup_kiosk.sh` |
| View backend logs | `journalctl -u mash-iot -f` |
| Start backend | `python3 -m app.main` (from rpi_gateway/) |
| Access dashboard | `http://localhost:5000` |

## Next Steps

1. ✅ Connect multiplexer to Arduino (SDA→A4, SCL→A5)
2. ✅ Upload firmware with `#define USE_MULTIPLEXER`
3. ✅ Run `python3 scripts/find_arduino.py` on RPi
4. ✅ Run `python3 scripts/test_arduino.py` to verify
5. ✅ Setup kiosk mode: `bash scripts/setup_kiosk.sh`
6. ✅ Reboot: `sudo reboot`

Your system will now auto-detect Arduino, auto-reconnect if disconnected, and boot directly to the dashboard!

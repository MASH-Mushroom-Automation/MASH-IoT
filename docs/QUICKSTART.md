# M.A.S.H. IoT - Quick Start Guide

## Prerequisites
- Arduino Uno R3 with firmware uploaded
- Raspberry Pi (or development machine)
- Python 3.7+
- USB cable connecting Arduino to RPi

## Installation

### 1. Install Python Dependencies
```bash
cd rpi_gateway
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Edit `rpi_gateway/config/.env` and set your backend API key:
```env
BACKEND_URL=https://api.mashmarket.app
BACKEND_API_KEY=your_actual_api_key_here
DEVICE_ID=rpi_gateway_001
DEVICE_NAME=MASH IoT Gateway
```

### 3. Review Configuration
Check `rpi_gateway/config/config.yaml` - defaults should work for most setups.

## Running the System

### Start the Gateway
```bash
cd rpi_gateway
python -m app.main
```

You should see:
```
==================================================
  M.A.S.H. IoT System Starting
  Mushroom Automation Smart Home
==================================================
[SERIAL] Using port: COM3
[BACKEND] API client initialized
[CONFIG] Loaded configuration from config/config.yaml
[BACKEND] Device registered: rpi_gateway_001
[SERIAL] Connected to Arduino on COM3 at 9600 baud
[WEB] Starting Flask server on 0.0.0.0:5000
[WEB] Access dashboard at: http://0.0.0.0:5000/dashboard
```

### Access the Web Dashboard
Open your browser and navigate to:
```
http://localhost:5000/dashboard
```

## Testing Checklist

### ✅ Arduino Communication
1. Check logs for "Connected to Arduino"
2. Verify sensor data appears every 5 seconds:
   ```
   [DATA] Received sensor data at 1738123456.789
   ```
3. Dashboard should show live readings

### ✅ Manual Control
1. Navigate to Controls page: `http://localhost:5000/controls`
2. Toggle any actuator switch
3. Check Arduino serial monitor for relay activation
4. Verify relay clicks (if hardware connected)

### ✅ Backend Integration
1. Check logs for "Device registered"
2. Dashboard status bar should show:
   - Arduino: Connected (green)
   - Backend: Online (green)
3. Sensor data uploads every 5 seconds (check logs)

## Troubleshooting

### Arduino Not Connecting
**Issue:** `[SERIAL] Connection failed`

**Solutions:**
1. Check USB cable connection
2. Verify correct COM port:
   - Windows: Check Device Manager → Ports (COM & LPT)
   - Linux: Run `ls /dev/tty*` to find `/dev/ttyACM0`
3. Update port in code or config if needed
4. Ensure Arduino firmware is uploaded

### Backend Offline
**Issue:** `Backend: Offline` in dashboard

**Solutions:**
1. Check internet connection
2. Verify `BACKEND_URL` in `.env`
3. Test backend health:
   ```bash
   curl https://api.mashmarket.app/health
   ```
4. Check `BACKEND_API_KEY` is set correctly
5. System works offline - data syncs when connection restores

### Sensor Data Not Showing
**Issue:** Dashboard shows zeros or "No Data"

**Solutions:**
1. Check Arduino serial monitor for JSON output:
   ```
   pio device monitor
   ```
2. Should see:
   ```json
   {"fruiting":{"temp":23.5,"humidity":85.1,"co2":850}}
   ```
3. If not, reflash Arduino firmware:
   ```bash
   cd arduino_firmware
   pio run -t upload
   ```

### Actuators Not Responding
**Issue:** Switches toggle but relays don't activate

**Possible Causes:**
1. **Demo Mode**: Arduino not connected - UI works but no hardware control
2. **Wiring**: Check relay module connections to Arduino pins
3. **Power**: Ensure relay module has external 5V power supply
4. **Firmware**: Verify actuator pins match hardware setup

**Debug:**
```python
# In Python shell or add to routes.py
from app.core.serial_comm import ArduinoSerialComm
arduino = ArduinoSerialComm(port='COM3')
arduino.connect()
arduino.control_actuator('fruiting', 'exhaust_fan', 'ON')
```

## Port Configuration

### Windows
Default: `COM3`
- Check Device Manager if different
- Update in `app/main.py` line 54 if needed

### Linux/Raspberry Pi
Default: `/dev/ttyACM0`
- May be `/dev/ttyUSB0` with some USB adapters
- Check with: `ls -l /dev/tty*`

### Manual Override
Edit `rpi_gateway/app/main.py`:
```python
arduino_port = 'COM5'  # Your specific port
```

## API Endpoints

Test individual endpoints:

### Get Latest Sensor Data
```bash
curl http://localhost:5000/api/latest_data
```

Response:
```json
{
  "fruiting_data": {"temp": 23.5, "humidity": 88.2, "co2": 950.7},
  "arduino_connected": true,
  "backend_connected": true
}
```

### Control Actuator
```bash
curl -X POST http://localhost:5000/api/control_actuator \
  -H "Content-Type: application/json" \
  -d '{"room": "fruiting", "actuator": "exhaust_fan", "state": "ON"}'
```

Response:
```json
{
  "status": "success",
  "room": "fruiting",
  "actuator": "exhaust_fan",
  "state": "ON"
}
```

## Development Mode

Run with debug enabled:
```python
# In main.py, change:
orchestrator.start(host='0.0.0.0', port=5000, debug=True)
```

Benefits:
- Auto-reload on file changes
- Detailed error traces
- Interactive debugger

⚠️ **Warning:** Never use debug mode in production!

## Production Deployment

### Using Systemd (Linux)
1. Create service file: `/etc/systemd/system/mash-iot.service`
```ini
[Unit]
Description=M.A.S.H. IoT Gateway
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/MASH-IoT/rpi_gateway
ExecStart=/usr/bin/python3 -m app.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Enable and start:
```bash
sudo systemctl enable mash-iot
sudo systemctl start mash-iot
sudo systemctl status mash-iot
```

### View Logs
```bash
sudo journalctl -u mash-iot -f
```

## Arduino Command Reference

### Supported Commands
```
SPAWNING_EXHAUST_FAN_ON
SPAWNING_EXHAUST_FAN_OFF
FRUITING_EXHAUST_FAN_ON
FRUITING_EXHAUST_FAN_OFF
FRUITING_BLOWER_FAN_ON
FRUITING_BLOWER_FAN_OFF
HUMIDIFIER_FAN_ON
HUMIDIFIER_FAN_OFF
HUMIDIFIER_ON
HUMIDIFIER_OFF
FRUITING_LED_ON
FRUITING_LED_OFF
```

### Test Commands via Serial Monitor
In Arduino IDE or PlatformIO serial monitor, type:
```
FRUITING_LED_ON
```
Press Enter. LED should turn on.

## File Structure Reference
```
rpi_gateway/
├── app/
│   ├── main.py                 # Main orchestrator (START HERE)
│   ├── core/
│   │   ├── serial_comm.py      # Arduino communication
│   │   └── logic_engine.py     # Automation logic
│   ├── cloud/
│   │   ├── backend_api.py      # Backend API client (NEW)
│   │   └── firebase.py         # Firebase integration
│   ├── database/
│   │   └── db_manager.py       # SQLite operations
│   └── web/
│       ├── routes.py           # Flask routes
│       └── templates/          # HTML templates
├── config/
│   ├── .env                    # Environment variables
│   └── config.yaml             # System configuration
└── requirements.txt            # Python dependencies
```

## Getting Help

1. **Check Logs**: Most issues show in console output
2. **Review Documentation**: `UPDATES.md` for detailed changes
3. **Arduino Issues**: See `arduino_firmware/README.md`
4. **API Reference**: `docs/API.md`

## Next Steps

1. ✅ Get basic system running
2. ✅ Verify Arduino communication
3. ✅ Test manual controls
4. 📊 Collect baseline data (1 week)
5. 🤖 Train ML models
6. 🚀 Deploy to production
7. 📱 Set up kiosk mode (see `scripts/setup_kiosk.sh`)

---

**Quick Links:**
- Dashboard: http://localhost:5000/dashboard
- Controls: http://localhost:5000/controls
- Settings: http://localhost:5000/settings
- AI Insights: http://localhost:5000/ai_insights

**Support:** Review `UPDATES.md` for comprehensive documentation

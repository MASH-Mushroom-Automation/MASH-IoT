# M.A.S.H. IoT - System Updates Summary

## Overview
The Raspberry Pi gateway has been updated to fully synchronize with the Arduino firmware and integrate with the backend server at `api.mashmarket.app`.

## Changes Made

### 1. Environment Configuration (`.env`)
**File:** `rpi_gateway/config/.env`

Added comprehensive environment variables:
- `BACKEND_URL=https://api.mashmarket.app` - Backend API endpoint
- `BACKEND_API_KEY` - API authentication key (set your actual key)
- Firebase configuration placeholders
- MQTT broker configuration (HiveMQ Cloud)
- Device identification (`DEVICE_ID`, `DEVICE_NAME`)

### 2. System Configuration (`config.yaml`)
**File:** `rpi_gateway/config/config.yaml`

Complete configuration rewrite with:
- **System settings**: ML enabled, auto mode, sync intervals
- **Room configurations**: Precise thresholds for fruiting and spawning rooms
- **Actuator mappings**: Match Arduino firmware pins exactly
  - Fruiting Room: Exhaust Fan, Blower Fan, Humidifier, Humidifier Fan, LED
  - Spawning Room: Exhaust Fan
- **Alert thresholds**: Critical levels for CO2, temperature, humidity
- **ML model paths**: Anomaly detection and decision tree models

### 3. Serial Communication Module
**File:** `rpi_gateway/app/core/serial_comm.py`

**Key Updates:**
- Added `ACTUATORS` dictionary mapping room/actuator types to Arduino command names
- Updated `parse_sensor_data()` to handle single-sensor JSON format from Arduino
  - Expects: `{"fruiting": {"temp": 23.5, "humidity": 85, "co2": 800}}`
  - Spawning sensor currently disabled in Arduino firmware
- New `control_actuator(room, actuator_type, state)` method for friendly control
  - Example: `control_actuator('fruiting', 'exhaust_fan', 'ON')`
  - Automatically translates to: `FRUITING_EXHAUST_FAN_ON\n`
- Added `get_latest_data()` method for web UI
- Improved error handling for sensor errors

**Arduino Protocol Match:**
- Commands: Plain text format `ACTUATOR_NAME_STATE\n`
- Data: JSON format `{"fruiting": {...}}\n`
- Baud rate: 9600 (unchanged)

### 4. Backend API Client (NEW)
**File:** `rpi_gateway/app/cloud/backend_api.py`

Brand new module for backend communication:
- **Connection management**: Health checks with 30s caching
- **Device registration**: `register_device()` - Called on startup
- **Sensor data upload**: `send_sensor_data()` - Real-time data sync
- **Command retrieval**: `get_actuator_commands()` - Remote control capability
- **Alert sending**: `send_alert()` - Notifications to backend
- **Configuration sync**: `get_config()` - Remote configuration updates

**Features:**
- Automatic retry logic
- Offline-first design (fails gracefully)
- Session pooling for efficiency
- Bearer token authentication

### 5. Web Routes
**File:** `rpi_gateway/app/web/routes.py`

**Updates:**
- `get_live_data()`: Now fetches from Arduino serial instead of simulated data
- Added connection status tracking (Arduino + Backend)
- Updated `/api/control_actuator` endpoint:
  - Uses friendly `control_actuator()` method
  - Sends alerts to backend on manual control
  - Proper error handling with HTTP status codes
- Context now includes `arduino_connected` and `backend_connected` flags

### 6. Dashboard UI
**File:** `rpi_gateway/app/web/templates/dashboard.html`

**Visual Updates:**
- System status bar shows:
  - Arduino connection status (Connected/Offline)
  - Backend connection status (Online/Offline)
  - Uptime counter
- Fruiting Room actuator icons updated:
  - Exhaust Fan, Blower Fan, Humidifier, LED
  - Removed obsolete "Intake Fan" icon
- Added sensor error indicators
- Dynamic status colors (green=OK, yellow=warning, red=error)

### 7. Controls UI
**File:** `rpi_gateway/app/web/templates/controls.html`

**Updated Controls:**
- Fruiting Room now has 5 actuators:
  1. Exhaust Fan
  2. Blower Fan
  3. Humidifier
  4. Humidifier Fan
  5. LED Light
- Spawning Room: Exhaust Fan only
- All switches use proper `data-room` and `data-actuator` attributes

### 8. Main Orchestrator
**File:** `rpi_gateway/app/main.py`

**Major Integration:**
- Added `BackendAPIClient` initialization
- Device registration on startup
- Backend upload in `on_sensor_data()` callback (non-blocking)
- Flask app context now includes:
  - `app.serial_comm` - Arduino communication object
  - `app.backend_client` - Backend API client
  - `app.backend_connected` - Connection status flag
  - `app.config['MUSHROOM_CONFIG']` - Full configuration
- Enhanced shutdown sequence (closes all connections)

## Arduino Firmware Compatibility

### Supported Actuators
Based on `arduino_firmware/src/config.h`:

| Arduino Name | Pin | Description |
|--------------|-----|-------------|
| `SPAWNING_EXHAUST_FAN` | 2 | Spawning room exhaust |
| `FRUITING_EXHAUST_FAN` | 3 | Fruiting room exhaust |
| `FRUITING_BLOWER_FAN` | 4 | Air circulation fan |
| `HUMIDIFIER_FAN` | 5 | Pushes mist into pipes |
| `HUMIDIFIER` | 6 | Ultrasonic mist maker |
| `FRUITING_LED` | 7 | LED grow light |

### Command Format
```
FRUITING_EXHAUST_FAN_ON\n    # Turn on fruiting exhaust
HUMIDIFIER_OFF\n             # Turn off humidifier
```

### Data Format (Arduino → RPi)
```json
{
  "fruiting": {
    "temp": 23.5,
    "humidity": 85.2,
    "co2": 950
  },
  "timestamp": 1738123456.789
}
```

## Backend API Integration

### Base URL
`https://api.mashmarket.app`

### API Endpoints Used
- `POST /api/devices/register` - Device registration
- `POST /api/sensors/data` - Upload sensor readings
- `GET /api/devices/{device_id}/commands` - Fetch remote commands
- `POST /api/alerts` - Send notifications
- `GET /api/devices/{device_id}/config` - Remote config sync
- `GET /health` - Health check

### Authentication
Bearer token via `Authorization` header:
```
Authorization: Bearer {BACKEND_API_KEY}
```

## Installation & Setup

### 1. Install Dependencies
```bash
cd rpi_gateway
pip install -r requirements.txt
```

### 2. Configure Environment
Edit `rpi_gateway/config/.env`:
```env
BACKEND_URL=https://api.mashmarket.app
BACKEND_API_KEY=your_actual_api_key_here
DEVICE_ID=rpi_gateway_001
```

### 3. Review Configuration
Check `rpi_gateway/config/config.yaml` and adjust thresholds as needed.

### 4. Run the System
```bash
python -m app.main
```

Access dashboard at: `http://localhost:5000/dashboard`

## Testing Checklist

### Arduino Communication
- [ ] Serial connection establishes (check logs for "Connected to Arduino")
- [ ] Sensor data received every 5 seconds
- [ ] Manual actuator control works from web UI
- [ ] All 6 actuators respond correctly

### Backend Integration
- [ ] Device registration succeeds on startup
- [ ] Sensor data uploads every 5 seconds
- [ ] Backend status shows "Online" in dashboard
- [ ] Alerts are sent on manual control actions

### Web UI
- [ ] Dashboard shows live sensor readings
- [ ] Actuator icons animate when active
- [ ] Connection status indicators update
- [ ] Controls page switches actuators successfully
- [ ] Error states display correctly (sensor errors, disconnects)

## Architecture Highlights

### Offline-First Data Flow
1. Arduino → Serial JSON → RPi receives
2. **IMMEDIATELY** save to SQLite
3. **THEN** attempt backend upload
4. If offline: data queues locally, syncs when reconnected

### Two-Layer Safety
- Arduino: Watchdog timer shuts down relays if serial disconnects
- RPi: Graceful shutdown sends `ALL_OFF` command before disconnect

### Dual I2C Sensor Setup
- **Sensor 1 (Fruiting)**: Hardware I2C (A4/A5) via Grove Hub
- **Sensor 2 (Spawning)**: Software I2C (D10/D11) - **CURRENTLY DISABLED**
  - Both are SCD41 at address 0x62
  - Differentiated by I2C bus, not address

## Known Limitations

1. **Spawning Sensor Disabled**: Arduino firmware has spawning sensor commented out
   - UI still shows spawning room but data will be null/zero
   - Uncomment in `arduino_firmware/src/main.cpp` to enable

2. **Backend API Key Required**: Must set `BACKEND_API_KEY` in `.env` for uploads to work

3. **ML Models Not Included**: Decision tree and isolation forest models need training
   - See `docs/MACHINE_LEARNING.md` for training instructions

4. **No HTTPS in Local Dev**: Flask development server runs HTTP only
   - Use reverse proxy (nginx) for production HTTPS

## Next Steps

1. **Upload Arduino Firmware**: Flash latest firmware to Arduino
   ```bash
   cd arduino_firmware
   pio run -t upload
   ```

2. **Test Serial Communication**: Monitor Arduino output
   ```bash
   pio device monitor
   ```

3. **Verify Backend Connectivity**: Check backend health endpoint
   ```bash
   curl https://api.mashmarket.app/health
   ```

4. **Train ML Models**: Generate baseline data and train models
   - Collect 1 week of sensor data
   - Run training scripts in `docs/MACHINE_LEARNING.md`

5. **Deploy to Production**: Use systemd service for auto-start
   - See `scripts/setup_kiosk.sh` for kiosk mode setup

## Support & Documentation

- **Project Structure**: `STRUCTURE.md`
- **ML Training**: `docs/MACHINE_LEARNING.md`
- **Database Schema**: `docs/SCHEMA.md`
- **Backend API**: `docs/API.md`
- **Arduino Setup**: `arduino_firmware/README.md`

---

**Last Updated:** January 28, 2026
**System Version:** 1.0.0
**Author:** M.A.S.H. IoT Team

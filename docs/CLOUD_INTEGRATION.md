# Cloud Integration Implementation Guide

## Overview

The M.A.S.H. IoT system now includes comprehensive cloud integration with:

1. **Backend API** (JWT authenticated REST API)
2. **MQTT** (Real-time bidirectional communication via HiveMQ Cloud)
3. **Firebase** (Backup and analytics)
4. **Sync Manager** (Offline-first orchestration)

---

## Architecture

```
Arduino → USB Serial → RPi Gateway
                          ↓
                    ┌─────────────┐
                    │   SQLite    │  (Primary, always available)
                    │  (Offline)  │
                    └─────────────┘
                          ↓ (sync)
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                  ↓
  ┌──────────┐     ┌──────────┐      ┌──────────┐
  │ Backend  │     │   MQTT   │      │ Firebase │
  │   API    │     │ HiveMQ   │      │Realtime  │
  │ (REST+   │     │ (Real-   │      │Database  │
  │  JWT)    │     │  time)   │      │(Optional)│
  └──────────┘     └──────────┘      └──────────┘
       ↓                ↓                  ↓
  PostgreSQL      Commands/Status    Analytics
```

---

## Configuration

### 1. Environment Variables (.env)

Create `rpi_gateway/config/.env` with:

```bash
# Device Identity
DEVICE_ID=rpi_gateway_001
DEVICE_NAME=MASH IoT Gateway
DEVICE_EMAIL=device@mashmarket.app
DEVICE_PASSWORD=your_secure_device_password

# Backend API
BACKEND_URL=https://api.mashmarket.app

# MQTT (HiveMQ Cloud)
MQTT_BROKER=290691cd2bcb4d7faf979db077890beb.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USERNAME=your_hivemq_username
MQTT_PASSWORD=your_hivemq_password

# Firebase (Optional)
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com

# Sync Settings
SYNC_INTERVAL=60
BATCH_SIZE=50
```

### 2. Backend API Setup

The device needs a registered user account on the backend:

1. Register device account via backend admin panel or API:
   - Email: `device@mashmarket.app`
   - Role: `GROWER` or `ADMIN`
   - Active: `true`

2. The device will automatically:
   - Authenticate on startup
   - Refresh JWT tokens before expiry
   - Register itself as an IoT device

### 3. MQTT Setup (HiveMQ Cloud)

1. Create account at https://www.hivemq.com/
2. Create cluster in EU region
3. Create credentials with:
   - Username: `mash_device`
   - Password: (secure password)
   - Permissions: Publish/Subscribe on `devices/#`

### 4. Firebase Setup (Optional)

1. Create Firebase project at https://console.firebase.google.com/
2. Generate service account key
3. Save as `rpi_gateway/config/firebase_config.json`
4. Enable Realtime Database

---

## Module Documentation

### backend_api.py

**Purpose**: REST API communication with JWT authentication

**Key Features**:
- Automatic JWT authentication with refresh
- Sensor data upload (batch)
- Device registration and status updates
- Remote command fetching
- Alert/notification sending
- Configuration retrieval

**Usage**:
```python
from app.cloud.backend_api import create_backend_client

backend = create_backend_client()

# Authentication happens automatically
if backend.check_connection():
    # Upload sensor data
    backend.send_sensor_data({
        "fruiting": {"temp": 24.5, "humidity": 85, "co2": 800},
        "timestamp": time.time()
    })
    
    # Send alert
    backend.send_alert("high_co2", "CO2 exceeded threshold", "CRITICAL")
    
    # Get commands
    commands = backend.get_actuator_commands()
```

**API Endpoints Used**:
- `POST /auth/login` - Initial authentication
- `POST /auth/refresh` - Token refresh
- `POST /devices` - Device registration
- `POST /sensors/data` - Sensor data upload
- `GET /devices/{id}/commands` - Fetch commands
- `POST /alerts/trigger` - Send alerts
- `PUT /devices/{id}` - Update device status

---

### mqtt_client.py

**Purpose**: Real-time bidirectional MQTT communication

**Key Features**:
- TLS encrypted connection to HiveMQ Cloud
- Automatic reconnection with exponential backoff
- Command subscription and callback
- Real-time sensor data publishing
- Status and alert publishing

**Usage**:
```python
from app.cloud.mqtt_client import create_mqtt_client

mqtt = create_mqtt_client()

# Connect
if mqtt.connect():
    # Publish sensor data
    mqtt.publish_sensor_data({
        "fruiting": {"temp": 24.5, "humidity": 85, "co2": 800}
    })
    
    # Set command callback
    def handle_command(cmd):
        print(f"Received: {cmd}")
    
    mqtt.set_command_callback(handle_command)
    
    # Publish alert
    mqtt.publish_alert("high_temp", "Temperature critical", "CRITICAL")
```

**MQTT Topics**:
- `devices/{device_id}/sensor_data` - Publish sensor readings
- `devices/{device_id}/commands` - Subscribe for commands
- `devices/{device_id}/status` - Publish device status
- `devices/{device_id}/alerts` - Publish alerts

---

### firebase.py

**Purpose**: Optional backup to Firebase Realtime Database

**Key Features**:
- Batch sensor data sync
- Device status updates
- Configuration retrieval

**Usage**:
```python
from app.cloud.firebase import create_firebase_sync

firebase = create_firebase_sync()

if firebase.is_initialized:
    # Sync sensor readings
    readings = [
        {"room": "fruiting", "temp": 24.5, "humidity": 85, "co2": 800}
    ]
    count = firebase.sync_sensor_readings(readings)
```

**Firebase Structure**:
```
/
├── sensor_data/
│   ├── fruiting/
│   │   └── 2026-01-28T10-00-00/
│   │       ├── temperature: 24.5
│   │       ├── humidity: 85
│   │       └── co2: 800
│   └── spawning/
│       └── ...
└── devices/
    └── rpi_gateway_001/
        ├── status/
        └── config/
```

---

### sync.py

**Purpose**: Offline-first synchronization orchestrator

**Key Features**:
- Automatic background sync every 60 seconds
- Batch processing for efficiency
- Exponential backoff retry logic
- Multi-threaded (sync + MQTT heartbeat)
- Queue-based real-time publishing
- Health monitoring

**Usage**:
```python
from app.cloud.sync import create_sync_manager
from app.database.db_manager import DatabaseManager
from app.cloud.backend_api import create_backend_client
from app.cloud.mqtt_client import create_mqtt_client

db = DatabaseManager()
backend = create_backend_client()
mqtt = create_mqtt_client()

sync_mgr = create_sync_manager(
    db_manager=db,
    backend_client=backend,
    mqtt_client=mqtt
)

# Start sync threads
sync_mgr.start()

# Queue real-time sensor data
sync_mgr.queue_sensor_data({"fruiting": {"temp": 24.5}})

# Queue alert
sync_mgr.queue_alert("high_co2", "CO2 critical", "CRITICAL")

# Get pending commands
cmd = sync_mgr.get_pending_command()
if cmd:
    # Execute command
    success = execute(cmd)
    sync_mgr.acknowledge_command(cmd['id'], success)

# Get statistics
stats = sync_mgr.get_stats()
print(f"Synced: {stats['total_synced']}, Pending: {stats['pending_records']}")

# Stop when done
sync_mgr.stop()
```

**Sync Flow**:
1. **SQLite → Backend API**: Unsynced sensor data (batch)
2. **SQLite → Firebase**: Backup (optional)
3. **Queue → MQTT**: Real-time sensor data
4. **Queue → Backend API**: Alerts
5. **Backend API → Queue**: Remote commands
6. **MQTT → Queue**: Real-time commands

---

## Integration with Main Application

Update `rpi_gateway/app/main.py`:

```python
from app.cloud.backend_api import create_backend_client
from app.cloud.mqtt_client import create_mqtt_client
from app.cloud.firebase import create_firebase_sync
from app.cloud.sync import create_sync_manager
from app.database.db_manager import DatabaseManager

# Initialize components
db = DatabaseManager()
backend = create_backend_client()
firebase = create_firebase_sync()
mqtt = create_mqtt_client()

# Create sync manager
sync_manager = create_sync_manager(
    db_manager=db,
    backend_client=backend,
    firebase_sync=firebase,
    mqtt_client=mqtt
)

# Start sync
sync_manager.start()

# In sensor read loop:
def process_sensor_data(data):
    # Save to SQLite (primary)
    db.save_sensor_data(data)
    
    # Queue for real-time MQTT
    sync_manager.queue_sensor_data(data)
    
    # Check thresholds and send alerts
    if data['co2'] > 1500:
        sync_manager.queue_alert(
            "high_co2",
            f"CO2 level critical: {data['co2']} ppm",
            "CRITICAL"
        )

# In command processing:
def process_commands():
    cmd = sync_manager.get_pending_command(timeout=1.0)
    if cmd:
        logger.info(f"Executing command: {cmd}")
        success = execute_command(cmd)
        sync_manager.acknowledge_command(cmd['id'], success)

# On shutdown:
def cleanup():
    sync_manager.stop()
    backend.close()
    mqtt.disconnect()
```

---

## Security Considerations

1. **JWT Tokens**:
   - Automatically refreshed before expiry
   - Never logged or exposed
   - Stored only in memory

2. **MQTT**:
   - TLS 1.2 encryption
   - Username/password authentication
   - Certificate validation enabled

3. **Credentials**:
   - Stored in `.env` (gitignored)
   - Environment variable based
   - No hardcoded secrets

4. **API Communication**:
   - HTTPS only
   - JWT bearer authentication
   - Request/response validation

---

## Monitoring and Debugging

### Check Sync Status
```python
stats = sync_manager.get_stats()
print(f"""
Backend: {'✓' if stats['backend_online'] else '✗'}
MQTT:    {'✓' if stats['mqtt_online'] else '✗'}
Firebase:{'✓' if stats['firebase_online'] else '✗'}
Synced:  {stats['total_synced']}
Pending: {stats['pending_records']}
Last:    {stats['last_sync']}
""")
```

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Backend Connection
```python
if backend.check_connection():
    print("✓ Backend reachable and authenticated")
else:
    print("✗ Backend offline or authentication failed")
```

### Test MQTT Connection
```python
if mqtt.is_alive():
    print("✓ MQTT connected")
else:
    print("✗ MQTT disconnected")
```

---

## Troubleshooting

### Backend Authentication Fails
- Verify `DEVICE_EMAIL` and `DEVICE_PASSWORD` in `.env`
- Check if user exists in backend database
- Ensure user role is `GROWER` or `ADMIN`
- Check backend logs for authentication errors

### MQTT Connection Fails
- Verify HiveMQ credentials
- Check firewall allows port 8883 outbound
- Ensure TLS certificates are valid
- Test with MQTT Explorer tool first

### Firebase Initialization Fails
- Check `firebase_config.json` exists and is valid
- Verify service account has Database Admin role
- Ensure Realtime Database is enabled
- Check database URL is correct

### Data Not Syncing
- Check `pending_records` in stats
- Verify backend/MQTT are online
- Check database for unsynced records:
  ```sql
  SELECT COUNT(*) FROM sensor_data WHERE synced = 0;
  ```
- Force immediate sync:
  ```python
  sync_manager.force_sync()
  ```

---

## Performance Optimization

1. **Batch Size**: Adjust `BATCH_SIZE` in `.env` (default: 50)
   - Higher = fewer requests, more data per sync
   - Lower = more frequent updates, less load per sync

2. **Sync Interval**: Adjust `SYNC_INTERVAL` in `.env` (default: 60s)
   - Shorter = more real-time, higher network usage
   - Longer = less load, delayed sync

3. **MQTT QoS**: Currently QoS 1 (at least once)
   - Can reduce to QoS 0 for fire-and-forget
   - QoS 2 not recommended (performance impact)

4. **Disable Optional Services**:
   - Set `firebase_sync=None` to disable Firebase
   - Set `mqtt_client=None` to disable MQTT

---

## Testing

### Unit Test Example
```python
import pytest
from app.cloud.backend_api import BackendAPIClient

def test_authentication():
    backend = BackendAPIClient()
    assert backend.authenticate() == True
    assert backend.access_token is not None

def test_sensor_upload():
    backend = BackendAPIClient()
    backend.authenticate()
    
    result = backend.send_sensor_data({
        "fruiting": {"temp": 24.5, "humidity": 85, "co2": 800},
        "timestamp": time.time()
    })
    assert result == True
```

---

## Dependencies

All required packages are in `requirements.txt`:

```
requests==2.31.0       # HTTP client
paho-mqtt==1.6.1       # MQTT client
PyJWT==2.8.0           # JWT token handling
firebase-admin==6.3.0  # Firebase (optional)
python-dotenv==1.0.0   # Environment variables
```

Install:
```bash
pip install -r requirements.txt
```

---

## Next Steps

1. Configure `.env` with your credentials
2. Test each component individually
3. Integrate into main application loop
4. Monitor sync statistics
5. Implement dashboard for cloud status
6. Add web UI for sync controls

---

**Documentation Version**: 1.0  
**Last Updated**: 2026-01-28  
**Author**: M.A.S.H. IoT Development Team

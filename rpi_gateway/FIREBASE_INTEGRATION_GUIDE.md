# Firebase Realtime Database Integration Guide

## Architecture Overview

```
Arduino → RPi → [SAVE SQLITE] → Parallel Sync:
                                  ├─► Backend API (PostgreSQL)
                                  ├─► Firebase Realtime DB
                                  └─► MQTT (Real-time commands)

Mobile App ← Listens to Firebase Realtime DB (Live updates)
Mobile App ← REST API Polling (Historical data)
Mobile App ← MQTT Subscribe (Commands/Alerts)
```

## Why Three Sync Channels?

### 1. **Firebase Realtime Database** (Real-time sensor updates)
- **Purpose**: Live sensor data streaming to mobile app
- **Best for**: Dashboard real-time charts, current values
- **Update frequency**: Every 5 seconds (as Arduino sends data)
- **Data retention**: Last 24 hours only (auto-cleanup)

### 2. **Backend API (PostgreSQL)** (Historical data & user management)
- **Purpose**: Long-term storage, analytics, user authentication
- **Best for**: Historical trends, reports, user accounts, device management
- **Update frequency**: Batched every 60 seconds
- **Data retention**: Permanent

### 3. **MQTT** (Low-latency commands)
- **Purpose**: Instant actuator control (Fan ON/OFF, Mist ON/OFF)
- **Best for**: Remote control, alerts, critical commands
- **Latency**: <100ms
- **Quality of Service**: QoS 1 (guaranteed delivery)

---

## Firebase Database Structure

```
mash-ddf8d-default-rtdb.asia-southeast1.firebasedatabase.app/
├── devices/
│   ├── {device_id}/
│   │   ├── status/
│   │   │   ├── status: "ONLINE" | "OFFLINE" | "ERROR"
│   │   │   ├── last_update: "2026-02-06T10:30:00"
│   │   │   └── metadata: {...}
│   │   ├── config/
│   │   │   ├── ml_enabled: true
│   │   │   ├── sync_interval: 60
│   │   │   └── ...
│   │   └── latest_reading/  (for quick dashboard access)
│   │       ├── fruiting: {...}
│   │       └── spawning: {...}
│   
├── sensor_data/
│   ├── {device_id}/
│   │   ├── fruiting/
│   │   │   └── 2026-02-06T10-30-00/
│   │   │       ├── temperature: 24.5
│   │   │       ├── humidity: 85
│   │   │       ├── co2: 800
│   │   │       ├── timestamp: "2026-02-06T10:30:00"
│   │   │       └── synced_at: "2026-02-06T10:30:01"
│   │   └── spawning/
│   │       └── 2026-02-06T10-30-00/
│   │           ├── temperature: 25.0
│   │           ├── humidity: 90
│   │           └── co2: 1200
│   
└── alerts/
    └── {device_id}/
        └── 2026-02-06T10-30-00/
            ├── type: "HIGH_TEMP"
            ├── room: "fruiting"
            ├── message: "Temperature exceeds threshold"
            └── timestamp: "2026-02-06T10:30:00"
```

---

## Setup Instructions

### 1. RPi Firebase Configuration

#### Install Firebase Admin SDK:
```bash
cd MASH-IoT/rpi_gateway
source venv/bin/activate  # Or venv\Scripts\activate on Windows
pip install firebase-admin
```

#### Download Service Account Key:
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select project: `mash-ddf8d`
3. Project Settings → Service Accounts
4. Click "Generate New Private Key"
5. Save as: `MASH-IoT/rpi_gateway/config/firebase_config.json`

**⚠️ SECURITY WARNING**: Never commit `firebase_config.json` to Git!
```bash
# Add to .gitignore (already done)
echo "config/firebase_config.json" >> .gitignore
```

#### Update .env file:
```bash
# Add to config/.env
FIREBASE_DATABASE_URL=https://mash-ddf8d-default-rtdb.asia-southeast1.firebasedatabase.app
FIREBASE_CONFIG_PATH=config/firebase_config.json
```

### 2. Mobile App Firebase Setup

**Already configured!** Your mobile app has:
- ✅ Firebase initialized in `lib/main.dart`
- ✅ Database URL configured in `lib/firebase_options.dart`
- ✅ Google Services JSON added

**Add Firebase Realtime Database package:**
```yaml
# pubspec.yaml
dependencies:
  firebase_database: ^11.1.4  # Latest version
```

```bash
flutter pub get
```

---

## Implementation

### RPi: Enhanced Firebase Sync

The RPi code in `app/cloud/firebase.py` already implements:
- ✅ Firebase initialization with Admin SDK
- ✅ Sensor data upload to `/sensor_data/{room}/{timestamp}`
- ✅ Device status tracking
- ✅ Configuration retrieval

**How data flows:**
1. Arduino sends JSON → Serial → RPi
2. RPi saves to SQLite immediately (offline-first)
3. `SyncManager` in `app/cloud/sync.py` pushes to Firebase asynchronously
4. No blocking - if Firebase fails, data remains in SQLite

### Mobile App: Firebase Realtime Listener

**Create new service:** `lib/services/firebase_realtime_service.dart`

```dart
import 'dart:async';
import 'package:firebase_database/firebase_database.dart';
import '../data/models/sensor_reading_model.dart';
import '../core/utils/logger.dart';

class FirebaseRealtimeService {
  final FirebaseDatabase _database = FirebaseDatabase.instance;
  StreamSubscription? _sensorDataSubscription;
  
  /// Listen to real-time sensor data for a specific device
  Stream<Map<String, SensorReadingModel>> listenToSensorData(String deviceId) {
    final ref = _database.ref('devices/$deviceId/latest_reading');
    
    return ref.onValue.map((event) {
      if (!event.snapshot.exists) return {};
      
      final data = event.snapshot.value as Map<dynamic, dynamic>?;
      if (data == null) return {};
      
      return {
        'fruiting': _parseSensorData(data['fruiting'], 'fruiting'),
        'spawning': _parseSensorData(data['spawning'], 'spawning'),
      };
    });
  }
  
  /// Listen to device status changes
  Stream<String> listenToDeviceStatus(String deviceId) {
    final ref = _database.ref('devices/$deviceId/status/status');
    
    return ref.onValue.map((event) {
      return event.snapshot.value as String? ?? 'UNKNOWN';
    });
  }
  
  SensorReadingModel _parseSensorData(dynamic data, String room) {
    if (data == null) return _createEmptyReading(room);
    
    final map = data as Map<dynamic, dynamic>;
    return SensorReadingModel(
      id: 0,
      deviceId: '',
      room: room,
      temperature: (map['temperature'] as num?)?.toDouble() ?? 0.0,
      humidity: (map['humidity'] as num?)?.toDouble() ?? 0.0,
      co2: (map['co2'] as num?)?.toInt() ?? 0,
      timestamp: DateTime.parse(map['timestamp'] as String? ?? DateTime.now().toIso8601String()),
    );
  }
  
  SensorReadingModel _createEmptyReading(String room) {
    return SensorReadingModel(
      id: 0,
      deviceId: '',
      room: room,
      temperature: 0.0,
      humidity: 0.0,
      co2: 0,
      timestamp: DateTime.now(),
    );
  }
  
  void dispose() {
    _sensorDataSubscription?.cancel();
  }
}
```

### Update Sensor Provider

**Enhance** `lib/presentation/providers/sensor_provider.dart`:

```dart
import 'package:flutter/foundation.dart';
import '../../services/firebase_realtime_service.dart';
import '../../data/models/sensor_reading_model.dart';

class SensorProvider extends ChangeNotifier {
  final FirebaseRealtimeService _firebaseService = FirebaseRealtimeService();
  
  Map<String, SensorReadingModel> _latestReadings = {};
  String _deviceStatus = 'UNKNOWN';
  bool _isListening = false;
  
  // Getters
  Map<String, SensorReadingModel> get latestReadings => _latestReadings;
  String get deviceStatus => _deviceStatus;
  bool get isListening => _isListening;
  
  /// Start listening to real-time sensor data from Firebase
  void startListening(String deviceId) {
    if (_isListening) return;
    
    _firebaseService.listenToSensorData(deviceId).listen(
      (readings) {
        _latestReadings = readings;
        notifyListeners();
      },
      onError: (error) {
        debugPrint('[Firebase] Sensor data error: $error');
      },
    );
    
    _firebaseService.listenToDeviceStatus(deviceId).listen(
      (status) {
        _deviceStatus = status;
        notifyListeners();
      },
      onError: (error) {
        debugPrint('[Firebase] Device status error: $error');
      },
    );
    
    _isListening = true;
    notifyListeners();
  }
  
  void stopListening() {
    _firebaseService.dispose();
    _isListening = false;
    notifyListeners();
  }
  
  @override
  void dispose() {
    _firebaseService.dispose();
    super.dispose();
  }
}
```

### Dashboard Integration

**In your dashboard screen:**

```dart
// lib/presentation/screens/dashboard/dashboard_screen.dart

@override
void initState() {
  super.initState();
  
  final deviceId = Provider.of<DeviceProvider>(context, listen: false).selectedDevice?.id;
  if (deviceId != null) {
    // Start Firebase real-time listener
    Provider.of<SensorProvider>(context, listen: false).startListening(deviceId);
  }
}

// In build method:
Consumer<SensorProvider>(
  builder: (context, sensorProvider, child) {
    final fruitingData = sensorProvider.latestReadings['fruiting'];
    final spawningData = sensorProvider.latestReadings['spawning'];
    
    return Column(
      children: [
        SensorCard(
          title: 'Fruiting Room',
          temperature: fruitingData?.temperature ?? 0.0,
          humidity: fruitingData?.humidity ?? 0.0,
          co2: fruitingData?.co2 ?? 0,
        ),
        SensorCard(
          title: 'Spawning Room',
          temperature: spawningData?.temperature ?? 0.0,
          humidity: spawningData?.humidity ?? 0.0,
          co2: spawningData?.co2 ?? 0,
        ),
      ],
    );
  },
)
```

---

## Data Flow Scenarios

### Scenario 1: Normal Operation (Internet Available)

```
Arduino → RPi → SQLite (saved) → Parallel:
                                  ├─► Firebase (5s updates)
                                  ├─► Backend API (60s batches)
                                  └─► MQTT (instant commands)

Mobile App → Firebase listener → UI updates every 5s
```

### Scenario 2: Internet Outage (Offline-First)

```
Arduino → RPi → SQLite (saved) → [Sync fails silently]

When internet returns:
SQLite (unsynced rows) → Bulk upload to:
                         ├─► Firebase (last 24h only)
                         ├─► Backend API (all data)
                         └─► MQTT reconnect
```

### Scenario 3: Mobile App Offline

```
Mobile App → Show last cached data from SQLite
Mobile App → Display offline indicator
Mobile App → When reconnects → Firebase listener resumes
```

---

## Security Rules (Firebase Console)

**Set up security rules** to protect your database:

```json
{
  "rules": {
    "devices": {
      "$deviceId": {
        ".read": "auth != null && (auth.uid == $deviceId || root.child('users').child(auth.uid).child('devices').child($deviceId).exists())",
        ".write": "auth != null && auth.uid == $deviceId",
        "status": {
          ".write": "auth != null"
        }
      }
    },
    "sensor_data": {
      "$deviceId": {
        ".read": "auth != null",
        ".write": "auth != null && auth.uid == $deviceId"
      }
    },
    "alerts": {
      "$deviceId": {
        ".read": "auth != null",
        ".write": "auth != null"
      }
    }
  }
}
```

**Apply rules:**
1. Go to Firebase Console → Realtime Database → Rules
2. Paste the JSON above
3. Click "Publish"

---

## Testing

### Test RPi Firebase Upload

```bash
cd MASH-IoT/rpi_gateway

# Run main app
python -m app.main

# Check logs for:
# [FIREBASE] Initialized successfully
# [FIREBASE] Synced 2/2 readings
```

### Test Mobile App Listener

```dart
// In your test widget or dashboard
import 'package:firebase_database/firebase_database.dart';

final ref = FirebaseDatabase.instance.ref('devices/rpi_gateway_001/latest_reading');

ref.onValue.listen((event) {
  print('Firebase data: ${event.snapshot.value}');
});
```

### Manual Firebase Write (Test from RPi)

```python
# In Python shell
from app.cloud.firebase import FirebaseSync

firebase = FirebaseSync(
    config_path='config/firebase_config.json',
    db_url='https://mash-ddf8d-default-rtdb.asia-southeast1.firebasedatabase.app'
)

# Test upload
test_reading = {
    'id': 999,
    'room': 'fruiting',
    'temp': 24.5,
    'humidity': 85,
    'co2': 800,
    'timestamp': '2026-02-06T10:30:00'
}

firebase.sync_sensor_readings([test_reading])
```

---

## Troubleshooting

### Problem: "firebase-admin not installed"
**Solution:**
```bash
pip install firebase-admin
```

### Problem: "Firebase initialization failed"
**Solution:**
- Check `config/firebase_config.json` exists
- Verify file has correct JSON format
- Check `.env` has `FIREBASE_DATABASE_URL`

### Problem: "Permission denied" on mobile app
**Solution:**
- Check Firebase Security Rules
- Ensure user is authenticated (`auth != null`)
- Verify device ownership in user's account

### Problem: Data not appearing in Firebase
**Solution:**
```bash
# Check RPi logs
tail -f /var/log/mash_iot.log | grep FIREBASE

# Verify network connectivity
ping firebase.googleapis.com

# Test manual upload (see Testing section above)
```

### Problem: Mobile app not receiving real-time updates
**Solution:**
```dart
// Enable Firebase database logging
FirebaseDatabase.instance.setLoggingEnabled(true);

// Check listener is active
print('Listening: ${sensorProvider.isListening}');
```

---

## Performance Optimization

### RPi: Reduce Firebase Writes
```python
# In config/config.yaml
system:
  firebase_sync_interval: 5  # Sync every 5 seconds (default)
  firebase_batch_size: 10    # Send up to 10 readings per batch
```

### Mobile App: Connection Persistence
```dart
// In main.dart, after Firebase initialization
FirebaseDatabase.instance.setPersistenceEnabled(true);
FirebaseDatabase.instance.setPersistenceCacheSizeBytes(10000000); // 10MB cache
```

### Firebase: Auto-cleanup Old Data
```python
# In app/cloud/firebase.py, add cleanup method:
def cleanup_old_data(self, device_id: str, days_to_keep: int = 1):
    """Delete sensor data older than specified days."""
    cutoff = datetime.now() - timedelta(days=days_to_keep)
    ref = firebase_db.reference(f'sensor_data/{device_id}')
    
    # Query and delete old entries
    old_data = ref.order_by_child('timestamp').end_at(cutoff.isoformat()).get()
    for key in old_data:
        ref.child(key).delete()
```

---

## Integration with MQTT

**When to use what:**

| Action | Use Firebase | Use MQTT | Use Backend API |
|--------|-------------|----------|-----------------|
| View live sensor data | ✅ Primary | ❌ | ❌ |
| Send actuator command (Fan ON) | ❌ | ✅ Primary | ✅ Fallback |
| View historical data | ❌ | ❌ | ✅ Primary |
| Device status updates | ✅ | ✅ | ✅ |
| User authentication | ❌ | ❌ | ✅ Primary |

**Combined flow for actuator control:**

```dart
// Mobile app sends command
Future<void> turnOnFan(String deviceId) async {
  // 1. Try MQTT first (fastest)
  if (mqttService.isConnected) {
    await mqttService.sendCommand(deviceId, 'FRUITING_EXHAUST_FAN', 'ON');
  }
  
  // 2. Fallback to Backend API
  else {
    await apiClient.post('/devices/$deviceId/commands', {
      'actuator': 'FRUITING_EXHAUST_FAN',
      'state': 'ON'
    });
  }
  
  // 3. Firebase listener will notify when state changes
  // (No action needed - listener handles UI update)
}
```

---

## Next Steps

1. ✅ **RPi Setup**: Install firebase-admin, add config file
2. ✅ **Mobile App**: Add firebase_database package
3. ✅ **Create Service**: Implement `FirebaseRealtimeService`
4. ✅ **Update Provider**: Enhance `SensorProvider` with Firebase listener
5. ✅ **Dashboard**: Wire up real-time data display
6. ⚠️ **Security Rules**: Configure Firebase access control
7. ⚠️ **Testing**: Verify end-to-end data flow
8. ⚠️ **Monitoring**: Set up Firebase Analytics

---

## Questions?

- **Why not just use Firebase?** Backend API provides user management, long-term storage, and complex queries that Firebase Realtime DB doesn't handle well.
- **Why not just use MQTT?** MQTT is great for commands but requires persistent connection. Firebase works even with intermittent connectivity.
- **Why SQLite?** Offline-first architecture ensures data is never lost, even during internet outages.

**All three services complement each other for a robust IoT system!**

# Firebase Integration Checklist ✅

## RPi Gateway Setup

### Step 1: Install Firebase SDK
```bash
cd MASH-IoT/rpi_gateway
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install firebase-admin
```

### Step 2: Download Service Account Key
1. Visit: https://console.firebase.google.com/project/mash-ddf8d/settings/serviceaccounts/adminsdk
2. Click **"Generate New Private Key"**
3. Save file as: `config/firebase_config.json`
4. **⚠️ NEVER commit this file to Git!**

### Step 3: Update Environment Variables
Edit `config/.env` and add:
```bash
FIREBASE_DATABASE_URL=https://mash-ddf8d-default-rtdb.asia-southeast1.firebasedatabase.app
FIREBASE_CONFIG_PATH=config/firebase_config.json
```

### Step 4: Start Gateway
```bash
python -m app.main
```

**Look for this in logs:**
```
[FIREBASE] ✅ Connected to Realtime Database
[FIREBASE] Initialized successfully
```

### Step 5: Verify Data Upload
```bash
# Check logs
tail -f /var/log/mash_iot.log | grep FIREBASE

# Should see:
# [FIREBASE] Synced 2/2 readings
```

---

## Mobile App Setup

### Step 1: Install Dependencies
```bash
cd MASH-Grower-Mobile
flutter pub get
```

**Verify `pubspec.yaml` has:**
```yaml
dependencies:
  firebase_database: ^11.1.4
```

### Step 2: Update Dashboard Screen

Add Firebase listener in your dashboard:

```dart
import 'package:provider/provider.dart';

@override
void initState() {
  super.initState();
  
  final deviceId = 'rpi_gateway_001'; // Get from device provider
  Provider.of<SensorProvider>(context, listen: false)
      .startFirebaseListening(deviceId);
}

@override
void dispose() {
  Provider.of<SensorProvider>(context, listen: false)
      .stopFirebaseListening();
  super.dispose();
}
```

### Step 3: Use Firebase Data in UI

```dart
Consumer<SensorProvider>(
  builder: (context, sensorProvider, child) {
    final fruitingData = sensorProvider.latestFirebaseReadings['fruiting'];
    final spawningData = sensorProvider.latestFirebaseReadings['spawning'];
    final deviceStatus = sensorProvider.deviceStatus;
    
    return Column(
      children: [
        Text('Status: $deviceStatus'),
        Text('Fruiting Temp: ${fruitingData?.temperature ?? 0.0}°C'),
        Text('Spawning Humidity: ${spawningData?.humidity ?? 0.0}%'),
      ],
    );
  },
)
```

### Step 4: Test
1. Run app: `flutter run`
2. Navigate to dashboard
3. Should see live data updating every 5 seconds

---

## Firebase Security Rules

### For Testing (Open Access)
```json
{
  "rules": {
    ".read": true,
    ".write": true
  }
}
```

### For Production (Authenticated Only)
```json
{
  "rules": {
    "devices": {
      "$deviceId": {
        ".read": "auth != null",
        ".write": "auth != null"
      }
    },
    "sensor_data": {
      "$deviceId": {
        ".read": "auth != null",
        ".write": "auth != null"
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
1. Go to: https://console.firebase.google.com/project/mash-ddf8d/database/rules
2. Paste rules
3. Click **"Publish"**

---

## Testing & Verification

### Test RPi → Firebase Upload

```bash
cd MASH-IoT/rpi_gateway
python
```

```python
from app.cloud.firebase import FirebaseSync

firebase = FirebaseSync(
    config_path='config/firebase_config.json',
    db_url='https://mash-ddf8d-default-rtdb.asia-southeast1.firebasedatabase.app'
)

# Test data
test_data = [{
    'id': 1,
    'room': 'fruiting',
    'temp': 24.5,
    'humidity': 85,
    'co2': 800,
    'timestamp': '2026-02-06T10:30:00'
}]

result = firebase.sync_sensor_readings(test_data)
print(f"✅ Synced {result} readings")
```

### Test Mobile App → Firebase Read

In any Dart file:

```dart
import 'package:firebase_database/firebase_database.dart';

void testFirebase() {
  final ref = FirebaseDatabase.instance.ref('devices/rpi_gateway_001/latest_reading');
  
  ref.onValue.listen((event) {
    print('✅ Firebase data: ${event.snapshot.value}');
  });
}
```

### Verify Data in Firebase Console

1. Visit: https://console.firebase.google.com/project/mash-ddf8d/database/data
2. Navigate to: `devices/rpi_gateway_001/latest_reading`
3. Should see live sensor data updating every 5 seconds

---

## Troubleshooting

### ❌ "firebase-admin not installed"
```bash
pip install firebase-admin
```

### ❌ "[FIREBASE] Config not found"
- Check file exists: `config/firebase_config.json`
- Verify file permissions (readable)
- Ensure it's valid JSON

### ❌ "[FIREBASE] Initialization failed"
- Check `.env` has `FIREBASE_DATABASE_URL`
- Verify service account key is valid
- Ensure internet connection works

### ❌ Mobile app shows no data
```dart
// Enable Firebase logging
FirebaseDatabase.instance.setLoggingEnabled(true);

// Check listener status
final sensorProvider = Provider.of<SensorProvider>(context, listen: false);
print('Firebase listening: ${sensorProvider.isFirebaseListening}');
print('Device status: ${sensorProvider.deviceStatus}');
```

### ❌ "Permission denied" on mobile
- Check Firebase Security Rules
- Ensure test rules allow open access (for testing)
- Verify user is authenticated (for production)

---

## Success Indicators ✅

### RPi Gateway
```
[FIREBASE] ✅ Connected to Realtime Database
[FIREBASE] Initialized successfully
[FIREBASE] Synced 2/2 readings
[DATA] Received sensor data at 2026-02-06T10:30:00
```

### Mobile App
```
[Firebase Realtime] Service initialized
[Sensor Provider] Starting Firebase listeners for rpi_gateway_001
[Sensor Provider] Firebase sensor data updated
[Sensor Provider] Device status: ONLINE
```

### Firebase Console
- Data appears under `devices/rpi_gateway_001/`
- `latest_reading` updates every 5 seconds
- `sensor_data/{room}/` contains historical entries

---

## Quick Reference

| Component | Purpose | Update Frequency |
|-----------|---------|------------------|
| `devices/{id}/latest_reading` | Real-time dashboard data | Every 5s |
| `devices/{id}/status` | Device connection status | On change |
| `sensor_data/{id}/{room}/` | Historical data (24h) | Every 5s |
| `alerts/{id}/` | Critical alerts | On alert |

---

## What's Next?

✅ Firebase Realtime Database integrated  
✅ Mobile app receiving live data  
✅ RPi syncing every 5 seconds  

**Optional enhancements:**
- [ ] Set up Firebase Cloud Functions for auto-cleanup
- [ ] Configure Firebase Analytics
- [ ] Add Firebase Performance Monitoring
- [ ] Implement push notifications via FCM

---

## 📚 Full Documentation

- **Quick Start**: [FIREBASE_QUICK_START.md](FIREBASE_QUICK_START.md)
- **Complete Guide**: [FIREBASE_INTEGRATION_GUIDE.md](FIREBASE_INTEGRATION_GUIDE.md)
- **System Overview**: [../FIREBASE_MQTT_INTEGRATION_SUMMARY.md](../FIREBASE_MQTT_INTEGRATION_SUMMARY.md)

---

**🎉 Your IoT system now has real-time Firebase integration!**

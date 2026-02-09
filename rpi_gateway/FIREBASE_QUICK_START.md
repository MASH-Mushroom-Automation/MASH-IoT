# Firebase Realtime Database - Quick Start Guide

## 🚀 Quick Setup (5 Minutes)

### RPi Gateway Setup

1. **Install Firebase Admin SDK**
```bash
cd MASH-IoT/rpi_gateway
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install firebase-admin
```

2. **Download Service Account Key**
- Visit: https://console.firebase.google.com/project/mash-ddf8d/settings/serviceaccounts/adminsdk
- Click "Generate New Private Key"
- Save as: `MASH-IoT/rpi_gateway/config/firebase_config.json`

3. **Update .env file**
```bash
# Add to config/.env
FIREBASE_DATABASE_URL=https://mash-ddf8d-default-rtdb.asia-southeast1.firebasedatabase.app
```

4. **Start the gateway**
```bash
python -m app.main
```

Check logs for: `[FIREBASE] Initialized successfully`

### Mobile App Setup

1. **Install dependencies** (already in pubspec.yaml)
```bash
cd MASH-Grower-Mobile
flutter pub get
```

2. **That's it!** Firebase is already configured.

---

## 📊 How It Works

```
┌─────────────┐      ┌──────────────┐      ┌──────────────────┐
│   Arduino   │─────▶│  Raspberry   │─────▶│    Firebase      │
│  (Sensors)  │ USB  │     Pi       │ WiFi │  Realtime DB     │
└─────────────┘      └──────────────┘      └──────────────────┘
                             │                       │
                             │                       │ Real-time
                             │                       │ Listener
                             ▼                       ▼
                      ┌──────────────┐      ┌──────────────────┐
                      │   SQLite     │      │   Mobile App     │
                      │  (Offline)   │      │   (Dashboard)    │
                      └──────────────┘      └──────────────────┘
```

**Data Flow:**
1. Arduino sends sensor data every 5s → RPi via serial
2. RPi saves to SQLite immediately (offline-first)
3. RPi pushes to Firebase Realtime DB (non-blocking)
4. Mobile app listens to Firebase → Updates UI automatically

---

## 🔥 Test Firebase Connection

### From RPi (Python)

```bash
cd MASH-IoT/rpi_gateway
source venv/bin/activate
python
```

```python
from app.cloud.firebase import FirebaseSync

# Initialize Firebase
firebase = FirebaseSync(
    config_path='config/firebase_config.json',
    db_url='https://mash-ddf8d-default-rtdb.asia-southeast1.firebasedatabase.app'
)

# Test data upload
test_data = [{
    'id': 1,
    'room': 'fruiting',
    'temp': 24.5,
    'humidity': 85,
    'co2': 800,
    'timestamp': '2026-02-06T10:30:00'
}]

result = firebase.sync_sensor_readings(test_data)
print(f"Synced {result} readings")
```

### From Mobile App (Dart)

Add to any screen:

```dart
import 'package:firebase_database/firebase_database.dart';

// Test Firebase connection
final ref = FirebaseDatabase.instance.ref('devices/rpi_gateway_001/latest_reading');

ref.onValue.listen((event) {
  print('Firebase data received: ${event.snapshot.value}');
});

// Manually write test data
await ref.set({
  'fruiting': {
    'temperature': 24.5,
    'humidity': 85,
    'co2': 800,
    'timestamp': DateTime.now().toIso8601String()
  }
});
```

---

## 📱 Use in Dashboard

### Update your dashboard screen:

```dart
import 'package:provider/provider.dart';
import '../../providers/sensor_provider.dart';

class DashboardScreen extends StatefulWidget {
  @override
  _DashboardScreenState createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    
    // Start Firebase real-time listening
    final deviceId = 'rpi_gateway_001'; // Get from device provider
    Provider.of<SensorProvider>(context, listen: false)
        .startFirebaseListening(deviceId);
  }
  
  @override
  void dispose() {
    // Stop listening when leaving screen
    Provider.of<SensorProvider>(context, listen: false)
        .stopFirebaseListening();
    super.dispose();
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Dashboard')),
      body: Consumer<SensorProvider>(
        builder: (context, sensorProvider, child) {
          // Get Firebase real-time data
          final fruitingData = sensorProvider.latestFirebaseReadings['fruiting'];
          final spawningData = sensorProvider.latestFirebaseReadings['spawning'];
          final deviceStatus = sensorProvider.deviceStatus;
          
          return Column(
            children: [
              // Device status indicator
              StatusBanner(
                status: deviceStatus,
                isOnline: deviceStatus == 'ONLINE',
              ),
              
              // Fruiting room card
              SensorCard(
                title: 'Fruiting Room',
                temperature: fruitingData?.temperature ?? 0.0,
                humidity: fruitingData?.humidity ?? 0.0,
                co2: fruitingData?.co2 ?? 0,
                lastUpdate: fruitingData?.timestamp,
              ),
              
              // Spawning room card
              SensorCard(
                title: 'Spawning Room',
                temperature: spawningData?.temperature ?? 0.0,
                humidity: spawningData?.humidity ?? 0.0,
                co2: spawningData?.co2 ?? 0,
                lastUpdate: spawningData?.timestamp,
              ),
              
              // Recent alerts
              AlertsSection(
                alerts: sensorProvider.recentAlerts,
              ),
            ],
          );
        },
      ),
    );
  }
}
```

---

## 🔒 Firebase Security Rules

**Set in Firebase Console → Database → Rules:**

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

⚠️ **WARNING**: These rules require authentication. For testing, you can temporarily set:
```json
{
  "rules": {
    ".read": true,
    ".write": true
  }
}
```

**Don't forget to restrict it later!**

---

## 🐛 Troubleshooting

### Problem: "firebase-admin not installed"
```bash
pip install firebase-admin
```

### Problem: "Permission denied" errors
- Check if `firebase_config.json` exists
- Verify file contains valid JSON
- Ensure `.env` has `FIREBASE_DATABASE_URL`

### Problem: Mobile app not receiving data
```dart
// Enable Firebase logging in main.dart
FirebaseDatabase.instance.setLoggingEnabled(true);

// Check if listening is active
print('Firebase listening: ${sensorProvider.isFirebaseListening}');
```

### Problem: Data not syncing from RPi
```bash
# Check RPi logs
tail -f /var/log/mash_iot.log | grep FIREBASE

# Test internet connection
ping firebase.googleapis.com

# Manually test sync (see Test section above)
```

---

## 📚 Additional Resources

- **Full Integration Guide**: [FIREBASE_INTEGRATION_GUIDE.md](FIREBASE_INTEGRATION_GUIDE.md)
- **Firebase Console**: https://console.firebase.google.com/project/mash-ddf8d
- **Database URL**: https://mash-ddf8d-default-rtdb.asia-southeast1.firebasedatabase.app/

---

## 🎯 Key Benefits

✅ **Real-time updates** - Dashboard updates every 5 seconds automatically  
✅ **Offline-first** - Data saved locally if internet fails  
✅ **No polling** - Mobile app uses push updates (efficient)  
✅ **Low latency** - Firebase delivers data in <1 second  
✅ **Automatic sync** - RPi handles everything in background  

---

## 🔄 MQTT vs Firebase vs Backend API

| Feature | Firebase | MQTT | Backend API |
|---------|----------|------|-------------|
| **Live sensor data** | ✅ Primary | ❌ | ❌ |
| **Actuator commands** | ❌ | ✅ Primary | ✅ Fallback |
| **Historical data (>24h)** | ❌ | ❌ | ✅ Primary |
| **User authentication** | ❌ | ❌ | ✅ Primary |
| **Latency** | ~1s | ~100ms | ~2-5s |
| **Offline support** | ✅ Cache | ❌ | ✅ Queue |

**Use all three together for best results!**

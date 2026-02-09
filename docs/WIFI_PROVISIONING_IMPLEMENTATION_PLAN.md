# WiFi Provisioning Flow Implementation Plan

**Status:** 🔨 In Progress  
**Target:** Full WiFi provisioning via Mobile App (no keyboard needed)  
**Date:** February 3, 2026

---

## Current State Analysis

### ✅ Already Implemented
- RPi hotspot creation via NetworkManager (`utils/wifi_manager.py`)
- WiFi scan endpoint (`/wifi-scan`)
- WiFi connect endpoint (`/wifi-connect`)
- Mobile app device discovery via mDNS (`services/mdns_discovery_service.dart`)
- Mobile app provisioning service (`services/device_provisioning_service.dart`)
- Flask web server with routes (`web/routes.py`)

### ❌ Needs Implementation
1. Remove "Connect to Network" from RPi web UI
2. Move WiFi controls to Settings page
3. Static QR code generation/display on RPi
4. Auto-enable hotspot on boot if no network
5. Ensure mobile uses RPi's WiFi scan (not phone's)
6. Remove demo mode from mobile app
7. Auto-reconnect logic after successful WiFi connection
8. MQTT/Cloud fallback for remote access

---

## Implementation Tasks

### Phase 1: RPi Gateway Changes

#### Task 1.1: Remove Network Tab, Add to Settings ✅
**Files to modify:**
- `rpi_gateway/app/web/templates/base.html` - Remove WiFi nav item
- `rpi_gateway/app/web/templates/settings.html` - Add WiFi section
- `rpi_gateway/app/web/routes.py` - Keep endpoints, remove `/wifi-setup` page route

**Changes:**
```python
# Remove this route from routes.py
@web_bp.route('/wifi-setup')
def wifi_setup():
    # DELETE THIS - no longer needed
```

**Add to settings.html:**
- Current WiFi status (SSID, IP, signal strength)
- Disconnect button (if connected)
- "Provisioning Mode: Active" indicator (if in hotspot mode)

#### Task 1.2: Static QR Code for Hotspot Connection
**Files to modify:**
- `rpi_gateway/app/utils/wifi_manager.py` - Generate WiFi QR code
- `rpi_gateway/app/web/templates/dashboard.html` - Display QR when in hotspot mode
- `rpi_gateway/app/web/static/` - Add QR code library or pre-generate QR

**QR Format:**
```
WIFI:T:nopass;S:RPi_IoT_Provisioning;P:;;
```

**Implementation:**
```python
import qrcode
from io import BytesIO
import base64

def generate_wifi_qr(ssid: str, password: str = None, security: str = "nopass"):
    """Generate WiFi QR code as base64 image"""
    if password:
        wifi_string = f"WIFI:T:WPA;S:{ssid};P:{password};;"
    else:
        wifi_string = f"WIFI:T:nopass;S:{ssid};P:;;"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(wifi_string)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"
```

#### Task 1.3: Auto-Enable Hotspot on Boot/Disconnect
**Files to modify:**
- `rpi_gateway/app/main.py` - Add startup network check
- `rpi_gateway/app/utils/wifi_manager.py` - Add `ensure_connectivity()`

**Logic:**
```python
def ensure_connectivity():
    """Ensure device has network connectivity"""
    if not is_connected_to_wifi():
        logger.info("[WIFI] No network connection, starting hotspot...")
        start_hotspot()
    else:
        logger.info(f"[WIFI] Connected to {get_current_ssid()}")
```

**Add to main.py startup:**
```python
# In MASHOrchestrator.__init__
from utils.wifi_manager import WiFiManager
self.wifi = WiFiManager()
self.wifi.ensure_connectivity()
```

#### Task 1.4: Enhanced WiFi Endpoints
**Files to modify:**
- `rpi_gateway/app/web/routes.py`

**Current Endpoints (Keep):**
- `GET /wifi-scan` - Returns available networks
- `POST /wifi-connect` - Connect to network
- `GET /wifi-status` - Current connection status

**New Endpoints (Add):**
- `GET /wifi-qr` - Return QR code as base64 image
- `POST /wifi-disconnect` - Disconnect and enable hotspot
- `GET /wifi-mode` - Return current mode (station/hotspot)

**Example:**
```python
@web_bp.route('/api/wifi-qr')
def get_wifi_qr():
    """Get QR code for hotspot connection"""
    from utils.wifi_manager import generate_wifi_qr
    
    if WiFiManager.is_hotspot_active():
        qr_data = generate_wifi_qr("RPi_IoT_Provisioning")
        return jsonify({'success': True, 'qr': qr_data})
    else:
        return jsonify({'success': False, 'error': 'Hotspot not active'})
```

---

### Phase 2: Mobile App Changes

#### Task 2.1: Remove Demo Mode
**Files to modify:**
- `lib/core/config/app_config.dart` - Already removed (per PRODUCTION_IOT_MIGRATION_GUIDE.md)
- `lib/presentation/screens/home/home_screen.dart` - Verify no demo references
- `lib/services/device_provisioning_service.dart` - Clean up any demo logic

**Verify:**
```dart
// Ensure these are removed:
// - AppConfig.isDemoMode
// - Mock device auto-connection
// - Demo device constants
```

#### Task 2.2: Use RPi's WiFi Scan (Not Phone's)
**Files to modify:**
- `lib/services/device_provisioning_service.dart`

**Current Issue:** Mobile might use phone's WiFi scan (includes 5GHz)
**Solution:** Always use RPi's `/wifi-scan` endpoint

**Implementation:**
```dart
Future<List<WiFiNetwork>> scanNetworksFromDevice(String deviceIp) async {
  // Force using device's scan, not phone's
  final response = await dio.get('http://$deviceIp:5000/wifi-scan');
  
  if (response.statusCode == 200) {
    final networks = (response.data['networks'] as List)
        .map((n) => WiFiNetwork.fromJson(n))
        .toList();
    
    // Filter to 2.4GHz only (optional, RPi should already do this)
    return networks.where((n) => n.frequency < 5000).toList();
  }
  
  throw Exception('Failed to scan networks from device');
}
```

#### Task 2.3: Enhanced Provisioning Flow UI
**Files to modify:**
- `lib/presentation/screens/devices/device_connection_screen.dart`

**New Flow:**
1. Show "Scan for QR Code" instruction
2. User scans QR → connects to RPi hotspot manually
3. App detects connection to `RPi_IoT_Provisioning`
4. Show discovered device at `10.42.0.1`
5. User taps device → shows WiFi networks FROM RPi
6. User selects network, enters password
7. Send to RPi via `/wifi-connect`
8. Show connection progress
9. On success → prompt to reconnect to home WiFi
10. Discover device again via mDNS

**UI Additions:**
```dart
// Step 1: QR Scan Instruction
Widget _buildQRScanInstruction() {
  return Card(
    child: Padding(
      padding: EdgeInsets.all(16),
      child: Column(
        children: [
          Icon(Icons.qr_code_scanner, size: 64),
          SizedBox(height: 16),
          Text('Scan the QR code displayed on your device'),
          SizedBox(height: 8),
          Text('This will connect you to the device\'s setup network',
              style: TextStyle(color: Colors.grey)),
        ],
      ),
    ),
  );
}

// Step 2: Hotspot Detection
bool _isConnectedToDeviceHotspot() {
  final currentWifi = _connectivity.getCurrentWifi();
  return currentWifi?.ssid == 'RPi_IoT_Provisioning';
}
```

#### Task 2.4: Post-Connection Reconnect Logic
**Files to modify:**
- `lib/services/device_provisioning_service.dart`

**Logic:**
```dart
Future<void> provisionDevice({
  required String ssid,
  required String password,
}) async {
  // 1. Send credentials to device
  await sendWiFiCredentials(ssid, password);
  
  // 2. Wait for device to connect (30s timeout)
  await _waitForDeviceConnection();
  
  // 3. Prompt user to reconnect to home WiFi
  _showReconnectDialog();
  
  // 4. After user reconnects, discover device via mDNS
  await _rediscoverDevice();
}
```

---

### Phase 3: MQTT/Cloud Integration

#### Task 3.1: Enable MQTT Client
**Files to modify:**
- `rpi_gateway/app/cloud/mqtt_client.py` - Activate MQTT connection
- `rpi_gateway/app/main.py` - Initialize MQTT on startup
- `rpi_gateway/config/.env` - Add MQTT credentials

**MQTT Topics:**
```
mash/{device_id}/sensor_data   → Publish sensor readings
mash/{device_id}/commands      → Subscribe to actuator commands
mash/{device_id}/status        → Publish online/offline status
```

#### Task 3.2: Mobile App MQTT Fallback
**Files to modify:**
- `lib/services/` - Add `mqtt_service.dart`
- `lib/presentation/providers/device_provider.dart` - Use MQTT when not on local network

**Logic:**
```dart
Future<void> connectToDevice(String deviceId) async {
  // Try local connection first (mDNS)
  if (await _tryLocalConnection(deviceId)) {
    _connectionType = 'local';
    return;
  }
  
  // Fallback to cloud/MQTT
  if (await _tryMQTTConnection(deviceId)) {
    _connectionType = 'remote';
    return;
  }
  
  throw Exception('Cannot connect to device');
}
```

---

## File Modifications Checklist

### RPi Gateway (`MASH-IoT/rpi_gateway/`)
- [ ] `app/web/templates/base.html` - Remove WiFi nav tab
- [ ] `app/web/templates/settings.html` - Add WiFi section
- [ ] `app/web/templates/dashboard.html` - Add QR code display (when in hotspot mode)
- [ ] `app/web/routes.py` - Remove `/wifi-setup` route, add QR endpoint
- [ ] `app/utils/wifi_manager.py` - Add QR generation, auto-hotspot logic
- [ ] `app/main.py` - Add startup connectivity check
- [ ] `app/cloud/mqtt_client.py` - Implement MQTT connection
- [ ] `config/.env` - Add MQTT credentials
- [ ] `requirements.txt` - Add `qrcode` and `Pillow` packages

### Mobile App (`MASH-Grower-Mobile/`)
- [ ] `lib/services/device_provisioning_service.dart` - Use RPi WiFi scan
- [ ] `lib/presentation/screens/devices/device_connection_screen.dart` - New provisioning UI
- [ ] `lib/services/mqtt_service.dart` - Create MQTT service
- [ ] `lib/presentation/providers/device_provider.dart` - Add MQTT fallback
- [ ] `pubspec.yaml` - Add MQTT package (`mqtt_client`)

---

## Testing Plan

### Manual Testing Steps

1. **Hotspot QR Code Test**
   - Disconnect RPi from WiFi
   - Verify hotspot starts automatically
   - Check QR code displays on web UI
   - Scan QR with phone → should prompt to connect

2. **WiFi Provisioning Test**
   - Connect phone to RPi hotspot
   - Open mobile app
   - Navigate to "Connect Device"
   - Verify device shows at 10.42.0.1
   - Tap device → verify WiFi networks load from RPi
   - Select network, enter password
   - Verify connection succeeds
   - Verify RPi switches to station mode
   - Reconnect phone to home WiFi
   - Verify device discoverable via mDNS

3. **Settings WiFi Display Test**
   - Navigate to Settings in RPi web UI
   - Verify current WiFi shows (SSID, IP, signal)
   - Test disconnect button
   - Verify hotspot activates after disconnect

4. **MQTT Remote Access Test**
   - Connect mobile to different network (4G/5G)
   - Verify device accessible via MQTT
   - Test sensor data reading
   - Test actuator control

---

## Implementation Priority

### Must Have (v1.1.0)
1. ✅ Remove demo mode
2. ✅ Use RPi WiFi scan
3. ✅ QR code for hotspot
4. ✅ Auto-hotspot on boot/disconnect
5. ✅ Settings page WiFi section

### Should Have (v1.1.0)
6. Enhanced provisioning UI
7. Post-connection reconnect flow
8. Error handling for failed connections

### Nice to Have (v1.2.0)
9. MQTT integration
10. Remote access outside local network
11. Connection health monitoring

---

## Next Steps

1. **Start with RPi changes** (easier to test independently)
2. **Update mobile app** (requires RPi to be ready)
3. **Test locally** (same network)
4. **Add MQTT** (remote access)
5. **Version bump** to v1.1.0

**Estimated Time:** 2-3 days for core features, +1 day for MQTT

---

## Questions/Decisions Needed

1. **QR Code location:** Dashboard or dedicated provisioning page?
   - **Recommendation:** Dashboard with prominent "Setup WiFi" card when in hotspot mode

2. **Password storage:** Save WiFi credentials on RPi?
   - **Recommendation:** Yes, in NetworkManager (already done by nmcli)

3. **Hotspot SSID:** Keep `RPi_IoT_Provisioning` or use device-specific name?
   - **Recommendation:** Add device serial: `RPi_IoT_{LAST_4_MAC_DIGITS}`

4. **Connection timeout:** How long to wait for RPi to connect?
   - **Recommendation:** 30 seconds, then fallback to hotspot

5. **Multiple devices:** How to handle multiple RPi devices?
   - **Recommendation:** Each device has unique hotspot SSID based on MAC address

---

Ready to start implementation? Let me know which phase to begin with!

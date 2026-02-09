# WiFi Provisioning: Complete Implementation Guide

**Implementation Date:** February 3, 2026  
**Status:** Ready for Review → Implementation  
**Version:** Will bump to v1.1.0 after completion

---

## Summary of Changes

This implementation removes the need for physical keyboard on RPi and enables full WiFi provisioning through the mobile app using QR code scanning.

### Key Flow
1. RPi boots → Check network → If no connection, start hotspot
2. RPi displays QR code on dashboard (for WiFi connection)
3. User scans QR → connects to RPi hotspot
4. Mobile app discovers device at 10.42.0.1
5. User selects WiFi network (from RPi's 2.4GHz scan)
6. User enters password → sends to RPi
7. RPi connects to network → disables hotspot
8. User reconnects phone → discovers device via mDNS
9. Full local network access established

---

## Implementation Steps

Let me guide you through each file modification with exact code changes.

### Step 1: Install Required Python Package

```bash
cd MASH-IoT/rpi_gateway
pip install qrcode[pil]
```

Add to `requirements.txt`:
```txt
qrcode[pil]==7.4.2
```

### Step 2: Remove WiFi Nav Tab

**File:** `rpi_gateway/app/web/templates/base.html`

**Change:** Remove line 52 (WiFi navigation item)

**Before:**
```html
<li><a href="{{ url_for('web.wifi_setup') }}"><i class="fas fa-wifi"></i> WiFi</a></li>
```

**After:** (Delete this line entirely)

---

### Step 3: Enhanced WiFi Manager with QR Generation

**File:** `rpi_gateway/app/utils/wifi_manager.py`

**Add these imports at the top:**
```python
import qrcode
from io import BytesIO
import base64
```

**Add this function before the WiFiManager class:**
```python
def generate_wifi_qr_code(ssid: str, password: str = "", security: str = "nopass") -> str:
    """
    Generate WiFi QR code as base64 image
    
    QR Format: WIFI:T:<security>;S:<ssid>;P:<password>;;
    - T: Security type (nopass, WEP, WPA)
    - S: SSID (network name)
    - P: Password (empty for open networks)
    
    Returns base64-encoded PNG image string
    """
    if password:
        wifi_string = f"WIFI:T:WPA;S:{ssid};P:{password};;"
    else:
        wifi_string = f"WIFI:T:{security};S:{ssid};P:;;"
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(wifi_string)
    qr.make(fit=True)
    
    # Generate image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return f"data:image/png;base64,{img_base64}"
```

**Add this method to WiFiManager class:**
```python
def ensure_connectivity(self):
    """
    Ensure device has network connectivity.
    If not connected to WiFi, start hotspot automatically.
    """
    if not self.is_connected_to_wifi():
        logger.info("[WIFI] No network connection detected")
        
        # Check if hotspot is already active
        if self.is_hotspot_active():
            logger.info("[WIFI] Hotspot already active")
        else:
            logger.info("[WIFI] Starting provisioning hotspot...")
            success = self.start_hotspot()
            if success:
                logger.info("[WIFI] ✅ Hotspot started successfully")
            else:
                logger.error("[WIFI] ❌ Failed to start hotspot")
    else:
        current_ssid = self.get_current_ssid()
        logger.info(f"[WIFI] ✅ Connected to '{current_ssid}'")
```

---

### Step 4: Add QR and WiFi Status Endpoints

**File:** `rpi_gateway/app/web/routes.py`

**Add these new routes (after existing WiFi routes around line 400):**

```python
@web_bp.route('/api/wifi-qr')
def get_wifi_qr():
    """Get QR code for connecting to provisioning hotspot"""
    try:
        from utils.wifi_manager import WiFiManager, generate_wifi_qr_code
        
        wifi_mgr = WiFiManager()
        
        # Only provide QR if in hotspot mode
        if wifi_mgr.is_hotspot_active():
            qr_data = generate_wifi_qr_code("RPi_IoT_Provisioning")
            return jsonify({
                'success': True,
                'qr_code': qr_data,
                'ssid': 'RPi_IoT_Provisioning',
                'ip': '10.42.0.1',
                'instructions': 'Scan this QR code with your phone to connect to the device'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Device is not in provisioning mode'
            }), 400
            
    except Exception as e:
        logger.error(f"[API] QR generation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@web_bp.route('/api/wifi-mode')
def get_wifi_mode():
    """Get current WiFi mode (station/hotspot)"""
    try:
        from utils.wifi_manager import WiFiManager
        
        wifi_mgr = WiFiManager()
        
        if wifi_mgr.is_hotspot_active():
            return jsonify({
                'success': True,
                'mode': 'hotspot',
                'ssid': 'RPi_IoT_Provisioning',
                'ip': '10.42.0.1'
            })
        elif wifi_mgr.is_connected_to_wifi():
            return jsonify({
                'success': True,
                'mode': 'station',
                'ssid': wifi_mgr.get_current_ssid(),
                'ip': wifi_mgr.get_current_ip()
            })
        else:
            return jsonify({
                'success': True,
                'mode': 'disconnected'
            })
            
    except Exception as e:
        logger.error(f"[API] WiFi mode check error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@web_bp.route('/api/wifi-scan')
def scan_wifi_networks():
    """Scan for available WiFi networks (2.4GHz only for RPi compatibility)"""
    try:
        from utils.wifi_manager import WiFiManager
        
        wifi_mgr = WiFiManager()
        networks = wifi_mgr.get_wifi_list()
        
        # Filter to 2.4GHz only (optional - RPi should already only see 2.4GHz)
        # Frequency < 5000 MHz = 2.4GHz band
        filtered_networks = [n for n in networks if n.get('frequency', 0) < 5000]
        
        return jsonify({
            'success': True,
            'networks': filtered_networks
        })
        
    except Exception as e:
        logger.error(f"[API] WiFi scan error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

### Step 5: Update Dashboard with QR Code

**File:** `rpi_gateway/app/web/templates/dashboard.html`

**Add after the status-bar div (around line 17):**

```html
<!-- WiFi Provisioning QR Code (shown only in hotspot mode) -->
<div id="wifi-provisioning-card" class="card" style="display: none;">
    <div class="card-header">
        <i class="fas fa-qrcode"></i>
        <h3>Device Provisioning</h3>
    </div>
    <div class="card-body">
        <div style="text-align: center;">
            <p style="margin-bottom: 20px;">
                <strong>Connect to this device using your mobile phone</strong>
            </p>
            <p style="color: #666; margin-bottom: 20px;">
                Scan this QR code to connect to the provisioning network
            </p>
            <div id="qr-code-container" style="margin: 20px auto;">
                <img id="qr-code-image" src="" alt="WiFi QR Code" style="max-width: 300px; width: 100%;">
            </div>
            <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 20px;">
                <p style="margin: 5px 0;"><strong>Network:</strong> RPi_IoT_Provisioning</p>
                <p style="margin: 5px 0;"><strong>IP Address:</strong> 10.42.0.1</p>
                <p style="margin: 5px 0;"><strong>Security:</strong> Open (No Password)</p>
            </div>
            <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 8px;">
                <p style="margin: 0; color: #856404;">
                    <i class="fas fa-info-circle"></i>
                    Once scanned, use the MASH Grower Mobile app to complete WiFi setup
                </p>
            </div>
        </div>
    </div>
</div>
```

**Add to the JavaScript section at the bottom:**

```javascript
// Check WiFi mode and display QR if in provisioning mode
async function checkProvisioningMode() {
    try {
        const response = await fetch('/api/wifi-mode');
        const data = await response.json();
        
        if (data.success && data.mode === 'hotspot') {
            // Device is in provisioning mode - show QR code
            document.getElementById('wifi-provisioning-card').style.display = 'block';
            
            // Fetch and display QR code
            const qrResponse = await fetch('/api/wifi-qr');
            const qrData = await qrResponse.json();
            
            if (qrData.success) {
                document.getElementById('qr-code-image').src = qrData.qr_code;
            }
        } else {
            // Connected to network - hide provisioning card
            document.getElementById('wifi-provisioning-card').style.display = 'none';
        }
    } catch (error) {
        console.error('Error checking provisioning mode:', error);
    }
}

// Check provisioning mode on page load and every 10 seconds
document.addEventListener('DOMContentLoaded', function() {
    checkProvisioningMode();
    setInterval(checkProvisioningMode, 10000);
});
```

---

### Step 6: Update Settings Page with WiFi Status

**File:** `rpi_gateway/app/web/templates/settings.html`

**Replace the WiFi Configuration section (lines 10-20) with:**

```html
<!-- WiFi Status and Control -->
<div class="setting-card">
    <div class="setting-icon">
        <i class="fas fa-wifi"></i>
    </div>
    <div class="setting-content">
        <h3>WiFi Connection</h3>
        <p>View current network status and manage connection</p>
        
        <div id="wifi-status-container" style="margin-top: 20px;">
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i> Loading WiFi status...
            </div>
        </div>
        
        <div id="wifi-controls" style="margin-top: 20px; display: none;">
            <!-- Disconnect button (shown when connected) -->
            <button id="disconnect-btn" class="setting-button" style="background: #f44336;">
                <i class="fas fa-unlink"></i> Disconnect and Enable Provisioning
            </button>
        </div>
    </div>
</div>

<script>
// Load WiFi status
async function loadWiFiStatus() {
    try {
        const response = await fetch('/api/wifi-mode');
        const data = await response.json();
        
        const container = document.getElementById('wifi-status-container');
        const controls = document.getElementById('wifi-controls');
        
        if (!data.success) {
            container.innerHTML = '<p style="color: #f44336;">Failed to load WiFi status</p>';
            return;
        }
        
        if (data.mode === 'station') {
            // Connected to WiFi
            container.innerHTML = `
                <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50;">
                    <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: #4CAF50;">Connected</span></p>
                    <p style="margin: 5px 0;"><strong>Network:</strong> ${data.ssid}</p>
                    <p style="margin: 5px 0;"><strong>IP Address:</strong> ${data.ip}</p>
                </div>
            `;
            controls.style.display = 'block';
            
        } else if (data.mode === 'hotspot') {
            // In provisioning mode
            container.innerHTML = `
                <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ff9800;">
                    <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: #ff9800;">Provisioning Mode</span></p>
                    <p style="margin: 5px 0;"><strong>Hotspot SSID:</strong> ${data.ssid}</p>
                    <p style="margin: 5px 0;"><strong>IP Address:</strong> ${data.ip}</p>
                    <p style="margin: 10px 0 0 0; color: #856404;">
                        <i class="fas fa-info-circle"></i>
                        Device is waiting for WiFi configuration. Use the MASH Grower Mobile app to connect.
                    </p>
                </div>
            `;
            controls.style.display = 'none';
            
        } else {
            // Disconnected
            container.innerHTML = `
                <div style="background: #ffebee; padding: 15px; border-radius: 8px; border-left: 4px solid #f44336;">
                    <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: #f44336;">Disconnected</span></p>
                    <p style="margin: 5px 0;">No network connection</p>
                </div>
            `;
            controls.style.display = 'none';
        }
        
    } catch (error) {
        console.error('Error loading WiFi status:', error);
        document.getElementById('wifi-status-container').innerHTML = 
            '<p style="color: #f44336;">Error loading WiFi status</p>';
    }
}

// Disconnect from WiFi
document.addEventListener('DOMContentLoaded', function() {
    loadWiFiStatus();
    
    // Refresh every 10 seconds
    setInterval(loadWiFiStatus, 10000);
    
    // Disconnect button handler
    document.getElementById('disconnect-btn').addEventListener('click', async function() {
        if (!confirm('Disconnect from current network? Device will enter provisioning mode.')) {
            return;
        }
        
        try {
            const response = await fetch('/wifi-disconnect', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                alert('Disconnected successfully. Device is now in provisioning mode.');
                setTimeout(loadWiFiStatus, 2000);
            } else {
                alert('Failed to disconnect: ' + data.error);
            }
        } catch (error) {
            alert('Error disconnecting: ' + error.message);
        }
    });
});
</script>
```

---

### Step 7: Add Auto-Connectivity Check on RPi Startup

**File:** `rpi_gateway/app/main.py`

**Add in `MASHOrchestrator.__init__` method after WiFi manager initialization:**

```python
        # Initialize WiFi manager and ensure connectivity
        from utils.wifi_manager import WiFiManager
        self.wifi_manager = WiFiManager()
        
        # Auto-start hotspot if not connected to network
        logger.info("[INIT] Checking network connectivity...")
        self.wifi_manager.ensure_connectivity()
```

---

### Step 8: Update Mobile App Device Provisioning

**File:** `MASH-Grower-Mobile/lib/services/device_provisioning_service.dart`

**Update the `scanWiFiNetworks` method to use RPi's scan:**

```dart
/// Scan WiFi networks from the connected device (not from phone)
/// This ensures we only see 2.4GHz networks compatible with RPi
Future<List<Map<String, dynamic>>> scanWiFiNetworks(String deviceIp) async {
  try {
    Logger.info('📡 Scanning WiFi networks from device: $deviceIp');
    
    final response = await _dio.get(
      'http://$deviceIp:5000/api/wifi-scan',
      options: Options(
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 10),
      ),
    );
    
    if (response.statusCode == 200 && response.data['success'] == true) {
      final networks = (response.data['networks'] as List)
          .map((n) => n as Map<String, dynamic>)
          .toList();
      
      Logger.info('✅ Found ${networks.length} networks from device');
      return networks;
    } else {
      throw Exception('Failed to scan networks: ${response.data['error']}');
    }
  } catch (e) {
    Logger.error('❌ Network scan from device failed', e);
    throw Exception('Failed to scan networks from device: $e');
  }
}
```

---

### Step 9: Update Provisioning Flow UI

**File:** `MASH-Grower-Mobile/lib/presentation/screens/devices/device_connection_screen.dart`

**Add prominent QR scan instruction at the top:**

```dart
Widget _buildQRScanInstruction() {
  return Card(
    margin: const EdgeInsets.all(16),
    child: Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          Icon(
            Icons.qr_code_scanner,
            size: 64,
            color: Theme.of(context).colorScheme.primary,
          ),
          const SizedBox(height: 16),
          Text(
            'Setup New Device',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'Look at your device\'s screen and scan the QR code',
            style: Theme.of(context).textTheme.bodyLarge,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'This will connect your phone to the device\'s setup network',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Colors.grey[600],
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: () {
              // Open device settings to WiFi
              // User manually scans QR and connects
              _showQRScanGuide();
            },
            icon: const Icon(Icons.wifi),
            label: const Text('Open WiFi Settings'),
          ),
        ],
      ),
    ),
  );
}

void _showQRScanGuide() {
  showDialog(
    context: context,
    builder: (context) => AlertDialog(
      title: const Text('Connect to Device'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('1. Scan the QR code on your device screen'),
          const SizedBox(height: 8),
          const Text('2. Your phone will prompt you to connect'),
          const SizedBox(height: 8),
          const Text('3. Tap "Connect" or "Join"'),
          const SizedBox(height: 8),
          const Text('4. Return to this app'),
          const SizedBox(height: 16),
          Text(
            'Network: RPi_IoT_Provisioning\nIP: 10.42.0.1',
            style: TextStyle(
              fontFamily: 'monospace',
              backgroundColor: Colors.grey[200],
            ),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Got it'),
        ),
      ],
    ),
  );
}
```

---

## Testing Checklist

### Pre-Implementation Testing
- [ ] Verify current WiFi routes work
- [ ] Test existing provisioning flow
- [ ] Backup current configuration

### Post-Implementation Testing

#### RPi Gateway Tests
- [ ] Install qrcode package: `pip install qrcode[pil]`
- [ ] Restart RPi gateway: `python -m app.main`
- [ ] Disconnect from WiFi → verify hotspot starts
- [ ] Check dashboard shows QR code
- [ ] Verify QR code is scannable
- [ ] Check settings page shows WiFi status
- [ ] Test disconnect button in settings

#### Mobile App Tests  
- [ ] Scan QR code → connects to RPi hotspot
- [ ] Open app → discovers device at 10.42.0.1
- [ ] Verify WiFi scan shows RPi's networks (not phone's)
- [ ] Select network, enter password
- [ ] Verify connection success
- [ ] Reconnect phone to home WiFi
- [ ] Verify device discovered via mDNS

#### Integration Tests
- [ ] Full provisioning flow (start to finish)
- [ ] Failed password → returns to hotspot
- [ ] Multiple reconnection attempts
- [ ] Settings page updates after connection

---

## Version Bump

After successful testing:

```bash
python version_manager.py bump all minor
# Mobile: 1.0.0+1 → 1.1.0+2
# RPi: 1.0.0 → 1.1.0
# Arduino: 1.0.0 (no changes)
```

Update `version` file changelog with these features.

---

## Next Phase: MQTT Integration (v1.2.0)

After WiFi provisioning is stable, add MQTT for remote access outside local network.

---

**Ready to implement? Review this guide and let me know if you want to proceed with the changes!**

# Mobile App Connection Fix Summary

## Problem
- Mobile app could detect RPi device via mDNS ✅
- Mobile app failed to connect to detected device ❌

## Root Causes
1. **Missing `/status` endpoint** - Mobile app calls `testConnection()` which hits `/status`
2. **Missing CORS headers** - Cross-origin requests from mobile app were blocked
3. **Missing `/provisioning/info` endpoint** - Mobile app expects device provisioning status
4. **Device ID sanitization** - Serial number "MASH-B2-CAL26-CE637C" not RFC 6763 compliant

## Fixes Applied

### 1. Device ID Sanitization (mdns_advertiser.py)
```python
# Added sanitize_device_id() function
# MASH-B2-CAL26-CE637C → mash-b2-cal26-ce637c
# Ensures RFC 6763 compliance for mDNS service names
```

### 2. CORS Support (main.py)
```python
from flask_cors import CORS

CORS(self.app, resources={
    r"/api/*": {"origins": "*"},
    r"/status": {"origins": "*"},
    r"/dashboard": {"origins": "*"},
    r"/provisioning/*": {"origins": "*"},
    r"/wifi-*": {"origins": "*"},
})
```

### 3. Health Check Endpoint (routes.py)
```python
@web_bp.route('/status', methods=['GET'])
def get_status():
    """Health check endpoint for device connection testing."""
    return jsonify({
        'success': True,
        'status': 'online',
        'device_id': ...,
        'device_name': ...,
        'timestamp': time.time()
    })
```

### 4. Provisioning Info Endpoint (routes.py)
```python
@web_bp.route('/provisioning/info', methods=['GET'])
def provisioning_info():
    """Returns device provisioning status and network info."""
    return jsonify({
        'success': True,
        'data': {
            'active': is_provisioning,
            'device_id': ...,
            'network_connected': ...,
            ...
        }
    })
```

### 5. Local IP Helper (wifi_manager.py)
```python
def get_local_ip():
    """Get device's local IP address."""
    # Uses hostname -I and socket fallback
```

### 6. Updated Requirements
```
Flask-CORS==4.0.0  # Added for cross-origin support
zeroconf==0.120.0  # Already present, verified version
```

## Deployment Steps

### Step 1: Update Code on RPi
```bash
cd ~/MASH-IoT
git pull
```

### Step 2: Install Flask-CORS
```bash
cd ~/MASH-IoT/rpi_gateway
source venv/bin/activate
pip install Flask-CORS==4.0.0
```

### Step 3: Restart Flask Service
```bash
sudo systemctl restart mash-iot-gateway
```

### Step 4: Verify Logs
```bash
sudo journalctl -u mash-iot-gateway -f
```

**Expected output:**
```
[mDNS] Initialized with ID: mash-b2-cal26-ce637c (from: MASH-B2-CAL26-CE637C)
[mDNS] ✓ Service advertised successfully
[mDNS]   Service Name: mash-b2-cal26-ce637c._mash-iot._tcp.local.
[mDNS]   Device ID: mash-b2-cal26-ce637c
[mDNS]   Display Name: MASH IoT Chamber
[mDNS]   IP Address: 192.168.x.x
[mDNS]   Port: 5000
[WEB] Starting Flask server on 0.0.0.0:5000
```

### Step 5: Test mDNS Discovery
```bash
avahi-browse -r _mash-iot._tcp
```

### Step 6: Test Connection Endpoints
```bash
# Health check
curl http://192.168.x.x:5000/status

# Should return:
# {"success": true, "status": "online", "device_id": "MASH-B2-CAL26-CE637C", ...}

# Provisioning info
curl http://192.168.x.x:5000/provisioning/info

# Should return:
# {"success": true, "data": {"active": false, "device_id": "MASH-B2-CAL26-CE637C", ...}}
```

### Step 7: Test from Mobile App
1. Open MASH Grower Mobile app
2. Go to "Connect to Chamber" screen
3. Tap "Scan for Devices"
4. Device should appear as "mash-b2-cal26-ce637c"
5. Tap device to connect
6. Should show "Connected" status ✅

## Troubleshooting

### Device Still Not Connecting

**Check 1: CORS Headers**
```bash
curl -H "Origin: http://localhost" -I http://192.168.x.x:5000/status
```
Should see: `Access-Control-Allow-Origin: *`

**Check 2: Flask-CORS Installed**
```bash
source ~/MASH-IoT/rpi_gateway/venv/bin/activate
pip list | grep Flask-CORS
```
Should show: `Flask-CORS    4.0.0`

**Check 3: Endpoint Exists**
```bash
curl http://192.168.x.x:5000/status
```
Should NOT return 404

**Check 4: Firewall**
```bash
sudo ufw status
```
Port 5000 should be allowed

**Check 5: Mobile App Logs**
In Flutter app, check debug console for:
```
[LocalDeviceClient] Connection test failed: ...
[LocalDeviceClient] Failed to connect to device: ...
```

### mDNS Discovery Issues

**Check 1: Avahi Running**
```bash
sudo systemctl status avahi-daemon
```

**Check 2: Service Registered**
```bash
avahi-browse -r _mash-iot._tcp
```
Should show: `mash-b2-cal26-ce637c`

**Check 3: zeroconf Installed**
```bash
source ~/MASH-IoT/rpi_gateway/venv/bin/activate
pip list | grep zeroconf
```
Should show: `zeroconf    0.120.0`

## Files Modified

1. `rpi_gateway/app/utils/mdns_advertiser.py` - Device ID sanitization
2. `rpi_gateway/app/main.py` - CORS configuration
3. `rpi_gateway/app/web/routes.py` - `/status` and `/provisioning/info` endpoints
4. `rpi_gateway/app/utils/wifi_manager.py` - `get_local_ip()` function
5. `rpi_gateway/requirements.txt` - Added Flask-CORS

## Expected Behavior After Fix

### mDNS Discovery
- Device broadcasts as: `mash-b2-cal26-ce637c._mash-iot._tcp.local.`
- Mobile app sees: "MASH IoT Chamber" with device ID "mash-b2-cal26-ce637c"

### Connection Flow
1. Mobile app discovers device via mDNS
2. Mobile app calls `http://192.168.x.x:5000/status` (health check)
3. Server responds with 200 OK + device info
4. Mobile app marks device as "Connected"
5. Mobile app can now call other endpoints:
   - `/api/latest_data` - Sensor readings
   - `/api/actuator_states` - Actuator status
   - `/api/control_actuator` - Control commands
   - `/provisioning/info` - Provisioning status

## Technical Details

### Why Flask-CORS?
- Mobile app makes cross-origin requests (different domain/port)
- Without CORS headers, browser/Flutter blocks requests for security
- Flask-CORS adds proper `Access-Control-Allow-Origin` headers

### Why /status Endpoint?
- Mobile app's `LocalDeviceClient.testConnection()` needs lightweight ping
- Alternative to loading full dashboard HTML
- Returns JSON for programmatic parsing

### Why Device ID Sanitization?
- mDNS service names must follow RFC 6763 (DNS-SD)
- Only alphanumeric, hyphens, underscores allowed
- Serial "MASH-B2-CAL26-CE637C" has invalid characters for service name
- Sanitized to "mash-b2-cal26-ce637c" for compatibility

## Success Criteria

✅ Device appears in mobile app device list  
✅ Mobile app can connect to device  
✅ Mobile app shows "Connected" status  
✅ Mobile app can fetch sensor data  
✅ Mobile app can control actuators  
✅ No CORS errors in logs  
✅ /status returns 200 OK  
✅ /provisioning/info returns device info

---

**Date:** February 3, 2026  
**Issue:** Mobile app connection failure after mDNS discovery  
**Resolution:** Added CORS support, /status endpoint, device ID sanitization  
**Status:** Ready for deployment and testing

# WiFi Network Switching with Automatic Fallback

## Overview
Enhanced WiFi management system with intelligent network switching, credential storage, and automatic fallback to last known network on connection failure.

## Features Implemented

### 1. **Smart Network Switching**
- Automatically detects if device is currently connected
- Disconnects from current network before connecting to new one
- Prevents connection conflicts and ensures clean handoff

### 2. **Credential Storage**
- Saves last successful WiFi credentials to `config/wifi_credentials.json`
- Stores SSID, password, and timestamp
- Used for automatic fallback on connection failure

### 3. **Automatic Fallback**
- If new connection fails, automatically attempts to reconnect to previous network
- Uses saved credentials to restore connection
- Recreates connection profile if necessary
- Provides detailed console logging of rollback process

### 4. **Manual Disconnect**
- New "Disconnect" button on WiFi Setup page
- Allows user to disconnect from internet at any time
- Confirms action before disconnecting
- Refreshes page to show updated status

### 5. **Connection Status API**
- New `/api/wifi_status` endpoint
- Returns current connection status, connected network, and last known network
- Can be used for monitoring and UI updates

## File Changes

### `rpi_gateway/app/utils/wifi_manager.py`
**New Functions:**
- `save_wifi_credentials(ssid, password)` - Saves credentials to JSON file
- `load_wifi_credentials()` - Loads saved credentials
- `disconnect_wifi()` - Disconnects from current network
- `_rollback_connection(backup_ssid, backup_password, original_network)` - Internal helper for fallback

**Modified Functions:**
- `connect_to_wifi(ssid, password, save_credentials=True)` - Enhanced with:
  - Automatic disconnection from current network
  - Credential backup before switching
  - Automatic rollback on failure
  - Credential saving on success
  - Better error handling and logging

### `rpi_gateway/app/web/routes.py`
**New Routes:**
- `/wifi-disconnect` [POST] - Disconnects from WiFi, returns JSON status
- `/api/wifi_status` [GET] - Returns connection status and saved networks

### `rpi_gateway/app/web/templates/wifi_setup.html`
**Changes:**
- Added "Disconnect" button in connection status card
- Added `disconnectWiFi()` JavaScript function
- Updated info section with new features description
- Added confirmation dialog before disconnect

### `rpi_gateway/app/web/static/css/styles.css`
**New Styles:**
- `.btn-danger` - Red gradient button for disconnect action
- Hover and active states for danger button
- Matches design consistency with primary buttons

## Usage Flow

### Connecting to New Network:
```
1. User opens WiFi Setup page
2. Page shows current connection (if any)
3. User selects new network and enters password
4. System flow:
   a. Detect current network → Save as backup
   b. Load backup credentials (if available)
   c. Disconnect from current network
   d. Create new connection profile
   e. Attempt connection (25s timeout)
   f. On success:
      - Save new credentials
      - Display success message
   g. On failure:
      - Load backup credentials
      - Attempt rollback connection
      - Try up to 2 reconnection attempts
      - If all fail, restart hotspot
```

### Disconnecting from Network:
```
1. User clicks "Disconnect" button
2. Confirmation dialog appears
3. On confirm:
   a. Send POST request to /wifi-disconnect
   b. System runs `nmcli connection down <network>`
   c. Return success/failure JSON
   d. Page reloads to show disconnected status
```

## Configuration File Structure

### `config/wifi_credentials.json`
```json
{
  "last_known_ssid": "HomeNetwork",
  "last_known_password": "password123",
  "saved_at": "2025-01-15 10:30:45"
}
```

**Location:** `MASH-IoT/config/wifi_credentials.json`

**Security Note:** This file contains sensitive credentials. Ensure proper file permissions:
```bash
chmod 600 config/wifi_credentials.json
```

## Error Handling

### Connection Failure Scenarios:
1. **Wrong Password:**
   - Connection times out after 25s
   - Automatic rollback initiated
   - Previous network restored

2. **Weak Signal:**
   - Connection fails or times out
   - Rollback to previous network
   - User can retry with closer proximity

3. **Network Not Found:**
   - Connection fails immediately
   - Rollback initiated
   - User notified to check SSID

4. **Rollback Failure:**
   - If backup network also fails
   - System attempts to recreate connection profile
   - If all fails, hotspot restart as last resort

## Console Logging

The system provides detailed console output for debugging:

```
--------------------------------------------------
[*] WiFi Manager: Switching to 'NewNetwork'...
[*] Currently connected to: OldNetwork
[*] Disconnecting from current network...
[SUCCESS] Disconnected from OldNetwork
[*] Creating connection profile for 'NewNetwork'...
[*] Connecting to network...
[FAIL] Connection timed out (wrong password or weak signal)
--------------------------------------------------
[*] ROLLBACK: Attempting to reconnect to OldNetwork...
[SUCCESS] Rolled back to OldNetwork
```

## API Endpoints

### POST `/wifi-connect`
**Purpose:** Connect to new WiFi network  
**Body:** Form data with `ssid_select`, `manual_ssid`, `password`  
**Response:** Renders connecting status page  
**Background:** Runs connection in separate thread with 2s delay

### POST `/wifi-disconnect`
**Purpose:** Disconnect from current network  
**Response:**
```json
{
  "success": true,
  "message": "Disconnected from HomeNetwork",
  "previous_network": "HomeNetwork"
}
```

### GET `/api/wifi_status`
**Purpose:** Get current WiFi status  
**Response:**
```json
{
  "connected": true,
  "current_network": "HomeNetwork",
  "last_known_network": "HomeNetwork"
}
```

## Testing Checklist

- [ ] Connect to network successfully
- [ ] Verify credentials saved to `config/wifi_credentials.json`
- [ ] Test connection with wrong password → Verify rollback
- [ ] Test connection to non-existent network → Verify rollback
- [ ] Disconnect from network manually → Verify status updates
- [ ] Switch networks while connected → Verify smooth handoff
- [ ] Test with no previous credentials → Verify graceful handling
- [ ] Verify hotspot restart if all connections fail
- [ ] Check console logs for detailed flow tracking
- [ ] Test page refresh after disconnect

## Security Considerations

1. **Credential Storage:**
   - Credentials stored in plain text for system use
   - File should have restricted permissions (600)
   - Consider encrypting in future version

2. **API Endpoints:**
   - Disconnect endpoint requires POST method (CSRF protection)
   - Consider adding authentication in production

3. **Network Scanning:**
   - WiFi scan shows all available networks
   - Consider filtering hidden networks

## Future Enhancements

1. **Credential Encryption:**
   - Encrypt stored passwords using system keyring
   - Use base64 or stronger encryption

2. **Multiple Saved Networks:**
   - Store multiple known networks
   - Auto-connect to strongest known network
   - Priority-based connection attempts

3. **Connection History:**
   - Log all connection attempts with timestamps
   - Display connection history on settings page

4. **Signal Strength Display:**
   - Show signal strength for available networks
   - Indicate connection quality

5. **Scheduled Network Switching:**
   - Allow time-based network switching
   - Useful for home/work scenarios

## Troubleshooting

### Issue: Disconnect button doesn't work
**Solution:** Check browser console for JavaScript errors, verify `/wifi-disconnect` route is accessible

### Issue: Rollback fails repeatedly
**Solution:** Check if `config/wifi_credentials.json` exists and is readable, verify nmcli is working properly

### Issue: Page doesn't refresh after disconnect
**Solution:** Ensure JavaScript `location.reload()` executes, check for browser caching

### Issue: Credentials not saving
**Solution:** Verify `config/` directory exists and is writable, check file permissions

## Dependencies

- **NetworkManager (nmcli):** Required for WiFi operations
- **Python json module:** For credential storage
- **Python subprocess:** For running nmcli commands
- **Flask:** For web routes and API endpoints

## Compatibility

- **OS:** Linux with NetworkManager (Raspberry Pi OS, Ubuntu, etc.)
- **Hardware:** Raspberry Pi with WiFi adapter
- **Browser:** Modern browsers with fetch API support

---

## Summary

This enhancement provides a robust WiFi management system that:
- ✅ Intelligently switches between networks
- ✅ Automatically falls back on failure
- ✅ Stores credentials for recovery
- ✅ Allows manual disconnection
- ✅ Provides detailed status information
- ✅ Maintains user control over connectivity

The system ensures reliable WiFi connectivity while giving users full control over their network connections.

# Deployment Checklist - System Improvements

## Pre-Deployment

### 1. Configuration Files
- [ ] Update `rpi_gateway/config/config.yaml` with hysteresis parameters (already added)
- [ ] Create/update `rpi_gateway/config/.env` with backend credentials:
  ```bash
  BACKEND_URL=https://api.mashmarket.app
  DEVICE_EMAIL=your_device@email.com
  DEVICE_PASSWORD=your_device_password
  ```

### 2. Database Schema
The system will auto-create tables, but verify `system_logs` table exists:
```sql
-- Check if table exists
SELECT name FROM sqlite_master WHERE type='table' AND name='system_logs';

-- If needed, create manually:
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    level TEXT NOT NULL,
    component TEXT NOT NULL,
    message TEXT NOT NULL,
    data TEXT
);
```

### 3. Python Dependencies
No new dependencies required. Existing requirements.txt covers all needs.

## Deployment Steps

### 1. Pull Changes from Git
```bash
cd /home/pi/MASH-IoT
git pull origin main
```

### 2. Run Update Script
```bash
cd /home/pi/MASH-IoT
./scripts/update.sh
```

This will:
- Pull latest code
- Fix script permissions
- Restart systemd services

### 3. Verify Services
```bash
# Check orchestrator status
sudo systemctl status mashiot-orchestrator

# Check logs
sudo journalctl -u mashiot-orchestrator -f

# Expected output:
# [ORCHESTRATOR] Starting M.A.S.H. IoT Orchestrator
# [ML] MushroomAI initialized
# [BACKEND] Initial connection successful
# [WEB] Flask server started on 0.0.0.0:5000
```

### 4. Test Web Interface
```bash
# From RPi terminal
curl http://localhost:5000/api/latest_data

# Expected JSON response includes:
# {
#   "arduino_connected": true/false,
#   "backend_connected": true/false,
#   "uptime": "0h 5m",
#   "fruiting": {...},
#   "spawning": {...}
# }
```

### 5. Check Kiosk Mode
- Reboot Raspberry Pi: `sudo reboot`
- Verify Chromium auto-launches to dashboard
- Check system status bar shows all 3 indicators:
  - Arduino: Connected/Disconnected
  - Backend: Online/Offline
  - Uptime: Xh Ym

## Post-Deployment Testing

### Feature 1: Backend Connection Status
**Test Steps:**
1. Open dashboard in browser
2. Check status bar: "Backend: Online" (green) or "Offline" (yellow)
3. Disconnect ethernet/WiFi
4. Wait 60 seconds
5. Verify status changes to "Offline"
6. Reconnect network
7. Wait 60 seconds
8. Verify status returns to "Online"

**Expected Logs:**
```
[BACKEND] Initial connection successful
[BACKEND] Connection check: Online
```

### Feature 2: Uptime Display
**Test Steps:**
1. Note current uptime on dashboard
2. Wait 60 seconds
3. Verify uptime increments without page refresh
4. Restart orchestrator service
5. Verify uptime resets to "0h 0m"

**Expected Behavior:**
- Auto-updates every 3 seconds
- Format: "Xh Ym" (e.g., "2h 14m")

### Feature 3: Actuation Control with Hysteresis
**Test Steps:**
1. Monitor Fruiting Room CO2 reading
2. When CO2 approaches 1000ppm:
   - Verify exhaust fan turns ON at 1000ppm
   - CO2 drops to 990ppm → fan stays ON (hysteresis)
   - CO2 drops to 890ppm → fan turns OFF
3. Check logs for actuation commands:
   ```
   [ORCHESTRATOR] Sending commands: ['FRUITING_EXHAUST_FAN_ON']
   ```

**Test Humidity Hysteresis:**
1. Monitor humidity readings
2. When humidity < 85% (target 90% - 5% hysteresis):
   - Humidifier should turn ON
3. When humidity reaches 90%:
   - Humidifier should turn OFF

**Expected Logs:**
```
[ML] Processing sensor data for automation
[ORCHESTRATOR] Sending commands: ['FRUITING_HUMIDITY_SYSTEM_ON']
```

### Feature 4: Navigation Bar Icons
**Test Steps:**
1. Open dashboard
2. Check navigation bar (left side)
3. Verify icons appear LEFT of text, not above:
   - ✓ [Icon] Dashboard
   - ✗ [Icon]
        Dashboard

**Visual Check:**
- All nav items aligned horizontally
- Icons centered vertically with text
- Consistent 60px height

### Feature 5: Alerts System
**Test Steps:**
1. Navigate to `/alerts` page
2. Trigger a threshold violation:
   - Increase CO2 > 1000ppm (use manual command or wait for natural increase)
   - Or manually heat sensor to exceed temp_target + tolerance
3. Wait 10 seconds for processing
4. Refresh alerts page
5. Verify alert appears with:
   - Timestamp (YYYY-MM-DD HH:MM:SS format)
   - Room name (Fruiting/Spawning)
   - Severity badge (WARNING)
   - Message describing violation

**Expected Logs:**
```
[ALERT] FRUITING temperature HIGH: 27.5°C (target: 24.0°C)
[DB] Alert insert successful: id=1
```

**Check Database:**
```bash
sqlite3 /home/pi/MASH-IoT/rpi_gateway/data/sensor_data.db

SELECT * FROM system_logs WHERE level='WARNING' ORDER BY timestamp DESC LIMIT 5;
```

### Feature 6: Decision Tree Logic (Optional)
**Current State:** Using rule-based logic with hysteresis
**Test Steps:**
1. Monitor actuator decisions
2. Verify predictable behavior based on thresholds
3. Check logs confirm rule-based mode:
   ```
   [ML] Using rule-based control (fruiting)
   ```

**Future:** To enable Decision Tree:
- Collect training data
- Train model: `python -m app.core.train_decision_tree`
- Verify model file: `rpi_gateway/data/models/decision_tree.pkl`

## Troubleshooting

### Backend Shows "Offline" but Internet Works
**Check:**
```bash
# Test backend URL manually
curl -I https://api.mashmarket.app

# Check environment variables
cat /home/pi/MASH-IoT/rpi_gateway/config/.env

# Verify Flask can access env vars
python3 -c "import os; print(os.getenv('BACKEND_URL'))"
```

**Fix:**
- Ensure `.env` file exists in `rpi_gateway/config/`
- Verify credentials are correct
- Check firewall/network restrictions

### Uptime Shows "--" Instead of Time
**Check:**
```bash
# Test API endpoint
curl http://localhost:5000/api/latest_data | jq '.uptime'
```

**Fix:**
- Verify `START_TIME` in app.config: `print(current_app.config.get('START_TIME'))`
- Check JavaScript console for errors
- Restart orchestrator service

### No Alerts Generated
**Check:**
```bash
# Verify database connection
sqlite3 /home/pi/MASH-IoT/rpi_gateway/data/sensor_data.db "SELECT COUNT(*) FROM system_logs;"

# Check if db reference passed to AI
# In logs, look for:
[ML] MushroomAI initialized
```

**Fix:**
- Verify `self.ai.db = self.db` in main.py line 70
- Check sensor readings exceed thresholds
- Verify `_check_and_alert()` is called

### Hysteresis Not Working (Rapid On/Off)
**Check:**
```bash
# Verify config.yaml has hysteresis parameters
cat /home/pi/MASH-IoT/rpi_gateway/config/config.yaml | grep hysteresis

# Expected output:
# co2_hysteresis: 100
# humidity_hysteresis: 5.0
```

**Fix:**
- Update config.yaml with hysteresis parameters (see IMPROVEMENTS_SUMMARY.md)
- Restart orchestrator service
- Monitor actuator state changes in logs

### Navigation Icons Above Text
**Check:**
```bash
# Verify CSS file loaded
curl http://localhost:5000/static/css/styles.css | grep "nav-links li a"
```

**Expected Output:**
```css
.nav-links li a {
    display: flex;
    align-items: center;
    ...
}
```

**Fix:**
- Clear browser cache (Ctrl+Shift+R)
- Verify styles.css has `display: flex` for `.nav-links li a`

## Rollback Procedure

If issues occur, rollback to previous version:

```bash
cd /home/pi/MASH-IoT

# Find last working commit
git log --oneline -n 10

# Rollback to specific commit
git reset --hard <commit-hash>

# Restart services
sudo systemctl restart mashiot-orchestrator

# Or use update script
./scripts/update.sh
```

## Success Criteria

✅ **System is ready for production when:**
1. All 3 status indicators show correct state (Arduino, Backend, Uptime)
2. Uptime increments every minute without page refresh
3. Actuators respond to thresholds with hysteresis (no rapid cycling)
4. Navigation icons aligned properly
5. Alerts page populates with threshold violations
6. No errors in systemd logs: `sudo journalctl -u mashiot-orchestrator --since "10 minutes ago"`

## Support

For issues, check:
1. **Logs:** `sudo journalctl -u mashiot-orchestrator -f`
2. **Database:** `sqlite3 /home/pi/MASH-IoT/rpi_gateway/data/sensor_data.db`
3. **Config:** `cat /home/pi/MASH-IoT/rpi_gateway/config/config.yaml`
4. **Documentation:** `/home/pi/MASH-IoT/docs/IMPROVEMENTS_SUMMARY.md`

---

**Prepared by:** GitHub Copilot AI Agent
**Deployment Target:** M.A.S.H. IoT Raspberry Pi Gateway
**Version:** 2.0 (Production-Ready)

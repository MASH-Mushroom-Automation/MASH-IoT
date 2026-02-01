# Loading Screen - Troubleshooting Guide

## Symptoms
System is stuck at a "Loading Screen" and won't show the dashboard.

## Possible Causes & Solutions

### 1. ✅ Flask Service Not Running

**Check if service is running:**
```bash
sudo systemctl status mash-iot
```

**Expected output:**
```
● mash-iot.service - MASH IoT System
   Loaded: loaded
   Active: active (running)
```

**If NOT running:**
```bash
# Start the service
sudo systemctl start mash-iot

# Check for errors
sudo journalctl -u mash-iot -n 50
```

**Common errors to look for:**
- `ModuleNotFoundError` - Missing Python package
- `Port 5000 already in use` - Another process using the port
- `Permission denied` - File permission issues
- Import errors - Code syntax errors

---

### 2. ✅ Port 5000 Not Accessible

**Check if Flask is listening:**
```bash
# On Raspberry Pi
curl http://localhost:5000

# Or check which process is on port 5000
sudo netstat -tlnp | grep 5000
```

**If nothing on port 5000:**
- Flask app failed to start
- Check logs: `sudo journalctl -u mash-iot -f`

**If different process on port 5000:**
```bash
# Kill the process (replace PID with actual process ID)
sudo kill -9 <PID>

# Restart MASH IoT
sudo systemctl restart mash-iot
```

---

### 3. ✅ Browser Cache Issue

**Clear Chromium cache:**
```bash
# Stop kiosk
pkill chromium

# Clear cache
rm -rf ~/.cache/chromium
rm -rf ~/.config/chromium

# Restart kiosk
sudo reboot
```

---

### 4. ✅ JavaScript Error

**Check browser console (if accessible):**
- Press `F12` to open developer tools
- Look for errors in Console tab
- Common errors:
  - `Failed to fetch` - API endpoint not responding
  - `Uncaught TypeError` - JavaScript error
  - `404 Not Found` - Missing files

**Check if main.js is loading:**
```bash
curl http://localhost:5000/static/js/main.js
```

Should return JavaScript code, not an error.

---

### 5. ✅ Kiosk Configuration Issue

**Check if kiosk is pointing to correct URL:**
```bash
cat ~/.config/lxsession/LXDE-pi/autostart | grep chromium
```

**Expected:**
```
@chromium-browser --kiosk --disable-restore-session-state http://localhost:5000/dashboard
```

**If wrong URL or missing:**
```bash
cd ~/MASH-IoT/scripts
chmod +x ./setup_kiosk.sh
./setup_kiosk.sh
sudo reboot
```

---

### 6. ✅ Network/WiFi Issue

**Check WiFi connection:**
```bash
ip addr show wlan0
```

Should show an IP address like `192.168.1.x`

**If no IP:**
```bash
# Restart WiFi
sudo systemctl restart dhcpcd
sudo systemctl restart wpa_supplicant
```

**Check if can reach internet:**
```bash
ping -c 3 8.8.8.8
```

---

### 7. ✅ Database Lock or File Permission Issue

**Check file permissions:**
```bash
cd ~/MASH-IoT
ls -la rpi_gateway/app/web/
```

All files should be readable (at minimum).

**If permission denied:**
```bash
# Fix permissions
sudo chown -R $USER:$USER ~/MASH-IoT
chmod -R 755 ~/MASH-IoT
```

---

## Quick Diagnostic Commands

Run these on the Raspberry Pi to diagnose the issue:

```bash
# 1. Check if service is running
echo "=== Service Status ==="
sudo systemctl status mash-iot --no-pager

# 2. Check recent logs
echo "=== Recent Logs ==="
sudo journalctl -u mash-iot -n 50 --no-pager

# 3. Check if port 5000 is listening
echo "=== Port 5000 Status ==="
sudo netstat -tlnp | grep 5000

# 4. Test API endpoint
echo "=== API Test ==="
curl http://localhost:5000/api/latest_data

# 5. Check Python processes
echo "=== Python Processes ==="
ps aux | grep python

# 6. Check for errors in Flask
echo "=== Flask Errors ==="
sudo journalctl -u mash-iot | grep -i error | tail -20
```

Save output of all commands and share for further diagnosis.

---

## Emergency Recovery

If nothing works, try a full reset:

```bash
cd ~/MASH-IoT

# Pull latest code
git fetch origin
git reset --hard origin/main

# Reinstall dependencies
pip3 install -r requirements.txt

# Restart service
sudo systemctl restart mash-iot

# Check status
sudo systemctl status mash-iot
sudo journalctl -u mash-iot -f
```

---

## Most Likely Issues (in order)

1. **Flask service crashed or didn't start** → Check `sudo systemctl status mash-iot`
2. **Import error in Python code** → Check `sudo journalctl -u mash-iot -n 50`
3. **Port 5000 blocked** → Check `sudo netstat -tlnp | grep 5000`
4. **Chromium pointing to wrong URL** → Check autostart file
5. **Browser cache corruption** → Clear cache and reboot

---

## What "Loading Screen" Could Mean

1. **Blank white page**: Flask not running or URL wrong
2. **Browser's loading spinner**: Page trying to load but can't reach server
3. **"Checking..." status forever**: JavaScript running but API calls failing
4. **Partial page load**: Some resources (CSS/JS) not loading

Please run the **Quick Diagnostic Commands** above and share the output so we can identify the exact issue.

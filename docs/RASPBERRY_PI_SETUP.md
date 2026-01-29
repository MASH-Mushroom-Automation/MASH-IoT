# M.A.S.H. IoT - Complete Setup Guide for Raspberry Pi

## Prerequisites
- Raspberry Pi 3B+ or 4 with Raspberry Pi OS (Bookworm or Bullseye)
- Arduino Uno with uploaded firmware
- Internet connection (for initial setup)

---

## Initial Setup (First Time Only)

### 1. Clone Repository
```bash
cd ~
git clone https://github.com/MASH-Mushroom-Automation/MASH-IoT.git
cd MASH-IoT
```

### 2. Fix Script Permissions (IMPORTANT!)
```bash
# Option 1: Run the fix script
bash scripts/fix_permissions.sh

# Option 2: Manual fix
chmod +x scripts/*.sh
chmod +x scripts/*.py
```

**Why this is needed:** Git doesn't preserve execute permissions by default. Scripts won't run without this step!

### 3. Install Dependencies
```bash
bash scripts/install_dependencies.sh
```

This installs:
- Python 3 and pip
- System packages (SQLite, NetworkManager, etc.)
- Chromium browser
- PlatformIO (for Arduino development)
- Python virtual environment with all packages

**Time required:** ~10-15 minutes

---

## Arduino Connection Setup

### 4. Connect Arduino to Raspberry Pi
- Plug Arduino into RPi USB port
- Wait 5 seconds for device to enumerate

### 5. Find Arduino Port
```bash
python3 scripts/find_arduino.py
```

**Expected output:**
```
✓ ARDUINO [1] /dev/ttyACM0
       Description: Arduino Uno
```

**Troubleshooting:** If "Permission denied" error:
```bash
sudo usermod -a -G dialout $USER
# Then logout and login again (or reboot)
```

### 6. Test Arduino Connection
```bash
python3 scripts/test_arduino.py
```

**Expected output:**
```
🍄 Fruiting Room:
   Temperature: 23.5°C
   Humidity:    85.0%
   CO2:         800 ppm

🌱 Spawning Room:
   Temperature: 24.0°C
   Humidity:    90.0%
   CO2:         1200 ppm
```

**Test auto-reconnect:** While script is running, unplug Arduino and plug it back in. Should reconnect within 5 seconds!

---

## Backend Configuration

### 7. Configure Environment Variables
```bash
cd rpi_gateway
cp config/.env.example config/.env
nano config/.env
```

Edit with your credentials:
```env
# Backend API
BACKEND_API_URL=https://your-backend.com/api
API_KEY=your_api_key_here

# Firebase (optional)
FIREBASE_PROJECT_ID=your_project_id

# MQTT (optional)
MQTT_BROKER=your_broker_url
MQTT_USERNAME=your_username
MQTT_PASSWORD=your_password
```

### 8. Test Backend Manually
```bash
cd ~/MASH-IoT/rpi_gateway
python3 -m app.main
```

**Expected output:**
```
[SERIAL] Scanning for Arduino...
[SERIAL] Found Arduino: /dev/ttyACM0
[SERIAL] ✓ Connected to Arduino on /dev/ttyACM0 @ 9600 baud
[WEB] Starting Flask server on 0.0.0.0:5000
```

**Access dashboard:** Open browser to `http://localhost:5000`

Press `Ctrl+C` to stop.

---

## Kiosk Mode Setup (Production)

### 9. Setup Kiosk Mode
```bash
cd ~/MASH-IoT
bash scripts/setup_kiosk.sh
```

**What this does:**
1. Creates systemd service for backend (`mash-iot.service`)
2. Creates systemd service for kiosk mode (`mash-kiosk.service`)
3. Configures auto-login to console
4. Disables unnecessary services (Bluetooth, etc.)
5. Creates X session script for fullscreen browser

**Time required:** ~2 minutes

### 10. Reboot
```bash
sudo reboot
```

**After reboot:**
- System boots to console (no desktop)
- Backend starts automatically
- Browser opens in fullscreen kiosk mode
- Dashboard loads at `http://localhost:5000`

---

## Managing the System

### Systemd Service Commands

**Backend service:**
```bash
# Start/stop/restart
sudo systemctl start mash-iot
sudo systemctl stop mash-iot
sudo systemctl restart mash-iot

# Check status
sudo systemctl status mash-iot

# Enable/disable auto-start
sudo systemctl enable mash-iot
sudo systemctl disable mash-iot

# View logs
journalctl -u mash-iot -f           # Follow logs
journalctl -u mash-iot -n 50        # Last 50 lines
journalctl -u mash-iot --since "10 minutes ago"
```

**Kiosk service:**
```bash
# Start/stop/restart
sudo systemctl start mash-kiosk
sudo systemctl stop mash-kiosk
sudo systemctl restart mash-kiosk

# Check status
sudo systemctl status mash-kiosk

# View logs
journalctl -u mash-kiosk -f
```

### Exit Kiosk Mode
Press `Alt+F4` to close browser and return to console.

To disable kiosk mode permanently:
```bash
sudo systemctl disable mash-kiosk
sudo reboot
```

---

## Troubleshooting

### Scripts won't run: "Permission denied"
```bash
# Fix script permissions
bash scripts/fix_permissions.sh

# Or manually
chmod +x scripts/*.sh scripts/*.py
```

### Arduino not detected
```bash
# 1. Check USB connection
lsusb | grep Arduino

# 2. Check serial ports
ls -l /dev/ttyACM* /dev/ttyUSB*

# 3. Fix permissions
sudo usermod -a -G dialout $USER
# Then logout/login or reboot

# 4. Scan for Arduino
python3 scripts/find_arduino.py
```

### Backend won't start
```bash
# Check service status
sudo systemctl status mash-iot

# View logs
journalctl -u mash-iot -n 100

# Check if port 5000 is in use
sudo netstat -tlnp | grep 5000

# Test manually
cd ~/MASH-IoT/rpi_gateway
python3 -m app.main
```

### Kiosk mode not working
```bash
# Check if backend is running first
sudo systemctl status mash-iot

# Check kiosk service
sudo systemctl status mash-kiosk

# View detailed logs
journalctl -u mash-kiosk -n 100

# Check if Chromium is installed
which chromium-browser

# Try manual start
sudo systemctl start mash-kiosk
```

### Connection drops frequently
- Try a different USB cable (must be data-capable, not power-only)
- Use a powered USB hub
- Check for electrical interference from relay module
- Ensure Arduino has stable power supply

### Dashboard not accessible from other devices
```bash
# Allow port 5000 through firewall
sudo ufw allow 5000

# Check firewall status
sudo ufw status

# Access from another device on same network
http://RASPBERRY_PI_IP:5000
```

---

## Verification Checklist

### Hardware
- [ ] Arduino connected to RPi USB port
- [ ] Multiplexer connected (SDA→A4, SCL→A5)
- [ ] Fruiting sensor on SD0/SC0 (Channel 0)
- [ ] Spawning sensor on SD1/SC1 (Channel 1)
- [ ] All sensors powered (VIN/GND)
- [ ] Relay module connected to Arduino

### Software
- [ ] Scripts have execute permissions (`bash scripts/fix_permissions.sh`)
- [ ] Dependencies installed (`bash scripts/install_dependencies.sh`)
- [ ] Arduino detected (`python3 scripts/find_arduino.py`)
- [ ] Connection works (`python3 scripts/test_arduino.py`)
- [ ] Backend starts (`python3 -m app.main` from rpi_gateway/)
- [ ] Dashboard accessible (`http://localhost:5000`)

### Kiosk Mode (Optional)
- [ ] Kiosk setup completed (`bash scripts/setup_kiosk.sh`)
- [ ] System rebooted
- [ ] Backend service running (`systemctl status mash-iot`)
- [ ] Kiosk service running (`systemctl status mash-kiosk`)
- [ ] Dashboard opens in fullscreen
- [ ] Alt+F4 exits kiosk mode

---

## Quick Command Reference

| Task | Command |
|------|---------|
| **Fix permissions** | `bash scripts/fix_permissions.sh` |
| **Install dependencies** | `bash scripts/install_dependencies.sh` |
| **Find Arduino port** | `python3 scripts/find_arduino.py` |
| **Test connection** | `python3 scripts/test_arduino.py` |
| **Upload firmware** | `cd arduino_firmware && pio run -t upload` |
| **Start backend** | `cd rpi_gateway && python3 -m app.main` |
| **Setup kiosk** | `bash scripts/setup_kiosk.sh` |
| **Backend logs** | `journalctl -u mash-iot -f` |
| **Kiosk logs** | `journalctl -u mash-kiosk -f` |
| **Restart backend** | `sudo systemctl restart mash-iot` |
| **Stop kiosk** | `sudo systemctl stop mash-kiosk` |

---

## Network Configuration

### WiFi Setup (If needed)
```bash
# Scan for networks
nmcli device wifi list

# Connect to WiFi
sudo nmcli device wifi connect "SSID" password "PASSWORD"

# Check connection
nmcli connection show
```

### Static IP (Optional)
```bash
# Get current connection name
nmcli connection show

# Set static IP
sudo nmcli connection modify "YOUR_CONNECTION" \
  ipv4.addresses "192.168.1.100/24" \
  ipv4.gateway "192.168.1.1" \
  ipv4.dns "8.8.8.8" \
  ipv4.method "manual"

# Apply changes
sudo nmcli connection down "YOUR_CONNECTION"
sudo nmcli connection up "YOUR_CONNECTION"
```

---

## Development Workflow

### Making Changes
```bash
# 1. Stop services
sudo systemctl stop mash-iot
sudo systemctl stop mash-kiosk

# 2. Make code changes
nano rpi_gateway/app/core/serial_comm.py

# 3. Test manually
cd rpi_gateway
python3 -m app.main

# 4. If working, restart services
sudo systemctl restart mash-iot
sudo systemctl start mash-kiosk
```

### Updating from Git
```bash
cd ~/MASH-IoT

# Stop services
sudo systemctl stop mash-iot mash-kiosk

# Pull updates
git pull

# Fix permissions (important after git pull!)
bash scripts/fix_permissions.sh

# Update dependencies if needed
cd rpi_gateway
source venv/bin/activate
pip install -r requirements.txt

# Restart services
sudo systemctl start mash-iot mash-kiosk
```

---

## Performance Tips

1. **Disable unused services:**
   ```bash
   sudo systemctl disable bluetooth
   sudo systemctl disable hciuart
   ```

2. **Monitor system resources:**
   ```bash
   htop
   ```

3. **Check disk space:**
   ```bash
   df -h
   ```

4. **Clear old logs:**
   ```bash
   sudo journalctl --vacuum-time=7d
   ```

---

## Support

For issues, check:
1. [docs/ARDUINO_CONNECTION.md](../docs/ARDUINO_CONNECTION.md) - Arduino setup
2. [scripts/README.md](./README.md) - Script documentation
3. [docs/SYSTEM_UPDATES.md](../docs/SYSTEM_UPDATES.md) - Recent changes

**Common solutions:**
- Always run `bash scripts/fix_permissions.sh` after git pull
- Check logs with `journalctl -u mash-iot -f`
- Verify Arduino with `python3 scripts/find_arduino.py`
- Test connection with `python3 scripts/test_arduino.py`

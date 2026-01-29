#!/bin/bash
# M.A.S.H. IoT - Kiosk Mode Setup Script
# Configures Raspberry Pi to auto-launch dashboard in kiosk mode using .bash_profile

set -e

echo "========================================="
echo " M.A.S.H. IoT - Kiosk Mode Setup"
echo "========================================="

# Check if running as normal user
if [ "$EUID" -eq 0 ]; then 
    echo "Do not run as root. Run as normal user."
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_NAME="mash-iot"

echo "Project directory: $PROJECT_DIR"

# Set execute permissions on all scripts first
echo "Setting execute permissions on scripts..."
chmod +x "$PROJECT_DIR/scripts/"*.sh 2>/dev/null || true
chmod +x "$PROJECT_DIR/scripts/"*.py 2>/dev/null || true
echo "✓ Script permissions updated"

# ---------------------------------------------------------
# 1. Create systemd service for M.A.S.H. backend
# ---------------------------------------------------------
echo "[1/5] Creating systemd service for M.A.S.H. backend..."

sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=M.A.S.H. IoT Gateway Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR/rpi_gateway
ExecStart=$PROJECT_DIR/rpi_gateway/venv/bin/python -m app.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service

echo "Service created: ${SERVICE_NAME}.service"

# ---------------------------------------------------------
# 2. Install Dependencies
# ---------------------------------------------------------
echo "[2/5] Checking for Chromium and X11 tools..."

if ! command -v chromium-browser &> /dev/null && ! command -v chromium &> /dev/null; then
    echo "Installing Chromium browser..."
    sudo apt-get update
    sudo apt-get install -y chromium-browser x11-xserver-utils unclutter
fi

# ---------------------------------------------------------
# 3. Create the Kiosk Launcher Script
# ---------------------------------------------------------
echo "[3/5] Creating Kiosk Launcher Script..."

# This script actually runs the browser. It is called by startx.
cat > "$PROJECT_DIR/scripts/run_kiosk_x.sh" <<'XEOF'
#!/bin/bash
# Minimal X session - just Chromium, no desktop environment

# Find Chromium executable
CHROMIUM_CMD=$(which chromium-browser || which chromium)

# Wait for backend to be ready
echo "Waiting for M.A.S.H. backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:5000 > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    sleep 1
done

# Launch Chromium in kiosk mode (FULLSCREEN, NO DESKTOP)
# Added --no-sandbox strictly if needed, but usually safe to omit on Pi user
$CHROMIUM_CMD \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-translate \
    --check-for-update-interval=31536000 \
    --disable-features=TranslateUI \
    --no-first-run \
    --fast \
    --fast-start \
    --disable-popup-blocking \
    --password-store=basic \
    http://localhost:5000
XEOF

chmod +x "$PROJECT_DIR/scripts/run_kiosk_x.sh"
echo "✓ run_kiosk_x.sh created"

# ---------------------------------------------------------
# 4. Configure X11 (The "Profile" Method)
# ---------------------------------------------------------
echo "[4/5] Configuring X11 auto-start..."

# Create .xinitrc
# This file tells 'startx' what to do when it loads.
cat > "$HOME/.xinitrc" <<EOF
#!/bin/sh

# Disable screen blanking/energy saving
xset s off
xset -dpms
xset s noblank

# Hide cursor after inactivity
unclutter -idle 0.1 &

# Run our kiosk script
exec $PROJECT_DIR/scripts/run_kiosk_x.sh
EOF

chmod +x "$HOME/.xinitrc"
echo "✓ ~/.xinitrc created"

# Update .bash_profile to auto-start X on login
# This detects when the Pi auto-logs in to the console and runs 'startx'
if ! grep -q "startx" "$HOME/.bash_profile"; then
    cat >> "$HOME/.bash_profile" <<'EOF'

# M.A.S.H. IoT Kiosk Auto-Start
# If logged into tty1 (the physical screen) and no GUI is running, start X
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    startx -- -nocursor
fi
EOF
    echo "✓ Added startx trigger to .bash_profile"
else
    echo "✓ .bash_profile already configured"
fi

# ---------------------------------------------------------
# 5. System Configuration
# ---------------------------------------------------------
echo "[5/5] Final System Configuration..."

# Enable auto-login to console (B2)
# This is CRITICAL. It ensures the 'pi' user logs in, triggering .bash_profile
sudo raspi-config nonint do_boot_behaviour B2

# Disable unneeded services for faster boot
sudo systemctl disable bluetooth.service 2>/dev/null || true
sudo systemctl disable hciuart.service 2>/dev/null || true

# Clean up any old attempts (if the old service file exists)
if [ -f "/etc/systemd/system/mash-kiosk.service" ]; then
    echo "Removing old/broken mash-kiosk service..."
    sudo systemctl disable mash-kiosk.service
    sudo rm /etc/systemd/system/mash-kiosk.service
    sudo systemctl daemon-reload
fi

echo ""
echo "========================================="
echo " Kiosk Mode Setup Complete!"
echo "========================================="
echo ""
echo "Configuration Summary:"
echo "  1. Backend Service:   mash-iot.service (Active)"
echo "  2. Boot Mode:         Console Autologin (B2)"
echo "  3. Auto-Start Logic:  .bash_profile -> startx -> .xinitrc -> Chromium"
echo ""
echo "** PLEASE REBOOT NOW TO START KIOSK MODE **"
echo "   sudo reboot"
echo ""
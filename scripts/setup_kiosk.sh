#!/bin/bash
# M.A.S.H. IoT - Kiosk Mode Setup Script
# Configures Raspberry Pi to auto-launch dashboard in kiosk mode on desktop

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
echo "[1/4] Creating systemd service for M.A.S.H. backend..."

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

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service
sudo systemctl restart ${SERVICE_NAME}.service

echo "✓ systemd service created and started"

# ---------------------------------------------------------
# 2. Check for Chromium and Desktop Tools
# ---------------------------------------------------------
echo "[2/4] Checking for Chromium and tools..."

if ! command -v chromium-browser &> /dev/null && ! command -v chromium &> /dev/null; then
    echo "Installing Chromium browser..."
    sudo apt-get update
    sudo apt-get install -y chromium-browser unclutter
fi

# ---------------------------------------------------------
# 3. Create the Kiosk Launcher Script (Desktop Mode)
# ---------------------------------------------------------
echo "[3/4] Creating Kiosk Launcher Script..."

# This script launches Chromium in kiosk mode from the desktop
cat > "$PROJECT_DIR/scripts/launch_kiosk.sh" <<'LAUNCHEOF'
#!/bin/bash
# M.A.S.H. IoT Kiosk Launcher (Desktop Mode)

# Find Chromium executable
CHROMIUM_CMD=$(which chromium-browser || which chromium)

if [ -z "$CHROMIUM_CMD" ]; then
    echo "Chromium not found!" > ~/kiosk_error.log
    exit 1
fi

# Wait for backend to be ready
echo "Waiting for M.A.S.H. backend..."
for i in {1..30}; do
    if curl -s http://localhost:5000 > /dev/null 2>&1; then
        echo "Backend ready!"
        break
    fi
    sleep 1
done

# Small delay for desktop to fully load
sleep 3

# Launch Chromium in kiosk mode (let desktop handle resolution)
$CHROMIUM_CMD \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-translate \
    --no-first-run \
    --fast \
    --fast-start \
    --disable-popup-blocking \
    --password-store=basic \
    --enable-features=OverlayScrollbar \
    http://localhost:5000 &
LAUNCHEOF

chmod +x "$PROJECT_DIR/scripts/launch_kiosk.sh"
echo "✓ launch_kiosk.sh created"

# ---------------------------------------------------------
# 4. Configure LXDE Autostart (Desktop Mode)
# ---------------------------------------------------------
echo "[4/4] Configuring LXDE autostart..."

# Create LXDE autostart directory if it doesn't exist
mkdir -p "$HOME/.config/lxsession/LXDE-pi"

# Create autostart file
cat > "$HOME/.config/lxsession/LXDE-pi/autostart" <<EOF
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash

# Disable screen blanking
@xset s off
@xset -dpms
@xset s noblank

# Hide mouse cursor
@unclutter -idle 0.1 -root

# Launch M.A.S.H. IoT Kiosk
@$PROJECT_DIR/scripts/launch_kiosk.sh
EOF

echo "✓ LXDE autostart configured"

# ---------------------------------------------------------
# Final System Configuration
# ---------------------------------------------------------
echo ""
echo "Configuring system boot mode..."

# Enable auto-login to desktop (B4)
echo "Enabling auto-login to desktop..."
sudo raspi-config nonint do_boot_behaviour B4

# Clean up old attempts
if [ -f "/etc/systemd/system/mash-kiosk.service" ]; then
    echo "Removing old service..."
    sudo systemctl disable mash-kiosk.service 2>/dev/null || true
    sudo rm -f /etc/systemd/system/mash-kiosk.service
fi

# Remove .bash_profile auto-start if it exists (from old setup)
if grep -q "startx" "$HOME/.bash_profile" 2>/dev/null; then
    echo "Cleaning up old .bash_profile auto-start..."
    sed -i '/M.A.S.H. IoT Kiosk Auto-Start/,/^fi$/d' "$HOME/.bash_profile"
fi

# Remove .xinitrc if it exists (from old setup)
if [ -f "$HOME/.xinitrc" ]; then
    echo "Removing old .xinitrc..."
    rm -f "$HOME/.xinitrc"
fi

# Remove run_kiosk_x.sh if it exists (from old setup)
if [ -f "$PROJECT_DIR/scripts/run_kiosk_x.sh" ]; then
    echo "Removing old run_kiosk_x.sh..."
    rm -f "$PROJECT_DIR/scripts/run_kiosk_x.sh"
fi

sudo systemctl daemon-reload

echo ""
echo "========================================="
echo " Kiosk Mode Setup Complete!"
echo "========================================="
echo ""
echo "Configuration Summary:"
echo "  1. Backend Service:   mash-iot.service (systemd)"
echo "  2. Boot Mode:         Desktop Autologin (B4)"
echo "  3. Auto-Start:        LXDE autostart -> launch_kiosk.sh"
echo "  4. Display:           Native (handled by desktop)"
echo ""
echo "** REBOOT NOW TO START KIOSK MODE **"
echo "   sudo reboot"
echo ""

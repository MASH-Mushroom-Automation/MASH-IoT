#!/bin/bash
# M.A.S.H. IoT - Kiosk Mode Setup Script
# Configures Raspberry Pi to auto-launch dashboard in kiosk mode

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

# 1. Create systemd service for M.A.S.H. backend
echo "[1/4] Creating systemd service..."

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

# 2. Create autostart entry for Chromium kiosk
echo "[2/4] Setting up Chromium kiosk mode..."

AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

cat > "$AUTOSTART_DIR/mash-dashboard.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=M.A.S.H. Dashboard
Exec=/usr/bin/chromium-browser --kiosk --noerrdialogs --disable-infobars --disable-session-crashed-bubble http://localhost:5000
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

echo "Chromium kiosk autostart configured"

# 3. Disable screen blanking
echo "[3/4] Disabling screen blanking..."

# For X11
if [ -f "$HOME/.config/lxsession/LXDE-pi/autostart" ]; then
    if ! grep -q "xset s off" "$HOME/.config/lxsession/LXDE-pi/autostart"; then
        cat >> "$HOME/.config/lxsession/LXDE-pi/autostart" <<EOF
@xset s off
@xset -dpms
@xset s noblank
EOF
    fi
fi

echo "Screen blanking disabled"

# 4. Optional: Custom boot splash
echo "[4/4] Custom boot splash (optional)..."

if [ -f "$PROJECT_DIR/assets/splash.png" ]; then
    sudo cp "$PROJECT_DIR/assets/splash.png" /usr/share/plymouth/themes/pix/splash.png
    echo "Custom splash screen installed"
else
    echo "No splash.png found in assets/, skipping"
fi

echo ""
echo "========================================="
echo " Kiosk Mode Setup Complete!"
echo "========================================="
echo ""
echo "The system will now:"
echo "  • Start M.A.S.H. backend on boot"
echo "  • Auto-launch dashboard in fullscreen"
echo "  • Prevent screen blanking"
echo ""
echo "To start service now: sudo systemctl start ${SERVICE_NAME}"
echo "To check status: sudo systemctl status ${SERVICE_NAME}"
echo "To view logs: journalctl -u ${SERVICE_NAME} -f"
echo ""
echo "Reboot to activate kiosk mode: sudo reboot"


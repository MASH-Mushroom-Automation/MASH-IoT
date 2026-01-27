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

# 2. Configure kiosk mode autostart
echo "[2/4] Setting up Chromium kiosk mode..."

# First, check if Chromium is installed. Exit if it's not.
if ! command -v chromium-browser &> /dev/null && ! command -v chromium &> /dev/null; then
    echo "ERROR: Chromium browser not found. Please install it first by running:"
    echo "sudo apt-get update && sudo apt-get install -y chromium-browser"
    exit 1
fi

LAUNCH_SCRIPT_PATH="$PROJECT_DIR/scripts/launch_kiosk.sh"
AUTOSTART_FILE="$HOME/.config/lxsession/LXDE-pi/autostart"
KIOSK_COMMAND="@$LAUNCH_SCRIPT_PATH"

# First, make the launch script executable
chmod +x "$LAUNCH_SCRIPT_PATH"

# Ensure the directory exists
mkdir -p "$(dirname "$AUTOSTART_FILE")"

# Use tee to add the command with sudo to avoid permission issues,
# then ensure the file has the correct owner.
if ! grep -qF "$KIOSK_COMMAND" "$AUTOSTART_FILE"; then
    echo "$KIOSK_COMMAND" | sudo tee -a "$AUTOSTART_FILE" > /dev/null
    sudo chown "$USER":"$USER" "$AUTOSTART_FILE"
    echo "Chromium kiosk autostart configured."
else
    echo "Chromium kiosk autostart already configured."
fi

# Ensure the autostart file is executable
chmod +x "$AUTOSTART_FILE"

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


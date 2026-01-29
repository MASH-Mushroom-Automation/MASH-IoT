#!/bin/bash
# M.A.S.H. IoT - Kiosk Mode Setup Script
# Configures Raspberry Pi to auto-launch dashboard in kiosk mode WITHOUT DESKTOP

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

# 1. Create systemd service for M.A.S.H. backend
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

# 2. Create DIRECT KIOSK MODE systemd service (boots straight to Chromium)
echo "[2/5] Creating kiosk mode service (direct boot to browser)..."

# Install required packages if not present
if ! command -v chromium-browser &> /dev/null && ! command -v chromium &> /dev/null; then
    echo "Installing Chromium browser..."
    sudo apt-get update
    sudo apt-get install -y chromium-browser x11-xserver-utils unclutter
fi

# Create kiosk systemd service that starts X server + Chromium directly
sudo tee /etc/systemd/system/mash-kiosk.service > /dev/null <<EOF
[Unit]
Description=M.A.S.H. Kiosk Mode (Direct to Browser)
After=graphical.target ${SERVICE_NAME}.service
Wants=graphical.target

[Service]
Type=simple
User=$USER
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$USER/.Xauthority
ExecStartPre=/bin/sleep 5
ExecStart=/usr/bin/startx $PROJECT_DIR/scripts/run_kiosk_x.sh -- -nocursor
Restart=on-failure
RestartSec=10

[Install]
WantedBy=graphical.target
EOF

# Create X session script that launches only Chromium (no desktop)
echo "Creating X session script..."
cat > $PROJECT_DIR/scripts/run_kiosk_x.sh <<'XEOF'
#!/bin/bash
# Minimal X session - just Chromium, no desktop environment

# Disable screen blanking
xset s off
xset -dpms
xset s noblank

# Hide cursor after inactivity
unclutter -idle 0.1 &

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

chmod +x $PROJECT_DIR/scripts/run_kiosk_x.sh
echo "✓ X session script created and made executable"

# Enable auto-login to console (no GUI login required)
echo "[3/5] Enabling auto-login to console..."
sudo raspi-config nonint do_boot_behaviour B2  # B2 = Console with auto-login

# Enable kiosk service
echo "[4/5] Enabling kiosk service..."
sudo systemctl daemon-reload
sudo systemctl enable mash-kiosk.service

# Disable unneeded services for faster boot
echo "[5/5] Optimizing boot speed..."
sudo systemctl disable bluetooth.service 2>/dev/null || true
sudo systemctl disable hciuart.service 2>/dev/null || true

echo ""
echo "========================================="
echo " Kiosk Mode Setup Complete!"
echo "========================================="
echo ""
echo "The system will now:"
echo "  • Boot directly to console (no desktop)"
echo "  • Auto-start M.A.S.H. backend"
echo "  • Launch Chromium in FULLSCREEN kiosk mode"
echo "  • No desktop environment overhead"
echo ""
echo "Manual controls:"
echo "  Backend:  sudo systemctl start/stop ${SERVICE_NAME}"
echo "  Kiosk:    sudo systemctl start/stop mash-kiosk"
echo "  Logs:     journalctl -u ${SERVICE_NAME} -f"
echo "            journalctl -u mash-kiosk -f"
echo ""
echo "To exit kiosk mode after boot: Press Alt+F4"
echo ""
echo "** REBOOT NOW to activate kiosk mode: sudo reboot **"


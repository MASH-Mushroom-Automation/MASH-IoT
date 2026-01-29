#!/bin/bash
# M.A.S.H. IoT - CLI Kiosk Setup (Fixed for Debian Trixie)
# Reverts to Console Boot and adds 'matchbox-window-manager' to fix black bars.

set -e

echo "========================================="
echo " M.A.S.H. IoT - CLI Kiosk Setup (Fixed)"
echo "========================================="

# Check if running as normal user
if [ "$EUID" -eq 0 ]; then 
    echo "Do not run as root. Run as normal user."
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_NAME="mash-iot"

# Set execute permissions
chmod +x "$PROJECT_DIR/scripts/"*.sh 2>/dev/null || true
chmod +x "$PROJECT_DIR/scripts/"*.py 2>/dev/null || true

# ---------------------------------------------------------
# 1. Cleanup Desktop Mode Settings
# ---------------------------------------------------------
echo "[1/5] Cleaning up Desktop Mode settings..."

# Remove Desktop autostart file if it exists
rm "$HOME/.config/autostart/mash-kiosk.desktop" 2>/dev/null || true

# ---------------------------------------------------------
# 2. Setup Backend Service
# ---------------------------------------------------------
echo "[2/5] Ensuring Backend Service is set..."

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

# ---------------------------------------------------------
# 3. Install Window Manager (THE FIX)
# ---------------------------------------------------------
echo "[3/5] Installing Window Manager and Chromium..."

# UPDATED: Replaced 'chromium-browser' with 'chromium' for newer OS compatibility
sudo apt-get update
sudo apt-get install -y chromium x11-xserver-utils unclutter matchbox-window-manager

# ---------------------------------------------------------
# 4. Create the X Session Script
# ---------------------------------------------------------
echo "[4/5] Creating X Session Script..."

cat > "$PROJECT_DIR/scripts/run_kiosk_x.sh" <<'XEOF'
#!/bin/bash

# 1. Disable Screen Blanking
xset s off
xset -dpms
xset s noblank

# 2. Start the Window Manager (Fixes the black/void spaces)
# "-use_titlebar no" ensures it looks like a kiosk (no close buttons)
matchbox-window-manager -use_titlebar no &

# 3. Hide Cursor
unclutter -idle 0.1 &

# 4. Find Chromium (Checks both old and new names)
CHROMIUM_CMD=$(which chromium || which chromium-browser)

if [ -z "$CHROMIUM_CMD" ]; then
    echo "Error: Chromium not found!"
    exit 1
fi

# 5. Wait for Backend
for i in {1..30}; do
    if curl -s http://localhost:5000 > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# 6. Launch Chromium
# We add --window-size and --start-maximized to help matchbox do its job
$CHROMIUM_CMD \
    --kiosk \
    --start-maximized \
    --window-position=0,0 \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-translate \
    --check-for-update-interval=31536000 \
    --no-first-run \
    --fast \
    --fast-start \
    --password-store=basic \
    http://localhost:5000
XEOF

chmod +x "$PROJECT_DIR/scripts/run_kiosk_x.sh"

# ---------------------------------------------------------
# 5. Configure Boot Logic (Console -> startx)
# ---------------------------------------------------------
echo "[5/5] Configuring Console Boot..."

# Create .xinitrc to run our script when X starts
cat > "$HOME/.xinitrc" <<EOF
#!/bin/sh
exec $PROJECT_DIR/scripts/run_kiosk_x.sh
EOF
chmod +x "$HOME/.xinitrc"

# Add auto-start to .bash_profile
# (Check if it's already there to avoid duplicates)
if ! grep -q "startx" "$HOME/.bash_profile"; then
    cat >> "$HOME/.bash_profile" <<'EOF'

# M.A.S.H. IoT Kiosk Auto-Start
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    startx -- -nocursor
fi
EOF
fi

# Force Boot to Console Autologin (B2)
sudo raspi-config nonint do_boot_behaviour B2

echo ""
echo "========================================="
echo " Setup Complete!"
echo "========================================="
echo "1. Reverted to CLI/Console boot (Faster/More reliable)"
echo "2. Fixed package name to 'chromium'"
echo "3. Added 'matchbox-window-manager' to fix resolution issues"
echo ""
echo "** PLEASE REBOOT NOW: **"
echo "   sudo reboot"
echo ""
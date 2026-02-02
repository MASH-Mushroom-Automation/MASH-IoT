#!/bin/bash
# M.A.S.H. IoT - Desktop Kiosk Setup (Touch Screen Mode)
# Configures the Pi to boot into Desktop Mode with NO MOUSE CURSOR.

set -e

echo "========================================="
echo " M.A.S.H. IoT - Desktop Touch Kiosk"
echo "========================================="

if [ "$EUID" -eq 0 ]; then 
    echo "Do not run as root. Run as normal user."
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_NAME="mash-iot"

# Set permissions
chmod +x "$PROJECT_DIR/scripts/"*.sh 2>/dev/null || true
chmod +x "$PROJECT_DIR/scripts/"*.py 2>/dev/null || true

# ---------------------------------------------------------
# 1. Cleanup CLI/Console Mode Settings
# ---------------------------------------------------------
echo "[1/6] Cleaning up CLI/Console settings..."

if [ -f "$HOME/.bash_profile" ]; then
    sed -i '/M.A.S.H. IoT Kiosk Auto-Start/,/fi/d' "$HOME/.bash_profile"
fi
rm "$HOME/.xinitrc" 2>/dev/null || true

# ---------------------------------------------------------
# 2. Setup Backend Service
# ---------------------------------------------------------
echo "[2/6] Ensuring Backend Service is set..."

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
# 3. Install Dependencies
# ---------------------------------------------------------
echo "[3/6] Installing Chromium & Unclutter..."
sudo apt-get update
sudo apt-get install -y chromium x11-xserver-utils unclutter

# ---------------------------------------------------------
# 4. Create Splash Screen
# ---------------------------------------------------------
echo "[4/6] Creating Splash Screen..."

IMAGE_PATH="$PROJECT_DIR/assets/splash.png"

cat > "$PROJECT_DIR/scripts/splash.html" <<EOF
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            background-color: #000000;
            color: #ffffff;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            overflow: hidden;
            cursor: none; /* CSS Backup to hide cursor */
        }
        img {
            max-width: 80%;
            max-height: 60vh;
            object-fit: contain;
            margin-bottom: 30px;
        }
        .loader {
            border: 4px solid #333;
            border-top: 4px solid #4CAF50;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
    <script>
        async function checkServer() {
            try {
                await fetch('http://localhost:5000', { mode: 'no-cors' });
                window.location.href = 'http://localhost:5000';
            } catch (e) {
                setTimeout(checkServer, 1000);
            }
        }
        window.onload = checkServer;
    </script>
</head>
<body>
    <img src="file://$IMAGE_PATH" alt="M.A.S.H. IoT">
    <div class="loader"></div>
</body>
</html>
EOF

# ---------------------------------------------------------
# 5. Create Desktop Launcher (Touch Mode)
# ---------------------------------------------------------
echo "[5/6] Creating Desktop Launcher..."

cat > "$PROJECT_DIR/scripts/launch_desktop_kiosk.sh" <<XEOF
#!/bin/bash
# Wrapper to launch Kiosk on Desktop (Touch Mode)

# 1. Safety Sleep
sleep 5

# 2. Disable Screen Blanking
xset s off
xset -dpms
xset s noblank

# 3. PERMANENTLY Hide Cursor (Touch Mode)
# We use 'idle 0' to hide it immediately and keep it hidden
unclutter -idle 0 -root &

# 4. Find Chromium
CHROMIUM_CMD=\$(which chromium || which chromium-browser)

# 5. Launch Chromium
\$CHROMIUM_CMD \\
    --kiosk \\
    --start-maximized \\
    --window-position=0,0 \\
    --noerrdialogs \\
    --disable-infobars \\
    --disable-session-crashed-bubble \\
    --disable-translate \\
    --check-for-update-interval=31536000 \\
    --no-first-run \\
    --fast \\
    --fast-start \
    --touch-events=enabled \
    --enable-features=TouchUI \
    --password-store=basic \
    --user-data-dir=$HOME/.config/chromium-kiosk \\
    "file://$PROJECT_DIR/scripts/splash.html"
XEOF

chmod +x "$PROJECT_DIR/scripts/launch_desktop_kiosk.sh"

# ---------------------------------------------------------
# 6. Configure Autostart
# ---------------------------------------------------------
echo "[6/6] Configuring Desktop Autostart..."

mkdir -p "$HOME/.config/autostart"

cat > "$HOME/.config/autostart/mash-kiosk.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=MASH IoT Kiosk
Comment=Auto-launch MASH IoT Dashboard
Exec=$PROJECT_DIR/scripts/launch_desktop_kiosk.sh
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

# Force Boot to Desktop Autologin (B4)
sudo raspi-config nonint do_boot_behaviour B4

echo ""
echo "========================================="
echo " Touch Mode Setup Complete"
echo "========================================="
echo "1. Mouse cursor is now permanently hidden."
echo "2. Touch events enabled in Chromium."
echo "3. Desktop autostart configured."
echo ""
echo "** PLEASE REBOOT NOW: **"
echo "   sudo reboot"
echo ""
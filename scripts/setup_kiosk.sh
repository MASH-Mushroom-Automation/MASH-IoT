#!/bin/bash
# M.A.S.H. IoT - CLI Kiosk Final Fix
# 1. FIXES the .bash_profile syntax error by overwriting the file.
# 2. Ensures the CLI auto-start logic is valid.
# 3. Keeps the Splash Screen and Resolution Fix.

set -e

echo "========================================="
echo " M.A.S.H. IoT - Kiosk Fix (Syntax Error)"
echo "========================================="

# Check if running as normal user
if [ "$EUID" -eq 0 ]; then 
    echo "Do not run as root. Run as normal user."
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_NAME="mash-iot"

# Set permissions
chmod +x "$PROJECT_DIR/scripts/"*.sh 2>/dev/null || true

# ---------------------------------------------------------
# 1. CLEANUP (Remove old settings)
# ---------------------------------------------------------
echo "[1/5] Removing broken config files..."
rm "$HOME/.config/autostart/mash-kiosk.desktop" 2>/dev/null || true
rm "$HOME/.xinitrc" 2>/dev/null || true

# ---------------------------------------------------------
# 2. SETUP BACKEND
# ---------------------------------------------------------
echo "[2/5] Verifying Backend Service..."
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
# 3. INSTALL DEPENDENCIES
# ---------------------------------------------------------
echo "[3/5] Verifying Dependencies..."
sudo apt-get update
sudo apt-get install -y chromium x11-xserver-utils unclutter matchbox-window-manager xinit matchbox-keyboard

# ---------------------------------------------------------
# 4. CREATE LAUNCH SCRIPTS
# ---------------------------------------------------------
echo "[4/5] writing Launch Scripts..."

# A. Splash Screen HTML
IMAGE_PATH="$PROJECT_DIR/assets/splash.png"
cat > "$PROJECT_DIR/scripts/splash.html" <<EOF
<!DOCTYPE html>
<html>
<head>
    <style>
        body { background-color: #000; color: #fff; height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; cursor: none; overflow: hidden; }
        img { max-width: 80%; max-height: 60vh; object-fit: contain; margin-bottom: 30px; }
        .loader { border: 4px solid #333; border-top: 4px solid #4CAF50; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
    <script>
        async function checkServer() {
            try { await fetch('http://localhost:5000', { mode: 'no-cors' }); window.location.href = 'http://localhost:5000'; }
            catch (e) { setTimeout(checkServer, 1000); }
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

# B. X Session Script (Run Kiosk)
cat > "$PROJECT_DIR/scripts/run_kiosk_x.sh" <<XEOF
#!/bin/bash
xset s off
xset -dpms
xset s noblank
matchbox-window-manager -use_titlebar no &
unclutter -idle 0.1 &

# Start on-screen keyboard (hidden by default)
matchbox-keyboard -s 50 extended &

CHROMIUM_CMD=\$(which chromium || which chromium-browser)
\$CHROMIUM_CMD --kiosk --start-maximized --window-position=0,0 --noerrdialogs --disable-infobars --no-first-run --fast --fast-start --password-store=basic --user-data-dir=\$HOME/.config/chromium-kiosk "file://$PROJECT_DIR/scripts/splash.html"
XEOF
chmod +x "$PROJECT_DIR/scripts/run_kiosk_x.sh"

# C. .xinitrc (Tells startx what to run)
echo "exec $PROJECT_DIR/scripts/run_kiosk_x.sh" > "$HOME/.xinitrc"

# ---------------------------------------------------------
# 5. FIX .BASH_PROFILE (The Critical Step)
# ---------------------------------------------------------
echo "[5/5] Overwriting .bash_profile..."

# We completely OVERWRITE the file to eliminate syntax errors from previous runs.
cat > "$HOME/.bash_profile" <<'EOF'
# .bash_profile for M.A.S.H. IoT Kiosk

# Source .bashrc if it exists (Standard Linux behavior)
if [ -f ~/.bashrc ]; then
    . ~/.bashrc
fi

# M.A.S.H. IoT Kiosk Auto-Start
# Only run if we are on the physical screen (tty1) and X isn't running
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    echo "M.A.S.H. IoT: Starting Kiosk..."
    exec startx -- -nocursor > "$HOME/kiosk_startup.log" 2>&1
fi
EOF

# Ensure Console Autologin is active
sudo raspi-config nonint do_boot_behaviour B2

echo ""
echo "========================================="
echo " Fix Complete!"
echo "========================================="
echo "The .bash_profile has been completely reset."
echo "Your syntax error should be gone."
echo ""
echo "** PLEASE REBOOT NOW: **"
echo "   sudo reboot"
echo ""
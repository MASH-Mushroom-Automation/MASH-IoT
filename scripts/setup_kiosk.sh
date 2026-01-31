#!/bin/bash
# M.A.S.H. IoT - CLI Kiosk Setup (Self-Healing / Full Rebuild)
# 1. CLEANS all Desktop/OS settings.
# 2. INSTALLS CLI dependencies (Matchbox, xinit).
# 3. REBUILDS .xinitrc and .bash_profile from scratch.
# 4. CONFIGURES Splash Screen & Resolution Fix.

set -e

echo "========================================="
echo " M.A.S.H. IoT - CLI Kiosk (Full Rebuild)"
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
# 1. AGGRESSIVE CLEANUP (Remove Desktop/OS Settings)
# ---------------------------------------------------------
echo "[1/6] Removing Desktop/OS config files..."

# Remove Desktop autostart
rm "$HOME/.config/autostart/mash-kiosk.desktop" 2>/dev/null || true

# Remove any old X11 startup files
rm "$HOME/.xinitrc" 2>/dev/null || true

# Clean .bash_profile of old MASH triggers to prevent duplicates
if [ -f "$HOME/.bash_profile" ]; then
    sed -i '/M.A.S.H. IoT/d' "$HOME/.bash_profile"
    sed -i '/startx/d' "$HOME/.bash_profile"
    echo "✓ Cleaned .bash_profile"
fi

# ---------------------------------------------------------
# 2. Setup Backend Service
# ---------------------------------------------------------
echo "[2/6] Verifying Backend Service..."

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
# 3. Install Critical CLI Dependencies
# ---------------------------------------------------------
echo "[3/6] Installing Window Manager & XInit..."

# We force install 'xinit' and 'matchbox' because these are often missing
# on standard OS images but are REQUIRED for CLI kiosk mode.
sudo apt-get update
sudo apt-get install -y chromium x11-xserver-utils unclutter matchbox-window-manager xinit

# ---------------------------------------------------------
# 4. Create Splash Screen (Using assets/splash.png)
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
            cursor: none;
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
# 5. Create Launch Script (With Resolution Fix)
# ---------------------------------------------------------
echo "[5/6] Creating Launch Script..."

cat > "$PROJECT_DIR/scripts/run_kiosk_x.sh" <<XEOF
#!/bin/bash

# 1. Disable Screen Blanking
xset s off
xset -dpms
xset s noblank

# 2. Window Manager (CRITICAL FIX for black bars)
matchbox-window-manager -use_titlebar no &

# 3. Hide Cursor
unclutter -idle 0.1 &

# 4. Launch Chromium
CHROMIUM_CMD=\$(which chromium || which chromium-browser)

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
    --fast-start \\
    --password-store=basic \\
    --user-data-dir=$HOME/.config/chromium-kiosk \\
    "file://$PROJECT_DIR/scripts/splash.html"
XEOF

chmod +x "$PROJECT_DIR/scripts/run_kiosk_x.sh"

# ---------------------------------------------------------
# 6. Rebuild Auto-Start Logic (The "Missing Link")
# ---------------------------------------------------------
echo "[6/6] Rebuilding Auto-Start Logic..."

# A. Create .xinitrc (Required for startx to know what to run)
echo "exec $PROJECT_DIR/scripts/run_kiosk_x.sh" > "$HOME/.xinitrc"
chmod +x "$HOME/.xinitrc"
echo "✓ Recreated .xinitrc"

# B. Update .bash_profile (Required for auto-start on login)
# This was likely deleted by the OS setup script. We put it back now.
cat >> "$HOME/.bash_profile" <<'EOF'

# M.A.S.H. IoT Kiosk Auto-Start
# Check if we are on the physical display (tty1) and X isn't running
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    echo "M.A.S.H. IoT: Auto-starting Kiosk..."
    # We use 'exec' so the shell is replaced by the X session
    exec startx -- -nocursor > "$HOME/kiosk_startup.log" 2>&1
fi
EOF
echo "✓ Re-added startx trigger to .bash_profile"

# C. Force Console Autologin (B2)
# This ensures the 'pi' user logs in, which triggers .bash_profile
sudo raspi-config nonint do_boot_behaviour B2
echo "✓ Set Boot Behaviour to B2 (Console Autologin)"

echo ""
echo "========================================="
echo " Setup Complete!"
echo "========================================="
echo "1. Reinstalled Matchbox & XInit (for CLI mode)."
echo "2. Recreated .xinitrc and .bash_profile from scratch."
echo "3. Configured Splash Screen & Resolution Fix."
echo ""
echo "** PLEASE REBOOT NOW: **"
echo "   sudo reboot"
echo ""
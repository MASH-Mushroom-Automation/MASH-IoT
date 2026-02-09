#!/bin/bash
#######################################################################
# Setup Script for Boot Splash Screen
# Run this on Raspberry Pi to enable custom boot logo
#######################################################################

set -e

# Get script directory for relative paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOGO_SOURCE="$PROJECT_ROOT/assets/splash.png"
INSTALL_DIR="/opt/mash/assets"
SERVICE_FILE="/etc/systemd/system/mash-splash.service"

echo "========================================"
echo "MASH IoT - Boot Splash Setup"
echo "========================================"
echo ""

# 1. Check if source image exists
if [ ! -f "$LOGO_SOURCE" ]; then
    echo "❌ Error: Splash image not found at $LOGO_SOURCE"
    echo "   Time to create one? Or did you move the assets folder?"
    exit 1
fi

# 2. Install fbi (framebuffer image viewer)
echo "[1/5] Installing fbi (framebuffer image viewer)..."
if ! command -v fbi &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y fbi
else
    echo "      fbi is already installed."
fi

# 3. Copy image to system location
echo "[2/5] Installing splash image..."
sudo mkdir -p "$INSTALL_DIR"
sudo cp "$LOGO_SOURCE" "$INSTALL_DIR/splash.png"
# Set permissions
sudo chmod 644 "$INSTALL_DIR/splash.png"
echo "      Copied to $INSTALL_DIR/splash.png"

# 4. Create systemd service
echo "[3/5] Creating systemd service..."
sudo tee "$SERVICE_FILE" > /dev/null << 'EOF'
[Unit]
Description=MASH Boot Splash Screen
DefaultDependencies=no
After=local-fs.target
Wants=local-fs.target

[Service]
Type=oneshot
ExecStart=/usr/bin/fbi -d /dev/fb0 --noverbose -a /opt/mash/assets/splash.png
StandardInput=tty
StandardOutput=tty

[Install]
WantedBy=sysinit.target
EOF

# 5. Replace Plymouth Theme (Fixes "Welcome to Raspberry Pi Desktop")
PLYMOUTH_DIR="/usr/share/plymouth/themes/pix"
if [ -d "$PLYMOUTH_DIR" ]; then
    echo "[4/5] Found Plymouth 'pix' theme. Replacing background..."
    
    # Backup original if not already backed up
    if [ ! -f "$PLYMOUTH_DIR/splash.png.bak" ]; then
        sudo cp "$PLYMOUTH_DIR/splash.png" "$PLYMOUTH_DIR/splash.png.bak"
    fi
    
    # Replace with our logo
    sudo cp "$LOGO_SOURCE" "$PLYMOUTH_DIR/splash.png"
    echo "      Updated $PLYMOUTH_DIR/splash.png"
else
    echo "      Plymouth 'pix' theme not found. Skipping theme replacement."
fi

# 6. Enable service
echo "[5/5] Enabling splash service..."
sudo systemctl daemon-reload
sudo systemctl enable mash-splash.service

echo ""
echo "Splash screen setup complete!"
echo "   Reboot to see it in action: sudo reboot"

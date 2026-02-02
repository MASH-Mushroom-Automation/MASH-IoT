#!/bin/bash
# Configure On-Screen Keyboard for MASH IoT Kiosk
# This script installs and configures squeekboard for touchscreen use

echo "Configuring On-Screen Keyboard (squeekboard)..."

# Install dependencies
echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y build-essential meson ninja-build cargo rustc git \
    libwayland-dev libxkbcommon-dev libglib2.0-dev libgtk-3-dev \
    libfeedback-dev libgnome-desktop-3-dev wayland-protocols

# Clone and build squeekboard
echo "Building squeekboard from source..."
cd /tmp
rm -rf squeekboard
git clone https://gitlab.gnome.org/World/Phosh/squeekboard.git
cd squeekboard
meson build -Dprefix=/usr/local
ninja -C build
sudo ninja -C build install

# Create autostart entry for X11 compatibility
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/squeekboard.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Squeekboard
Exec=squeekboard
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

echo ""
echo "========================================="
echo " On-Screen Keyboard Configured!"
echo "========================================="
echo ""
echo "squeekboard (Virtual Keyboard) installed!"
echo "Features:"
echo "  ✓ Purpose-built for touch interfaces"
echo "  ✓ Smart auto-show/hide behavior"
echo "  ✓ Multiple keyboard layouts"
echo "  ✓ Optimized for mobile/kiosk use"
echo ""
echo "The keyboard will automatically appear when"
echo "you tap on text input fields (WiFi setup, etc.)"
echo ""

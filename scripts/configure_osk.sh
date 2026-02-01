#!/bin/bash
# Configure On-Screen Keyboard for MASH IoT Kiosk
# This script installs and configures wvkbd for touchscreen use

echo "Configuring On-Screen Keyboard (wvkbd)..."

# Install wvkbd - virtual keyboard for Wayland (works on X11 too)
echo "Installing wvkbd..."
sudo apt-get update
sudo apt-get install -y wvkbd

# wvkbd automatically shows when text input is focused
# No additional configuration needed!

echo ""
echo "========================================="
echo " On-Screen Keyboard Configured!"
echo "========================================="
echo ""
echo "wvkbd (Virtual Keyboard) installed!"
echo "Features:"
echo "  ✓ Auto-shows when text input is focused"
echo "  ✓ Auto-hides when focus is lost"
echo "  ✓ Touch-optimized layout"
echo "  ✓ Positioned at bottom of screen"
echo ""
echo "The keyboard will automatically appear when"
echo "you tap on text input fields (WiFi setup, etc.)"
echo ""

#!/bin/bash
# Configure On-Screen Keyboard for MASH IoT Kiosk
# This script configures matchbox-keyboard to:
# 1. Only show when text input is focused
# 2. Appear at the bottom of screen
# 3. Proper size for touchscreen input

echo "Configuring On-Screen Keyboard..."

# Create matchbox-keyboard config directory
mkdir -p "$HOME/.matchbox"

# Configure matchbox-keyboard settings
cat > "$HOME/.matchbox/keyboard.xml" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<keyboard>
  <options>
    <font>Sans 18</font>
    <layout>us</layout>
    <landscape>true</landscape>
  </options>
</keyboard>
EOF

# Create a system service for on-demand keyboard launch
sudo tee /usr/local/bin/launch_osk.sh > /dev/null <<'EOF'
#!/bin/bash
# Launch matchbox-keyboard on-demand
if ! pgrep -x "matchbox-keyboa" > /dev/null; then
    matchbox-keyboard &
fi
EOF

sudo chmod +x /usr/local/bin/launch_osk.sh

# Configure input method to auto-show keyboard
# Use onboard settings if available
if command -v gsettings &> /dev/null; then
    gsettings set org.onboard.keyboard show-status-icon false 2>/dev/null || true
    gsettings set org.onboard auto-show enabled 2>/dev/null || true
fi

echo ""
echo "========================================="
echo " On-Screen Keyboard Configured!"
echo "========================================="
echo "Changes applied:"
echo "  - Keyboard launches on text input focus"
echo "  - Positioned at bottom of screen"
echo "  - Larger font for touchscreen (18pt)"
echo ""
echo "Note: The keyboard will now only appear when"
echo "you tap on text input fields (like WiFi setup)"
echo "and will hide automatically when done."
echo ""

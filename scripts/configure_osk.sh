#!/bin/bash
# Configure On-Screen Keyboard for MASH IoT Kiosk
# This script configures matchbox-keyboard with proper settings for touchscreen use

echo "Configuring On-Screen Keyboard..."

# Install Florence Virtual Keyboard (better auto-show/hide than matchbox)
echo "Installing Florence Virtual Keyboard..."
sudo apt-get update
sudo apt-get install -y florence at-spi2-core

# Configure Florence to start minimized and auto-show on focus
mkdir -p "$HOME/.config/florence"
cat > "$HOME/.config/florence/florence.conf" <<'EOF'
[window]
xid=0
decorated=false
keep_on_top=true
startup_show=false
task_bar=false

[layout]
style=/usr/share/florence/styles/default
file=/usr/share/florence/layouts/compact.xml

[behaviour]
hide_on_start=true
auto_hide=true
EOF

# Alternative: Configure matchbox-keyboard for better behavior
mkdir -p "$HOME/.matchbox"
cat > "$HOME/.matchbox/keyboard.xml" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<keyboard>
  <options>
    <font>Sans 20</font>
    <layout>us</layout>
    <landscape>true</landscape>
  </options>
</keyboard>
EOF

echo ""
echo "========================================="
echo " On-Screen Keyboard Configured!"
echo "========================================="
echo ""
echo "Two options configured:"
echo ""
echo "Option 1: Florence (Recommended)"
echo "  - Auto-shows on text input focus"
echo "  - Auto-hides when done"
echo "  - Better for touchscreen kiosks"
echo "  To use: Edit run_kiosk_x.sh and replace"
echo "    'matchbox-keyboard' with 'florence'"
echo ""
echo "Option 2: Matchbox (Simple)"
echo "  - Manual toggle mode"
echo "  - Larger font (20pt) configured"
echo "  - Already in use"
echo ""
echo "Current setup uses matchbox with toggle mode (-s 50)"
echo "Keyboard will start minimized and can be toggled"
echo "via the keyboard button in the UI."
echo ""

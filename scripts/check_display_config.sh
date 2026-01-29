#!/bin/bash
# Diagnostic script to check display and resolution configs
# Run this to see what might be affecting the splash screen

echo "========================================="
echo " M.A.S.H. Display Configuration Check"
echo "========================================="
echo ""

echo "1. Boot Config Check:"
echo "---------------------"
for CONFIG_FILE in /boot/config.txt /boot/firmware/config.txt; do
    if [ -f "$CONFIG_FILE" ]; then
        echo "Checking $CONFIG_FILE for resolution settings..."
        grep -E "(framebuffer|hdmi_)" "$CONFIG_FILE" 2>/dev/null || echo "  No resolution configs found"
    fi
done
echo ""

echo "2. Current Display Info:"
echo "------------------------"
if command -v xrandr &> /dev/null && [ -n "$DISPLAY" ]; then
    xrandr | grep -A 1 "connected"
else
    echo "  X server not running or xrandr not available"
fi
echo ""

echo "3. Autostart Files:"
echo "-------------------"
if [ -f "$HOME/.config/lxsession/LXDE-pi/autostart" ]; then
    echo "LXDE autostart:"
    cat "$HOME/.config/lxsession/LXDE-pi/autostart" | grep -v "^@lx" | grep -v "^@pcman" | grep -v "^@xscreen"
else
    echo "  No LXDE autostart file found"
fi
echo ""

echo "4. Old Config Files:"
echo "--------------------"
[ -f "$HOME/.xinitrc" ] && echo "  ⚠ Old .xinitrc exists (should be removed)" || echo "  ✓ No .xinitrc"
[ -f "$HOME/.bash_profile" ] && grep -q "startx" "$HOME/.bash_profile" && echo "  ⚠ .bash_profile has startx (should be removed)" || echo "  ✓ No startx in .bash_profile"
echo ""

echo "5. Boot Behavior:"
echo "-----------------"
raspi-config nonint get_boot_behaviour || echo "  Could not check boot behavior"
echo "  (B4 = Desktop autologin)"
echo ""

echo "6. Service Status:"
echo "------------------"
systemctl is-active mash-iot.service && echo "  ✓ mash-iot.service is running" || echo "  ✗ mash-iot.service is NOT running"
echo ""

echo "Done! Review the output above for any issues."

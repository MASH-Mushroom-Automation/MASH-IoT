#!/bin/bash
#######################################################################
# Script: disable_onscreen_keyboard.sh
# Purpose: Disable the onscreen keyboard (matchbox-keyboard) from 
#          auto-starting on boot for Raspberry Pi OS
# Usage: sudo bash disable_onscreen_keyboard.sh
#######################################################################

set -e

echo "======================================"
echo "Disabling Onscreen Keyboard (OSK)"
echo "======================================"
echo ""

# 1. Stop matchbox-keyboard if running
echo "1. Stopping matchbox-keyboard service (if running)..."
if pgrep -x "matchbox-keyboa" > /dev/null; then
    pkill matchbox-keyboard || true
    echo "   ✓ Stopped matchbox-keyboard process"
else
    echo "   ℹ matchbox-keyboard not currently running"
fi

# 2. Disable autostart from LXDE autostart
LXDE_AUTOSTART="/etc/xdg/lxsession/LXDE-pi/autostart"
if [ -f "$LXDE_AUTOSTART" ]; then
    echo "2. Checking LXDE autostart configuration..."
    if grep -q "matchbox-keyboard" "$LXDE_AUTOSTART"; then
        # Comment out the line
        sed -i 's/^@matchbox-keyboard/#@matchbox-keyboard/' "$LXDE_AUTOSTART"
        echo "   ✓ Disabled matchbox-keyboard in $LXDE_AUTOSTART"
    else
        echo "   ℹ No matchbox-keyboard entry found in LXDE autostart"
    fi
else
    echo "   ℹ LXDE autostart file not found (not using LXDE?)"
fi

# 3. Check user-level autostart
USER_AUTOSTART="/home/mash/.config/lxsession/LXDE-pi/autostart"
if [ -f "$USER_AUTOSTART" ]; then
    echo "3. Checking user-level autostart configuration..."
    if grep -q "matchbox-keyboard" "$USER_AUTOSTART"; then
        sed -i 's/^@matchbox-keyboard/#@matchbox-keyboard/' "$USER_AUTOSTART"
        echo "   ✓ Disabled matchbox-keyboard in user autostart"
    else
        echo "   ℹ No matchbox-keyboard entry in user autostart"
    fi
else
    echo "   ℹ User autostart file not found"
fi

# 4. Check .desktop autostart files
AUTOSTART_DIR="/etc/xdg/autostart"
KEYBOARD_DESKTOP="$AUTOSTART_DIR/matchbox-keyboard.desktop"
if [ -f "$KEYBOARD_DESKTOP" ]; then
    echo "4. Disabling keyboard .desktop entry..."
    # Add Hidden=true to disable it
    if ! grep -q "Hidden=true" "$KEYBOARD_DESKTOP"; then
        echo "Hidden=true" >> "$KEYBOARD_DESKTOP"
        echo "   ✓ Added Hidden=true to $KEYBOARD_DESKTOP"
    else
        echo "   ℹ Already disabled in .desktop file"
    fi
else
    echo "   ℹ No matchbox-keyboard.desktop found in autostart"
fi

# 5. Check systemd service (unlikely but possible)
echo "5. Checking for systemd services..."
if systemctl list-unit-files | grep -q "matchbox-keyboard"; then
    systemctl disable matchbox-keyboard || true
    echo "   ✓ Disabled matchbox-keyboard systemd service"
else
    echo "   ℹ No systemd service found for matchbox-keyboard"
fi

echo ""
echo "======================================"
echo "✓ Onscreen Keyboard Disabled"
echo "======================================"
echo ""
echo "The onscreen keyboard will no longer appear on boot."
echo ""
echo "To re-enable it in the future, you can:"
echo "  1. Uncomment lines in autostart files"
echo "  2. Remove 'Hidden=true' from .desktop files"
echo "  3. Or manually start: matchbox-keyboard &"
echo ""
echo "⚠ IMPORTANT: You may need to reboot for changes to take full effect:"
echo "   sudo reboot"
echo ""

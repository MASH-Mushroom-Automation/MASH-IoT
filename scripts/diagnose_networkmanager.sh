#!/bin/bash
#######################################################################
# NetworkManager Diagnostic Script
# Helps identify why WiFi disconnect might be failing
#######################################################################

echo "========================================"
echo "NetworkManager Permission Diagnostic"
echo "========================================"
echo ""

# Current user
echo "1. Current User:"
echo "   $(whoami)"
echo ""

# Groups
echo "2. User Groups:"
groups
echo ""

# NetworkManager status
echo "3. NetworkManager Status:"
systemctl status NetworkManager --no-pager | head -10
echo ""

# PolicyKit files
echo "4. PolicyKit Configuration:"
echo ""
echo "   Old format (.pkla):"
if [ -f "/etc/polkit-1/localauthority/50-local.d/allow-wifi-control.pkla" ]; then
    echo "   ✓ File exists"
    cat /etc/polkit-1/localauthority/50-local.d/allow-wifi-control.pkla
else
    echo "   ✗ File NOT found"
fi
echo ""

echo "   New format (.rules):"
if [ -f "/etc/polkit-1/rules.d/50-allow-wifi-control.rules" ]; then
    echo "   ✓ File exists"
    cat /etc/polkit-1/rules.d/50-allow-wifi-control.rules
else
    echo "   ✗ File NOT found"
fi
echo ""

# NetworkManager.conf
echo "5. NetworkManager Configuration:"
if [ -f "/etc/NetworkManager/NetworkManager.conf" ]; then
    cat /etc/NetworkManager/NetworkManager.conf
else
    echo "   ✗ Config file not found"
fi
echo ""

# Current WiFi connection
echo "6. Current WiFi Connection:"
nmcli -t -f active,ssid dev wifi | grep '^yes' || echo "   Not connected"
echo ""

# Test nmcli permissions
echo "7. Testing nmcli permissions:"
echo "   Attempting: nmcli general permissions"
nmcli general permissions
echo ""

# Check recent auth failures in journal
echo "8. Recent NetworkManager auth failures:"
journalctl -u NetworkManager --since "1 hour ago" | grep -i "audit.*fail" | tail -5
echo ""

# polkit version
echo "9. PolicyKit/Polkit Version:"
pkaction --version 2>/dev/null || echo "   pkaction not found"
echo ""

echo "========================================"
echo "Diagnostic Complete"
echo "========================================"
echo ""
echo "If you see 'result=\"fail\"' in section 8, permissions are still not working."
echo "Try running: sudo bash MASH-IoT/scripts/fix_networkmanager_permissions.sh"
echo "Then REBOOT the system for changes to take full effect."
echo ""

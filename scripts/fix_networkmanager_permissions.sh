#!/bin/bash
#######################################################################
# NetworkManager Permission Fix - Comprehensive Solution
# Fixes "Not authorized to deactivate connections" error
# Supports both old PolicyKit (.pkla) and new polkit (.rules) formats
#######################################################################

set -e

if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo bash $0"
    exit 1
fi

echo "========================================"
echo "NetworkManager Permission Fix"
echo "========================================"
echo ""

# Get the actual user (not root when using sudo)
ACTUAL_USER=${SUDO_USER:-$USER}
echo "Configuring permissions for user: $ACTUAL_USER"
echo ""

# -------------------------------------------
# Method 1: PolicyKit (Old Format - .pkla)
# -------------------------------------------
echo "[1/4] Creating PolicyKit rule (.pkla)..."
mkdir -p /etc/polkit-1/localauthority/50-local.d/

cat > /etc/polkit-1/localauthority/50-local.d/allow-wifi-control.pkla <<'EOF'
[Allow WiFi Control for All Users]
Identity=unix-user:*
Action=org.freedesktop.NetworkManager.network-control;org.freedesktop.NetworkManager.settings.modify.system;org.freedesktop.NetworkManager.settings.modify.own;org.freedesktop.NetworkManager.enable-disable-network;org.freedesktop.NetworkManager.enable-disable-wifi
ResultAny=yes
ResultInactive=yes
ResultActive=yes
EOF
echo "   ✓ Created: /etc/polkit-1/localauthority/50-local.d/allow-wifi-control.pkla"

# -------------------------------------------
# Method 2: Polkit (New Format - .rules)
# -------------------------------------------
echo "[2/4] Creating polkit rule (.rules)..."
mkdir -p /etc/polkit-1/rules.d/

cat > /etc/polkit-1/rules.d/50-allow-wifi-control.rules <<EOF
/* Allow NetworkManager WiFi control without authentication */
polkit.addRule(function(action, subject) {
    if ((action.id == "org.freedesktop.NetworkManager.network-control" ||
         action.id == "org.freedesktop.NetworkManager.settings.modify.system" ||
         action.id == "org.freedesktop.NetworkManager.settings.modify.own" ||
         action.id == "org.freedesktop.NetworkManager.enable-disable-network" ||
         action.id == "org.freedesktop.NetworkManager.enable-disable-wifi") &&
        subject.isInGroup("sudo")) {
        return polkit.Result.YES;
    }
});
EOF
echo "   ✓ Created: /etc/polkit-1/rules.d/50-allow-wifi-control.rules"

# -------------------------------------------
# Method 3: Add user to netdev group
# -------------------------------------------
echo "[3/4] Adding user to netdev group..."
if ! groups $ACTUAL_USER | grep -q netdev; then
    usermod -a -G netdev $ACTUAL_USER
    echo "   ✓ User '$ACTUAL_USER' added to netdev group"
else
    echo "   ℹ User already in netdev group"
fi

# -------------------------------------------
# Method 4: NetworkManager.conf settings
# -------------------------------------------
echo "[4/4] Configuring NetworkManager.conf..."
NM_CONF="/etc/NetworkManager/NetworkManager.conf"

if ! grep -q "\[main\]" $NM_CONF; then
    echo "" >> $NM_CONF
    echo "[main]" >> $NM_CONF
fi

if ! grep -q "auth-polkit=false" $NM_CONF; then
    sed -i '/\[main\]/a auth-polkit=false' $NM_CONF
    echo "   ✓ Disabled PolicyKit authentication in NetworkManager"
else
    echo "   ℹ NetworkManager already configured"
fi

echo ""
echo "========================================"
echo "Restarting Services..."
echo "========================================"

# Restart services
echo "Restarting polkit..."
systemctl restart polkit 2>/dev/null || systemctl restart policykit 2>/dev/null || echo "   ⚠ Could not restart polkit (might not be needed)"

echo "Restarting NetworkManager..."
systemctl restart NetworkManager

echo ""
echo "========================================"
echo "✓ Permission Fix Complete!"
echo "========================================"
echo ""
echo "IMPORTANT: To apply all changes, you must:"
echo "1. Restart your Flask application"
echo "2. Log out and log back in (or reboot)"
echo ""
echo "To restart Flask app:"
echo "   sudo systemctl restart mash-iot-gateway"
echo "   # OR kill and restart manually"
echo ""
echo "To verify permissions work:"
echo "   nmcli connection down '<network-name>'"
echo "   # Should work without sudo"
echo ""
echo "If still not working, run this diagnostic:"
echo "   bash MASH-IoT/scripts/diagnose_networkmanager.sh"
echo ""
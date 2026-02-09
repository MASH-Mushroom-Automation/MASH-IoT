#!/bin/bash
# =======================================================
# MASH IoT Gateway - Local Domain Setup (mash.lan)
# =======================================================
# Sets up mash.lan domain to work in both hotspot and WiFi modes
# This allows accessing the gateway via http://mash.lan instead of IP addresses

set -e  # Exit on error

echo "=========================================="
echo "MASH IoT Gateway - Domain Setup"
echo "=========================================="
echo ""
echo "This script configures mash.lan domain for:"
echo "  • Hotspot mode: mash.lan → 10.42.0.1"
echo "  • WiFi mode: mash.lan → DHCP assigned IP"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

# 1. Configure dnsmasq for NetworkManager
echo "[1/4] Configuring dnsmasq for NetworkManager..."
mkdir -p /etc/NetworkManager/dnsmasq-shared.d

cat > /etc/NetworkManager/dnsmasq-shared.d/mash.conf <<EOF
# MASH IoT Gateway Local Domain Configuration
# Provides mash.lan domain resolution

# In hotspot mode, resolve to hotspot IP
address=/mash.lan/10.42.0.1

# Also provide reverse DNS
ptr-record=1.0.42.10.in-addr.arpa,mash.lan

# Local domain processing
local=/lan/
domain=lan
expand-hosts
EOF

echo "dnsmasq configuration created"

# 2. Enable dnsmasq in NetworkManager
echo "[2/4] Enabling dnsmasq in NetworkManager..."
if ! grep -q "^dns=dnsmasq" /etc/NetworkManager/NetworkManager.conf 2>/dev/null; then
    # Backup original config
    cp /etc/NetworkManager/NetworkManager.conf /etc/NetworkManager/NetworkManager.conf.backup.$(date +%Y%m%d_%H%M%S)
    
    # Add dns=dnsmasq to [main] section
    sed -i '/^\[main\]/a dns=dnsmasq' /etc/NetworkManager/NetworkManager.conf
    echo "dnsmasq enabled in NetworkManager"
else
    echo "dnsmasq already enabled"
fi

# 3. Configure /etc/hosts fallback
echo "[3/4] Adding /etc/hosts fallback entry..."
if ! grep -q "mash.lan" /etc/hosts; then
    echo "10.42.0.1    mash.lan    mash" >> /etc/hosts
    echo "/etc/hosts entry added"
else
    echo "/etc/hosts entry already exists"
fi

# 4. Restart NetworkManager to apply changes
echo "[4/4] Restarting NetworkManager..."
systemctl restart NetworkManager
sleep 3
echo "NetworkManager restarted"

echo ""
echo "=========================================="
echo "Domain Setup Complete!"
echo "=========================================="
echo ""
echo "You can now access the gateway at:"
echo "  http://mash.lan:5000"
echo ""
echo "Test with:"
echo "  ping mash.lan"
echo "  curl http://mash.lan:5000/status"
echo ""
echo "Note: Devices connecting to the hotspot will"
echo "need to wait a few seconds for DNS to update."
echo ""
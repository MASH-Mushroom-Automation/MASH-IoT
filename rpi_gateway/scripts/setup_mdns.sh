#!/bin/bash
#######################################################################
# Quick Setup Script for mDNS Discovery
# Run this on Raspberry Pi to enable device discovery
#######################################################################

set -e

echo "========================================"
echo "MASH IoT - mDNS Discovery Setup"
echo "========================================"
echo ""

# Check if running on Raspberry Pi
if [ ! -f /etc/rpi-issue ]; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    echo "   Script may still work on other Linux systems"
    echo ""
fi

# 1. Install Avahi daemon
echo "[1/3] Installing Avahi daemon..."
sudo apt-get update
sudo apt-get install -y avahi-daemon avahi-utils

# 2. Enable and start Avahi
echo "[2/3] Enabling Avahi service..."
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

# Check if it's running
if systemctl is-active --quiet avahi-daemon; then
    echo "   ✓ Avahi daemon is running"
else
    echo "   ✗ Avahi daemon failed to start"
    echo "   Check logs: sudo journalctl -u avahi-daemon"
    exit 1
fi

# 3. Install Python zeroconf library
echo "[3/3] Installing Python dependencies..."
cd "$(dirname "$0")/.."

if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q zeroconf

echo ""
echo "========================================"
echo "✓ mDNS Discovery Setup Complete!"
echo "========================================"
echo ""
echo "Testing mDNS:"
echo "   avahi-browse -a"
echo ""
echo "After starting Flask app, you should see:"
echo "   + wlan0 IPv4 MASH-Device _mash-iot._tcp local"
echo ""
echo "Next steps:"
echo "   1. Restart Flask app: sudo systemctl restart MASH-Device"
echo "   2. Test discovery: avahi-browse -r _mash-iot._tcp"
echo "   3. Open mobile app and go to 'Connect to Chamber'"
echo ""

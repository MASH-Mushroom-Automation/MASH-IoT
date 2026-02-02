#!/bin/bash
# Fix NetworkManager permissions for WiFi management
# This allows the Flask app user to control WiFi without sudo

echo "Setting up PolicyKit rules for NetworkManager..."

# Create PolicyKit rule file
sudo tee /etc/polkit-1/localauthority/50-local.d/allow-wifi-control.pkla > /dev/null <<'EOF'
[Allow WiFi Control]
Identity=unix-user:*
Action=org.freedesktop.NetworkManager.network-control;org.freedesktop.NetworkManager.settings.modify.system
ResultAny=yes
ResultInactive=yes
ResultActive=yes
EOF

echo "✅ PolicyKit rules created"
echo "Restarting PolicyKit service..."

# Restart polkit to apply changes
sudo systemctl restart polkit

echo "✅ Done! NetworkManager permissions fixed"
echo "You can now disconnect/connect WiFi without sudo"

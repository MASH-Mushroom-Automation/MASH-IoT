#!/bin/bash
# M.A.S.H. IoT - Application Update Script
# Pulls the latest changes from the main branch and restarts the service.

set -e

echo "========================================="
echo " M.A.S.H. IoT - Starting Update"
echo "========================================="

# Navigate to the project directory (assuming the script is in /scripts)
cd "$(dirname "$0")/.." || { echo "Could not find project directory. Exiting."; exit 1; }

echo "Current directory: $(pwd)"

# 1. Fetch the latest code from the repository
echo "[1/4] Pulling latest changes from GitHub..."
git pull origin main

# 2. Activate virtual environment and install/update dependencies
echo "[2/4] Checking for updated Python dependencies..."
if [ -f "rpi_gateway/requirements.txt" ]; then
    source rpi_gateway/venv/bin/activate
    pip install -r rpi_gateway/requirements.txt
    deactivate
    echo "Dependencies are up to date."
else
    echo "WARNING: requirements.txt not found, skipping dependency check."
fi

# 3. Restart the backend service to apply changes
echo "[3/4] Restarting the M.A.S.H. IoT service..."
sudo systemctl restart mash-iot.service

# 4. Give the service a moment to start up
sleep 5

echo "[4/4] Checking service status..."
if systemctl is-active --quiet mash-iot.service; then
    echo "SUCCESS: The service was restarted successfully and is running."
else
    echo "ERROR: The service failed to restart. Check the logs with:"
    echo "journalctl -u mash-iot.service -n 50"
    exit 1
fi


echo "========================================="
echo " Update Complete!"
echo "========================================="

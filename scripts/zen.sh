#!/bin/bash

echo "Starting Master Setup Sequence..."

# 1. Run the update script
# Using 'bash' bypasses the need for chmod +x
echo ">> Running Update..."
bash update.sh

# Check if update.sh succeeded (exit code 0)
if [ $? -ne 0 ]; then
    echo "CRITICAL ERROR: update.sh failed. Aborting setup and reboot."
    exit 1
fi

# 2. Run the kiosk setup script
# Note: I am using 'setup_kiosk.sh' as you requested.
# If you meant 'run_kiosk.sh', see the warning below.
echo ">> Running Kiosk Setup..."
bash setup_kiosk.sh

if [ $? -ne 0 ]; then
    echo "CRITICAL ERROR: setup_kiosk.sh failed. Aborting reboot."
    exit 1
fi

# 3. Reboot the Pi
echo "All sequences complete."
echo "Rebooting in 5 seconds..."
sleep 5
sudo reboot
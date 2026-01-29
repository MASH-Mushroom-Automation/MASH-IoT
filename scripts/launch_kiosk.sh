#!/bin/bash
# This script waits for the desktop environment to be ready and then launches Chromium.

# Wait for 10 seconds to ensure the desktop session and network are fully loaded
sleep 5

# Run run_kiosk.sh to launch Chromium in kiosk mode
"$HOME/MASH-IoT/scripts/run_kiosk.sh"
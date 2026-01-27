#!/bin/bash
# This script waits for the desktop environment to be ready and then launches Chromium.

# Wait for 10 seconds to ensure the desktop session and network are fully loaded
sleep 10

# Find the correct chromium executable path
CHROMIUM_CMD=$(which chromium-browser || which chromium)

if [ -z "$CHROMIUM_CMD" ]; then
    # If the browser is not found, we can't proceed.
    # This will create a log file in the user's home directory for debugging.
    echo "Chromium executable not found. Please install it via 'sudo apt-get install chromium-browser'." > ~/kiosk_error.log
    exit 1
fi

# Launch Chromium in kiosk mode using the found path
$CHROMIUM_CMD \
    --password-store=basic \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --enable-features=OverscrollHistoryNavigation \
    --disable-translate \
    http://localhost:5000

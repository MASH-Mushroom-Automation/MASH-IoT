#!/bin/bash
# This script waits for the desktop environment to be ready and then launches Chromium.

# Find the correct chromium executable path
CHROMIUM_CMD=$(which chromium-browser || which chromium)

if [ -z "$CHROMIUM_CMD" ]; then
    # If the browser is not found, we can't proceed.
    # This will create a log file in the user's home directory for debugging.
    echo "Chromium executable not found. Please install it via 'sudo apt-get install chromium-browser'." > ~/kiosk_error.log
    exit 1
fi

# Start on-screen keyboard (hidden by default, press keyboard icon to show)
matchbox-keyboard -s 50 extended &

# Launch Chromium in kiosk mode using the found path
$CHROMIUM_CMD \
    --disable-gpu \
    --enable-features=TouchUI \
    --touch-events=enabled \
    --disable-pinch \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --password-store=basic \
    --disable-translate \
    --overscroll-history-navigation=0 \
    http://localhost:5000

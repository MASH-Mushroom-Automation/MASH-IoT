#!/bin/bash
# This script waits for the desktop environment to be ready and then launches Chromium.

# Wait for 10 seconds to ensure the desktop session and network are fully loaded
sleep 10

# Launch Chromium in kiosk mode
/usr/bin/chromium-browser \
    --password-store=basic \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --enable-features=OverscrollHistoryNavigation \
    --disable-translate \
    http://localhost:5000

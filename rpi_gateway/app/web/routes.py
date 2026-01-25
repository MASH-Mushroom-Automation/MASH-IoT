from flask import Blueprint, render_template, request, render_template_string
import threading
import time

# Adjust this import based on where your main.py is located.
# If running from 'rpi_gateway/app/', it might be: from app.utils import wifi_manager
# For now, assuming direct import or package import:
from app.utils import wifi_manager 

# Create a Blueprint (Standard Flask practice for separating routes)
web_bp = Blueprint('web', __name__, template_folder='templates')

def delayed_switch_thread(ssid, password):
    """
    Background Task:
    1. Wait 2 seconds (allows user to see the 'Connecting' screen).
    2. Kill Hotspot and Attempt WiFi Connection.
    3. If WiFi fails, Restart Hotspot (Failsafe).
    """
    time.sleep(2)
    success = wifi_manager.connect_to_wifi(ssid, password)
    
    if success:
        print(f"[Routes] SUCCESS: Connected to {ssid}. Hotspot is now OFF.")
    else:
        print(f"[Routes] FAIL: Could not connect to {ssid}. Restoring Hotspot...")
        wifi_manager.start_hotspot()

@web_bp.route('/')
def setup_page():
    """
    Renders the WiFi Setup page with the scanned list of networks.
    """
    # 1. Scan for networks
    networks = wifi_manager.get_wifi_list()
    
    # 2. Render the pastel green HTML template
    return render_template('wifi_setup.html', wifi_list=networks)

@web_bp.route('/connect', methods=['POST'])
def connect():
    """
    Handles the form submission from wifi_setup.html
    """
    # 1. Get Data from Form
    selection = request.form.get('ssid_select')
    manual_entry = request.form.get('manual_ssid')
    password = request.form.get('password')
    
    # Determine which SSID to use (Dropdown vs Manual)
    target_ssid = manual_entry if selection == "OTHER" else selection
    
    print(f"[*] Web Request: Connect to '{target_ssid}'")
    
    # 2. Start the Switch in Background (Non-blocking)
    # This prevents the UI from freezing/crashing while the network changes
    thread = threading.Thread(target=delayed_switch_thread, args=(target_ssid, password))
    thread.start()
    
    # 3. Return a Temporary Status Page
    # (The user sees this while their phone loses connection)
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Connecting...</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #f1f8e9; color: #2e7d32; text-align: center; padding-top: 50px; }}
            .loader {{ font-size: 20px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>Attempting Connection...</h1>
        <p>Target Network: <strong>{target_ssid}</strong></p>
        <p>The Hotspot will now turn off.</p>
        <hr style="width: 50%; border-color: #81c784;">
        <p class="loader">Please wait 30 seconds.</p>
        <p style="font-size: 14px; color: #558b2f;">
            If the connection is successful, your phone will switch back to WiFi.<br>
            If it fails, this Hotspot ('{wifi_manager.HOTSPOT_SSID}') will reappear.
        </p>
    </body>
    </html>
    """
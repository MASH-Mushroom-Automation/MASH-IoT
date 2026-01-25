from flask import Flask, request, render_template_string
import wifi_manager
import os
import time
import threading

app = Flask(__name__)

# --- UI TEMPLATE WITH DROPDOWN ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>M.A.S.H. Setup</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #2c3e50; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #34495e; padding: 25px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); width: 300px; text-align: center; }
        h2 { margin-bottom: 20px; }
        select, input { width: 100%; padding: 12px; margin: 8px 0; border: none; border-radius: 5px; box-sizing: border-box; font-size: 16px; }
        select { background: #ecf0f1; color: #2c3e50; }
        button { width: 100%; padding: 12px; background: #27ae60; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 16px; margin-top: 15px; }
        button:hover { background: #2ecc71; }
        .label { text-align: left; font-size: 14px; color: #bdc3c7; margin-top: 10px; display: block; }
    </style>
    <script>
        function toggleManual(select) {
            var input = document.getElementById("manual_ssid");
            if (select.value === "OTHER") {
                input.style.display = "block";
                input.required = true;
            } else {
                input.style.display = "none";
                input.required = false;
            }
        }
    </script>
</head>
<body>
    <div class="card">
        <h2>M.A.S.H. WiFi Setup</h2>
        <form action="/connect" method="post">
            <label class="label">Choose Network:</label>
            <select name="ssid_select" onchange="toggleManual(this)">
                {% for net in wifi_list %}
                    <option value="{{ net }}">{{ net }}</option>
                {% endfor %}
                <option value="OTHER">Enter Manually...</option>
            </select>
            
            <input type="text" id="manual_ssid" name="manual_ssid" placeholder="Type SSID name..." style="display:none;">
            
            <label class="label">Password:</label>
            <input type="password" name="password" placeholder="WiFi Password" required>
            
            <button type="submit">Connect</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    # SCAN LIST LOGIC
    # We pass the list of networks to the template
    networks = wifi_manager.get_wifi_list()
    return render_template_string(HTML_TEMPLATE, wifi_list=networks)

def delayed_switch(ssid, password):
    """
    Background Thread:
    1. Waits 2 seconds (to let the browser show the 'Connecting' screen).
    2. Kills Hotspot -> Tries to Connect to WiFi.
    3. FAILSAFE: If connection fails, it RESTARTs the Hotspot.
    """
    time.sleep(2)
    success = wifi_manager.connect_to_wifi(ssid, password)
    
    if success:
        print(f"[SUCCESS] System is now connected to {ssid}. Hotspot is GONE.")
    else:
        print("[!] Connection Failed (Wrong Password?).")
        print("[*] ACTIVATING FAILSAFE: Restoring Hotspot...")
        wifi_manager.start_hotspot()

@app.route('/connect', methods=['POST'])
def connect():
    # Handle Dropdown vs Manual Input
    selection = request.form.get('ssid_select')
    manual = request.form.get('manual_ssid')
    password = request.form.get('password')
    
    target_ssid = manual if selection == "OTHER" else selection
    
    print(f"[*] Request to connect to: {target_ssid}")
    
    # Start the switch in background so the UI doesn't freeze
    thread = threading.Thread(target=delayed_switch, args=(target_ssid, password))
    thread.start()
    
    return f"""
    <div style='text-align:center; font-family:sans-serif; padding:50px;'>
        <h1>Connecting...</h1>
        <p>Attempting to join <b>{target_ssid}</b>.</p>
        <p>If successful, this Hotspot will disappear.</p>
        <hr>
        <p style='color:red;'><b>Wait 30 seconds.</b></p>
        <p>If the connection fails, the <b>{wifi_manager.HOTSPOT_SSID}</b> hotspot will reappear automatically.</p>
    </div>
    """

if __name__ == '__main__':
    if os.geteuid() != 0:
        print("Error: Must run as root (sudo)")
        exit(1)

    wifi_manager.start_hotspot()
    app.run(host='0.0.0.0', port=5000)
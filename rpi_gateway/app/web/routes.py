from flask import Blueprint, render_template, request, jsonify, current_app
import threading
import time
from datetime import datetime

# Import WiFi manager from utils (tested prototype)
try:
    from app.utils import wifi_manager
except ImportError:
    # Fallback to root level for development
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
    import wifi_manager

# Create Flask Blueprint
web_bp = Blueprint('web', __name__, template_folder='templates', static_folder='static')


def delayed_switch_thread(ssid, password):
    """
    Background Task for WiFi switching:
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


# ==================== WEB UI ROUTES ====================
@web_bp.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')


@web_bp.route('/wifi-setup')
def wifi_setup():
    """WiFi provisioning page."""
    networks = wifi_manager.get_wifi_list()
    return render_template('wifi_setup.html', wifi_list=networks)


@web_bp.route('/connect', methods=['POST'])
def wifi_connect():
    """Handle WiFi connection form submission."""
    # Get form data
    selection = request.form.get('ssid_select')
    manual_entry = request.form.get('manual_ssid')
    password = request.form.get('password')
    
    # Determine which SSID to use (dropdown vs manual)
    ssid = manual_entry if selection == "OTHER" and manual_entry else selection
    
    if not ssid or not password:
        return render_template('wifi_setup.html', 
                             wifi_list=wifi_manager.get_wifi_list(),
                             error="SSID and password are required")
    
    # Start background WiFi switch
    thread = threading.Thread(target=delayed_switch_thread, args=(ssid, password), daemon=True)
    thread.start()
    
    # Show connecting page
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Connecting...</title>
        <meta http-equiv="refresh" content="5;url=/">
        <style>
            body {{ 
                font-family: sans-serif; 
                background: #f1f8e9; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                height: 100vh; 
                text-align: center;
            }}
            .spinner {{ 
                border: 8px solid #c5e1a5;
                border-top: 8px solid #81c784;
                border-radius: 50%;
                width: 60px;
                height: 60px;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }}
            @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        </style>
    </head>
    <body>
        <div>
            <div class="spinner"></div>
            <h2>Connecting to {ssid}...</h2>
            <p>Please wait. You will be redirected to the dashboard.</p>
        </div>
    </body>
    </html>
    """


@web_bp.route('/settings')
def settings():
    """Settings page."""
    return render_template('settings.html')


# ==================== API ROUTES ====================
@web_bp.route('/api/sensor-data')
def api_sensor_data():
    """Get latest sensor readings (JSON API)."""
    latest_data = current_app.config.get('LATEST_DATA', {})
    return jsonify({
        'fruiting': latest_data.get('fruiting'),
        'spawning': latest_data.get('spawning'),
        'timestamp': datetime.now().isoformat()
    })


@web_bp.route('/api/send-command', methods=['POST'])
def api_send_command():
    """Send command to Arduino."""
    try:
        data = request.get_json()
        
        room = data.get('room')  # 'fruiting' or 'spawning'
        actuator = data.get('actuator')  # 'fan', 'mist', 'light'
        action = data.get('action')  # 'on' or 'off'
        
        if not all([room, actuator, action]):
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400
        
        # Format command for Arduino
        command = f"{room.upper()}_{actuator.upper()}_{action.upper()}"
        
        # Send to Arduino
        arduino = current_app.config.get('ARDUINO')
        if arduino and arduino.send_command(command):
            # Log to database
            db = current_app.config.get('DB')
            if db:
                from database.models import DeviceCommand
                cmd = DeviceCommand(room=room, actuator=actuator, action=action, source='web')
                db.insert_command(cmd)
            
            return jsonify({'success': True, 'command': command})
        else:
            return jsonify({'success': False, 'error': 'Arduino not connected'}), 503
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@web_bp.route('/api/history')
def api_history():
    """Get historical sensor data."""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        db = current_app.config.get('DB')
        if not db:
            return jsonify({'error': 'Database not available'}), 503
        
        readings = db.get_latest_readings(limit=limit)
        return jsonify({'data': readings, 'count': len(readings)})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    """Get or update system settings."""
    import yaml
    import os
    
    config_path = os.path.join(os.path.dirname(__file__), '../../config/config.yaml')
    
    if request.method == 'GET':
        # Return current settings
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    settings = yaml.safe_load(f)
                return jsonify(settings)
            else:
                return jsonify({'error': 'Config file not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        # Save new settings
        try:
            new_settings = request.get_json()
            
            # Merge with existing config (preserve other sections)
            existing_config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    existing_config = yaml.safe_load(f) or {}
            
            # Update sections
            existing_config.update(new_settings)
            
            # Write back to file
            with open(config_path, 'w') as f:
                yaml.dump(existing_config, f, default_flow_style=False, sort_keys=False)
            
            return jsonify({'success': True, 'message': 'Settings saved'})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


# ==================== ERROR HANDLERS ====================
@web_bp.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@web_bp.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

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
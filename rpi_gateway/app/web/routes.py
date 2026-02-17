from flask import Blueprint, render_template, jsonify, redirect, url_for, current_app, request, send_from_directory
import time
import logging
import os
import subprocess
from datetime import datetime

logger = logging.getLogger(__name__)

# Create Flask Blueprint
web_bp = Blueprint('web', __name__, template_folder='templates', static_folder='static')


@web_bp.route('/status', methods=['GET'])
def get_status():
    """Health check endpoint for device connection testing."""
    try:
        # Get Firebase sync user preference
        user_prefs = current_app.config.get('USER_PREFS')
        firebase_sync_enabled = user_prefs.get_preference('firebase_sync_enabled', default=True) if user_prefs else True

        return jsonify({
            'success': True,
            'status': 'online',
            'device_id': current_app.config.get('MUSHROOM_CONFIG', {}).get('device', {}).get('serial_number', 'unknown'),
            'device_name': current_app.config.get('MUSHROOM_CONFIG', {}).get('device', {}).get('name', 'MASH IoT Chamber'),
            'firebase_sync_enabled': firebase_sync_enabled,  # NEW: Connection mode decision
            'timestamp': time.time()
        }), 200
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Add custom Jinja filter for timestamp formatting
@web_bp.app_template_filter('strftime')
def strftime_filter(timestamp, format_string='%Y-%m-%d %H:%M:%S'):
    """Convert Unix timestamp to formatted datetime string."""
    try:
        return datetime.fromtimestamp(float(timestamp)).strftime(format_string)
    except (ValueError, TypeError):
        return 'Invalid timestamp'


def calculate_room_condition(room_type, sensor_data, targets):
    """
    Calculate dynamic condition status based on sensor values and targets.
    Returns: ('Optimal'|'Warning'|'Critical'|'Waiting', color_class)
    """
    # Check if we have sensor data
    if not sensor_data or 'error' in sensor_data:
        return 'Sensor Error', 'error'
    
    temp = sensor_data.get('temp')
    humidity = sensor_data.get('humidity')
    co2 = sensor_data.get('co2')
    
    # If all values are None or 0, system is initializing - show "Waiting"
    if temp is None or humidity is None or co2 is None:
        return 'Waiting...', 'warning'
    
    # If values are 0 (sensors not yet read), show "Initializing"
    if temp == 0 and humidity == 0 and co2 == 0:
        return 'Initializing', 'warning'
    
    # Get thresholds
    temp_target = targets.get('temp_target', 24)
    temp_tolerance = targets.get('temp_tolerance', 2)
    humidity_target = targets.get('humidity_target', 90)
    humidity_tolerance = targets.get('humidity_tolerance', 10)
    co2_max = targets.get('co2_max', 1000)
    
    # Count issues by severity
    critical_issues = 0
    warning_issues = 0
    
    # Temperature checks
    temp_diff = abs(temp - temp_target)
    if temp_diff > temp_tolerance * 1.5:  # Critical if beyond 1.5x tolerance
        critical_issues += 1
    elif temp_diff > temp_tolerance:
        warning_issues += 1
    
    # Humidity checks
    humidity_diff = abs(humidity - humidity_target)
    if humidity_diff > humidity_tolerance * 1.5:
        critical_issues += 1
    elif humidity_diff > humidity_tolerance:
        warning_issues += 1
    
    # CO2 checks
    if co2 > co2_max * 1.3:  # Critical if 30% above max
        critical_issues += 1
    elif co2 > co2_max:
        warning_issues += 1
    
    # Determine overall status
    if critical_issues > 0:
        return 'Critical', 'error'
    elif warning_issues > 0:
        return 'Warning', 'warning'
    else:
        return 'Optimal', 'ok'


def get_live_data():
    """
    Fetches the latest data and actuator states from the orchestrator.
    """
    # Get components from Flask app context
    serial_comm = getattr(current_app, 'serial_comm', None)
    config = current_app.config.get('MUSHROOM_CONFIG', {})

    # Get latest sensor data from app context (stored by orchestrator)
    sensor_data = current_app.config.get('LATEST_DATA', {})

    # DEBUG: Log when we're accessing LATEST_DATA (helps diagnose mobile app connection issues)
    if not sensor_data or not isinstance(sensor_data, dict):
        logger.warning("[API] LATEST_DATA is empty or invalid - sensor data may not be updating")
        # Fallback if no data available
        sensor_data = {
            'fruiting': None,
            'spawning': None
        }
    else:
        logger.debug(f"[API] Retrieved sensor data - fruiting: {sensor_data.get('fruiting') is not None}, spawning: {sensor_data.get('spawning') is not None}")
    
    # Handle null/error states
    fruiting_data = sensor_data.get('fruiting')
    spawning_data = sensor_data.get('spawning')
    
    # Check for sensor errors or invalid data
    fruiting_error = False
    spawning_error = False
    
    if fruiting_data:
        if 'error' in fruiting_data:
            fruiting_error = True
            fruiting_data = None  # Set to None so UI shows N/A
    
    if spawning_data:
        if 'error' in spawning_data:
            spawning_error = True
            spawning_data = None  # Set to None so UI shows N/A
    
    # If no data, set to None (not 0)
    if not fruiting_data:
        fruiting_data = None
        fruiting_error = True  # Mark as error if no data
    if not spawning_data:
        spawning_data = None
        spawning_error = True  # Mark as error if no data
    
    # Get target thresholds from config
    fruiting_targets = config.get("fruiting_room", {})
    spawning_targets = config.get("spawning_room", {})
    
    # Get actuator states from app context
    actuator_states = current_app.config.get('ACTUATOR_STATES', {})
    
    fruiting_actuators = actuator_states.get('fruiting', {
        'exhaust_fan': False,
        'blower_fan': False,
        'humidifier': False,
        'humidifier_fan': False,
        'led': False
    })
    
    spawning_actuators = actuator_states.get('spawning', {
        'exhaust_fan': False
    })
    
    # Calculate dynamic condition status
    fruiting_condition, fruiting_condition_class = calculate_room_condition(
        'fruiting', fruiting_data, fruiting_targets
    )
    spawning_condition, spawning_condition_class = calculate_room_condition(
        'spawning', spawning_data, spawning_targets
    )
    
    # [FIX] Get LIVE backend status from the client object, not the static app variable
    backend_client = getattr(current_app, 'backend_client', None)
    backend_connected = backend_client.is_connected if backend_client else False
    
    # Get Firebase sync user preference (controls whether Firebase sync is active)
    user_prefs = current_app.config.get('USER_PREFS')
    firebase_sync_enabled = user_prefs.get_preference('firebase_sync_enabled', default=True) if user_prefs else True

    return {
        "fruiting_data": fruiting_data,
        "spawning_data": spawning_data,
        "fruiting_error": fruiting_error,
        "spawning_error": spawning_error,
        "fruiting_targets": fruiting_targets,
        "spawning_targets": spawning_targets,
        "fruiting_actuators": fruiting_actuators,
        "spawning_actuators": spawning_actuators,
        "fruiting_condition": fruiting_condition,
        "fruiting_condition_class": fruiting_condition_class,
        "spawning_condition": spawning_condition,
        "spawning_condition_class": spawning_condition_class,
        "backend_connected": backend_connected,  # Backend API (PostgreSQL) connection status
        "firebase_sync_enabled": firebase_sync_enabled,  # Whether Firebase sync is enabled (on_sensor_data checks this)
        "arduino_connected": serial_comm.is_connected if serial_comm else False
    }

# =======================================================
#                  WEB PAGE ROUTES
# =======================================================

@web_bp.route('/')
def index():
    """Redirect to dashboard."""
    return redirect(url_for('web.dashboard'))

@web_bp.route('/dashboard')
def dashboard():
    """Renders the main dashboard page with live data."""
    context = get_live_data()
    # Add this line:
    context['device_id'] = current_app.config.get('MUSHROOM_CONFIG', {}) \
        .get('device', {}).get('serial_number', 'unknown')
    return render_template('dashboard.html', **context)

@web_bp.route('/controls')
def controls():
    """Renders the manual controls page with current actuator states."""
    context = get_live_data()
    
    # Get current actuator states from config
    actuator_states = current_app.config.get('ACTUATOR_STATES', {})
    
    # Add device room actuators
    device_room_states = actuator_states.get('device', {})
    device_actuators = {
        'exhaust_fan': device_room_states.get('exhaust_fan', False),
        'exhaust_fan_auto': False
    }
    
    # Get fruiting room actuator states
    fruiting_room_states = actuator_states.get('fruiting', {})
    fruiting_actuators = {
        'mist_maker': fruiting_room_states.get('mist_maker', False),
        'humidifier_fan': fruiting_room_states.get('humidifier_fan', False),
        'exhaust_fan': fruiting_room_states.get('exhaust_fan', False),
        'intake_fan': fruiting_room_states.get('intake_fan', False),
        'led': fruiting_room_states.get('led', False),
        'mist_maker_auto': False,
        'humidifier_fan_auto': False,
        'exhaust_fan_auto': False,
        'intake_fan_auto': False,
        'led_auto': False
    }
    
    # Get spawning room actuator states
    spawning_room_states = actuator_states.get('spawning', {})
    spawning_actuators = {
        'exhaust_fan': spawning_room_states.get('exhaust_fan', False),
        'exhaust_fan_auto': False,
        'exhaust_fan_flush': False  # Flush mode indicator
    }
    
    # Get auto mode status from config
    config = current_app.config.get('MUSHROOM_CONFIG', {})
    auto_mode_enabled = config.get('system', {}).get('auto_mode', True)
    
    return render_template('controls.html', 
                           fruiting_actuators=fruiting_actuators,
                           spawning_actuators=spawning_actuators,
                           device_actuators=device_actuators,
                           auto_mode_enabled=auto_mode_enabled)

@web_bp.route('/ai_insights')
def ai_insights():
    """Renders the AI/ML insights page."""
    # Check if the ML libraries were imported successfully
    try:
        from sklearn.ensemble import IsolationForest
        ml_available = True
    except ImportError:
        ml_available = False
    
    # Check if ML is actually enabled and models are loaded
    logic_engine = getattr(current_app, 'logic_engine', None)
    ml_enabled = False
    anomaly_model_loaded = False
    actuation_model_loaded = False
    
    if logic_engine and hasattr(logic_engine, 'ml_enabled'):
        ml_enabled = logic_engine.ml_enabled
        anomaly_model_loaded = logic_engine.anomaly_detector is not None
        actuation_model_loaded = logic_engine.actuator_model is not None
        
    return render_template('ai_insights.html', 
                         ml_available=ml_available,
                         ml_enabled=ml_enabled,
                         anomaly_model_loaded=anomaly_model_loaded,
                         actuation_model_loaded=actuation_model_loaded)

@web_bp.route('/alerts')
def alerts():
    """Display system alerts page."""
    db = current_app.config.get('DB')
    active_alerts = []
    history = []
    
    if db:
        active_alerts = db.get_active_alerts()
        # Also fetch history for reference
        history = db.get_recent_alerts(limit=50)
    
    return render_template('alerts.html', active_alerts=active_alerts, history=history)

@web_bp.route('/api/alerts/acknowledge/<int:alert_id>', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge an active alert."""
    try:
        db = current_app.config.get('DB')
        if db:
            db.acknowledge_alert(alert_id)
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Database not available'}), 500
    except Exception as e:
        logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@web_bp.route('/settings')
def settings():
    """Renders the system settings page."""
    # Get system info for settings page
    context = {
        'arduino_connected': False,
        'backend_connected': False
    }
    
    # Try to get connection status
    serial_comm = getattr(current_app, 'serial_comm', None)
    if serial_comm:
        context['arduino_connected'] = serial_comm.is_connected
    
    # [FIX] Get LIVE backend status
    backend_client = getattr(current_app, 'backend_client', None)
    context['backend_connected'] = backend_client.is_connected if backend_client else False
    
    return render_template('settings.html', **context)

@web_bp.route('/wifi-setup')
def wifi_setup():
    """Renders the WiFi provisioning page with available networks."""
    from app.utils import wifi_manager
    
    # Scan for available WiFi networks
    networks = wifi_manager.get_wifi_list()
    
    # Get current connected network
    current_network = wifi_manager.get_current_network()
    
    return render_template('wifi_setup.html', networks=networks, current_network=current_network)

@web_bp.route('/wifi-connect', methods=['POST'])
def wifi_connect():
    """Handles WiFi connection request."""
    from app.utils import wifi_manager
    import threading
    
    # Get form data
    selection = request.form.get('ssid_select')
    manual = request.form.get('manual_ssid')
    password = request.form.get('password')
    
    # Determine target SSID
    target_ssid = manual if selection == "OTHER" else selection
    
    logger.info(f"WiFi connection request for: {target_ssid}")
    
    def delayed_switch(ssid, password):
        """Background thread to handle WiFi switching with failsafe."""
        import time
        time.sleep(2)  # Give browser time to receive response
        
        success = wifi_manager.connect_to_wifi(ssid, password)
        
        if success:
            logger.info(f"Successfully connected to {ssid}")
        else:
            logger.warning(f"Failed to connect to {ssid}, restarting hotspot")
            wifi_manager.start_hotspot()
    
    # Start connection attempt in background
    thread = threading.Thread(target=delayed_switch, args=(target_ssid, password))
    thread.daemon = True
    thread.start()
    
    # Return status page
    return render_template('wifi_connecting.html', 
                         ssid=target_ssid, 
                         hotspot_ssid=wifi_manager.HOTSPOT_SSID)


@web_bp.route('/wifi-disconnect', methods=['POST'])
def wifi_disconnect():
    """Disconnect from current WiFi network and start hotspot."""
    from app.utils import wifi_manager
    import threading
    import time
    
    current = wifi_manager.get_current_network()
    
    # Attempt disconnect
    if wifi_manager.disconnect_wifi():
        logger.info(f"Successfully disconnected from {current}")
        
        # Start hotspot in background thread
        def start_hotspot_delayed():
            time.sleep(3)  # Give disconnect time to complete
            logger.info("[WIFI] Starting provisioning hotspot...")
            success = wifi_manager.start_hotspot()
            if success:
                logger.info("[WIFI] ✅ Hotspot started successfully")
            else:
                logger.error("[WIFI] ❌ Failed to start hotspot")
        
        thread = threading.Thread(target=start_hotspot_delayed)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Disconnected from {current}. Starting provisioning hotspot...' if current else 'Disconnected. Starting provisioning hotspot...'
        })
    else:
        logger.error(f"Failed to disconnect from WiFi: {current}")
        return jsonify({
            'success': False,
            'error': 'Failed to disconnect from WiFi. You may need to run the app with sudo privileges or configure PolicyKit permissions.'
        }), 500


@web_bp.route('/api/wifi_status')
def wifi_status():
    """Get current WiFi connection status."""
    from app.utils import wifi_manager
    
    current_network = wifi_manager.get_current_network()
    saved_ssid, _ = wifi_manager.load_wifi_credentials()
    
    return jsonify({
        'connected': current_network is not None,
        'current_network': current_network,
        'last_known_network': saved_ssid
    })


@web_bp.route('/api/wifi-qr')
def get_wifi_qr():
    """Get QR code for connecting to provisioning hotspot"""
    try:
        from app.utils import wifi_manager
        
        # Only provide QR if in hotspot mode
        if wifi_manager.is_hotspot_active():
            # NEW PROVISIONING FLOW: QR links to the Setup Page, not just WiFi Credentials
            # The user is expected to connect to 10.42.0.1 manually, OR we can provide the enrollment purely as a fallback.
            # But per request: "QR Code... opens a link where we can Modify the WiFi"
            # Since the user is likely ALREADY connected to the hotspot if they see this on the dashboard (at 10.42.0.1), 
            # or if they are on mobile scanning the screen of the RPi:
            # If they scan this, they need to be on the WiFi network 10.42.0.1.
            
            # Use the Web Setup Page URL
            setup_url = "http://10.42.0.1:5000/wifi-setup"
            qr_data = wifi_manager.generate_url_qr_code(setup_url)
            
            return jsonify({
                'success': True,
                'qr_code': qr_data,
                'ssid': 'MASH-Device',
                'ip': '10.42.0.1',
                'instructions': 'Scan to open WiFi Setup'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Device is not in provisioning mode'
            }), 400
            
    except Exception as e:
        logger.error(f"[API] QR generation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@web_bp.route('/api/wifi-mode')
def get_wifi_mode():
    """Get current WiFi mode (station/hotspot)"""
    try:
        from app.utils import wifi_manager
        
        if wifi_manager.is_hotspot_active():
            return jsonify({
                'success': True,
                'mode': 'hotspot',
                'ssid': 'MASH-Device',
                'ip': '10.42.0.1'
            })
        elif wifi_manager.is_connected_to_wifi():
            return jsonify({
                'success': True,
                'mode': 'station',
                'ssid': wifi_manager.get_current_network(),
                'ip': wifi_manager.get_local_ip() or '0.0.0.0'
            })
        else:
            return jsonify({
                'success': True,
                'mode': 'disconnected'
            })
            
    except Exception as e:
        logger.error(f"[API] WiFi mode check error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@web_bp.route('/api/wifi-scan')
def scan_wifi_networks():
    """Scan for available WiFi networks (2.4GHz only for RPi compatibility)"""
    try:
        from app.utils import wifi_manager
        
        networks = wifi_manager.get_wifi_list()
        
        # Convert to list of dicts with basic info
        network_list = [{'ssid': ssid, 'frequency': 2400} for ssid in networks]
        
        return jsonify({
            'success': True,
            'networks': network_list
        })
        
    except Exception as e:
        logger.error(f"[API] WiFi scan error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@web_bp.route('/api/wifi-connect', methods=['POST'])
def api_wifi_connect():
    """API endpoint to connect to WiFi (used by mobile app)."""
    from app.utils import wifi_manager
    import threading
    
    try:
        payload = request.get_json(silent=True) or {}
        ssid = payload.get('ssid') or request.form.get('ssid') or request.form.get('ssid_select')
        password = payload.get('password') or request.form.get('password') or ''

        if not ssid:
            return jsonify({'success': False, 'error': 'SSID is required'}), 400

        logger.info(f"[API] WiFi connect requested for: {ssid}")

        def delayed_switch(target_ssid: str, target_password: str):
            import time
            time.sleep(2)
            success = wifi_manager.connect_to_wifi(target_ssid, target_password)
            if success:
                logger.info(f"[API] Connected to {target_ssid}")
            else:
                logger.warning(f"[API] Failed to connect to {target_ssid}, restarting hotspot")
                wifi_manager.start_hotspot()

        thread = threading.Thread(target=delayed_switch, args=(ssid, password))
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': f'Connecting to {ssid}',
            'ssid': ssid,
            'ip_address': wifi_manager.get_local_ip() or wifi_manager.HOTSPOT_IP
        })
    except Exception as e:
        logger.error(f"[API] WiFi connect error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =======================================================
#                    API ENDPOINTS
# =======================================================


# ---------------- Connection QR Code Endpoint ----------------
@web_bp.route('/api/connection-qr')
def get_connection_qr():
    """
    Generate QR code for mobile app to scan and connect to this device.
    
    Returns a base64-encoded QR code image containing connection info in JSON format:
    {
        "type": "mash_device",
        "deviceId": "MASH-RPI-12345",
        "deviceName": "Caloocan Chamber 1",
        "ipAddress": "192.168.1.100",
        "port": 5000
    }
    """
    try:
        from app.utils import wifi_manager
        
        # Get device information
        config = current_app.config.get('MUSHROOM_CONFIG', {})
        device_config = config.get('device', {})
        
        device_id = device_config.get('serial_number', 'unknown')
        device_name = device_config.get('name', 'MASH IoT Chamber')
        
        # Get current IP address
        ip_address = wifi_manager.get_local_ip()
        
        if not ip_address:
            return jsonify({
                'success': False,
                'error': 'Device IP address not available'
            }), 500
        
        # Generate QR code
        qr_code = wifi_manager.generate_device_connection_qr(
            device_id=device_id,
            device_name=device_name,
            ip_address=ip_address,
            port=5000
        )
        
        return jsonify({
            'success': True,
            'qr_code': qr_code,
            'device_id': device_id,
            'device_name': device_name,
            'ip_address': ip_address,
            'port': 5000,
            'instructions': 'Scan this QR code with the MASH Grower mobile app to connect'
        })
        
    except Exception as e:
        logger.error(f"[API] Connection QR generation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ---------------- Version API Endpoint ----------------
@web_bp.route('/api/version')
def api_version():
    """
    API endpoint to provide gateway version info for frontend.
    """
    try:
        from app.core import version as version_module
        info = version_module.get_version_info()
        return jsonify({
            'success': True,
            'version': info.get('version'),
            'major': info.get('major'),
            'minor': info.get('minor'),
            'patch': info.get('patch'),
            'release_date': info.get('release_date'),
            'release_name': info.get('release_name')
        })
    except Exception as e:
        logger.error(f"[API] Version info error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Existing endpoint below
@web_bp.route('/api/latest_data')
def api_latest_data():
    """
    API endpoint to provide the latest sensor data and actuator states.
    This can be called by JavaScript to dynamically update the dashboard.
    """
    data = get_live_data()
    
    # Add uptime calculation
    start_time = current_app.config.get('START_TIME', time.time())
    uptime_seconds = int(time.time() - start_time)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    data['uptime'] = f"{hours}h {minutes}m"
    
    # Add sensor warmup status
    warmup_complete = current_app.config.get('SENSOR_WARMUP_COMPLETE', False)
    warmup_duration = current_app.config.get('WARMUP_DURATION', 30)
    remaining_warmup = max(0, warmup_duration - uptime_seconds) if not warmup_complete else 0
    
    # Make sure condition data is included
    return jsonify({
        "arduino_connected": data.get('arduino_connected', False),
        "backend_connected": data.get('backend_connected', False),
        "firebase_sync_enabled": data.get('firebase_sync_enabled', False),
        "uptime": data['uptime'],
        "warmup_complete": warmup_complete,
        "warmup_remaining": remaining_warmup,
        "fruiting_data": data.get('fruiting_data'),
        "spawning_data": data.get('spawning_data'),
        "fruiting_actuators": data.get('fruiting_actuators'),
        "spawning_actuators": data.get('spawning_actuators'),
        "fruiting_condition": data.get('fruiting_condition'),
        "fruiting_condition_class": data.get('fruiting_condition_class'),
        "spawning_condition": data.get('spawning_condition'),
        "spawning_condition_class": data.get('spawning_condition_class')
    })

@web_bp.route('/api/control_actuator', methods=['POST'])
def control_actuator():
    """
    API endpoint to manually control an actuator.
    Receives a JSON object like: {"room": "fruiting", "actuator": "mist_maker", "state": "ON"}
    """
    data = request.get_json()
    if not all(key in data for key in ['room', 'actuator', 'state']):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    room = data['room'].lower()
    actuator = data['actuator'].lower()
    state = data['state'].upper()
    
    if state not in ['ON', 'OFF']:
        return jsonify({"success": False, "message": "Invalid state (must be ON or OFF)"}), 400

    # Map web UI actuator names to Arduino firmware names
    actuator_map = {
        'mist_maker': 'MIST_MAKER',
        'humidifier_fan': 'HUMIDIFIER_FAN',
        'exhaust_fan': 'FRUITING_EXHAUST_FAN' if room == 'fruiting' else 'SPAWNING_EXHAUST_FAN' if room == 'spawning' else 'DEVICE_EXHAUST_FAN',
        'intake_fan': 'FRUITING_INTAKE_FAN',
        'led': 'FRUITING_LED'
    }
    
    arduino_actuator = actuator_map.get(actuator)
    if not arduino_actuator:
        return jsonify({"success": False, "message": f"Unknown actuator: {actuator}"}), 400

    # Get the serial comm object from app context
    serial_comm = getattr(current_app, 'serial_comm', None)

    if not serial_comm:
        logger.warning("Serial comm not available in app context")
        return jsonify({"success": False, "message": "Serial communication not initialized"}), 500

    if not serial_comm.is_connected:
        logger.warning("Arduino not connected")
        return jsonify({"success": False, "message": "Arduino not connected"}), 503

    # Send command to Arduino
    try:
        # Use JSON format for consistency
        import json
        json_cmd = json.dumps({"actuator": arduino_actuator, "state": state})
        success = serial_comm.send_command(json_cmd)
        
        if not success:
            logger.warning(f"Failed to send command to Arduino: {json_cmd}")
            return jsonify({"success": False, "message": "Failed to communicate with Arduino"}), 503
        
        logger.info(f"Sent JSON command to Arduino: {json_cmd}")
        
        # Update actuator state in app config
        actuator_states = current_app.config.get('ACTUATOR_STATES', {'fruiting': {}, 'spawning': {}})
        
        # Map back to UI actuator name
        if room not in actuator_states:
            actuator_states[room] = {}
        
        actuator_states[room][actuator] = (state == 'ON')
        current_app.config['ACTUATOR_STATES'] = actuator_states
        
        # Track manual override to prevent auto-mode from changing this actuator
        # Manual overrides are stored with timestamp and cleared after 5 minutes or when auto-mode is toggled
        manual_overrides = current_app.config.get('MANUAL_OVERRIDES', {})
        if room not in manual_overrides:
            manual_overrides[room] = {}
        manual_overrides[room][actuator] = {'state': state, 'timestamp': time.time()}
        current_app.config['MANUAL_OVERRIDES'] = manual_overrides
        logger.info(f"[MANUAL] Override set: {room}/{actuator} = {state}")
        
        # Also send to backend if available
        backend_client = getattr(current_app, 'backend_client', None)
        if backend_client:
            try:
                backend_client.send_alert(
                    alert_type='manual_control',
                    message=f"User set {room}/{actuator} to {state}",
                    severity='INFO'
                )
            except Exception as be:
                logger.warning(f"Failed to send to backend: {be}")
        
        return jsonify({"success": True, "room": room, "actuator": actuator, "state": state})
    except Exception as e:
        logger.error(f"Failed to send command: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


@web_bp.route('/api/set_auto_mode', methods=['POST'])
def set_auto_mode():
    """
    API endpoint to toggle automatic control mode.
    Receives: {"enabled": true/false}
    """
    data = request.get_json()
    if 'enabled' not in data:
        return jsonify({"success": False, "message": "Missing 'enabled' field"}), 400
    
    enabled = bool(data['enabled'])
    
    # Update config
    config = current_app.config.get('MUSHROOM_CONFIG', {})
    if 'system' not in config:
        config['system'] = {}
    config['system']['auto_mode'] = enabled
    
    # Clear manual overrides when switching to auto mode
    if enabled:
        current_app.config['MANUAL_OVERRIDES'] = {}
        logger.info("Auto mode enabled - cleared manual overrides")
    else:
        logger.info("Auto mode disabled - manual control active")
    
    return jsonify({"success": True, "auto_mode": enabled})


@web_bp.route('/provisioning/info', methods=['GET'])
def provisioning_info():
    """
    API endpoint for device provisioning information.
    Used by mobile app to check if device is in provisioning mode and get connection details.
    """
    try:
        from utils import wifi_manager
        
        # Check if hotspot is active
        is_provisioning = wifi_manager.is_hotspot_active()
        
        # Get device config
        device_config = current_app.config.get('MUSHROOM_CONFIG', {}).get('device', {})
        
        # Get current network status
        current_network = wifi_manager.get_current_network()
        network_connected = current_network is not None
        
        return jsonify({
            'success': True,
            'data': {
                'active': is_provisioning,
                'ssid': 'MASH-Device' if is_provisioning else (current_network or 'Not Connected'),
                'ip_address': wifi_manager.get_local_ip() or '10.42.0.1',
                'password_protected': False,  # Provisioning hotspot is open
                'channel': 6,  # Default channel for 2.4GHz
                'device_id': device_config.get('serial_number', 'MASH-Device'),
                'network_connected': network_connected,
                'current_connection': {
                    'ssid': current_network,
                    'connected': network_connected
                } if current_network else None
            }
        })
    except Exception as e:
        logger.error(f"Error getting provisioning info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@web_bp.route('/api/actuator_states')
def actuator_states():
    """
    API endpoint to get current actuator states.
    Returns state of all actuators across all rooms.
    """
    # Get actual state from app config
    actuator_state_data = current_app.config.get('ACTUATOR_STATES', {})
    
    # Initialize default structure
    states = {
        "fruiting": {
            "mist_maker": {"state": False, "auto": False},
            "humidifier_fan": {"state": False, "auto": False},
            "exhaust_fan": {"state": False, "auto": False},
            "intake_fan": {"state": False, "auto": False},
            "led": {"state": False, "auto": False}
        },
        "spawning": {
            "exhaust_fan": {"state": False, "auto": False}
        },
        "device": {
            "exhaust_fan": {"state": False, "auto": False}
        }
    }
    
    # Update with actual states from config
    for room in ['fruiting', 'spawning', 'device']:
        if room in actuator_state_data:
            for actuator_name, is_on in actuator_state_data[room].items():
                if actuator_name in states[room]:
                    states[room][actuator_name]['state'] = is_on
    
    return jsonify(states)


@web_bp.route('/api/toggle-keyboard', methods=['POST'])
def toggle_keyboard():
    """
    API endpoint to toggle on-screen keyboard.
    Supports Onboard (via DBus) and Matchbox (legacy).
    """
    try:
        import subprocess
        
        # 1. Try Onboard (The new keyboard we installed)
        # Onboard uses DBus to toggle visibility cleanly
        try:
            subprocess.run([
                'dbus-send', '--type=method_call', '--dest=org.onboard.Onboard',
                '/org/onboard/Onboard/Keyboard', 'org.onboard.Onboard.Keyboard.ToggleVisible'
            ], check=True, timeout=1)
            return jsonify({"success": True, "message": "Onboard toggled"})
        except Exception:
            # If Onboard DBus fails, maybe it's not running or we are on Matchbox
            pass

        # 2. Legacy Fallback: Matchbox-keyboard
        result = subprocess.run(['pkill', '-USR1', 'matchbox-keyboard'], 
                              capture_output=True, timeout=2)
        
        if result.returncode == 0:
            return jsonify({"success": True, "message": "Matchbox keyboard toggled"})
        else:
            # 3. Last Resort: xdotool to activate window
            subprocess.run(['xdotool', 'search', '--name', 'Keyboard', 'windowactivate'],
                         capture_output=True, timeout=2)
            return jsonify({"success": True, "message": "Keyboard window activated"})
            
    except Exception as e:
        logger.error(f"Keyboard toggle error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# System Control Endpoints
@web_bp.route('/api/system/reboot', methods=['POST'])
def system_reboot():
    """Reboot the Raspberry Pi system"""
    try:
        logger.info("System reboot requested from web interface")
        # Use subprocess to execute reboot command with sudo
        # Note: User must be in sudoers with NOPASSWD for reboot
        subprocess.Popen(['sudo', 'reboot'])
        return jsonify({"success": True, "message": "System is rebooting..."})
    except Exception as e:
        logger.error(f"Reboot failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@web_bp.route('/api/system/shutdown', methods=['POST'])
def system_shutdown():
    """Shutdown the Raspberry Pi system"""
    try:
        logger.info("System shutdown requested from web interface")
        # Use subprocess to execute shutdown command with sudo
        # Note: User must be in sudoers with NOPASSWD for shutdown
        subprocess.Popen(['sudo', 'shutdown', '-h', 'now'])
        return jsonify({"success": True, "message": "System is shutting down..."})
    except Exception as e:
        logger.error(f"Shutdown failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@web_bp.route('/api/changelog')
def get_changelog():
    """
    Get system changelogs with optional filtering.
    
    Query params:
        since    - Return changelogs newer than this version (e.g. ?since=2.1.0)
        version  - Return a specific version's changelog (e.g. ?version=2.2.2)
        limit    - Return the last N versions (e.g. ?limit=3)
        full     - Return all changelogs (e.g. ?full=true)
    
    Default (no params): Returns only the current version's changelog.
    """
    try:
        from app.core import version as version_module

        since = request.args.get('since')
        specific_version = request.args.get('version')
        limit = request.args.get('limit', type=int)
        full = request.args.get('full', '').lower() == 'true'

        if specific_version:
            # Single version lookup
            entry = version_module.get_changelog(specific_version)
            if entry is None:
                return jsonify({
                    "success": False,
                    "error": f"Version {specific_version} not found"
                }), 404
            changelogs = [entry]

        elif since:
            # All versions newer than 'since'
            changelogs = version_module.get_changelogs_since(since)

        elif full:
            # All versions
            changelogs = version_module.get_changelogs()

        elif limit:
            # Last N versions
            changelogs = version_module.get_changelogs(limit=limit)

        else:
            # Default: current version only
            entry = version_module.get_changelog()
            changelogs = [entry] if entry else []

        return jsonify({
            "success": True,
            "current_version": version_module.VERSION,
            "changelogs": changelogs
        })
    except Exception as e:
        logger.error(f"Failed to load changelog: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@web_bp.route('/api/debug/firebase')
def debug_firebase():
    """Debug Firebase sync status and configuration"""
    try:
        config = current_app.config.get('MUSHROOM_CONFIG', {})
        device_config = config.get('device', {})
        latest_data = current_app.config.get('LATEST_DATA', {})
        
        # Check if Firebase client exists
        firebase_client = getattr(current_app, 'orchestrator', None)
        firebase_obj = firebase_client.firebase if firebase_client else None
        
        # Get user preference
        user_prefs = current_app.config.get('USER_PREFS')
        sync_pref = user_prefs.get_preference('firebase_sync_enabled', default=True) if user_prefs else True
        
        return jsonify({
            "success": True,
            "firebase_initialized": firebase_obj is not None,
            "firebase_enabled": firebase_obj.is_initialized if firebase_obj else False,
            "sync_preference": sync_pref,
            "device_id": device_config.get('serial_number', 'unknown'),
            "device_uuid": device_config.get('id', 'unknown'),
            "latest_data": {
                "fruiting": latest_data.get('fruiting'),
                "spawning": latest_data.get('spawning')
            },
            "firebase_url": os.getenv('FIREBASE_DATABASE_URL', 'not set')
        })
    except Exception as e:
        logger.error(f"Debug firebase failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@web_bp.route('/api/firebase-sync/status', methods=['GET'])
def get_firebase_sync_status():
    """Get current Firebase sync status (server-side preference)"""
    try:
        user_prefs = current_app.config.get('USER_PREFS')
        if user_prefs:
            enabled = user_prefs.get_preference('firebase_sync_enabled', default=True)
        else:
            enabled = True
        
        return jsonify({"success": True, "enabled": enabled})
    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@web_bp.route('/api/firebase-sync/toggle', methods=['POST'])
def toggle_firebase_sync():
    """Toggle Firebase sync (affects all clients)"""
    try:
        data = request.json
        enabled = data.get('enabled', True)
        
        user_prefs = current_app.config.get('USER_PREFS')
        if user_prefs:
            user_prefs.set_preference('firebase_sync_enabled', enabled)
            logger.info(f"[FIREBASE] Sync toggled: {enabled}")
        
        return jsonify({"success": True, "enabled": enabled})
    except Exception as e:
        logger.error(f"Failed to toggle sync: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# OTA Update Endpoints
# =============================================================================

@web_bp.route('/api/update/check')
def check_ota_update():
    """
    Check GitHub Releases for available updates.
    
    Query params:
        force - If 'true', bypass cache and check immediately (default: false)
    
    Returns:
        {
            "success": true,
            "update_available": true/false,
            "current_version": "2.3.0",
            "latest_version": "2.4.0",
            "release_name": "Release Name",
            "priority": "high|medium|low",
            "changelog": "Release body markdown",
            "published_at": "ISO datetime"
        }
    """
    try:
        from app.core import updater, version

        force = request.args.get('force', '').lower() == 'true'
        
        logger.info(f"[OTA] Check update requested (force={force})")
        result = updater.check_for_update(force=force)

        if result.get('available'):
            return jsonify({
                "success": True,
                "update_available": True,
                "current_version": version.VERSION,
                "latest_version": result['version'],
                "release_name": result.get('name', ''),
                "priority": result.get('priority', 'medium'),
                "changelog": result.get('changelog', ''),
                "published_at": result.get('published_at', ''),
                "download_url": result.get('download_url'),
            })
        else:
            return jsonify({
                "success": True,
                "update_available": False,
                "current_version": version.VERSION,
                "reason": result.get('reason', 'up_to_date'),
                "error": result.get('error'),
            })

    except Exception as e:
        logger.error(f"[OTA] Check update failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@web_bp.route('/api/update/install', methods=['POST'])
def install_ota_update():
    """
    Trigger OTA update installation.
    Downloads the release tarball and runs ota_update.sh.
    
    Request body:
        {
            "version": "2.4.0",
            "download_url": "https://github.com/.../rpi_gateway.tar.gz"
        }
    
    Returns:
        {
            "success": true/false,
            "message": "Update status message",
            "output": "Script output (if available)"
        }
    """
    try:
        from app.core import updater

        data = request.json
        if not data:
            return jsonify({"success": False, "error": "Missing request body"}), 400

        target_version = data.get('version')
        download_url = data.get('download_url')

        if not target_version or not download_url:
            return jsonify({
                "success": False,
                "error": "Missing required fields: version, download_url"
            }), 400

        logger.info(f"[OTA] Install update requested: v{target_version}")

        # Download the release tarball
        tarball_path = updater.download_update(download_url)
        if not tarball_path:
            return jsonify({
                "success": False,
                "error": "Failed to download update package"
            }), 500

        # Run the update script
        result = updater.install_update(tarball_path, target_version)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"[OTA] Install update failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@web_bp.route('/api/update/status')
def get_ota_status():
    """
    Get current OTA update state.
    
    Returns:
        {
            "success": true,
            "current_version": "2.3.0",
            "last_check": "ISO datetime or null",
            "last_update": "ISO datetime or null",
            "update_status": "stable|rolled_back",
            "update_in_progress": true/false,
            "backup_version": "2.2.2 or null",
            "unstable_versions": ["2.2.3"]
        }
    """
    try:
        from app.core import updater, version

        state = updater.get_update_state()

        return jsonify({
            "success": True,
            "current_version": version.VERSION,
            "last_check": state.get('last_check'),
            "last_update": state.get('last_update'),
            "update_status": state.get('update_status', 'stable'),
            "update_in_progress": state.get('update_in_progress', False),
            "backup_version": state.get('backup_version'),
            "unstable_versions": state.get('unstable_versions', []),
        })

    except Exception as e:
        logger.error(f"[OTA] Get update status failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
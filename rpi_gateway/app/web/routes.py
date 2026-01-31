from flask import Blueprint, render_template, jsonify, redirect, url_for, current_app, request
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Create Flask Blueprint
web_bp = Blueprint('web', __name__, template_folder='templates', static_folder='static')

# Add custom Jinja filter for timestamp formatting
@web_bp.app_template_filter('strftime')
def strftime_filter(timestamp, format_string='%Y-%m-%d %H:%M:%S'):
    """Convert Unix timestamp to formatted datetime string."""
    try:
        return datetime.fromtimestamp(float(timestamp)).strftime(format_string)
    except (ValueError, TypeError):
        return 'Invalid timestamp'


def get_live_data():
    """
    Fetches the latest data and actuator states from the orchestrator.
    """
    # Get components from Flask app context
    serial_comm = getattr(current_app, 'serial_comm', None)
    config = current_app.config.get('MUSHROOM_CONFIG', {})
    
    # Get latest sensor data from app context (stored by orchestrator)
    sensor_data = current_app.config.get('LATEST_DATA', {})
    
    if not sensor_data or not isinstance(sensor_data, dict):
        # Fallback if no data available
        sensor_data = {
            'fruiting': None,
            'spawning': None
        }
    
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
    
    return {
        "fruiting_data": fruiting_data,
        "spawning_data": spawning_data,
        "fruiting_error": fruiting_error,
        "spawning_error": spawning_error,
        "fruiting_targets": fruiting_targets,
        "spawning_targets": spawning_targets,
        "fruiting_actuators": fruiting_actuators,
        "spawning_actuators": spawning_actuators,
        "backend_connected": getattr(current_app, 'backend_connected', False),
        "arduino_connected": serial_comm.is_connected if serial_comm else False
    }

# =======================================================
#                  WEB PAGE ROUTES
# =======================================================

@web_bp.route('/')
def index():
    """Redirects the root URL to the main dashboard."""
    return redirect(url_for('web.dashboard'))

@web_bp.route('/dashboard')
def dashboard():
    """Renders the main dashboard page with live data."""
    context = get_live_data()
    return render_template('dashboard.html', **context)

@web_bp.route('/controls')
def controls():
    """Renders the manual controls page with current actuator states."""
    context = get_live_data()
    
    # Add device room actuators
    device_actuators = {
        'exhaust_fan': False,
        'exhaust_fan_auto': False
    }
    
    # Update actuator names to match Arduino firmware
    # Map: mist_maker, humidifier_fan, exhaust_fan, intake_fan, led
    fruiting_actuators = {
        'mist_maker': False,
        'humidifier_fan': False,
        'exhaust_fan': False,
        'intake_fan': False,
        'led': False,
        'mist_maker_auto': False,
        'humidifier_fan_auto': False,
        'exhaust_fan_auto': False,
        'intake_fan_auto': False,
        'led_auto': False
    }
    
    spawning_actuators = {
        'exhaust_fan': False,
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
        ml_enabled = True
    except ImportError:
        ml_enabled = False
        
    return render_template('ai_insights.html', ml_enabled=ml_enabled)

@web_bp.route('/alerts')
def alerts():
    """Display system alerts page."""
    db = current_app.config.get('DB')
    recent_alerts = []
    
    if db:
        recent_alerts = db.get_recent_alerts(limit=100)
    
    return render_template('alerts.html', alerts=recent_alerts)

@web_bp.route('/settings')
def settings():
    """Renders the system settings page."""
    return render_template('settings.html')

@web_bp.route('/wifi-setup')
def wifi_setup():
    """Renders the WiFi provisioning page with available networks."""
    from app.utils import wifi_manager
    
    # Scan for available WiFi networks
    networks = wifi_manager.get_wifi_list()
    
    return render_template('wifi_setup.html', networks=networks)

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


# =======================================================
#                    API ENDPOINTS
# =======================================================

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
    
    return jsonify(data)

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
        command = f'{arduino_actuator}_{state}'
        success = serial_comm.send_command(command)
        
        if not success:
            logger.warning(f"Failed to send command to Arduino: {command}")
            return jsonify({"success": False, "message": "Failed to communicate with Arduino"}), 503
        
        logger.info(f"Sent command to Arduino: {command}")
        
        # Update actuator state in app config
        actuator_states = current_app.config.get('ACTUATOR_STATES', {'fruiting': {}, 'spawning': {}})
        
        # Map back to UI actuator name
        if room not in actuator_states:
            actuator_states[room] = {}
        
        actuator_states[room][actuator] = (state == 'ON')
        current_app.config['ACTUATOR_STATES'] = actuator_states
        
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
    
    logger.info(f"Auto mode {'enabled' if enabled else 'disabled'}")
    
    return jsonify({"success": True, "auto_mode": enabled})


@web_bp.route('/api/actuator_states')
def actuator_states():
    """
    API endpoint to get current actuator states.
    Returns state of all actuators across all rooms.
    """
    # TODO: Implement actual state tracking
    # For now, return dummy data
    states = {
        "fruiting": {
            "mist_maker": {"state": False, "auto": False},
            "humidifier_fan": {"state": False, "auto": False},
            "exhaust_fan": {"state": False, "auto": False},
            "intake_fan": {"state": False, "auto": False},
            "led": {"state": False, "auto": True}
        },
        "spawning": {
            "exhaust_fan": {"state": False, "auto": True, "mode": "passive"}
        },
        "device": {
            "exhaust_fan": {"state": False, "auto": True}
        }
    }
    
    return jsonify(states)
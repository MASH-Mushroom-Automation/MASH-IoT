from flask import Blueprint, render_template, jsonify, redirect, url_for, current_app, request
import time
import logging

logger = logging.getLogger(__name__)

# Create Flask Blueprint
web_bp = Blueprint('web', __name__, template_folder='templates', static_folder='static')


def get_live_data():
    """
    Fetches the latest data and actuator states from the orchestrator.
    """
    # Get components from Flask app context
    serial_comm = getattr(current_app, 'serial_comm', None)
    config = current_app.config.get('MUSHROOM_CONFIG', {})
    
    # Get latest sensor data
    if serial_comm and hasattr(serial_comm, 'get_latest_data'):
        sensor_data = serial_comm.get_latest_data()
    else:
        # Fallback demo data if Arduino not connected
        sensor_data = {
            "fruiting": {"temp": 23.5, "humidity": 88.2, "co2": 950.7},
            "spawning": None,  # Currently disabled in firmware
            "timestamp": time.time()
        }
    
    # Handle null/error states
    fruiting_data = sensor_data.get('fruiting') or {"temp": 0, "humidity": 0, "co2": 0}
    spawning_data = sensor_data.get('spawning') or {"temp": 0, "humidity": 0, "co2": 0}
    
    # Check for sensor errors
    fruiting_error = 'error' in fruiting_data
    spawning_error = 'error' in spawning_data if spawning_data else False
    
    # Get target thresholds from config
    fruiting_targets = config.get("fruiting_room", {})
    spawning_targets = config.get("spawning_room", {})
    
    # For actuator states, we'll track them separately in the orchestrator
    # For now, return empty states
    fruiting_actuators = {
        'exhaust_fan': False,
        'blower_fan': False,
        'humidifier': False,
        'humidifier_fan': False,
        'led': False
    }
    
    spawning_actuators = {
        'exhaust_fan': False
    }
    
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
    # We can reuse the get_live_data function to get the current state
    context = get_live_data()
    return render_template('controls.html', 
                           fruiting_actuators=context.get('fruiting_actuators', {}),
                           spawning_actuators=context.get('spawning_actuators', {}))

@web_bp.route('/alerts')
def alerts():
    """Renders the alerts and notifications page."""
    # In a real app, this data would come from the database
    dummy_alerts = [
        {"timestamp": "2026-01-27 10:30:00", "room": "fruiting", "level": "CRITICAL", "message": "CO2 levels exceeded 1200 ppm."},
        {"timestamp": "2026-01-27 09:15:23", "room": "fruiting", "level": "WARNING", "message": "Humidity dropped below 85% threshold."},
        {"timestamp": "2026-01-26 22:05:10", "room": "spawning", "level": "WARNING", "message": "Temperature is slightly above target at 26.5°C."}
    ]
    return render_template('alerts.html', alerts=dummy_alerts)

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

@web_bp.route('/settings')
def settings():
    """Renders the system settings page."""
    return render_template('settings.html')

@web_bp.route('/wifi-setup')
def wifi_setup():
    """Renders the WiFi provisioning page."""
    # In a real scenario, this would call wifi_manager.get_wifi_list()
    networks = ["WiFi_Network_1", "Another_SSID", "MyHomeWiFi"] 
    return render_template('wifi_setup.html', networks=networks)


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
    return jsonify(data)

@web_bp.route('/api/control_actuator', methods=['POST'])
def control_actuator():
    """
    API endpoint to manually control an actuator.
    Receives a JSON object like: {"room": "fruiting", "actuator": "exhaust_fan", "state": "ON"}
    """
    data = request.get_json()
    if not all(key in data for key in ['room', 'actuator', 'state']):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    room = data['room'].lower()
    actuator = data['actuator'].lower()
    state = data['state'].upper()
    
    if state not in ['ON', 'OFF']:
        return jsonify({"status": "error", "message": "Invalid state (must be ON or OFF)"}), 400

    # Get the serial comm object from app context
    serial_comm = getattr(current_app, 'serial_comm', None)

    if not serial_comm:
        logger.warning("Serial comm not available in app context")
        return jsonify({"status": "error", "message": "Serial communication not initialized"}), 500

    if not serial_comm.is_connected:
        logger.warning("Arduino not connected")
        return jsonify({"status": "error", "message": "Arduino not connected"}), 503

    # Use the friendly control_actuator method
    success = serial_comm.control_actuator(room, actuator, state)
    
    if success:
        logger.info(f"Actuator controlled: {room}/{actuator} -> {state}")
        
        # Also send to backend if available
        backend_client = getattr(current_app, 'backend_client', None)
        if backend_client:
            backend_client.send_alert(
                alert_type='manual_control',
                message=f"User set {room}/{actuator} to {state}",
                severity='INFO'
            )
        
        return jsonify({"status": "success", "room": room, "actuator": actuator, "state": state})
    else:
        return jsonify({"status": "error", "message": "Failed to send command to Arduino"}), 500
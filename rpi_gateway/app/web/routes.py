from flask import Blueprint, render_template, jsonify, redirect, url_for, current_app
from app.core.logic_engine import MushroomAI

# Create Flask Blueprint
web_bp = Blueprint('web', __name__, template_folder='templates', static_folder='static')

def get_live_data():
    """
    Fetches the latest data and actuator states.
    In a real app, this would get data from a shared state or database.
    """
    # For now, we simulate the data that would come from serial_comm
    # and be stored in the database.
    simulated_sensor_data = {
        "fruiting": {"temp": 23.5, "humidity": 88.2, "co2": 950.7},
        "spawning": {"temp": 24.1, "humidity": 92.5, "co2": 1850.2}
    }

    # Use the logic engine to determine actuator states
    # The config would normally be loaded from config.yaml
    config = current_app.config.get('MUSHROOM_CONFIG', {})
    ai_logic = MushroomAI(config=config)
    
    fruiting_actuators = ai_logic.predict_actuator_states('fruiting', simulated_sensor_data['fruiting'])
    spawning_actuators = ai_logic.predict_actuator_states('spawning', simulated_sensor_data['spawning'])
    
    # Convert actuator states from ON/OFF to True/False for the template
    fruiting_actuators_bool = {key: value == "ON" for key, value in fruiting_actuators.items()}
    spawning_actuators_bool = {key: value == "ON" for key, value in spawning_actuators.items()}

    return {
        "fruiting_data": simulated_sensor_data["fruiting"],
        "spawning_data": simulated_sensor_data["spawning"],
        "fruiting_targets": config.get("fruiting_room", {}),
        "spawning_targets": config.get("spawning_room", {}),
        "fruiting_actuators": fruiting_actuators_bool,
        "spawning_actuators": spawning_actuators_bool
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
    """Renders the manual controls page."""
    return render_template('controls.html')

@web_bp.route('/alerts')
def alerts():
    """Renders the alerts and notifications page."""
    return render_template('alerts.html')

@web_bp.route('/ai_insights')
def ai_insights():
    """Renders the AI/ML insights page."""
    return render_template('ai_insights.html')

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
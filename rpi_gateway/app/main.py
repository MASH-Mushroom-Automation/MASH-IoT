# M.A.S.H. IoT - Main Orchestrator
# Starts Flask web server and Arduino serial communication loop

import os
import sys
import logging
import time
import yaml
from flask import Flask
from flask_cors import CORS
from threading import Thread
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

# Add app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.serial_comm import ArduinoSerialComm
from core.logic_engine import MushroomAI
from database.db_manager import DatabaseManager
from cloud.backend_api import BackendAPIClient
from cloud.mqtt_client import create_mqtt_client
from web.routes import web_bp
from utils.user_preferences import UserPreferencesManager

# Optional mDNS support - app will work without it
try:
    from utils.mdns_advertiser import start_mdns_service, stop_mdns_service
    MDNS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"[mDNS] Module not available: {e}")
    logger.warning("[mDNS] Device discovery via mDNS will be disabled")
    MDNS_AVAILABLE = False
    def start_mdns_service(*args, **kwargs):
        return False
    def stop_mdns_service():
        pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MASHOrchestrator:
    """
    Main orchestrator for M.A.S.H. IoT system.
    Manages:
    - Flask web server
    - Arduino serial communication
    - Database operations
    - ML-powered automation
    """
    
    def __init__(self, config_path='config/config.yaml'):
        # Initialize user preferences manager
        self.user_prefs = UserPreferencesManager()
        
        # Load configuration (with user preferences merged)
        self.config = self.user_prefs.get_merged_config()
        
        # Flask app
        self.app = Flask(__name__, 
                         template_folder='web/templates',
                         static_folder='web/static')
        
        # Enable CORS for mobile app access
        CORS(self.app, resources={
            r"/api/*": {"origins": "*"},
            r"/status": {"origins": "*"},
            r"/dashboard": {"origins": "*"},
            r"/provisioning/*": {"origins": "*"},
            r"/wifi-*": {"origins": "*"},
        })
        
        # Register web blueprint
        self.app.register_blueprint(web_bp)
        
        # Store orchestrator reference in app for routes to access cycle manager
        self.app.config['orchestrator'] = self
        
        # Store user prefs in app context for access in routes
        self.app.config['USER_PREFS'] = self.user_prefs
        self.app.config['MUSHROOM_CONFIG'] = self.config
        
        # Initialize WiFi manager and ensure connectivity
        from utils import wifi_manager
        logger.info("[INIT] Checking network connectivity...")
        wifi_manager.ensure_connectivity()
        
        # Components
        self.db = DatabaseManager()
        
        # Backend API client with device config
        device_config = self.config.get('device', {})
        self.backend = BackendAPIClient(device_config=device_config)
        logger.info(f"[BACKEND] API client initialized for device: {device_config.get('serial_number', 'unknown')}")

        # Initialize Firebase Sync (Optional - will work without it)
        from cloud.firebase import FirebaseSync
        firebase_url = os.getenv('FIREBASE_DATABASE_URL', 'https://mash-ddf8d-default-rtdb.asia-southeast1.firebasedatabase.app')
        firebase_config = os.getenv('FIREBASE_CONFIG_PATH', 'config/firebase_config.json')
        self.firebase = FirebaseSync(config_path=firebase_config, db_url=firebase_url)
        
        if self.firebase.is_initialized:
            logger.info(f"[FIREBASE] ✅ Connected to Realtime Database")
            # Update device status on startup
            device_id = device_config.get('serial_number', 'rpi_gateway_001')
            self.firebase.sync_device_status(device_id, 'ONLINE', {
                'last_boot': time.strftime('%Y-%m-%d %H:%M:%S'),
                'ml_enabled': self.config.get('system', {}).get('ml_enabled', True),
            })
        else:
            logger.warning("[FIREBASE] Not initialized - running in offline mode only")
            self.firebase = None

        # Initialize MQTT Client
        self.mqtt = create_mqtt_client(device_id=device_config.get('serial_number', 'rpi_gateway_001'))
        
        # Arduino port (Windows: COM3, Linux: /dev/ttyACM0)
        arduino_port = 'COM3' if sys.platform == 'win32' else '/dev/ttyACM0'
        logger.info(f"[SERIAL] Using port: {arduino_port}")
        self.arduino = ArduinoSerialComm(port=arduino_port)
        
        # ML Logic Engine
        ml_enabled = (self.config or {}).get('system', {}).get('ml_enabled', True)
        if ml_enabled:
            self.ai = MushroomAI(config=self.config)
            self.ai.db = self.db  # Pass database reference for alerts
            logger.info("[ML] MushroomAI initialized")
        else:
            self.ai = None
            logger.info("[ML] ML disabled - using rule-based logic only")
        
        # State
        self.is_running = False
        self.start_time = time.time()  # Track uptime
        self.sensor_warmup_complete = False  # Track sensor calibration
        self.warmup_duration = 30  # Wait 30 seconds for sensors to stabilize
        self.latest_data = {
            'fruiting': None,
            'spawning': None
        }
    
    def _load_config(self, config_path):
        """Load configuration from YAML file."""
        try:
            full_path = os.path.join(os.path.dirname(__file__), '..', config_path)
            if not os.path.exists(full_path):
                logger.warning(f"[CONFIG] Config file not found: {full_path}, using defaults")
                return self._get_default_config()
            
            with open(full_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if config is None:
                logger.warning(f"[CONFIG] Empty config file, using defaults")
                return self._get_default_config()
                
            logger.info(f"[CONFIG] Loaded configuration from {config_path}")
            return config
        except Exception as e:
            logger.warning(f"[CONFIG] Failed to load config: {e}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self):
        """Return default configuration if YAML file is missing."""
        return {
            'fruiting_room': {
                'fan_control': {'co2_threshold': 900},
                'mist_control': {'humidity_threshold': 88},
                'light': {'duration': 12}
            },
            'spawning_room': {
                'fan_control': {'co2_threshold': 4000},
                'mist_control': {'humidity_threshold': 92},
                'light': {'duration': 0}
            },
            'system': {
                'ml_enabled': True,
                'sensor_read_interval': 5
            }
        }
    
    def on_sensor_data(self, data):
        """Callback when sensor data is received from Arduino."""
        try:
            # Check if sensor warmup period is complete
            time_since_boot = time.time() - self.start_time
            if not self.sensor_warmup_complete:
                if time_since_boot < self.warmup_duration:
                    logger.info(f"[WARMUP] Sensor calibration in progress... {int(self.warmup_duration - time_since_boot)}s remaining")
                    # Store data but don't run automation yet
                    if 'fruiting' in data:
                        self.latest_data['fruiting'] = data['fruiting']
                    if 'spawning' in data:
                        self.latest_data['spawning'] = data['spawning']
                    return
                else:
                    self.sensor_warmup_complete = True
                    self.app.config['SENSOR_WARMUP_COMPLETE'] = True  # Update Flask config
                    logger.info("[WARMUP] ✅ Sensor calibration complete! Starting automatic control...")
            
            # Store latest data (for web UI)
            if 'fruiting' in data:
                self.latest_data['fruiting'] = data['fruiting']
            if 'spawning' in data:
                self.latest_data['spawning'] = data['spawning']
            
            # Save to database (IMMEDIATELY - offline-first pattern)
            self.db.insert_sensor_data_batch(data)
            
            logger.info(f"[DATA] Received sensor data at {data.get('timestamp', 'unknown')}")
            
            # Upload to Firebase (Real-time sync for mobile app)
            if self.firebase:
                try:
                    # Prepare readings for Firebase
                    readings = []
                    device_id = self.config.get('device', {}).get('serial_number', 'rpi_gateway_001')
                    
                    if 'fruiting' in data:
                        readings.append({
                            'id': 0,
                            'room': 'fruiting',
                            'temp': data['fruiting'].get('temp'),
                            'humidity': data['fruiting'].get('humidity'),
                            'co2': data['fruiting'].get('co2'),
                            'timestamp': data.get('timestamp')
                        })
                    
                    if 'spawning' in data:
                        readings.append({
                            'id': 0,
                            'room': 'spawning',
                            'temp': data['spawning'].get('temp'),
                            'humidity': data['spawning'].get('humidity'),
                            'co2': data['spawning'].get('co2'),
                            'timestamp': data.get('timestamp')
                        })
                    
                    if readings:
                        self.firebase.sync_sensor_readings(readings)
                        
                        # Also update latest_reading path for quick access
                        # Normalize field names: Arduino uses 'temp' but mobile expects 'temperature'
                        from firebase_admin import db as firebase_db
                        latest_ref = firebase_db.reference(f'devices/{device_id}/latest_reading')
                        
                        latest_data = {'timestamp': data.get('timestamp')}
                        
                        if 'fruiting' in data:
                            fr = data['fruiting']
                            latest_data['fruiting'] = {
                                'temperature': fr.get('temp', fr.get('temperature')),
                                'humidity': fr.get('humidity'),
                                'co2': fr.get('co2'),
                                'timestamp': data.get('timestamp'),
                            }
                        
                        if 'spawning' in data:
                            sp = data['spawning']
                            latest_data['spawning'] = {
                                'temperature': sp.get('temp', sp.get('temperature')),
                                'humidity': sp.get('humidity'),
                                'co2': sp.get('co2'),
                                'timestamp': data.get('timestamp'),
                            }
                        
                        latest_ref.set(latest_data)
                except Exception as e:
                    logger.warning(f"[FIREBASE] Sync failed: {e}")
            
            # Upload to backend (non-blocking)
            if self.backend:
                try:
                    self.backend.send_sensor_data(data)
                except Exception as e:
                    logger.warning(f"[BACKEND] Upload failed: {e}")

            # Publish to MQTT (Real-time updates)
            if self.mqtt and self.mqtt.is_alive():
                try:
                    self.mqtt.publish_sensor_data(data)
                except Exception as e:
                    logger.warning(f"[MQQT] Publish failed: {e}")
            
            # Check if auto mode is enabled before running automation
            auto_mode = self.config.get('system', {}).get('auto_mode', True)
            
            # ML Automation: Process readings and generate commands (only in auto mode)
            # In manual mode, actuators stay in whatever state the user set them to
            if self.ai is not None and auto_mode:
                self._run_automation(data)
                
                # Only run humidifier cycle in auto mode
                if self.ai.humidifier_cycle.cycle_active:
                    import json
                    cycle_states = self.ai.humidifier_cycle.get_current_states()
                    
                    # Only send commands when state changes (avoid redundant sends)
                    for actuator, state in cycle_states.items():
                        if actuator == 'mist_maker':
                            arduino_name = 'MIST_MAKER'
                        elif actuator == 'humidifier_fan':
                            arduino_name = 'HUMIDIFIER_FAN'
                        else:
                            continue
                        
                        # Check if state changed since last send
                        last_state = self.ai.last_cycle_commands.get(actuator)
                        if last_state != state:
                            json_cmd = json.dumps({"actuator": arduino_name, "state": state})
                            if self.arduino.send_command(json_cmd):
                                logger.info(f"[CYCLE] State changed: {actuator} -> {state}")
                                # Update UI state
                                command_for_state = f"{arduino_name}_{state}"
                                self._update_actuator_state_from_command(command_for_state)
                                self.db.insert_command(json_cmd, source='humidifier_cycle')
                                # Remember this state
                                self.ai.last_cycle_commands[actuator] = state
            else:
                # In manual mode, stop any active cycles
                if self.ai and self.ai.humidifier_cycle.cycle_active:
                    self.ai.humidifier_cycle.stop_cycle()
                    self.ai.last_cycle_commands = {}
                    logger.info("[MANUAL MODE] Stopped automatic humidifier cycle")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to process sensor data: {e}")
    
    def _run_automation(self, data):
        """Run ML-powered automation on sensor data."""
        try:
            # Get manual overrides and clean up old ones (>5 minutes)
            manual_overrides = self.config.get('MANUAL_OVERRIDES', {})
            current_time = time.time()
            for room in list(manual_overrides.keys()):
                for actuator in list(manual_overrides[room].keys()):
                    if current_time - manual_overrides[room][actuator].get('timestamp', 0) > 300:  # 5 minutes
                        del manual_overrides[room][actuator]
                        logger.info(f"[AUTO] Manual override expired: {room}/{actuator}")
                if not manual_overrides[room]:  # Remove empty room dict
                    del manual_overrides[room]
            
            # Filter out invalid readings (sensor errors)
            valid_rooms = {}
            for room in ['fruiting', 'spawning']:
                if room in data and data[room]:
                    # Check if it's an error message
                    if 'error' not in data[room]:
                        valid_rooms[room] = data[room]
                    else:
                        logger.warning(f"[AUTO] Skipping {room} room - sensor error: {data[room].get('error')}")
            
            # Only run automation if we have valid data from at least one room
            if not valid_rooms:
                logger.debug("[AUTO] No valid sensor data to process")
                return
            
            # Get recommended commands from AI (pass all rooms at once)
            commands = self.ai.process_sensor_reading(valid_rooms)
            
            # Filter out commands for manually overridden actuators
            manual_overrides = self.config.get('MANUAL_OVERRIDES', {})
            filtered_commands = []
            for command in commands:
                # Parse command to extract room and actuator
                # Commands are like: "FRUITING_EXHAUST_FAN_ON" or "MIST_MAKER_OFF"
                skip_command = False
                for room in manual_overrides:
                    for actuator in manual_overrides[room]:
                        # Map UI actuator names to Arduino command names
                        actuator_mappings = {
                            'exhaust_fan': ['EXHAUST_FAN', 'FRUITING_EXHAUST_FAN', 'SPAWNING_EXHAUST_FAN'],
                            'intake_fan': ['INTAKE_FAN', 'FRUITING_INTAKE_FAN'],
                            'mist_maker': ['MIST_MAKER'],
                            'humidifier_fan': ['HUMIDIFIER_FAN'],
                            'led': ['LED', 'FRUITING_LED']
                        }
                        arduino_names = actuator_mappings.get(actuator, [])
                        if any(name in command for name in arduino_names):
                            logger.debug(f"[AUTO] Skipping command '{command}' - {room}/{actuator} has manual override")
                            skip_command = True
                            break
                    if skip_command:
                        break
                if not skip_command:
                    filtered_commands.append(command)
            
            # Send filtered commands to Arduino
            import json
            for command in filtered_commands:
                # Convert command format from "ACTUATOR_NAME_STATE" to JSON
                # e.g., "MIST_MAKER_ON" -> {"actuator": "MIST_MAKER", "state": "ON"}
                if '_ON' in command:
                    actuator_name = command.replace('_ON', '')
                    state = 'ON'
                elif '_OFF' in command:
                    actuator_name = command.replace('_OFF', '')
                    state = 'OFF'
                else:
                    logger.warning(f"[AUTO] Invalid command format: {command}")
                    continue
                
                json_cmd = json.dumps({"actuator": actuator_name, "state": state})
                success = self.arduino.send_command(json_cmd)
                
                if success:
                    logger.info(f"[AUTO] Sent command: {json_cmd}")
                    
                    # Update actuator states in app config for UI
                    self._update_actuator_state_from_command(command)
                    
                    # Log to database
                    self.db.insert_command(json_cmd, source='ml_automation')
                else:
                    logger.warning(f"[AUTO] Failed to send command: {json_cmd}")
        
        except Exception as e:
            logger.error(f"[AUTO] Automation error: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_actuator_state_from_command(self, command):
        """Parse Arduino command and update actuator state in app config."""
        try:
            # Command format: ACTUATOR_NAME_ON or ACTUATOR_NAME_OFF
            # Examples: MIST_MAKER_ON, FRUITING_EXHAUST_FAN_OFF
            
            if '_ON' in command:
                state = True
                actuator_cmd = command.replace('_ON', '')
            elif '_OFF' in command:
                state = False
                actuator_cmd = command.replace('_OFF', '')
            else:
                return
            
            # Get actuator states from app config
            actuator_states = self.app.config.get('ACTUATOR_STATES', {})
            
            # Map Arduino commands to rooms and actuators
            if actuator_cmd == 'MIST_MAKER':
                actuator_states['fruiting']['mist_maker'] = state
            elif actuator_cmd == 'HUMIDIFIER_FAN':
                actuator_states['fruiting']['humidifier_fan'] = state
            elif actuator_cmd == 'FRUITING_EXHAUST_FAN':
                actuator_states['fruiting']['exhaust_fan'] = state
            elif actuator_cmd == 'FRUITING_INTAKE_FAN':
                actuator_states['fruiting']['intake_fan'] = state
            elif actuator_cmd == 'FRUITING_LED':
                actuator_states['fruiting']['led'] = state
            elif actuator_cmd == 'SPAWNING_EXHAUST_FAN':
                actuator_states['spawning']['exhaust_fan'] = state
            elif actuator_cmd == 'DEVICE_EXHAUST_FAN':
                actuator_states['device']['exhaust_fan'] = state
            
            # Update app config
            self.app.config['ACTUATOR_STATES'] = actuator_states
            
        except Exception as e:
            logger.error(f"[STATE] Failed to update actuator state: {e}")
    
    def _handle_mqtt_command(self, payload):
        """
        Handle incoming MQTT commands from mobile app or backend.
        Payload format: {"actuator": "MIST_MAKER", "state": "ON", "source": "mobile_app"}
        """
        try:
            actuator = payload.get('actuator')
            state = payload.get('state', '').upper()
            source = payload.get('source', 'unknown')
            
            if not actuator or state not in ['ON', 'OFF']:
                logger.warning(f"[MQTT] Invalid command payload: {payload}")
                return
            
            logger.info(f"[MQTT] 📱 Remote command from {source}: {actuator} -> {state}")
            
            # Send to Arduino via serial
            import json
            json_cmd = json.dumps({"actuator": actuator, "state": state})
            success = self.arduino.send_command(json_cmd)
            
            if success:
                logger.info(f"[MQTT] ✅ Command forwarded to Arduino: {json_cmd}")
                # Update local actuator state for web UI
                command_for_state = f"{actuator}_{state}"
                self._update_actuator_state_from_command(command_for_state)
                # Log command to database
                self.db.insert_command(json_cmd, source=f'mqtt_{source}')
                
                # Track manual override to prevent auto-mode from changing this actuator
                with self.app.app_context():
                    manual_overrides = self.app.config.get('MANUAL_OVERRIDES', {})
                    # Map Arduino actuator name to UI actuator name and room
                    room = 'fruiting'
                    ui_actuator = actuator.lower()
                    if 'SPAWNING' in actuator:
                        room = 'spawning'
                    if 'DEVICE' in actuator:
                        room = 'device'
                    # Strip room prefix for UI name
                    ui_actuator = ui_actuator.replace('fruiting_', '').replace('spawning_', '').replace('device_', '')
                    
                    if room not in manual_overrides:
                        manual_overrides[room] = {}
                    manual_overrides[room][ui_actuator] = {'state': state, 'timestamp': time.time()}
                    self.app.config['MANUAL_OVERRIDES'] = manual_overrides
            else:
                logger.warning(f"[MQTT] ❌ Failed to forward command to Arduino")
                
        except Exception as e:
            logger.error(f"[MQTT] Error handling command: {e}")
            import traceback
            traceback.print_exc()
    
    def start_serial_listener(self):
        """Start Arduino serial communication in background thread."""
        def serial_loop():
            logger.info("[SERIAL] Starting serial listener...")
            
            # Connect to Arduino
            if not self.arduino.connect():
                logger.warning("[SERIAL] Arduino not connected - running in DEMO mode")
                logger.warning("[SERIAL] Web UI will work but no real sensor data")
                return
            
            # Start listening
            self.arduino.start_listening(callback=self.on_sensor_data)
            
            # Keep thread alive
            while self.is_running:
                time.sleep(1)
            
            # Cleanup
            self.arduino.disconnect()
            logger.info("[SERIAL] Serial listener stopped")
        
        thread = Thread(target=serial_loop, daemon=True)
        thread.start()
    
    def start(self, host='0.0.0.0', port=5000, debug=False):
        """Start the M.A.S.H. system and register device with backend"""
        try:
            if self.backend:
                try:
                    self.backend.register_device()
                except Exception as e:
                    logger.warning(f"[BACKEND] Device registration failed: {e}")
            
            # Connect MQTT
            if self.mqtt:
                self.mqtt.set_command_callback(self._handle_mqtt_command)
                mqtt_connected = self.mqtt.connect()
                if mqtt_connected:
                    logger.info("[MQTT] ✅ Connected to HiveMQ Cloud - remote control enabled")
                else:
                    logger.warning("[MQTT] ⚠️ Failed to connect - remote control unavailable")

            # Connect to database
            self.db.connect()
            # Start serial communication
            self.is_running = True
            self.start_serial_listener()
            # Make components available to Flask routes via app context
            self.app.serial_comm = self.arduino
            self.app.backend_client = self.backend
            self.app.backend_connected = self.backend.check_connection() if self.backend else False
            self.app.logic_engine = self.ai  # Pass ML engine to routes
            self.app.orchestrator = self  # Pass orchestrator for cycle manager access
            self.app.config['MUSHROOM_CONFIG'] = self.config
            self.app.config['LATEST_DATA'] = self.latest_data
            self.app.config['START_TIME'] = self.start_time
            self.app.config['SENSOR_WARMUP_COMPLETE'] = False  # Track sensor calibration status
            self.app.config['WARMUP_DURATION'] = self.warmup_duration
            self.app.config['ACTUATOR_STATES'] = {
                'fruiting': {
                    'mist_maker': False,
                    'humidifier_fan': False,
                    'exhaust_fan': False,
                    'intake_fan': False,
                    'led': False
                },
                'spawning': {
                    'exhaust_fan': False
                },
                'device': {
                    'exhaust_fan': False
                }
            }
            self.app.config['DB'] = self.db
            
            # Start mDNS service advertisement for local discovery (optional)
            if MDNS_AVAILABLE:
                device_config = self.config.get('device', {})
                device_id = device_config.get('serial_number', 'MASH-Device')
                device_name = device_config.get('name', 'MASH IoT Chamber')
                logger.info(f"[mDNS] Starting service advertisement...")
                mdns_started = start_mdns_service(device_id=device_id, device_name=device_name, port=port)
                if not mdns_started:
                    logger.warning("[mDNS] Failed to start mDNS - device won't be discoverable via mDNS")
                    logger.warning("[mDNS] Install: pip install zeroconf && sudo apt-get install avahi-daemon")
            else:
                logger.info("[mDNS] Module not installed - device discovery disabled")
            
            logger.info(f"[WEB] Starting Flask server on {host}:{port}")
            logger.info(f"[WEB] Access dashboard at: http://{host}:{port}/dashboard")
            # Start Flask (blocks here)
            self.app.run(host=host, port=port, debug=debug, use_reloader=False)
        except KeyboardInterrupt:
            logger.info("[MAIN] Shutting down...")
        except Exception as e:
            logger.error(f"[MAIN] Error: {e}")
        finally:
            self.shutdown()
    def shutdown(self):
        """Graceful shutdown."""
        logger.info("[MAIN] Shutting down M.A.S.H. system...")
        self.is_running = False
        
        # Stop mDNS service
        try:
            stop_mdns_service()
        except Exception as e:
            logger.warning(f"[mDNS] Error stopping mDNS: {e}")
        
        # Disconnect Arduino
        if self.arduino:
            self.arduino.disconnect()
        
        # Disconnect MQTT
        if self.mqtt:
            self.mqtt.disconnect()

        # Close backend connection
        if self.backend:
            self.backend.close()
        # Close database
        if self.db:
            self.db.disconnect()
        logger.info("[MAIN] Goodbye!")


def main():
    """Entry point."""
    orchestrator = MASHOrchestrator()
    orchestrator.start(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    main()


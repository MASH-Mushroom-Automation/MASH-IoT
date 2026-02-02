# M.A.S.H. IoT - Main Orchestrator
# Starts Flask web server and Arduino serial communication loop

import os
import sys
import logging
import time
import yaml
from flask import Flask
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
from web.routes import web_bp
from utils.user_preferences import UserPreferencesManager

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
        
        # Register web blueprint
        self.app.register_blueprint(web_bp)
        
        # Store orchestrator reference in app for routes to access cycle manager
        self.app.config['orchestrator'] = self
        
        # Store user prefs in app context for access in routes
        self.app.config['USER_PREFS'] = self.user_prefs
        self.app.config['MUSHROOM_CONFIG'] = self.config
        
        # Components
        self.db = DatabaseManager()
        
        # Backend API client with device config
        device_config = self.config.get('device', {})
        self.backend = BackendAPIClient(device_config=device_config)
        logger.info(f"[BACKEND] API client initialized for device: {device_config.get('serial_number', 'unknown')}")
        
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
            
            # Upload to backend (non-blocking)
            if self.backend:
                try:
                    self.backend.send_sensor_data(data)
                except Exception as e:
                    logger.warning(f"[BACKEND] Upload failed: {e}")
            
            # ML Automation: Process readings and generate commands
            if self.ai is not None:
                self._run_automation(data)
            
            # Always update humidifier cycle (even in manual mode)
            # This ensures the cycle continues running and sends commands
            if self.ai and self.ai.humidifier_cycle.cycle_active:
                import json
                cycle_states = self.ai.humidifier_cycle.get_current_states()
                # Send cycle commands to Arduino
                for actuator, state in cycle_states.items():
                    if actuator == 'mist_maker':
                        arduino_name = 'MIST_MAKER'
                    elif actuator == 'humidifier_fan':
                        arduino_name = 'HUMIDIFIER_FAN'
                    else:
                        continue
                    
                    json_cmd = json.dumps({"actuator": arduino_name, "state": state})
                    if self.arduino.send_command(json_cmd):
                        logger.debug(f"[CYCLE] Sent: {json_cmd}")
                        # Update UI state
                        command_for_state = f"{arduino_name}_{state}"
                        self._update_actuator_state_from_command(command_for_state)
                        self.db.insert_command(json_cmd, source='humidifier_cycle')
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to process sensor data: {e}")
    
    def _run_automation(self, data):
        """Run ML-powered automation on sensor data."""
        try:
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
            
            # Send commands to Arduino
            import json
            for command in commands:
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
        # Disconnect Arduino
        if self.arduino:
            self.arduino.disconnect()
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


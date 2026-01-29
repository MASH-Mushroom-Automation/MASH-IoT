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
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Flask app
        self.app = Flask(__name__, 
                         template_folder='web/templates',
                         static_folder='web/static')
        
        # Register web blueprint
        self.app.register_blueprint(web_bp)
        
        # Components
        self.db = DatabaseManager()
        
        # Backend API client
        self.backend = BackendAPIClient()
        logger.info("[BACKEND] API client initialized")
        
        # Arduino port (Windows: COM3, Linux: /dev/ttyACM0)
        arduino_port = 'COM3' if sys.platform == 'win32' else '/dev/ttyACM0'
        logger.info(f"[SERIAL] Using port: {arduino_port}")
        self.arduino = ArduinoSerialComm(port=arduino_port)
        
        # ML Logic Engine
        ml_enabled = (self.config or {}).get('system', {}).get('ml_enabled', True)
        if ml_enabled:
            self.ai = MushroomAI(config=self.config)
            logger.info("[ML] MushroomAI initialized")
        else:
            self.ai = None
            logger.info("[ML] ML disabled - using rule-based logic only")
        
        # State
        self.is_running = False
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
            for command in commands:
                success = self.arduino.send_command(command)
                
                if success:
                    logger.info(f"[AUTO] Sent command: {command}")
                    
                    # Log to database
                    self.db.insert_command(command, source='ml_automation')
                else:
                    logger.warning(f"[AUTO] Failed to send command: {command}")
        
        except Exception as e:
            logger.error(f"[AUTO] Automation error: {e}")
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
            # Connect to database
            self.db.connect()
            # Start serial communication
            self.is_running = True
            self.start_serial_listener()
            # Make components available to Flask routes via app context
            self.app.serial_comm = self.arduino
            self.app.backend_client = self.backend
            self.app.backend_connected = self.backend.check_connection() if self.backend else False
            self.app.config['MUSHROOM_CONFIG'] = self.config
            self.app.config['LATEST_DATA'] = self.latest_data
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


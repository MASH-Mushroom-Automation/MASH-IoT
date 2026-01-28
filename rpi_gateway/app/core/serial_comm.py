# M.A.S.H. IoT - Serial Communication Module
# Manages USB Serial communication between Raspberry Pi and Arduino

import serial
import json
import time
import threading
from typing import Optional, Callable, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Arduino Actuator Name Constants (matches Arduino firmware)
ACTUATORS = {
    'fruiting': {
        'exhaust_fan': 'FRUITING_EXHAUST_FAN',
        'blower_fan': 'FRUITING_BLOWER_FAN',
        'humidifier_fan': 'HUMIDIFIER_FAN',
        'humidifier': 'HUMIDIFIER',
        'led': 'FRUITING_LED'
    },
    'spawning': {
        'exhaust_fan': 'SPAWNING_EXHAUST_FAN'
    }
}


class ArduinoSerialComm:
    """
    Handles serial communication with Arduino Uno R3.
    
    Protocol:
    - Arduino sends JSON every 5 seconds: {"fruiting": {"temp": 23.5, "humidity": 85, "co2": 800}}
    - RPi sends plain text commands: "FRUITING_EXHAUST_FAN_ON\n", "HUMIDIFIER_OFF\n"
    
    Supported actuators (from Arduino config.h):
    - SPAWNING_EXHAUST_FAN
    - FRUITING_EXHAUST_FAN
    - FRUITING_BLOWER_FAN
    - HUMIDIFIER_FAN
    - HUMIDIFIER
    - FRUITING_LED
    """
    
    def __init__(self, port: str = '/dev/ttyACM0', baudrate: int = 9600, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        self.is_listening = False
        self.listen_thread: Optional[threading.Thread] = None
        self.data_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # Track latest sensor data
        self.latest_data: Dict[str, Any] = {
            'fruiting': None,
            'spawning': None,
            'timestamp': None
        }
        
    def connect(self) -> bool:
        """Establish serial connection to Arduino."""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            # Wait for Arduino to reset after connection
            time.sleep(2)
            
            # Flush any startup garbage
            self.serial_conn.reset_input_buffer()
            self.serial_conn.reset_output_buffer()
            
            self.is_connected = True
            logger.info(f"Connected to Arduino on {self.port} at {self.baudrate} baud")
            return True
            
        except serial.SerialException as e:
            logger.error(f"Failed to connect to Arduino on {self.port}: {e}")
            logger.warning("Running in DEMO MODE without hardware")
            self.is_connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to Arduino: {e}")
            self.is_connected = False
            return False
            logger.info(f"[SERIAL] Connected to Arduino on {self.port} @ {self.baudrate} baud")
            return True
            
        except serial.SerialException as e:
            logger.error(f"[SERIAL] Connection failed: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Close serial connection."""
        self.stop_listening()
        
        if self.serial_conn and self.serial_conn.is_open:
            # Send shutdown command before disconnecting
            self.send_command("ALL_OFF")
            time.sleep(0.5)
            self.serial_conn.close()
            logger.info("[SERIAL] Disconnected from Arduino")
        
        self.is_connected = False
    
    def send_command(self, command: str) -> bool:
        """
        Send a command string to the Arduino.
        
        Args:
            command: The command to send (e.g., "FRUITING_FAN_ON").
            
        Returns:
            True if successful, False otherwise.
        """
        if not self.is_connected or not self.serial_conn:
            logger.warning(f"Cannot send command '{command}': Not connected.")
            return False
        
        try:
            # Ensure command ends with a newline character, as Arduino expects
            cmd_with_newline = f"{command}\n".encode('utf-8')
            self.serial_conn.write(cmd_with_newline)
            self.serial_conn.flush() # Wait until all data is written
            logger.info(f"Sent command to Arduino: {command}")
            return True
        except Exception as e:
            logger.error(f"Failed to send command '{command}': {e}")
            return False
    
    def read_line(self) -> Optional[str]:
        """Read a single line from Arduino."""
        if not self.is_connected or not self.serial_conn:
            return None
        
        try:
            if self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode('utf-8').strip()
                return line if line else None
            return None
            
        except Exception as e:
            logger.error(f"[SERIAL] Read failed: {e}")
            return None
    
    def parse_sensor_data(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON sensor data from Arduino.
        
        Expected format from Arduino:
        {"fruiting": {"temp": 24.5, "humidity": 85, "co2": 800}}
        or with error: {"fruiting": {"error": "invalid_reading"}}
        
        Note: Spawning room sensor is currently disabled in Arduino firmware
        """
        try:
            data = json.loads(line)
            
            # Validate structure - must have at least fruiting room
            if 'fruiting' not in data:
                logger.warning(f"[SERIAL] Invalid JSON structure: {line}")
                return None
            
            # Add timestamp
            data['timestamp'] = time.time()
            
            # Log if there are errors in readings
            if 'error' in data.get('fruiting', {}):
                logger.warning(f"[ARDUINO] Fruiting sensor error: {data['fruiting']['error']}")
            if 'spawning' in data and 'error' in data.get('spawning', {}):
                logger.warning(f"[ARDUINO] Spawning sensor error: {data['spawning']['error']}")
            
            # Store latest data
            self.latest_data = data
            
            return data
            
        except json.JSONDecodeError:
            # Not JSON - probably a debug message from Arduino
            if line.startswith('['):
                logger.debug(f"[ARDUINO] {line}")
            else:
                logger.debug(f"[ARDUINO] Non-JSON: {line}")
            return None
        except Exception as e:
            logger.error(f"[SERIAL] Parse error: {e}")
            return None
    
    def start_listening(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Start background thread to listen for sensor data.
        
        Args:
            callback: Function to call when data is received
        """
        if self.is_listening:
            logger.warning("[SERIAL] Already listening")
            return
        
        self.data_callback = callback
        self.is_listening = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        logger.info("[SERIAL] Started listening thread")
    
    def stop_listening(self):
        """Stop the listening thread."""
        if not self.is_listening:
            return
        
        self.is_listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=2)
        logger.info("[SERIAL] Stopped listening thread")
    
    def _listen_loop(self):
        """Background thread loop for reading serial data."""
        logger.info("[SERIAL] Listen loop started")
        
        while self.is_listening:
            try:
                line = self.read_line()
                
                if line:
                    # Try to parse as JSON sensor data
                    data = self.parse_sensor_data(line)
                    
                    if data and self.data_callback:
                        self.data_callback(data)
                
                # Small delay to prevent CPU spinning
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"[SERIAL] Listen loop error: {e}")
                time.sleep(1)  # Back off on error
        
        logger.info("[SERIAL] Listen loop stopped")
    
    def __enter__(self):
        """Context manager support."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.disconnect()

    def control_actuator(self, room: str, actuator_type: str, state: str) -> bool:
        """
        Control a specific actuator with friendly names.
        
        Args:
            room: 'fruiting' or 'spawning'
            actuator_type: 'exhaust_fan', 'humidifier', 'led', etc.
            state: 'ON' or 'OFF'
        
        Returns:
            True if command sent successfully
            
        Example:
            control_actuator('fruiting', 'exhaust_fan', 'ON')
            -> Sends "FRUITING_EXHAUST_FAN_ON\n" to Arduino
        """
        if room not in ACTUATORS:
            logger.error(f"Invalid room: {room}")
            return False
            
        if actuator_type not in ACTUATORS[room]:
            logger.error(f"Invalid actuator type '{actuator_type}' for room '{room}'")
            return False
        
        state = state.upper()
        if state not in ['ON', 'OFF']:
            logger.error(f"Invalid state: {state}")
            return False
        
        actuator_name = ACTUATORS[room][actuator_type]
        command = f"{actuator_name}_{state}"
        
        return self.send_command(command)
    
    def get_latest_data(self) -> Dict[str, Any]:
        """Get the most recent sensor data received from Arduino."""
        return self.latest_data.copy()


# ==================== CONVENIENCE FUNCTIONS ====================
def create_arduino_connection(port: str = '/dev/ttyACM0') -> ArduinoSerialComm:
    """Create and connect to Arduino."""
    comm = ArduinoSerialComm(port=port)
    comm.connect()
    return comm


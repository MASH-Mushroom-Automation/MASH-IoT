# M.A.S.H. IoT - Serial Communication Module
# Manages USB Serial communication between Raspberry Pi and Arduino

import serial
import serial.tools.list_ports
import json
import time
import threading
from typing import Optional, Callable, Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Arduino Actuator Name Constants (matches Arduino firmware)
ACTUATORS = {
    'fruiting': {
        'mist_maker': 'MIST_MAKER',
        'humidifier_fan': 'HUMIDIFIER_FAN',
        'exhaust_fan': 'FRUITING_EXHAUST_FAN',
        'intake_fan': 'FRUITING_INTAKE_FAN',
        'led': 'FRUITING_LED'
    },
    'spawning': {
        'exhaust_fan': 'SPAWNING_EXHAUST_FAN'
    },
    'device': {
        'exhaust_fan': 'DEVICE_EXHAUST_FAN'
    }
}


class ArduinoSerialComm:
    """
    Handles serial communication with Arduino Uno R3.
    
    Protocol:
    - Arduino sends JSON every 5 seconds: {"fruiting": {"temp": 23.5, "humidity": 85, "co2": 800}}
    - RPi sends plain text commands: "FRUITING_EXHAUST_FAN_ON\n", "HUMIDIFIER_OFF\n"
    
    Features:
    - Auto-detection of Arduino USB port (searches /dev/ttyACM* and /dev/ttyUSB*)
    - Auto-reconnect if Arduino disconnects
    - Room-specific data access (fruiting/spawning)
    
    Supported actuators (from Arduino config.h):
    - SPAWNING_EXHAUST_FAN
    - FRUITING_EXHAUST_FAN
    - FRUITING_BLOWER_FAN
    - HUMIDIFIER_FAN
    - HUMIDIFIER
    - FRUITING_LED
    """
    
    def __init__(self, port: str = '/dev/ttyACM0', baudrate: int = 9600, timeout: float = 1.0, auto_reconnect: bool = True):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.auto_reconnect = auto_reconnect
        self.reconnect_interval = 5  # seconds
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
        
        # Relay state tracking for recovery after disconnects
        self.last_relay_states: Dict[str, str] = {}  # {"MIST_MAKER": "ON", "FRUITING_EXHAUST_FAN": "OFF", ...}
        
        # Heartbeat tracking
        self.last_write_time = time.time()
        self.heartbeat_interval = 15.0  # Send keepalive every 15s (well below 60s watchdog)
    
    @staticmethod
    def find_arduino_port() -> Optional[str]:
        """
        Auto-detect Arduino USB port on Raspberry Pi.
        
        Returns:
            Port name (e.g., '/dev/ttyACM0') or None if not found
            
        Note: On RPi, Arduino typically appears as:
        - /dev/ttyACM0 (Arduino Uno, Mega with native USB)
        - /dev/ttyUSB0 (Arduino with CH340/FTDI chip)
        """
        logger.info("[SERIAL] Scanning for Arduino...")
        
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            # Check for Arduino identifiers
            if 'Arduino' in port.description or \
               'ttyACM' in port.device or \
               'ttyUSB' in port.device or \
               '2341' in str(port.vid):  # Arduino VID
                logger.info(f"[SERIAL] Found Arduino: {port.device} ({port.description})")
                return port.device
        
        logger.warning("[SERIAL] No Arduino found. Available ports:")
        for port in ports:
            logger.warning(f"  - {port.device}: {port.description}")
        
        return None
        
    def connect(self, auto_detect: bool = True) -> bool:
        """
        Establish serial connection to Arduino.
        
        Args:
            auto_detect: If True, automatically search for Arduino port
        """
        try:
            # Auto-detect Arduino port if enabled
            if auto_detect:
                detected_port = self.find_arduino_port()
                if detected_port:
                    self.port = detected_port
                else:
                    logger.warning(f"[SERIAL] Auto-detect failed, using configured port: {self.port}")
            
            logger.info(f"[SERIAL] Connecting to {self.port}...")
            
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
            logger.info(f"[SERIAL] ✓ Connected to Arduino on {self.port} @ {self.baudrate} baud")
            return True
            
        except serial.SerialException as e:
            logger.error(f"[SERIAL] Failed to connect to {self.port}: {e}")
            self.is_connected = False
            return False
        except Exception as e:
            logger.error(f"[SERIAL] Unexpected error: {e}")
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
        Send a JSON command string to the Arduino.
        
        Args:
            command: JSON command string (e.g., '{"actuator": "MIST_MAKER", "state": "ON"}').
            
        Returns:
            True if successful, False otherwise.
        """
        if not self.is_connected or not self.serial_conn:
            logger.warning(f"Cannot send command '{command}': Not connected.")
            return False
        
        try:
            # Parse command to track relay state for recovery
            import json
            try:
                cmd_data = json.loads(command)
                if 'actuator' in cmd_data and 'state' in cmd_data:
                    actuator = cmd_data['actuator']
                    state = cmd_data['state']
                    self.last_relay_states[actuator] = state
                    logger.debug(f"[STATE] Tracked: {actuator} = {state}")
            except json.JSONDecodeError:
                pass  # Not a relay command, skip tracking
            
            # Add newline and encode
            cmd_with_newline = f"{command}\n".encode('utf-8')
            
            self.serial_conn.write(cmd_with_newline)
            # self.serial_conn.flush()  # Removed to prevent blocking on slow serial
            
            self.last_write_time = time.time()  # Update heartbeat timer
            logger.info(f"[SERIAL] ✅ Sent command: {command}")
            return True
        except Exception as e:
            logger.error(f"[SERIAL] ❌ Failed to send command '{command}': {e}")
            return False
    
    def restore_relay_states(self) -> bool:
        """
        Restore all relay states after Arduino reset or reconnection.
        Sends all previously tracked relay commands to restore system state.
        
        Returns:
            True if all commands sent successfully, False otherwise.
        """
        if not self.last_relay_states:
            logger.info("[RECOVERY] No relay states to restore")
            return True
        
        logger.info(f"[RECOVERY] 🔄 Restoring {len(self.last_relay_states)} relay states...")
        success_count = 0
        
        for actuator, state in self.last_relay_states.items():
            import json
            cmd = json.dumps({"actuator": actuator, "state": state})
            if self.send_command(cmd):
                success_count += 1
                time.sleep(0.1)  # Small delay between commands to prevent Arduino buffer overflow
            else:
                logger.warning(f"[RECOVERY] Failed to restore {actuator} = {state}")
        
        logger.info(f"[RECOVERY] ✅ Restored {success_count}/{len(self.last_relay_states)} relay states")
        return success_count == len(self.last_relay_states)
    
    def read_line(self) -> Optional[str]:
        """Read a single line from Arduino."""
        if not self.is_connected or not self.serial_conn:
            return None
        
        try:
            # Check if port is actually open
            if not self.serial_conn.is_open:
                logger.warning("[SERIAL] Port closed unexpectedly")
                self.is_connected = False
                return None
            
            if self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode('utf-8').strip()
                return line if line else None
            return None
            
        except (serial.SerialException, OSError, IOError) as e:
            logger.error(f"[SERIAL] Read failed - Connection lost: {e}")
            self.is_connected = False
            # Try to close the dead connection
            try:
                if self.serial_conn:
                    self.serial_conn.close()
            except:
                pass
            return None
        except Exception as e:
            logger.error(f"[SERIAL] Unexpected read error: {e}")
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
        """Background thread loop for reading serial data with auto-reconnect."""
        logger.info("[SERIAL] Listen loop started")
        
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        while self.is_listening:
            try:
                # Check if connection is alive
                if not self.is_connected or not self.serial_conn or not self.serial_conn.is_open:
                    if self.auto_reconnect:
                        logger.warning("[SERIAL] 🔴 Connection lost. Attempting to reconnect...")
                        
                        # Close any existing connection
                        if self.serial_conn:
                            try:
                                self.serial_conn.close()
                            except:
                                pass
                            self.serial_conn = None
                        
                        # Attempt reconnection
                        if self.connect(auto_detect=True):
                            logger.info("[SERIAL] 🟢 Reconnected successfully!")
                            consecutive_failures = 0
                            
                            # Restore relay states after reconnection
                            time.sleep(2)  # Wait for Arduino to stabilize after reset
                            self.restore_relay_states()
                        else:
                            consecutive_failures += 1
                            logger.error(f"[SERIAL] Reconnect failed ({consecutive_failures}/{max_consecutive_failures}). Retrying in {self.reconnect_interval}s...")
                            time.sleep(self.reconnect_interval)
                            continue
                    else:
                        logger.error("[SERIAL] Connection lost and auto-reconnect disabled")
                        break
                
                # HEARTBEAT LOGIC: Keep Arduino watchdog happy (prevent auto-shutdown)
                # Send a valid JSON keepalive command instead of just newline to ensure Arduino processes it
                if time.time() - self.last_write_time > self.heartbeat_interval:
                    try:
                        if self.serial_conn and self.serial_conn.is_open:
                            # Send a no-op keepalive command that Arduino will process (updates watchdog)
                            keepalive_cmd = '{"keepalive":true}\n'.encode('utf-8')
                            self.serial_conn.write(keepalive_cmd)
                            self.last_write_time = time.time()
                            logger.debug("[SERIAL] ❤️  Sent keepalive to prevent watchdog timeout (60s)")
                    except Exception as hb_err:
                        logger.warning(f"[SERIAL] Heartbeat failed: {hb_err}")
                        self.is_connected = False  # Mark as disconnected to trigger reconnect

                # BUFFER MANAGEMENT: extensive buffer indicates lag
                try:
                    if self.serial_conn.in_waiting > 1024:
                        logger.warning(f"[SERIAL] Buffer overflow ({self.serial_conn.in_waiting} bytes). Flushing to prevent lag.")
                        self.serial_conn.reset_input_buffer()
                except:
                    pass

                # Read data from Arduino
                line = self.read_line()
                
                # If read_line returned None but we think we're connected, check again
                if line is None and not self.is_connected:
                    # Connection was lost in read_line, loop will retry
                    continue
                
                if line:
                    # Reset failure counter on successful read
                    consecutive_failures = 0
                    
                    # Try to parse as JSON sensor data
                    data = self.parse_sensor_data(line)
                    
                    if data and self.data_callback:
                        self.data_callback(data)
                
                # Small delay to prevent CPU spinning
                time.sleep(0.1)
                
            except (serial.SerialException, OSError, IOError) as e:
                logger.error(f"[SERIAL] Serial I/O error: {e}")
                self.is_connected = False
                consecutive_failures += 1
                
                # Clean up dead connection
                if self.serial_conn:
                    try:
                        self.serial_conn.close()
                    except:
                        pass
                    self.serial_conn = None
                
                # Back off if too many failures
                if consecutive_failures >= max_consecutive_failures:
                    logger.warning(f"[SERIAL] Too many failures ({consecutive_failures}), backing off...")
                    time.sleep(self.reconnect_interval * 2)
                    consecutive_failures = 0  # Reset after backoff
                else:
                    time.sleep(self.reconnect_interval)
                    
            except Exception as e:
                logger.error(f"[SERIAL] Unexpected error in listen loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)
        
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
        Sends JSON command to Arduino.
        
        Args:
            room: 'fruiting', 'spawning', or 'device'
            actuator_type: 'exhaust_fan', 'mist_maker', 'led', etc.
            state: 'ON' or 'OFF'
        
        Returns:
            True if command sent successfully
            
        Example:
            control_actuator('fruiting', 'exhaust_fan', 'ON')
            -> Sends '{"actuator": "FRUITING_EXHAUST_FAN", "state": "ON"}\n' to Arduino
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
        
        # Send JSON command
        json_cmd = json.dumps({"actuator": actuator_name, "state": state})
        
        return self.send_command(json_cmd)
    
    def get_latest_data(self) -> Dict[str, Any]:
        """Get the most recent sensor data received from Arduino."""
        return self.latest_data.copy()
    
    def get_fruiting_room_data(self) -> Optional[Dict[str, float]]:
        """
        Get latest fruiting room sensor data.
        
        Returns:
            {'temp': 23.5, 'humidity': 85.0, 'co2': 800} or None
        """
        return self.latest_data.get('fruiting')
    
    def get_spawning_room_data(self) -> Optional[Dict[str, float]]:
        """
        Get latest spawning room sensor data.
        
        Returns:
            {'temp': 24.0, 'humidity': 90.0, 'co2': 1200} or None
        """
        return self.latest_data.get('spawning')
    
    def is_arduino_connected(self) -> bool:
        """Check if Arduino is currently connected."""
        return self.is_connected and self.serial_conn is not None and self.serial_conn.is_open


# ==================== CONVENIENCE FUNCTIONS ====================
def create_arduino_connection(port: str = '/dev/ttyACM0') -> ArduinoSerialComm:
    """Create and connect to Arduino."""
    comm = ArduinoSerialComm(port=port)
    comm.connect()
    return comm


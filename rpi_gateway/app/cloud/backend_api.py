# M.A.S.H. IoT - Backend API Client
# Handles communication with the MASH backend server (api.mashmarket.app)

import requests
import logging
import time
import os
import jwt
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackendAPIClient:
    """
    Client for communicating with the MASH backend server.
    Handles JWT authentication, sensor data uploads, device registration, and command retrieval.
    """
    
    def __init__(self, base_url: Optional[str] = None, device_email: Optional[str] = None, device_password: Optional[str] = None, device_config: Optional[Dict] = None):
        self.base_url = base_url or os.getenv('BACKEND_URL', 'https://api.mashmarket.app/api/v1')
        self.device_email = device_email or os.getenv('DEVICE_EMAIL', '')
        self.device_password = device_password or os.getenv('DEVICE_PASSWORD', '')
        
        # Load device ID from config or environment
        if device_config:
            self.device_id = device_config.get('id', os.getenv('DEVICE_ID', 'unknown'))
            self.device_name = device_config.get('name', os.getenv('DEVICE_NAME', 'MASH IoT Gateway'))
            self.serial_number = device_config.get('serial_number', '')
        else:
            self.device_id = os.getenv('DEVICE_ID', 'unknown')
            self.device_name = os.getenv('DEVICE_NAME', 'MASH IoT Gateway')
            self.serial_number = os.getenv('DEVICE_SERIAL', '')
        
        # Remove trailing slash from base URL
        self.base_url = self.base_url.rstrip('/')
        
        # JWT Token Management
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        # Connection state
        self.is_connected = False
        self.last_connection_check = 0
        self.connection_check_interval = 300  # Check every 5 minutes (300 seconds)
        
        logger.info(f"[BACKEND] Initialized client for {self.base_url}")
        
        # Attempt initial connection
        self._initial_connection_check()
    
    def _is_token_expired(self) -> bool:
        """Check if access token is expired or about to expire (within 5 min)."""
        if not self.token_expiry:
            return True
        return datetime.now() >= (self.token_expiry - timedelta(minutes=5))
    
    def _update_auth_header(self):
        """Update Authorization header with current access token."""
        if self.access_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })
    
    def _initial_connection_check(self):
        """Attempt initial connection to backend."""
        try:
            self.is_connected = self.check_connection()
            if self.is_connected:
                logger.info("[BACKEND] Initial connection successful")
            else:
                logger.warning("[BACKEND] Initial connection failed - will retry")
        except Exception as e:
            logger.warning(f"[BACKEND] Initial connection check failed: {e}")
            self.is_connected = False
    
    def authenticate(self) -> bool:
        """
        Authenticate with backend using device credentials and obtain JWT tokens.
        
        Returns:
            True if authentication successful, False otherwise
        """
        if not self.device_email or not self.device_password:
            logger.error("[BACKEND] Device credentials not configured")
            return False
        
        try:
            payload = {
                'email': self.device_email,
                'password': self.device_password
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('accessToken')
                self.refresh_token = data.get('refreshToken')
                
                # Decode JWT to get expiry (without verification for expiry check only)
                if self.access_token:
                    try:
                        decoded = jwt.decode(self.access_token, options={"verify_signature": False})
                        self.token_expiry = datetime.fromtimestamp(decoded.get('exp', 0))
                    except Exception:
                        # Default to 1 hour expiry if decode fails
                        self.token_expiry = datetime.now() + timedelta(hours=1)
                
                self._update_auth_header()
                logger.info(f"[BACKEND] Authentication successful, token expires at {self.token_expiry}")
                return True
            else:
                logger.error(f"[BACKEND] Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[BACKEND] Authentication error: {e}")
            return False
    
    def refresh_access_token(self) -> bool:
        """
        Refresh access token using refresh token.
        
        Returns:
            True if refresh successful, False otherwise
        """
        if not self.refresh_token:
            logger.warning("[BACKEND] No refresh token available, re-authenticating")
            return self.authenticate()
        
        try:
            payload = {
                'refreshToken': self.refresh_token
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/refresh",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('accessToken')
                
                # Update expiry
                if self.access_token:
                    try:
                        decoded = jwt.decode(self.access_token, options={"verify_signature": False})
                        self.token_expiry = datetime.fromtimestamp(decoded.get('exp', 0))
                    except Exception:
                        self.token_expiry = datetime.now() + timedelta(hours=1)
                
                self._update_auth_header()
                logger.info(f"[BACKEND] Token refreshed, expires at {self.token_expiry}")
                return True
            else:
                logger.warning(f"[BACKEND] Token refresh failed: {response.status_code}, re-authenticating")
                return self.authenticate()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[BACKEND] Token refresh error: {e}")
            return self.authenticate()
    
    def ensure_authenticated(self) -> bool:
        """
        Ensure valid authentication token is available.
        Automatically refreshes if expired.
        
        Returns:
            True if authenticated, False otherwise
        """
        if not self.access_token:
            return self.authenticate()
        
        if self._is_token_expired():
            return self.refresh_access_token()
        
        return True
    
    def check_connection(self) -> bool:
        """
        Check if backend is reachable and authenticated.
        Caches result to avoid excessive requests (uses connection_check_interval).
        """
        current_time = time.time()
        
        # Use cached result if checked recently
        if current_time - self.last_connection_check < self.connection_check_interval:
            return self.is_connected
        
        try:
            # Use device heartbeat endpoint for proper tracking
            if not self.ensure_authenticated():
                logger.warning("[BACKEND] Authentication failed, cannot send heartbeat")
                self.is_connected = False
                self.last_connection_check = current_time
                return False
            
            # Send heartbeat to device-specific endpoint
            response = self.session.post(
                f"{self.base_url}/devices/{self.device_id}/heartbeat",
                json={"status": "ONLINE", "timestamp": datetime.now().isoformat()},
                timeout=10
            )
            
            self.is_connected = response.status_code in [200, 201]
            self.last_connection_check = current_time
            
            if self.is_connected:
                logger.info(f"[BACKEND] Device heartbeat sent successfully")
            else:
                logger.warning(f"[BACKEND] Heartbeat failed: {response.status_code} - {response.text}")
            
            return self.is_connected
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"[BACKEND] Connection check failed: {e}")
            self.is_connected = False
            self.last_connection_check = current_time
            return False
    
    def verify_device(self) -> Dict[str, Any]:
        """
        Verify device exists in backend via serial number (no auth required).
        Used during initial activation to check if device is valid.
        
        Returns:
            dict with 'exists' boolean and device data if found
        """
        try:
            response = self.session.get(
                f"{self.base_url}/iot/devices/serial/{self.device_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                device_data = response.json()
                logger.info(f"[BACKEND] Device verified: {self.device_id}")
                return {'exists': True, 'device': device_data}
            elif response.status_code == 404:
                logger.error(f"[BACKEND] Device not found in registry: {self.device_id}")
                return {'exists': False, 'error': 'Device not registered in Admin panel'}
            else:
                logger.error(f"[BACKEND] Verification failed: {response.status_code}")
                return {'exists': False, 'error': f'Backend error: {response.status_code}'}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[BACKEND] Device verification error: {e}")
            return {'exists': False, 'error': str(e)}
    
    def activate_device(self, network_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Activate device by updating status to ONLINE (no auth required).
        Called once after WiFi setup on first boot.
        
        Args:
            network_info: Optional dict with ipAddress, macAddress, etc.
        
        Returns:
            True if activation successful
        """
        try:
            payload = {
                'status': 'ONLINE',
                'isActive': True,
                'lastSeen': datetime.now().isoformat()
            }
            
            # Add network info if provided
            if network_info:
                payload.update(network_info)
            
            response = self.session.patch(
                f"{self.base_url}/iot/devices/serial/{self.device_id}",
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"[BACKEND] Device activated: {self.device_id}")
                return True
            else:
                logger.error(f"[BACKEND] Activation failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[BACKEND] Device activation error: {e}")
            return False
    
    def register_device(self) -> bool:
        """
        Register/update device metadata with the backend (no auth for IoT devices).
        Used to sync device information.
        """
        try:
            payload = {
                'name': self.device_name,
                'type': 'MUSHROOM_CHAMBER',
                'serialNumber': self.device_id,
                'location': 'Mushroom Cultivation Facility',
                'firmware': '1.0.0',
                'status': 'ONLINE',
                'isActive': True
            }
            
            response = self.session.post(
                f"{self.base_url}/iot/devices",
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"[BACKEND] Device registered/updated: {self.device_id}")
                return True
            else:
                logger.warning(f"[BACKEND] Registration failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[BACKEND] Device registration error: {e}")
            return False
    
    def send_sensor_data(self, sensor_data: Dict[str, Any]) -> bool:
        """
        Upload sensor data to backend using the batch ingest endpoint.
        
        Args:
            sensor_data: Dictionary containing sensor readings
                         e.g., {"fruiting": {"temp": 24.5, "humidity": 85, "co2": 800}, "spawning": {...}, "timestamp": 1234567890}
        
        Returns:
            True if upload successful, False otherwise
        """
        if not self.check_connection():
            logger.debug("[BACKEND] Skipping upload - backend offline")
            return False
        
        if not self.ensure_authenticated():
            logger.error("[BACKEND] Cannot upload sensor data - authentication failed")
            return False
        
        try:
            timestamp = sensor_data.get('timestamp', time.time())
            timestamp_iso = datetime.fromtimestamp(timestamp).isoformat()
            
            success = True
            
            # Process each room's sensor data
            for room, readings in sensor_data.items():
                if room == 'timestamp':
                    continue
                
                if not isinstance(readings, dict):
                    continue
                
                # Send individual sensor readings using POST /sensors/:id/data
                # Note: You'll need to map room+sensor_type to actual sensor IDs
                # For now, using a device-level endpoint pattern
                
                for sensor_type, value in readings.items():
                    if sensor_type in ['temp', 'humidity', 'co2'] and not isinstance(value, str):
                        # Map sensor types to backend sensor IDs
                        # This assumes sensors are pre-created and mapped
                        sensor_id = self._get_sensor_id(room, sensor_type)
                        
                        if sensor_id:
                            ingest_payload = {
                                'value': value,
                                'timestamp': timestamp_iso,
                                'metadata': {
                                    'room': room,
                                    'deviceId': self.device_id
                                }
                            }
                            
                            response = self.session.post(
                                f"{self.base_url}/sensors/{sensor_id}/data",
                                json=ingest_payload,
                                timeout=10
                            )
                            
                            if response.status_code not in [200, 201]:
                                logger.warning(f"[BACKEND] Upload failed for {room}/{sensor_type}: {response.status_code}")
                                success = False
            
            if success:
                logger.debug(f"[BACKEND] Sensor data uploaded")
            return success
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[BACKEND] Upload error: {e}")
            return False
    
    def send_sensor_batch(self, sensor_id: str, readings: List[Dict[str, Any]]) -> bool:
        """
        Send batch sensor data for a specific sensor using POST /sensors/:id/data/batch.
        
        Args:
            sensor_id: The sensor ID
            readings: List of reading dicts with 'value', 'timestamp', 'metadata'
        
        Returns:
            True if successful
        """
        if not self.ensure_authenticated():
            return False
        
        try:
            payload = {
                'data': readings
            }
            
            response = self.session.post(
                f"{self.base_url}/sensors/{sensor_id}/data/batch",
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.debug(f"[BACKEND] Batch uploaded for sensor {sensor_id}")
                return True
            else:
                logger.warning(f"[BACKEND] Batch upload failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[BACKEND] Batch upload error: {e}")
            return False
    
    def get_sensor_data(self, sensor_id: str, start_date: Optional[str] = None, 
                        end_date: Optional[str] = None, limit: int = 100) -> Optional[List[Dict]]:
        """
        Fetch sensor data from backend using GET /sensors/:id/data.
        
        Args:
            sensor_id: The sensor ID
            start_date: Optional ISO date string
            end_date: Optional ISO date string
            limit: Maximum records to fetch
        
        Returns:
            List of sensor readings or None
        """
        if not self.ensure_authenticated():
            return None
        
        try:
            params = {'limit': limit}
            if start_date:
                params['startDate'] = start_date
            if end_date:
                params['endDate'] = end_date
            
            response = self.session.get(
                f"{self.base_url}/sensors/{sensor_id}/data",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('data', [])
            else:
                logger.warning(f"[BACKEND] Sensor data fetch failed: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[BACKEND] Sensor data fetch error: {e}")
            return None
    
    def get_device_sensors(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch all sensors associated with this device using GET /devices/:id/sensors.
        
        Returns:
            List of sensor objects or None
        """
        if not self.ensure_authenticated():
            return None
        
        try:
            response = self.session.get(
                f"{self.base_url}/devices/{self.device_id}/sensors",
                timeout=10
            )
            
            if response.status_code == 200:
                sensors = response.json()
                logger.info(f"[BACKEND] Fetched {len(sensors)} sensors for device")
                return sensors
            else:
                logger.warning(f"[BACKEND] Sensor list fetch failed: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[BACKEND] Sensor list fetch error: {e}")
            return None
    
    def _get_sensor_id(self, room: str, sensor_type: str) -> Optional[str]:
        """
        Map room and sensor type to backend sensor ID.
        Uses local database cache for performance.
        
        Args:
            room: 'fruiting' or 'spawning'
            sensor_type: 'temp', 'humidity', or 'co2'
        
        Returns:
            Backend sensor ID or None
        """
        try:
            from ..database.db_manager import DatabaseManager
            db = DatabaseManager()
            db.connect()
            sensor_id = db.get_sensor_mapping(room, sensor_type)
            db.disconnect()
            
            if sensor_id:
                return sensor_id
            else:
                logger.debug(f"[BACKEND] No mapping found for {room}/{sensor_type}")
                return None
                
        except Exception as e:
            logger.error(f"[BACKEND] Sensor mapping lookup error: {e}")
            return None
    
    def sync_sensor_mappings(self) -> bool:
        """
        Fetch device sensors from backend and update local mappings.
        Should be called after device activation or periodically.
        
        Returns:
            True if successful
        """
        sensors = self.get_device_sensors()
        
        if not sensors:
            logger.warning("[BACKEND] No sensors found for device")
            return False
        
        try:
            from ..database.db_manager import DatabaseManager
            db = DatabaseManager()
            db.connect()
            
            updated_count = 0
            
            for sensor in sensors:
                sensor_id = sensor.get('id')
                sensor_name = sensor.get('name', '')
                sensor_type_raw = sensor.get('type', '').lower()
                unit = sensor.get('unit', '')
                
                # Parse room and sensor type from sensor name or metadata
                # Expected naming: "Fruiting Room - Temperature" or use metadata
                room = None
                sensor_type = None
                
                if 'fruiting' in sensor_name.lower():
                    room = 'fruiting'
                elif 'spawning' in sensor_name.lower():
                    room = 'spawning'
                
                if 'temp' in sensor_type_raw or 'temperature' in sensor_name.lower():
                    sensor_type = 'temp'
                elif 'humid' in sensor_type_raw or 'humidity' in sensor_name.lower():
                    sensor_type = 'humidity'
                elif 'co2' in sensor_type_raw or 'co2' in sensor_name.lower():
                    sensor_type = 'co2'
                
                if room and sensor_type and sensor_id:
                    if db.set_sensor_mapping(room, sensor_type, sensor_id, sensor_name, unit):
                        updated_count += 1
                        logger.info(f"[BACKEND] Mapped {room}/{sensor_type} -> {sensor_id}")
            
            db.disconnect()
            logger.info(f"[BACKEND] Synced {updated_count} sensor mappings")
            return updated_count > 0
            
        except Exception as e:
            logger.error(f"[BACKEND] Sensor mapping sync error: {e}")
            return False
    
    def get_actuator_commands(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch pending actuator commands from backend.
        Allows remote control of devices.
        
        Returns:
            List of command dictionaries, or None if error/offline
            Example: [{"id": "cmd123", "command": "FAN_ON", "parameters": {...}}]
        """
        if not self.check_connection():
            return None
        
        if not self.ensure_authenticated():
            return None
        
        try:
            response = self.session.get(
                f"{self.base_url}/devices/{self.device_id}/commands",
                timeout=10
            )
            
            if response.status_code == 200:
                commands = response.json().get('commands', [])
                if commands:
                    logger.info(f"[BACKEND] Received {len(commands)} commands")
                return commands
            else:
                logger.warning(f"[BACKEND] Command fetch failed: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[BACKEND] Command fetch error: {e}")
            return None
    
    def acknowledge_command(self, command_id: str, success: bool, response_data: Optional[Dict] = None) -> bool:
        """
        Acknowledge execution of a command.
        
        Args:
            command_id: ID of the command to acknowledge
            success: Whether command execution was successful
            response_data: Optional execution result data
        
        Returns:
            True if acknowledgment sent successfully
        """
        if not self.ensure_authenticated():
            return False
        
        try:
            payload = {
                'status': 'completed' if success else 'failed',
                'response': response_data,
                'acknowledgedAt': datetime.now().isoformat()
            }
            
            response = self.session.put(
                f"{self.base_url}/devices/{self.device_id}/commands/{command_id}",
                json=payload,
                timeout=10
            )
            
            return response.status_code in [200, 201]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[BACKEND] Command acknowledgment error: {e}")
            return False
    
    def send_alert(self, alert_type: str, message: str, severity: str = "WARNING", device_data: Optional[Dict] = None) -> bool:
        """
        Send an alert/notification to backend.
        
        Args:
            alert_type: Type of alert (e.g., 'high_co2', 'sensor_error')
            message: Human-readable alert message
            severity: 'INFO', 'WARNING', 'CRITICAL'
            device_data: Optional device-related data
        
        Returns:
            True if alert sent successfully
        """
        if not self.ensure_authenticated():
            return False
        
        try:
            payload = {
                'type': alert_type,
                'severity': severity.lower(),
                'title': f"{self.device_name} Alert",
                'message': message,
                'deviceId': self.device_id,
                'metadata': device_data,
                'triggeredAt': datetime.now().isoformat()
            }
            
            response = self.session.post(
                f"{self.base_url}/alerts/trigger",
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"[BACKEND] Alert sent: {alert_type}")
                return True
            else:
                logger.warning(f"[BACKEND] Alert send failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[BACKEND] Alert send error: {e}")
            return False
    
    def update_device_status(self, status: str, health_data: Optional[Dict] = None) -> bool:
        """
        Update device status and health metrics using IoT endpoint (no auth required).
        
        Args:
            status: Device status ('ONLINE', 'OFFLINE', 'ERROR', 'MAINTENANCE')
            health_data: Optional health metrics (CPU, memory, temperature, etc.)
        
        Returns:
            True if update successful
        """
        try:
            payload = {
                'status': status,
                'lastSeen': datetime.now().isoformat()
            }
            
            # Add health data to payload if provided
            if health_data:
                payload.update(health_data)
            
            response = self.session.patch(
                f"{self.base_url}/iot/devices/serial/{self.device_id}",
                json=payload,
                timeout=10
            )
            
            return response.status_code in [200, 201]
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[BACKEND] Status update error: {e}")
            return False
    
    def send_device_health(self, health_metrics: Dict[str, Any]) -> bool:
        """
        Send device health metrics to backend.
        
        Args:
            health_metrics: Dict with cpuUsage, memoryUsage, temperature, diskUsage, etc.
        
        Returns:
            True if successful
        """
        if not self.ensure_authenticated():
            return False
        
        try:
            payload = {
                'timestamp': datetime.now().isoformat(),
                **health_metrics
            }
            
            response = self.session.post(
                f"{self.base_url}/devices/{self.device_id}/health",
                json=payload,
                timeout=10
            )
            
            return response.status_code in [200, 201]
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[BACKEND] Health metrics send error: {e}")
            return False
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        """
        Fetch configuration from backend.
        Allows remote configuration updates.
        
        Returns:
            Configuration dictionary or None if error/offline
        """
        if not self.ensure_authenticated():
            return None
        
        try:
            response = self.session.get(
                f"{self.base_url}/devices/{self.device_id}/config",
                timeout=10
            )
            
            if response.status_code == 200:
                config = response.json()
                logger.info("[BACKEND] Configuration fetched")
                return config
            else:
                logger.warning(f"[BACKEND] Config fetch failed: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[BACKEND] Config fetch error: {e}")
            return None
    
    def logout(self) -> bool:
        """Logout and invalidate tokens."""
        if not self.access_token:
            return True
        
        try:
            self.session.post(f"{self.base_url}/auth/logout", timeout=5)
        except Exception:
            pass
        
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.session.headers.pop('Authorization', None)
        logger.info("[BACKEND] Logged out")
        return True
    
    def close(self):
        """Close the session."""
        self.logout()
        self.session.close()
        logger.info("[BACKEND] Session closed")


# ==================== CONVENIENCE FUNCTION ====================
def create_backend_client() -> BackendAPIClient:
    """Create and return a configured backend API client."""
    return BackendAPIClient()

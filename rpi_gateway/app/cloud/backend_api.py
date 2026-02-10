# M.A.S.H. IoT - Backend API Client (Device Token Support)
# Handles communication with the MASH backend server

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
    Supports both Email/Password login AND Static Device Tokens.
    """
    
    def __init__(self, base_url: Optional[str] = None, device_email: Optional[str] = None, device_password: Optional[str] = None, device_config: Optional[Dict] = None):
        self.base_url = base_url or os.getenv('BACKEND_URL', 'https://api.mashmarket.app/api/v1')
        
        # 1. Try to load Device Credentials
        self.device_email = device_email or os.getenv('DEVICE_EMAIL', '')
        self.device_password = device_password or os.getenv('DEVICE_PASSWORD', '')
        
        # 2. Try to load Static Access Token (Preferred for IoT)
        self.access_token = os.getenv('ACCESS_TOKEN')
        self.is_static_token = bool(self.access_token)
        self.refresh_token = None
        self.token_expiry = None

        # Load device ID
        if device_config:
            self.device_id = device_config.get('id', os.getenv('DEVICE_ID', 'unknown'))
            self.device_name = device_config.get('name', os.getenv('DEVICE_NAME', 'MASH IoT Gateway'))
            self.serial_number = device_config.get('serial_number', '')
        else:
            self.device_id = os.getenv('DEVICE_ID', 'unknown')
            self.device_name = os.getenv('DEVICE_NAME', 'MASH IoT Gateway')
            self.serial_number = os.getenv('DEVICE_SERIAL', '')
        
        self.base_url = self.base_url.rstrip('/')
        
        # Session Setup
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        # Connection state
        self.is_connected = False
        self.last_connection_check = 0
        self.connection_check_interval = 300
        
        # Exponential backoff state for failed connections
        self.retry_count = 0
        self.last_failed_attempt = 0
        self.retry_intervals = [10, 30, 60, 300, 600]  # 10s, 30s, 1min, 5min, 10min (max)
        self.max_retry_delay = 600  # 10 minutes maximum
        
        logger.info(f"[BACKEND] Initialized client for {self.base_url}")
        
        # 3. If we have a static token, set up headers immediately
        if self.is_static_token:
            self._decode_and_set_token(self.access_token)
            logger.info("[BACKEND] Running in Static Token Mode (Login skipped)")
        
        # Attempt initial connection
        self._initial_connection_check()

    def _decode_and_set_token(self, token: str):
        """Helper to decode token expiry and update headers"""
        self.access_token = token
        self._update_auth_header()
        
        try:
            # Decode without verification just to read the 'exp' claim
            decoded = jwt.decode(token, options={"verify_signature": False})
            exp_timestamp = decoded.get('exp', 0)
            
            if exp_timestamp:
                self.token_expiry = datetime.fromtimestamp(exp_timestamp)
                logger.info(f"[BACKEND] Token valid until: {self.token_expiry}")
            else:
                # No expiry in token? Assume infinite/long-lived
                self.token_expiry = datetime.now() + timedelta(days=3650)
                
        except Exception as e:
            logger.warning(f"[BACKEND] Could not decode token expiry: {e}")
            self.token_expiry = datetime.now() + timedelta(hours=1)

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
        Authenticate with backend. 
        Prioritizes Static Token if present. Otherwise tries Email/Password.
        """
        # 1. Static Token Mode
        if self.is_static_token:
            if self._is_token_expired():
                logger.error("[BACKEND] CRITICAL: Static Access Token has expired!")
                logger.error("[BACKEND] Please update ACCESS_TOKEN in .env file")
                return False
            return True

        # 2. Email/Password Mode
        if not self.device_email or not self.device_password:
            # Only complain if we don't have a static token either
            if not self.is_static_token:
                logger.error("[BACKEND] No credentials found (Set ACCESS_TOKEN or EMAIL/PASSWORD)")
            return False
        
        try:
            payload = {
                'email': self.device_email,
                'password': self.device_password
            }
            
            logger.info(f"[BACKEND] Attempting authentication for: {self.device_email}")
            
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('accessToken')
                self.refresh_token = data.get('refreshToken')
                
                if not token:
                    logger.error("[BACKEND] Authentication response missing accessToken")
                    return False
                
                self._decode_and_set_token(token)
                logger.info(f"[BACKEND] ✓ Authentication successful")
                return True
            else:
                logger.error(f"[BACKEND] Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[BACKEND] Authentication error: {e}")
            return False
    
    def refresh_access_token(self) -> bool:
        """
        Refresh access token.
        If using Static Token, we cannot refresh (user must update .env).
        """
        if self.is_static_token:
            logger.warning("[BACKEND] Cannot refresh Static Token. Please update .env if expired.")
            return False

        if not self.refresh_token:
            logger.warning("[BACKEND] No refresh token available, re-authenticating")
            return self.authenticate()
        
        try:
            payload = {'refreshToken': self.refresh_token}
            response = self.session.post(
                f"{self.base_url}/auth/refresh",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('accessToken')
                self._decode_and_set_token(token)
                logger.info(f"[BACKEND] Token refreshed")
                return True
            else:
                logger.warning(f"[BACKEND] Token refresh failed: {response.status_code}, re-authenticating")
                return self.authenticate()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[BACKEND] Token refresh error: {e}")
            return self.authenticate()
            
    def ensure_authenticated(self) -> bool:
        """Ensure valid authentication token is available."""
        if not self.access_token:
            return self.authenticate()
        
        if self._is_token_expired():
            return self.refresh_access_token()
        
        return True
    
    # ... [The rest of the methods (check_connection, send_sensor_data, etc.) remain exactly the same] ...
    
    def _calculate_retry_delay(self) -> int:
        """Calculate backoff delay based on retry count."""
        if self.retry_count == 0:
            return 0
        
        # Get delay from intervals list, or use max delay if exceeded
        index = min(self.retry_count - 1, len(self.retry_intervals) - 1)
        return self.retry_intervals[index]
    
    def _reset_retry_state(self):
        """Reset retry state after successful connection."""
        if self.retry_count > 0:
            logger.info(f"[BACKEND] Connection successful, resetting retry state (was at retry {self.retry_count})")
        self.retry_count = 0
        self.last_failed_attempt = 0
    
    def _handle_connection_failure(self, current_time: float):
        """Handle connection failure and update retry state."""
        self.retry_count += 1
        self.last_failed_attempt = current_time
        next_delay = self._calculate_retry_delay()
        logger.warning(
            f"[BACKEND] Connection failed (retry {self.retry_count}/{len(self.retry_intervals)}), "
            f"backing off for {next_delay}s"
        )
    
    def _is_in_backoff_period(self, current_time: float) -> bool:
        """Check if we're still in backoff period after a failure."""
        if self.retry_count == 0 or self.last_failed_attempt == 0:
            return False
        
        retry_delay = self._calculate_retry_delay()
        time_since_failure = current_time - self.last_failed_attempt
        
        return time_since_failure < retry_delay
    
    def _get_next_retry_seconds(self, current_time: float) -> int:
        """Get seconds until next retry attempt."""
        if not self._is_in_backoff_period(current_time):
            return 0
        
        retry_delay = self._calculate_retry_delay()
        time_since_failure = current_time - self.last_failed_attempt
        return int(retry_delay - time_since_failure)
    
    def check_connection(self) -> bool:
        current_time = time.time()
        
        # If in backoff period, don't attempt connection
        if self._is_in_backoff_period(current_time):
            next_retry = self._get_next_retry_seconds(current_time)
            logger.debug(f"[BACKEND] In backoff period, next retry in {next_retry}s")
            return self.is_connected
        
        # If successfully connected recently, check per interval
        if self.is_connected and (current_time - self.last_connection_check < self.connection_check_interval):
            return True
        
        try:
            if not self.ensure_authenticated():
                self._handle_connection_failure(current_time)
                self.is_connected = False
                return False
            
            response = self.session.patch(
                f"{self.base_url}/iot/devices/serial/{self.serial_number}",
                json={"status": "ONLINE", "lastSeen": datetime.now().isoformat()},
                timeout=10
            )
            
            success = response.status_code in [200, 201]
            
            if success:
                self.last_connection_check = current_time
                logger.info(f"[BACKEND] Device heartbeat sent successfully")
                self._reset_retry_state()
                self.is_connected = True
            else:
                logger.warning(f"[BACKEND] Heartbeat failed: {response.status_code}")
                self._handle_connection_failure(current_time)
                self.is_connected = False
                
                # Fallback registration logic
                if response.status_code == 404:
                    self.register_device()

            return self.is_connected
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"[BACKEND] Connection check failed: {e}")
            self._handle_connection_failure(current_time)
            self.is_connected = False
            return False

    def register_device(self) -> bool:
        try:
            payload = {
                'name': self.device_name,
                'type': 'MUSHROOM_CHAMBER',
                'serialNumber': self.device_id, # Using device_id as serial for consistency based on your config
                'location': 'Mushroom Cultivation Facility',
                'status': 'ONLINE'
            }
            response = self.session.post(f"{self.base_url}/iot/devices", json=payload, timeout=10)
            if response.status_code in [200, 201]:
                logger.info(f"[BACKEND] Device registered: {self.device_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"[BACKEND] Registration error: {e}")
            return False

    # (Include other methods like send_sensor_data, get_config, etc. from original file here)
    # They don't need changes, just ensuring the class structure is maintained.
    
    def send_sensor_data(self, sensor_data: Dict[str, Any]) -> bool:
        """
        Send sensor data to backend via device status update.
        
        The backend's sensor ingestion requires individual sensor IDs (POST /sensors/:id/data),
        which adds complexity. Instead, we use the device update endpoint to attach
        latest sensor readings as metadata, and rely on Firebase as the primary
        real-time data channel for the mobile app.
        
        Args:
            sensor_data: Dict with 'fruiting' and/or 'spawning' room data
                         e.g. {'fruiting': {'temp': 23.5, 'humidity': 85, 'co2': 800}, ...}
        
        Returns:
            True if successful
        """
        if not self.ensure_authenticated():
            return False
        
        try:
            # Update device with latest sensor readings via PATCH endpoint
            payload = {
                "status": "ONLINE",
                "lastSeen": datetime.now().isoformat(),
                "metadata": {
                    "latestReadings": {
                        "fruiting": sensor_data.get('fruiting', {}),
                        "spawning": sensor_data.get('spawning', {}),
                        "timestamp": sensor_data.get('timestamp', datetime.now().isoformat())
                    }
                }
            }
            
            response = self.session.patch(
                f"{self.base_url}/iot/devices/serial/{self.serial_number}",
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.debug(f"[BACKEND] Sensor data sent successfully")
                return True
            else:
                logger.warning(f"[BACKEND] Sensor data send failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"[BACKEND] Sensor data send error: {e}")
            return False

    def close(self):
        self.session.close()

# Convenience function
def create_backend_client() -> BackendAPIClient:
    return BackendAPIClient()
"""M.A.S.H. IoT - Firebase Cloud Sync
Implements offline-first pattern: SQLite -> Firebase Realtime Database
"""

import os
import time
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime

try:
    import firebase_admin
    from firebase_admin import credentials, db as firebase_db
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logging.warning("firebase-admin not installed")

logger = logging.getLogger(__name__)


class FirebaseSync:
    """
    Handles cloud synchronization with Firebase Realtime Database.
    Pattern: Local SQLite (primary) -> Firebase (backup/analytics)
    """
    
    def __init__(self, config_path: str = "config/firebase_config.json", db_url: Optional[str] = None):
        self.config_path = config_path
        self.db_url = db_url
        self.is_initialized = False
        self.firebase_app = None
        
        if FIREBASE_AVAILABLE:
            self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK with service account."""
        try:
            # Check if already initialized
            if firebase_admin._apps:
                self.firebase_app = firebase_admin.get_app()
                self.is_initialized = True
                logger.info("[FIREBASE] Using existing Firebase app")
                return
            
            # Load service account credentials
            full_path = os.path.join(os.path.dirname(__file__), '..', '..', self.config_path)
            
            if not os.path.exists(full_path):
                logger.warning(f"[FIREBASE] Config not found: {full_path}")
                return
            
            cred = credentials.Certificate(full_path)
            
            # Initialize app
            if self.db_url:
                self.firebase_app = firebase_admin.initialize_app(cred, {
                    'databaseURL': self.db_url
                })
            else:
                self.firebase_app = firebase_admin.initialize_app(cred)
            
            self.is_initialized = True
            logger.info("[FIREBASE] Initialized successfully")
            
        except Exception as e:
            logger.error(f"[FIREBASE] Initialization failed: {e}")
            self.is_initialized = False
    
    def sync_sensor_readings(self, readings: List[Dict], device_id: str) -> int:
        """
        Deprecated. The live sensor readings are now written to devices/{device_id}/latest_reading.
        Historical data is handled exclusively by the sensor_aggregator bucket mechanism.
        This method is kept as a no-op to avoid breaking backward compatibility.
        """
        return len(readings)
    
    def sync_device_status(self, device_id: str, status: str, metadata: Optional[Dict] = None) -> bool:
        """
        Update device status in Firebase.
        
        Args:
            device_id: Device identifier
            status: Device status (ONLINE, OFFLINE, ERROR)
            metadata: Optional additional status information
        
        Returns:
            True if successful
        """
        if not self.is_initialized or not FIREBASE_AVAILABLE:
            return False
        
        try:
            ref = firebase_db.reference(f'devices/{device_id}/status')
            
            ref.set({
                'status': status,
                'last_update': datetime.now().isoformat(),
                'metadata': metadata or {}
            })
            
            logger.debug(f"[FIREBASE] Device status updated: {status}")
            return True
            
        except Exception as e:
            logger.error(f"[FIREBASE] Status update failed: {e}")
            return False
    
    def sync_actuator_states(self, device_id: str, actuator_states: Dict) -> bool:
        """
        Upload actuator states to Firebase for real-time mobile app sync.
        
        Args:
            device_id: Device identifier
            actuator_states: Dictionary of actuator states by room
                Format: {'fruiting': {'mist_maker': True, ...}, 'spawning': {...}}
        
        Returns:
            True if successful
        """
        if not self.is_initialized or not FIREBASE_AVAILABLE:
            return False
        
        try:
            # Update latest_actuators path for quick access
            ref = firebase_db.reference(f'devices/{device_id}/latest_actuators')
            
            # Prepare data with timestamp
            actuator_data = {
                'timestamp': datetime.now().isoformat(),
                'fruiting': actuator_states.get('fruiting', {}),
                'spawning': actuator_states.get('spawning', {}),
                'device': actuator_states.get('device', {})
            }
            
            # Set to Firebase
            ref.set(actuator_data)
            logger.debug(f"[FIREBASE] Uploaded actuator states to devices/{device_id}/latest_actuators")
            return True
            
        except Exception as e:
            logger.error(f"[FIREBASE] Actuator sync failed: {e}")
            return False
    
    def log_actuator_event(self, device_id: str, room: str, actuator: str, state: bool, mode: str = 'auto') -> bool:
        """
        Log actuator state change event to Firebase for historical tracking.
        
        Args:
            device_id: Device identifier
            room: Room name (fruiting, spawning, device)
            actuator: Actuator name (mist_maker, exhaust_fan, etc.)
            state: New state (True = ON, False = OFF)
            mode: Control mode ('auto' or 'manual')
        
        Returns:
            True if successful
        """
        if not self.is_initialized or not FIREBASE_AVAILABLE:
            return False
        
        try:
            # Create timestamp key for Firebase
            timestamp = datetime.now()
            timestamp_key = timestamp.isoformat().replace(':', '-').replace('.', '-')
            
            # Path: actuator_logs/{device_id}/{timestamp_key}
            ref = firebase_db.reference(f'actuator_logs/{device_id}/{timestamp_key}')
            
            # Log event
            ref.set({
                'room': room,
                'actuator': actuator,
                'state': 'ON' if state else 'OFF',
                'mode': mode,
                'timestamp': timestamp.isoformat(),
                'timestamp_unix': int(timestamp.timestamp())
            })
            
            logger.debug(f"[FIREBASE] Logged actuator event: {room}/{actuator} = {state} ({mode})")
            return True
            
        except Exception as e:
            logger.error(f"[FIREBASE] Actuator event logging failed: {e}")
            return False

    def sync_active_alert(self, device_id: str, room: str, alert_type: str, message: str, severity: str = 'WARNING') -> bool:
        """
        Sync an active alert to Firebase so connected clients can render it in real time.

        Alerts are written to alerts/{device_id}/{room}_{alert_type} to match the mobile
        alert listener path and keep the latest alert state visible.
        """
        if not self.is_initialized or not FIREBASE_AVAILABLE:
            return False

        try:
            alert_key = f'{room}_{alert_type}'
            ref = firebase_db.reference(f'alerts/{device_id}/{alert_key}')

            now = datetime.now()
            ref.set({
                'id': alert_key,
                'room': room,
                'alert_type': alert_type,
                'severity': severity,
                'message': message,
                'is_acknowledged': False,
                'active': True,
                'timestamp': now.isoformat(),
                'timestamp_unix': int(now.timestamp()),
                'updated_at': now.isoformat(),
            })

            logger.debug(f"[FIREBASE] Synced active alert: alerts/{device_id}/{alert_key}")
            return True

        except Exception as e:
            logger.error(f"[FIREBASE] Active alert sync failed: {e}")
            return False

    def remove_active_alert(self, device_id: str, room: str, alert_type: str) -> bool:
        """Remove an active alert from Firebase once the condition resolves."""
        if not self.is_initialized or not FIREBASE_AVAILABLE:
            return False

        try:
            alert_key = f'{room}_{alert_type}'
            firebase_db.reference(f'alerts/{device_id}/{alert_key}').delete()
            logger.debug(f"[FIREBASE] Removed active alert: alerts/{device_id}/{alert_key}")
            return True

        except Exception as e:
            logger.error(f"[FIREBASE] Active alert removal failed: {e}")
            return False

    def log_alert_notification(
        self,
        device_id: str,
        room: str,
        alert_type: str,
        message: str,
        severity: str = 'WARNING',
        active: bool = True,
    ) -> bool:
        """Write a notification history entry for a newly raised or resolved alert."""
        if not self.is_initialized or not FIREBASE_AVAILABLE:
            return False

        try:
            now = datetime.now()
            timestamp_key = now.isoformat().replace(':', '-').replace('.', '-')
            event_type = 'alert_raised' if active else 'alert_resolved'

            ref = firebase_db.reference(f'notifications/{device_id}/{timestamp_key}')
            ref.set({
                'id': timestamp_key,
                'device_id': device_id,
                'room': room,
                'alert_type': alert_type,
                'severity': severity,
                'message': message,
                'event_type': event_type,
                'active': active,
                'read': False,
                'timestamp': now.isoformat(),
                'timestamp_unix': int(now.timestamp()),
            })

            logger.debug(f"[FIREBASE] Logged alert notification: notifications/{device_id}/{timestamp_key}")
            return True

        except Exception as e:
            logger.error(f"[FIREBASE] Alert notification logging failed: {e}")
            return False
    
    def push_hourly_aggregate(
        self,
        device_id: str,
        room: str,
        year_month: str,
        day: str,
        hour_key: str,
        data: Dict,
    ) -> bool:
        """
        Write a completed hourly aggregate bucket.
        Path: historical_aggregates/{device_id}/{room}/{YYYY-MM}/{DD}/{HH:00}
        Called by SensorAggregator when the UTC hour rolls over.
        """
        if not self.is_initialized or not FIREBASE_AVAILABLE:
            return False
        path = f'historical_aggregates/{device_id}/{room}/{year_month}/{day}/{hour_key}'
        try:
            firebase_db.reference(path).set(data)
            logger.debug(f"[FIREBASE] Pushed aggregate: {path}")
            return True
        except Exception as e:
            logger.error(f"[FIREBASE] aggregate push failed ({path}): {e}")
            return False

    def get_device_config(self, device_id: str) -> Optional[Dict]:
        """
        Fetch device configuration from Firebase.
        
        Args:
            device_id: Device identifier
        
        Returns:
            Configuration dictionary or None
        """
        if not self.is_initialized or not FIREBASE_AVAILABLE:
            return None
        
        try:
            ref = firebase_db.reference(f'devices/{device_id}/config')
            config = ref.get()
            
            if config:
                logger.info("[FIREBASE] Device config fetched")
            
            return config
            
        except Exception as e:
            logger.error(f"[FIREBASE] Config fetch failed: {e}")
            return None


def create_firebase_sync(config_path: str = "config/firebase_config.json", db_url: Optional[str] = None) -> FirebaseSync:
    """Factory function to create FirebaseSync instance."""
    return FirebaseSync(config_path=config_path, db_url=db_url)


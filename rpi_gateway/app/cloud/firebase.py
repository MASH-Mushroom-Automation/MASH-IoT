"""M.A.S.H. IoT - Firebase Cloud Sync
Implements offline-first pattern: SQLite -> Firebase Realtime Database
"""

import os
import logging
import json
from typing import List, Dict
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
    
    def __init__(self, config_path: str = "config/firebase_config.json", db_url: str = None):
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
    
    def sync_sensor_readings(self, readings: List[Dict]) -> int:
        """
        Upload sensor readings to Firebase.
        
        Args:
            readings: List of sensor data dicts
        
        Returns:
            Number of successfully synced records
        """
        if not self.is_initialized or not FIREBASE_AVAILABLE:
            logger.warning("[FIREBASE] Not initialized, skipping sync")
            return 0
        
        synced_count = 0
        
        try:
            ref = firebase_db.reference('sensor_data')
            
            for reading in readings:
                try:
                    timestamp_key = reading.get('timestamp', datetime.now().isoformat()).replace(':', '-').replace('.', '-')
                    room = reading.get('room', 'unknown')
                    
                    room_ref = ref.child(room).child(timestamp_key)
                    
                    room_ref.set({
                        'temperature': reading.get('temp'),
                        'humidity': reading.get('humidity'),
                        'co2': reading.get('co2'),
                        'timestamp': reading.get('timestamp'),
                        'synced_at': datetime.now().isoformat()
                    })
                    
                    synced_count += 1
                    
                except Exception as e:
                    logger.error(f"[FIREBASE] Failed to sync reading {reading.get('id')}: {e}")
            
            logger.info(f"[FIREBASE] Synced {synced_count}/{len(readings)} readings")
            return synced_count
            
        except Exception as e:
            logger.error(f"[FIREBASE] Batch sync failed: {e}")
            return synced_count


def create_firebase_sync(config_path: str = "config/firebase_config.json") -> FirebaseSync:
    """Factory function to create FirebaseSync instance."""
    return FirebaseSync(config_path=config_path)

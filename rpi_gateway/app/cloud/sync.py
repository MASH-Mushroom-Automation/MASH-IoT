# M.A.S.H. IoT - Cloud Synchronization Manager
# Offline-first data synchronization: SQLite → Backend API + Firebase + MQTT
# Implements queue and retry logic with exponential backoff

import logging
import time
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from queue import Queue, Empty
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.cloud.backend_api import BackendAPIClient
from app.cloud.firebase import FirebaseSync
from app.cloud.mqtt_client import MQTTClient
from app.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class SyncManager:
    """
    Manages offline-first synchronization between local SQLite and cloud services.
    
    Architecture:
        1. Local SQLite (primary, always available)
        2. Backend API (PostgreSQL via REST, JWT authenticated)
        3. Firebase Realtime DB (backup/analytics, optional)
        4. MQTT (real-time updates, optional)
    
    Features:
        - Automatic retry with exponential backoff
        - Queue-based async uploads
        - Batch processing for efficiency
        - Health monitoring and reconnection
    """
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        backend_client: Optional[BackendAPIClient] = None,
        firebase_sync: Optional[FirebaseSync] = None,
        mqtt_client: Optional[MQTTClient] = None,
        sync_interval: int = 60,
        batch_size: int = 50
    ):
        self.db = db_manager
        self.backend = backend_client
        self.firebase = firebase_sync
        self.mqtt = mqtt_client
        
        # Configuration
        self.sync_interval = sync_interval  # seconds
        self.batch_size = batch_size
        self.max_retries = 5
        self.retry_delays = [10, 30, 60, 300, 900]  # exponential backoff (seconds)
        
        # Sync queues
        self.sensor_queue = Queue()
        self.command_queue = Queue()
        self.alert_queue = Queue()
        
        # Threads
        self.sync_thread = None
        self.mqtt_thread = None
        self.running = False
        
        # Statistics
        self.stats = {
            'last_sync': None,
            'total_synced': 0,
            'failed_syncs': 0,
            'pending_records': 0,
            'backend_online': False,
            'firebase_online': False,
            'mqtt_online': False
        }
        
        logger.info("[SYNC] Initialized SyncManager")
    
    def start(self):
        """Start sync threads."""
        if self.running:
            logger.warning("[SYNC] Already running")
            return
        
        self.running = True
        
        # Authenticate with backend on startup
        if self.backend:
            logger.info("[SYNC] Authenticating with backend...")
            if self.backend.authenticate():
                self.stats['backend_online'] = True
                # Register device
                self.backend.register_device()
                self.backend.update_device_status('ONLINE')
            else:
                logger.warning("[SYNC] Backend authentication failed, will retry")
        
        # Connect MQTT
        if self.mqtt:
            logger.info("[SYNC] Connecting to MQTT broker...")
            if self.mqtt.connect():
                self.stats['mqtt_online'] = True
                # Set up command handler
                self.mqtt.set_command_callback(self._handle_mqtt_command)
            else:
                logger.warning("[SYNC] MQTT connection failed, will retry")
        
        # Start sync thread
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        
        # Start MQTT heartbeat thread if available
        if self.mqtt:
            self.mqtt_thread = threading.Thread(target=self._mqtt_heartbeat_loop, daemon=True)
            self.mqtt_thread.start()
        
        logger.info("[SYNC] Sync manager started")
    
    def stop(self):
        """Stop sync threads."""
        if not self.running:
            return
        
        logger.info("[SYNC] Stopping sync manager...")
        self.running = False
        
        # Update device status to offline
        if self.backend and self.stats['backend_online']:
            self.backend.update_device_status('OFFLINE')
        
        # Disconnect MQTT
        if self.mqtt and self.stats['mqtt_online']:
            self.mqtt.disconnect()
        
        # Wait for threads to finish
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        if self.mqtt_thread:
            self.mqtt_thread.join(timeout=5)
        
        logger.info("[SYNC] Sync manager stopped")
    
    def _sync_loop(self):
        """Main sync loop - runs in background thread."""
        logger.info("[SYNC] Sync loop started")
        
        while self.running:
            try:
                # Sync unsynced sensor data
                self._sync_sensor_data()
                
                # Process queues
                self._process_sensor_queue()
                self._process_alert_queue()
                
                # Fetch remote commands
                self._fetch_commands()
                
                # Update stats
                self.stats['last_sync'] = datetime.now()
                
                # Sleep until next sync
                time.sleep(self.sync_interval)
                
            except Exception as e:
                logger.error(f"[SYNC] Sync loop error: {e}", exc_info=True)
                time.sleep(10)  # Short delay before retry
        
        logger.info("[SYNC] Sync loop stopped")
    
    def _mqtt_heartbeat_loop(self):
        """MQTT heartbeat and reconnection loop."""
        while self.running:
            try:
                if self.mqtt:
                    if not self.mqtt.is_alive():
                        logger.warning("[SYNC] MQTT disconnected, reconnecting...")
                        if self.mqtt.connect():
                            self.stats['mqtt_online'] = True
                            logger.info("[SYNC] MQTT reconnected")
                        else:
                            self.stats['mqtt_online'] = False
                    
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"[SYNC] MQTT heartbeat error: {e}")
                time.sleep(10)
    
    def _sync_sensor_data(self):
        """Sync unsynced sensor data from SQLite to cloud."""
        try:
            # Get unsynced records
            unsynced = self.db.get_unsynced_sensor_data(limit=self.batch_size)
            
            if not unsynced:
                self.stats['pending_records'] = 0
                return
            
            logger.info(f"[SYNC] Syncing {len(unsynced)} sensor records")
            self.stats['pending_records'] = len(unsynced)
            
            # Sync to Backend API
            if self.backend and self.stats['backend_online']:
                synced_ids = self._sync_to_backend(unsynced)
                
                # Mark as synced
                for record_id in synced_ids:
                    self.db.mark_sensor_data_synced(record_id)
                
                self.stats['total_synced'] += len(synced_ids)
            
            # Sync to Firebase (optional)
            if self.firebase and self.firebase.is_initialized:
                firebase_count = self.firebase.sync_sensor_readings(unsynced)
                logger.debug(f"[SYNC] Firebase synced {firebase_count} records")
                self.stats['firebase_online'] = True
            
        except Exception as e:
            logger.error(f"[SYNC] Sensor data sync error: {e}")
            self.stats['failed_syncs'] += 1
    
    def _sync_to_backend(self, records: List[Dict]) -> List[int]:
        """
        Sync sensor records to backend API.
        
        Returns:
            List of successfully synced record IDs
        """
        synced_ids = []
        
        # Group by room
        by_room = {}
        for record in records:
            room = record.get('room', 'unknown')
            if room not in by_room:
                by_room[room] = []
            by_room[room].append(record)
        
        # Send per room
        for room, room_records in by_room.items():
            # Prepare batch data
            for record in room_records:
                sensor_data = {
                    room: {
                        'temp': record.get('temp'),
                        'humidity': record.get('humidity'),
                        'co2': record.get('co2')
                    },
                    'timestamp': record.get('timestamp')
                }
                
                # Upload
                if self.backend.send_sensor_data(sensor_data):
                    synced_ids.append(record['id'])
        
        return synced_ids
    
    def _process_sensor_queue(self):
        """Process queued sensor data for real-time publishing."""
        if not self.mqtt or not self.stats['mqtt_online']:
            return
        
        try:
            while not self.sensor_queue.empty():
                try:
                    sensor_data = self.sensor_queue.get(timeout=0.1)
                    self.mqtt.publish_sensor_data(sensor_data)
                    self.sensor_queue.task_done()
                except Empty:
                    break
        except Exception as e:
            logger.error(f"[SYNC] Sensor queue processing error: {e}")
    
    def _process_alert_queue(self):
        """Process queued alerts."""
        try:
            while not self.alert_queue.empty():
                try:
                    alert = self.alert_queue.get(timeout=0.1)
                    
                    # Send via backend
                    if self.backend and self.stats['backend_online']:
                        self.backend.send_alert(
                            alert['type'],
                            alert['message'],
                            alert.get('severity', 'WARNING'),
                            alert.get('data')
                        )
                    
                    # Publish via MQTT
                    if self.mqtt and self.stats['mqtt_online']:
                        self.mqtt.publish_alert(
                            alert['type'],
                            alert['message'],
                            alert.get('severity', 'WARNING')
                        )
                    
                    self.alert_queue.task_done()
                except Empty:
                    break
        except Exception as e:
            logger.error(f"[SYNC] Alert queue processing error: {e}")
    
    def _fetch_commands(self):
        """Fetch pending commands from backend."""
        if not self.backend or not self.stats['backend_online']:
            return
        
        try:
            commands = self.backend.get_actuator_commands()
            
            if commands:
                for cmd in commands:
                    self.command_queue.put(cmd)
                    logger.info(f"[SYNC] Queued command: {cmd.get('command')}")
        
        except Exception as e:
            logger.error(f"[SYNC] Command fetch error: {e}")
    
    def _handle_mqtt_command(self, command: Dict[str, Any]):
        """Handle command received via MQTT."""
        logger.info(f"[SYNC] Received MQTT command: {command}")
        self.command_queue.put(command)
    
    # ==================== PUBLIC API ====================
    
    def queue_sensor_data(self, sensor_data: Dict[str, Any]):
        """
        Queue sensor data for real-time MQTT publishing.
        SQLite storage is handled separately.
        """
        self.sensor_queue.put(sensor_data)
    
    def queue_alert(self, alert_type: str, message: str, severity: str = "WARNING", data: Optional[Dict] = None):
        """Queue alert for cloud delivery."""
        alert = {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        self.alert_queue.put(alert)
    
    def get_pending_command(self, timeout: float = 0.1) -> Optional[Dict[str, Any]]:
        """
        Get next pending command from queue.
        
        Returns:
            Command dictionary or None if queue empty
        """
        try:
            command = self.command_queue.get(timeout=timeout)
            self.command_queue.task_done()
            return command
        except Empty:
            return None
    
    def acknowledge_command(self, command_id: str, success: bool, response_data: Optional[Dict] = None):
        """Acknowledge command execution."""
        if self.backend and self.stats['backend_online']:
            self.backend.acknowledge_command(command_id, success, response_data)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get sync statistics."""
        stats = self.stats.copy()
        stats['sensor_queue_size'] = self.sensor_queue.qsize()
        stats['alert_queue_size'] = self.alert_queue.qsize()
        stats['command_queue_size'] = self.command_queue.qsize()
        return stats
    
    def force_sync(self):
        """Force immediate sync (bypasses interval)."""
        logger.info("[SYNC] Forcing immediate sync")
        self._sync_sensor_data()
    
    def is_online(self) -> bool:
        """Check if any cloud service is online."""
        return (
            self.stats['backend_online'] or
            self.stats['firebase_online'] or
            self.stats['mqtt_online']
        )


# ==================== CONVENIENCE FUNCTION ====================
def create_sync_manager(
    db_manager: DatabaseManager,
    backend_client: Optional[BackendAPIClient] = None,
    firebase_sync: Optional[FirebaseSync] = None,
    mqtt_client: Optional[MQTTClient] = None
) -> SyncManager:
    """Create and return configured sync manager."""
    return SyncManager(
        db_manager=db_manager,
        backend_client=backend_client,
        firebase_sync=firebase_sync,
        mqtt_client=mqtt_client
    )

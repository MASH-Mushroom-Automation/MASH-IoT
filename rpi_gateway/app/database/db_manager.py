# M.A.S.H. IoT - Database Manager
# Offline-first SQLite database with Firebase sync support

import sqlite3
import logging
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import SCHEMA, SensorReading, DeviceCommand

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages local SQLite database for offline-first data storage.
    
    Pattern: IMMEDIATELY save to SQLite, THEN attempt cloud sync.
    """
    
    def __init__(self, db_path: str = 'rpi_gateway/data/sensor_data.db'):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist."""
        data_dir = os.path.dirname(self.db_path)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            logger.info(f"[DB] Created data directory: {data_dir}")
    
    def connect(self):
        """Open database connection and initialize schema."""
        try:
            self.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,  # Allow multi-threading
                timeout=10.0
            )
            self.conn.row_factory = sqlite3.Row  # Access columns by name
            
            # Initialize schema
            self.conn.executescript(SCHEMA)
            self.conn.commit()
            
            logger.info(f"[DB] Connected to database: {self.db_path}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"[DB] Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("[DB] Disconnected from database")
    
    # ==================== SENSOR DATA ====================
    def insert_sensor_reading(self, reading: SensorReading) -> Optional[int]:
        """
        Insert sensor reading into database.
        
        Returns:
            Row ID if successful, None otherwise
        """
        if not self.conn:
            logger.error("[DB] Not connected")
            return None
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO sensor_data (timestamp, room, temperature, humidity, co2)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(timestamp, room) DO UPDATE SET
                    temperature = excluded.temperature,
                    humidity = excluded.humidity,
                    co2 = excluded.co2
            """, (reading.timestamp, reading.room, reading.temperature, 
                  reading.humidity, reading.co2))
            
            self.conn.commit()
            row_id = cursor.lastrowid
            
            logger.debug(f"[DB] Inserted {reading.room} reading: T={reading.temperature}°C")
            return row_id
            
        except sqlite3.Error as e:
            logger.error(f"[DB] Insert failed: {e}")
            return None
    
    def insert_sensor_data_batch(self, data: Dict[str, Any]) -> bool:
        """
        Insert both fruiting and spawning room data from Arduino JSON.
        
        Args:
            data: {"fruiting": {...}, "spawning": {...}, "timestamp": ...}
        """
        try:
            timestamp = data.get('timestamp', datetime.now().timestamp())
            
            # Insert fruiting room data
            if 'fruiting' in data and 'error' not in data['fruiting']:
                fruiting = data['fruiting']
                reading = SensorReading(
                    room='fruiting',
                    temperature=fruiting['temp'],
                    humidity=fruiting['humidity'],
                    co2=fruiting['co2'],
                    timestamp=timestamp
                )
                self.insert_sensor_reading(reading)
            
            # Insert spawning room data
            if 'spawning' in data and 'error' not in data['spawning']:
                spawning = data['spawning']
                reading = SensorReading(
                    room='spawning',
                    temperature=spawning['temp'],
                    humidity=spawning['humidity'],
                    co2=spawning['co2'],
                    timestamp=timestamp
                )
                self.insert_sensor_reading(reading)
            
            return True
            
        except Exception as e:
            logger.error(f"[DB] Batch insert failed: {e}")
            return False
    
    def get_latest_readings(self, limit: int = 1) -> List[Dict[str, Any]]:
        """Get latest sensor readings for both rooms."""
        if not self.conn:
            return []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM sensor_data
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit * 2,))  # Get both rooms
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            logger.error(f"[DB] Query failed: {e}")
            return []
    
    def get_unsynced_readings(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get sensor readings that haven't been synced to cloud."""
        if not self.conn:
            return []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM sensor_data
                WHERE is_synced = 0
                ORDER BY timestamp ASC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            logger.error(f"[DB] Query failed: {e}")
            return []
    
    def mark_as_synced(self, record_id: int):
        """Mark a sensor reading as synced to cloud."""
        if not self.conn:
            return
        
        try:
            self.conn.execute("""
                UPDATE sensor_data
                SET is_synced = 1, synced_at = ?
                WHERE id = ?
            """, (datetime.now().timestamp(), record_id))
            self.conn.commit()
            
        except sqlite3.Error as e:
            logger.error(f"[DB] Update failed: {e}")
    
    # ==================== DEVICE COMMANDS ====================
    def insert_command(self, command: DeviceCommand) -> Optional[int]:
        """Insert device command into database."""
        if not self.conn:
            return None
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO device_commands (timestamp, room, actuator, action, source)
                VALUES (?, ?, ?, ?, ?)
            """, (command.timestamp, command.room, command.actuator, 
                  command.action, command.source))
            
            self.conn.commit()
            return cursor.lastrowid
            
        except sqlite3.Error as e:
            logger.error(f"[DB] Command insert failed: {e}")
            return None
    
    def insert_alert(self, room: str, alert_type: str, message: str, severity: str = 'warning') -> Optional[int]:
        """Insert system alert into database."""
        if not self.conn:
            return None
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO system_logs (timestamp, level, component, message, data)
                VALUES (?, ?, ?, ?, ?)
            """, (datetime.now().timestamp(), severity.upper(), room, message, alert_type))
            
            self.conn.commit()
            return cursor.lastrowid
            
        except sqlite3.Error as e:
            logger.error(f"[DB] Alert insert failed: {e}")
            return None
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent system logs (alerts history)."""
        if not self.conn:
            return []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM system_logs
                WHERE level IN ('WARNING', 'ERROR', 'CRITICAL')
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            logger.error(f"[DB] Logs query failed: {e}")
            return []

    # ==================== ACTIVE ALERTS (STATEFUL) ====================
    def upsert_active_alert(self, room: str, alert_type: str, message: str, severity: str = 'WARNING'):
        """
        Upsert an active alert. 
        If it exists, update the message and timestamp.
        If it doesn't exist, insert it.
        """
        if not self.conn:
            return

        try:
            # We also log to system_logs for history
            self.insert_alert(room, alert_type, message, severity)

            self.conn.execute("""
                INSERT INTO active_alerts (room, alert_type, severity, message, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(room, alert_type) DO UPDATE SET
                    severity = excluded.severity,
                    message = excluded.message,
                    updated_at = excluded.updated_at
            """, (room, alert_type, severity.upper(), message, datetime.now().timestamp()))
            
            self.conn.commit()
            logger.info(f"[DB] Active alert upserted: {room}/{alert_type}")
            
        except sqlite3.Error as e:
            logger.error(f"[DB] Active alert upsert failed: {e}")

    def resolve_alert(self, room: str, alert_type: str):
        """
        Remove an alert from active_alerts table (mark as resolved).
        """
        if not self.conn:
            return

        try:
            self.conn.execute("""
                DELETE FROM active_alerts
                WHERE room = ? AND alert_type = ?
            """, (room, alert_type))
            
            self.conn.commit()
            # logger.debug(f"[DB] Alert resolved: {room}/{alert_type}") # debug only to avoid noise
            
        except sqlite3.Error as e:
            logger.error(f"[DB] Alert resolution failed: {e}")

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts."""
        if not self.conn:
            return []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM active_alerts
                ORDER BY severity = 'CRITICAL' DESC, severity = 'ERROR' DESC, created_at DESC
            """)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            logger.error(f"[DB] Active alerts query failed: {e}")
            return []

    def acknowledge_alert(self, alert_id: int):
        """Mark an active alert as acknowledged."""
        if not self.conn:
            return

        try:
            self.conn.execute("""
                UPDATE active_alerts
                SET is_acknowledged = 1, acknowledged_at = ?
                WHERE id = ?
            """, (datetime.now().timestamp(), alert_id))
            self.conn.commit()
            logger.info(f"[DB] Alert {alert_id} acknowledged")
            
        except sqlite3.Error as e:
            logger.error(f"[DB] Alert acknowledgement failed: {e}")
    
    def mark_command_executed(self, command_id: int):
        """Mark command as executed."""
        if not self.conn:
            return
        
        try:
            self.conn.execute("""
                UPDATE device_commands
                SET is_executed = 1, executed_at = ?
                WHERE id = ?
            """, (datetime.now().timestamp(), command_id))
            self.conn.commit()
            
        except sqlite3.Error as e:
            logger.error(f"[DB] Command update failed: {e}")
    
    # ==================== SENSOR MAPPING ====================
    def get_sensor_mapping(self, room: str, sensor_type: str) -> Optional[str]:
        """
        Get backend sensor ID for a room and sensor type.
        
        Args:
            room: 'fruiting' or 'spawning'
            sensor_type: 'temp', 'humidity', or 'co2'
        
        Returns:
            Backend sensor ID or None if not found
        """
        if not self.conn:
            return None
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT backend_sensor_id FROM sensor_mapping
                WHERE room = ? AND sensor_type = ?
            """, (room, sensor_type))
            
            row = cursor.fetchone()
            return row['backend_sensor_id'] if row else None
            
        except sqlite3.Error as e:
            logger.error(f"[DB] Sensor mapping query failed: {e}")
            return None
    
    def set_sensor_mapping(self, room: str, sensor_type: str, backend_sensor_id: str, 
                          sensor_name: Optional[str] = None, unit: Optional[str] = None) -> bool:
        """
        Set or update sensor ID mapping.
        
        Args:
            room: 'fruiting' or 'spawning'
            sensor_type: 'temp', 'humidity', or 'co2'
            backend_sensor_id: UUID from backend
            sensor_name: Optional friendly name
            unit: Optional unit (°C, %, ppm)
        
        Returns:
            True if successful
        """
        if not self.conn:
            return False
        
        try:
            self.conn.execute("""
                INSERT INTO sensor_mapping (room, sensor_type, backend_sensor_id, sensor_name, unit, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(room, sensor_type) DO UPDATE SET
                    backend_sensor_id = excluded.backend_sensor_id,
                    sensor_name = excluded.sensor_name,
                    unit = excluded.unit,
                    updated_at = excluded.updated_at
            """, (room, sensor_type, backend_sensor_id, sensor_name, unit, datetime.now().timestamp()))
            
            self.conn.commit()
            logger.info(f"[DB] Sensor mapping updated: {room}/{sensor_type} -> {backend_sensor_id}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"[DB] Sensor mapping update failed: {e}")
            return False
    
    def get_all_sensor_mappings(self) -> List[Dict[str, Any]]:
        """Get all sensor mappings."""
        if not self.conn:
            return []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM sensor_mapping ORDER BY room, sensor_type")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            logger.error(f"[DB] Sensor mappings query failed: {e}")
            return []
    
    # ==================== DEVICE CONFIGURATION ====================
    def get_config(self, key: str) -> Optional[Any]:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key
        
        Returns:
            Configuration value or None
        """
        if not self.conn:
            return None
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT config_value, config_type FROM device_config
                WHERE config_key = ?
            """, (key,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            value = row['config_value']
            config_type = row['config_type']
            
            # Parse value based on type
            if config_type == 'number':
                return float(value)
            elif config_type == 'boolean':
                return value.lower() in ('true', '1', 'yes')
            elif config_type == 'json':
                import json
                return json.loads(value)
            else:
                return value
                
        except Exception as e:
            logger.error(f"[DB] Config get failed: {e}")
            return None
    
    def set_config(self, key: str, value: Any, config_type: str = 'string') -> bool:
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Value to store
            config_type: 'string', 'number', 'boolean', or 'json'
        
        Returns:
            True if successful
        """
        if not self.conn:
            return False
        
        try:
            # Convert value to string for storage
            if config_type == 'json':
                import json
                value_str = json.dumps(value)
            else:
                value_str = str(value)
            
            self.conn.execute("""
                INSERT INTO device_config (config_key, config_value, config_type, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(config_key) DO UPDATE SET
                    config_value = excluded.config_value,
                    config_type = excluded.config_type,
                    updated_at = excluded.updated_at
            """, (key, value_str, config_type, datetime.now().timestamp()))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"[DB] Config set failed: {e}")
            return False
    
    # ==================== SYSTEM LOGS ====================
    def log(self, level: str, component: str, message: str, data: Optional[str] = None):
        """Insert system log entry."""
        if not self.conn:
            return
        
        try:
            self.conn.execute("""
                INSERT INTO system_logs (timestamp, level, component, message, data)
                VALUES (?, ?, ?, ?, ?)
            """, (datetime.now().timestamp(), level, component, message, data))
            self.conn.commit()
            
        except sqlite3.Error as e:
            logger.error(f"[DB] Log insert failed: {e}")
    
    # ==================== CONTEXT MANAGER ====================
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# ==================== CONVENIENCE FUNCTIONS ====================
def create_db_manager(db_path: str = 'rpi_gateway/data/sensor_data.db') -> DatabaseManager:
    """Create and connect database manager."""
    manager = DatabaseManager(db_path)
    manager.connect()
    return manager


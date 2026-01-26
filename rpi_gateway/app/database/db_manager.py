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


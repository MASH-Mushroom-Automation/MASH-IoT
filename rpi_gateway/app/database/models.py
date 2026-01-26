# M.A.S.H. IoT - Database Models
# SQLite schema for offline-first data storage

from datetime import datetime
from typing import Optional

# SQLite schema (will be created by db_manager)
SCHEMA = """
-- Sensor readings table
CREATE TABLE IF NOT EXISTS sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    room TEXT NOT NULL CHECK(room IN ('fruiting', 'spawning')),
    temperature REAL NOT NULL,
    humidity REAL NOT NULL,
    co2 INTEGER NOT NULL,
    is_synced INTEGER DEFAULT 0,
    synced_at REAL,
    created_at REAL DEFAULT (strftime('%s', 'now')),
    UNIQUE(timestamp, room)
);

-- Device commands table (sent to Arduino)
CREATE TABLE IF NOT EXISTS device_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    room TEXT NOT NULL CHECK(room IN ('fruiting', 'spawning', 'all')),
    actuator TEXT NOT NULL CHECK(actuator IN ('fan', 'mist', 'light', 'all')),
    action TEXT NOT NULL CHECK(action IN ('on', 'off')),
    source TEXT DEFAULT 'manual' CHECK(source IN ('manual', 'ml', 'schedule', 'api')),
    is_executed INTEGER DEFAULT 0,
    executed_at REAL,
    created_at REAL DEFAULT (strftime('%s', 'now'))
);

-- Sync queue for unsynced records
CREATE TABLE IF NOT EXISTS sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    retry_count INTEGER DEFAULT 0,
    last_attempt REAL,
    created_at REAL DEFAULT (strftime('%s', 'now')),
    UNIQUE(table_name, record_id)
);

-- System logs
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    level TEXT NOT NULL CHECK(level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    component TEXT NOT NULL,
    message TEXT NOT NULL,
    data TEXT,
    created_at REAL DEFAULT (strftime('%s', 'now'))
);

-- ML model metadata
CREATE TABLE IF NOT EXISTS ml_model_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL UNIQUE,
    version TEXT NOT NULL,
    accuracy REAL,
    trained_at REAL NOT NULL,
    training_samples INTEGER,
    file_path TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at REAL DEFAULT (strftime('%s', 'now'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sensor_timestamp ON sensor_data(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_room ON sensor_data(room, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_synced ON sensor_data(is_synced, created_at);
CREATE INDEX IF NOT EXISTS idx_commands_timestamp ON device_commands(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sync_queue_table ON sync_queue(table_name, created_at);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(level, timestamp DESC);
"""

# Data classes for type safety
class SensorReading:
    def __init__(self, room: str, temperature: float, humidity: float, co2: int, 
                 timestamp: Optional[float] = None):
        self.room = room
        self.temperature = temperature
        self.humidity = humidity
        self.co2 = co2
        self.timestamp = timestamp or datetime.now().timestamp()
    
    def to_dict(self):
        return {
            'room': self.room,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'co2': self.co2,
            'timestamp': self.timestamp
        }


class DeviceCommand:
    def __init__(self, room: str, actuator: str, action: str, 
                 source: str = 'manual', timestamp: Optional[float] = None):
        self.room = room
        self.actuator = actuator
        self.action = action
        self.source = source
        self.timestamp = timestamp or datetime.now().timestamp()
    
    def to_dict(self):
        return {
            'room': self.room,
            'actuator': self.actuator,
            'action': self.action,
            'source': self.source,
            'timestamp': self.timestamp
        }
    
    def to_arduino_command(self) -> str:
        """Convert to Arduino serial command format."""
        if self.room == 'all' and self.actuator == 'all':
            return "ALL_OFF" if self.action == 'off' else ""
        
        # Format: ROOM_ACTUATOR_ACTION
        room_upper = self.room.upper()
        actuator_upper = self.actuator.upper()
        action_upper = self.action.upper()
        
        return f"{room_upper}_{actuator_upper}_{action_upper}"


# M.A.S.H. IoT - MQTT Client (HiveMQ Cloud)
# Handles real-time device communication via MQTT protocol

import logging
import json
import os
import ssl
import time
from typing import Dict, Any, Callable, Optional
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()

logger = logging.getLogger(__name__)


class MQTTClient:
    """
    MQTT client for real-time bidirectional communication with MASH backend.
    Uses HiveMQ Cloud broker with TLS encryption.
    
    Topics:
        - devices/{device_id}/sensor_data (publish) - Sensor readings
        - devices/{device_id}/commands (subscribe) - Remote commands
        - devices/{device_id}/status (publish) - Device status updates
        - devices/{device_id}/alerts (publish) - Alert notifications
    """
    
    def __init__(self, device_id: Optional[str] = None):
        self.device_id = device_id or os.getenv('DEVICE_ID', 'rpi_gateway_001')
        
        # HiveMQ Cloud credentials
        self.broker = os.getenv('MQTT_BROKER', '290691cd2bcb4d7faf979db077890beb.s1.eu.hivemq.cloud')
        self.port = int(os.getenv('MQTT_PORT', '8883'))  # TLS port
        self.username = os.getenv('MQTT_USERNAME', '')
        self.password = os.getenv('MQTT_PASSWORD', '')
        
        # MQTT Client
        self.client = mqtt.Client(
            client_id=f"mash_iot_{self.device_id}",
            clean_session=True,
            protocol=mqtt.MQTTv311
        )
        
        # Callbacks
        self.command_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # Connection state
        self.is_connected = False
        self.reconnect_delay = 5  # seconds
        
        # Setup
        self._setup_client()
        
        logger.info(f"[MQTT] Initialized client for {self.broker}:{self.port}")
    
    def _setup_client(self):
        """Configure MQTT client with TLS and callbacks."""
        # Set credentials
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        
        # Enable TLS/SSL
        self.client.tls_set(
            ca_certs=None,  # Use system CA bundle
            certfile=None,
            keyfile=None,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1_2,
            ciphers=None
        )
        
        # Disable hostname verification if needed (not recommended for production)
        # self.client.tls_insecure_set(True)
        
        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        self.client.on_subscribe = self._on_subscribe
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            self.is_connected = True
            logger.info("[MQTT] Connected to broker")
            
            # Subscribe to command topic
            command_topic = f"devices/{self.device_id}/commands"
            client.subscribe(command_topic, qos=1)
            logger.info(f"[MQTT] Subscribed to {command_topic}")
            
            # Publish online status
            self.publish_status("ONLINE")
        else:
            self.is_connected = False
            error_messages = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized"
            }
            logger.error(f"[MQTT] Connection failed: {error_messages.get(rc, f'Unknown error {rc}')}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker."""
        self.is_connected = False
        
        if rc == 0:
            logger.info("[MQTT] Disconnected cleanly")
        else:
            logger.warning(f"[MQTT] Unexpected disconnect (rc={rc}), paho will auto-reconnect via loop_start()")
            # paho-mqtt's loop_start() handles auto-reconnect with exponential backoff
    
    def _on_message(self, client, userdata, msg):
        """Callback when message received."""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))
            
            logger.info(f"[MQTT] Received message on {topic}")
            logger.debug(f"[MQTT] Payload: {payload}")
            
            # Handle commands
            if topic.endswith('/commands'):
                if self.command_callback:
                    self.command_callback(payload)
                else:
                    logger.warning("[MQTT] Received command but no callback registered")
            
        except json.JSONDecodeError as e:
            logger.error(f"[MQTT] Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"[MQTT] Error processing message: {e}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback when message published."""
        logger.debug(f"[MQTT] Message {mid} published")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback when subscribed to topic."""
        logger.debug(f"[MQTT] Subscribed (mid={mid}, QoS={granted_qos})")
    
    def connect(self) -> bool:
        """
        Connect to MQTT broker.
        
        Returns:
            True if connection initiated successfully
        """
        try:
            logger.info(f"[MQTT] Connecting to {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()  # Start background thread
            
            # Wait for connection (with timeout)
            timeout = 10
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.5)
            
            if self.is_connected:
                logger.info("[MQTT] Connection established")
                return True
            else:
                logger.error("[MQTT] Connection timeout")
                return False
                
        except Exception as e:
            logger.error(f"[MQTT] Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.is_connected:
            self.publish_status("OFFLINE")
            time.sleep(0.5)  # Allow message to send
        
        self.client.loop_stop()
        self.client.disconnect()
        self.is_connected = False
        logger.info("[MQTT] Disconnected")
    
    def publish_sensor_data(self, sensor_data: Dict[str, Any]) -> bool:
        """
        Publish sensor readings to MQTT.
        
        Args:
            sensor_data: Dictionary containing sensor readings
        
        Returns:
            True if published successfully
        """
        if not self.is_connected:
            logger.warning("[MQTT] Cannot publish - not connected")
            return False
        
        topic = f"devices/{self.device_id}/sensor_data"
        
        try:
            payload = json.dumps(sensor_data)
            result = self.client.publish(topic, payload, qos=1, retain=False)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"[MQTT] Published sensor data to {topic}")
                return True
            else:
                logger.error(f"[MQTT] Publish failed: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"[MQTT] Publish error: {e}")
            return False
    
    def publish_status(self, status: str, metadata: Optional[Dict] = None) -> bool:
        """
        Publish device status.
        
        Args:
            status: Device status ('ONLINE', 'OFFLINE', 'ERROR', etc.)
            metadata: Optional additional status information
        
        Returns:
            True if published successfully
        """
        if not self.is_connected and status != "OFFLINE":
            return False
        
        topic = f"devices/{self.device_id}/status"
        
        try:
            payload = {
                'status': status,
                'timestamp': time.time(),
                'metadata': metadata or {}
            }
            
            result = self.client.publish(topic, json.dumps(payload), qos=1, retain=True)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"[MQTT] Published status: {status}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"[MQTT] Status publish error: {e}")
            return False
    
    def publish_alert(self, alert_type: str, message: str, severity: str = "WARNING") -> bool:
        """
        Publish alert to MQTT.
        
        Args:
            alert_type: Alert type identifier
            message: Alert message
            severity: Alert severity ('INFO', 'WARNING', 'CRITICAL')
        
        Returns:
            True if published successfully
        """
        if not self.is_connected:
            return False
        
        topic = f"devices/{self.device_id}/alerts"
        
        try:
            payload = {
                'type': alert_type,
                'message': message,
                'severity': severity,
                'timestamp': time.time()
            }
            
            result = self.client.publish(topic, json.dumps(payload), qos=1, retain=False)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            logger.error(f"[MQTT] Alert publish error: {e}")
            return False
    
    def set_command_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Register callback for incoming commands.
        
        Args:
            callback: Function to call when command received
        """
        self.command_callback = callback
        logger.info("[MQTT] Command callback registered")
    
    def is_alive(self) -> bool:
        """Check if MQTT connection is alive."""
        return self.is_connected


# ==================== CONVENIENCE FUNCTION ====================
def create_mqtt_client(device_id: Optional[str] = None) -> MQTTClient:
    """Create and return a configured MQTT client."""
    return MQTTClient(device_id=device_id)

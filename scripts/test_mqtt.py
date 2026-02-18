#!/usr/bin/env python3
"""
MQTT Test Script - Verify MQTT connectivity and command reception
Usage: python test_mqtt.py
"""

import os
import sys
import time
import json
import logging
from dotenv import load_dotenv

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from cloud.mqtt_client import create_mqtt_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))

def test_callback(payload):
    """Test callback for MQTT commands."""
    logger.info("=" * 60)
    logger.info("🎯 CALLBACK TRIGGERED!")
    logger.info(f"Payload received: {json.dumps(payload, indent=2)}")
    logger.info("=" * 60)

def main():
    # Get device ID from environment
    device_id = os.getenv('DEVICE_ID', 'MASH-B2-CAL26-CE637C')

    logger.info("=" * 60)
    logger.info("🧪 MQTT CONNECTIVITY TEST")
    logger.info("=" * 60)
    logger.info(f"Device ID: {device_id}")
    logger.info(f"Broker: {os.getenv('MQTT_BROKER')}")
    logger.info(f"Port: {os.getenv('MQTT_PORT')}")
    logger.info(f"Username: {os.getenv('MQTT_USERNAME')}")
    logger.info(f"Expected command topic: devices/{device_id}/commands")
    logger.info("=" * 60)

    # Create MQTT client
    logger.info("\n📡 Creating MQTT client...")
    mqtt_client = create_mqtt_client(device_id=device_id)

    # Register callback
    logger.info("🔗 Registering command callback...")
    mqtt_client.set_command_callback(test_callback)

    # Connect
    logger.info("🔌 Connecting to MQTT broker...")
    success = mqtt_client.connect()

    if success:
        logger.info("✅ MQTT CONNECTED SUCCESSFULLY!")
        logger.info(f"📡 Now listening on: devices/{device_id}/commands")
        logger.info("")
        logger.info("=" * 60)
        logger.info("📱 TEST INSTRUCTIONS:")
        logger.info("=" * 60)
        logger.info("1. Open your mobile app")
        logger.info("2. Toggle any actuator (e.g., Mist Maker)")
        logger.info("3. Watch this console for incoming MQTT messages")
        logger.info("")
        logger.info("Alternatively, use MQTT Explorer or mosquitto_pub:")
        logger.info(f"  mosquitto_pub -h {os.getenv('MQTT_BROKER')} \\")
        logger.info(f"    -p {os.getenv('MQTT_PORT')} \\")
        logger.info(f"    -u {os.getenv('MQTT_USERNAME')} \\")
        logger.info(f"    -P {os.getenv('MQTT_PASSWORD')} \\")
        logger.info(f"    --cafile /etc/ssl/certs/ca-certificates.crt \\")
        logger.info(f"    -t devices/{device_id}/commands \\")
        logger.info(f'    -m \'{{"room":"fruiting","actuator":"mist_maker","state":"ON","source":"test"}}\'')
        logger.info("=" * 60)
        logger.info("")
        logger.info("⏳ Waiting for commands... (Press Ctrl+C to exit)")
        logger.info("")

        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n\n🛑 Stopping test...")
    else:
        logger.error("❌ MQTT CONNECTION FAILED!")
        logger.error("Check:")
        logger.error("  - MQTT credentials in config/.env")
        logger.error("  - Network connectivity")
        logger.error("  - HiveMQ Cloud cluster status")

    # Cleanup
    mqtt_client.disconnect()
    logger.info("👋 Test completed")

if __name__ == '__main__':
    main()

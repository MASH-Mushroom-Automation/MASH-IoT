import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rpi_gateway.app.database.db_manager import DatabaseManager
from rpi_gateway.app.core.logic_engine import MushroomAI

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_alerts")

def test_alerts():
    # Use a test database
    db_path = 'rpi_gateway/data/test_alerts.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        
    db = DatabaseManager(db_path)
    db.connect()
    
    # Initialize Logic Engine
    config = {
        "fruiting_room": {
            "temp_target": 24,
            "temp_tolerance": 2,
            "humidity_target": 90,
            "humidity_tolerance": 10,
            "co2_max": 1000
        }
    }
    ai = MushroomAI(config=config)
    ai.db = db # Inject DB manually
    
    logger.info("--- TEST 1: Normal Conditions ---")
    data_normal = {"temp": 24, "humidity": 90, "co2": 800}
    ai._check_and_alert("fruiting", data_normal, config["fruiting_room"])
    
    active = db.get_active_alerts()
    logger.info(f"Active alerts: {len(active)}")
    assert len(active) == 0, "Should have 0 alerts"

    logger.info("--- TEST 2: High Temperature Alert ---")
    data_hot = {"temp": 28, "humidity": 90, "co2": 800} # Target 24 + 2 = 26 max
    ai._check_and_alert("fruiting", data_hot, config["fruiting_room"])
    
    active = db.get_active_alerts()
    logger.info(f"Active alerts: {len(active)}")
    assert len(active) == 1, "Should have 1 alert"
    assert active[0]['alert_type'] == 'temperature_high'
    logger.info(f"Alert found: {active[0]['message']}")

    logger.info("--- TEST 3: Back to Normal (Resolve Alert) ---")
    ai._check_and_alert("fruiting", data_normal, config["fruiting_room"])
    
    active = db.get_active_alerts()
    logger.info(f"Active alerts: {len(active)}")
    assert len(active) == 0, "Should have 0 alerts (resolved)"
    
    # Check history
    history = db.get_recent_alerts()
    logger.info(f"History entries: {len(history)}")
    assert len(history) >= 1, "Should have history of the alert"

    logger.info("--- TEST 4: Multiple Alerts ---")
    data_bad = {"temp": 28, "humidity": 50, "co2": 2000}
    ai._check_and_alert("fruiting", data_bad, config["fruiting_room"])
    
    active = db.get_active_alerts()
    logger.info(f"Active alerts: {len(active)}")
    assert len(active) == 3, "Should have 3 alerts (Temp, Humidity, CO2)"

    logger.info("--- TEST 5: Acknowledge Alert ---")
    alert_id = active[0]['id']
    logger.info(f"Acknowledging alert ID {alert_id}")
    db.acknowledge_alert(alert_id)
    
    active_after_ack = db.get_active_alerts()
    ack_alert = next(a for a in active_after_ack if a['id'] == alert_id)
    assert ack_alert['is_acknowledged'] == 1, "Alert should be acknowledged"
    
    logger.info("✅ ALL TESTS PASSED")
    
    db.disconnect()
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    test_alerts()

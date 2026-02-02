"""
M.A.S.H. IoT - Logic Engine with Machine Learning
Implements two-stage ML pipeline for mushroom cultivation automation:
1. Anomaly Detection (Isolation Forest) - Filters sensor noise
2. Actuation Control (Decision Tree) - Automates relay states

Features:
- Smart Humidifier System: Alternating mist (5s) and fan (10s) cycles
- Predictive humidity control to prevent overshooting
- Hysteresis to prevent rapid on/off cycling
"""

import os
import logging
import time
from typing import Dict, List, Tuple
from datetime import datetime
import numpy as np

try:
    import joblib
    from sklearn.ensemble import IsolationForest
    from sklearn.tree import DecisionTreeClassifier
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("scikit-learn not available, ML features disabled")

logger = logging.getLogger(__name__)

class HumidifierCycleManager:
    """
    Manages the Humidifier System cycle:
    - Mist Maker ON for 10 seconds (Fan OFF)
    - Humidifier Fan ON for 30 seconds (Mist OFF)
    - Alternates between the two when system is active
    """
    
    def __init__(self):
        self.cycle_active = False
        self.cycle_start_time = 0
        self.current_phase = "idle"  # "idle", "mist", "fan"
        self.phase_start_time = 0
        
        # Cycle timings
        self.MIST_DURATION = 10.0  # seconds
        self.FAN_DURATION = 30.0  # seconds
    
    def start_cycle(self):
        """Start the humidifier cycle"""
        if not self.cycle_active:
            self.cycle_active = True
            self.cycle_start_time = time.time()
            self.current_phase = "mist"
            self.phase_start_time = time.time()
            logger.info("[HUMIDIFIER] Starting cycle: MIST phase")
    
    def stop_cycle(self):
        """Stop the humidifier cycle"""
        if self.cycle_active:
            self.cycle_active = False
            self.current_phase = "idle"
            logger.info("[HUMIDIFIER] Stopping cycle")
    
    def get_current_states(self) -> Dict[str, str]:
        """
        Get current actuator states based on cycle phase.
        
        Returns:
            Dict with mist_maker and humidifier_fan states
        """
        if not self.cycle_active:
            return {"mist_maker": "OFF", "humidifier_fan": "OFF"}
        
        current_time = time.time()
        elapsed = current_time - self.phase_start_time
        
        if self.current_phase == "mist":
            if elapsed >= self.MIST_DURATION:
                # Switch to fan phase
                self.current_phase = "fan"
                self.phase_start_time = current_time
                logger.info("[HUMIDIFIER] Switching: MIST OFF -> FAN ON")
                return {"mist_maker": "OFF", "humidifier_fan": "ON"}
            else:
                # During mist phase: mist ON, fan OFF
                return {"mist_maker": "ON", "humidifier_fan": "OFF"}
        
        elif self.current_phase == "fan":
            if elapsed >= self.FAN_DURATION:
                # Switch back to mist phase
                self.current_phase = "mist"
                self.phase_start_time = current_time
                logger.info("[HUMIDIFIER] Switching: FAN OFF -> MIST ON")
                return {"mist_maker": "ON", "humidifier_fan": "OFF"}
            else:
                # During fan phase: mist OFF, fan ON
                return {"mist_maker": "OFF", "humidifier_fan": "ON"}
        
        return {"mist_maker": "OFF", "humidifier_fan": "OFF"}
    
    def get_phase_info(self) -> Dict:
        """Get detailed cycle information for monitoring"""
        if not self.cycle_active:
            return {"active": False, "phase": "idle", "elapsed": 0, "remaining": 0}
        
        current_time = time.time()
        elapsed = current_time - self.phase_start_time
        
        if self.current_phase == "mist":
            remaining = max(0, self.MIST_DURATION - elapsed)
        elif self.current_phase == "fan":
            remaining = max(0, self.FAN_DURATION - elapsed)
        else:
            remaining = 0
        
        return {
            "active": True,
            "phase": self.current_phase,
            "elapsed": round(elapsed, 1),
            "remaining": round(remaining, 1),
            "total_runtime": round(current_time - self.cycle_start_time, 1)
        }


class MushroomAI:
    """
    ML-powered automation controller for mushroom cultivation.
    Uses scikit-learn models trained on baseline cultivation data.
    """
    
    def __init__(self, model_dir: str = "rpi_gateway/data/models", config: Dict = None):
        """
        Initialize ML models and load configuration.
        
        Args:
            model_dir: Path to directory containing .pkl model files
            config: Configuration dict with room thresholds
        """
        self.model_dir = model_dir
        self.config = config or {}
        self.anomaly_detector = None
        self.actuator_model = None
        self.ml_enabled = ML_AVAILABLE
        self.db = None  # Database reference (set by orchestrator)
        
        # Humidifier cycle manager
        self.humidifier_cycle = HumidifierCycleManager()
        
        # Track last sent commands to avoid duplicates
        self.last_cycle_commands = {}
        
        # Humidity control state tracking
        self.last_humidity_readings = []  # Track last 3 readings for trend analysis
        self.humidity_rising_rate = 0  # Rate of humidity increase (% per second)
        
        if self.ml_enabled:
            self._load_models()
        else:
            logger.warning("ML disabled - using rule-based logic only")
    
    def _load_models(self):
        """Load pre-trained ML models from disk"""
        try:
            isolation_forest_path = os.path.join(self.model_dir, "isolation_forest.pkl")
            decision_tree_path = os.path.join(self.model_dir, "decision_tree.pkl")
            
            if os.path.exists(isolation_forest_path):
                self.anomaly_detector = joblib.load(isolation_forest_path)
                logger.info("Loaded Isolation Forest model for anomaly detection")
            else:
                logger.warning(f"Anomaly model not found at {isolation_forest_path}")
                self.anomaly_detector = None
            
            if os.path.exists(decision_tree_path):
                self.actuator_model = joblib.load(decision_tree_path)
                logger.info("Loaded Decision Tree model for actuation control")
            else:
                logger.warning(f"Actuation model not found at {decision_tree_path}")
                self.actuator_model = None
                
        except Exception as e:
            logger.error(f"Failed to load ML models: {e}")
            self.ml_enabled = False
    
    def detect_anomaly(self, sensor_data: Dict) -> Tuple[bool, float]:
        """
        Stage 1: Anomaly Detection
        Filters out sensor hardware faults and environmental spikes.
        
        Args:
            sensor_data: Dict with keys {temp, humidity, co2}
        
        Returns:
            (is_anomaly, anomaly_score) - True if data is anomalous
        """
        if not self.ml_enabled or self.anomaly_detector is None:
            # Fallback: Simple range-based validation
            return self._rule_based_anomaly_check(sensor_data)
        
        try:
            # Prepare feature vector [temp, humidity, co2]
            features = np.array([[
                sensor_data.get('temp', 0),
                sensor_data.get('humidity', 0),
                sensor_data.get('co2', 0)
            ]])
            
            # Predict (-1 = anomaly, 1 = normal)
            prediction = self.anomaly_detector.predict(features)[0]
            score = self.anomaly_detector.score_samples(features)[0]
            
            is_anomaly = (prediction == -1)
            
            if is_anomaly:
                logger.warning(f"Anomaly detected: {sensor_data}, score: {score:.3f}")
            
            return is_anomaly, score
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return self._rule_based_anomaly_check(sensor_data)
    
    def _rule_based_anomaly_check(self, sensor_data: Dict) -> Tuple[bool, float]:
        """Fallback rule-based anomaly detection"""
        temp = sensor_data.get('temp', 0)
        humidity = sensor_data.get('humidity', 0)
        co2 = sensor_data.get('co2', 0)
        
        # Hard limits for sensor validation
        is_anomaly = (
            temp < 0 or temp > 50 or          # Temperature out of physical range
            humidity < 0 or humidity > 100 or # Humidity impossible values
            co2 < 400 or co2 > 10000          # CO2 unrealistic
        )
        
        return is_anomaly, -1.0 if is_anomaly else 0.0
    
    def predict_actuator_states(self, room: str, sensor_data: Dict) -> Dict[str, str]:
        """
        Stage 2: Actuation Control
        Predicts optimal relay states (fan, mist, light) based on environment.
        
        Args:
            room: "fruiting" or "spawning"
            sensor_data: Dict with keys {temp, humidity, co2}
        
        Returns:
            Dict with keys {fan, mist, light} and values "on" or "off"
        """
        # First check for anomalies
        is_anomaly, _ = self.detect_anomaly(sensor_data)
        if is_anomaly:
            logger.warning(f"Skipping actuation for anomalous {room} data")
            # Return a safe state for all possible actuators
            return {
                "exhaust_fan": "OFF", "intake_fan": "OFF", 
                "humidity_system": "OFF", "light": "OFF"
            }
        
        # Route to the correct logic based on the room
        if room == "fruiting":
            return self._rule_based_fruiting_actuation(sensor_data)
        elif room == "spawning":
            return self._rule_based_spawning_actuation(sensor_data)
        else:
            logger.warning(f"Unknown room '{room}', returning safe state.")
            return {
                "exhaust_fan": "OFF", "intake_fan": "OFF", 
                "humidity_system": "OFF", "light": "OFF"
            }

    def _calculate_humidity_trend(self, current_humidity: float) -> float:
        """
        Calculate humidity rising rate based on recent readings.
        
        Args:
            current_humidity: Current humidity reading
            
        Returns:
            Rate of change in % per second (positive = rising, negative = falling)
        """
        self.last_humidity_readings.append({
            'value': current_humidity,
            'timestamp': time.time()
        })
        
        # Keep only last 3 readings (15 seconds of data at 5s intervals)
        if len(self.last_humidity_readings) > 3:
            self.last_humidity_readings.pop(0)
        
        if len(self.last_humidity_readings) < 2:
            return 0  # Not enough data
        
        # Calculate rate of change
        first = self.last_humidity_readings[0]
        last = self.last_humidity_readings[-1]
        
        time_delta = last['timestamp'] - first['timestamp']
        if time_delta == 0:
            return 0
        
        humidity_delta = last['value'] - first['value']
        rate = humidity_delta / time_delta  # % per second
        
        return rate
    
    def _predict_humidity_overshoot(self, current_humidity: float, target: float, rate: float) -> bool:
        """
        Predict if humidity will overshoot target if misting continues.
        
        Args:
            current_humidity: Current humidity %
            target: Target humidity %
            rate: Current rate of change (% per second)
            
        Returns:
            True if likely to overshoot, False otherwise
        """
        if rate <= 0:
            return False  # Not rising
        
        # Predict humidity after one full cycle (15 seconds)
        predicted_humidity = current_humidity + (rate * 15)
        
        # Add 2% safety margin to prevent overshooting
        safety_margin = 2
        
        return predicted_humidity > (target + safety_margin)

    def _rule_based_fruiting_actuation(self, sensor_data: Dict) -> Dict[str, str]:
        """
        Enhanced rule-based actuation logic for FRUITING stage with AI-controlled humidifier.
        Uses hysteresis to prevent rapid on/off cycling.
        Implements smart humidity control with predictive stopping.
        
        Args:
            sensor_data: Sensor readings dict
            
        Returns:
            Dict mapping actuator names to states ("ON"/"OFF")
        """
        config = self.config.get("fruiting_room", {})
        temp = sensor_data.get('temp', 0)
        humidity = sensor_data.get('humidity', 0)
        co2 = sensor_data.get('co2', 0)

        # CO2 Control with hysteresis (prevent rapid on/off)
        co2_max = config.get('co2_max', 1000)
        co2_hysteresis = config.get('co2_hysteresis', 100)
        exhaust_fan_state = "ON" if co2 > co2_max else ("OFF" if co2 < (co2_max - co2_hysteresis) else "OFF")

        # ===== SMART HUMIDITY CONTROL WITH AI CYCLE =====
        humidity_target = config.get('humidity_target', 90)
        humidity_min = humidity_target - 5  # 85%
        humidity_max = humidity_target + 5  # 95%
        
        # Calculate humidity trend
        humidity_rate = self._calculate_humidity_trend(humidity)
        
        # Decision logic for humidifier cycle
        cycle_info = self.humidifier_cycle.get_phase_info()
        
        if humidity < humidity_min - 2:
            # Far below target - start cycle if not active
            if not cycle_info['active']:
                self.humidifier_cycle.start_cycle()
                logger.info(f"[AI-HUMIDIFIER] Started cycle - Humidity {humidity:.1f}% < target {humidity_min}%")
        
        elif humidity >= humidity_target and cycle_info['active']:
            # At or above target - check if we should stop
            will_overshoot = self._predict_humidity_overshoot(humidity, humidity_max, humidity_rate)
            
            if will_overshoot:
                # Stop cycle to prevent overshooting
                self.humidifier_cycle.stop_cycle()
                logger.info(f"[AI-HUMIDIFIER] Stopped cycle - Predicted overshoot (humidity={humidity:.1f}%, rate={humidity_rate:.3f}%/s)")
            elif humidity >= humidity_max:
                # At maximum - stop immediately
                self.humidifier_cycle.stop_cycle()
                logger.info(f"[AI-HUMIDIFIER] Stopped cycle - Max humidity reached ({humidity:.1f}%)")
        
        elif humidity > humidity_max + 2:
            # Significantly over target - ensure cycle is stopped
            if cycle_info['active']:
                self.humidifier_cycle.stop_cycle()
                logger.warning(f"[AI-HUMIDIFIER] Emergency stop - Humidity too high ({humidity:.1f}%)")
        
        # Get actuator states from cycle manager
        humidifier_states = self.humidifier_cycle.get_current_states()
        mist_maker_state = humidifier_states['mist_maker']
        humidifier_fan_state = humidifier_states['humidifier_fan']
        
        # Log cycle status periodically
        if cycle_info['active'] and int(cycle_info.get('total_runtime', 0)) % 5 == 0:
            logger.debug(f"[HUMIDIFIER] Phase={cycle_info['phase']}, elapsed={cycle_info['elapsed']}s, humidity={humidity:.1f}%, rate={humidity_rate:.3f}%/s")
        
        # Temperature-based fan assist
        temp_max = config.get('temp_target', 24) + 2
        if temp > temp_max:
            exhaust_fan_state = "ON"  # Emergency cooling
        
        # Intake fan works opposite to exhaust for air circulation
        intake_fan_state = "OFF" if exhaust_fan_state == "ON" else "OFF"

        # Generate alerts for critical conditions and save to database
        alerts = self._check_and_alert("fruiting", sensor_data, config)
        if alerts and self.db is not None:
            for room, alert_type, message, severity in alerts:
                try:
                    self.db.insert_alert(room, alert_type, message, severity)
                    logger.info(f"[ALERT] {message}")
                except Exception as e:
                    logger.error(f"[ALERT] Failed to save alert: {e}")

        return {
            "exhaust_fan": exhaust_fan_state,
            "intake_fan": intake_fan_state,
            "mist_maker": mist_maker_state,
            "humidifier_fan": humidifier_fan_state,
        }

    def _rule_based_spawning_actuation(self, sensor_data: Dict) -> Dict[str, str]:
        """
        Rule-based logic for the spawning room.
        - Timed exhaust fan for air exchange.
        - Emergency exhaust fan activation if temperature is too high.
        """
        config = self.config.get("spawning_room", {})
        temp = sensor_data.get('temp', 0)
        
        # Emergency Temperature Flush
        temp_emergency_threshold = config.get('temp_emergency', 28)
        if temp > temp_emergency_threshold:
            logger.warning(f"SPAWNING EMERGENCY: Temp at {temp}°C. Forcing exhaust fan ON.")
            return {"exhaust_fan": "ON"}

        # Timed Air Cycle Logic (placeholder)
        # This logic is more complex as it requires state (last run time).
        # For now, we'll keep it simple and turn it off. A real implementation
        # would use a timestamp to decide when to run the timed cycle.
        # For example, run for 5 minutes every 4 hours.
        exhaust_fan_state = "OFF" 

        return {
            "exhaust_fan": exhaust_fan_state
        }

    def _check_and_alert(self, room: str, sensor_data: Dict, config: Dict):
        """Check sensor data against thresholds and log alerts."""
        temp = sensor_data.get('temp', 0)
        humidity = sensor_data.get('humidity', 0)
        co2 = sensor_data.get('co2', 0)
        
        alerts = []
        
        # Temperature alerts
        temp_target = config.get('temp_target', 24)
        temp_tolerance = config.get('temp_tolerance', 2)
        if temp > (temp_target + temp_tolerance):
            msg = f"{room.upper()} temperature HIGH: {temp}°C (target: {temp_target}°C)"
            logger.warning(f"[ALERT] {msg}")
            alerts.append((room, 'temperature_high', msg, 'warning'))
        elif temp < (temp_target - temp_tolerance):
            msg = f"{room.upper()} temperature LOW: {temp}°C (target: {temp_target}°C)"
            logger.warning(f"[ALERT] {msg}")
            alerts.append((room, 'temperature_low', msg, 'warning'))
        
        # Humidity alerts
        humidity_target = config.get('humidity_target', 90)
        humidity_tolerance = config.get('humidity_tolerance', 10)
        if humidity < (humidity_target - humidity_tolerance):
            msg = f"{room.upper()} humidity LOW: {humidity}% (target: {humidity_target}%)"
            logger.warning(f"[ALERT] {msg}")
            alerts.append((room, 'humidity_low', msg, 'warning'))
        
        # CO2 alerts
        co2_max = config.get('co2_max', 1000)
        if co2 > co2_max:
            msg = f"{room.upper()} CO2 HIGH: {co2}ppm (max: {co2_max}ppm)"
            logger.warning(f"[ALERT] {msg}")
            alerts.append((room, 'co2_high', msg, 'warning'))
        
        return alerts
    
    def process_sensor_reading(self, room_data: Dict) -> List[str]:
        """
        Main entry point: Process sensor readings for all rooms and generate commands.
        
        Args:
            room_data: Dict with "fruiting" and "spawning" keys.
                       e.g., {"fruiting": {"temp":...}, "spawning": {"temp":...}}
        
        Returns:
            List of command strings to send to Arduino (e.g., ["MIST_MAKER_ON"])
        """
        all_commands = []
        
        # Actuator name mapping for Arduino commands
        # Some actuators don't need room prefix (shared), others do (room-specific)
        actuator_name_map = {
            'mist_maker': 'MIST_MAKER',  # Shared actuator (no room prefix)
            'humidifier_fan': 'HUMIDIFIER_FAN',  # Shared actuator
            'exhaust_fan': 'EXHAUST_FAN',  # Will add room prefix
            'intake_fan': 'INTAKE_FAN',  # Will add room prefix
            'led': 'LED'  # Will add room prefix
        }
        
        for room, sensor_data in room_data.items():
            if room not in ["fruiting", "spawning"]:
                continue

            actuator_states = self.predict_actuator_states(room, sensor_data)
            
            # Convert states to Arduino commands
            room_prefix = room.upper()
            
            for actuator, state in actuator_states.items():
                # Get mapped actuator name
                arduino_actuator = actuator_name_map.get(actuator, actuator.upper())
                
                # Add room prefix for room-specific actuators
                if actuator in ['exhaust_fan', 'intake_fan', 'led']:
                    command = f"{room_prefix}_{arduino_actuator}_{state.upper()}"
                else:
                    # Shared actuators (mist_maker, humidifier_fan)
                    command = f"{arduino_actuator}_{state.upper()}"
                
                all_commands.append(command)
                logger.debug(f"[COMMAND] Generated: {command} for {room}/{actuator}")
                
        return all_commands


# Training utilities (for baseline data generation)
def generate_baseline_training_data(num_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic training data for ML models.
    Based on ideal mushroom cultivation parameters.
    
    Returns:
        (X_features, y_labels) for model training
    """
    np.random.seed(42)
    
    # Normal operating ranges
    temp_normal = np.random.normal(24, 2, num_samples)
    humidity_normal = np.random.normal(90, 3, num_samples)
    co2_normal = np.random.normal(800, 200, num_samples)
    hour_normal = np.random.randint(0, 24, num_samples)
    
    X = np.column_stack([temp_normal, humidity_normal, co2_normal, hour_normal])
    
    # Labels: [fan_state, mist_state, light_state]
    # Simple rules for labels:
    y_fan = (co2_normal > 900).astype(int)
    y_mist = (humidity_normal < 88).astype(int)
    y_light = ((hour_normal >= 8) & (hour_normal < 20)).astype(int)
    
    y = np.column_stack([y_fan, y_mist, y_light])
    
    return X, y


def train_and_save_models(model_dir: str = "rpi_gateway/data/models"):
    """
    Train ML models on baseline data and save to disk.
    Run this during initial setup or for model retraining.
    """
    if not ML_AVAILABLE:
        logger.error("scikit-learn not available, cannot train models")
        return
    
    os.makedirs(model_dir, exist_ok=True)
    
    # Generate training data
    X, y = generate_baseline_training_data(1000)
    
    # Train Isolation Forest (anomaly detection)
    logger.info("Training Isolation Forest...")
    iso_forest = IsolationForest(contamination=0.1, random_state=42)
    iso_forest.fit(X[:, :3])  # Only temp, humidity, co2
    joblib.dump(iso_forest, os.path.join(model_dir, "isolation_forest.pkl"))
    logger.info("Isolation Forest saved")
    
    # Train Decision Tree (actuation control)
    logger.info("Training Decision Tree...")
    dt_model = DecisionTreeClassifier(max_depth=5, random_state=42)
    dt_model.fit(X, y)
    joblib.dump(dt_model, os.path.join(model_dir, "decision_tree.pkl"))
    logger.info("Decision Tree saved")
    
    logger.info(f"Models saved to {model_dir}")


if __name__ == "__main__":
    # Example usage and model training
    logging.basicConfig(level=logging.INFO)
    
    # Train models
    train_and_save_models()
    
    # Test inference
    test_config = {
        "fruiting_room": {
            "fan_control": {"co2_threshold": 900},
            "mist_control": {"humidity_threshold": 88},
            "light": {"duration": 12}
        }
    }
    
    ai = MushroomAI(config=test_config)
    
    test_data = {"temp": 24.5, "humidity": 85, "co2": 950}
    commands = ai.process_sensor_reading("fruiting", test_data)
    
    logger.info(f"Test commands: {commands}")

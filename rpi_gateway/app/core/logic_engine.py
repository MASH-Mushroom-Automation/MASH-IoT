"""
M.A.S.H. IoT - Logic Engine with Machine Learning
Implements two-stage ML pipeline for mushroom cultivation automation:
1. Anomaly Detection (Isolation Forest) - Filters sensor noise
2. Actuation Control (Decision Tree) - Automates relay states
"""

import os
import logging
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
            return {"fan": "off", "mist": "off", "light": "off"}  # Safe state
        
        if self.ml_enabled and self.actuator_model is not None:
            return self._ml_based_actuation(room, sensor_data)
        else:
            return self._rule_based_actuation(room, sensor_data)
    
    def _ml_based_actuation(self, room: str, sensor_data: Dict) -> Dict[str, str]:
        """ML-powered actuation decisions"""
        try:
            # Feature engineering: [temp, humidity, co2, hour_of_day]
            hour = datetime.now().hour
            features = np.array([[
                sensor_data.get('temp', 0),
                sensor_data.get('humidity', 0),
                sensor_data.get('co2', 0),
                hour
            ]])
            
            # Predict [fan_state, mist_state, light_state] (0=off, 1=on)
            predictions = self.actuator_model.predict(features)[0]
            
            return {
                "fan": "on" if predictions[0] == 1 else "off",
                "mist": "on" if predictions[1] == 1 else "off",
                "light": "on" if predictions[2] == 1 else "off"
            }
            
        except Exception as e:
            logger.error(f"ML actuation failed: {e}, falling back to rules")
            return self._rule_based_actuation(room, sensor_data)
    
    def _rule_based_actuation(self, room: str, sensor_data: Dict) -> Dict[str, str]:
        """Fallback rule-based automation (threshold logic)"""
        room_config = self.config.get(f"{room}_room", {})
        
        temp = sensor_data.get('temp', 0)
        humidity = sensor_data.get('humidity', 0)
        co2 = sensor_data.get('co2', 0)
        
        # Fan Control: Turn on if CO2 exceeds threshold
        fan_threshold = room_config.get('fan_control', {}).get('co2_threshold', 1000)
        fan_state = "on" if co2 > fan_threshold else "off"
        
        # Mist Control: Turn on if humidity drops below threshold
        mist_threshold = room_config.get('mist_control', {}).get('humidity_threshold', 85)
        mist_state = "on" if humidity < mist_threshold else "off"
        
        # Light Control: Based on time and room type
        hour = datetime.now().hour
        light_duration = room_config.get('light', {}).get('duration', 0)
        
        # Simple photoperiod: Light on from 8 AM to (8 AM + duration)
        if room == "fruiting" and light_duration > 0:
            light_state = "on" if 8 <= hour < (8 + light_duration) else "off"
        else:
            light_state = "off"  # Spawning room stays dark
        
        logger.info(f"{room.capitalize()} Room - Rule-based: Fan={fan_state}, Mist={mist_state}, Light={light_state}")
        
        return {
            "fan": fan_state,
            "mist": mist_state,
            "light": light_state
        }
    
    def process_sensor_reading(self, room: str, sensor_data: Dict) -> List[str]:
        """
        Main entry point: Process sensor reading and generate commands.
        
        Args:
            room: "fruiting" or "spawning"
            sensor_data: Dict with {temp, humidity, co2}
        
        Returns:
            List of command strings to send to Arduino (e.g., ["FRUITING_FAN_ON"])
        """
        actuator_states = self.predict_actuator_states(room, sensor_data)
        
        # Convert states to Arduino commands
        commands = []
        room_prefix = room.upper()
        
        for actuator, state in actuator_states.items():
            command = f"{room_prefix}_{actuator.upper()}_{state.upper()}"
            commands.append(command)
        
        return commands


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

#!/usr/bin/env python3
"""
M.A.S.H. IoT - System Test Script
Tests the improvements made to condition monitoring, controls, and alerts.
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from web.routes import calculate_room_condition

def test_condition_calculation():
    """Test the dynamic condition status calculation."""
    print("=" * 60)
    print("Testing Dynamic Condition Status Calculation")
    print("=" * 60)
    
    # Test cases for Fruiting Room
    fruiting_targets = {
        'temp_target': 24.0,
        'temp_tolerance': 2.0,
        'humidity_target': 90.0,
        'humidity_tolerance': 10.0,
        'co2_max': 1000
    }
    
    test_cases_fruiting = [
        # (sensor_data, expected_status)
        ({'temp': 24.0, 'humidity': 90.0, 'co2': 800}, 'Optimal'),
        ({'temp': 24.0, 'humidity': 90.0, 'co2': 1100}, 'Warning'),
        ({'temp': 24.0, 'humidity': 90.0, 'co2': 1350}, 'Critical'),
        ({'temp': 28.0, 'humidity': 90.0, 'co2': 800}, 'Warning'),
        ({'temp': 29.0, 'humidity': 90.0, 'co2': 800}, 'Critical'),
        ({'temp': 24.0, 'humidity': 75.0, 'co2': 800}, 'Warning'),
    ]
    
    print("\n📊 FRUITING ROOM Tests:")
    for i, (data, expected) in enumerate(test_cases_fruiting, 1):
        status, _ = calculate_room_condition('fruiting', data, fruiting_targets)
        result = "✅ PASS" if status == expected else f"❌ FAIL (got {status})"
        print(f"  Test {i}: {data} -> {status} {result}")
    
    # Test cases for Spawning Room
    spawning_targets = {
        'temp_target': 25.0,
        'temp_tolerance': 2.0,
        'humidity_target': 95.0,
        'humidity_tolerance': 10.0,
        'co2_max': 2000
    }
    
    test_cases_spawning = [
        # (sensor_data, expected_status)
        ({'temp': 25.0, 'humidity': 95.0, 'co2': 1800}, 'Optimal'),
        ({'temp': 25.0, 'humidity': 95.0, 'co2': 2100}, 'Warning'),
        ({'temp': 25.0, 'humidity': 95.0, 'co2': 2700}, 'Critical'),
        ({'temp': 28.2, 'humidity': 55.6, 'co2': 563}, 'Critical'),  # The original issue!
    ]
    
    print("\n📊 SPAWNING ROOM Tests:")
    for i, (data, expected) in enumerate(test_cases_spawning, 1):
        status, _ = calculate_room_condition('spawning', data, spawning_targets)
        result = "✅ PASS" if status == expected else f"❌ FAIL (got {status})"
        print(f"  Test {i}: {data} -> {status} {result}")
    
    # Test edge cases
    print("\n📊 EDGE CASES:")
    
    # Sensor error
    status, _ = calculate_room_condition('fruiting', {'error': 'timeout'}, fruiting_targets)
    print(f"  Sensor Error: {status} {'✅ PASS' if status == 'Sensor Error' else '❌ FAIL'}")
    
    # No data
    status, _ = calculate_room_condition('fruiting', None, fruiting_targets)
    print(f"  No Data: {status} {'✅ PASS' if status == 'No Data' else '❌ FAIL'}")
    
    # Missing values
    status, _ = calculate_room_condition('fruiting', {'temp': 24.0}, fruiting_targets)
    print(f"  Missing Values: {status} {'✅ PASS' if status == 'No Data' else '❌ FAIL'}")


def test_ml_system():
    """Test ML system availability."""
    print("\n" + "=" * 60)
    print("Testing ML System")
    print("=" * 60)
    
    try:
        from sklearn.ensemble import IsolationForest
        print("✅ scikit-learn is installed")
        
        from core.logic_engine import MushroomAI
        print("✅ MushroomAI module imported")
        
        # Check for model files
        import os
        model_dir = "rpi_gateway/data/models"
        iso_path = os.path.join(model_dir, "isolation_forest.pkl")
        dt_path = os.path.join(model_dir, "decision_tree.pkl")
        
        if os.path.exists(iso_path):
            print(f"✅ Anomaly detection model found: {iso_path}")
        else:
            print(f"⚠️  Anomaly detection model NOT found: {iso_path}")
            print("   Run: python -m app.core.logic_engine to train models")
        
        if os.path.exists(dt_path):
            print(f"✅ Actuation control model found: {dt_path}")
        else:
            print(f"⚠️  Actuation control model NOT found: {dt_path}")
            print("   Run: python -m app.core.logic_engine to train models")
        
    except ImportError as e:
        print(f"❌ scikit-learn NOT installed: {e}")
        print("   Install with: pip install scikit-learn joblib")


def test_database():
    """Test database connectivity."""
    print("\n" + "=" * 60)
    print("Testing Database")
    print("=" * 60)
    
    try:
        from database.db_manager import DatabaseManager
        
        db = DatabaseManager()
        if db.connect():
            print("✅ Database connection successful")
            
            # Test alert insertion
            alert_id = db.insert_alert(
                room='test',
                alert_type='test_alert',
                message='System test alert',
                severity='info'
            )
            
            if alert_id:
                print(f"✅ Alert insertion successful (ID: {alert_id})")
                
                # Test alert retrieval
                alerts = db.get_recent_alerts(limit=1)
                if alerts:
                    print(f"✅ Alert retrieval successful ({len(alerts)} alerts)")
                else:
                    print("⚠️  No alerts retrieved (this is OK if database is empty)")
            else:
                print("❌ Alert insertion failed")
            
            db.disconnect()
        else:
            print("❌ Database connection failed")
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")


def main():
    """Run all tests."""
    print("\n🔬 M.A.S.H. IoT System Test Suite")
    print("Testing improvements made to the system\n")
    
    test_condition_calculation()
    test_ml_system()
    test_database()
    
    print("\n" + "=" * 60)
    print("✨ Test Suite Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. If models are missing, run: python -m app.core.logic_engine")
    print("2. Start the system: python -m app.main")
    print("3. Access dashboard: http://localhost:5000/dashboard")
    print("4. Test controls with automation toggle")
    print("5. Check alerts page for any system warnings")


if __name__ == '__main__':
    main()

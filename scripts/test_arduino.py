#!/usr/bin/env python3
"""
M.A.S.H. IoT - Arduino Connection Test
Tests serial connection and verifies sensor data reception
"""

import sys
import os
import time

# Add project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'rpi_gateway'))

from app.core.serial_comm import ArduinoSerialComm

def test_connection():
    """Test Arduino connection with auto-detection and reconnect."""
    print("=" * 60)
    print("M.A.S.H. IoT - Arduino Connection Test")
    print("=" * 60)
    print()
    
    # Create connection with auto-reconnect enabled
    print("Initializing connection (auto-detect ON, auto-reconnect ON)...")
    arduino = ArduinoSerialComm(auto_reconnect=True)
    
    # Attempt connection with auto-detection
    print("\nConnecting to Arduino...")
    if not arduino.connect(auto_detect=True):
        print("❌ Connection failed!")
        print("\nTroubleshooting:")
        print("  1. Run: python3 scripts/find_arduino.py")
        print("  2. Check Arduino is powered on")
        print("  3. Verify USB cable supports data")
        return False
    
    print("✅ Connection successful!")
    print(f"   Port: {arduino.port}")
    print(f"   Baud: {arduino.baudrate}")
    print()
    
    # Test data reception
    print("-" * 60)
    print("Listening for sensor data (press Ctrl+C to stop)...")
    print("-" * 60)
    print()
    
    data_count = 0
    
    def on_data_received(data):
        nonlocal data_count
        data_count += 1
        
        print(f"\n[Packet #{data_count}] Received at {time.strftime('%H:%M:%S')}")
        print("-" * 40)
        
        # Fruiting room data
        if 'fruiting' in data and data['fruiting']:
            fruiting = data['fruiting']
            print("🍄 Fruiting Room:")
            print(f"   Temperature: {fruiting.get('temp', 'N/A')}°C")
            print(f"   Humidity:    {fruiting.get('humidity', 'N/A')}%")
            print(f"   CO2:         {fruiting.get('co2', 'N/A')} ppm")
        else:
            print("🍄 Fruiting Room: No data")
        
        # Spawning room data
        if 'spawning' in data and data['spawning']:
            spawning = data['spawning']
            print("\n🌱 Spawning Room:")
            print(f"   Temperature: {spawning.get('temp', 'N/A')}°C")
            print(f"   Humidity:    {spawning.get('humidity', 'N/A')}%")
            print(f"   CO2:         {spawning.get('co2', 'N/A')} ppm")
        else:
            print("\n🌱 Spawning Room: No data")
        
        print("-" * 40)
        
        # Test room-specific data accessors
        if data_count == 1:
            print("\n📊 Testing room-specific data methods:")
            fruiting_data = arduino.get_fruiting_room_data()
            spawning_data = arduino.get_spawning_room_data()
            
            if fruiting_data:
                print(f"   get_fruiting_room_data(): {fruiting_data}")
            if spawning_data:
                print(f"   get_spawning_room_data(): {spawning_data}")
    
    # Start listening
    arduino.start_listening(callback=on_data_received)
    
    try:
        # Test reconnect by simulating disconnect after 10 packets
        packet_limit = 50
        print(f"\nTest will run for {packet_limit} packets or until Ctrl+C")
        print("Try unplugging and replugging Arduino to test auto-reconnect!\n")
        
        while data_count < packet_limit:
            time.sleep(1)
            
            # Show connection status every 5 seconds
            if data_count % 5 == 0 and data_count > 0:
                status = "🟢 CONNECTED" if arduino.is_arduino_connected() else "🔴 DISCONNECTED"
                print(f"\n[Status Check] {status}")
        
        print(f"\n✅ Test completed! Received {data_count} data packets")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        print(f"   Received {data_count} data packets before stopping")
    
    finally:
        arduino.disconnect()
        print("\n✅ Disconnected cleanly")
    
    return True


if __name__ == '__main__':
    try:
        success = test_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

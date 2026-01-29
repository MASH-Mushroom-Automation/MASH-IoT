#!/usr/bin/env python3
"""
M.A.S.H. IoT - Connection Diagnostics
Monitors Arduino connection health and tests reconnection
"""

import sys
import os
import time
import signal

# Add project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'rpi_gateway'))

from app.core.serial_comm import ArduinoSerialComm

# Global flag for graceful shutdown
running = True

def signal_handler(sig, frame):
    global running
    print('\n\n⚠️  Shutting down...')
    running = False

signal.signal(signal.SIGINT, signal_handler)

def diagnose_connection():
    """Run continuous connection diagnostics."""
    print("=" * 70)
    print("M.A.S.H. IoT - Connection Diagnostics")
    print("=" * 70)
    print()
    print("This tool monitors connection health and tests auto-reconnect.")
    print("Instructions:")
    print("  1. Let it run and establish connection")
    print("  2. Unplug Arduino USB cable")
    print("  3. Wait 5-10 seconds")
    print("  4. Plug Arduino back in")
    print("  5. Watch for successful reconnection")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()
    
    # Create connection with auto-reconnect
    arduino = ArduinoSerialComm(auto_reconnect=True)
    
    # Initial connection
    print("Attempting initial connection...")
    if not arduino.connect(auto_detect=True):
        print("❌ Initial connection failed!")
        print("\nTroubleshooting:")
        print("  1. Run: python3 scripts/find_arduino.py")
        print("  2. Check Arduino is powered on")
        print("  3. Verify USB cable supports data")
        return False
    
    print(f"✅ Initial connection successful!")
    print(f"   Port: {arduino.port}")
    print()
    
    # Start monitoring
    print("-" * 70)
    print("Monitoring connection status (updates every second)")
    print("-" * 70)
    print()
    
    last_status = True
    data_received = 0
    consecutive_disconnects = 0
    disconnect_start = None
    
    def on_data(data):
        nonlocal data_received
        data_received += 1
    
    arduino.start_listening(callback=on_data)
    
    try:
        while running:
            current_status = arduino.is_arduino_connected()
            
            # Detect status change
            if current_status != last_status:
                timestamp = time.strftime('%H:%M:%S')
                
                if current_status:
                    # Reconnected
                    if disconnect_start:
                        downtime = time.time() - disconnect_start
                        print(f"\n[{timestamp}] 🟢 RECONNECTED after {downtime:.1f} seconds")
                        disconnect_start = None
                        consecutive_disconnects = 0
                    else:
                        print(f"\n[{timestamp}] 🟢 CONNECTED")
                    print(f"{'='*70}\n")
                else:
                    # Disconnected
                    disconnect_start = time.time()
                    consecutive_disconnects += 1
                    print(f"\n[{timestamp}] 🔴 DISCONNECTED (#{consecutive_disconnects})")
                    print(f"   Auto-reconnect is active - will retry every 5 seconds")
                    print(f"{'='*70}\n")
                
                last_status = current_status
            
            # Show status every 5 seconds
            if int(time.time()) % 5 == 0:
                timestamp = time.strftime('%H:%M:%S')
                
                if current_status:
                    print(f"[{timestamp}] ✓ Online | Packets: {data_received}")
                else:
                    if disconnect_start:
                        downtime = time.time() - disconnect_start
                        print(f"[{timestamp}] ✗ Offline | Downtime: {downtime:.0f}s | Retrying...")
                
                time.sleep(1)  # Prevent multiple prints in same second
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        pass
    finally:
        print("\n\nDisconnecting...")
        arduino.disconnect()
        
        print("\n" + "=" * 70)
        print("Diagnostics Summary")
        print("=" * 70)
        print(f"Total packets received: {data_received}")
        print(f"Total disconnections: {consecutive_disconnects}")
        
        if consecutive_disconnects > 0 and last_status:
            print("\n✅ Auto-reconnect is WORKING")
        elif consecutive_disconnects > 0 and not last_status:
            print("\n❌ Auto-reconnect FAILED - still disconnected")
            print("\nTroubleshooting:")
            print("  • Check Arduino is powered on")
            print("  • Verify USB cable is data-capable")
            print("  • Run: python3 scripts/find_arduino.py")
            print("  • Check permissions: sudo usermod -a -G dialout $USER")
        else:
            print("\n✓ Connection remained stable (no disconnections)")
        
        print("=" * 70)
    
    return True


if __name__ == '__main__':
    try:
        success = diagnose_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python3
"""
M.A.S.H. IoT - Arduino Port Finder
Scans all USB serial ports and identifies Arduino connections
"""

import serial.tools.list_ports
import sys

def find_arduino_ports():
    """Find all Arduino devices connected via USB."""
    print("=" * 60)
    print("M.A.S.H. IoT - Arduino Port Scanner")
    print("=" * 60)
    print()
    
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("❌ No serial ports found!")
        print("\nMake sure:")
        print("  • Arduino is plugged into USB port")
        print("  • USB cable supports data transfer (not power-only)")
        return None
    
    print(f"Found {len(ports)} serial port(s):\n")
    
    arduino_ports = []
    
    for i, port in enumerate(ports, 1):
        is_arduino = False
        
        # Check for Arduino identifiers
        if 'Arduino' in port.description or \
           'ttyACM' in port.device or \
           'ttyUSB' in port.device or \
           '2341' in str(port.vid):  # Arduino Vendor ID
            is_arduino = True
            arduino_ports.append(port.device)
        
        # Display port info
        marker = "✓ ARDUINO" if is_arduino else "  "
        print(f"{marker} [{i}] {port.device}")
        print(f"       Description: {port.description}")
        print(f"       Hardware ID: {port.hwid}")
        if port.vid:
            print(f"       VID:PID: {hex(port.vid)}:{hex(port.pid)}")
        print()
    
    if arduino_ports:
        print("=" * 60)
        print(f"Found {len(arduino_ports)} Arduino device(s):")
        for port in arduino_ports:
            print(f"   {port}")
        print()
        print("Use this port in your configuration:")
        print(f"   arduino = ArduinoSerialComm(port='{arduino_ports[0]}')")
        print("=" * 60)
        return arduino_ports[0]
    else:
        print("=" * 60)
        print("❌ No Arduino devices detected")
        print("\nAvailable ports might be:")
        print("  • USB-to-Serial adapters")
        print("  • Bluetooth devices")
        print("  • Other microcontrollers")
        print("\nTry the first port manually if you know Arduino is connected")
        print("=" * 60)
        return None


if __name__ == '__main__':
    try:
        arduino_port = find_arduino_ports()
        sys.exit(0 if arduino_port else 1)
    except KeyboardInterrupt:
        print("\n\nScan cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

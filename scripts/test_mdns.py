#!/usr/bin/env python3
"""
Test mDNS Advertisement for MASH IoT Gateway

This script tests if the mDNS service is being advertised correctly.
Run this on the Raspberry Pi to verify mDNS is working.

Usage:
    python3 test_mdns.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rpi_gateway.app.utils.mdns_advertiser import start_mdns_service, stop_mdns_service
import time

def main():
    print("=" * 60)
    print("MASH IoT mDNS Advertisement Test")
    print("=" * 60)
    print()
    
    # Test configuration
    device_id = "MASH-TEST-001"
    device_name = "Test Chamber"
    port = 5000
    
    print(f"Starting mDNS advertisement...")
    print(f"  Device ID: {device_id}")
    print(f"  Device Name: {device_name}")
    print(f"  Port: {port}")
    print()
    
    # Start mDNS service
    success = start_mdns_service(
        device_id=device_id,
        device_name=device_name,
        port=port
    )
    
    if success:
        print("✓ mDNS service started successfully!")
        print()
        print("Service should now be discoverable as:")
        print(f"  _mash-iot._tcp.local.")
        print()
        print("Test from another device:")
        print("  • Linux/Mac: avahi-browse -r _mash-iot._tcp")
        print("  • Windows: Use Bonjour Browser")
        print("  • Mobile: Use your MASH Grower app")
        print()
        print("Press Ctrl+C to stop...")
        
        try:
            # Keep running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nStopping mDNS service...")
            stop_mdns_service()
            print("✓ mDNS service stopped")
    else:
        print("✗ Failed to start mDNS service!")
        print()
        print("Troubleshooting:")
        print("  1. Check if avahi-daemon is installed:")
        print("     sudo apt-get install avahi-daemon")
        print("  2. Check if avahi-daemon is running:")
        print("     sudo systemctl status avahi-daemon")
        print("  3. Install Python zeroconf:")
        print("     pip install zeroconf")
        sys.exit(1)

if __name__ == "__main__":
    main()

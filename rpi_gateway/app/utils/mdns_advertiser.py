"""
mDNS Service Advertisement for MASH IoT Gateway

Advertises the device on the local network so mobile apps can discover it
via mDNS (multicast DNS) using the _mash-iot._tcp service type.

Requirements:
    - Avahi daemon must be installed and running (sudo apt-get install avahi-daemon)
    - Python zeroconf library (already in requirements.txt)
"""

import socket
import re
from zeroconf import ServiceInfo, Zeroconf
from typing import Optional
import time

def sanitize_device_id(device_id: str) -> str:
    """
    Sanitize device ID for mDNS service name (RFC 6763 compliant)
    
    Rules:
    - Only alphanumeric, hyphens, and underscores
    - Must start with letter or digit
    - Max 63 characters
    - Convert to lowercase
    
    Args:
        device_id: Raw device identifier
        
    Returns:
        Sanitized device ID safe for mDNS
    """
    # Convert to lowercase
    sanitized = device_id.lower()
    
    # Replace invalid characters with hyphens
    sanitized = re.sub(r'[^a-z0-9\-_]', '-', sanitized)
    
    # Ensure starts with alphanumeric
    sanitized = re.sub(r'^[^a-z0-9]+', '', sanitized)
    
    # Remove consecutive hyphens
    sanitized = re.sub(r'-+', '-', sanitized)
    
    # Trim to 63 characters
    sanitized = sanitized[:63]
    
    # Remove trailing hyphen
    sanitized = sanitized.rstrip('-')
    
    return sanitized or 'mash-device'  # Fallback if empty

class MDNSAdvertiser:
    """
    Advertises MASH IoT Gateway on local network via mDNS/Zeroconf
    """
    
    def __init__(self, device_id: str = "mash-iot-gateway", device_name: str = "MASH IoT Chamber", port: int = 5000):
        """
        Initialize mDNS advertiser
        
        Args:
            device_id: Unique identifier for this device (will be sanitized)
            device_name: Human-readable name
            port: Flask web server port
        """
        self.device_id = sanitize_device_id(device_id)
        self.device_name = device_name
        self.port = port
        self.zeroconf: Optional[Zeroconf] = None
        self.service_info: Optional[ServiceInfo] = None
        
        print(f"[mDNS] Initialized with ID: {self.device_id} (from: {device_id})")
        
    def get_local_ip(self) -> str:
        """
        Get the local IP address of this device
        
        Returns:
            IP address as string (e.g., "192.168.1.100" or "10.42.0.1")
        """
        try:
            # Create a dummy socket to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            print(f"[mDNS] Error getting local IP, using localhost: {e}")
            return "127.0.0.1"
    
    def start(self) -> bool:
        """
        Start advertising the service
        
        Returns:
            True if successful, False otherwise
        """
        try:
            local_ip = self.get_local_ip()
            print(f"[mDNS] Starting mDNS advertisement on {local_ip}:{self.port}")
            
            # Initialize Zeroconf
            self.zeroconf = Zeroconf()
            
            # Create service info
            # Service name format: <device-id>._mash-iot._tcp.local.
            service_type = "_mash-iot._tcp.local."
            service_name = f"{self.device_id}.{service_type}"
            
            # Properties (TXT records) that mobile app can read
            properties = {
                'name': self.device_name,
                'type': 'rpi-gateway',
                'api_version': 'v1',
                'device_id': self.device_id,
                'manufacturer': 'MASH',
                'port': str(self.port),
                'protocol': 'http',
            }
            
            self.service_info = ServiceInfo(
                type_=service_type,
                name=service_name,
                port=self.port,
                properties=properties,
                addresses=[socket.inet_aton(local_ip)],
                server=f"{self.device_id}.local."
            )
            
            # Register service
            self.zeroconf.register_service(self.service_info)
            
            print(f"[mDNS] ✓ Service advertised successfully")
            print(f"[mDNS]   Service Name: {service_name}")
            print(f"[mDNS]   Device ID: {self.device_id}")
            print(f"[mDNS]   Display Name: {self.device_name}")
            print(f"[mDNS]   IP Address: {local_ip}")
            print(f"[mDNS]   Port: {self.port}")
            print(f"[mDNS]   Browse for: avahi-browse -r _mash-iot._tcp")
            
            return True
            
        except Exception as e:
            print(f"[mDNS] ✗ Failed to start mDNS advertisement: {e}")
            print(f"[mDNS]   Make sure avahi-daemon is installed: sudo apt-get install avahi-daemon")
            return False
    
    def stop(self):
        """
        Stop advertising the service
        """
        try:
            if self.zeroconf and self.service_info:
                print("[mDNS] Stopping mDNS advertisement...")
                self.zeroconf.unregister_service(self.service_info)
                self.zeroconf.close()
                print("[mDNS] ✓ Service unregistered")
        except Exception as e:
            print(f"[mDNS] Error stopping mDNS: {e}")
    
    def update_service(self, new_name: Optional[str] = None, new_properties: Optional[dict] = None):
        """
        Update service information (requires re-registration)
        
        Args:
            new_name: New device name
            new_properties: New TXT record properties
        """
        if new_name:
            self.device_name = new_name
        
        # Stop and restart with new info
        self.stop()
        time.sleep(1)
        self.start()


# Global instance
_mdns_advertiser: Optional[MDNSAdvertiser] = None

def start_mdns_service(device_id: str = "mash-iot-gateway", device_name: str = "MASH IoT Chamber", port: int = 5000) -> bool:
    """
    Start mDNS service advertisement (module-level function)
    
    Args:
        device_id: Unique device identifier
        device_name: Human-readable name
        port: Flask server port
        
    Returns:
        True if successful
    """
    global _mdns_advertiser
    
    if _mdns_advertiser:
        print("[mDNS] Service already running")
        return True
    
    _mdns_advertiser = MDNSAdvertiser(device_id, device_name, port)
    return _mdns_advertiser.start()

def stop_mdns_service():
    """
    Stop mDNS service advertisement
    """
    global _mdns_advertiser
    
    if _mdns_advertiser:
        _mdns_advertiser.stop()
        _mdns_advertiser = None

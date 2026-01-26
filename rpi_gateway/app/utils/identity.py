"""M.A.S.H. IoT - Device Identity Manager
Generates and persists unique device identifier
"""

import os
import uuid
import logging

logger = logging.getLogger(__name__)

IDENTITY_FILE = os.path.expanduser('~/.mash/device_id')


class DeviceIdentity:
    """
    Manages persistent device identification.
    Used for cloud registration and analytics.
    """
    
    def __init__(self, identity_file: str = None):
        self.identity_file = identity_file or IDENTITY_FILE
        self.device_id = None
        self._load_or_generate()
    
    def _load_or_generate(self):
        """Load existing ID or generate new one."""
        if os.path.exists(self.identity_file):
            try:
                with open(self.identity_file, 'r') as f:
                    self.device_id = f.read().strip()
                logger.info(f"[IDENTITY] Loaded device ID: {self.device_id[:8]}...")
                return
            except Exception as e:
                logger.warning(f"[IDENTITY] Failed to load ID: {e}")
        
        self._generate_new_id()
    
    def _generate_new_id(self):
        """Generate and persist new device ID."""
        self.device_id = str(uuid.uuid4())
        
        try:
            os.makedirs(os.path.dirname(self.identity_file), exist_ok=True)
            
            with open(self.identity_file, 'w') as f:
                f.write(self.device_id)
            
            logger.info(f"[IDENTITY] Generated new device ID: {self.device_id[:8]}...")
            
        except Exception as e:
            logger.error(f"[IDENTITY] Failed to save ID: {e}")
    
    def get_id(self) -> str:
        """Get the device ID."""
        return self.device_id
    
    def get_short_id(self) -> str:
        """Get shortened ID for display (first 8 chars)."""
        return self.device_id[:8] if self.device_id else 'unknown'


_device_identity = None

def get_device_identity() -> DeviceIdentity:
    """Get or create device identity singleton."""
    global _device_identity
    if _device_identity is None:
        _device_identity = DeviceIdentity()
    return _device_identity

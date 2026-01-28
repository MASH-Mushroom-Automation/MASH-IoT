"""M.A.S.H. IoT - Device Identity Manager
Verifies device identifier against backend registry.
Device IDs are created on Admin side and flashed to IoT devices.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

IDENTITY_FILE = os.path.expanduser('~/.mash/device_id')
ACTIVATION_FILE = os.path.expanduser('~/.mash/device_activated')


class DeviceIdentity:
    """
    Manages persistent device identification and activation.
    Device ID must be pre-assigned from Admin panel - no auto-generation.
    """
    
    def __init__(self, identity_file: str = None, activation_file: str = None):
        self.identity_file = identity_file or IDENTITY_FILE
        self.activation_file = activation_file or ACTIVATION_FILE
        self.device_id = None
        self.is_activated = False
        self._load_identity()
        self._load_activation_status()
    
    def _load_identity(self):
        """Load device ID from persistent storage."""
        if os.path.exists(self.identity_file):
            try:
                with open(self.identity_file, 'r') as f:
                    self.device_id = f.read().strip()
                logger.info(f"[IDENTITY] Loaded device ID: {self.device_id[:8]}...")
                return
            except Exception as e:
                logger.error(f"[IDENTITY] Failed to load device ID: {e}")
        
        logger.warning("[IDENTITY] No device ID found - device must be provisioned from Admin panel")
    
    def _load_activation_status(self):
        """Check if device has been activated."""
        if os.path.exists(self.activation_file):
            try:
                with open(self.activation_file, 'r') as f:
                    status = f.read().strip()
                    self.is_activated = (status == 'activated')
                    if self.is_activated:
                        logger.info("[IDENTITY] Device is activated")
            except Exception as e:
                logger.warning(f"[IDENTITY] Failed to load activation status: {e}")
    
    def set_device_id(self, device_id: str) -> bool:
        """
        Set device ID (used during initial provisioning).
        
        Args:
            device_id: Pre-assigned device ID from Admin panel
        
        Returns:
            True if successfully saved
        """
        try:
            os.makedirs(os.path.dirname(self.identity_file), exist_ok=True)
            
            with open(self.identity_file, 'w') as f:
                f.write(device_id)
            
            self.device_id = device_id
            logger.info(f"[IDENTITY] Device ID set: {self.device_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"[IDENTITY] Failed to save device ID: {e}")
            return False
    
    def mark_activated(self) -> bool:
        """
        Mark device as activated after successful backend verification.
        This is done once on first boot after network setup.
        
        Returns:
            True if successfully saved
        """
        try:
            os.makedirs(os.path.dirname(self.activation_file), exist_ok=True)
            
            with open(self.activation_file, 'w') as f:
                f.write('activated')
            
            self.is_activated = True
            logger.info("[IDENTITY] Device marked as activated")
            return True
            
        except Exception as e:
            logger.error(f"[IDENTITY] Failed to save activation status: {e}")
            return False
    
    def verify_device_id(self) -> bool:
        """
        Check if device has a valid ID.
        
        Returns:
            True if device ID exists, False if not provisioned
        """
        if not self.device_id:
            logger.error("[IDENTITY] No device ID - device not provisioned")
            return False
        return True
    
    def get_id(self) -> Optional[str]:
        """Get the device ID."""
        return self.device_id
    
    def get_short_id(self) -> str:
        """Get shortened ID for display (first 8 chars)."""
        return self.device_id[:8] if self.device_id else 'unprovisioned'
    
    def is_device_activated(self) -> bool:
        """Check if device has been activated."""
        return self.is_activated
    
    def requires_activation(self) -> bool:
        """Check if device needs activation (has ID but not activated yet)."""
        return self.device_id is not None and not self.is_activated


_device_identity = None

def get_device_identity() -> DeviceIdentity:
    """Get or create device identity singleton."""
    global _device_identity
    if _device_identity is None:
        _device_identity = DeviceIdentity()
    return _device_identity

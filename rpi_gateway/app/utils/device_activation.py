"""M.A.S.H. IoT - Device Activation Flow
Handles first-boot WiFi provisioning and device activation.
"""

import logging
import time
from typing import Dict, Any, Optional, Tuple
from .identity import get_device_identity
from .wifi_manager import start_hotspot, get_wifi_list
from ..cloud.backend_api import BackendAPIClient

logger = logging.getLogger(__name__)


class DeviceActivationManager:
    """
    Manages the device activation workflow:
    1. Check if device is already activated
    2. If not, check WiFi connectivity
    3. If no WiFi, start provisioning mode
    4. Once connected, verify device with backend
    5. Activate device on backend
    6. Mark as activated locally
    """
    
    def __init__(self, backend_client: Optional[BackendAPIClient] = None):
        self.identity = get_device_identity()
        self.backend = backend_client or BackendAPIClient()
        self.activation_status = {
            'is_activated': False,
            'needs_provisioning': False,
            'needs_wifi': False,
            'error': None
        }
    
    def check_activation_status(self) -> Dict[str, Any]:
        """
        Check overall device activation status.
        
        Returns:
            dict with activation state and required actions
        """
        # Check if device ID exists
        if not self.identity.verify_device_id():
            self.activation_status['error'] = 'No device ID found - device not provisioned from Admin panel'
            self.activation_status['needs_provisioning'] = True
            logger.error("[ACTIVATION] Device has no ID - must be provisioned via Admin panel first")
            return self.activation_status
        
        # Check if already activated
        if self.identity.is_device_activated():
            self.activation_status['is_activated'] = True
            logger.info("[ACTIVATION] Device is already activated")
            return self.activation_status
        
        # Device needs activation
        self.activation_status['needs_wifi'] = True
        logger.info("[ACTIVATION] Device requires activation via network")
        return self.activation_status
    
    def check_network_connectivity(self) -> bool:
        """
        Check if device has network connectivity.
        
        Returns:
            True if network is available
        """
        try:
            # Try to reach backend health endpoint
            import requests
            response = requests.get(
                f"{self.backend.base_url}/health",
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("[ACTIVATION] Network connectivity OK")
                return True
            else:
                logger.warning("[ACTIVATION] Backend unreachable")
                return False
                
        except Exception as e:
            logger.warning(f"[ACTIVATION] Network check failed: {e}")
            return False
    
    def start_provisioning_mode(self) -> bool:
        """
        Start WiFi provisioning hotspot for user to configure network.
        
        Returns:
            True if hotspot started successfully
        """
        logger.info("[ACTIVATION] Starting WiFi provisioning mode...")
        
        try:
            success = start_hotspot()
            
            if success:
                logger.info("[ACTIVATION] Provisioning hotspot active - waiting for WiFi configuration")
                self.activation_status['needs_provisioning'] = True
            else:
                logger.error("[ACTIVATION] Failed to start provisioning hotspot")
                self.activation_status['error'] = 'Failed to start provisioning mode'
            
            return success
            
        except Exception as e:
            logger.error(f"[ACTIVATION] Provisioning mode error: {e}")
            self.activation_status['error'] = str(e)
            return False
    
    def verify_and_activate(self) -> Tuple[bool, Optional[str]]:
        """
        Verify device with backend and activate it.
        This is the critical step that happens once after WiFi is configured.
        
        Returns:
            (success, error_message)
        """
        logger.info("[ACTIVATION] Starting device verification and activation...")
        
        # Step 1: Verify device exists in backend registry
        verification_result = self.backend.verify_device()
        
        if not verification_result.get('exists'):
            error_msg = verification_result.get('error', 'Device not found in backend')
            logger.error(f"[ACTIVATION] Device verification failed: {error_msg}")
            return False, error_msg
        
        logger.info("[ACTIVATION] Device verified in backend registry")
        device_data = verification_result.get('device', {})
        
        # Step 2: Prepare network information
        network_info = self._get_network_info()
        
        # Step 3: Activate device on backend
        if not self.backend.activate_device(network_info):
            error_msg = "Failed to activate device on backend"
            logger.error(f"[ACTIVATION] {error_msg}")
            return False, error_msg
        
        logger.info("[ACTIVATION] Device activated on backend")
        
        # Step 4: Mark device as activated locally
        if not self.identity.mark_activated():
            error_msg = "Failed to save activation status locally"
            logger.error(f"[ACTIVATION] {error_msg}")
            return False, error_msg
        
        logger.info("[ACTIVATION] Device activation complete!")
        self.activation_status['is_activated'] = True
        self.activation_status['needs_wifi'] = False
        self.activation_status['needs_provisioning'] = False
        
        return True, None
    
    def _get_network_info(self) -> Dict[str, Any]:
        """
        Collect network information for device activation.
        
        Returns:
            dict with ipAddress, macAddress, etc.
        """
        network_info = {}
        
        try:
            import subprocess
            import socket
            
            # Get IP address
            try:
                hostname = socket.gethostname()
                ip_address = socket.gethostbyname(hostname)
                network_info['ipAddress'] = ip_address
            except Exception as e:
                logger.warning(f"[ACTIVATION] Could not get IP address: {e}")
            
            # Get MAC address
            try:
                result = subprocess.run(
                    ['cat', '/sys/class/net/wlan0/address'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    network_info['macAddress'] = result.stdout.strip()
            except Exception as e:
                logger.warning(f"[ACTIVATION] Could not get MAC address: {e}")
            
            # Get WiFi SSID
            try:
                result = subprocess.run(
                    ['iwgetid', '-r'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    network_info['metadata'] = {'ssid': result.stdout.strip()}
            except Exception as e:
                logger.warning(f"[ACTIVATION] Could not get SSID: {e}")
                
        except Exception as e:
            logger.error(f"[ACTIVATION] Error collecting network info: {e}")
        
        return network_info
    
    def run_activation_flow(self) -> Dict[str, Any]:
        """
        Run complete activation flow.
        This is the main entry point called on device boot.
        
        Returns:
            dict with activation result and status
        """
        logger.info("[ACTIVATION] Starting device activation flow...")
        
        # Check current activation status
        status = self.check_activation_status()
        
        # If device has no ID, cannot proceed
        if status.get('needs_provisioning') and status.get('error'):
            return {
                'success': False,
                'requires_provisioning': True,
                'error': status['error']
            }
        
        # If already activated, we're done
        if status.get('is_activated'):
            return {
                'success': True,
                'is_activated': True,
                'message': 'Device already activated'
            }
        
        # Check network connectivity
        has_network = self.check_network_connectivity()
        
        if not has_network:
            # No network - need to start provisioning
            logger.info("[ACTIVATION] No network - starting provisioning mode")
            return {
                'success': False,
                'requires_wifi_setup': True,
                'message': 'WiFi provisioning required'
            }
        
        # Network available - verify and activate
        logger.info("[ACTIVATION] Network available - proceeding with activation")
        success, error = self.verify_and_activate()
        
        if success:
            return {
                'success': True,
                'is_activated': True,
                'message': 'Device successfully activated'
            }
        else:
            return {
                'success': False,
                'error': error,
                'message': 'Activation failed'
            }


def create_activation_manager(backend_client: Optional[BackendAPIClient] = None) -> DeviceActivationManager:
    """Create and return activation manager."""
    return DeviceActivationManager(backend_client)

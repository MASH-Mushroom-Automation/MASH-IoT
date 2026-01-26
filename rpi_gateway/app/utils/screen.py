"""M.A.S.H. IoT - Screen Control Module
Manages HDMI display power for energy savings
"""

import subprocess
import logging
import os

logger = logging.getLogger(__name__)


class ScreenController:
    """
    Controls Raspberry Pi HDMI output for power management.
    Uses vcgencmd for screen on/off control.
    """
    
    def __init__(self):
        self.is_raspberry_pi = self._check_platform()
    
    def _check_platform(self) -> bool:
        """Check if running on Raspberry Pi."""
        try:
            result = subprocess.run(['which', 'vcgencmd'], 
                                    capture_output=True, 
                                    text=True,
                                    timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def turn_on(self) -> bool:
        """
        Turn on HDMI display.
        
        Returns:
            True if successful
        """
        if not self.is_raspberry_pi:
            logger.warning("[SCREEN] Not on Raspberry Pi, skipping")
            return False
        
        try:
            subprocess.run(['vcgencmd', 'display_power', '1'],
                          check=True,
                          capture_output=True,
                          timeout=5)
            logger.info("[SCREEN] Display turned ON")
            return True
            
        except Exception as e:
            logger.error(f"[SCREEN] Failed to turn on: {e}")
            return False
    
    def turn_off(self) -> bool:
        """
        Turn off HDMI display (power save mode).
        
        Returns:
            True if successful
        """
        if not self.is_raspberry_pi:
            logger.warning("[SCREEN] Not on Raspberry Pi, skipping")
            return False
        
        try:
            subprocess.run(['vcgencmd', 'display_power', '0'],
                          check=True,
                          capture_output=True,
                          timeout=5)
            logger.info("[SCREEN] Display turned OFF")
            return True
            
        except Exception as e:
            logger.error(f"[SCREEN] Failed to turn off: {e}")
            return False
    
    def get_status(self) -> str:
        """
        Get current display power status.
        
        Returns:
            'on', 'off', or 'unknown'
        """
        if not self.is_raspberry_pi:
            return 'unknown'
        
        try:
            result = subprocess.run(['vcgencmd', 'display_power'],
                                   capture_output=True,
                                   text=True,
                                   timeout=5)
            
            output = result.stdout.strip()
            
            if 'display_power=1' in output:
                return 'on'
            elif 'display_power=0' in output:
                return 'off'
            else:
                return 'unknown'
                
        except Exception as e:
            logger.error(f"[SCREEN] Status check failed: {e}")
            return 'unknown'


_screen_controller = None

def get_screen_controller() -> ScreenController:
    """Get or create screen controller singleton."""
    global _screen_controller
    if _screen_controller is None:
        _screen_controller = ScreenController()
    return _screen_controller

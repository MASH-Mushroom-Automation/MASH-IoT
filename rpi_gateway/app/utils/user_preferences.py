"""
User Preferences Manager for MASH IoT

Manages user-specific configuration that persists across reboots.
Keeps default config.yaml intact while allowing user customizations.
"""

import os
import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class UserPreferencesManager:
    """
    Manages user preferences separately from the default config.yaml.
    User preferences override default config values.
    """
    
    def __init__(self, user_config_path='config/user_preferences.yaml', default_config_path='config/config.yaml'):
        """
        Initialize the preferences manager.
        
        Args:
            user_config_path: Path to user preferences file (created if doesn't exist)
            default_config_path: Path to default config file (read-only)
        """
        self.user_config_path = user_config_path
        self.default_config_path = default_config_path
        self.user_prefs = self._load_user_preferences()
        self.default_config = self._load_default_config()
    
    def _load_default_config(self):
        """Load default configuration from config.yaml."""
        try:
            full_path = os.path.join(os.path.dirname(__file__), '..', self.default_config_path)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    return yaml.safe_load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load default config: {e}")
            return {}
    
    def _load_user_preferences(self):
        """Load user preferences from user_preferences.yaml."""
        try:
            full_path = os.path.join(os.path.dirname(__file__), '..', self.user_config_path)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    prefs = yaml.safe_load(f)
                    logger.info(f"Loaded user preferences from {self.user_config_path}")
                    return prefs if prefs else {}
            else:
                logger.info("No user preferences file found, creating new one")
                return {}
        except Exception as e:
            logger.error(f"Failed to load user preferences: {e}")
            return {}
    
    def save_user_preferences(self):
        """Save current user preferences to file."""
        try:
            full_path = os.path.join(os.path.dirname(__file__), '..', self.user_config_path)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w') as f:
                yaml.dump(self.user_prefs, f, default_flow_style=False)
            
            logger.info(f"Saved user preferences to {self.user_config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save user preferences: {e}")
            return False
    
    def get_merged_config(self):
        """
        Get configuration with user preferences merged over defaults.
        User preferences override default config values.
        """
        # Deep merge: user prefs override defaults
        merged = self._deep_merge(self.default_config.copy(), self.user_prefs)
        return merged
    
    def _deep_merge(self, base, override):
        """
        Recursively merge override dict into base dict.
        Override values take precedence.
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base
    
    def set_preference(self, path, value):
        """
        Set a user preference value at a specific path.
        
        Args:
            path: Dot-separated path (e.g., 'system.auto_mode')
            value: Value to set
        
        Example:
            set_preference('fruiting_room.temp_target', 25.0)
            set_preference('system.auto_mode', True)
        """
        keys = path.split('.')
        current = self.user_prefs
        
        # Navigate to the correct nested dict
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the value
        current[keys[-1]] = value
        
        # Save to file
        return self.save_user_preferences()
    
    def get_preference(self, path, default=None):
        """
        Get a user preference value at a specific path.
        Falls back to default config if not set in user prefs.
        
        Args:
            path: Dot-separated path (e.g., 'system.auto_mode')
            default: Default value if not found
        
        Returns:
            Value from user prefs, default config, or default parameter
        """
        # Try user prefs first
        keys = path.split('.')
        current = self.user_prefs
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                # Not in user prefs, try default config
                current = self.default_config
                for key in keys:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        return default
                return current
        
        return current
    
    def reset_to_defaults(self):
        """Clear all user preferences and revert to defaults."""
        self.user_prefs = {}
        return self.save_user_preferences()
    
    def list_user_preferences(self):
        """Get a list of all user-modified preferences."""
        return self.user_prefs

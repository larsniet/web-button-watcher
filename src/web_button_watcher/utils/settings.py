"""Settings manager for Web Button Watcher."""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SettingsManager:
    """Manages application settings."""
    
    def __init__(self, settings_file=None):
        """Initialize the settings manager.
        
        Args:
            settings_file: Optional path to settings file. If None, uses default.
        """
        if settings_file is None:
            # Use default settings file in user's home directory
            home_dir = os.path.expanduser("~")
            settings_dir = os.path.join(home_dir, ".web_button_watcher")
            
            # Create directory if it doesn't exist
            if not os.path.exists(settings_dir):
                os.makedirs(settings_dir)
                
            self.settings_file = os.path.join(settings_dir, "settings.json")
        else:
            self.settings_file = settings_file
            
        # Initialize settings
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file.
        
        Returns:
            Dictionary of settings.
        """
        if not os.path.exists(self.settings_file):
            logger.info(f"Settings file not found, creating new one at {self.settings_file}")
            return {
                'url': '',
                'refresh_interval': 5.0,
                'selected_buttons': [],
                'telegram': {
                    'api_id': '',
                    'api_hash': '',
                    'bot_token': '',
                    'chat_id': ''
                },
                'window': {
                    'position_x': None,
                    'position_y': None,
                    'width': 600,
                    'height': 900
                }
            }
        
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
                logger.debug(f"Loaded settings from {self.settings_file}")
                return settings
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return {
                'url': '',
                'refresh_interval': 5.0,
                'selected_buttons': [],
                'telegram': {
                    'api_id': '',
                    'api_hash': '',
                    'bot_token': '',
                    'chat_id': ''
                },
                'window': {
                    'position_x': None,
                    'position_y': None,
                    'width': 600,
                    'height': 900
                }
            }
    
    def _save_settings(self) -> bool:
        """Save settings to file.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
                logger.debug(f"Saved settings to {self.settings_file}")
                return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def get(self, key: str, default=None) -> Any:
        """Get a setting value.
        
        Args:
            key: Setting key.
            default: Default value if key not found.
            
        Returns:
            Setting value or default.
        """
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set a setting value.
        
        Args:
            key: Setting key.
            value: Setting value.
            
        Returns:
            True if successful, False otherwise.
        """
        self.settings[key] = value
        return self._save_settings()
    
    def update(self, settings: Dict[str, Any]) -> bool:
        """Update multiple settings.
        
        Args:
            settings: Dictionary of settings to update.
            
        Returns:
            True if successful, False otherwise.
        """
        self.settings.update(settings)
        return self._save_settings()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings.
        
        Returns:
            Dictionary of all settings.
        """
        return self.settings.copy()
    
    def get_telegram_settings(self) -> Dict[str, str]:
        """Get Telegram notification settings.
        
        Returns:
            Dictionary of Telegram settings.
        """
        return self.settings.get('telegram', {
            'api_id': '',
            'api_hash': '',
            'bot_token': '',
            'chat_id': ''
        })
    
    def update_telegram_settings(self, api_id: str, api_hash: str, bot_token: str, chat_id: str) -> bool:
        """Update Telegram notification settings.
        
        Args:
            api_id: Telegram API ID.
            api_hash: Telegram API hash.
            bot_token: Telegram bot token.
            chat_id: Telegram chat ID.
            
        Returns:
            True if successful, False otherwise.
        """
        self.settings['telegram'] = {
            'api_id': api_id,
            'api_hash': api_hash,
            'bot_token': bot_token,
            'chat_id': chat_id
        }
        return self._save_settings()

    def save_window_position(self, x: Optional[int], y: Optional[int],
                           width: Optional[int], height: Optional[int]) -> bool:
        """Save window position and size.
        
        Args:
            x: Window x position.
            y: Window y position.
            width: Window width.
            height: Window height.
            
        Returns:
            True if successful, False otherwise.
        """
        self.settings['window'] = {
            'position_x': x,
            'position_y': y,
            'width': width,
            'height': height
        }
        return self._save_settings()
    
    def get_window_settings(self) -> Dict[str, Optional[int]]:
        """Get window position and size settings.
        
        Returns:
            Dictionary of window settings.
        """
        default_settings = {
            'position_x': None,
            'position_y': None,
            'width': 600,
            'height': 900
        }
        return self.settings.get('window', default_settings) 
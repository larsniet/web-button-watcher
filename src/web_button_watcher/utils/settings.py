"""Settings management for Web Button Watcher."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class Settings:
    """Manages persistent application settings."""
    
    def __init__(self):
        """Initialize settings manager."""
        self.app_dir = self._get_app_dir()
        self.settings_file = self.app_dir / 'settings.json'
        self.settings = self.load()
    
    def _get_app_dir(self) -> Path:
        """Get or create application directory."""
        if os.name == 'nt':  # Windows
            app_dir = Path(os.getenv('APPDATA')) / 'WebButtonWatcher'
        else:  # macOS and Linux
            app_dir = Path.home() / '.config' / 'web-button-watcher'
        
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir
    
    def load(self) -> Dict[str, Any]:
        """Load settings from file."""
        default_settings = {
            'refresh_interval': 1,
            'url': '',
            'selected_buttons': [],
            'telegram': {
                'api_id': '',
                'api_hash': '',
                'bot_token': '',
                'chat_id': ''
            },
            'window': {
                'width': 600,
                'height': 700,
                'position_x': None,
                'position_y': None
            }
        }
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file) as f:
                    saved_settings = json.load(f)
                # Merge with defaults to ensure all fields exist
                return {**default_settings, **saved_settings}
            except (json.JSONDecodeError, IOError):
                return default_settings
        return default_settings
    
    def save(self) -> None:
        """Save current settings to file."""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a setting value and save."""
        self.settings[key] = value
        self.save()
    
    def update(self, settings: Dict[str, Any]) -> None:
        """Update multiple settings at once."""
        self.settings.update(settings)
        self.save()
    
    def get_telegram_settings(self) -> Dict[str, str]:
        """Get Telegram-specific settings."""
        return self.settings.get('telegram', {})
    
    def update_telegram_settings(self, api_id: str, api_hash: str, 
                               bot_token: str, chat_id: str) -> None:
        """Update Telegram settings."""
        self.settings['telegram'] = {
            'api_id': api_id,
            'api_hash': api_hash,
            'bot_token': bot_token,
            'chat_id': chat_id
        }
        self.save()
    
    def save_window_position(self, x: Optional[int], y: Optional[int],
                           width: Optional[int], height: Optional[int]) -> None:
        """Save window position and size."""
        if x is not None and y is not None:
            self.settings['window']['position_x'] = x
            self.settings['window']['position_y'] = y
        if width is not None and height is not None:
            self.settings['window']['width'] = width
            self.settings['window']['height'] = height
        self.save()
    
    def get_window_settings(self) -> Dict[str, Optional[int]]:
        """Get window position and size settings."""
        return self.settings.get('window', {
            'width': 600,
            'height': 700,
            'position_x': None,
            'position_y': None
        }) 
"""Command-line interface and core monitoring logic for Web Button Watcher."""

import asyncio
import os
from typing import List, Optional

from ..core.monitor import PageMonitor
from ..utils.notifier import TelegramNotifier
from ..utils.settings import Settings

class MonitorController:
    """Core controller for the Web Button Watcher functionality."""
    
    def __init__(self):
        self.settings_manager = Settings()
        self.monitor: Optional[PageMonitor] = None
        self.notifier: Optional[TelegramNotifier] = None
        self.running = False
    
    def update_telegram_settings(self, api_id: str, api_hash: str, bot_token: str, chat_id: str) -> None:
        """Update Telegram credentials."""
        # Update settings
        self.settings_manager.update_telegram_settings(api_id, api_hash, bot_token, chat_id)
        
        # Update environment variables for current session
        os.environ['TELEGRAM_API_ID'] = api_id
        os.environ['TELEGRAM_API_HASH'] = api_hash
        os.environ['TELEGRAM_BOT_TOKEN'] = bot_token
        os.environ['TELEGRAM_CHAT_ID'] = chat_id
    
    def select_buttons(self, url: str) -> List[int]:
        """Open browser for interactive button selection."""
        monitor = PageMonitor(url)
        selected = monitor.select_buttons_interactive()
        if monitor.driver:
            monitor.driver.quit()
        
        # Save selected buttons to settings
        if selected:
            self.settings_manager.set('selected_buttons', selected)
            self.settings_manager.set('url', url)
        
        return selected
    
    def start_monitoring(self, url: str, refresh_interval: float, selected_buttons: List[int],
                        status_callback=None) -> None:
        """Start the monitoring process."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Save current monitoring settings
            self.settings_manager.update({
                'url': url,
                'refresh_interval': refresh_interval,
                'selected_buttons': selected_buttons
            })
            
            # Create notifier using saved Telegram settings
            telegram_settings = self.settings_manager.get_telegram_settings()
            if all(telegram_settings.values()):
                self.notifier = TelegramNotifier()
            
            # Create and setup monitor
            self.monitor = PageMonitor(url, refresh_interval=refresh_interval, notifier=self.notifier)
            self.monitor.setup_driver()
            self.monitor.target_buttons = selected_buttons
            
            # Start monitoring
            self.running = True
            if status_callback:
                status_callback(f"Monitoring buttons: {[x+1 for x in selected_buttons]}")
            
            self.monitor.monitor()
            
        except Exception as e:
            if status_callback:
                status_callback(f"Monitor error: {str(e)}")
            raise
        finally:
            self.running = False
            if 'loop' in locals():
                loop.close()
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring process."""
        self.running = False
        if self.monitor and self.monitor.driver:
            self.monitor.driver.quit()
            self.monitor = None 
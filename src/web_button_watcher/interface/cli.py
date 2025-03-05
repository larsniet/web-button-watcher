"""Command-line interface for Web Button Watcher."""

import logging
import time
import asyncio
from typing import List, Dict, Any, Optional
from ..core.driver_manager import DriverManager
from ..core.button_selector import ButtonSelector
from ..core.button_monitor import ButtonMonitor
from ..utils.settings import SettingsManager
from ..utils.notifier import TelegramNotifier

logger = logging.getLogger(__name__)

class MonitorController:
    """Controls the monitoring process via CLI."""
    
    def __init__(self):
        """Initialize the monitor controller."""
        self.settings_manager = SettingsManager()
        self.driver_manager = None
        self.button_selector = None
        self.button_monitor = None
        self.notifier = None
        self.running = False
        self.status_callback = None
    
    def update_telegram_settings(self, api_id: str, api_hash: str, bot_token: str, chat_id: str) -> None:
        """Update Telegram notification settings."""
        self.settings_manager.update_telegram_settings(api_id, api_hash, bot_token, chat_id)
        logger.info("Updated Telegram settings")
    
    def select_buttons(self, url: str) -> List[int]:
        """Select buttons to monitor on the specified URL.
        
        Args:
            url: The URL to select buttons from.
            
        Returns:
            List of selected button indices.
        """
        try:
            # Initialize driver manager if needed
            if not self.driver_manager:
                self.driver_manager = DriverManager()
            
            # Navigate to URL
            self.driver_manager.navigate_to(url)
            
            # Create button selector
            self.button_selector = ButtonSelector(self.driver_manager)
            
            # Select buttons interactively
            selected = self.button_selector.select_buttons_interactive()
            
            # Save selected buttons to settings
            if selected:
                self.settings_manager.set('selected_buttons', selected)
                self.settings_manager.set('url', url)
            
            # Close the browser after selection
            if self.driver_manager:
                self.driver_manager.cleanup()
                self.driver_manager = None
            
            return selected
        except Exception as e:
            logger.error(f"Error during button selection: {e}")
            raise
    
    def start_monitoring(self, url: str, refresh_interval: float, selected_buttons: List[int]) -> None:
        """Start the monitoring process.
        
        Args:
            url: The URL to monitor.
            refresh_interval: How often to refresh the page (in seconds).
            selected_buttons: List of button indices to monitor.
        """
        try:
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
            
            # Initialize driver manager if needed
            if not self.driver_manager:
                self.driver_manager = DriverManager()
                self.driver_manager.navigate_to(url)
            
            # Create button monitor
            self.button_monitor = ButtonMonitor(
                self.driver_manager,
                refresh_interval=refresh_interval,
                notifier=self.notifier,
                status_callback=self.status_callback
            )
            
            # Set target buttons
            self.button_monitor.set_target_buttons(selected_buttons)
            
            # Start monitoring
            self.running = True
            
            # Log status if callback is set
            if self.status_callback:
                self.status_callback(f"Starting to monitor {len(selected_buttons)} buttons on {url}")
                
            self.button_monitor.start_monitoring()
            
        except Exception as e:
            logger.error(f"Error during monitoring: {e}")
            if self.status_callback:
                self.status_callback(f"Error during monitoring: {e}")
            raise
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring process."""
        if self.button_monitor:
            self.button_monitor.stop_monitoring()
        
        self.running = False
        
        # Close the browser
        if self.driver_manager:
            self.driver_manager.cleanup()
            self.driver_manager = None
            
        if self.status_callback:
            self.status_callback("Monitoring stopped. Browser closed.")
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop_monitoring()
        
        if self.driver_manager:
            self.driver_manager.cleanup()
            self.driver_manager = None
    
    def run(self) -> None:
        """Run the monitor controller in interactive mode."""
        print("\nWeb Button Watcher")
        print("=================")
        
        try:
            # Load settings
            settings = self.settings_manager.get_all()
            url = settings.get('url', '')
            refresh_interval = settings.get('refresh_interval', 5.0)
            selected_buttons = settings.get('selected_buttons', [])
            
            # Ask for URL if not saved
            if not url:
                url = input("\nEnter URL to monitor: ")
                if not url:
                    print("No URL provided. Exiting.")
                    return
            
            # Ask if user wants to select buttons or use saved ones
            if selected_buttons:
                print(f"\nFound {len(selected_buttons)} previously selected buttons for {url}")
                choice = input("Use these buttons? (y/n): ").lower()
                
                if choice != 'y':
                    selected_buttons = self.select_buttons(url)
                    if not selected_buttons:
                        print("No buttons selected. Exiting.")
                        return
            else:
                print(f"\nNo buttons selected for {url}")
                selected_buttons = self.select_buttons(url)
                if not selected_buttons:
                    print("No buttons selected. Exiting.")
                    return
            
            # Ask for refresh interval
            try:
                refresh_input = input(f"\nRefresh interval in seconds (default: {refresh_interval}): ")
                if refresh_input:
                    refresh_interval = float(refresh_input)
            except ValueError:
                print(f"Invalid input. Using default: {refresh_interval} seconds.")
            
            # Start monitoring
            print(f"\nStarting to monitor {len(selected_buttons)} buttons on {url}")
            print("Press Ctrl+C to stop.")
            
            self.start_monitoring(url, refresh_interval, selected_buttons)
            
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")
        except Exception as e:
            logger.exception(f"Error in run: {e}")
            print(f"\nAn error occurred: {e}")
        finally:
            self.cleanup()

    def set_status_callback(self, callback):
        """Set a callback function for status updates.
        
        Args:
            callback: Function to call with status updates.
        """
        self.status_callback = callback
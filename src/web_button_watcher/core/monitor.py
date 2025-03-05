"""Main module for Web Button Watcher."""

import logging
import time
import atexit
from .driver_manager import DriverManager
from .button_selector import ButtonSelector
from .button_monitor import ButtonMonitor

logger = logging.getLogger(__name__)

class PageMonitor:
    """Monitors a web page for button changes."""
    
    def __init__(self, url, refresh_interval=1, notifier=None):
        """Initialize the page monitor.
        
        Args:
            url: The URL to monitor.
            refresh_interval: How often to refresh the page (in seconds).
            notifier: Optional notifier to send alerts.
        """
        self.url = url
        self.refresh_interval = refresh_interval
        self.notifier = notifier
        self.driver_manager = DriverManager()
        self.button_selector = ButtonSelector(self.driver_manager)
        self.button_monitor = ButtonMonitor(self.driver_manager, refresh_interval, notifier)
        self.target_buttons = []
        self.running = False
        
        # Register cleanup on exit
        atexit.register(self.cleanup)
    
    def setup_driver(self):
        """Initialize the driver and navigate to the URL."""
        self.driver_manager.initialize_driver()
        self.driver_manager.navigate_to(self.url)
        return self.driver_manager.driver
    
    def select_buttons_interactive(self):
        """Allow user to select buttons by clicking them.
        
        Returns:
            List of selected button indices.
        """
        # Make sure driver is initialized and on the right page
        self.setup_driver()
        
        # Use the button selector to handle selection
        selected_indices = self.button_selector.select_buttons_interactive()
        
        if selected_indices:
            self.target_buttons = selected_indices
            
        return selected_indices
    
    def get_button_texts(self):
        """Get the text of the selected buttons.
        
        Returns:
            Dictionary mapping button indices to their text.
        """
        return self.button_selector.get_button_texts(self.target_buttons)
    
    def start(self, target_buttons=None):
        """Start monitoring the page for button changes.
        
        Args:
            target_buttons: Optional list of button indices to monitor.
                If not provided, uses previously selected buttons.
        """
        if target_buttons is not None:
            self.target_buttons = target_buttons
        
        if not self.target_buttons:
            logger.error("No buttons selected for monitoring")
            print("\nError: No buttons selected for monitoring. Please select buttons first.")
            return
        
        # Make sure driver is initialized and on the right page
        if not self.driver_manager.driver:
            self.setup_driver()
        
        # Set target buttons on the monitor
        self.button_monitor.set_target_buttons(self.target_buttons)
        
        # Start monitoring
        self.running = True
        self.button_monitor.start_monitoring()
    
    def monitor(self):
        """Monitor the page for button changes."""
        # This is now just a wrapper around start() for backward compatibility
        self.start()
    
    def stop(self):
        """Stop monitoring."""
        self.running = False
        self.button_monitor.stop_monitoring()
    
    def cleanup(self):
        """Clean up resources."""
        self.stop()
        self.driver_manager.cleanup()


def main():
    """Main entry point for the application."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor buttons on a web page for changes")
    parser.add_argument("url", help="URL of the page to monitor")
    parser.add_argument("--interval", type=float, default=1, help="Refresh interval in seconds")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    try:
        # Create monitor
        monitor = PageMonitor(args.url, args.interval)
        
        # Select buttons
        print(f"\nOpening {args.url} to select buttons...")
        selected = monitor.select_buttons_interactive()
        
        if not selected:
            print("\nNo buttons selected. Exiting.")
            monitor.cleanup()
            return
        
        # Start monitoring
        monitor.start(selected)
        
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\nError: {e}")
    finally:
        # Cleanup will be called by atexit handler
        pass


if __name__ == "__main__":
    main() 
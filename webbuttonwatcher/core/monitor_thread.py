import time
import logging
import threading
from datetime import datetime
from PyQt5.QtCore import pyqtSignal, QObject

from .driver_manager import DriverManager
from ..utils.config import Config

logger = logging.getLogger(__name__)

class MonitorSignals(QObject):
    """Signals for the MonitorThread class."""
    status_changed = pyqtSignal(str)
    button_found = pyqtSignal(str)
    button_clicked = pyqtSignal(str)
    monitor_started = pyqtSignal()
    monitor_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str)

class MonitorThread(threading.Thread):
    """Thread for monitoring a webpage for a specific button."""
    
    def __init__(self, url, button_text, button_identifiers=None, refresh_interval=30, auto_click=False):
        """Initialize the MonitorThread."""
        super().__init__()
        self.url = url
        self.button_text = button_text
        self.button_identifiers = button_identifiers or []
        self.refresh_interval = refresh_interval
        self.auto_click = auto_click
        self.running = False
        self.driver_manager = None
        self.signals = MonitorSignals()
        self.daemon = True
        
        logger.info(f"MonitorThread initialized for URL: {url}, button: {button_text}")
    
    def run(self):
        """Run the monitor thread."""
        try:
            self.running = True
            self.signals.monitor_started.emit()
            self.signals.status_changed.emit(f"Starting monitor for {self.button_text} on {self.url}")
            
            # Initialize the driver
            self.driver_manager = DriverManager()
            
            # Navigate to the URL
            if not self.driver_manager.navigate_to(self.url):
                self.signals.error_occurred.emit(f"Failed to navigate to {self.url}")
                self.running = False
                self.signals.monitor_stopped.emit()
                return
            
            self.signals.status_changed.emit(f"Monitoring for {self.button_text} on {self.url}")
            
            # Main monitoring loop
            while self.running:
                try:
                    # Look for the button
                    self.signals.status_changed.emit(f"Looking for button: {self.button_text}")
                    button = self.driver_manager.find_button(self.button_text, self.button_identifiers)
                    
                    if button:
                        # Button found
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.signals.button_found.emit(f"Button found at {now}")
                        self.signals.status_changed.emit(f"Button found: {self.button_text}")
                        
                        # Click the button if auto_click is enabled
                        if self.auto_click:
                            self.signals.status_changed.emit(f"Attempting to click button: {self.button_text}")
                            
                            if self.driver_manager.click_button(button):
                                self.signals.button_clicked.emit(f"Button clicked at {now}")
                                self.signals.status_changed.emit(f"Button clicked: {self.button_text}")
                                
                                # If button is clicked, we can stop monitoring if configured to do so
                                if Config.get_instance().get('general', 'stop_after_click', fallback=False):
                                    self.signals.status_changed.emit("Monitoring stopped after clicking button")
                                    self.running = False
                                    break
                            else:
                                self.signals.error_occurred.emit("Failed to click button")
                    else:
                        # Button not found, refresh after the interval
                        self.signals.status_changed.emit(f"Button not found, refreshing in {self.refresh_interval} seconds")
                    
                    # Wait for the specified interval before refreshing
                    interval_counter = 0
                    while interval_counter < self.refresh_interval and self.running:
                        time.sleep(1)
                        interval_counter += 1
                    
                    # Refresh the page if still running
                    if self.running:
                        self.signals.status_changed.emit("Refreshing page")
                        
                        if not self.driver_manager.refresh_page():
                            # If refresh fails, try to navigate to the URL again
                            self.signals.status_changed.emit(f"Refresh failed, navigating to {self.url} again")
                            
                            if not self.driver_manager.navigate_to(self.url):
                                self.signals.error_occurred.emit(f"Failed to navigate to {self.url}")
                                break
                
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    self.signals.error_occurred.emit(f"Error monitoring: {str(e)}")
                    
                    # Try to recover by navigating to the URL again
                    try:
                        self.signals.status_changed.emit(f"Attempting to recover, navigating to {self.url}")
                        
                        if not self.driver_manager.navigate_to(self.url):
                            self.signals.error_occurred.emit(f"Failed to recover")
                            break
                    except Exception as recovery_error:
                        logger.error(f"Recovery failed: {recovery_error}")
                        self.signals.error_occurred.emit(f"Recovery failed: {str(recovery_error)}")
                        break
            
        except Exception as e:
            logger.error(f"MonitorThread encountered an error: {e}")
            self.signals.error_occurred.emit(f"Monitor error: {str(e)}")
        
        finally:
            # Cleanup
            self.running = False
            if self.driver_manager:
                try:
                    self.driver_manager.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up driver: {e}")
            
            self.signals.status_changed.emit("Monitoring stopped")
            self.signals.monitor_stopped.emit()
            logger.info("MonitorThread terminated")
    
    def stop(self):
        """Stop the monitoring thread."""
        logger.info("Stopping MonitorThread")
        self.running = False 
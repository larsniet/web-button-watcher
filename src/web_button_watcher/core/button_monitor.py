"""Button monitor for Web Button Watcher."""

import logging
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

logger = logging.getLogger(__name__)

class ButtonMonitor:
    """Monitors buttons for changes."""
    
    def __init__(self, driver_manager, refresh_interval=1, notifier=None, status_callback=None):
        """Initialize the button monitor.
        
        Args:
            driver_manager: The driver manager instance.
            refresh_interval: How often to refresh the page (in seconds).
            notifier: Optional notifier to send alerts.
            status_callback: Optional callback for status updates.
        """
        self.driver_manager = driver_manager
        self.refresh_interval = refresh_interval
        self.notifier = notifier
        self.status_callback = status_callback
        self.target_buttons = []
        self.original_texts = {}
        self.is_running = False
        self.highlight_css = """
            .monitored-button {
                box-shadow: 0 0 0 3px #ff9800 !important;
                position: relative !important;
            }
            .monitored-button::after {
                content: '👁️' !important;
                position: absolute !important;
                top: -20px !important;
                right: -10px !important;
                background: #ff9800 !important;
                color: white !important;
                border-radius: 50% !important;
                width: 20px !important;
                height: 20px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                font-size: 12px !important;
            }
        """
    
    def set_target_buttons(self, button_indices):
        """Set the buttons to monitor.
        
        Args:
            button_indices: List of button indices to monitor.
        """
        self.target_buttons = button_indices
        logger.info(f"Set target buttons: {button_indices}")
    
    def store_original_texts(self):
        """Store the original text of target buttons."""
        if not self.target_buttons:
            logger.warning("No target buttons set")
            return
        
        buttons = self.driver_manager.find_elements(By.TAG_NAME, "button")
        
        for idx in self.target_buttons:
            if idx < len(buttons):
                self.original_texts[idx] = buttons[idx].text
                logger.debug(f"Stored original text for button {idx}: '{self.original_texts[idx]}'")
            else:
                logger.warning(f"Button index {idx} is out of range")
    
    def highlight_monitored_buttons(self):
        """Highlight the buttons being monitored."""
        if not self.target_buttons:
            return
        
        # Inject CSS for highlighting
        self.driver_manager.inject_css(self.highlight_css)
        
        # Add class to monitored buttons
        script = """
            const buttons = document.querySelectorAll('button');
            const indices = arguments[0];
            
            // Remove existing highlights
            document.querySelectorAll('.monitored-button').forEach(el => {
                el.classList.remove('monitored-button');
            });
            
            // Add highlights to target buttons
            indices.forEach(idx => {
                if (buttons[idx]) {
                    buttons[idx].classList.add('monitored-button');
                }
            });
        """
        
        self.driver_manager.execute_script(script, self.target_buttons)
    
    def check_button_changes(self):
        """Check if any monitored buttons have changed.
        
        Returns:
            List of tuples (button_index, old_text, new_text) for changed buttons.
        """
        if not self.target_buttons or not self.original_texts:
            return []
        
        changes = []
        buttons = self.driver_manager.find_elements(By.TAG_NAME, "button")
        
        for idx in self.target_buttons:
            if idx >= len(buttons):
                logger.warning(f"Button index {idx} is out of range")
                continue
                
            if idx not in self.original_texts:
                logger.warning(f"No original text stored for button {idx}")
                continue
                
            current_text = buttons[idx].text
            original_text = self.original_texts[idx]
            
            if current_text != original_text:
                logger.info(f"Button {idx} changed: '{original_text}' -> '{current_text}'")
                changes.append((idx, original_text, current_text))
        
        return changes
    
    def notify_changes(self, changes):
        """Send notifications for button changes.
        
        Args:
            changes: List of tuples (button_index, old_text, new_text).
        """
        if not changes:
            return
            
        if not self.notifier:
            # Print to console if no notifier
            for idx, old_text, new_text in changes:
                print(f"\n🔔 Button {idx+1} changed: '{old_text}' -> '{new_text}'")
            return
            
        # Use notifier if available
        for idx, old_text, new_text in changes:
            message = f"🔔 Button {idx+1} changed:\nFrom: '{old_text}'\nTo: '{new_text}'"
            try:
                self.notifier.send_notification(message)
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
                print(f"\n🔔 Button {idx+1} changed: '{old_text}' -> '{new_text}'")
    
    def start_monitoring(self):
        """Start monitoring the target buttons."""
        if not self.target_buttons:
            logger.warning("No target buttons set")
            print("\nNo buttons selected for monitoring.")
            if self.status_callback:
                self.status_callback("No buttons selected for monitoring.")
            return
        
        self.is_running = True
        logger.info(f"Starting monitoring of {len(self.target_buttons)} buttons")
        print(f"\nStarting to monitor {len(self.target_buttons)} buttons.")
        print("Press Ctrl+C to stop monitoring.")
        
        if self.status_callback:
            self.status_callback(f"Starting to monitor {len(self.target_buttons)} buttons.")
        
        # Store original texts if not already done
        if not self.original_texts:
            self.store_original_texts()
        
        try:
            while self.is_running:
                try:
                    # Refresh the page
                    self.driver_manager.refresh_page()
                    
                    # Highlight monitored buttons
                    self.highlight_monitored_buttons()
                    
                    # Check for changes
                    changes = self.check_button_changes()
                    
                    # Notify if changes detected
                    if changes:
                        self.notify_changes(changes)
                        
                        # Update original texts to avoid repeated notifications
                        for idx, _, new_text in changes:
                            self.original_texts[idx] = new_text
                    
                    # Wait before next check
                    time.sleep(self.refresh_interval)
                    
                except WebDriverException as e:
                    logger.error(f"WebDriver error during monitoring: {e}")
                    print("\nBrowser error. Attempting to recover...")
                    
                    if self.status_callback:
                        self.status_callback(f"Browser error: {e}. Attempting to recover...")
                    
                    # Try to recover by reinitializing the driver
                    try:
                        self.driver_manager.navigate_to(self.driver_manager.url)
                        self.store_original_texts()  # Re-store original texts
                        
                        if self.status_callback:
                            self.status_callback("Recovery successful. Continuing monitoring.")
                    except Exception as e2:
                        logger.error(f"Failed to recover from WebDriver error: {e2}")
                        print("\nFailed to recover. Stopping monitoring.")
                        
                        if self.status_callback:
                            self.status_callback(f"Failed to recover: {e2}. Stopping monitoring.")
                        
                        self.is_running = False
                        break
                
                except Exception as e:
                    logger.error(f"Error during monitoring: {e}")
                    print(f"\nError: {e}")
                    
                    if self.status_callback:
                        self.status_callback(f"Error during monitoring: {e}")
                    
                    time.sleep(self.refresh_interval)
            
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
            print("\nMonitoring stopped.")
            
            if self.status_callback:
                self.status_callback("Monitoring stopped by user.")
        
        self.is_running = False
    
    def stop_monitoring(self):
        """Stop the monitoring process."""
        self.is_running = False
        logger.info("Monitoring stopped") 
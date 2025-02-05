"""Core monitoring functionality for Web Button Watcher."""

import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from ..utils.notifier import TelegramNotifier
import atexit
from selenium.common.exceptions import WebDriverException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class PageMonitor:
    def __init__(self, url, refresh_interval=1, notifier=None):
        """Initialize the page monitor."""
        self.url = url
        self.refresh_interval = refresh_interval
        self.driver = None
        self.target_buttons = []
        self.notifier = notifier
        self.button_texts = {}  # Store original button texts
        self.is_running = False
        
        # Register cleanup on program exit
        atexit.register(self.cleanup)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def inject_css(self):
        """Inject the required CSS styles into the page."""
        self.driver.execute_script("""
            if (!document.getElementById('monitor-styles')) {
                var style = document.createElement('style');
                style.id = 'monitor-styles';
                style.innerHTML = `
                    .button-container {
                        position: relative;
                        display: inline-block;
                    }
                    .button-number {
                        position: absolute;
                        top: -25px;
                        left: 0;
                        font-weight: bold;
                        background-color: #fefefe;
                        color: #000;
                        font-size: 12px;
                        z-index: 1000;
                        border-radius: 9999px;
                        padding: 10px;
                        border: 1px solid #000;
                        line-height: 1;
                    }
                `;
                document.head.appendChild(style);
            }
        """)

    def cleanup(self):
        """Safely cleanup browser resources."""
        try:
            # Stop the monitor first
            self.is_running = False
            
            # Wait for monitor thread to finish if it exists
            if hasattr(self, 'monitor_thread') and self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join()
            
            if self.driver:
                try:
                    # Try to close any alert that might be present
                    try:
                        alert = self.driver.switch_to.alert
                        alert.accept()
                    except:
                        pass
                    
                    # Close all windows
                    for handle in self.driver.window_handles:
                        self.driver.switch_to.window(handle)
                        self.driver.close()
                except WebDriverException:
                    pass
                
                try:
                    self.driver.quit()
                except WebDriverException:
                    pass
                
                self.driver = None
        except Exception as e:
            logging.debug(f"Cleanup error (can be ignored): {e}")

    def setup_driver(self):
        """Set up the Chrome driver with appropriate options."""
        try:
            # Cleanup any existing session first
            self.cleanup()
            
            options = uc.ChromeOptions()
            options.add_argument('--start-maximized')
            self.driver = uc.Chrome(options=options, version_main=131)
            self.driver.get(self.url)
            self.inject_css()
            return self.driver
        except Exception as e:
            logging.error(f"Failed to initialize Chrome driver: {e}")
            self.cleanup()
            raise
    
    def highlight_element(self, element, color="yellow"):
        """Highlight an element on the page."""
        try:
            self.driver.execute_script("""
                arguments[0].style.backgroundColor = arguments[1];
            """, element, color)
        except Exception as e:
            logging.error(f"Failed to highlight element: {e}")
    
    def add_button_number(self, element, number):
        """Add a number label above the button."""
        try:
            self.driver.execute_script("""
                // Check if button is already wrapped
                if (!arguments[0].parentElement.classList.contains('button-container')) {
                    // Create container
                    var container = document.createElement('div');
                    container.className = 'button-container';
                    
                    // Wrap button in container
                    arguments[0].parentNode.insertBefore(container, arguments[0]);
                    container.appendChild(arguments[0]);
                    
                    // Add number label
                    var span = document.createElement('span');
                    span.className = 'button-number';
                    span.textContent = arguments[1];
                    container.appendChild(span);
                }
            """, element, str(number))
        except Exception as e:
            logging.error(f"Failed to add button number: {e}")
    
    def get_available_buttons(self):
        """Get list of buttons with 'GET NOTIFIED' text."""
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        notify_buttons = []
        notify_count = 1  # Counter just for GET NOTIFIED buttons
        
        for i, button in enumerate(buttons):
            if button.text == "GET NOTIFIED":
                notify_buttons.append(i)
                # Add button number starting from 1 for GET NOTIFIED buttons
                self.add_button_number(button, notify_count)
                notify_count += 1
        return notify_buttons
    
    def select_buttons(self):
        """Let user select which buttons to monitor."""
        notify_buttons = self.get_available_buttons()
        print("\nAvailable 'GET NOTIFIED' buttons:")
        for i, btn_index in enumerate(notify_buttons):
            print(f"{i + 1}. Button {i + 1}")  # Show 1-based indexing
        
        while True:
            try:
                input_str = input("\nEnter the button numbers to monitor (comma-separated, e.g., '2,4'): ")
                selected = [int(x.strip()) for x in input_str.split(',')]
                
                # Convert selection to button indices
                self.target_buttons = [notify_buttons[x-1] for x in selected if 1 <= x <= len(notify_buttons)]
                if self.target_buttons:
                    break
                print(f"Please enter valid button numbers between 1 and {len(notify_buttons)}")
            except (ValueError, IndexError):
                print("Please enter valid numbers separated by commas")
    
    def select_buttons_interactive(self):
        """Allow user to select buttons by clicking them."""
        if not self.driver:
            self.setup_driver()
            
        # Find all buttons first
        buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
        if not buttons:
            raise ValueError("No buttons found on the page")
        
        # Add selection UI styles
        self.driver.execute_script("""
            if (!document.getElementById('selection-styles')) {
                var style = document.createElement('style');
                style.id = 'selection-styles';
                style.innerHTML = `
                    .button-wrapper {
                        position: relative !important;
                        display: inline-block !important;
                    }
                    .button-overlay {
                        position: absolute !important;
                        top: 0 !important;
                        left: 0 !important;
                        right: 0 !important;
                        bottom: 0 !important;
                        background: transparent !important;
                        cursor: pointer !important;
                        z-index: 99999 !important;
                    }
                    .button-number {
                        position: absolute !important;
                        top: -20px !important;
                        left: 50% !important;
                        transform: translateX(-50%) !important;
                        background: #000 !important;
                        color: #fff !important;
                        padding: 2px 6px !important;
                        border-radius: 10px !important;
                        font-size: 12px !important;
                        z-index: 100000 !important;
                    }
                    .button-overlay.selected {
                        background: rgba(0, 255, 0, 0.2) !important;
                        box-shadow: 0 0 0 3px #00ff00 !important;
                    }
                    .button-overlay:hover:not(.selected) {
                        background: rgba(0, 255, 0, 0.1) !important;
                    }
                    .selection-header {
                        position: fixed !important;
                        top: 0 !important;
                        left: 0 !important;
                        right: 0 !important;
                        background: rgba(0, 0, 0, 0.8) !important;
                        color: white !important;
                        padding: 10px !important;
                        text-align: center !important;
                        z-index: 100001 !important;
                    }
                    .selection-buttons {
                        margin-top: 10px !important;
                    }
                    .selection-button {
                        padding: 5px 15px !important;
                        margin: 0 5px !important;
                        cursor: pointer !important;
                        background: #4CAF50 !important;
                        border: none !important;
                        color: white !important;
                        border-radius: 3px !important;
                    }
                `;
                document.head.appendChild(style);
            }
        """)
        
        # Initialize selection and wrap buttons
        self.driver.execute_script("""
            // Initialize selection state
            window.selectedButtons = [];
            window.selectionConfirmed = false;
            
            // Add selection header
            const header = document.createElement('div');
            header.className = 'selection-header';
            header.innerHTML = `
                <div>Click on any buttons you want to monitor for changes (click again to unselect)</div>
                <div class="selection-buttons">
                    <button class="selection-button" id="confirm-selection">Confirm Selection</button>
                    <button class="selection-button" id="clear-selection">Clear Selection</button>
                </div>
            `;
            document.body.appendChild(header);
            
            // Function to wrap a button
            function wrapButton(button, index) {
                // Create wrapper
                const wrapper = document.createElement('div');
                wrapper.className = 'button-wrapper';
                
                // Add button number
                const numberLabel = document.createElement('div');
                numberLabel.className = 'button-number';
                numberLabel.textContent = (index + 1).toString();
                
                // Create overlay
                const overlay = document.createElement('div');
                overlay.className = 'button-overlay';
                
                // Prevent any click events from reaching the button
                overlay.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    
                    if (overlay.classList.contains('selected')) {
                        // Deselect
                        overlay.classList.remove('selected');
                        window.selectedButtons = window.selectedButtons.filter(i => i !== index);
                    } else {
                        // Select
                        overlay.classList.add('selected');
                        window.selectedButtons.push(index);
                        window.selectedButtons.sort((a, b) => a - b);
                    }
                    console.log('Selected buttons:', window.selectedButtons);
                    return false;
                }, true);
                
                // Wrap the button
                button.parentNode.insertBefore(wrapper, button);
                wrapper.appendChild(button);
                wrapper.appendChild(overlay);
                wrapper.appendChild(numberLabel);
                
                // Disable the original button
                button.style.pointerEvents = 'none';
                ['onclick', 'onmousedown', 'onmouseup', 'onmouseover'].forEach(attr => {
                    button.removeAttribute(attr);
                });
            }
            
            // Get all buttons except our UI control buttons
            let buttonIndex = 0;
            document.querySelectorAll('button').forEach((button) => {
                // Skip our own UI buttons
                if (!button.classList.contains('selection-button')) {
                    wrapButton(button, buttonIndex);
                    buttonIndex++;
                }
            });
            
            // Add confirm handler
            document.getElementById('confirm-selection').addEventListener('click', () => {
                if (window.selectedButtons.length > 0) {
                    window.selectionConfirmed = true;
                } else {
                    alert('Please select at least one button before confirming.');
                }
            });
            
            // Add clear handler
            document.getElementById('clear-selection').addEventListener('click', () => {
                window.selectedButtons = [];
                document.querySelectorAll('.button-overlay.selected').forEach(overlay => {
                    overlay.classList.remove('selected');
                });
            });
        """)
        
        # Wait for user to confirm selection
        try:
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script("return window.selectionConfirmed === true;")
            )
            
            # Get selected buttons
            selected = self.driver.execute_script("return window.selectedButtons;")
            
            if selected and len(selected) > 0:
                self.target_buttons = sorted(selected)
                
                # Store original button texts
                buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
                for i in self.target_buttons:
                    if i < len(buttons):
                        self.button_texts[i] = buttons[i].text
                
                print("\nSelected buttons:")
                for i in self.target_buttons:
                    print(f"Button {i+1}: '{self.button_texts[i]}'")
            else:
                print("No buttons were selected")
            
            # Clean up UI but keep the page open
            self.driver.execute_script("""
                document.querySelector('.selection-header').remove();
            """)
            
            return self.target_buttons
            
        except Exception as e:
            logging.error(f"Error during button selection: {e}")
            raise
    
    def monitor(self):
        """Monitor the page for button changes."""
        if not self.driver:
            self.setup_driver()
        
        # Validate that buttons are selected
        if not self.target_buttons:
            raise ValueError("No buttons selected for monitoring. Please select at least one button first.")
        
        print(f"\nMonitoring {len(self.target_buttons)} buttons...")
        print("\nWatching for changes...")
        
        self.is_running = True
        try:
            refresh_count = 0
            while self.is_running:
                try:
                    refresh_count += 1
                    print(f"\rRefresh #{refresh_count}", end="", flush=True)
                    
                    if not self.is_running:
                        break
                    
                    # Refresh the page
                    try:
                        self.driver.get(self.url)
                    except WebDriverException as e:
                        if not self.is_running:
                            break
                        logging.debug(f"Page refresh error (retrying): {e}")
                        time.sleep(self.refresh_interval)
                        continue
                    
                    # Wait for buttons to load
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button:not(.selection-button)"))
                        )
                    except WebDriverException:
                        if not self.is_running:
                            break
                        continue
                    
                    # Add styles for monitored buttons
                    self.driver.execute_script("""
                        if (!document.getElementById('monitor-styles')) {
                            var style = document.createElement('style');
                            style.id = 'monitor-styles';
                            style.innerHTML = `
                                .monitored-button {
                                    border: 2px solid #00ff00 !important;
                                    box-shadow: 0 0 5px rgba(0,255,0,0.5) !important;
                                }
                            `;
                            document.head.appendChild(style);
                        }
                        
                        // Clear any existing highlights
                        document.querySelectorAll('.monitored-button').forEach(button => {
                            button.classList.remove('monitored-button');
                        });
                        
                        // Get all non-UI buttons
                        let buttons = Array.from(document.querySelectorAll('button')).filter(
                            button => !button.classList.contains('selection-button')
                        );
                        
                        // Highlight monitored buttons
                        let targetButtons = arguments[0];
                        targetButtons.forEach(index => {
                            if (index < buttons.length) {
                                buttons[index].classList.add('monitored-button');
                            }
                        });
                    """, self.target_buttons)
                    
                    # Check for changes
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, "button:not(.selection-button)")
                    for button_index in self.target_buttons:
                        if button_index < len(buttons):
                            try:
                                current_text = buttons[button_index].text
                                original_text = self.button_texts[button_index]
                                if current_text != original_text:
                                    print(f"\nButton {button_index + 1} changed from '{original_text}' to '{current_text}'")
                                    
                                    # Send notification if notifier is available
                                    if self.notifier:
                                        self.notifier.notify_button_clicked(button_index + 1, current_text)
                                    
                                    print("\nButton changed! Browser will stay open.")
                                    print("Press Ctrl+C when you want to close the browser.")
                                    while self.is_running:
                                        time.sleep(1)  # Keep browser open until user interrupts
                            except KeyError:
                                logging.debug(f"Button index {button_index} not found in stored texts")
                                continue
                            except Exception as e:
                                logging.debug(f"Error checking button {button_index}: {e}")
                                continue
                    
                    if not self.is_running:
                        break
                    
                    time.sleep(self.refresh_interval)
                    
                except Exception as e:
                    if not self.is_running:
                        break
                    logging.debug(f"Error during refresh (retrying): {e}")
                    time.sleep(self.refresh_interval)
                    continue
                
        except KeyboardInterrupt:
            print("\nMonitoring interrupted by user")
        except Exception as e:
            logging.error(f"Error during monitoring: {e}")
        finally:
            self.is_running = False
            self.cleanup()

    def stop(self):
        """Stop monitoring and cleanup resources."""
        self.is_running = False
        time.sleep(0.5)  # Give a moment for the monitoring loop to finish
        self.cleanup()

def main():
    """Example usage of the PageMonitor class."""
    url = "https://example.com/page-with-buttons"
    notifier = None
    refresh_interval = 1  # Set default refresh interval to 1 second
    
    while True:
        try:
            # Initialize Telegram notifier if not already initialized
            if not notifier:
                try:
                    notifier = TelegramNotifier()
                except Exception as e:
                    if "wait of" in str(e).lower():
                        wait_time = int(str(e).split()[3])  # Extract wait time from error
                        print(f"\nTelegram rate limit hit. Waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print("\nWarning: Failed to initialize Telegram notifications. Continuing without notifications.")
                        logging.warning(f"Telegram initialization error: {e}")
            
            # Initialize monitor with existing notifier and correct refresh interval
            monitor = PageMonitor(url, refresh_interval=refresh_interval, notifier=notifier)
            
            # Set up driver and select buttons
            monitor.setup_driver()
            monitor.select_buttons_interactive()
            
            # Start monitoring
            monitor.monitor()
            
        except KeyboardInterrupt:
            print("\nProgram interrupted by user")
            break
        except Exception as e:
            if "wait of" in str(e).lower():
                wait_time = int(str(e).split()[3])
                print(f"\nTelegram rate limit hit. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            
            logging.error(f"Monitor crashed, restarting: {e}")
            if notifier:
                notifier = None  # Reset notifier on error
            time.sleep(2)

if __name__ == "__main__":
    main() 
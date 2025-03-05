"""Button selector for Web Button Watcher."""

import logging
import time
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)

class ButtonSelector:
    """Handles button selection on web pages."""
    
    def __init__(self, driver_manager):
        """Initialize the button selector.
        
        Args:
            driver_manager: The driver manager instance.
        """
        self.driver_manager = driver_manager
        self.selection_css = """
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
                font-family: Arial, sans-serif !important;
            }
            .selection-button {
                background: #4CAF50 !important;
                border: none !important;
                color: white !important;
                padding: 10px 20px !important;
                text-align: center !important;
                text-decoration: none !important;
                display: inline-block !important;
                font-size: 16px !important;
                margin: 4px 2px !important;
                cursor: pointer !important;
                border-radius: 4px !important;
            }
            .selection-button:hover {
                background: #45a049 !important;
            }
        """
    
    def get_available_buttons(self):
        """Get list of all buttons on the page."""
        buttons = self.driver_manager.find_elements(By.TAG_NAME, "button")
        return buttons
    
    def select_buttons_interactive(self):
        """Allow user to select buttons by clicking them."""
        logger.info("Starting interactive button selection")
        
        # Inject CSS for selection UI
        self.driver_manager.inject_css(self.selection_css)
        
        # Find all buttons first
        buttons = self.get_available_buttons()
        if not buttons:
            logger.warning("No buttons found on the page")
            raise ValueError("No buttons found on the page")
        
        # Add selection UI
        self.driver_manager.execute_script("""
            // Remove any existing UI
            document.querySelectorAll('.selection-header, .button-wrapper, .button-overlay').forEach(el => {
                if (el.classList.contains('selection-header')) {
                    el.remove();
                } else if (el.classList.contains('button-wrapper')) {
                    // Unwrap button
                    const parent = el.parentNode;
                    while (el.firstChild) {
                        parent.insertBefore(el.firstChild, el);
                    }
                    parent.removeChild(el);
                } else if (el.classList.contains('button-overlay')) {
                    el.remove();
                }
            });
            
            // Add header
            const header = document.createElement('div');
            header.className = 'selection-header';
            header.innerHTML = '<h2>Select buttons to monitor</h2><p>Click on buttons you want to monitor, then click "Confirm Selection"</p>';
            
            // Add confirm button
            const confirmBtn = document.createElement('button');
            confirmBtn.className = 'selection-button';
            confirmBtn.textContent = 'Confirm Selection';
            confirmBtn.id = 'confirm-selection-btn';
            header.appendChild(confirmBtn);
            
            document.body.insertBefore(header, document.body.firstChild);
            
            // Initialize selection state
            window.selectedButtons = [];
            window.selectionConfirmed = false;
            
            // Add click handler for confirm button
            document.getElementById('confirm-selection-btn').addEventListener('click', function() {
                window.selectionConfirmed = true;
            });
            
            // Wrap all buttons with selection UI
            const buttons = Array.from(document.querySelectorAll('button')).filter(
                button => !button.classList.contains('selection-button') && button.id !== 'confirm-selection-btn'
            );
            
            buttons.forEach((button, index) => {
                // Create wrapper
                const wrapper = document.createElement('div');
                wrapper.className = 'button-wrapper';
                
                // Create overlay
                const overlay = document.createElement('div');
                overlay.className = 'button-overlay';
                overlay.dataset.index = index;
                
                // Create number label
                const label = document.createElement('div');
                label.className = 'button-number';
                label.textContent = (index + 1);
                
                // Add click handler to overlay
                overlay.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const buttonIndex = parseInt(this.dataset.index);
                    const idx = window.selectedButtons.indexOf(buttonIndex);
                    
                    if (idx === -1) {
                        // Add to selection
                        window.selectedButtons.push(buttonIndex);
                        this.classList.add('selected');
                    } else {
                        // Remove from selection
                        window.selectedButtons.splice(idx, 1);
                        this.classList.remove('selected');
                    }
                    
                    return false;
                });
                
                // Wrap button
                button.parentNode.insertBefore(wrapper, button);
                wrapper.appendChild(button);
                wrapper.appendChild(overlay);
                wrapper.appendChild(label);
            });
        """)
        
        # Wait for user to confirm selection
        print("\nPlease select buttons in the browser and click 'Confirm Selection'")
        
        try:
            # Wait for confirmation with timeout
            start_time = time.time()
            timeout = 300  # 5 minutes timeout
            
            while time.time() - start_time < timeout:
                confirmed = self.driver_manager.execute_script("return window.selectionConfirmed === true;")
                if confirmed:
                    break
                time.sleep(0.5)
            
            if not confirmed:
                logger.warning("Selection timed out")
                print("\nSelection timed out. Please try again.")
                return []
            
            # Get selected buttons
            selected_indices = self.driver_manager.execute_script("return window.selectedButtons;")
            
            if not selected_indices:
                logger.warning("No buttons were selected")
                print("\nNo buttons were selected.")
                return []
            
            # Log the selection
            logger.info(f"Selected {len(selected_indices)} buttons: {selected_indices}")
            print(f"\nSelected {len(selected_indices)} buttons.")
            
            # Get button texts
            button_texts = self.get_button_texts(selected_indices)
            
            # Print selected buttons
            for i, idx in enumerate(selected_indices):
                print(f"Button {i+1}: '{button_texts.get(idx, 'Unknown')}'")
            
            # Remove selection UI
            self.driver_manager.execute_script("""
                document.querySelectorAll('.selection-header').forEach(el => el.remove());
                
                // Unwrap buttons
                document.querySelectorAll('.button-wrapper').forEach(wrapper => {
                    const parent = wrapper.parentNode;
                    const button = wrapper.querySelector('button');
                    if (button) {
                        parent.insertBefore(button, wrapper);
                    }
                    parent.removeChild(wrapper);
                });
            """)
            
            return selected_indices
        except Exception as e:
            logger.error(f"Error during button selection: {e}")
            return []
    
    def get_button_texts(self, button_indices=None):
        """Get the text of buttons on the page.
        
        Args:
            button_indices: Optional list of button indices to get text for.
                If None, gets text for all buttons.
        
        Returns:
            Dictionary mapping button indices to their text.
        """
        button_texts = {}
        buttons = self.get_available_buttons()
        
        if button_indices is None:
            # Get text for all buttons
            for i, button in enumerate(buttons):
                button_texts[i] = button.text
        else:
            # Get text only for specified buttons
            for i in button_indices:
                if i < len(buttons):
                    button_texts[i] = buttons[i].text
        
        return button_texts 
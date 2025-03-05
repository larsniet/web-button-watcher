"""Driver manager for Web Button Watcher."""

import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

class DriverManager:
    """Manages the browser driver instance."""
    
    def __init__(self):
        """Initialize the driver manager."""
        self.driver = None
        self.url = None
    
    def initialize_driver(self):
        """Initialize the Chrome driver with appropriate version handling."""
        if self.driver:
            logger.info("Driver already initialized, reusing existing driver")
            return self.driver
            
        logger.info("Initializing Chrome driver...")
        
        try:
            # Use undetected_chromedriver which is better at bypassing Cloudflare
            import undetected_chromedriver as uc
            
            logger.debug("Initializing with undetected_chromedriver...")
            options = uc.ChromeOptions()
            
            # Basic settings
            options.add_argument("--start-maximized")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # Disable automation flags
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Set a realistic user agent
            options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36")
            
            # Add language and platform preferences to appear more human
            options.add_argument("--lang=en-US")
            options.add_argument("--disable-extensions")
            
            # Create the driver with the configured options
            # Use version_main to match your Chrome version
            self.driver = uc.Chrome(options=options, use_subprocess=True, version_main=133)
            
            # Execute CDP commands to modify navigator properties
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """
            })
            
            logger.info("Successfully initialized undetected_chromedriver")
            
        except Exception as e:
            logger.error(f"Failed to initialize with undetected_chromedriver: {e}")
            
            # Fall back to regular selenium with webdriver_manager
            try:
                from selenium import webdriver
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                
                logger.debug("Falling back to regular selenium...")
                service = Service(ChromeDriverManager().install())
                options = webdriver.ChromeOptions()
                
                # Basic settings
                options.add_argument("--start-maximized")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                
                # Disable automation flags
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option("useAutomationExtension", False)
                
                # Set a realistic user agent
                options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36")
                
                # Create the driver with the configured options
                self.driver = webdriver.Chrome(service=service, options=options)
                
                logger.info("Successfully initialized Chrome with webdriver_manager")
            except Exception as e2:
                logger.error(f"Failed to initialize Chrome driver: {e2}")
                raise
            
        return self.driver
    
    def navigate_to(self, url):
        """Navigate to the specified URL and handle Cloudflare challenges."""
        self.url = url
        
        if not self.driver:
            self.initialize_driver()
        
        logger.info(f"Navigating to {url}")
        self.driver.get(url)
        
        # Wait for Cloudflare challenge to be solved if present
        self.wait_for_cloudflare(timeout=60)
        
        return self.driver
    
    def wait_for_cloudflare(self, timeout=30):
        """Wait for Cloudflare challenge to be solved."""
        logger.info("Checking for Cloudflare challenge...")
        
        try:
            # Wait for Cloudflare challenge to be solved
            start_time = time.time()
            while time.time() - start_time < timeout:
                # Check if we're on a Cloudflare challenge page
                if "cloudflare" in self.driver.page_source.lower() and "checking your browser" in self.driver.page_source.lower():
                    logger.info("Cloudflare challenge detected, waiting for it to be solved...")
                    print("\nCloudflare challenge detected. Please solve the CAPTCHA manually if prompted.")
                    time.sleep(2)
                else:
                    # No Cloudflare challenge or it's been solved
                    logger.info("No Cloudflare challenge detected or it has been solved.")
                    return True
            
            # If we get here, the Cloudflare challenge wasn't solved in time
            logger.warning(f"Cloudflare challenge not solved within {timeout} seconds.")
            return False
            
        except Exception as e:
            logger.error(f"Error while waiting for Cloudflare: {e}")
            return False
    
    def refresh_page(self):
        """Refresh the current page and handle Cloudflare challenges."""
        if not self.driver:
            raise ValueError("Driver not initialized")
        
        logger.debug("Refreshing page...")
        self.driver.refresh()
        
        # Wait for Cloudflare challenge to be solved if present
        self.wait_for_cloudflare(timeout=30)
        
        # Wait for page to load
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "button"))
            )
        except Exception as e:
            logger.warning(f"Timeout waiting for buttons after refresh: {e}")
    
    def inject_css(self, css_code):
        """Inject custom CSS into the page."""
        if not self.driver:
            raise ValueError("Driver not initialized")
        
        logger.debug("Injecting CSS...")
        self.driver.execute_script(f"""
            if (!document.getElementById('custom-styles')) {{
                var style = document.createElement('style');
                style.id = 'custom-styles';
                style.innerHTML = `{css_code}`;
                document.head.appendChild(style);
            }}
        """)
    
    def execute_script(self, script, *args):
        """Execute JavaScript in the browser."""
        if not self.driver:
            raise ValueError("Driver not initialized")
        
        return self.driver.execute_script(script, *args)
    
    def find_elements(self, by, value):
        """Find elements in the page."""
        if not self.driver:
            raise ValueError("Driver not initialized")
        
        return self.driver.find_elements(by, value)
    
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error closing driver: {e}")
            finally:
                self.driver = None 
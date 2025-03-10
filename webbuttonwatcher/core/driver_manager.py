"""Driver manager for Web Button Watcher."""

import logging
import time
import sys
import os
import platform
import subprocess
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
        self.is_mac_app = sys.platform == 'darwin' and getattr(sys, 'frozen', False)
        self.browser_process = None
        self.web_view = None  # For QtWebEngine implementation
        self.using_qt_browser = False
    
    def initialize_driver(self):
        """Initialize the Chrome driver with appropriate version handling."""
        if self.driver:
            logger.info("Driver already initialized, reusing existing driver")
            return self.driver
            
        logger.info("Initializing browser driver...")
        
        # First try to use the QtWebEngine (embedded browser) approach
        if self.is_mac_app or '--use-qtwebengine' in sys.argv:
            try:
                return self._initialize_qt_webengine()
            except Exception as e:
                logger.warning(f"Failed to initialize QtWebEngine: {e}, falling back to standard approach")
        
        # Fall back to standard driver approach
        if self.is_mac_app:
            return self._initialize_mac_driver()
        else:
            return self._initialize_standard_driver()
    
    def _initialize_qt_webengine(self):
        """Initialize an integrated browser using QtWebEngine."""
        try:
            from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineSettings
            from PyQt5.QtCore import QUrl, QTimer, pyqtSignal, QObject, QByteArray
            from PyQt5.QtWidgets import QApplication
            
            logger.info("Initializing integrated QtWebEngine browser")
            
            # Create a custom profile with anti-detection settings
            profile = QWebEngineProfile("AntiDetectionProfile")
            
            # Desktop user agents
            desktop_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.54",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0"
            ]
            
            # Choose a random user agent
            import random
            user_agent = random.choice(desktop_agents)
            profile.setHttpUserAgent(user_agent)
            
            # Don't persist cookies or cache for consistent results
            profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
            profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
            
            # Set various settings to mimic a regular browser
            settings = profile.settings()
            settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
            settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
            settings.setAttribute(QWebEngineSettings.AllowGeolocationOnInsecureOrigins, True)
            settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
            settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
            
            # Create a custom page class to handle JavaScript and anti-detection
            class AntiDetectionWebEnginePage(QWebEnginePage):
                def __init__(self, profile):
                    super().__init__(profile)
                    self.loadFinished.connect(self.on_load_finished)
                    self.cloudflare_passed = False
                    
                def on_load_finished(self, success):
                    if success:
                        # Inject JS to evade fingerprinting
                        self.runJavaScript(self.get_anti_detection_js())
                        # Check for Cloudflare
                        self.runJavaScript("document.documentElement.outerHTML", self.check_for_cloudflare)
                
                def check_for_cloudflare(self, html):
                    if not html:
                        return
                        
                    # Convert bytes to string if needed
                    if isinstance(html, bytes):
                        html = html.decode('utf-8')
                    
                    html_lower = html.lower()
                    cloudflare_elements = [
                        "challenge-form", 
                        "cf-challenge", 
                        "cf-browser-verification",
                        "turnstile_iframe",
                        "cf-im-under-attack"
                    ]
                    
                    if any(element in html_lower for element in cloudflare_elements):
                        logger.info("Cloudflare challenge detected in QtWebEngine")
                        # If we detect Cloudflare, inject more anti-detection scripts
                        self.runJavaScript(self.get_cloudflare_bypass_js())
                    else:
                        self.cloudflare_passed = True
                
                def get_anti_detection_js(self):
                    """Return JS to help bypass bot detection."""
                    return """
                    // Override navigator properties
                    const originalNavigator = window.navigator;
                    delete window.navigator;
                    window.navigator = {
                        __proto__: originalNavigator,
                        // WebDriver should be undefined, not false
                        get webdriver() { return undefined; },
                        // Set a standard languages array
                        languages: ["en-US", "en"],
                        // Set standard platform
                        platform: "Win32",
                        // Make sure hardwareConcurrency looks normal
                        hardwareConcurrency: 8,
                        // Override device memory
                        deviceMemory: 8,
                        // Override connection type properties
                        connection: {
                            effectiveType: "4g",
                            rtt: 50,
                            downlink: 10
                        }
                    };
                    
                    // Spoof plugins array
                    Object.defineProperty(navigator, 'plugins', {
                        get: function() {
                            return [
                                { name: "PDF Viewer", description: "Portable Document Format", filename: "internal-pdf-viewer" },
                                { name: "Chrome PDF Viewer", description: "Portable Document Format", filename: "internal-pdf-viewer" },
                                { name: "Microsoft Edge PDF Viewer", description: "Portable Document Format", filename: "internal-pdf-viewer" },
                                { name: "WebKit built-in PDF", description: "Portable Document Format", filename: "internal-pdf-viewer" }
                            ];
                        }
                    });
                    
                    // Hide automation
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };
                    
                    // Modify iframe detection
                    Object.defineProperty(window, 'parent', {
                        get: function() { return window; }
                    });
                    
                    // Override permissions
                    Object.defineProperty(navigator, 'permissions', {
                        value: {
                            query: async function() {
                                return { state: 'granted' };
                            }
                        }
                    });
                    """
                
                def get_cloudflare_bypass_js(self):
                    """Return JS specifically for Cloudflare bypass."""
                    return """
                    // Add more aggressive Cloudflare bypass
                    
                    // Try to auto-click "I'm a human" verification buttons
                    function clickHumanButtons() {
                        const buttons = document.querySelectorAll('button, input[type="submit"], a.button');
                        for (const button of buttons) {
                            const text = button.textContent.toLowerCase();
                            if (text.includes('human') || text.includes('verify') || text.includes('continue') || 
                                text.includes('proceed') || text.includes('check')) {
                                console.log('Clicking verification button:', button);
                                button.click();
                                return true;
                            }
                        }
                        return false;
                    }
                    
                    // Handle common Cloudflare patterns
                    function handleCloudflareChallenges() {
                        // Check for turnstile frames and try to interact
                        const turnstileFrames = document.querySelectorAll('iframe[src*="challenges"]');
                        if (turnstileFrames.length > 0) {
                            console.log('Detected Cloudflare turnstile challenge');
                            // We can't solve the challenge automatically, but we can make it visible
                            turnstileFrames.forEach(frame => {
                                frame.style.visibility = 'visible';
                                frame.style.opacity = '1';
                            });
                        }
                        
                        // Try clicking verification buttons
                        if (clickHumanButtons()) {
                            return true;
                        }
                        
                        return false;
                    }
                    
                    // Run immediately and then every second for a while
                    handleCloudflareChallenges();
                    let attempts = 0;
                    const intervalId = setInterval(() => {
                        if (handleCloudflareChallenges() || attempts > 10) {
                            clearInterval(intervalId);
                        }
                        attempts++;
                    }, 1000);
                    """
                
                def javaScriptConsoleMessage(self, level, message, line, source):
                    # Uncomment for debugging JavaScript issues
                    # print(f"JS Console ({level}): {message} [line {line} in {source}]")
                    pass
            
            # Create our view and custom page
            self.web_view = QWebEngineView()
            self.page = AntiDetectionWebEnginePage(profile)
            self.web_view.setPage(self.page)
            
            # Create a wrapper object that mimics Selenium WebDriver API
            class WebDriverWrapper:
                def __init__(self, view, page):
                    self.view = view
                    self.page = page
                    self.current_url = ""
                    self.is_qt_browser = True
                
                def get(self, url):
                    self.current_url = url
                    self.page.load(QUrl(url))
                    QApplication.processEvents()
                
                def refresh(self):
                    self.page.triggerAction(QWebEnginePage.Reload)
                    QApplication.processEvents()
                
                def quit(self):
                    self.view.close()
                    self.view.deleteLater()
                
                @property
                def page_source(self):
                    # This is async in QtWebEngine, so we need to work around it
                    # For now, return an empty string - the actual content is checked in the page class
                    return ""
                
                def wait_for_page_load(self, timeout=30):
                    """Wait for the page to finish loading."""
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        if self.page.cloudflare_passed:
                            return True
                        QApplication.processEvents()
                        time.sleep(0.1)
                    return False
            
            driver = WebDriverWrapper(self.web_view, self.page)
            self.using_qt_browser = True
            
            # Show the browser with a reasonable size
            self.web_view.resize(1200, 800)
            self.web_view.show()
            
            logger.info("QtWebEngine browser initialized successfully")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to initialize QtWebEngine browser: {e}")
            self.using_qt_browser = False
            return None
    
    def _initialize_mac_driver(self):
        """Initialize driver for macOS to prevent application relaunching."""
        try:
            # Use the pure Selenium approach for macOS packaged apps
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            
            logger.info("Using pure Selenium approach for macOS packaged app")
            
            # Find Chrome executable
            chrome_path = self._find_chrome_executable()
            if not chrome_path:
                logger.warning("Could not find Chrome executable, using default location")
                
            # Use Selenium's built-in Chrome WebDriver - no external chromedriver needed
            options = webdriver.ChromeOptions()
            
            # Set Chrome binary location if found
            if chrome_path:
                options.binary_location = chrome_path
                
            # Add arguments to prevent automatic updates, notifications, etc.
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-sync")
            options.add_argument("--disable-gpu")  # Optional, can help with some issues
            
            # Disable automation flags
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            
            # Set window size explicitly
            options.add_argument("--window-size=1440,900")
            
            # Launch Chrome directly
            try:
                # Try using built-in WebDriver first (macOS should have Chrome WebDriver built in)
                logger.debug("Trying to launch Chrome using built-in WebDriver")
                self.driver = webdriver.Chrome(options=options)
            except Exception as inner_e:
                logger.warning(f"Failed to launch with built-in WebDriver: {inner_e}")
                
                # Fall back to using cached ChromeDriver
                import subprocess
                import glob
                import os
                
                # Use homebrew ChromeDriver if available
                homebrew_driver = "/opt/homebrew/bin/chromedriver"
                if os.path.exists(homebrew_driver):
                    logger.debug(f"Using Homebrew ChromeDriver at {homebrew_driver}")
                    service = Service(executable_path=homebrew_driver)
                    self.driver = webdriver.Chrome(service=service, options=options)
                else:
                    # Last resort - use whatever chromedriver is in PATH
                    self.driver = webdriver.Chrome(options=options)
                    
            logger.info("Successfully initialized Chrome on macOS")
            return self.driver
            
        except Exception as e:
            logger.error(f"Failed to initialize macOS Chrome: {e}")
            raise
            
    def _find_chrome_executable(self):
        """Find the Chrome executable on macOS."""
        default_paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chrome.app/Contents/MacOS/Chrome'
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                return path
                
        # Try to find Chrome using the 'mdfind' command (macOS)
        try:
            process = subprocess.Popen(
                ['mdfind', 'kMDItemCFBundleIdentifier == "com.google.Chrome"'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, _ = process.communicate()
            chrome_app_path = stdout.decode().strip().split('\n')[0]
            
            if chrome_app_path:
                chrome_executable = os.path.join(chrome_app_path, 'Contents/MacOS/Google Chrome')
                if os.path.exists(chrome_executable):
                    return chrome_executable
        except:
            pass
        
        return None
    
    def _initialize_standard_driver(self):
        """Initialize standard driver for non-macOS platforms or development mode."""
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
            
            # Prevent application relaunch from browser
            options.add_argument("--process-per-site")  # Use process-per-site mode
            options.add_argument("--disable-infobars")  # Disable info bars
            options.add_argument("--disable-notifications")  # Disable notifications
            options.add_argument("--disable-sync")  # Disable browser sync
            
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
                
                # Prevent application relaunch from browser
                options.add_argument("--process-per-site")  # Use process-per-site mode
                options.add_argument("--disable-infobars")  # Disable info bars
                options.add_argument("--disable-notifications")  # Disable notifications
                options.add_argument("--disable-sync")  # Disable browser sync
                
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
        """Navigate to the specified URL."""
        if not self.driver:
            self.initialize_driver()
            if not self.driver:
                logger.error("Failed to initialize driver for navigation")
                return False
        
        logger.info(f"Navigating to URL: {url}")
        
        try:
            # Ensure URL has proper scheme
            if not url.startswith('http'):
                url = 'https://' + url
                
            # Store the URL for potential recovery
            self.last_url = url
            
            # Navigate to the URL
            self.driver.get(url)
            
            # Wait for Cloudflare protection if present
            if self.using_qt_browser:
                # For QtWebEngine, wait for page loading and Cloudflare handling
                if hasattr(self.driver, 'wait_for_page_load'):
                    self.driver.wait_for_page_load(timeout=30)
            else:
                # For Selenium-based drivers, use the standard approach
                self.wait_for_cloudflare()
            
            logger.info(f"Successfully navigated to {url}")
            return True
            
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return False
    
    def wait_for_cloudflare(self, timeout=30):
        """Wait for Cloudflare protection if present."""
        if not self.driver:
            return
            
        try:
            if self.using_qt_browser:
                # For QtWebEngine, Cloudflare waiting is handled inside the get() and refresh() methods
                return
                
            # For Selenium-based drivers, use the standard approach
            logger.info("Checking for Cloudflare challenge...")
            
            # Check if we're on a Cloudflare page
            current_url = self.driver.current_url.lower()
            if "cloudflare" in current_url or "challenge" in current_url:
                logger.info("Detected possible Cloudflare challenge page")
            
            # Look for common Cloudflare elements
            cloudflare_elements = [
                "challenge-form", 
                "cf-challenge", 
                "cf-browser-verification",
                "turnstile_iframe",
                "cf-im-under-attack"
            ]
            
            # Wait for Cloudflare elements to disappear
            start_time = time.time()
            while time.time() - start_time < timeout:
                page_html = self.driver.page_source.lower() if hasattr(self.driver, 'page_source') else ""
                
                if any(element in page_html for element in cloudflare_elements):
                    logger.info("Waiting for Cloudflare challenge to complete...")
                    time.sleep(1)
                    continue
                    
                try:
                    # Try to find buttons to confirm we're past the challenge
                    buttons = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.TAG_NAME, "button"))
                    )
                    logger.info("Cloudflare challenge passed or not present")
                    return
                except:
                    # No buttons yet, continue waiting
                    time.sleep(1)
            
            logger.warning(f"Timed out waiting for Cloudflare challenge ({timeout}s)")
        except Exception as e:
            logger.warning(f"Error while checking for Cloudflare challenge: {e}")
            # Continue anyway
    
    def refresh_page(self):
        """Refresh the current page."""
        if not self.driver:
            logger.error("Cannot refresh page: driver not initialized")
            return False
            
        logger.info("Refreshing page")
        
        try:
            # Refresh the page
            self.driver.refresh()
            
            # Wait for Cloudflare protection if present
            if self.using_qt_browser:
                # For QtWebEngine, wait for page loading and Cloudflare handling
                if hasattr(self.driver, 'wait_for_page_load'):
                    self.driver.wait_for_page_load(timeout=30)
            else:
                # For Selenium-based drivers, use the standard approach
                self.wait_for_cloudflare()
                
            logger.info("Page refreshed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing page: {e}")
            
            # Try to recover by navigating to the last URL if available
            if hasattr(self, 'last_url') and self.last_url:
                logger.info(f"Attempting recovery by navigating to last URL: {self.last_url}")
                return self.navigate_to(self.last_url)
                
            return False
    
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
                # First try the standard quit method
                logger.debug("Attempting to quit driver")
                self.driver.quit()
                
                # Special cleanup for QtWebEngine
                if self.using_qt_browser and self.web_view:
                    logger.debug("Cleaning up QtWebEngine")
                    try:
                        self.web_view.close()
                        self.web_view.deleteLater()
                    except Exception as inner_e:
                        logger.debug(f"Error cleaning up web view: {inner_e}")
                # Special cleanup for macOS packaged app
                elif self.is_mac_app:
                    logger.debug("Performing macOS-specific cleanup")
                    self._kill_chrome_processes()
                # Regular cleanup for other platforms
                elif platform.system() == "Darwin":  # macOS
                    self._kill_chrome_processes()
                
            except Exception as e:
                logger.error(f"Error closing driver: {e}")
                # Try more aggressive cleanup
                self._kill_chrome_processes()
            finally:
                self.driver = None
                self.web_view = None
                self.using_qt_browser = False
                
    def _kill_chrome_processes(self):
        """Kill any remaining Chrome processes potentially related to automation."""
        try:
            # Find Chrome processes that might be related to automation
            ps_cmd = "ps -ax | grep Chrome | grep -v grep"
            process = subprocess.Popen(ps_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = process.communicate()
            
            for line in stdout.decode().split('\n'):
                if "Chrome" in line and ("--remote-debugging-port" in line or "--disable-notifications" in line):
                    # Extract PID and kill the process
                    try:
                        pid = int(line.strip().split()[0])
                        logger.info(f"Killing Chrome process with PID {pid}")
                        os.kill(pid, 9)  # SIGKILL
                    except (ValueError, IndexError, ProcessLookupError) as e:
                        logger.debug(f"Failed to kill Chrome process: {e}")
        except Exception as e:
            logger.debug(f"Error cleaning up Chrome processes: {e}")
    
    def find_button(self, button_text, button_identifiers):
        """Find a button on the page based on text and other identifiers."""
        if not self.driver:
            logger.error("Cannot find button: driver not initialized")
            return None
            
        logger.info(f"Looking for button with text: {button_text}")
        
        try:
            # For QtWebEngine, we need a different approach
            if self.using_qt_browser:
                # Use JavaScript to find buttons
                js_find_buttons = """
                (function() {
                    const buttonText = arguments[0].toLowerCase().trim();
                    const buttonIdentifiers = arguments[1];
                    
                    function getAllClickableElements() {
                        // Get all potentially clickable elements
                        const elements = [
                            ...document.querySelectorAll('button, input[type="button"], input[type="submit"], a.button, a[role="button"], div[role="button"], span[role="button"]'),
                            ...document.querySelectorAll('a')
                        ];
                        
                        return elements.filter(el => {
                            // Filter visible elements that are likely buttons
                            const style = window.getComputedStyle(el);
                            const isVisible = style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
                            
                            return isVisible;
                        });
                    }
                    
                    function checkElementMatch(element, buttonText, buttonIdentifiers) {
                        // Check if element's text contains buttonText
                        const elementText = (element.innerText || element.textContent || '').toLowerCase().trim();
                        const elementValue = (element.value || '').toLowerCase().trim();
                        
                        // Check text match
                        if (elementText.includes(buttonText) || elementValue.includes(buttonText)) {
                            return true;
                        }
                        
                        // If button identifiers are provided, check them too
                        if (buttonIdentifiers && buttonIdentifiers.length > 0) {
                            for (const identifier of buttonIdentifiers) {
                                // Check if any attribute contains the identifier
                                for (const attr of element.getAttributeNames()) {
                                    const attrValue = element.getAttribute(attr).toLowerCase();
                                    if (attrValue.includes(identifier.toLowerCase())) {
                                        return true;
                                    }
                                }
                                
                                // Check if ID, class, or name contains the identifier
                                if ((element.id && element.id.toLowerCase().includes(identifier.toLowerCase())) ||
                                    (element.className && element.className.toLowerCase().includes(identifier.toLowerCase())) ||
                                    (element.name && element.name.toLowerCase().includes(identifier.toLowerCase()))) {
                                    return true;
                                }
                            }
                        }
                        
                        return false;
                    }
                    
                    const buttons = getAllClickableElements();
                    
                    // Try to find the button
                    for (const button of buttons) {
                        if (checkElementMatch(button, buttonText, buttonIdentifiers)) {
                            // Return info about the button we found
                            return {
                                found: true,
                                text: button.innerText || button.textContent || button.value || '',
                                tag: button.tagName,
                                id: button.id || '',
                                class: button.className || ''
                            };
                        }
                    }
                    
                    return { found: false };
                })();
                """
                
                # Create a callback to handle the JS result
                button_result = [None]
                
                def js_callback(result):
                    button_result[0] = result
                
                # Execute JS and wait for result
                self.page.runJavaScript(js_find_buttons, [button_text, button_identifiers], js_callback)
                
                # Wait for JS to complete (simplified approach)
                start_time = time.time()
                while button_result[0] is None and time.time() - start_time < 10:
                    QApplication.processEvents()
                    time.sleep(0.1)
                
                if button_result[0] and button_result[0].get('found', False):
                    logger.info(f"Button found: {button_result[0].get('text', '')}")
                    return button_result[0]
                else:
                    logger.warning(f"Button with text '{button_text}' not found")
                    return None
            
            # For Selenium WebDriver
            else:
                # First try: find by button text
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{button_text.lower()}')]")
                    if not elements:
                        elements = self.driver.find_elements(By.XPATH, f"//input[@type='button' or @type='submit'][contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{button_text.lower()}')]")
                    if not elements:
                        elements = self.driver.find_elements(By.XPATH, f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{button_text.lower()}')]")
                    
                    if elements:
                        logger.info(f"Found button with text: {button_text}")
                        return elements[0]
                except Exception as e:
                    logger.warning(f"Error finding button by text: {e}")
                
                # Second try: find by button identifiers
                if button_identifiers:
                    for identifier in button_identifiers:
                        try:
                            xpath = f"//button[contains(@id, '{identifier}') or contains(@class, '{identifier}') or contains(@name, '{identifier}')]"
                            elements = self.driver.find_elements(By.XPATH, xpath)
                            if not elements:
                                xpath = f"//input[@type='button' or @type='submit'][contains(@id, '{identifier}') or contains(@class, '{identifier}') or contains(@name, '{identifier}')]"
                                elements = self.driver.find_elements(By.XPATH, xpath)
                            if not elements:
                                xpath = f"//a[contains(@id, '{identifier}') or contains(@class, '{identifier}') or contains(@name, '{identifier}')]"
                                elements = self.driver.find_elements(By.XPATH, xpath)
                                
                            if elements:
                                logger.info(f"Found button with identifier: {identifier}")
                                return elements[0]
                        except Exception as e:
                            logger.warning(f"Error finding button by identifier {identifier}: {e}")
                
                logger.warning(f"Button with text '{button_text}' not found")
                return None
            
        except Exception as e:
            logger.error(f"Error finding button: {e}")
            return None
    
    def click_button(self, button):
        """Click a button that was found with find_button."""
        if not self.driver:
            logger.error("Cannot click button: driver not initialized")
            return False
            
        if not button:
            logger.error("Cannot click button: no button provided")
            return False
        
        try:
            # Different handling based on the driver type
            if self.using_qt_browser:
                # For QtWebEngine, we need to use JavaScript to click the button
                # The button is already an object with information from find_button
                
                js_click_button = """
                (function() {
                    const buttonInfo = arguments[0];
                    
                    // Try to find the button again
                    let foundButton = null;
                    
                    // Try by ID first (most reliable)
                    if (buttonInfo.id) {
                        foundButton = document.getElementById(buttonInfo.id);
                        if (foundButton) {
                            console.log("Found button by ID: " + buttonInfo.id);
                        }
                    }
                    
                    // If not found by ID, try by class
                    if (!foundButton && buttonInfo.class) {
                        const elements = document.getElementsByClassName(buttonInfo.class);
                        if (elements.length > 0) {
                            foundButton = elements[0];
                            console.log("Found button by class: " + buttonInfo.class);
                        }
                    }
                    
                    // If still not found, try by text content
                    if (!foundButton && buttonInfo.text) {
                        const buttonText = buttonInfo.text.toLowerCase().trim();
                        const elements = document.querySelectorAll('button, input[type="button"], input[type="submit"], a.button, a[role="button"], div[role="button"], span[role="button"], a');
                        
                        for (const element of elements) {
                            const elementText = (element.innerText || element.textContent || element.value || '').toLowerCase().trim();
                            if (elementText.includes(buttonText)) {
                                foundButton = element;
                                console.log("Found button by text: " + buttonText);
                                break;
                            }
                        }
                    }
                    
                    // If button found, click it
                    if (foundButton) {
                        console.log("Clicking button: " + (foundButton.innerText || foundButton.textContent || foundButton.value || ''));
                        foundButton.click();
                        return true;
                    }
                    
                    console.log("Button not found for clicking");
                    return false;
                })();
                """
                
                # Execute the JS click
                click_result = [None]
                
                def js_callback(result):
                    click_result[0] = result
                
                self.page.runJavaScript(js_click_button, [button], js_callback)
                
                # Wait for JS to complete
                start_time = time.time()
                while click_result[0] is None and time.time() - start_time < 10:
                    QApplication.processEvents()
                    time.sleep(0.1)
                
                if click_result[0]:
                    logger.info("Button clicked successfully")
                    return True
                else:
                    logger.warning("Failed to click button")
                    return False
            
            # For Selenium WebDriver
            else:
                # Selenium button is directly clickable
                button.click()
                logger.info("Button clicked successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error clicking button: {e}")
            return False 
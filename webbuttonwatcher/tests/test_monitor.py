"""Tests for the PageMonitor class."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import warnings

# Suppress all warnings
warnings.filterwarnings("ignore")

# Create mocks before imports happen
mock_uc = MagicMock()
mock_webdriver = MagicMock()
sys.modules['undetected_chromedriver'] = mock_uc
sys.modules['selenium.webdriver'] = mock_webdriver

# Now safe to import
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException

from ..core.monitor import PageMonitor

@pytest.fixture(autouse=True)
def prevent_browser_launch():
    """Prevent any real browser windows from launching during tests."""
    # Create a more complete mock of the driver modules
    with patch('undetected_chromedriver.Chrome', return_value=MagicMock()), \
         patch('selenium.webdriver.Chrome', return_value=MagicMock()), \
         patch('selenium.webdriver.support.ui.WebDriverWait', return_value=MagicMock()):
        yield

@pytest.fixture
def mock_driver():
    """Create a mock Chrome driver."""
    driver = MagicMock()
    driver.window_handles = ['window1']
    driver.switch_to = MagicMock()
    driver.switch_to.alert = MagicMock()
    driver.switch_to.window = MagicMock()
    
    # Add more comprehensive mocking to prevent hanging
    driver.find_elements = MagicMock(return_value=[])
    driver.execute_script = MagicMock(return_value=None)
    driver.get = MagicMock()
    driver.title = "Test Page"
    driver.current_url = "https://test.example.com"
    driver.page_source = "<html><body><button>Test Button</button></body></html>"
    
    return driver

@pytest.fixture
def mock_notifier():
    """Create a mock Telegram notifier."""
    notifier = MagicMock()
    notifier.send_notification = MagicMock()
    return notifier

@pytest.fixture
def monitor(mock_notifier):
    """Create a PageMonitor instance with mocked dependencies."""
    url = "https://test.example.com"
    return PageMonitor(url=url, refresh_interval=0.1, notifier=mock_notifier)

class TestPageMonitor:
    """Test suite for PageMonitor class."""

    def test_init(self, monitor):
        """Test monitor initialization."""
        assert monitor.url == "https://test.example.com"
        assert monitor.refresh_interval == 0.1
        assert monitor.driver is None
        assert monitor.target_buttons == []
        assert monitor.button_texts == {}
        assert monitor.is_running is False

    @patch('undetected_chromedriver.Chrome')
    def test_setup_driver(self, mock_chrome, monitor, mock_driver):
        """Test driver setup."""
        # Configure mock
        mock_chrome.return_value = mock_driver
        
        # Call setup_driver
        driver = monitor.setup_driver()
        
        # Assert Chrome was created
        mock_chrome.assert_called_once()
        assert driver == mock_driver

    @patch('undetected_chromedriver.Chrome')
    def test_cleanup(self, mock_chrome, monitor, mock_driver):
        """Test driver cleanup."""
        # Setup driver
        mock_chrome.return_value = mock_driver
        monitor.driver = mock_driver
        
        # Call cleanup
        monitor.cleanup()
        
        # Verify driver was quit and cleared
        mock_driver.quit.assert_called_once()
        assert monitor.driver is None

    @patch('undetected_chromedriver.Chrome')
    def test_stop(self, mock_chrome, monitor, mock_driver):
        """Test stopping the monitor."""
        # Setup driver and state
        mock_chrome.return_value = mock_driver
        monitor.driver = mock_driver
        monitor.is_running = True
        
        # Call stop
        monitor.stop()
        
        # Verify state was changed and cleanup called
        assert monitor.is_running is False
        mock_driver.quit.assert_called_once()
        assert monitor.driver is None

    @patch('undetected_chromedriver.Chrome')
    def test_select_buttons_interactive(self, mock_chrome, monitor, mock_driver):
        """Test button selection in interactive mode."""
        # Setup driver
        mock_chrome.return_value = mock_driver
        
        # Mock the execute_script to simulate button selection
        def execute_script_mock(script, *args):
            if "window.selectedButtons" in script:
                return {0: "Book Now"}
            elif "window.buttonsDetected" in script:
                return True
            elif "window.selectionConfirmed" in script:
                return True
            return None
        
        mock_driver.execute_script.side_effect = execute_script_mock
        
        # Call select_buttons
        buttons = monitor.select_buttons_interactive()
        
        # Verify buttons were detected and selected
        assert buttons == {0: "Book Now"}
        assert monitor.target_buttons == [0]
        assert monitor.button_texts == {0: "Book Now"}

    @patch('undetected_chromedriver.Chrome')
    @patch('time.sleep')
    def test_monitor_button_changes(self, mock_sleep, mock_chrome, monitor, mock_driver, mock_notifier):
        """Test detecting button changes."""
        # Setup driver
        mock_chrome.return_value = mock_driver
        
        # Set up a sequence of button states
        button1 = MagicMock()
        button2 = MagicMock()
        button1.text = "Book Now"
        button2.text = "Sold Out"
        
        call_count = 0
        def find_elements_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                return [button1]  # Initial state
            else:
                monitor.stop()  # Stop after second check
                return [button2]  # Changed state
        
        mock_driver.find_elements.side_effect = find_elements_side_effect
        
        # Setup monitor
        monitor.driver = mock_driver
        monitor.target_buttons = [0]
        monitor.button_texts = {0: "Book Now"}
        
        # Run monitor
        monitor.monitor()
        
        # Verify notification was sent for button change
        mock_notifier.send_notification.assert_called_once()

    @patch('undetected_chromedriver.Chrome')
    def test_error_handling(self, mock_chrome, monitor, mock_driver):
        """Test error handling during monitoring."""
        # Set up mock
        mock_chrome.return_value = mock_driver
        mock_driver.get.side_effect = WebDriverException("Test error")
        
        # Try to navigate
        with pytest.raises(WebDriverException):
            monitor.navigate_to_page()
        
        # Verify error was handled
        assert mock_driver.get.called

    @patch('undetected_chromedriver.Chrome')
    @patch('time.sleep')
    def test_monitor_without_buttons(self, mock_sleep, mock_chrome, monitor):
        """Test monitoring without any buttons."""
        # Set up mock driver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.find_elements.return_value = []
        
        # Set driver
        monitor.driver = mock_driver
        monitor.target_buttons = []
        
        # Monitor should exit normally when no buttons are specified
        mock_sleep.side_effect = lambda x: monitor.stop()
        monitor.monitor()
        
        # Verify monitoring was attempted but no notifications were sent
        assert mock_driver.find_elements.called
        assert not monitor.notifier.send_notification.called

    @patch('undetected_chromedriver.Chrome')
    @patch('time.sleep')
    def test_refresh_interval(self, mock_sleep, mock_chrome, monitor, mock_driver):
        """Test page refresh interval."""
        # Set up mock
        mock_chrome.return_value = mock_driver
        
        # Set driver and state
        monitor.driver = mock_driver
        monitor.target_buttons = [0]
        monitor.button_texts = {0: "Book Now"}
        
        # Mock sleeping and exit after one cycle
        sleep_calls = []
        def mock_sleep_func(interval):
            sleep_calls.append(interval)
            # Stop the monitor after the first sleep
            monitor.stop()
        
        mock_sleep.side_effect = mock_sleep_func
        
        # Start monitoring
        monitor.monitor()
        
        # Verify correct refresh interval was used
        assert 0.1 in sleep_calls
        assert mock_driver.get.called

    @patch('undetected_chromedriver.Chrome')
    def test_setup_driver_error_handling(self, mock_chrome, monitor):
        """Test handling of errors during driver setup."""
        # Setup Chrome mock to raise an exception
        mock_chrome.side_effect = Exception("Browser error")
        
        # Trying to setup the driver should raise the exception
        with pytest.raises(Exception):
            monitor.setup_driver()

    @patch('undetected_chromedriver.Chrome')
    def test_cleanup_with_active_thread(self, mock_chrome, monitor, mock_driver):
        """Test cleanup with an active monitoring thread."""
        # Set up mock
        mock_chrome.return_value = mock_driver
        
        # Mock the monitor thread
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        
        # Set state
        monitor.monitor_thread = mock_thread
        monitor.driver = mock_driver
        monitor.is_running = True
        
        # Call cleanup
        monitor.cleanup()
        
        # Verify state was reset and driver was closed
        assert monitor.is_running is False
        assert monitor.monitor_thread is None
        assert mock_driver.quit.called

    @patch('undetected_chromedriver.Chrome')
    @patch('time.sleep')
    def test_monitor_empty_button_list(self, mock_sleep, mock_chrome, monitor):
        """Test monitoring with empty button list."""
        # Setup mock driver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        monitor.driver = mock_driver
        monitor.target_buttons = []
        
        # Should exit immediately
        mock_sleep.side_effect = lambda x: monitor.stop()
        monitor.monitor()
        
        # Verify no buttons were checked and no notifications sent
        assert not mock_driver.find_elements.called
        assert not monitor.notifier.send_notification.called

    @patch('undetected_chromedriver.Chrome')
    @patch('time.sleep')
    def test_monitor_button_not_found(self, mock_sleep, mock_chrome, monitor):
        """Test behavior when monitored button disappears."""
        # Setup mock driver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Set up find_elements to simulate button disappearing
        call_count = 0
        def find_elements_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Return a button on first call
                button = MagicMock()
                button.text = "Book Now"
                return [button]
            else:
                # Return no buttons on second call
                monitor.stop()
                return []
        
        mock_driver.find_elements.side_effect = find_elements_side_effect
        
        # Set driver and target buttons
        monitor.driver = mock_driver
        monitor.target_buttons = [0]
        monitor.button_texts = {0: "Book Now"}
        
        # Start monitoring
        mock_sleep.return_value = None
        monitor.monitor()
        
        # Verify warning but no notification
        assert not monitor.notifier.send_notification.called

    @patch('undetected_chromedriver.Chrome')
    @patch('time.sleep')
    def test_monitor_timeout_handling(self, mock_sleep, mock_chrome, monitor):
        """Test handling of timeout errors."""
        # Setup mock driver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Set up find_elements to raise TimeoutException
        def find_elements_side_effect(*args, **kwargs):
            # Raise TimeoutException on first call
            if args[0] == By.CSS_SELECTOR and args[1] == 'button':
                raise TimeoutException("Test timeout")
            return []
        
        mock_driver.find_elements.side_effect = find_elements_side_effect
        
        # Set driver and target buttons
        monitor.driver = mock_driver
        monitor.target_buttons = [0]
        monitor.button_texts = {0: "Book Now"}
        
        # Start monitoring
        mock_sleep.side_effect = lambda x: monitor.stop()
        monitor.monitor()
        
        # Verify behavior after timeout
        assert not monitor.notifier.send_notification.called

    @patch('undetected_chromedriver.Chrome')
    @patch('selenium.webdriver.support.ui.WebDriverWait')
    @patch('time.sleep')  # Add sleep mock to prevent hanging
    def test_button_selection_cancellation(self, mock_sleep, mock_wait, mock_chrome, monitor):
        """Test cancellation during interactive button selection."""
        # Set up mock driver with all required attributes
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        monitor.driver = mock_driver  # Set driver directly
        
        # Mock button elements
        button1 = MagicMock()
        button1.text = "GET NOTIFIED"
        
        # Set up find_elements to return our button
        def find_elements_side_effect(*args, **kwargs):
            return [button1]
        mock_driver.find_elements.side_effect = find_elements_side_effect
        
        # Mock JavaScript execution sequence for selection
        def execute_script_side_effect(script, *args):
            if "return window.selectionConfirmed" in script:
                raise TimeoutException("Selection timed out")  # Simulate timeout
            return None  # Return None for CSS injection and other scripts
        mock_driver.execute_script.side_effect = execute_script_side_effect
        
        # Mock WebDriverWait to simulate timeout
        mock_wait_instance = MagicMock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.side_effect = TimeoutException("Selection timed out")
        
        # Call the method under test and expect it to raise an exception
        with pytest.raises(TimeoutException):
            monitor.select_buttons_interactive()
        
        # Verify that find_elements was called at least once
        mock_driver.find_elements.assert_called_with(By.CSS_SELECTOR, "button")
        assert mock_driver.execute_script.call_count > 0

    @patch('undetected_chromedriver.Chrome')
    def test_monitor_invalid_url(self, mock_chrome, monitor):
        """Test monitoring with an invalid URL."""
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Simulate invalid URL
        mock_driver.get.side_effect = WebDriverException("Invalid URL")
        
        with pytest.raises(WebDriverException, match="Invalid URL"):
            monitor.setup_driver()

    @patch('undetected_chromedriver.Chrome')
    @patch('time.sleep')  # Add sleep mock to prevent actual sleeping
    def test_monitor_permission_error(self, mock_sleep, mock_chrome, monitor):
        """Test handling of permission errors."""
        # Set up mock driver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        monitor.driver = mock_driver
        monitor.target_buttons = [0]
        monitor.button_texts = {0: "Original Text"}
        monitor.is_running = True
        
        # Set up the permission error sequence
        def find_elements_side_effect(*args, **kwargs):
            if args[0] == By.CSS_SELECTOR and "button:not(.selection-button)" in args[1]:
                monitor.stop()  # Stop after permission error
                raise WebDriverException("Permission denied")
            return []
            
        mock_driver.find_elements.side_effect = find_elements_side_effect
        
        # Mock WebDriverWait to avoid timeouts
        mock_wait = MagicMock()
        mock_wait.until.return_value = True
        with patch('selenium.webdriver.support.ui.WebDriverWait', return_value=mock_wait):
            # Run the monitor
            monitor.monitor()
        
        # Verify the monitor stopped and tried to find buttons
        assert not monitor.is_running
        mock_driver.find_elements.assert_any_call(By.CSS_SELECTOR, "button:not(.selection-button)")
        mock_driver.quit.assert_called_once()

    @patch('undetected_chromedriver.Chrome')
    @patch('time.sleep')  # Add sleep mock to prevent actual sleeping
    def test_monitor_stale_element(self, mock_sleep, mock_chrome, monitor):
        """Test handling of stale elements during monitoring."""
        # Set up mock driver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        monitor.driver = mock_driver
        monitor.target_buttons = [0]
        monitor.button_texts = {0: "Original Text"}
        monitor.is_running = True
        
        # Set up the stale element sequence
        call_count = 0
        def find_elements_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if args[0] == By.CSS_SELECTOR and "button:not(.selection-button)" in args[1]:
                if call_count == 1:
                    button = MagicMock()
                    button.text = "Original Text"
                    return [button]
                monitor.stop()  # Stop after second attempt
                raise NoSuchElementException("Element is stale")
            return []
            
        mock_driver.find_elements.side_effect = find_elements_side_effect
        
        # Mock WebDriverWait to avoid timeouts
        mock_wait = MagicMock()
        mock_wait.until.return_value = True
        with patch('selenium.webdriver.support.ui.WebDriverWait', return_value=mock_wait):
            # Run the monitor
            monitor.monitor()
        
        # Verify the monitor stopped and tried to find buttons
        assert not monitor.is_running
        mock_driver.find_elements.assert_any_call(By.CSS_SELECTOR, "button:not(.selection-button)")
        assert call_count >= 2  # Should try at least twice
        mock_driver.quit.assert_called_once()

    def test_stop_monitor_during_execution(self, monitor, mock_driver):
        """Test stopping the monitor while it's running."""
        monitor.driver = mock_driver
        monitor.is_running = True
        monitor.target_buttons = [0]
        monitor.button_texts = {0: "Original Text"}
        
        # Simulate a running monitor
        def side_effect(*args, **kwargs):
            monitor.stop()  # Stop the monitor during execution
            return [MagicMock(text="Original Text")]
            
        mock_driver.find_elements.side_effect = side_effect
        
        monitor.monitor()
        assert not monitor.is_running
        mock_driver.quit.assert_called_once() 
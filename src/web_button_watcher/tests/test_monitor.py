"""Tests for the PageMonitor class."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException

from ..core.monitor import PageMonitor

@pytest.fixture
def mock_driver():
    """Create a mock Chrome driver."""
    driver = MagicMock()
    driver.window_handles = ['window1']
    driver.switch_to = MagicMock()
    driver.switch_to.alert = MagicMock()
    driver.switch_to.window = MagicMock()
    return driver

@pytest.fixture
def mock_notifier():
    """Create a mock Telegram notifier."""
    return Mock()

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
    def test_setup_driver(self, mock_chrome, monitor):
        """Test driver setup."""
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        driver = monitor.setup_driver()
        
        assert driver == mock_driver
        mock_chrome.assert_called_once()
        mock_driver.get.assert_called_once_with(monitor.url)

    def test_cleanup(self, monitor, mock_driver):
        """Test browser cleanup."""
        monitor.driver = mock_driver
        monitor.cleanup()

        mock_driver.switch_to.alert.accept.assert_called_once()
        mock_driver.switch_to.window.assert_called_once_with('window1')
        mock_driver.close.assert_called_once()
        mock_driver.quit.assert_called_once()
        assert monitor.driver is None

    def test_stop(self, monitor, mock_driver):
        """Test stopping the monitor."""
        monitor.driver = mock_driver
        monitor.is_running = True
        
        monitor.stop()
        
        assert not monitor.is_running
        mock_driver.quit.assert_called_once()
        assert monitor.driver is None

    @patch('undetected_chromedriver.Chrome')
    @patch('selenium.webdriver.support.ui.WebDriverWait')
    @patch('selenium.webdriver.support.expected_conditions')
    def test_select_buttons_interactive(self, mock_ec, mock_wait, mock_chrome, monitor):
        """Test interactive button selection."""
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        monitor.driver = mock_driver

        # Mock WebDriverWait
        mock_wait_instance = MagicMock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.return_value = True

        # Mock button elements
        button1 = MagicMock()
        button1.text = "GET NOTIFIED"
        button2 = MagicMock()
        button2.text = "BOOK NOW"
        mock_driver.find_elements.return_value = [button1, button2]

        # Mock JavaScript execution sequence
        js_responses = {
            "return window.selectionConfirmed === true;": True,
            "return window.selectedButtons;": [0, 1]
        }

        def mock_execute_script(script, *args):
            # Return predefined responses for known scripts
            if script in js_responses:
                return js_responses[script]
            # Return None for all other scripts (CSS injection, etc)
            return None

        mock_driver.execute_script.side_effect = mock_execute_script

        selected = monitor.select_buttons_interactive()
        
        assert selected == [0, 1]
        assert monitor.button_texts == {0: "GET NOTIFIED", 1: "BOOK NOW"}

    @patch('undetected_chromedriver.Chrome')
    @patch('selenium.webdriver.support.ui.WebDriverWait')
    @patch('selenium.webdriver.support.expected_conditions')
    @patch('time.sleep')
    def test_monitor_button_changes(self, mock_sleep, mock_ec, mock_wait, mock_chrome, monitor):
        """Test monitoring button changes."""
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        monitor.driver = mock_driver

        # Mock WebDriverWait
        mock_wait_instance = MagicMock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.return_value = True

        # Set up initial state
        monitor.target_buttons = [0]  # Only monitor first button
        monitor.button_texts = {0: "GET NOTIFIED"}
        monitor.is_running = True

        # Mock expected conditions
        mock_ec.presence_of_all_elements_located.return_value = MagicMock()

        # Mock find_elements to return changed button text
        button = MagicMock()
        button.text = "NOTIFY ME"  # Changed from "GET NOTIFIED"
        mock_driver.find_elements.return_value = [button]

        # Mock sleep to prevent infinite loop
        mock_sleep.side_effect = lambda x: monitor.stop()

        # Run monitoring
        monitor.monitor()

        # Verify notification was sent for changed button (note the +1 for 1-based indexing)
        monitor.notifier.notify_button_clicked.assert_called_once_with(1, "NOTIFY ME")

    @patch('undetected_chromedriver.Chrome')
    def test_error_handling(self, mock_chrome, monitor, mock_driver):
        """Test error handling during monitoring."""
        mock_chrome.return_value = mock_driver
        monitor.driver = mock_driver
        monitor.target_buttons = [0]
        monitor.button_texts = {0: "GET NOTIFIED"}

        # Simulate a WebDriver exception that triggers stop
        def mock_get(*args):
            monitor.stop()  # Stop the monitor immediately
            raise WebDriverException("Connection lost")
            
        mock_driver.get.side_effect = mock_get
        
        # Start monitoring
        monitor.monitor()

        # Verify cleanup was called
        assert not monitor.is_running
        mock_driver.quit.assert_called_once()
        assert monitor.driver is None

    @patch('undetected_chromedriver.Chrome')
    def test_monitor_without_buttons(self, mock_chrome, monitor):
        """Test monitoring without selected buttons."""
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        monitor.driver = mock_driver
        
        with pytest.raises(ValueError, match="No buttons selected for monitoring"):
            monitor.target_buttons = []  # Ensure no buttons are selected
            monitor.monitor()

    @patch('time.sleep')
    @patch('undetected_chromedriver.Chrome')
    @patch('selenium.webdriver.support.ui.WebDriverWait')
    @patch('selenium.webdriver.support.expected_conditions')
    def test_refresh_interval(self, mock_ec, mock_wait, mock_chrome, mock_sleep, monitor, mock_driver):
        """Test refresh interval timing."""
        mock_chrome.return_value = mock_driver
        monitor.driver = mock_driver
        monitor.target_buttons = [0]
        monitor.button_texts = {0: "GET NOTIFIED"}
        monitor.refresh_interval = 2
        monitor.is_running = True

        # Mock WebDriverWait
        mock_wait_instance = MagicMock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.return_value = True

        # Mock expected conditions
        mock_ec.presence_of_all_elements_located.return_value = MagicMock()

        # Mock find_elements to return unchanged button
        button = MagicMock()
        button.text = "GET NOTIFIED"  # No change
        mock_driver.find_elements.return_value = [button]

        # Mock sleep to stop after first interval
        sleep_calls = []
        def mock_sleep_func(interval):
            sleep_calls.append(interval)
            if len(sleep_calls) >= 2:  # Stop after second sleep call (first is in the loop)
                monitor.stop()

        mock_sleep.side_effect = mock_sleep_func

        # Run monitor for one iteration
        monitor.monitor()

        # Verify sleep was called with correct interval
        assert 2 in sleep_calls, "Sleep should have been called with interval 2"

    @patch('undetected_chromedriver.Chrome')
    def test_setup_driver_error_handling(self, mock_chrome, monitor):
        """Test error handling during driver setup."""
        # Test network error
        mock_chrome.side_effect = WebDriverException("Failed to connect")
        with pytest.raises(WebDriverException, match="Failed to connect"):
            monitor.setup_driver()

        # Test browser crash
        mock_driver = MagicMock()
        mock_driver.get.side_effect = WebDriverException("Browser crashed")
        mock_chrome.side_effect = None
        mock_chrome.return_value = mock_driver
        with pytest.raises(WebDriverException, match="Browser crashed"):
            monitor.setup_driver()

    def test_cleanup_with_active_thread(self, monitor, mock_driver):
        """Test cleanup with an active monitoring thread."""
        monitor.driver = mock_driver
        monitor.is_running = True  # Set initial state
        
        # Mock an active thread
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        mock_thread.join = MagicMock()
        monitor.monitor_thread = mock_thread
        
        # Call cleanup
        monitor.cleanup()
        
        # Verify cleanup sequence
        mock_driver.switch_to.alert.accept.assert_called_once()
        mock_driver.switch_to.window.assert_called_once_with('window1')
        mock_driver.close.assert_called_once()
        mock_driver.quit.assert_called_once()
        assert monitor.driver is None
        
        # Verify thread was properly handled
        mock_thread.join.assert_called_once()  # Should try to join the thread
        assert not monitor.is_running  # Should be set to False after cleanup

    @patch('undetected_chromedriver.Chrome')
    def test_monitor_empty_button_list(self, mock_chrome, monitor):
        """Test monitoring with no buttons selected."""
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        monitor.driver = mock_driver
        
        with pytest.raises(ValueError, match="No buttons selected for monitoring"):
            monitor.target_buttons = []
            monitor.monitor()

    @patch('undetected_chromedriver.Chrome')
    @patch('time.sleep')  # Add sleep mock to prevent actual sleeping
    def test_monitor_button_not_found(self, mock_sleep, mock_chrome, monitor):
        """Test handling of missing buttons during monitoring."""
        # Set up mock driver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        monitor.driver = mock_driver
        monitor.target_buttons = [0]
        monitor.button_texts = {0: "Original Text"}
        monitor.is_running = True
        
        # Set up the button not found sequence
        def find_elements_side_effect(*args, **kwargs):
            monitor.stop()  # Stop immediately after first attempt
            return []  # Return empty list for button search
            
        mock_driver.find_elements.side_effect = find_elements_side_effect
        
        # Mock WebDriverWait to avoid timeouts
        mock_wait = MagicMock()
        mock_wait.until.return_value = True
        
        # Mock sleep to prevent actual sleeping
        def sleep_side_effect(*args):
            monitor.stop()
        mock_sleep.side_effect = sleep_side_effect
        
        with patch('selenium.webdriver.support.ui.WebDriverWait', return_value=mock_wait):
            # Run the monitor
            monitor.monitor()
        
        # Verify the monitor stopped and tried to find buttons
        assert not monitor.is_running
        mock_driver.find_elements.assert_called()
        mock_driver.quit.assert_called_once()

    @patch('undetected_chromedriver.Chrome')
    @patch('time.sleep')  # Add sleep mock to prevent actual sleeping
    def test_monitor_timeout_handling(self, mock_sleep, mock_chrome, monitor):
        """Test handling of timeouts during monitoring."""
        # Set up mock driver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        monitor.driver = mock_driver
        monitor.target_buttons = [0]
        monitor.button_texts = {0: "Original Text"}
        monitor.is_running = True
        
        # Set up the timeout sequence
        def find_elements_side_effect(*args, **kwargs):
            if args[0] == By.CSS_SELECTOR and "button:not(.selection-button)" in args[1]:
                monitor.stop()  # Stop after timeout
                raise TimeoutException("Loading took too long")
            return []
            
        mock_driver.find_elements.side_effect = find_elements_side_effect
        
        # Mock WebDriverWait to simulate timeout
        mock_wait = MagicMock()
        mock_wait.until.side_effect = TimeoutException("Loading took too long")
        with patch('selenium.webdriver.support.ui.WebDriverWait', return_value=mock_wait):
            # Run the monitor
            monitor.monitor()
        
        # Verify the monitor stopped and tried to find buttons
        assert not monitor.is_running
        mock_driver.find_elements.assert_any_call(By.CSS_SELECTOR, "button:not(.selection-button)")
        mock_driver.quit.assert_called_once()

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
"""Tests for the PageMonitor class."""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
import time

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
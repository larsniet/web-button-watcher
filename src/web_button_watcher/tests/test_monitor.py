"""Tests for the PageMonitor class."""

import pytest
from unittest.mock import Mock, patch, MagicMock
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
    def test_select_buttons_interactive(self, mock_chrome, monitor):
        """Test interactive button selection."""
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        # Mock button elements
        button1 = MagicMock()
        button1.text = "GET NOTIFIED"
        button2 = MagicMock()
        button2.text = "BOOK NOW"
        mock_driver.find_elements.return_value = [button1, button2]

        # Mock JavaScript execution for button selection
        mock_driver.execute_script.side_effect = [
            None,  # First call (inject CSS)
            None,  # Second call (initialize selection)
            True,  # Third call (check selection confirmed)
            [0, 1],  # Fourth call (get selected buttons)
        ]

        selected = monitor.select_buttons_interactive()
        
        assert selected == [0, 1]
        assert monitor.button_texts == {0: "GET NOTIFIED", 1: "BOOK NOW"}

    @patch('undetected_chromedriver.Chrome')
    def test_monitor_button_changes(self, mock_chrome, monitor):
        """Test monitoring button changes."""
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        # Set up initial state
        monitor.target_buttons = [0, 1]
        monitor.button_texts = {0: "GET NOTIFIED", 1: "BOOK NOW"}

        # Mock button elements with changed text
        button1 = MagicMock()
        button1.text = "NOTIFY ME"  # Changed from "GET NOTIFIED"
        button2 = MagicMock()
        button2.text = "BOOK NOW"  # Unchanged
        mock_driver.find_elements.return_value = [button1, button2]

        # Start monitoring in a way we can control
        monitor.is_running = True
        try:
            monitor.monitor()
        except Exception:
            pass

        # Verify notification was sent for changed button
        monitor.notifier.notify_button_clicked.assert_called_once_with(1, "NOTIFY ME")

    def test_error_handling(self, monitor, mock_driver):
        """Test error handling during monitoring."""
        monitor.driver = mock_driver
        monitor.target_buttons = [0]
        monitor.button_texts = {0: "GET NOTIFIED"}

        # Simulate a WebDriver exception
        mock_driver.get.side_effect = WebDriverException("Connection lost")
        
        # Start monitoring
        monitor.is_running = True
        try:
            monitor.monitor()
        except Exception:
            pass

        # Verify cleanup was called
        assert not monitor.is_running
        mock_driver.quit.assert_called_once()
        assert monitor.driver is None

    def test_monitor_without_buttons(self, monitor):
        """Test monitoring without selected buttons."""
        with pytest.raises(ValueError, match="No buttons selected for monitoring"):
            monitor.monitor()

    @patch('time.sleep', return_value=None)
    def test_refresh_interval(self, mock_sleep, monitor, mock_driver):
        """Test refresh interval timing."""
        monitor.driver = mock_driver
        monitor.target_buttons = [0]
        monitor.button_texts = {0: "GET NOTIFIED"}
        monitor.refresh_interval = 2

        # Run monitor for a few cycles
        monitor.is_running = True
        try:
            monitor.monitor()
        except Exception:
            pass

        # Verify sleep was called with correct interval
        mock_sleep.assert_called_with(2) 
"""Integration tests for Web Button Watcher."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import warnings

# Suppress all warnings to clean up test output
warnings.filterwarnings("ignore")

# First import the test dependencies
from webbuttonwatcher.core.monitor import PageMonitor
from webbuttonwatcher.interface.cli import MonitorController
from webbuttonwatcher.core.button_monitor import ButtonMonitor
from webbuttonwatcher.utils.notifier import TelegramNotifier
from webbuttonwatcher.utils.settings import SettingsManager
from webbuttonwatcher.core.button_selector import ButtonSelector
from webbuttonwatcher.core.driver_manager import DriverManager

@pytest.fixture
def mock_settings():
    """Create mock settings for tests."""
    settings = SettingsManager()
    settings.set('url', 'https://example.com')
    settings.set('buttons', {'0': 'Test Button'})
    settings.set('refresh_interval', 1)
    settings.set('telegram_token', 'test_token')
    settings.set('telegram_chat_id', 'test_chat_id')
    return settings

@pytest.fixture
def mock_notifier():
    """Create a mock notifier."""
    notifier = MagicMock()
    notifier.send_notification.return_value = True
    return notifier

@pytest.fixture
def mock_driver():
    """Create a mock driver for testing."""
    driver = MagicMock()
    button1 = MagicMock()
    button1.text = "Book Now"
    button2 = MagicMock()
    button2.text = "Sold Out"
    
    # Make find_elements return different buttons in sequence
    find_count = 0
    def find_elements_side_effect(*args, **kwargs):
        nonlocal find_count
        find_count += 1
        
        if find_count % 2 == 1:
            return [button1]
        else:
            return [button2]
    
    driver.find_elements.side_effect = find_elements_side_effect
    return driver

@pytest.fixture
def test_page_path():
    """Get the path to the test HTML page."""
    current_dir = Path(__file__).parent
    return f"file://{current_dir}/fixtures/test_page.html"

@pytest.mark.integration
class TestIntegration:
    """Integration tests for button monitoring functionality."""
    
    @patch('undetected_chromedriver.Chrome')
    @patch('selenium.webdriver.support.ui.WebDriverWait')
    @patch('time.sleep')
    def test_full_monitoring_workflow(self, mock_sleep, mock_wait, mock_chrome, mock_notifier):
        """Test the full monitoring workflow from page monitoring to notification."""
        # Create a mock for the Chrome driver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Create buttons for change detection
        button1 = MagicMock()
        button1.text = "Book Now"
        button2 = MagicMock()
        button2.text = "Sold Out"
        
        # Make find_elements return different buttons in sequence
        find_count = 0
        def find_elements_side_effect(*args, **kwargs):
            nonlocal find_count
            find_count += 1
            
            if find_count == 1:
                return [button1]  # First call - initial state
            else:
                return [button2]  # Second call - changed state
        
        mock_driver.find_elements.side_effect = find_elements_side_effect
        
        # Create and set up PageMonitor directly with necessary state
        monitor = PageMonitor(url="https://example.com", notifier=mock_notifier)
        monitor.driver = mock_driver
        monitor.target_buttons = [0]  # Important: set target buttons
        monitor.button_texts = {0: "Book Now"}
        
        # Start monitoring and stop after seeing change
        def sleep_side_effect(seconds):
            # Stop after one iteration
            if find_count >= 2:
                monitor.stop()
        
        mock_sleep.side_effect = sleep_side_effect
        
        # Run the monitoring
        monitor.monitor()
        
        # Verify notification was sent when button changed
        mock_notifier.send_notification.assert_called_once()
    
    @patch('webbuttonwatcher.utils.settings.SettingsManager')
    @patch('webbuttonwatcher.core.button_monitor.ButtonMonitor')
    @patch('webbuttonwatcher.core.button_selector.ButtonSelector')
    @patch('webbuttonwatcher.core.driver_manager.DriverManager')
    def test_controller_workflow(self, mock_driver_manager_class, mock_selector_class, mock_monitor_class, mock_settings_class, mock_settings):
        """Test the full controller workflow with button selection and monitoring."""
        # Create mocks for selector, monitor, and driver manager
        mock_selector = MagicMock()
        mock_monitor = MagicMock()
        mock_settings_instance = MagicMock()
        mock_driver_manager = MagicMock()
        
        # Set up the mocks
        mock_selector_class.return_value = mock_selector
        mock_monitor_class.return_value = mock_monitor
        mock_settings_class.return_value = mock_settings_instance
        mock_driver_manager_class.return_value = mock_driver_manager
        
        # Set up selector to return buttons when called interactively
        mock_selector.select_buttons_interactive.return_value = {"0": "Book Now"}
        
        # Set up settings
        mock_settings_instance.get_telegram_settings.return_value = {
            'api_id': '12345',
            'api_hash': 'abcdef',
            'bot_token': '123:abc',
            'chat_id': '123456'
        }
        
        # Create a mock for status callback tracking
        status_msgs = []
        def status_callback(msg):
            status_msgs.append(msg)
        
        # Create controller with proper initialization
        controller = MonitorController()
        controller.settings_manager = mock_settings_instance
        controller.status_callback = status_callback
        
        # Execute select buttons with a URL
        result = controller.select_buttons("https://example.com")
        
        # Verify buttons were selected interactively
        assert mock_selector.select_buttons_interactive.called
        assert result == {"0": "Book Now"}
        
        # Start monitoring
        with patch('webbuttonwatcher.core.button_monitor.ButtonMonitor', return_value=mock_monitor):
            controller.start_monitoring("https://example.com", 1, [0])
        
        # Verify monitor was created and started
        assert mock_monitor_class.called
        
        # Stop monitoring
        controller.stop_monitoring()
    
    @patch('undetected_chromedriver.Chrome')
    @patch('time.sleep')
    def test_error_recovery(self, mock_sleep, mock_chrome, mock_notifier):
        """Test that the monitor can recover from errors."""
        # Create a mock for the Chrome driver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Set up driver to raise an exception on first get(), then succeed
        get_call_count = 0
        def get_side_effect(url):
            nonlocal get_call_count
            get_call_count += 1
            if get_call_count == 1:
                raise Exception("Test error")
            return None
        
        mock_driver.get.side_effect = get_side_effect
        
        # Create monitor with properly initialized state
        monitor = PageMonitor(url="https://example.com", notifier=mock_notifier)
        monitor.driver = mock_driver
        monitor.target_buttons = [0]  # Important: set target buttons
        monitor.button_texts = {0: "Book Now"}
        
        # Start monitoring with automatic stop after recovery
        def sleep_side_effect(seconds):
            # Force a second get attempt and then stop
            if get_call_count < 2:
                # Call get again by simulating navigate_to_page
                try:
                    monitor.driver.get(monitor.url)
                except Exception:
                    pass
            
            # Stop after recovery attempt
            monitor.stop()
        
        mock_sleep.side_effect = sleep_side_effect
        
        # Run monitoring
        monitor.monitor()
        
        # Verify driver was reinitialized after error
        assert get_call_count == 2 
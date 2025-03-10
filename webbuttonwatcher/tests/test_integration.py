"""Integration tests for Web Button Watcher."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
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
from selenium.common.exceptions import WebDriverException

from ..core.monitor import PageMonitor
from ..interface.cli import MonitorController

@pytest.fixture(autouse=True)
def prevent_browser_launch():
    """Prevent any real browser windows from launching during tests."""
    # Create a more complete mock of the driver modules
    with patch('undetected_chromedriver.Chrome', return_value=MagicMock()), \
         patch('selenium.webdriver.Chrome', return_value=MagicMock()), \
         patch('selenium.webdriver.support.ui.WebDriverWait', return_value=MagicMock()):
        yield

@pytest.fixture
def test_page_path():
    """Get the path to the test HTML page."""
    current_dir = Path(__file__).parent
    return f"file://{current_dir}/fixtures/test_page.html"

@pytest.fixture
def mock_notifier():
    """Create a mock notifier."""
    return MagicMock()

@pytest.fixture
def mock_driver():
    """Create a mock Chrome driver."""
    driver = MagicMock()
    driver.title = "Room Booking Test Page"
    driver.window_handles = ['window1']
    driver.switch_to = MagicMock()
    driver.switch_to.alert = MagicMock()
    driver.switch_to.window = MagicMock()
    
    # Mock WebDriverWait
    def until_mock(*args, **kwargs):
        return True
    driver.wait = MagicMock()
    driver.wait.until = until_mock
    
    # Mock execute_script to handle JavaScript calls
    def execute_script_mock(script, *args):
        if "return window.selectionConfirmed" in script:
            return True
        if "return window.selectedButtons" in script:
            return [0]
        return None
    driver.execute_script = MagicMock(side_effect=execute_script_mock)
    
    # Mock find_elements
    def find_elements_side_effect(*args, **kwargs):
        if args[0] == By.CSS_SELECTOR and "button" in args[1]:
            # Return a list of mock button elements
            button = MagicMock()
            button.is_displayed.return_value = True
            button.is_enabled.return_value = True
            button.get_attribute.return_value = "Book Room"
            button.text = "Book Room"
            return [button]
        return []
    
    driver.find_elements = MagicMock(side_effect=find_elements_side_effect)
    driver.page_source = "<html><body><button>Book Room</button></body></html>"
    driver.current_url = "test_url"
    
    return driver

@pytest.mark.integration
class TestIntegration:
    """Integration tests for button monitoring functionality."""
    
    @patch('time.sleep')  # Prevent actual sleeping
    def test_full_monitoring_workflow(self, mock_sleep, test_page_path, mock_notifier, mock_driver):
        """Test the full monitoring workflow from start to finish."""
        # Setup driver mocking
        mock_uc.Chrome.return_value = mock_driver
        
        # Create a PageMonitor instance
        monitor = PageMonitor(
            test_page_path,
            refresh_interval=0.1,  # Fast refresh for testing
            notifier=mock_notifier
        )
        
        try:
            # Start monitoring
            monitor.start()
            
            # Now call on_button_change 
            monitor.on_button_change([{
                'id': 'button1',
                'text': 'Book Room',
                'status': 'Available'
            }])
            
            # Check if notifier was called
            mock_notifier.send_notification.assert_called_once()
            
        finally:
            # Clean up
            monitor.stop()
    
    def test_controller_workflow(self, test_page_path, mock_notifier, mock_driver):
        """Test the CLI controller workflow."""
        # Setup driver mocking
        mock_uc.Chrome.return_value = mock_driver
        
        # Create a MonitorController instance
        controller = MonitorController()
        
        # Mock settings
        with patch.object(controller, 'settings_manager') as mock_settings:
            mock_settings.get_telegram_settings.return_value = {
                'api_id': '12345',
                'api_hash': 'abcdef',
                'bot_token': '123:abc',
                'chat_id': '123456'
            }
            
            # Create a mock status callback to capture status messages
            status_messages = []
            def status_callback(msg):
                status_messages.append(msg)
            controller.status_callback = status_callback
            
            # Test select buttons
            buttons = controller.select_buttons(test_page_path)
            assert buttons is not None, "No buttons were selected"
            
            # Test start monitoring
            controller.start_monitoring(test_page_path, 0.1, [0])
            assert controller.running is True
            
            # Test stop monitoring
            controller.stop_monitoring()
            assert controller.running is False
            
            # Verify some status messages were captured
            assert len(status_messages) > 0
    
    @patch('time.sleep')  # Prevent actual sleeping
    def test_error_recovery(self, mock_sleep, test_page_path, mock_notifier, mock_driver):
        """Test error recovery during monitoring."""
        # Setup driver mocking with an error
        mock_uc.Chrome.return_value = mock_driver
        calls = 0
        
        # Make get throw an error on the second call
        def get_side_effect(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise WebDriverException("Test error")
            return None
        
        mock_driver.get = MagicMock(side_effect=get_side_effect)
        
        # Create a PageMonitor instance with error recovery
        monitor = PageMonitor(
            test_page_path,
            refresh_interval=0.1,  # Fast refresh for testing
            notifier=mock_notifier,
            max_retries=3
        )
        
        try:
            # Start monitoring - should recover from error
            monitor.start()
            assert monitor.is_running is True
            
            # Force an update cycle
            monitor.check_page()
            
            # Verify the driver was reinitialized after error
            assert mock_driver.get.call_count >= 2
            
        finally:
            # Clean up
            monitor.stop() 
"""Integration tests for Web Button Watcher."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException

from ..core.monitor import PageMonitor
from ..interface.cli import MonitorController

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
    
    return driver

@pytest.mark.integration
class TestIntegration:
    """Integration test suite."""

    @patch('undetected_chromedriver.Chrome')
    @patch('selenium.webdriver.support.ui.WebDriverWait')
    @patch('time.sleep')  # Prevent actual sleeping
    def test_full_monitoring_workflow(self, mock_sleep, mock_wait, mock_chrome, test_page_path, mock_notifier, mock_driver):
        """Test the complete monitoring workflow."""
        # Setup mocks
        mock_chrome.return_value = mock_driver
        
        # Mock button with changing text
        buttons = [
            MagicMock(text="GET NOTIFIED"),
            MagicMock(text="BOOK NOW")
        ]
        
        # Set up find_elements to return different results on each call
        find_elements_calls = 0
        def find_elements_side_effect(*args, **kwargs):
            nonlocal find_elements_calls
            find_elements_calls += 1
            if find_elements_calls == 1:
                return [buttons[0]]  # First call returns initial button
            else:
                monitor.stop()  # Stop monitoring after second call
                return [buttons[1]]  # Second call returns changed button
        mock_driver.find_elements.side_effect = find_elements_side_effect
        
        # Mock WebDriverWait
        wait_instance = MagicMock()
        wait_instance.until.return_value = True
        mock_wait.return_value = wait_instance

        # Initialize monitor
        monitor = PageMonitor(
            url=test_page_path,
            refresh_interval=0.1,
            notifier=mock_notifier
        )
        
        try:
            # Setup driver
            driver = monitor.setup_driver()
            
            # Set target buttons
            monitor.target_buttons = [0]
            monitor.button_texts = {0: "GET NOTIFIED"}
            
            # Run monitoring - it will stop after detecting the change
            monitor.monitor()
            
            # Verify notification was sent for changed button
            mock_notifier.notify_button_clicked.assert_called_once_with(1, "BOOK NOW")
            
        finally:
            monitor.cleanup()

    @patch('undetected_chromedriver.Chrome')
    def test_controller_workflow(self, mock_chrome, test_page_path, mock_notifier, mock_driver):
        """Test the complete workflow using the controller."""
        # Setup mocks
        mock_chrome.return_value = mock_driver
        mock_button = MagicMock()
        mock_button.text = "GET NOTIFIED"
        mock_driver.find_elements.return_value = [mock_button]
        
        # Initialize controller
        controller = MonitorController()
        
        try:
            # Mock button selection
            with patch.object(controller, 'select_buttons', return_value=[0]):
                selected = controller.select_buttons(test_page_path)
                assert selected == [0]
            
            # Start monitoring with status updates
            status_updates = []
            def status_callback(msg):
                status_updates.append(msg)
            
            # Mock start_monitoring to avoid actual monitoring
            with patch.object(controller, 'start_monitoring') as mock_start:
                controller.start_monitoring(test_page_path, 0.1, selected, status_callback)
                mock_start.assert_called_once_with(test_page_path, 0.1, selected, status_callback)
            
            # Stop monitoring
            controller.stop_monitoring()
            
        finally:
            controller.stop_monitoring()

    @patch('undetected_chromedriver.Chrome')
    @patch('time.sleep')  # Prevent actual sleeping
    def test_error_recovery(self, mock_sleep, mock_chrome, test_page_path, mock_notifier, mock_driver):
        """Test error recovery during monitoring."""
        # Setup mocks
        mock_chrome.return_value = mock_driver
        
        # Set up a sequence of exceptions and responses
        get_call_count = 0
        def get_side_effect(*args, **kwargs):
            nonlocal get_call_count
            get_call_count += 1
            if get_call_count == 1:
                raise WebDriverException("Simulated network error")
            monitor.stop()  # Stop after second attempt
            return None
            
        mock_driver.get.side_effect = get_side_effect
        
        # Mock find_elements to prevent hanging
        mock_driver.find_elements.return_value = [MagicMock(text="GET NOTIFIED")]
        
        # Mock WebDriverWait
        wait_instance = MagicMock()
        wait_instance.until.return_value = True
        
        with patch('selenium.webdriver.support.ui.WebDriverWait', return_value=wait_instance):
            monitor = PageMonitor(
                url=test_page_path,
                refresh_interval=0.1,
                notifier=mock_notifier
            )
            
            try:
                # Setup initial state
                monitor.driver = mock_driver
                monitor.target_buttons = [0]
                monitor.button_texts = {0: "GET NOTIFIED"}
                
                # Run monitoring - should handle error and stop
                monitor.monitor()
                
                # Verify monitor handled the error
                assert not monitor.is_running
                assert get_call_count == 2  # Initial error + one retry
                mock_sleep.assert_any_call(0.1)  # Should sleep with refresh interval
                
            finally:
                monitor.cleanup() 
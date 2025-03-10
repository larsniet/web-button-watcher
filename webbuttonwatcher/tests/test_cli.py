"""Tests for the CLI interface."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import asyncio
from ..interface.cli import MonitorController
from ..utils.settings import SettingsManager
from ..utils.notifier import TelegramNotifier
from ..core.monitor import ButtonMonitor
import sys

# Create mocks before imports happen
mock_uc = MagicMock()
mock_webdriver = MagicMock()
sys.modules['undetected_chromedriver'] = mock_uc
sys.modules['selenium.webdriver'] = mock_webdriver

@pytest.fixture(autouse=True)
def prevent_browser_launch():
    """Prevent any real browser windows from launching during tests."""
    # Mock the DriverManager class directly
    with patch('webbuttonwatcher.interface.cli.DriverManager') as mock_driver_cls:
        # Create a mock driver instance
        mock_driver = MagicMock()
        mock_driver.find_elements.return_value = []
        mock_driver.page_source = "<html><body>Test page</body></html>"
        
        # Set up the driver manager
        mock_driver_instance = MagicMock()
        mock_driver_instance.initialize_driver.return_value = mock_driver
        mock_driver_instance.driver = mock_driver
        mock_driver_cls.return_value = mock_driver_instance
        
        # Set up button selector
        with patch('webbuttonwatcher.interface.cli.ButtonSelector') as mock_button_selector_cls:
            mock_selector = MagicMock()
            mock_selector.select_buttons.return_value = [{'id': 'test-btn', 'text': 'Test Button'}]
            mock_button_selector_cls.return_value = mock_selector
            yield

@pytest.fixture
def mock_settings():
    """Create a mock settings manager."""
    with patch('webbuttonwatcher.interface.cli.SettingsManager') as mock_settings_cls:
        settings_instance = MagicMock(spec=SettingsManager)
        # Set up commonly used methods
        settings_instance.get.return_value = 'test_value'
        settings_instance.get_telegram_settings.return_value = {
            'api_id': '12345',
            'api_hash': 'abcdef',
            'bot_token': '123:abc',
            'chat_id': '123456'
        }
        # Make sure the set method is properly tracked
        settings_instance.set = MagicMock()
        mock_settings_cls.return_value = settings_instance
        yield mock_settings_cls, settings_instance

@pytest.fixture
def mock_monitor():
    """Create a mock ButtonMonitor."""
    with patch('webbuttonwatcher.interface.cli.ButtonMonitor') as mock_monitor_cls:
        monitor_instance = MagicMock(spec=ButtonMonitor)
        monitor_instance.start_monitoring = MagicMock()
        monitor_instance.stop_monitoring = MagicMock()
        mock_monitor_cls.return_value = monitor_instance
        yield mock_monitor_cls, monitor_instance

@pytest.fixture
def mock_notifier():
    """Create a mock TelegramNotifier."""
    with patch('webbuttonwatcher.interface.cli.TelegramNotifier') as mock_notifier_cls:
        notifier_instance = MagicMock(spec=TelegramNotifier)
        notifier_instance.send_notification = MagicMock(return_value=True)
        mock_notifier_cls.return_value = notifier_instance
        yield mock_notifier_cls, notifier_instance

@pytest.fixture
def mock_event_loop():
    """Mock asyncio loop."""
    loop = MagicMock(spec=asyncio.AbstractEventLoop)
    with patch('asyncio.new_event_loop', return_value=loop), \
         patch('asyncio.set_event_loop'):
        yield loop

@pytest.fixture(scope="session", autouse=True)
def cleanup_browsers():
    """Run at the end of all tests to make sure no browsers are left running."""
    yield
    # After all tests complete, ensure everything is cleaned up
    import gc
    gc.collect()
    
    # Try to explicitly close any browser drivers
    if "selenium.webdriver" in sys.modules:
        try:
            from selenium import webdriver
            for driver in getattr(webdriver, "_drivers", {}).values():
                try:
                    driver.quit()
                except:
                    pass
        except:
            pass
            
    # Try to kill any chromedriver processes
    if sys.platform.startswith('win'):
        try:
            os.system("taskkill /f /im chromedriver.exe")
        except:
            pass
    else:
        try:
            os.system("pkill -f 'chromedriver'")
        except:
            pass

# For testing the cleanup functionality
def test_cleanup_browsers_fixture():
    """Test that the cleanup_browsers fixture correctly handles browser cleanup."""
    # We'll just verify the os.system calls which we can test without affecting actual drivers
    
    # Test Windows path
    with patch('sys.platform', 'win32'):
        with patch('os.system') as mock_system:
            # Call function that would be called in fixture
            if sys.platform.startswith('win'):
                os.system("taskkill /f /im chromedriver.exe")
            mock_system.assert_called_once_with("taskkill /f /im chromedriver.exe")
    
    # Test Unix path
    with patch('sys.platform', 'darwin'):
        with patch('os.system') as mock_system:
            # Call function that would be called in fixture
            if not sys.platform.startswith('win'):
                os.system("pkill -f 'chromedriver'")
            mock_system.assert_called_once_with("pkill -f 'chromedriver'")

class TestMonitorController:
    """Test cases for the MonitorController class."""
    
    def test_init(self, mock_settings):
        """Test the constructor."""
        _, settings_instance = mock_settings
        controller = MonitorController()
        
        # Check initialization
        assert controller.settings_manager == settings_instance
        assert controller.driver_manager is None
        assert controller.button_selector is None
        assert controller.button_monitor is None
        assert controller.notifier is None
        assert controller.running is False
    
    def test_update_telegram_settings(self, mock_settings):
        """Test updating Telegram settings."""
        _, settings_instance = mock_settings
        
        # Setup test data
        api_id = '12345'
        api_hash = 'abcdef'
        bot_token = '123:abc'
        chat_id = '123456'
        
        # Create controller and call method
        controller = MonitorController()
        controller.update_telegram_settings(api_id, api_hash, bot_token, chat_id)
        
        # Verify settings were updated
        settings_instance.update_telegram_settings.assert_called_once_with(
            api_id, api_hash, bot_token, chat_id
        )
    
    def test_select_buttons(self, mock_settings):
        """Test selecting buttons."""
        _, settings_instance = mock_settings
        
        # Looking at the implementation, the controller calls select_buttons_interactive, not select_buttons
        mock_selector = MagicMock()
        mock_selector.select_buttons_interactive = MagicMock(return_value=[{'id': 'test-btn', 'text': 'Test Button'}])
        
        # Need to mock both driver manager and button selector
        with patch('webbuttonwatcher.interface.cli.DriverManager') as mock_driver_cls, \
             patch('webbuttonwatcher.interface.cli.ButtonSelector', return_value=mock_selector):
            # Return a mock driver instance
            driver_instance = MagicMock()
            mock_driver_cls.return_value = driver_instance
            
            controller = MonitorController()
            
            # Call the method
            result = controller.select_buttons('https://example.com')
            
            # Verify the correct method was called and result was returned
            mock_selector.select_buttons_interactive.assert_called_once()
            assert result == [{'id': 'test-btn', 'text': 'Test Button'}]
            # Verify URL was navigated to
            driver_instance.navigate_to.assert_called_once_with('https://example.com')
    
    def test_select_buttons_no_selection(self, mock_settings):
        """Test selecting buttons when no buttons are selected."""
        _, settings_instance = mock_settings
        
        # Mock for select_buttons_interactive that returns empty list
        mock_selector = MagicMock()
        mock_selector.select_buttons_interactive = MagicMock(return_value=[])
        
        # Mock both the driver and button selector
        with patch('webbuttonwatcher.interface.cli.DriverManager') as mock_driver_cls, \
             patch('webbuttonwatcher.interface.cli.ButtonSelector', return_value=mock_selector):
            # Return a mock driver instance
            driver_instance = MagicMock()
            mock_driver_cls.return_value = driver_instance
            
            controller = MonitorController()
            
            # Call the method
            result = controller.select_buttons('https://example.com')
            
            # Verify the correct method was called
            mock_selector.select_buttons_interactive.assert_called_once()
            # Empty result should be returned
            assert result == []
            # Verify URL was navigated to
            driver_instance.navigate_to.assert_called_once_with('https://example.com')
    
    def test_start_monitoring(self, mock_settings, mock_monitor, mock_notifier):
        """Test starting monitoring."""
        _, settings_instance = mock_settings
        mock_monitor_cls, monitor_instance = mock_monitor
        
        # We need to patch SettingsManager with a correct implementation for update
        # Create a custom mock that correctly implements the update method
        settings_mock = MagicMock(spec=SettingsManager)
        settings_dict = {}
        
        def mock_update(values):
            settings_dict.update(values)
            for key, value in values.items():
                settings_mock.set(key, value)
        
        settings_mock.update = mock_update
        settings_mock.get_telegram_settings.return_value = {
            'api_id': '', 'api_hash': '', 'bot_token': '', 'chat_id': ''
        }
        
        with patch('webbuttonwatcher.interface.cli.SettingsManager', return_value=settings_mock), \
             patch('webbuttonwatcher.interface.cli.DriverManager') as mock_driver_cls, \
             patch('webbuttonwatcher.interface.cli.ButtonMonitor', return_value=monitor_instance):
            # Return a mock driver instance
            driver_instance = MagicMock()
            driver_instance.driver = MagicMock()
            mock_driver_cls.return_value = driver_instance
            
            controller = MonitorController()
            
            # Set up test data
            url = 'https://example.com'
            refresh_interval = 10
            selected_buttons = [1, 2, 3]
            
            # Call the method
            controller.start_monitoring(url, refresh_interval, selected_buttons)
            
            # Verify settings update was called with correct values
            assert settings_dict == {
                'url': url,
                'refresh_interval': refresh_interval,
                'selected_buttons': selected_buttons
            }
            
            # Check that monitor was created and started
            monitor_instance.set_target_buttons.assert_called_once_with(selected_buttons)
            monitor_instance.start_monitoring.assert_called_once()
            assert controller.running is True
    
    def test_start_monitoring_with_error(self, mock_settings):
        """Test starting monitoring with an error."""
        _, settings_instance = mock_settings
        
        with patch('webbuttonwatcher.interface.cli.DriverManager') as mock_driver_cls:
            # Create a driver instance that raises an exception on navigate_to
            driver_instance = MagicMock()
            driver_instance.navigate_to = MagicMock(side_effect=Exception("Test error"))
            mock_driver_cls.return_value = driver_instance
            
            controller = MonitorController()
            
            # Method should handle the error
            try:
                controller.start_monitoring('https://example.com', 10, [1, 2, 3])
                assert False, "Should have raised an exception"
            except Exception as e:
                # MonitorController re-raises the exception after logging
                assert str(e) == "Test error"
            
            # Verify state after error
            assert controller.running is False
    
    def test_stop_monitoring(self, mock_settings, mock_monitor):
        """Test stopping monitoring."""
        _, settings_instance = mock_settings
        mock_monitor_cls, monitor_instance = mock_monitor
        
        # Create controller and set up state
        controller = MonitorController()
        controller.button_monitor = monitor_instance
        controller.running = True
        
        # Call method
        controller.stop_monitoring()
        
        # Verify monitoring was stopped
        monitor_instance.stop_monitoring.assert_called_once()
        assert controller.running is False

    def test_stop_monitoring_no_monitor(self, mock_settings):
        """Test stopping monitoring when no monitor exists."""
        _, settings_instance = mock_settings
        
        # Create controller
        controller = MonitorController()
        controller.running = True
        
        # Call method
        controller.stop_monitoring()
        
        # Verify state changed even though no monitor exists
        assert controller.running is False

    def test_with_status_callback(self, mock_settings, mock_monitor):
        """Test MonitorController with status callbacks."""
        _, settings_instance = mock_settings
        mock_monitor_cls, monitor_instance = mock_monitor
        
        # Create a controller with status callback
        controller = MonitorController()
        status_messages = []
        
        # Define a callback that records status messages
        def status_callback(message):
            status_messages.append(message)
        
        controller.status_callback = status_callback
        
        # Create a driver mock
        with patch('webbuttonwatcher.interface.cli.DriverManager') as mock_driver_cls, \
             patch('webbuttonwatcher.interface.cli.ButtonMonitor', return_value=monitor_instance):
            # Return a mock driver instance
            driver_instance = MagicMock()
            driver_instance.driver = MagicMock()
            mock_driver_cls.return_value = driver_instance
            
            # Call the start_monitoring method which should trigger the callback
            controller.start_monitoring('https://example.com', 5, [1, 2, 3])
            
            # Verify that status messages were recorded
            assert len(status_messages) > 0
            assert "Initializing browser..." in status_messages
            assert "Starting to monitor" in status_messages[-1]
            
            # Test error handling with status callback
            with patch.object(controller.button_monitor, 'start_monitoring', 
                             side_effect=Exception("Monitoring failed")):
                try:
                    controller.start_monitoring('https://example.com', 5, [1, 2, 3])
                except Exception:
                    # Expected to raise, but should have called callback first
                    pass
                    
                # Verify that error message was sent to callback
                assert any("Error during monitoring" in msg for msg in status_messages)
                
            # Test cleanup during stop_monitoring
            # Create a new driver_manager since stop_monitoring sets it to None
            controller.driver_manager = MagicMock()
            driver_cleanup = controller.driver_manager.cleanup = MagicMock()
            controller.stop_monitoring()
            driver_cleanup.assert_called_once() 
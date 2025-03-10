"""Tests for the CLI interface."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import asyncio
from ..interface.cli import MonitorController
from ..utils.settings import SettingsManager
from ..utils.notifier import TelegramNotifier
from ..core.monitor import PageMonitor

@pytest.fixture
def mock_settings():
    """Create a mock settings manager."""
    with patch('webbuttonwatcher.interface.cli.SettingsManager') as mock_settings:
        settings_instance = MagicMock(spec=SettingsManager)
        settings_instance.get.return_value = 'test_value'
        settings_instance.get_telegram_settings.return_value = {
            'api_id': '12345',
            'api_hash': 'abcdef',
            'bot_token': '123:abc',
            'chat_id': '123456'
        }
        mock_settings.return_value = settings_instance
        yield mock_settings

@pytest.fixture
def mock_monitor():
    """Create a mock PageMonitor."""
    with patch('webbuttonwatcher.interface.cli.PageMonitor') as mock_monitor:
        monitor_instance = Mock()
        monitor_instance.select_buttons_interactive.return_value = [0, 1]
        monitor_instance.driver = Mock()
        mock_monitor.return_value = monitor_instance
        yield monitor_instance

@pytest.fixture
def mock_notifier():
    """Create a mock TelegramNotifier."""
    with patch('webbuttonwatcher.interface.cli.TelegramNotifier') as mock_notifier:
        notifier_instance = Mock()
        mock_notifier.return_value = notifier_instance
        yield notifier_instance

@pytest.fixture
def mock_event_loop():
    """Create a mock event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    if not loop.is_closed():
        loop.close()

class TestMonitorController:
    """Test suite for MonitorController class."""

    def test_init(self, mock_settings):
        """Test controller initialization."""
        controller = MonitorController()
        assert controller.monitor is None
        assert controller.notifier is None
        assert controller.running is False
        assert controller.settings_manager == mock_settings

    def test_update_telegram_settings(self, mock_settings):
        """Test updating Telegram settings."""
        controller = MonitorController()
        
        # Update settings
        controller.update_telegram_settings('12345', 'test_hash', 'test_token', '67890')
        
        # Verify settings were updated
        mock_settings.update_telegram_settings.assert_called_once_with(
            '12345', 'test_hash', 'test_token', '67890'
        )
        
        # Verify environment variables were set
        assert os.environ['TELEGRAM_API_ID'] == '12345'
        assert os.environ['TELEGRAM_API_HASH'] == 'test_hash'
        assert os.environ['TELEGRAM_BOT_TOKEN'] == 'test_token'
        assert os.environ['TELEGRAM_CHAT_ID'] == '67890'

    def test_select_buttons(self, mock_settings, mock_monitor):
        """Test button selection."""
        controller = MonitorController()
        url = 'https://example.com'
        
        # Select buttons
        selected = controller.select_buttons(url)
        
        # Verify monitor was used correctly
        assert selected == [0, 1]
        mock_monitor.select_buttons_interactive.assert_called_once()
        mock_monitor.driver.quit.assert_called_once()
        
        # Verify settings were saved
        mock_settings.set.assert_any_call('selected_buttons', [0, 1])
        mock_settings.set.assert_any_call('url', url)

    def test_select_buttons_no_selection(self, mock_settings, mock_monitor):
        """Test button selection when no buttons are selected."""
        controller = MonitorController()
        mock_monitor.select_buttons_interactive.return_value = []
        
        # Select buttons
        selected = controller.select_buttons('https://example.com')
        
        # Verify no settings were saved
        assert selected == []
        mock_settings.set.assert_not_called()

    def test_start_monitoring(self, mock_settings, mock_monitor, mock_notifier, mock_event_loop):
        """Test starting the monitoring process."""
        controller = MonitorController()
        url = 'https://example.com'
        refresh_interval = 1.0
        selected_buttons = [0, 1]
        status_callback = Mock()
        
        # Start monitoring
        controller.start_monitoring(url, refresh_interval, selected_buttons, status_callback)
        
        # Verify settings were saved
        mock_settings.update.assert_called_once_with({
            'url': url,
            'refresh_interval': refresh_interval,
            'selected_buttons': selected_buttons
        })
        
        # Verify monitor was set up correctly
        assert controller.monitor == mock_monitor
        mock_monitor.setup_driver.assert_called_once()
        assert mock_monitor.target_buttons == selected_buttons
        mock_monitor.monitor.assert_called_once()
        
        # Verify status callback was called
        status_callback.assert_called_once_with("Monitoring buttons: [1, 2]")

    def test_start_monitoring_with_error(self, mock_settings, mock_monitor, mock_event_loop):
        """Test monitoring process with error."""
        controller = MonitorController()
        error_message = "Test error"
        mock_monitor.monitor.side_effect = Exception(error_message)
        status_callback = Mock()
        
        # Mock TelegramNotifier to avoid initialization issues
        with patch('webbuttonwatcher.interface.cli.TelegramNotifier') as mock_notifier:
            # Start monitoring and expect error
            with pytest.raises(Exception) as exc_info:
                controller.start_monitoring('https://example.com', 1.0, [0, 1], status_callback)
            
            # Verify error was handled correctly
            assert error_message in str(exc_info.value)
            status_callback.assert_any_call(f"Monitor error: {error_message}")
            assert controller.running is False

    def test_stop_monitoring(self, mock_settings, mock_monitor):
        """Test stopping the monitoring process."""
        controller = MonitorController()
        controller.monitor = mock_monitor
        controller.running = True
        
        # Stop monitoring
        controller.stop_monitoring()
        
        # Verify monitor was cleaned up
        assert controller.running is False
        mock_monitor.driver.quit.assert_called_once()
        assert controller.monitor is None

    def test_stop_monitoring_no_monitor(self, mock_settings):
        """Test stopping when no monitor exists."""
        controller = MonitorController()
        controller.running = True
        
        # Stop monitoring
        controller.stop_monitoring()
        
        # Verify state was updated
        assert controller.running is False
        assert controller.monitor is None 
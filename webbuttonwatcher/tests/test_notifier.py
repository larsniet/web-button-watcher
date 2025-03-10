"""Tests for the Telegram notifier."""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from ..utils.notifier import TelegramNotifier
from ..utils.settings import SettingsManager

# Remove the asyncio mark since the tests are synchronous
# pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_settings():
    """Create a mock settings manager."""
    settings = MagicMock(spec=SettingsManager)
    settings.get_telegram_settings.return_value = {
        'api_id': '12345',
        'api_hash': 'abcdef',
        'bot_token': '123:abc',
        'chat_id': '123456'
    }
    return settings

class TestTelegramNotifier:
    """Test the TelegramNotifier class."""
    
    def test_init(self, mock_settings):
        """Test initialization with settings."""
        # Create notifier
        notifier = TelegramNotifier(settings_manager=mock_settings)
        
        # Verify settings were loaded
        assert notifier.settings_manager == mock_settings
        assert notifier.telegram_settings == mock_settings.get_telegram_settings.return_value
    
    def test_init_with_no_settings(self):
        """Test initialization with no settings provided."""
        with patch('webbuttonwatcher.utils.notifier.SettingsManager') as mock_settings_cls:
            settings_instance = MagicMock(spec=SettingsManager)
            settings_instance.get_telegram_settings.return_value = {
                'api_id': '',
                'api_hash': '',
                'bot_token': '',
                'chat_id': ''
            }
            mock_settings_cls.return_value = settings_instance
            
            # Create notifier
            notifier = TelegramNotifier()
            
            # Verify settings were loaded
            assert notifier.settings_manager == settings_instance
            assert notifier.telegram_settings == settings_instance.get_telegram_settings.return_value
            
    def test_send_notification_success(self, mock_settings):
        """Test sending notification successfully."""
        # Setup mocks for TelegramClient
        mock_client = MagicMock()
        mock_client.start = MagicMock(return_value=None)
        mock_client.disconnect = MagicMock(return_value=None)
        mock_client.loop = MagicMock()
        mock_client.loop.run_until_complete = MagicMock(return_value=None)
        
        mock_telegram_client_cls = MagicMock(return_value=mock_client)
        
        # Create the notifier
        notifier = TelegramNotifier(settings_manager=mock_settings)
        
        # Patch both the import and the TelegramClient class
        with patch.dict('sys.modules', {'telethon': MagicMock()}), \
             patch('telethon.TelegramClient', mock_telegram_client_cls):
            
            # Call the method
            result = notifier.send_notification("Test message")
            
            # Verify
            assert result is True
            mock_telegram_client_cls.assert_called_once()
            mock_client.start.assert_called_once_with(bot_token='123:abc')
            mock_client.loop.run_until_complete.assert_called_once()
            mock_client.disconnect.assert_called_once()
        
    def test_send_notification_missing_settings(self, mock_settings):
        """Test sending notification with missing Telegram settings."""
        with patch('webbuttonwatcher.utils.notifier.SettingsManager') as mock_settings_cls:
            settings_instance = MagicMock(spec=SettingsManager)
            settings_instance.get_telegram_settings.return_value = {
                'api_id': '',
                'api_hash': '',
                'bot_token': '',
                'chat_id': ''
            }
            mock_settings_cls.return_value = settings_instance
            
            # Create notifier and attempt to send
            notifier = TelegramNotifier()
            result = notifier.send_notification("Test message")
            
            # Verify send was not attempted
            assert result is False
    
    def test_send_notification_import_error(self, mock_settings):
        """Test sending notification with ImportError."""
        # Create the notifier
        notifier = TelegramNotifier(settings_manager=mock_settings)
        
        # Simulate ImportError
        with patch.dict('sys.modules', {'telethon': None}), \
             patch('builtins.__import__', side_effect=ImportError("No module named 'telethon'")):
            
            # Call the method
            result = notifier.send_notification("Test message")
            
            # Verify
            assert result is False
    
    @patch('webbuttonwatcher.utils.notifier.logger.error')
    def test_send_notification_general_error(self, mock_logging, mock_settings):
        """Test sending notification with general error."""
        # Setup mock for TelegramClient
        mock_client = MagicMock()
        mock_client.start = MagicMock(side_effect=Exception("Test error"))
        mock_telegram_client_cls = MagicMock(return_value=mock_client)
        
        # Create the notifier
        notifier = TelegramNotifier(settings_manager=mock_settings)
        
        # Patch both the import and the TelegramClient class
        with patch.dict('sys.modules', {'telethon': MagicMock()}), \
             patch('telethon.TelegramClient', mock_telegram_client_cls):
            
            # Call the method
            result = notifier.send_notification("Test message")
            
            # Verify
            assert result is False
            mock_logging.assert_called_with("Error sending Telegram notification: Test error") 
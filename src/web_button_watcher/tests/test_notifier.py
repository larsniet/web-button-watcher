"""Tests for the Telegram notifier."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from ..utils.notifier import TelegramNotifier
from ..utils.settings import Settings

@pytest.fixture
def mock_settings():
    """Create a mock settings with valid Telegram credentials."""
    with patch('web_button_watcher.utils.notifier.Settings') as mock_settings:
        settings_instance = Mock()
        settings_instance.get_telegram_settings.return_value = {
            'api_id': '12345',
            'api_hash': 'test_hash',
            'bot_token': 'test_token',
            'chat_id': '67890'
        }
        mock_settings.return_value = settings_instance
        yield mock_settings

@pytest.fixture
def mock_telegram_client():
    """Create a mock Telegram client."""
    with patch('web_button_watcher.utils.notifier.TelegramClient') as mock_client:
        client_instance = MagicMock()
        client_instance.start = AsyncMock()
        client_instance.send_message = AsyncMock()
        client_instance.disconnect = AsyncMock()
        mock_client.return_value = client_instance
        yield client_instance

@pytest.mark.asyncio
class TestTelegramNotifier:
    """Test suite for TelegramNotifier class."""

    async def test_init_with_valid_credentials(self, mock_settings, mock_telegram_client):
        """Test initialization with valid credentials."""
        notifier = TelegramNotifier()
        await notifier.initialize()
        
        # Verify settings were loaded
        assert notifier.api_id == 12345
        assert notifier.api_hash == 'test_hash'
        assert notifier.bot_token == 'test_token'
        assert notifier.chat_id == 67890
        
        # Verify client was initialized
        mock_telegram_client.start.assert_awaited_once_with(bot_token='test_token')
        mock_telegram_client.send_message.assert_awaited_once_with(67890, "🤖 Bot initialized and ready to monitor buttons!")
        await notifier.cleanup()

    async def test_init_with_invalid_api_id(self, mock_settings):
        """Test initialization with invalid API ID."""
        mock_settings.return_value.get_telegram_settings.return_value = {
            'api_id': 'not_a_number',
            'api_hash': 'test_hash',
            'bot_token': 'test_token',
            'chat_id': '67890'
        }
        
        with pytest.raises(ValueError, match="API_ID and CHAT_ID must be integers"):
            TelegramNotifier()

    async def test_init_with_missing_credentials(self, mock_settings):
        """Test initialization with missing credentials."""
        mock_settings.return_value.get_telegram_settings.return_value = {
            'api_id': '',
            'api_hash': '',
            'bot_token': '',
            'chat_id': ''
        }
        
        with pytest.raises(ValueError, match="Missing Telegram credentials"):
            TelegramNotifier()

    async def test_notify_button_clicked_success(self, mock_settings, mock_telegram_client):
        """Test successful button click notification."""
        notifier = TelegramNotifier()
        await notifier.initialize()
        mock_telegram_client.send_message.reset_mock()  # Reset after init
        
        # Test notification
        result = await notifier.notify_button_clicked(1, "BOOK NOW")
        
        # Verify message was sent
        mock_telegram_client.send_message.assert_awaited_once_with(67890, "🔔 Button 1 changed to: BOOK NOW")
        assert result is True
        await notifier.cleanup()

    async def test_notify_button_clicked_failure(self, mock_settings, mock_telegram_client):
        """Test failed button click notification."""
        notifier = TelegramNotifier()
        await notifier.initialize()
        mock_telegram_client.send_message.reset_mock()  # Reset after init
        
        # Make send_message raise an exception
        mock_telegram_client.send_message.side_effect = Exception("Network error")
        
        # Test notification
        result = await notifier.notify_button_clicked(1, "BOOK NOW")
        
        # Verify result
        assert result is False
        await notifier.cleanup()

    async def test_cleanup_on_init_failure(self, mock_settings, mock_telegram_client):
        """Test cleanup when initialization fails."""
        # Make client.start raise an exception
        mock_telegram_client.start.side_effect = Exception("Connection failed")
        mock_telegram_client.disconnect.reset_mock()  # Reset before test
        
        notifier = TelegramNotifier()
        with pytest.raises(Exception, match="Connection failed"):
            await notifier.initialize()
        
        # Verify cleanup was called exactly once
        mock_telegram_client.disconnect.assert_awaited_once()

    async def test_cleanup(self, mock_settings, mock_telegram_client):
        """Test cleanup method."""
        notifier = TelegramNotifier()
        await notifier.initialize()
        mock_telegram_client.disconnect.reset_mock()  # Reset after init
        
        # Call cleanup
        await notifier.cleanup()
        
        # Verify cleanup was called
        mock_telegram_client.disconnect.assert_awaited_once()
        assert not notifier.initialized

    async def test_cleanup_on_deletion(self, mock_settings, mock_telegram_client):
        """Test cleanup when object is deleted."""
        notifier = TelegramNotifier()
        await notifier.initialize()
        mock_telegram_client.disconnect.reset_mock()  # Reset after init
        
        # Trigger cleanup
        await notifier.cleanup()
        
        # Verify cleanup was called
        mock_telegram_client.disconnect.assert_awaited_once()
        assert not notifier.initialized

    async def test_cleanup_with_closed_loop(self, mock_settings, mock_telegram_client):
        """Test cleanup when event loop is already closed."""
        notifier = TelegramNotifier()
        await notifier.initialize()
        mock_telegram_client.disconnect.reset_mock()  # Reset after init
        
        # Call cleanup
        await notifier.cleanup()
        
        # Verify cleanup was called
        mock_telegram_client.disconnect.assert_awaited_once()
        assert not notifier.initialized

    @patch('logging.error')
    async def test_error_logging(self, mock_logging, mock_settings, mock_telegram_client):
        """Test error logging."""
        notifier = TelegramNotifier()
        await notifier.initialize()
        mock_telegram_client.send_message.reset_mock()  # Reset after init
        
        # Make send_message raise an exception
        mock_telegram_client.send_message.side_effect = Exception("Test error")
        
        # Test notification
        await notifier.notify_button_clicked(1, "BOOK NOW")
        
        # Verify error was logged
        mock_logging.assert_called_with("Failed to send notification: Test error")
        await notifier.cleanup() 
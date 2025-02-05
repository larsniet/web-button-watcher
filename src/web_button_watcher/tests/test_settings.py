"""Tests for the Settings module."""

import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock, AsyncMock
import asyncio
from ..utils.settings import Settings

@pytest.fixture(autouse=True)
def mock_telegram_notifier():
    """Mock the TelegramNotifier to prevent any async operations."""
    mock_loop = MagicMock()
    mock_loop.is_closed.return_value = False
    mock_loop.run_until_complete = MagicMock()
    
    with patch('asyncio.new_event_loop', return_value=mock_loop), \
         patch('asyncio.get_event_loop', return_value=mock_loop), \
         patch('asyncio.set_event_loop'), \
         patch('web_button_watcher.utils.notifier.TelegramClient') as mock_client:
        
        # Create a mock client instance
        client_instance = MagicMock()
        client_instance.start = AsyncMock()
        client_instance.send_message = AsyncMock()
        client_instance.disconnect = AsyncMock()
        mock_client.return_value = client_instance
        
        # Mock the TelegramNotifier class
        with patch('web_button_watcher.utils.notifier.TelegramNotifier') as mock_notifier:
            instance = MagicMock()
            instance.loop = mock_loop
            instance.cleanup = AsyncMock()
            instance._init_client = AsyncMock()
            mock_notifier.return_value = instance
            
            yield mock_notifier

@pytest.fixture
def settings():
    """Create a Settings instance with a temporary directory."""
    with patch('pathlib.Path.mkdir'), \
         patch('pathlib.Path.exists', return_value=False), \
         patch('builtins.open', mock_open()):
        settings = Settings()
        yield settings

class TestSettings:
    """Test suite for Settings class."""

    def test_init_default_settings(self, settings):
        """Test initialization with default settings."""
        assert settings.settings['refresh_interval'] == 1
        assert settings.settings['url'] == ''
        assert settings.settings['selected_buttons'] == []
        assert 'telegram' in settings.settings
        assert 'window' in settings.settings

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_load_existing_settings(self, mock_json_load, mock_file, settings):
        """Test loading existing settings."""
        test_settings = {
            'refresh_interval': 2,
            'url': 'https://test.com',
            'selected_buttons': [1, 2],
            'telegram': {
                'api_id': '12345',  # Changed to valid integer string
                'api_hash': 'test_hash',
                'bot_token': 'test_token',
                'chat_id': '67890'  # Changed to valid integer string
            }
        }
        mock_json_load.return_value = test_settings
        
        with patch('pathlib.Path.exists', return_value=True):
            loaded_settings = settings.load()
        
        assert loaded_settings['refresh_interval'] == 2
        assert loaded_settings['url'] == 'https://test.com'
        assert loaded_settings['selected_buttons'] == [1, 2]
        assert loaded_settings['telegram']['api_id'] == '12345'

    def test_get_set_settings(self, settings):
        """Test getting and setting individual settings."""
        settings.set('test_key', 'test_value')
        assert settings.get('test_key') == 'test_value'
        assert settings.get('nonexistent', 'default') == 'default'

    def test_update_settings(self, settings):
        """Test updating multiple settings."""
        update_dict = {
            'refresh_interval': 5,
            'url': 'https://example.com'
        }
        settings.update(update_dict)
        
        assert settings.get('refresh_interval') == 5
        assert settings.get('url') == 'https://example.com'

    def test_telegram_settings(self, settings):
        """Test Telegram-specific settings."""
        test_telegram = {
            'api_id': '12345',  # Changed to valid integer string
            'api_hash': 'test_hash',
            'bot_token': 'test_token',
            'chat_id': '67890'  # Changed to valid integer string
        }
        
        # Test updating Telegram settings
        settings.update_telegram_settings(
            test_telegram['api_id'],
            test_telegram['api_hash'],
            test_telegram['bot_token'],
            test_telegram['chat_id']
        )
        
        # Test getting Telegram settings
        saved_settings = settings.get_telegram_settings()
        assert saved_settings == test_telegram

    def test_window_position(self, settings):
        """Test saving window position and size."""
        settings.save_window_position(100, 200, 800, 600)
        window_settings = settings.settings['window']
        
        assert window_settings['position_x'] == 100
        assert window_settings['position_y'] == 200
        assert window_settings['width'] == 800
        assert window_settings['height'] == 600

    @patch('json.dump')
    def test_save_settings(self, mock_json_dump, settings):
        """Test saving settings to file."""
        test_settings = {'test_key': 'test_value'}
        settings.settings = test_settings
        
        with patch('builtins.open', mock_open()) as mock_file:
            settings.save()
            
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once_with(test_settings, mock_file(), indent=2) 
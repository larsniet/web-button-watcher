"""Tests for the Settings module."""

import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock, AsyncMock
import asyncio
from ..utils.settings import SettingsManager

@pytest.fixture(autouse=True)
def mock_telegram_notifier():
    """Mock the TelegramNotifier to prevent any async operations."""
    mock_loop = MagicMock()
    mock_loop.is_closed.return_value = False
    mock_loop.run_until_complete = MagicMock()
    
    with patch('asyncio.new_event_loop', return_value=mock_loop), \
         patch('asyncio.get_event_loop', return_value=mock_loop), \
         patch('asyncio.set_event_loop'), \
         patch('webbuttonwatcher.utils.notifier.TelegramNotifier'):
        yield

@pytest.fixture
def settings():
    """Create a test settings instance with a temporary file."""
    temp_file = Path("test_settings.json")
    settings = SettingsManager(temp_file)
    yield settings
    # Clean up
    if temp_file.exists():
        temp_file.unlink()

class TestSettings:
    """Test cases for the SettingsManager class."""
    
    def test_init_default_settings(self, settings):
        """Test that default settings are initialized correctly."""
        assert hasattr(settings, 'settings_file')
        assert isinstance(settings._load_settings(), dict)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_load_existing_settings(self, mock_json_load, mock_file, settings):
        """Test loading settings from an existing file."""
        # Setup the mock to return some settings
        mock_settings = {
            'telegram': {
                'api_id': '12345',
                'api_hash': 'abcdef',
                'bot_token': '123:abc',
                'chat_id': '123456'
            },
            'window': {
                'x': 100,
                'y': 200,
                'width': 800,
                'height': 600
            }
        }
        mock_json_load.return_value = mock_settings
        
        # Call the function
        result = settings._load_settings()
        
        # Verify
        mock_file.assert_called_once_with(settings.settings_file, 'r')
        mock_json_load.assert_called_once_with(mock_file())
        assert result == mock_settings
    
    def test_get_set_settings(self, settings):
        """Test getting and setting individual settings."""
        settings.set('test_key', 'test_value')
        assert settings.get('test_key') == 'test_value'
        assert settings.get('nonexistent_key') is None
        assert settings.get('nonexistent_key', 'default') == 'default'
    
    def test_update_settings(self, settings):
        """Test updating multiple settings at once."""
        test_settings = {
            'key1': 'value1',
            'key2': 'value2',
            'nested': {
                'subkey': 'subvalue'
            }
        }
        settings.update(test_settings)
        assert settings.get('key1') == 'value1'
        assert settings.get('key2') == 'value2'
        assert settings.get('nested', {}).get('subkey') == 'subvalue'
        
        # Test that it updates existing settings
        settings.update({'key1': 'new_value'})
        assert settings.get('key1') == 'new_value'
    
    def test_telegram_settings(self, settings):
        """Test telegram settings getters and setters."""
        # Test default values
        telegram_settings = settings.get_telegram_settings()
        assert telegram_settings.get('api_id') == ''
        assert telegram_settings.get('api_hash') == ''
        assert telegram_settings.get('bot_token') == ''
        assert telegram_settings.get('chat_id') == ''
        
        # Test updating values
        settings.update_telegram_settings('12345', 'abcdef', '123:abc', '123456')
        telegram_settings = settings.get_telegram_settings()
        assert telegram_settings.get('api_id') == '12345'
        assert telegram_settings.get('api_hash') == 'abcdef'
        assert telegram_settings.get('bot_token') == '123:abc'
        assert telegram_settings.get('chat_id') == '123456'
    
    def test_window_position(self, settings):
        """Test window position settings."""
        # Test default values
        window_settings = settings.get_window_settings()
        assert window_settings.get('x') is None
        assert window_settings.get('y') is None
        assert window_settings.get('width') is None
        assert window_settings.get('height') is None
        
        # Test updating values
        settings.save_window_position(100, 200, 800, 600)
        window_settings = settings.get_window_settings()
        assert window_settings.get('x') == 100
        assert window_settings.get('y') == 200
        assert window_settings.get('width') == 800
        assert window_settings.get('height') == 600
    
    @patch('json.dump')
    def test_save_settings(self, mock_json_dump, settings):
        """Test saving settings to a file."""
        # Setup test data
        settings.set('test_key', 'test_value')
        
        # Mock the open context manager
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            result = settings._save_settings()
        
        # Verify
        mock_file.assert_called_once_with(settings.settings_file, 'w')
        mock_json_dump.assert_called_once()
        assert result is True 
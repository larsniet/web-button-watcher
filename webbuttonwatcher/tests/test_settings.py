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
    # Create a clean settings instance for each test
    with patch.object(SettingsManager, '_load_settings') as mock_load:
        mock_load.return_value = {
            'url': '',
            'refresh_interval': 5.0,
            'selected_buttons': [],
            'telegram': {
                'api_id': '',
                'api_hash': '',
                'bot_token': '',
                'chat_id': ''
            },
            'window': {
                'position_x': None,
                'position_y': None,
                'width': 600,
                'height': 900
            }
        }
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
    
    def test_load_settings_file_exists(self):
        """Test loading settings from an existing file (standalone test)."""
        # Create a test instance with mocked path existence check
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            # Create a mock for open and json.load
            test_settings = {
                'url': 'https://example.com',
                'refresh_interval': 10.0,
                'selected_buttons': [1, 2],
                'telegram': {
                    'api_id': '12345',
                    'api_hash': 'abcdef',
                    'bot_token': '123:abc',
                    'chat_id': '123456'
                }
            }
            
            # Setup the mocks for file operations
            mock_file = mock_open(read_data=json.dumps(test_settings))
            
            # Create the settings manager and test loading
            with patch('builtins.open', mock_file):
                with patch('json.load', return_value=test_settings) as mock_json_load:
                    settings_manager = SettingsManager("test_path.json")
                    
                    # Verify file was opened and parsed
                    mock_file.assert_called_once_with("test_path.json", 'r')
                    mock_json_load.assert_called_once()
                    
                    # Verify the settings were loaded correctly
                    assert settings_manager.settings == test_settings
                    assert settings_manager.get('url') == 'https://example.com'
                    assert settings_manager.get('refresh_interval') == 10.0
    
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
        assert window_settings.get('position_x') is None
        assert window_settings.get('position_y') is None
        assert window_settings.get('width') == 600
        assert window_settings.get('height') == 900
        
        # Test updating values
        settings.save_window_position(100, 200, 800, 600)
        window_settings = settings.get_window_settings()
        assert window_settings.get('position_x') == 100
        assert window_settings.get('position_y') == 200
        assert window_settings.get('width') == 800
        assert window_settings.get('height') == 600
    
    def test_save_settings_standalone(self):
        """Test saving settings to a file (standalone test)."""
        # Create settings with test data
        test_settings = {
            'url': 'https://example.com',
            'refresh_interval': 10.0,
            'selected_buttons': [1, 2],
            'telegram': {
                'api_id': '12345',
                'api_hash': 'abcdef',
                'bot_token': '123:abc',
                'chat_id': '123456'
            }
        }
        
        # Create a settings manager with the fixture pattern
        with patch.object(SettingsManager, '_load_settings') as mock_load:
            mock_load.return_value = test_settings
            settings_manager = SettingsManager("test_path.json")
            
            # Mock the file operations
            mock_file = mock_open()
            
            # Test saving
            with patch('builtins.open', mock_file) as mock_open_call:
                with patch('json.dump') as mock_json_dump:
                    result = settings_manager._save_settings()
                    
                    # Verify file operations
                    mock_open_call.assert_called_once_with("test_path.json", 'w')
                    mock_json_dump.assert_called_once()
                    assert result is True 
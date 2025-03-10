"""Tests for the GUI components."""

import pytest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
from tkinter import messagebox
import threading
from ..interface.gui import MonitorGUI

@pytest.fixture
def mock_string_var():
    """Create a mock StringVar."""
    mock_var = MagicMock()
    mock_var.get = MagicMock(return_value='')
    mock_var.set = MagicMock()
    return mock_var

@pytest.fixture
def root():
    """Create a mocked Tk root instance for headless environments."""
    with patch('tkinter.Tk') as mock_tk:
        root = mock_tk.return_value
        root.withdraw = MagicMock()
        root.destroy = MagicMock()
        root.geometry = MagicMock()
        root.title = MagicMock()
        root.protocol = MagicMock()
        root.columnconfigure = MagicMock()
        root.rowconfigure = MagicMock()
        yield root

@pytest.fixture
def mock_settings():
    """Create a mock Settings instance."""
    settings = MagicMock()
    settings.get_telegram_settings.return_value = {
        'api_id': '',
        'api_hash': '',
        'bot_token': '',
        'chat_id': ''
    }
    settings.get_window_settings.return_value = {
        'width': 800,
        'height': 600,
        'position_x': None,
        'position_y': None
    }
    settings.get.side_effect = lambda key, default=None: default
    return settings

@pytest.fixture
def gui(root, mock_settings):
    """Create a MonitorGUI instance."""
    with patch('webbuttonwatcher.interface.cli.MonitorController') as mock_controller, \
         patch('webbuttonwatcher.interface.gui.Settings', return_value=mock_settings), \
         patch('tkinter.ttk.Frame') as mock_frame, \
         patch('tkinter.ttk.LabelFrame') as mock_label_frame, \
         patch('tkinter.ttk.Entry') as mock_entry, \
         patch('tkinter.ttk.Label') as mock_label, \
         patch('tkinter.ttk.Button') as mock_button, \
         patch('tkinter.Text') as mock_text, \
         patch('tkinter.ttk.Scrollbar') as mock_scrollbar, \
         patch('tkinter.StringVar') as mock_string_var:
        
        # Setup mock widgets
        mock_frame.return_value.grid = MagicMock()
        mock_frame.return_value.columnconfigure = MagicMock()
        mock_frame.return_value.rowconfigure = MagicMock()
        
        mock_label_frame.return_value.grid = MagicMock()
        mock_label_frame.return_value.columnconfigure = MagicMock()
        mock_label_frame.return_value.rowconfigure = MagicMock()
        
        mock_entry.return_value.grid = MagicMock()
        mock_label.return_value.grid = MagicMock()
        mock_button.return_value.grid = MagicMock()
        mock_text.return_value.grid = MagicMock()
        mock_text.return_value.see = MagicMock()
        mock_text.return_value.insert = MagicMock()
        mock_scrollbar.return_value.grid = MagicMock()
        
        # Setup StringVar mocks
        def create_string_var(*args, **kwargs):
            var = MagicMock()
            initial_value = kwargs.get('value', '')
            var.get = MagicMock(return_value=initial_value)
            var.set = MagicMock()
            return var
        mock_string_var.side_effect = create_string_var
        
        controller = MagicMock()
        mock_controller.return_value = controller
        gui = MonitorGUI(root)
        gui.controller = controller
        
        # Mock the buttons directly since they're used in tests
        start_btn = MagicMock()
        start_btn.config = MagicMock()
        start_btn.configure = start_btn.config
        gui.start_btn = start_btn
        
        stop_btn = MagicMock()
        stop_btn.config = MagicMock()
        stop_btn.configure = stop_btn.config
        gui.stop_btn = stop_btn
        
        # Mock the status text widget
        gui.status_text = mock_text()
        gui.status_text.get = MagicMock(return_value="Test status message\n")
        gui.status_text.insert = MagicMock()
        gui.status_text.see = MagicMock()
        
        # Create separate StringVar instances for each variable
        gui.api_id_var = create_string_var()
        gui.api_hash_var = create_string_var()
        gui.bot_token_var = create_string_var()
        gui.chat_id_var = create_string_var()
        gui.url_var = create_string_var()
        gui.refresh_interval_var = create_string_var()
        gui.buttons_var = create_string_var()
        
        # Set default values
        gui.refresh_interval_var.get.return_value = '1'
        gui.buttons_var.get.return_value = 'None'
        
        yield gui

class TestMonitorGUI:
    """Test suite for MonitorGUI class."""

    @patch('tkinter.messagebox.showerror')
    def test_init(self, mock_error, gui):
        """Test GUI initialization."""
        assert gui.root is not None
        assert gui.api_id_var.get() == ''
        assert gui.api_hash_var.get() == ''
        assert gui.bot_token_var.get() == ''
        assert gui.chat_id_var.get() == ''
        assert gui.url_var.get() == ''
        assert gui.refresh_interval_var.get() == '1'
        assert gui.buttons_var.get() == 'None'

    @patch('tkinter.messagebox.showerror')
    def test_save_settings(self, mock_error, gui):
        """Test saving settings."""
        # Setup test data
        gui.api_id_var.get.return_value = '12345'
        gui.api_hash_var.get.return_value = 'hash123'
        gui.bot_token_var.get.return_value = 'bot123'
        gui.chat_id_var.get.return_value = 'chat123'
        gui.url_var.get.return_value = 'https://example.com'
        gui.refresh_interval_var.get.return_value = '2'
        gui.buttons_var.get.return_value = '1, 2'

        # Save settings
        gui.save_settings()

        # Verify settings were saved
        gui.settings.update_telegram_settings.assert_called_once_with(
            '12345', 'hash123', 'bot123', 'chat123'
        )
        gui.settings.update.assert_called_once_with({
            'refresh_interval': 2.0,
            'url': 'https://example.com',
            'selected_buttons': [0, 1]  # 0-based indices
        })

    @patch('tkinter.messagebox.showerror')
    def test_select_buttons(self, mock_error, gui):
        """Test button selection."""
        # Setup test data
        gui.url_var.get.return_value = 'https://example.com'
        gui.controller.select_buttons.return_value = [0, 2]  # 0-based indices

        # Select buttons
        gui.select_buttons()

        # Verify controller was called correctly
        gui.controller.select_buttons.assert_called_once_with('https://example.com')

        # Verify display is updated with 1-based indices
        gui.buttons_var.set.assert_called_with('1, 3')
        gui.start_btn.config.assert_called_with(state=tk.NORMAL)

    @patch('tkinter.messagebox.showerror')
    @patch('webbuttonwatcher.interface.gui.threading.Thread')
    def test_start_monitor(self, mock_thread, mock_error, gui):
        """Test starting the monitor."""
        # Setup test data
        gui.api_id_var.get.return_value = '12345'
        gui.api_hash_var.get.return_value = 'hash123'
        gui.bot_token_var.get.return_value = 'bot123'
        gui.chat_id_var.get.return_value = 'chat123'
        gui.url_var.get.return_value = 'https://example.com'
        gui.refresh_interval_var.get.return_value = '2'
        gui.buttons_var.get.return_value = '1, 2'

        # Mock settings.get to return different values based on the key
        def settings_get_side_effect(key, default=None):
            if key == 'selected_buttons':
                return [0, 1]
            return default
        gui.settings.get.side_effect = settings_get_side_effect

        # Create thread instance
        thread_instance = MagicMock()
        mock_thread.return_value = thread_instance

        # Start monitoring
        gui.start_monitor()

        # Verify thread was created correctly
        mock_thread.assert_called_once()
        args, kwargs = mock_thread.call_args
        assert kwargs['target'] == gui.controller.start_monitoring
        assert kwargs['args'] == (
            'https://example.com',
            2.0,
            [0, 1],
            gui.update_status
        )

        # Verify daemon was set after creation
        assert thread_instance.daemon is True

        # Verify thread was started
        thread_instance.start.assert_called_once()

        # Verify thread was stored
        assert gui.monitor_thread == thread_instance

        # Verify UI state
        gui.start_btn.config.assert_called_once_with(state='disabled')
        gui.stop_btn.config.assert_called_once_with(state='normal')

    @patch('tkinter.messagebox.showerror')
    def test_start_monitor_missing_settings(self, mock_error, gui):
        """Test starting monitor with missing settings."""
        # Clear all settings
        gui.api_id_var.get.return_value = ''
        gui.api_hash_var.get.return_value = ''
        gui.bot_token_var.get.return_value = ''
        gui.chat_id_var.get.return_value = ''

        gui.start_monitor()
        
        # Verify error message was shown
        mock_error.assert_called_once_with("Error", "Please fill in all Telegram settings first!")
        
        # Verify button states were not changed
        gui.start_btn.config.assert_not_called()
        gui.stop_btn.config.assert_not_called()

    @patch('tkinter.messagebox.showerror')
    def test_stop_monitor(self, mock_error, gui):
        """Test stopping the monitor."""
        # Stop monitoring
        gui.stop_monitor()

        # Verify controller was called
        gui.controller.stop_monitoring.assert_called_once()

        # Verify UI state was updated
        gui.start_btn.config.assert_called_once_with(state='normal')
        gui.stop_btn.config.assert_called_once_with(state='disabled')

    def test_update_status(self, gui):
        """Test status updates."""
        test_message = "Test status message"
        gui.update_status(test_message)
        
        # Verify text widget was updated
        gui.status_text.insert.assert_called_with(tk.END, f"{test_message}\n")
        gui.status_text.see.assert_called_with(tk.END) 
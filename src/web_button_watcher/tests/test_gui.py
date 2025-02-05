"""Tests for the GUI components."""

import pytest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock, call
from tkinter import messagebox
import threading
from ..interface.gui import MonitorGUI

@pytest.fixture
def root():
    """Create a Tk root instance."""
    root = tk.Tk()
    root.withdraw()  # Hide the window
    yield root
    root.destroy()

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
    with patch('web_button_watcher.interface.cli.MonitorController') as mock_controller, \
         patch('web_button_watcher.interface.gui.Settings', return_value=mock_settings):
        controller = MagicMock()
        mock_controller.return_value = controller
        gui = MonitorGUI(root)
        gui.controller = controller
        # Ensure buttons are in known state
        gui.start_btn.configure(state='normal')
        gui.stop_btn.configure(state='disabled')
        yield gui

class TestMonitorGUI:
    """Test suite for MonitorGUI class."""

    @patch('tkinter.messagebox.showerror')
    def test_init(self, mock_error, gui):
        """Test GUI initialization."""
        assert isinstance(gui.root, tk.Tk)
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
        gui.api_id_var.set('12345')
        gui.api_hash_var.set('hash123')
        gui.bot_token_var.set('bot123')
        gui.chat_id_var.set('chat123')
        gui.url_var.set('https://example.com')
        gui.refresh_interval_var.set('2')
        gui.buttons_var.set('1, 2')

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
        gui.url_var.set('https://example.com')
        gui.controller.select_buttons.return_value = [0, 2]  # 0-based indices

        # Select buttons
        gui.select_buttons()

        # Verify controller was called correctly
        gui.controller.select_buttons.assert_called_once_with('https://example.com')

        # Verify display is updated with 1-based indices
        assert gui.buttons_var.get() == '1, 3'
        assert str(gui.start_btn['state']) == 'normal'

    @patch('tkinter.messagebox.showerror')
    @patch('web_button_watcher.interface.gui.threading.Thread')
    def test_start_monitor(self, mock_thread, mock_error, gui):
        """Test starting the monitor."""
        # Setup test data
        gui.api_id_var.set('12345')
        gui.api_hash_var.set('hash123')
        gui.bot_token_var.set('bot123')
        gui.chat_id_var.set('chat123')
        gui.url_var.set('https://example.com')
        gui.refresh_interval_var.set('2')
        gui.buttons_var.set('1, 2')

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
        assert mock_thread.call_count == 1, "Thread should be created exactly once"
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
        assert str(gui.start_btn['state']) == 'disabled'
        assert str(gui.stop_btn['state']) == 'normal'

    @patch('tkinter.messagebox.showerror')
    def test_start_monitor_missing_settings(self, mock_error, gui):
        """Test starting monitor with missing settings."""
        # Clear all settings
        gui.api_id_var.set('')
        gui.api_hash_var.set('')
        gui.bot_token_var.set('')
        gui.chat_id_var.set('')

        gui.start_monitor()
        mock_error.assert_called_once_with("Error", "Please fill in all Telegram settings first!")
        assert str(gui.start_btn['state']) == 'normal'
        assert str(gui.stop_btn['state']) == 'disabled'

    @patch('tkinter.messagebox.showerror')
    def test_stop_monitor(self, mock_error, gui):
        """Test stopping the monitor."""
        # Enable stop button and disable start button
        gui.stop_btn['state'] = 'normal'
        gui.start_btn['state'] = 'disabled'

        # Stop monitoring
        gui.stop_monitor()

        # Verify controller was called
        gui.controller.stop_monitoring.assert_called_once()

        # Verify UI state
        assert str(gui.start_btn['state']) == 'normal'
        assert str(gui.stop_btn['state']) == 'disabled'

    def test_update_status(self, gui):
        """Test status updates."""
        test_message = "Test status message"
        gui.update_status(test_message)
        
        # Get text from status widget
        status_text = gui.status_text.get("1.0", tk.END).strip()
        assert test_message in status_text 
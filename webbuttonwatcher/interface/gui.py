"""PyQt5 GUI for Web Button Watcher."""

import sys
import os
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QFrame, QTextEdit, QGroupBox,
    QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor, QPalette
import PyQt5
import socket

logger = logging.getLogger(__name__)

from webbuttonwatcher.interface.cli import MonitorController
from webbuttonwatcher.utils.settings import SettingsManager

def set_style():
    """Set application style with a dark theme."""
    style = """
    QMainWindow, QDialog {
        background-color: #2D2D30;
        color: #E0E0E0;
    }
    QWidget {
        color: #E0E0E0;
    }
    QGroupBox {
        font-weight: bold;
        border: 1px solid #3F3F46;
        border-radius: 6px;
        margin-top: 12px;
        padding-top: 10px;
        background-color: #252526;
        color: #E0E0E0;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
        color: #E0E0E0;
    }
    QPushButton {
        border: 1px solid #3F3F46;
        border-radius: 4px;
        background-color: #333337;
        color: #E0E0E0;
        min-width: 80px;
        padding: 5px;
    }
    QPushButton:hover {
        background-color: #3E3E42;
        border-color: #007ACC;
    }
    QPushButton:pressed {
        background-color: #2D2D30;
    }
    #start_btn {
        background-color: #0E639C;
        color: white;
        font-weight: bold;
        border-color: #007ACC;
    }
    #start_btn:hover {
        background-color: #1177BB;
    }
    QLineEdit, QComboBox {
        border: 1px solid #3F3F46;
        border-radius: 4px;
        padding: 4px;
        background-color: #1E1E1E;
        color: #E0E0E0;
    }
    QComboBox::drop-down {
        border: 0px;
    }
    QComboBox::down-arrow {
        width: 14px;
        height: 14px;
    }
    QComboBox QAbstractItemView {
        background-color: #1E1E1E;
        color: #E0E0E0;
        border: 1px solid #3F3F46;
    }
    QTextEdit {
        border: 1px solid #3F3F46;
        border-radius: 4px;
        background-color: #1E1E1E;
        color: #E0E0E0;
        font-family: monospace;
    }
    QLabel {
        color: #E0E0E0;
    }
    QCheckBox {
        color: #E0E0E0;
    }
    QCheckBox::indicator {
        width: 13px;
        height: 13px;
    }
    QStatusBar {
        background-color: #007ACC;
        color: white;
    }
    QProgressBar {
        border: 1px solid #3F3F46;
        border-radius: 4px;
        background-color: #1E1E1E;
        text-align: center;
        color: #E0E0E0;
    }
    QProgressBar::chunk {
        background-color: #0E639C;
        width: 10px;
    }
    """
    return style

class MonitorThread(QThread):
    """Thread for running the monitor without blocking the GUI."""
    status_signal = pyqtSignal(str)
    
    def __init__(self, controller, url, selected_buttons, refresh_interval):
        super().__init__()
        self.controller = controller
        self.url = url
        self.selected_buttons = selected_buttons
        self.refresh_interval = refresh_interval
        
        # Set thread as daemon to ensure it doesn't prevent app exit
        self.setTerminationEnabled(True)
        
        # Flag to track if thread has been stopped
        self.stopped = False
        
        # Check if we're on macOS and running as a packaged app
        self.is_mac_app = sys.platform == 'darwin' and getattr(sys, 'frozen', False)
    
    def run(self):
        """Run the monitor in a separate thread."""
        try:
            # Ensure we have a valid application instance
            app = QApplication.instance()
            if app is None:
                self.status_signal.emit("Error: Could not get application instance")
                return
            
            # Special handling for macOS packaged apps
            if self.is_mac_app:
                self.status_signal.emit("Using macOS-specific monitoring configuration...")
            
            # Use controller's status callback to keep UI updated
            self.controller.set_status_callback(lambda msg: self.status_signal.emit(msg))
            
            # Start monitoring
            self.controller.start_monitoring(self.url, self.refresh_interval, self.selected_buttons)
            
        except Exception as e:
            if not self.stopped:  # Only emit if not stopped intentionally
                self.status_signal.emit(f"Error in monitoring thread: {str(e)}")
    
    def stop(self):
        """Explicitly stop the monitoring thread."""
        self.stopped = True
        if self.controller:
            try:
                self.controller.stop_monitoring()
            except Exception as e:
                logger.error(f"Error stopping controller: {e}")
                # Proceed anyway

class QtMonitorGUI(QMainWindow):
    """PyQt5 GUI for Web Button Watcher."""
    
    def __init__(self):
        """Initialize the GUI."""
        super().__init__()
        
        self.settings_manager = SettingsManager()
        self.controller = None
        self.monitor_thread = None
        self.selected_buttons = []
        self.monitoring = False  # Initialize monitoring flag
        
        # Set window title and size
        self.setWindowTitle("Web Button Watcher")
        self.setMinimumSize(600, 500)
        
        # Set application icon
        try:
            # Get the path to the logo file
            # First check if we're running as a bundled app or from source
            bundle_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            resources_dir = os.path.join(bundle_dir, "resources")
            
            # Check different possible locations for the logo
            possible_logo_paths = [
                os.path.join(resources_dir, "logo.webp"),  # When running as bundled app
                os.path.join(resources_dir, "logo.png"),
                os.path.join(bundle_dir, "webbuttonwatcher", "resources", "logo.webp"),
                os.path.join(bundle_dir, "webbuttonwatcher", "resources", "logo.png"),
                os.path.join(bundle_dir, "..", "resources", "logo.webp"),
                os.path.join(bundle_dir, "..", "resources", "logo.png"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "resources", "logo.webp"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "resources", "logo.png"),
            ]
            
            icon_path = None
            for path in possible_logo_paths:
                if os.path.exists(path):
                    icon_path = path
                    break
            
            if icon_path:
                app_icon = QIcon()
                app_icon.addFile(icon_path)
                self.setWindowIcon(app_icon)
        except Exception as e:
            logger.error(f"Error setting application icon: {e}")
        
        # Initialize the UI
        self.init_ui()
        
        # Load saved settings
        self.load_settings()

        # Apply the dark theme style
        self.setStyleSheet(set_style())
        
        # Update status
        self.update_status("Ready to monitor. Configure settings and click 'Start Monitor'.")
        
        # Initialize controller
        self.controller = MonitorController()
        self.controller.set_status_callback(self.update_status)
    
    def init_ui(self):
        """Initialize the user interface."""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Telegram Configuration section
        telegram_group = QGroupBox("Telegram Configuration")
        telegram_layout = QGridLayout()
        telegram_group.setLayout(telegram_layout)
        
        # API ID
        telegram_layout.addWidget(QLabel("API ID:"), 0, 0)
        self.api_id_edit = QLineEdit()
        telegram_layout.addWidget(self.api_id_edit, 0, 1)
        
        # API Hash
        telegram_layout.addWidget(QLabel("API Hash:"), 1, 0)
        self.api_hash_edit = QLineEdit()
        telegram_layout.addWidget(self.api_hash_edit, 1, 1)
        
        # Bot Token
        telegram_layout.addWidget(QLabel("Bot Token:"), 2, 0)
        self.bot_token_edit = QLineEdit()
        telegram_layout.addWidget(self.bot_token_edit, 2, 1)
        
        # Chat ID
        telegram_layout.addWidget(QLabel("Chat ID:"), 3, 0)
        self.chat_id_edit = QLineEdit()
        telegram_layout.addWidget(self.chat_id_edit, 3, 1)
        
        # Help text
        help_text = """To get these values:
1. API ID & Hash: Visit https://my.telegram.org/apps
2. Bot Token: Message @BotFather on Telegram
3. Chat ID: Send a message to your bot and check:
   https://api.telegram.org/bot<YourBOTToken>/getUpdates"""
        help_label = QLabel(help_text)
        help_label.setWordWrap(True)
        telegram_layout.addWidget(help_label, 4, 0, 1, 2)
        
        main_layout.addWidget(telegram_group)
        
        # Monitor Settings section
        monitor_group = QGroupBox("Monitor Settings")
        monitor_layout = QGridLayout()
        monitor_group.setLayout(monitor_layout)
        
        # URL
        monitor_layout.addWidget(QLabel("URL:"), 0, 0)
        self.url_edit = QLineEdit()
        monitor_layout.addWidget(self.url_edit, 0, 1)
        
        # Refresh Interval
        monitor_layout.addWidget(QLabel("Refresh Interval (seconds):"), 1, 0)
        self.refresh_edit = QLineEdit()
        monitor_layout.addWidget(self.refresh_edit, 1, 1)
        
        # Selected Buttons
        monitor_layout.addWidget(QLabel("Selected Buttons:"), 2, 0)
        self.buttons_label = QLabel("None")
        monitor_layout.addWidget(self.buttons_label, 2, 1)
        
        # Select Buttons button
        self.select_btn = QPushButton("Select Buttons to Monitor")
        self.select_btn.clicked.connect(self.select_buttons)
        monitor_layout.addWidget(self.select_btn, 3, 0, 1, 2)
        
        main_layout.addWidget(monitor_group)
        
        # Control buttons
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)
        
        self.start_btn = QPushButton("Start Monitor")
        self.start_btn.setObjectName("start_btn")  # Set object name for CSS styling
        self.start_btn.clicked.connect(self.start_monitor)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Monitor")
        self.stop_btn.clicked.connect(self.stop_monitor)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        main_layout.addWidget(button_frame)
        
        # Status area
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        status_group.setLayout(status_layout)
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMinimumHeight(200)
        status_layout.addWidget(self.status_text)
        
        main_layout.addWidget(status_group)
        
        # Set the layout
        main_widget.setLayout(main_layout)
    
    def load_settings(self):
        """Load settings into UI."""
        # Get Telegram settings
        telegram_settings = self.settings_manager.get_telegram_settings()
        self.api_id_edit.setText(telegram_settings.get('api_id', ''))
        self.api_hash_edit.setText(telegram_settings.get('api_hash', ''))
        self.bot_token_edit.setText(telegram_settings.get('bot_token', ''))
        self.chat_id_edit.setText(telegram_settings.get('chat_id', ''))
        
        # Get other settings
        self.url_edit.setText(self.settings_manager.get('url', ''))
        
        # Get selected buttons
        selected_buttons = self.settings_manager.get('selected_buttons', [])
        
        # Add type checking to handle incorrect type in settings
        if not isinstance(selected_buttons, list):
            logger.warning(f"selected_buttons has wrong type: {type(selected_buttons)}. Resetting to empty list.")
            selected_buttons = []
            # Fix settings file by updating with correct type
            self.settings_manager.set('selected_buttons', selected_buttons)
            
        if selected_buttons:
            # Convert 0-based indices to 1-based for display
            button_numbers = [i + 1 for i in selected_buttons]
            self.buttons_label.setText(', '.join(map(str, button_numbers)))
        else:
            self.buttons_label.setText('None')
            
        # Get refresh interval with type checking
        refresh_interval = self.settings_manager.get('refresh_interval', 5.0)
        if not isinstance(refresh_interval, (int, float)):
            logger.warning(f"refresh_interval has wrong type: {type(refresh_interval)}. Resetting to default 5.0.")
            refresh_interval = 5.0
            # Fix settings file by updating with correct type
            self.settings_manager.set('refresh_interval', refresh_interval)
        
        self.refresh_edit.setText(str(refresh_interval))
    
    def save_settings(self):
        """Save settings."""
        try:
            # Update Telegram settings
            self.settings_manager.update_telegram_settings(
                self.api_id_edit.text(),
                self.api_hash_edit.text(),
                self.bot_token_edit.text(),
                self.chat_id_edit.text()
            )
            
            # Convert displayed 1-based indices to 0-based for storage
            selected_buttons = []
            if self.buttons_label.text() != 'None':
                selected_buttons = [int(x.strip()) - 1 for x in self.buttons_label.text().split(',')]
            
            # Update other settings
            self.settings_manager.update({
                'refresh_interval': float(self.refresh_edit.text()),
                'url': self.url_edit.text(),
                'selected_buttons': selected_buttons
            })
            
            self.update_status("Settings saved successfully!")
        except Exception as e:
            self.update_status(f"Error saving settings: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
    
    def select_buttons(self):
        """Select buttons to monitor."""
        try:
            url = self.url_edit.text()
            if not url:
                QMessageBox.critical(self, "Error", "Please enter a URL first.")
                return
            
            # Initialize controller if needed
            if not self.controller:
                self.controller = MonitorController()
                self.controller.set_status_callback(self.update_status)
            
            # Save current settings before selecting buttons
            self.save_settings()
            
            # Select buttons
            selected = self.controller.select_buttons(url)
            
            if selected:
                # Convert 0-based indices to 1-based for display
                button_numbers = [i + 1 for i in selected]
                self.buttons_label.setText(', '.join(map(str, button_numbers)))
                self.start_btn.setEnabled(True)
                self.update_status(f"Selected buttons: {', '.join(map(str, button_numbers))}")
            else:
                self.buttons_label.setText('None')
                self.start_btn.setEnabled(False)
                self.update_status("No buttons selected.")
                
        except Exception as e:
            logger.error(f"Error selecting buttons: {e}")
            self.update_status(f"Error selecting buttons: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to select buttons: {str(e)}")
    
    def start_monitor(self):
        """Start monitoring the selected buttons."""
        try:
            if self.monitoring:
                return
            
            # Initialize controller if needed
            if not self.controller:
                self.controller = MonitorController()
                self.controller.set_status_callback(self.update_status)
            
            # Get settings
            url = self.url_edit.text()
            try:
                refresh_interval = float(self.refresh_edit.text())
            except ValueError:
                QMessageBox.critical(self, "Error", "Invalid refresh interval. Please enter a number.")
                return
            
            # Convert displayed 1-based indices to 0-based for monitoring
            selected_buttons = []
            if self.buttons_label.text() != 'None':
                selected_buttons = [int(x.strip()) - 1 for x in self.buttons_label.text().split(',')]
            
            if not selected_buttons:
                QMessageBox.critical(self, "Error", "No buttons selected to monitor.")
                return
            
            # Check if we're on macOS and running as a packaged app
            is_mac_app = sys.platform == 'darwin' and getattr(sys, 'frozen', False)
            
            if is_mac_app:
                # On macOS packaged app, use a different approach
                # Set up a QTimer to process events during monitoring
                
                self.update_status("Starting monitoring with macOS-specific configuration...")
                
                # Update UI immediately
                self.monitoring = True
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.select_btn.setEnabled(False)
                
                # Process events to ensure UI updates 
                QApplication.processEvents()
                
                # Create and start the monitor thread
                self.monitor_thread = MonitorThread(self.controller, url, selected_buttons, refresh_interval)
                self.monitor_thread.status_signal.connect(self.update_status)
                self.monitor_thread.finished.connect(self.on_monitor_thread_finished)
                
                # Start the thread
                self.monitor_thread.start()
                
                self.update_status("Monitoring started.")
            else:
                # Normal thread-based approach for other platforms
                # Create and start the monitor thread
                self.monitor_thread = MonitorThread(self.controller, url, selected_buttons, refresh_interval)
                self.monitor_thread.status_signal.connect(self.update_status)
                self.monitor_thread.finished.connect(self.on_monitor_thread_finished)
                self.monitor_thread.start()
                
                # Update UI
                self.monitoring = True
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.select_btn.setEnabled(False)
                
                self.update_status("Monitoring started.")
            
        except Exception as e:
            logger.error(f"Error starting monitor: {e}")
            self.update_status(f"Error starting monitor: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to start monitoring: {str(e)}")
    
    def stop_monitor(self):
        """Stop monitoring."""
        if not self.monitoring:
            return
        
        try:
            # First signal the thread to stop cleanly
            if self.monitor_thread and self.monitor_thread.isRunning():
                self.update_status("Stopping monitoring...")
                self.monitor_thread.stop()  # Use our custom stop method
                
                # Wait for the thread to finish with a timeout
                if not self.monitor_thread.wait(3000):  # 3 seconds timeout
                    logger.warning("Monitor thread did not stop in time, forcing termination")
                    self.monitor_thread.terminate()
                    self.monitor_thread.wait()
            
            # Clean up controller separately (belt and suspenders)
            if self.controller:
                logger.debug("Cleaning up controller")
                self.controller.cleanup()
                self.controller = None  # Force recreation next time
            
            # Update UI
            self.monitoring = False
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.select_btn.setEnabled(True)
            
            self.update_status("Monitoring stopped.")
        except Exception as e:
            logger.error(f"Error stopping monitor: {e}")
            self.update_status(f"Error stopping monitor: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to stop monitoring: {str(e)}")
    
    def on_monitor_thread_finished(self):
        """Handle monitor thread completion."""
        self.monitoring = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.select_btn.setEnabled(True)
        
        # Ensure the controller's resources are properly cleaned up
        if self.controller:
            try:
                # Clean up driver resources to make sure Chrome processes are terminated
                self.controller.cleanup()
                self.controller = None  # Force recreation of controller on next start
            except Exception as e:
                logger.error(f"Error cleaning up controller: {e}")
        
        self.update_status("Monitoring finished.")
    
    def update_status(self, message):
        """Update the status text."""
        self.status_text.append(message)
        # Scroll to the bottom
        self.status_text.verticalScrollBar().setValue(self.status_text.verticalScrollBar().maximum())
    
    def closeEvent(self, event):
        """Handle window close event."""
        try:
            if self.monitoring:
                # Stop monitoring before closing
                self.stop_monitor()
            
            # Make sure controller is cleaned up
            if self.controller:
                self.controller.cleanup()
                self.controller = None
            
            # For extra safety, try to find and kill any remaining Chrome processes
            import platform
            import subprocess
            import os
            
            if platform.system() == "Darwin":  # macOS
                try:
                    # Find and kill any remaining Chrome processes that might be related to automation
                    ps_cmd = "ps -ax | grep Chrome | grep -v grep"
                    process = subprocess.Popen(ps_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, _ = process.communicate()
                    
                    for line in stdout.decode().split('\n'):
                        if "Chrome" in line and "--remote-debugging-port" in line:
                            # Extract PID and kill the process
                            try:
                                pid = int(line.strip().split()[0])
                                os.kill(pid, 9)  # SIGKILL
                                logger.info(f"Killed Chrome process with PID {pid}")
                            except (ValueError, IndexError, ProcessLookupError) as e:
                                logger.debug(f"Failed to kill Chrome process: {e}")
                except Exception as e:
                    logger.debug(f"Error cleaning up Chrome processes during application close: {e}")
            
            # Remove socket file to allow future instances to run
            socket_path = os.path.expanduser('~/.webbuttonwatcher.sock')
            if os.path.exists(socket_path):
                try:
                    os.unlink(socket_path)
                    logger.debug(f"Removed socket file: {socket_path}")
                except OSError as e:
                    logger.debug(f"Error removing socket file: {e}")
                    
        except Exception as e:
            logger.error(f"Error during application close: {e}")
            
        # Accept the close event
        event.accept()

def main():
    """Main entry point for the Qt GUI."""
    import sys
    import socket
    import os
    from PyQt5.QtWidgets import QApplication, QMessageBox
    
    # Single instance check - try to create a server socket on a specific port
    # If it fails, another instance is already running
    socket_path = os.path.expanduser('~/.webbuttonwatcher.sock')
    if sys.platform == "darwin" or sys.platform.startswith("linux"):
        # Unix socket for macOS and Linux
        try:
            # If the socket file exists but no process is using it, remove it
            if os.path.exists(socket_path):
                try:
                    os.unlink(socket_path)
                except OSError:
                    # The socket file exists and is in use
                    # Show message to user and exit
                    app = QApplication(sys.argv)
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Web Button Watcher is already running")
                    msg.setInformativeText("Another instance of Web Button Watcher is already running. Please use that instance or close it before starting a new one.")
                    msg.setWindowTitle("Already Running")
                    msg.exec_()
                    return 1
                    
            # Create UNIX socket server
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(socket_path)
            # Keep the socket server running to prevent other instances
            server.listen(1)
        except (socket.error, OSError) as e:
            # Failed to bind, another instance is running
            app = QApplication(sys.argv)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Web Button Watcher is already running")
            msg.setInformativeText("Another instance of Web Button Watcher is already running. Please use that instance or close it before starting a new one.")
            msg.setWindowTitle("Already Running")
            msg.exec_()
            return 1
    elif sys.platform == "win32":
        # TCP socket for Windows
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(('localhost', 47758))  # Use a less common port
            server.listen(1)
        except socket.error:
            app = QApplication(sys.argv)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Web Button Watcher is already running")
            msg.setInformativeText("Another instance of Web Button Watcher is already running. Please use that instance or close it before starting a new one.")
            msg.setWindowTitle("Already Running")
            msg.exec_()
            return 1
    
    # If we got here, we are the first instance
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    gui = QtMonitorGUI()
    gui.show()
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main()) 
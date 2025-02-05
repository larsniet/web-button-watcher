"""Graphical user interface for Web Button Watcher."""

import tkinter as tk
from tkinter import ttk, messagebox
import threading

from .cli import MonitorController
from ..utils.settings import Settings

class MonitorGUI:
    def __init__(self, root):
        self.root = root
        self.settings = Settings()
        
        # Initialize window
        self.root.title("Web Button Watcher")
        window_settings = self.settings.get_window_settings()
        geometry = f"{window_settings['width']}x{window_settings['height']}"
        if window_settings['position_x'] is not None and window_settings['position_y'] is not None:
            geometry += f"+{window_settings['position_x']}+{window_settings['position_y']}"
        self.root.geometry(geometry)
        
        # Save window position on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initialize controller
        self.controller = MonitorController()
        
        # Create main container with padding
        main_container = ttk.Frame(root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create sections
        self.create_telegram_section(main_container)
        self.create_monitor_section(main_container)
        self.create_buttons_section(main_container)
        self.create_status_section(main_container)
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        
        # Load saved settings
        self.load_saved_settings()
    
    def on_closing(self):
        """Save window position and size before closing."""
        # Get window geometry
        geometry = self.root.geometry()
        parts = geometry.replace('+', 'x').split('x')
        if len(parts) == 4:
            width, height, x, y = map(int, parts)
            self.settings.save_window_position(x, y, width, height)
        
        self.root.destroy()
    
    def load_saved_settings(self):
        """Load saved settings into UI."""
        # Load Telegram settings
        telegram_settings = self.settings.get_telegram_settings()
        self.api_id_var.set(telegram_settings.get('api_id', ''))
        self.api_hash_var.set(telegram_settings.get('api_hash', ''))
        self.bot_token_var.set(telegram_settings.get('bot_token', ''))
        self.chat_id_var.set(telegram_settings.get('chat_id', ''))
        
        # Load monitor settings
        self.url_var.set(self.settings.get('url', ''))
        self.refresh_interval_var.set(str(self.settings.get('refresh_interval', 1)))
        
        # Convert 0-based indices to 1-based for display
        selected_buttons = self.settings.get('selected_buttons', [])
        if selected_buttons:
            button_numbers = [i + 1 for i in selected_buttons]
            self.buttons_var.set(', '.join(map(str, button_numbers)))
        else:
            self.buttons_var.set('None')
        
        # Update button states
        if selected_buttons:
            self.start_btn.config(state=tk.NORMAL)
        else:
            self.start_btn.config(state=tk.DISABLED)
    
    def create_telegram_section(self, parent):
        # Telegram Configuration Frame
        telegram_frame = ttk.LabelFrame(parent, text="Telegram Configuration", padding="5")
        telegram_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Get saved Telegram settings
        telegram_settings = self.settings.get_telegram_settings()
        
        # API ID
        ttk.Label(telegram_frame, text="API ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.api_id_var = tk.StringVar(value=telegram_settings.get('api_id', ''))
        self.api_id_entry = ttk.Entry(telegram_frame, textvariable=self.api_id_var)
        self.api_id_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # API Hash
        ttk.Label(telegram_frame, text="API Hash:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.api_hash_var = tk.StringVar(value=telegram_settings.get('api_hash', ''))
        self.api_hash_entry = ttk.Entry(telegram_frame, textvariable=self.api_hash_var)
        self.api_hash_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Bot Token
        ttk.Label(telegram_frame, text="Bot Token:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.bot_token_var = tk.StringVar(value=telegram_settings.get('bot_token', ''))
        self.bot_token_entry = ttk.Entry(telegram_frame, textvariable=self.bot_token_var)
        self.bot_token_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Chat ID
        ttk.Label(telegram_frame, text="Chat ID:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.chat_id_var = tk.StringVar(value=telegram_settings.get('chat_id', ''))
        self.chat_id_entry = ttk.Entry(telegram_frame, textvariable=self.chat_id_var)
        self.chat_id_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Help text
        help_text = """
        To get these values:
        1. API ID & Hash: Visit https://my.telegram.org/apps
        2. Bot Token: Message @BotFather on Telegram
        3. Chat ID: Send a message to your bot and check:
           https://api.telegram.org/bot<YourBOTToken>/getUpdates
        """
        help_label = ttk.Label(telegram_frame, text=help_text, wraplength=500, justify=tk.LEFT)
        help_label.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        telegram_frame.columnconfigure(1, weight=1)
    
    def create_monitor_section(self, parent):
        # Monitor Settings Frame
        monitor_frame = ttk.LabelFrame(parent, text="Monitor Settings", padding="5")
        monitor_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # URL Input
        ttk.Label(monitor_frame, text="URL:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.url_var = tk.StringVar(value=self.settings.get('url', ''))
        url_entry = ttk.Entry(monitor_frame, textvariable=self.url_var)
        url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Refresh Interval
        ttk.Label(monitor_frame, text="Refresh Interval (seconds):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.refresh_interval_var = tk.StringVar(value=str(self.settings.get('refresh_interval', 1)))
        refresh_entry = ttk.Entry(monitor_frame, textvariable=self.refresh_interval_var, width=10)
        refresh_entry.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Selected Buttons Display
        ttk.Label(monitor_frame, text="Selected Buttons:").grid(row=2, column=0, sticky=tk.W, pady=2)
        selected_buttons = self.settings.get('selected_buttons', [])
        self.buttons_var = tk.StringVar(value=', '.join(map(str, selected_buttons)) if selected_buttons else 'None')
        buttons_label = ttk.Label(monitor_frame, textvariable=self.buttons_var)
        buttons_label.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Select Buttons Button
        select_btn = ttk.Button(monitor_frame, text="Select Buttons to Monitor", command=self.select_buttons)
        select_btn.grid(row=3, column=0, columnspan=2, pady=10)
        
        monitor_frame.columnconfigure(1, weight=1)
    
    def create_buttons_section(self, parent):
        # Buttons Frame
        buttons_frame = ttk.Frame(parent, padding="5")
        buttons_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Save Settings Button
        save_btn = ttk.Button(buttons_frame, text="Save Settings", command=self.save_settings)
        save_btn.grid(row=0, column=0, padx=5)
        
        # Start Monitor Button
        self.start_btn = ttk.Button(buttons_frame, text="Start Monitor", command=self.start_monitor)
        self.start_btn.grid(row=0, column=1, padx=5)
        
        # Stop Monitor Button
        self.stop_btn = ttk.Button(buttons_frame, text="Stop Monitor", command=self.stop_monitor, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=2, padx=5)
        
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        buttons_frame.columnconfigure(2, weight=1)
    
    def create_status_section(self, parent):
        # Status Frame
        status_frame = ttk.LabelFrame(parent, text="Status", padding="5")
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Status Text
        self.status_text = tk.Text(status_frame, height=10, wrap=tk.WORD)
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.status_text['yscrollcommand'] = scrollbar.set
        
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
    
    def update_status(self, message):
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
    
    def save_settings(self):
        """Save current settings."""
        try:
            # Update Telegram settings
            self.settings.update_telegram_settings(
                self.api_id_var.get(),
                self.api_hash_var.get(),
                self.bot_token_var.get(),
                self.chat_id_var.get()
            )
            
            # Convert displayed 1-based indices to 0-based for storage
            selected_buttons = []
            if self.buttons_var.get() != 'None':
                selected_buttons = [int(x.strip()) - 1 for x in self.buttons_var.get().split(',')]
            
            # Update other settings
            self.settings.update({
                'refresh_interval': float(self.refresh_interval_var.get()),
                'url': self.url_var.get(),
                'selected_buttons': selected_buttons
            })
            
            self.update_status("Settings saved successfully!")
        except Exception as e:
            self.update_status(f"Error saving settings: {str(e)}")
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def select_buttons(self):
        """Select buttons to monitor."""
        try:
            url = self.url_var.get()
            selected = self.controller.select_buttons(url)  # Returns 0-based indices
            
            if selected:
                # Convert 0-based indices to 1-based for display
                button_numbers = [i + 1 for i in selected]
                self.buttons_var.set(', '.join(map(str, button_numbers)))
                self.settings.set('selected_buttons', selected)  # Store 0-based indices
                self.start_btn.config(state=tk.NORMAL)
            else:
                self.buttons_var.set("None")
                self.settings.set('selected_buttons', [])
                self.start_btn.config(state=tk.DISABLED)
            
        except Exception as e:
            self.update_status(f"Error selecting buttons: {str(e)}")
            messagebox.showerror("Error", f"Failed to select buttons: {str(e)}")
            self.start_btn.config(state=tk.DISABLED)
    
    def start_monitor(self):
        """Start monitoring the selected buttons."""
        if not all([
            self.api_id_var.get(),
            self.api_hash_var.get(),
            self.bot_token_var.get(),
            self.chat_id_var.get()
        ]):
            messagebox.showerror("Error", "Please fill in all Telegram settings first!")
            return
        
        try:
            # Save current settings before starting
            self.save_settings()
            
            # Get selected buttons (already 0-based from settings)
            selected_buttons = self.settings.get('selected_buttons', [])
            
            if not selected_buttons:
                messagebox.showerror("Error", "Please select at least one button to monitor first!")
                return
            
            # Update UI state
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            # Start monitor in a separate thread
            self.monitor_thread = threading.Thread(
                target=self.controller.start_monitoring,
                args=(
                    self.url_var.get(),
                    float(self.refresh_interval_var.get()),
                    selected_buttons,
                    self.update_status
                )
            )
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
            self.update_status("Monitor started...")
            
        except Exception as e:
            self.update_status(f"Error starting monitor: {str(e)}")
            messagebox.showerror("Error", f"Failed to start monitor: {str(e)}")
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
    
    def stop_monitor(self):
        """Stop the monitoring process."""
        try:
            self.controller.stop_monitoring()
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.update_status("Monitor stopped.")
        except Exception as e:
            self.update_status(f"Error stopping monitor: {str(e)}")
            messagebox.showerror("Error", f"Failed to stop monitor: {str(e)}")
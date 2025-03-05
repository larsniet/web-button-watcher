"""Notification system for Web Button Watcher."""

import logging
import os
from typing import Optional
from .settings import SettingsManager

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Sends notifications via Telegram."""
    
    def __init__(self, settings_manager=None):
        """Initialize the Telegram notifier.
        
        Args:
            settings_manager: Optional settings manager instance.
                If None, creates a new one.
        """
        self.settings_manager = settings_manager or SettingsManager()
        self.telegram_settings = self.settings_manager.get_telegram_settings()
        
        # Check if Telegram settings are configured
        if not all(self.telegram_settings.values()):
            logger.warning("Telegram settings not fully configured")
    
    def send_notification(self, message: str) -> bool:
        """Send a notification via Telegram.
        
        Args:
            message: The message to send.
            
        Returns:
            True if successful, False otherwise.
        """
        if not all(self.telegram_settings.values()):
            logger.error("Telegram settings not fully configured")
            return False
        
        try:
            # Import here to avoid dependency if not used
            import telethon
            from telethon import TelegramClient
            
            api_id = self.telegram_settings['api_id']
            api_hash = self.telegram_settings['api_hash']
            bot_token = self.telegram_settings['bot_token']
            chat_id = self.telegram_settings['chat_id']
            
            # Create a temporary session file
            session_file = "bot_session"
            
            # Create and start the client
            client = TelegramClient(session_file, api_id, api_hash)
            client.start(bot_token=bot_token)
            
            # Send the message
            client.loop.run_until_complete(
                client.send_message(chat_id, message)
            )
            
            # Disconnect the client
            client.disconnect()
            
            logger.info(f"Sent Telegram notification: {message[:50]}...")
            return True
            
        except ImportError:
            logger.error("Telethon package not installed. Cannot send Telegram notifications.")
            print("\nTo enable Telegram notifications, install the telethon package:")
            print("pip install telethon")
            return False
            
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
            return False 
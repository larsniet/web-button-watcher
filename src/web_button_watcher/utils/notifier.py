from telethon import TelegramClient
from telethon.sessions import MemorySession
import logging
import asyncio
from .settings import Settings

class TelegramNotifier:
    def __init__(self):
        # Load settings
        settings = Settings()
        telegram_settings = settings.get_telegram_settings()
        
        # Configure logging
        logging.basicConfig(level=logging.INFO,
                          format='%(asctime)s - %(levelname)s - %(message)s')
        
        # Get Telegram credentials from settings
        self.api_id = telegram_settings.get('api_id')
        self.api_hash = telegram_settings.get('api_hash')
        self.bot_token = telegram_settings.get('bot_token')
        chat_id = telegram_settings.get('chat_id')
        
        # Convert chat_id and api_id to integers
        try:
            self.chat_id = int(chat_id) if chat_id else None
            self.api_id = int(self.api_id) if self.api_id else None
        except ValueError as e:
            logging.error("API_ID and CHAT_ID must be integers")
            raise e
        
        # Validate credentials
        if not all([self.api_id, self.api_hash, self.bot_token, self.chat_id]):
            raise ValueError("Missing Telegram credentials. Please configure them in the settings.")
        
        logging.info("Checking Telegram credentials:")
        logging.info(f"API ID present: {'Yes' if self.api_id else 'No'}")
        logging.info(f"API Hash present: {'Yes' if self.api_hash else 'No'}")
        logging.info(f"Bot Token present: {'Yes' if self.bot_token else 'No'}")
        logging.info(f"Chat ID present: {'Yes' if self.chat_id else 'No'}")
        
        try:
            # Use MemorySession to avoid database locking
            self.client = TelegramClient(MemorySession(), self.api_id, self.api_hash)
            
            # Create an event loop for this instance
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Start the client
            self.loop.run_until_complete(self._init_client())
            
        except Exception as e:
            logging.error(f"Failed to initialize Telegram notifier: {e}")
            if hasattr(self, 'client'):
                self.loop.run_until_complete(self.client.disconnect())
            if hasattr(self, 'loop'):
                self.loop.close()
            raise
    
    async def _init_client(self):
        """Initialize the Telegram client."""
        await self.client.start(bot_token=self.bot_token)
        await self.client.send_message(self.chat_id, "🤖 Bot initialized and ready to monitor buttons!")
        logging.info("Test message sent successfully")
        logging.info("Telegram notifier initialized successfully")
    
    def notify_button_clicked(self, button_number, text):
        """Send notification when a button is clicked."""
        try:
            message = f"🔔 Button {button_number} changed to: {text}"
            self.loop.run_until_complete(self.client.send_message(self.chat_id, message))
            logging.info(f"Notification sent: {message}")
            return True
        except Exception as e:
            logging.error(f"Failed to send notification: {e}")
            return False
    
    def __del__(self):
        """Cleanup when the object is destroyed."""
        if hasattr(self, 'client') and hasattr(self, 'loop'):
            try:
                self.loop.run_until_complete(self.client.disconnect())
                self.loop.close()
            except:
                pass 
#!/usr/bin/env python3
"""Development launcher for Web Button Watcher."""

import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logger.debug("Starting Web Button Watcher...")

try:
    logger.debug("Importing main function...")
    from web_button_watcher import main
    logger.debug("Main function imported successfully")
    
    if __name__ == "__main__":
        logger.debug("Calling main function...")
        # Pass command line arguments to main
        main()
        logger.debug("Main function completed")
except Exception as e:
    logger.exception(f"Error occurred: {e}")
    sys.exit(1)
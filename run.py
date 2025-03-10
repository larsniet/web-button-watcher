#!/usr/bin/env python3
"""Development launcher for Web Button Watcher."""

import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


logger.debug("Starting Web Button Watcher...")

try:
    # Try to import and run the PyQt5 GUI
    logger.debug("Importing PyQt5 GUI...")
    from webbuttonwatcher.interface.gui import main
    
    if __name__ == "__main__":
        logger.debug("Starting PyQt5 GUI...")
        main()
except ImportError as e:
    logger.error(f"Error importing PyQt5 GUI: {e}")
    print("\nPyQt5 GUI failed to load. The error was:")
    print(f"{e}\n")
    
    # Try to fall back to Qt GUI directly
    print("Attempting to fall back to Qt GUI directly...")
    try:
        from webbuttonwatcher.interface.gui import QtMonitorGUI
        from PyQt5.QtWidgets import QApplication
        import sys
        
        if __name__ == "__main__":
            app = QApplication(sys.argv)
            app.setStyle("Fusion")
            gui = QtMonitorGUI()
            gui.show()
            sys.exit(app.exec_())
    except ImportError as qt_error:
        logger.error(f"Error importing Qt GUI: {qt_error}")
        print("\nFailed to load Qt GUI. The error was:")
        print(f"{qt_error}\n")
        
        # Fall back to CLI
        print("Falling back to command-line interface...")
        try:
            from webbuttonwatcher.interface.cli import cli_main
            cli_main()
        except Exception as cli_error:
            logger.exception(f"Error in CLI mode: {cli_error}")
            print(f"\nFailed to start CLI mode: {cli_error}")
            sys.exit(1)
except Exception as e:
    logger.exception(f"Error occurred: {e}")
    sys.exit(1)
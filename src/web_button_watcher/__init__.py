"""Web Button Watcher - Monitor buttons on websites for changes."""

import logging
import sys
import os
import atexit
import argparse
from .interface.cli import MonitorController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the application."""
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description="Web Button Watcher")
        parser.add_argument("--cli", action="store_true", help="Use CLI interface instead of GUI")
        args = parser.parse_args()
        
        if args.cli:
            # Use CLI interface
            controller = MonitorController()
            controller.run()
        else:
            # Use GUI interface by default
            try:
                import tkinter as tk
                from .interface.gui import MonitorGUI
                
                # Create root window
                root = tk.Tk()
                
                # Set up Tcl/Tk notifier for macOS
                if sys.platform == 'darwin':
                    root.createcommand('::tk::mac::Quit', root.destroy)
                
                # Create and start GUI
                app = MonitorGUI(root)
                root.mainloop()
                
            except ImportError as e:
                logger.error(f"Failed to import GUI dependencies: {e}")
                print("\nGUI dependencies not available. Falling back to CLI interface.")
                controller = MonitorController()
                controller.run()
            
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        print("\nApplication terminated.")
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        print(f"\nAn error occurred: {e}")
        sys.exit(1)
    finally:
        # Ensure cleanup happens
        logger.info("Cleaning up resources...")
        try:
            # If controller exists, clean up
            if 'controller' in locals():
                controller.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    main()

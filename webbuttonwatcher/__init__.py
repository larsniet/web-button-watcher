"""Main entry point for the Web Button Watcher."""

import sys
import logging
import argparse
from importlib.metadata import version, PackageNotFoundError

__version__ = "0.1.24"

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    """Run the application."""
    logger.debug("Starting Web Button Watcher")
    
    parser = argparse.ArgumentParser(description="Web Button Watcher")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode instead of GUI")
    parser.add_argument("--version", action="store_true", help="Show version information")
    args = parser.parse_args()
    
    if args.version:
        print(f"Web Button Watcher version: {__version__}")
        return
    
    if args.cli:
        # Run in CLI mode
        from webbuttonwatcher.interface.cli import cli_main
        cli_main()
    else:
        # Import PyQt GUI
        try:
            from webbuttonwatcher.interface.gui import main as qt_main
            qt_main()
        except ImportError as e:
            logger.error(f"Error importing PyQt5 GUI: {e}")
            logger.info("Falling back to Tkinter GUI")
            try:
                # Fallback to Tkinter GUI if PyQt is not available
                from webbuttonwatcher.interface.gui import TkMonitorGUI
                import tkinter as tk
                
                root = tk.Tk()
                root.title("Web Button Watcher")
                root.geometry("600x800")
                app = TkMonitorGUI(root)
                root.mainloop()
            except Exception as tk_error:
                logger.error(f"Error running Tkinter GUI: {tk_error}")
                logger.info("Falling back to CLI mode")
                from webbuttonwatcher.interface.cli import cli_main
                cli_main()

if __name__ == "__main__":
    main()

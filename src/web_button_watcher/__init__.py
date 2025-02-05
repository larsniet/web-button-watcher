"""Web Button Watcher - A tool for monitoring and interacting with buttons on web pages."""

import tkinter as tk
import sys
from .interface.gui import MonitorGUI

# Single source of truth for version
__version__ = "0.1.0"
__author__ = "Lars"
__license__ = "MIT"

def main():
    """Main entry point for the Web Button Watcher application."""
    # Create root window
    root = tk.Tk()
    
    # Set up Tcl/Tk notifier for macOS
    if sys.platform == 'darwin':
        root.createcommand('::tk::mac::Quit', root.destroy)
    
    app = MonitorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

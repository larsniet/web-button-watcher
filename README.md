# WebButtonWatcher

[![Tests](https://github.com/larsniet/web-button-watcher/actions/workflows/test.yml/badge.svg)](https://github.com/larsniet/web-button-watcher/actions/workflows/test.yml)
[![Release](https://github.com/larsniet/web-button-watcher/actions/workflows/build.yml/badge.svg)](https://github.com/larsniet/web-button-watcher/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/larsniet/web-button-watcher/branch/main/graph/badge.svg)](https://codecov.io/gh/larsniet/web-button-watcher)
[![PyPI version](https://badge.fury.io/py/web-button-watcher.svg)](https://badge.fury.io/py/web-button-watcher)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/larsniet/web-button-watcher)](https://github.com/larsniet/web-button-watcher/releases)

A Python application that monitors website buttons for state changes and sends notifications when they occur.

## Problem Solved

Ever missed out on an opportunity because you didn't notice a button changing state on a website? Whether it's a "Buy Now" button becoming available, a "Register" button activating, or any interactive element changing - manually checking websites is tedious and error-prone. WebButtonWatcher solves this by automatically monitoring buttons you select and sending instant notifications when their state changes.

## Features

- Visually select any button on any website to monitor
- Receive instant Telegram notifications when button states change
- Smart detection of button text and state changes
- Support for multiple monitoring sessions
- Automatic error recovery and browser reconnection
- Configurable monitoring intervals
- Adjustable notification settings
- Persistent configuration between sessions
- Undetected browser automation to avoid detection
- Support for complex websites with dynamic content
- Cross-platform compatibility (Windows, macOS, Linux)

## Screenshots

[Screenshots would go here]

## Requirements

- Python 3.8 or higher
- Chrome browser (will be automatically managed)
- Internet connection for monitoring and notifications
- Telegram account (for receiving notifications)

## Installation

### Quick Install (Prebuilt Binaries)

The easiest way to get started is to download the pre-built executable for your operating system:

1. Go to the [Releases page](https://github.com/larsniet/web-button-watcher/releases/latest)
2. Download the appropriate file for your system:
   - **Windows**: Download `webbuttonwatcher-windows.zip`, extract the contents, and run "WebButtonWatcher.exe"
   - **macOS**: Download `webbuttonwatcher-macos.zip`, extract and open the app
     - **Important**: When first opening the app, right-click (or Ctrl+click) on it and select "Open" from the menu. When prompted, click "Open" again to bypass the security warning.
   - **Linux**: Download `webbuttonwatcher-linux`, make it executable with `chmod +x webbuttonwatcher-linux`, and run it

No installation is required - just download and run!

### From PyPI

```bash
pip install web-button-watcher
```

Then run the application:

```bash
webbuttonwatcher-gui
```

### From Source

1. Clone this repository:
   ```bash
   git clone https://github.com/larsniet/web-button-watcher.git
   cd web-button-watcher
   ```

2. Install the package in development mode:
   ```bash
   pip install -e .
   ```

3. Run the application:
   ```bash
   webbuttonwatcher-gui
   ```

## Usage

### GUI Application

The GUI provides an intuitive interface to:
- Enter your Telegram notification details
- Specify the website URL to monitor
- Visually select buttons to watch
- Configure monitoring intervals
- Start and stop monitoring sessions
- View real-time monitoring logs

Launch the GUI with:

```bash
# If installed via pip
webbuttonwatcher-gui

# Or
python -m webbuttonwatcher.interface.gui

# Or from the source directory
python webbuttonwatcher/interface/gui.py
```

### Command Line Interface

For command-line usage:

```bash
# If installed via pip
webbuttonwatcher --url "https://example.com" --mode interactive

# Or
python -m webbuttonwatcher.cli --url "https://example.com" --mode interactive
```

With custom monitoring interval:

```bash
webbuttonwatcher --url "https://example.com" --interval 60
```

### Command Line Arguments

- `--url`: The URL of the website to monitor (required)
- `--mode`: Monitoring mode (interactive or headless)
- `--interval`: Time between checks in seconds (default: 300)
- `--notify`: Notification method (telegram, email, etc.)
- `--config`: Path to custom configuration file
- `--verbose`: Enable verbose logging
- `--version`: Show version information and exit

## Telegram Setup

To receive notifications via Telegram:

1. Create a bot through [@BotFather](https://t.me/botfather):
   - Start a chat with @BotFather
   - Send `/newbot` and follow the instructions
   - Copy the API token provided

2. Get your Telegram credentials:
   - Create an application at [my.telegram.org/apps](https://my.telegram.org/apps)
   - Note your API ID and API hash

3. Find your chat ID:
   - Send a message to your new bot
   - In the app, enter your bot token and the app will detect your chat ID

## Project Structure

```
web-button-watcher/             # Project root
├── LICENSE                     # MIT license file
├── README.md                   # Project documentation
├── requirements.txt            # Dependencies
├── setup.py                    # Package installation
├── pyproject.toml              # Modern Python packaging
├── setup.cfg                   # Package configuration
├── MANIFEST.in                 # Package manifest
├── pytest.ini                  # pytest configuration
├── release.sh                  # Release automation script
├── build.py                    # Build script for executables
├── resources/                  # Application resources
│   ├── icon.ico                # Windows icon
│   ├── icon.icns               # macOS icon
│   └── icon.png                # Application icon
├── webbuttonwatcher/           # Main package
│   ├── __init__.py             # Package init, version info
│   ├── cli.py                  # Command-line interface
│   ├── core/                   # Core functionality
│   │   ├── __init__.py
│   │   ├── monitor.py          # Button monitoring logic
│   │   ├── notifier.py         # Notification system
│   │   └── settings.py         # Configuration handling
│   └── interface/              # User interfaces
│       ├── __init__.py
│       └── gui.py              # GUI implementation
└── .github/workflows/          # CI/CD workflows
    ├── build.yml               # Build workflow for releases
    ├── publish.yml             # PyPI publishing workflow
    └── test.yml                # Testing workflow
```

## Running Tests

To run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run the tests
pytest

# Run tests with coverage report
pytest --cov=webbuttonwatcher
```

The test suite includes:
- Unit tests for core monitoring functionality
- Notification system tests
- Configuration handling tests
- Interface component tests
- Integration tests with mocked browser instances

## Releases

### Automated Builds

This project uses GitHub Actions to automatically build and release packages for Windows, macOS, and Linux. When a new release tag is pushed (e.g., `v0.1.0`), the following happens:

1. Tests are run on all supported platforms
2. A new GitHub Release is created
3. Binary packages are built for each platform:
   - Windows: Standalone executable in a ZIP archive
   - macOS: Standalone `.app` bundle in a ZIP archive
   - Linux: Standalone executable file
4. Python package is published to PyPI

### Creating a New Release

To create a new release:

```bash
# Use the release script (macOS/Linux)
./release.sh 0.1.0
```

The script will:
1. Ensure you're on the main branch
2. Run tests to verify everything works
3. Update the version number in the code
4. Commit and push the version change
5. Create and push a Git tag
6. GitHub Actions will automatically build and publish the release

## Troubleshooting

### Common Issues

- **Chrome doesn't launch**: The application requires Chrome to be installed. If it's not found, try installing or updating Chrome.

- **Telegram notifications not working**: Double-check your Telegram bot token and chat ID. Make sure you've started a conversation with your bot.

- **Website detection**: Some websites use bot protection which might interfere with monitoring. Try increasing the monitoring interval or switching to a different browser setting.

- **Application crashes**: Check that you have the latest version. If the issue persists, report it on the [issue tracker](https://github.com/larsniet/web-button-watcher/issues).

### Getting Help

If you encounter any issues:

1. Check existing [issues](https://github.com/larsniet/web-button-watcher/issues) to see if others have had the same problem
2. If all else fails, [open a new issue](https://github.com/larsniet/web-button-watcher/issues/new) with details about your problem

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

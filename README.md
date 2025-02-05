# WebButtonWatcher

[![Tests](https://github.com/larsniet/web-button-watcher/actions/workflows/test.yml/badge.svg)](https://github.com/larsniet/web-button-watcher/actions/workflows/test.yml)
[![Release](https://github.com/larsniet/web-button-watcher/actions/workflows/release.yml/badge.svg)](https://github.com/larsniet/web-button-watcher/actions/workflows/release.yml)
[![codecov](https://codecov.io/gh/larsniet/web-button-watcher/branch/main/graph/badge.svg)](https://codecov.io/gh/larsniet/web-button-watcher)

Ever missed out on an opportunity because you didn't notice a button changing state on a website? Whether it's a "Buy Now" button becoming available, a "Register" button activating, or any other interactive element changing - WebButtonWatcher has got you covered.

## What is WebButtonWatcher?

WebButtonWatcher is your vigilant assistant that keeps an eye on any buttons you choose on any website. When a button changes state - maybe from "Sold Out" to "Buy Now" or "Closed" to "Register" - you'll instantly know about it through a Telegram notification.

### The Story

Imagine you're waiting for:

- A limited edition product to become available
- A registration slot to open up
- A "Download" button to activate
- A form to become submittable

Instead of constantly refreshing the page and staring at your screen, WebButtonWatcher does the watching for you. It's like having a friend who never sleeps, constantly checking the website and immediately letting you know when something changes.

## Getting Started

### Quick Start

1. Download the latest release for your platform:

   - [Download for Windows](https://github.com/larsniet/web-button-watcher/releases/latest)
   - [Download for macOS](https://github.com/larsniet/web-button-watcher/releases/latest)

2. Set up your Telegram bot (one-time setup):

   - Create a bot through [@BotFather](https://t.me/botfather)
   - Get your API credentials from [my.telegram.org/apps](https://my.telegram.org/apps)
   - Send a message to your bot and get your chat ID

3. Launch WebButtonWatcher and:
   - Enter your Telegram details (they'll be securely saved for next time)
   - Paste the URL you want to monitor
   - Click "Select Buttons" and choose which buttons to watch
   - Hit "Start Monitor" and relax!

### For Developers

If you want to run from source or contribute:

```bash
# Clone and install
git clone https://github.com/larsniet/web-button-watcher.git
cd web-button-watcher
pip install -e ".[dev]"

# Run the application
web-button-watch
```

## How It Works

WebButtonWatcher uses smart automation to:

1. Load the webpage you specify
2. Let you visually select which buttons to monitor
3. Keep track of their original state
4. Periodically check for changes
5. Send you instant notifications when something changes

All of this happens in the background, using:

- Undetected Chrome automation to avoid detection
- Secure Telegram messaging for notifications
- Local settings storage for persistence
- Clean error handling for reliability

## Real-World Use Cases

Our users have used WebButtonWatcher to:

- Snag limited edition products the moment they become available
- Get into fully-booked courses when spots open up
- Monitor deployment status buttons
- Track form submission windows
- Get notified when downloads become available

## Smart Features

- **Visual Selection**: Point and click to choose buttons - no technical knowledge needed
- **Persistent Settings**: Your configuration is remembered between sessions
- **Smart Monitoring**: Efficiently checks for changes without overwhelming the website
- **Instant Notifications**: Get Telegram messages the moment something changes
- **Error Recovery**: Automatically handles network issues and page reloads

## Contributing

Have an idea to make WebButtonWatcher even better? We'd love your help! Check out our [contributing guidelines](CONTRIBUTING.md) to get started.

## Support

- 📖 [Documentation](docs/README.md)
- 🐛 [Issue Tracker](https://github.com/larsniet/web-button-watcher/issues)
- 💬 [Discussions](https://github.com/larsniet/web-button-watcher/discussions)

## License

WebButtonWatcher is open source software licensed under the MIT license. See the [LICENSE](LICENSE) file for more details.

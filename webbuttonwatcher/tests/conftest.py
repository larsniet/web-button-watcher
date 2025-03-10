"""
Pytest configuration and fixtures for the WebButtonWatcher test suite.
"""

import pytest
import sys
from unittest.mock import MagicMock, patch
import warnings

# Suppress all warnings for cleaner test output
warnings.filterwarnings("ignore")

# Define markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "gui: mark tests that require a GUI/browser")
    config.addinivalue_line("markers", "integration: mark tests that connect to external services")

# Automatically apply the gui marker to test classes/modules with relevant names
def pytest_collection_modifyitems(items):
    """Add gui marker to tests that would launch a browser."""
    for item in items:
        # Mark all tests in test_integration.py as both gui and integration
        if "test_integration" in item.module.__name__:
            item.add_marker(pytest.mark.gui)
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.skip(reason="GUI test disabled"))
        
        # Mark button_selector tests as gui since they interact with browser UI
        elif "button_selector" in item.module.__name__:
            item.add_marker(pytest.mark.gui)
            item.add_marker(pytest.mark.skip(reason="GUI test disabled"))
        
        # Mark monitor tests with browser interaction as gui
        elif "test_monitor" in item.module.__name__ and any(
            browser_keyword in item.name 
            for browser_keyword in ["browser", "driver", "chrome", "button"]
        ):
            item.add_marker(pytest.mark.gui)
            item.add_marker(pytest.mark.skip(reason="GUI test disabled"))

        # Any test that mentions selenium or chromedriver likely uses a browser
        elif hasattr(item, "function") and (
            "selenium" in item.function.__module__ or 
            "chromedriver" in item.function.__module__
        ):
            item.add_marker(pytest.mark.gui)
            item.add_marker(pytest.mark.skip(reason="GUI test disabled"))

# Create mock browser components
@pytest.fixture(autouse=True)
def mock_browser_components(monkeypatch):
    """Mock browser components to prevent actual browser launching."""
    # Create a mock driver class
    class MockDriver:
        def __init__(self, *args, **kwargs):
            pass
        
        def __getattr__(self, name):
            return MagicMock()
    
    # Mock the imports
    for module_name in [
        'selenium.webdriver',
        'selenium.webdriver.chrome.webdriver',
        'undetected_chromedriver',
    ]:
        try:
            # Only mock if the module exists or might be imported
            monkeypatch.setattr(f"{module_name}.Chrome", MockDriver)
        except (ImportError, AttributeError):
            pass

# Common test fixtures
@pytest.fixture
def mock_notifier():
    """Create a mock notifier for testing."""
    notifier = MagicMock()
    notifier.send_notification.return_value = True
    return notifier 
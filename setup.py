from setuptools import setup, find_packages
import re
from pathlib import Path
import io

def get_version():
    """Get version from __init__.py"""
    init_file = Path("src/web_button_watcher/__init__.py").read_text(encoding='utf-8')
    version_match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", init_file)
    if not version_match:
        raise RuntimeError("Version not found")
    return version_match.group(1)

# Read README with proper encoding
def read_file(filename):
    with io.open(filename, encoding='utf-8') as f:
        return f.read()

setup(
    name="web-button-watcher",
    version=get_version(),
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "selenium>=4.18.1",
        "webdriver-manager>=4.0.1",
        "undetected-chromedriver>=3.5.5",
        "telethon>=1.33.1",
        "python-dotenv>=1.0.0",
        "tk>=0.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.12.0",
            "pytest-asyncio>=0.23.5",
            "pyinstaller>=6.5.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "web-button-watch=web_button_watcher.interface.gui:main",
        ]
    },
    author="Lars",
    author_email="lars@lvdn.nl",
    description="A tool for monitoring and automatically interacting with buttons on web pages",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    keywords="web automation, button monitoring, selenium, chrome, telegram",
    url="https://github.com/larsniet/web-button-watcher",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Monitoring",
    ],
) 
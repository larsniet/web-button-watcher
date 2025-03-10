from setuptools import setup, find_packages
import re
from pathlib import Path
import io
import sys
import os

# Read version from __init__.py
try:
    init_file = Path("webbuttonwatcher/__init__.py").read_text(encoding='utf-8')
    version_line = next(line for line in init_file.splitlines() if line.startswith('__version__'))
    version = version_line.split('=')[1].strip().strip('"\'')
except Exception as e:
    print(f"Error reading version: {e}")
    version = '0.0.0'

# Read README with proper encoding
def read_file(filename):
    with io.open(filename, encoding='utf-8') as f:
        return f.read()

setup(
    name="web-button-watcher",
    version=version,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "selenium>=4.10.0",
        "undetected-chromedriver>=3.5.0",
        "telethon>=1.29.2",
        "python-dotenv>=1.0.0",
        "webdriver-manager>=4.0.0",
        "PyQt5>=5.15.0",
        "PyQtWebEngine>=5.15.0",
        "websockets>=12.0",
    ],
    entry_points={
        "console_scripts": [
            "web-button-watcher=webbuttonwatcher:main",
        ],
    },
    description="Monitors websites for button changes and sends Telegram notifications",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    author="Lars Niet",
    author_email="info@larsniet.nl",
    url="https://github.com/larsniet/web-button-watcher",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
) 
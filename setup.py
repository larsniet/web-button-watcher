"""
Compatibility setup script for projects that don't support pyproject.toml directly.
Most configuration is now in pyproject.toml.
"""

from setuptools import setup
import re
from pathlib import Path

# Read version from __init__.py
try:
    init_file = Path("webbuttonwatcher/__init__.py").read_text(encoding='utf-8')
    version_line = next(line for line in init_file.splitlines() if line.startswith('__version__'))
    version = version_line.split('=')[1].strip().strip('"\'')
except Exception as e:
    print(f"Error reading version: {e}")
    version = '0.0.0'

# Setup with minimal configuration - most is in pyproject.toml
setup(
    version=version,
) 
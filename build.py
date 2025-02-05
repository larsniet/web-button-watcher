#!/usr/bin/env python3
"""Build script for creating standalone executables."""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build():
    """Clean build directories."""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    # Clean PyInstaller cache
    cache = Path.home() / '.pyinstaller'
    if cache.exists():
        shutil.rmtree(cache)

def build_app():
    """Build the application for the current platform."""
    platform = sys.platform
    
    # Clean previous builds
    clean_build()
    
    # Install dependencies
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', '.[dev]'], check=True)
    
    # Create build command using Python module
    cmd = [
        sys.executable,
        '-m',
        'PyInstaller',
        '--clean',
        '--noconfirm',
    ]
    
    # Add platform-specific options
    if platform == 'darwin':
        cmd.extend(['--target-arch', 'universal2'])
    
    cmd.append('web_button_watcher.spec')
    
    # Run build
    subprocess.run(cmd, check=True)
    
    # Create platform-specific archive
    dist_dir = Path('dist')
    if platform == 'darwin':
        # For macOS, create a DMG
        app_path = dist_dir / 'WebButtonWatcher.app'
        if app_path.exists():
            # Create temporary directory for DMG contents
            dmg_dir = dist_dir / 'dmg'
            dmg_dir.mkdir(exist_ok=True)
            
            # Copy .app to DMG directory
            shutil.copytree(app_path, dmg_dir / 'WebButtonWatcher.app', dirs_exist_ok=True)
            
            # Create DMG
            subprocess.run([
                'hdiutil',
                'create',
                '-volname', 'WebButtonWatcher',
                '-srcfolder', dmg_dir,
                '-ov',
                '-format', 'UDZO',
                dist_dir / 'WebButtonWatcher-macOS.dmg'
            ], check=True)
            
            # Clean up temporary directory
            shutil.rmtree(dmg_dir)
    elif platform == 'win32':
        # For Windows, create a ZIP
        import zipfile
        with zipfile.ZipFile(dist_dir / 'WebButtonWatcher-Windows.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(dist_dir / 'WebButtonWatcher'):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, dist_dir)
                    zipf.write(file_path, arcname)

if __name__ == '__main__':
    build_app() 
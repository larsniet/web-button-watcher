#!/usr/bin/env python3
"""Build script for creating standalone executables."""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import time

MAIN_SCRIPT = 'src/webbuttonwatcher/interface/gui.py'  # Entry point (updated to gui.py)

def clean_build():
    """Clean up previous build files."""
    print("Cleaning previous build files...")
    
    # Directories to clean
    dirs_to_clean = ['dist', 'build', 'WebButtonWatcher.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                if os.path.isdir(dir_name):
                    shutil.rmtree(dir_name)
                else:
                    os.remove(dir_name)
            except Exception as e:
                print(f"Warning: Could not fully clean {dir_name}: {e}")
                # Try forcing cleanup with command-line
                try:
                    if os.path.exists(dir_name):
                        subprocess.run(['rm', '-rf', dir_name], check=False)
                except:
                    print(f"Warning: Forced cleanup of {dir_name} also failed")
                    
    # Make sure the directories are gone
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name) and os.path.isdir(dir_name):
            print(f"Warning: {dir_name} still exists. Please manually delete it if build fails.")

def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def build_exe():
    """Build executable for the current platform."""
    platform = sys.platform
    print(f"Building for platform: {platform}")
    
    # Clean previous builds
    clean_build()
    
    # Check for PyInstaller
    if not check_pyinstaller():
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
    
    # Create spec file if it doesn't exist
    spec_file = Path('webbuttonwatcher.spec')
    if not spec_file.exists():
        print("Creating spec file...")
        
        # Basic PyInstaller command
        spec_cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--name=webbuttonwatcher',  # Use lowercase to match expected spec filename
            '--windowed',  # GUI application
            '--onedir',    # Create a directory with the executable
            '--noupx',     # Don't use UPX (can cause issues)
            '--log-level=INFO',
            MAIN_SCRIPT
        ]
        
        # Platform-specific additions
        if platform == 'darwin':  # macOS
            spec_cmd.extend([
                '--icon=resources/icon.icns',
                '--osx-bundle-identifier=com.larsniet.webbuttonwatcher'
            ])
        elif platform == 'win32':  # Windows
            spec_cmd.extend([
                '--icon=resources/icon.ico',
            ])
        
        # Create the spec file
        subprocess.run(spec_cmd, check=True)
    
    # Build using the spec file
    print("Building executable...")
    build_cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',        # Clean cache
        '--noconfirm',    # Don't ask for confirmation
        spec_file
    ]
    subprocess.run(build_cmd, check=True)
    
    # Create distribution packages based on platform
    create_distribution(platform)
    
    print("\nBuild completed successfully!")
    if platform == 'darwin':
        print(f"Application bundle: {Path('dist/WebButtonWatcher.app')}")
        print(f"DMG package: {Path('dist/WebButtonWatcher-macOS.dmg')}")
    elif platform == 'win32':
        print(f"Executable directory: {Path('dist/WebButtonWatcher')}")
        print(f"ZIP package: {Path('dist/WebButtonWatcher-Windows.zip')}")
    else:
        print(f"Executable directory: {Path('dist/WebButtonWatcher')}")

def create_distribution(platform):
    """Create distribution packages (DMG for macOS, ZIP for Windows)."""
    print("\nCreating distribution package...")
    
    if platform == 'darwin':  # macOS
        # Create DMG
        app_path = Path('dist/WebButtonWatcher.app')
        if app_path.exists():
            try:
                # Create a temporary directory for DMG contents
                dmg_dir = Path('dist/dmg_temp')
                if dmg_dir.exists():
                    shutil.rmtree(dmg_dir)
                dmg_dir.mkdir(exist_ok=True)
                
                # Copy app to DMG directory
                print("Copying app to DMG directory...")
                app_dest = dmg_dir / 'WebButtonWatcher.app'
                shutil.copytree(app_path, app_dest)
                
                # Create symbolic link to Applications folder
                print("Creating Applications symlink...")
                os.symlink('/Applications', dmg_dir / 'Applications')
                
                # Use macOS dot_clean to remove resource forks and AppleDouble files
                print("Cleaning dot files...")
                try:
                    subprocess.run(['dot_clean', str(dmg_dir)], check=False)
                except Exception as e:
                    print(f"Warning: dot_clean failed: {e}")
                
                # Create the final DMG directly
                final_dmg = 'dist/WebButtonWatcher-macOS.dmg'
                
                # Use HFS+ and specific formatting options to ensure hidden files are properly handled
                subprocess.run([
                    'hdiutil', 'create',
                    '-volname', 'WebButtonWatcher', 
                    '-srcfolder', dmg_dir,
                    '-ov',  # Overwrite existing file
                    '-format', 'UDZO',  # Compressed image
                    '-fs', 'HFS+',  # Use HFS+ filesystem
                    final_dmg
                ], check=True)
                
                print("DMG created successfully!")
                
                # Clean up
                shutil.rmtree(dmg_dir)
                
            except Exception as e:
                print(f"Failed to create DMG: {e}")
                print("App bundle is still available in dist/WebButtonWatcher.app")
    
    elif platform == 'win32':  # Windows
        # Create ZIP
        import zipfile
        zip_path = Path('dist/WebButtonWatcher-Windows.zip')
        exe_dir = Path('dist/WebButtonWatcher')
        if exe_dir.exists():
            try:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(exe_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, 'dist')
                            zipf.write(file_path, arcname)
                print("ZIP file created successfully")
            except Exception as e:
                print(f"Failed to create ZIP: {e}")
                print("Executable is still available in dist/WebButtonWatcher")

def create_resources():
    """Create necessary resources for the build."""
    # Create resources directory if it doesn't exist
    resources_dir = Path('resources')
    resources_dir.mkdir(exist_ok=True)
    
    # Check for icon files
    icon_files = {
        'darwin': resources_dir / 'icon.icns',
        'win32': resources_dir / 'icon.ico'
    }
    
    platform = sys.platform
    if platform in icon_files and not icon_files[platform].exists():
        print(f"Warning: Icon file {icon_files[platform]} not found.")
        print("The application will use default system icons.")
        print(f"To use custom icons, place an appropriate icon file at {icon_files[platform]}")

def main():
    """Main function."""
    print("Web Button Watcher Build Script")
    print("---------------------------------")
    print("This will build a standalone executable for your platform.")
    
    # Create resources
    create_resources()
    
    # Build executable
    build_exe()

if __name__ == '__main__':
    main() 
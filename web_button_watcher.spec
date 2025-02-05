# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_dynamic_libs

block_cipher = None

# Set target architecture for macOS
if sys.platform == 'darwin':
    target_arch = 'universal2'
else:
    target_arch = None

a = Analysis(
    ['src/web_button_watcher/__init__.py'],
    pathex=[],
    binaries=collect_dynamic_libs('selenium'),
    datas=[
        ('src/web_button_watcher/interface/*.py', 'web_button_watcher/interface'),
        ('src/web_button_watcher/core/*.py', 'web_button_watcher/core'),
        ('src/web_button_watcher/utils/*.py', 'web_button_watcher/utils'),
        ('.env.example', '.'),
        ('README.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        'selenium',
        'undetected_chromedriver',
        'telethon',
        'python-dotenv',
        'tkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == 'darwin':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='WebButtonWatcher',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        target_arch=target_arch,
        codesign_identity=None,
        entitlements_file=None,
    )
    
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='WebButtonWatcher'
    )
    
    app = BUNDLE(
        coll,
        name='WebButtonWatcher.app',
        icon=None,  # Add your .icns file here if you have one
        bundle_identifier='com.larsniet.webbuttonwatcher',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'LSBackgroundOnly': 'False',
            'NSRequiresAquaSystemAppearance': 'False',
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='WebButtonWatcher',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        target_arch=target_arch,
        codesign_identity=None,
        entitlements_file=None,
    ) 
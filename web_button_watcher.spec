# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/web_button_watcher/__init__.py'],
    pathex=[],
    binaries=[],
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
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico'  # You'll need to create this icon file
) 
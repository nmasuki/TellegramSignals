# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Telegram Signal Extractor
Creates a portable executable for Windows and macOS
"""

import sys
from pathlib import Path

block_cipher = None

# Project root
PROJECT_ROOT = Path(SPECPATH)

# Platform detection
IS_WINDOWS = sys.platform == 'win32'
IS_MACOS = sys.platform == 'darwin'

# Collect data files
datas = [
    # Config files (templates)
    (str(PROJECT_ROOT / 'config' / 'config.yaml'), 'config'),
    # Icons
    (str(PROJECT_ROOT / 'src' / 'gui' / 'resources' / 'icons'), 'src/gui/resources/icons'),
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    # Telethon and its dependencies
    'telethon',
    'telethon.tl',
    'telethon.tl.types',
    'telethon.tl.functions',
    'telethon.crypto',
    'telethon.network',
    # Async support
    'asyncio',
    'aiosqlite',
    # PySide6 modules
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    # Data handling
    'pandas',
    'numpy',
    'dateutil',
    'yaml',
    # HTTP server
    'http.server',
    'socketserver',
    'json',
    # Cryptography (for Telethon)
    'cryptography',
    'cryptography.hazmat.primitives.ciphers.aead',
    # Other
    'pkg_resources.py2_warn',
]

# Platform-specific hidden imports
if IS_WINDOWS:
    hiddenimports.extend([
        'win32api',
        'win32con',
        'win32gui',
        'plyer.platforms.win.notification',
    ])
elif IS_MACOS:
    hiddenimports.extend([
        'plyer.platforms.macosx.notification',
    ])

# Icon file (platform-specific)
if IS_WINDOWS:
    icon_file = str(PROJECT_ROOT / 'src' / 'gui' / 'resources' / 'icons' / 'app.ico')
elif IS_MACOS:
    icon_file = str(PROJECT_ROOT / 'src' / 'gui' / 'resources' / 'icons' / 'app.icns')
else:
    icon_file = None

# Analysis
a = Analysis(
    [str(PROJECT_ROOT / 'src' / 'gui' / 'app.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'tkinter',
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'pylint',
        'black',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TelegramSignals',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=IS_MACOS,  # Enable for macOS drag-and-drop support
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TelegramSignals',
)

# macOS: Create .app bundle
if IS_MACOS:
    app = BUNDLE(
        coll,
        name='TelegramSignals.app',
        icon=icon_file,
        bundle_identifier='com.telegramsignals.app',
        info_plist={
            'CFBundleName': 'Telegram Signals',
            'CFBundleDisplayName': 'Telegram Signal Extractor',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.13.0',
            'NSRequiresAquaSystemAppearance': False,  # Support dark mode
        },
    )

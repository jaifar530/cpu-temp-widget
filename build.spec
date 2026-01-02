# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for CPU Temperature Widget.

To build:
    pyinstaller build.spec

Or simply run:
    python build.py
"""

import os
import sys

block_cipher = None

# Get the directory containing this spec file
spec_dir = os.path.dirname(os.path.abspath(SPECPATH))

a = Analysis(
    ['main.py'],
    pathex=[spec_dir],
    binaries=[],
    datas=[
        ('resources/styles.qss', 'resources'),
        ('resources/icon_data.py', 'resources'),
        ('resources/icon.ico', 'resources'),
        ('libs/LibreHardwareMonitorLib.dll', 'libs'),
        ('libs/HidSharp.dll', 'libs'),
        ('THIRD-PARTY-LICENSES.txt', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'clr',
        'clr_loader',
        'pythonnet',
        'wmi',
        'win32com',
        'win32com.client',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CPUTempWidget',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico' if os.path.exists('resources/icon.ico') else None,
    version='version_info.txt' if os.path.exists('version_info.txt') else None,
    uac_admin=True,  # Request admin privileges for hardware monitoring
)

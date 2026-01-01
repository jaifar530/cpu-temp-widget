#!/usr/bin/env python
"""
Build script for CPU Temperature Widget.

Creates a portable single-file executable using PyInstaller.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def create_icon():
    """Create the application icon from embedded data."""
    from resources.icon_data import save_icon
    
    icon_path = Path('resources/icon.ico')
    if not icon_path.exists():
        print("Creating application icon...")
        save_icon(str(icon_path))
        print(f"  Created: {icon_path}")


def create_version_info():
    """Create version info file for Windows executable."""
    version_info = '''# UTF-8
#
# Version info for CPU Temperature Widget
#

VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Virtual Platforms LLC'),
        StringStruct(u'FileDescription', u'CPU Temperature Widget'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'CPUTempWidget'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2024 Virtual Platforms LLC'),
        StringStruct(u'OriginalFilename', u'CPUTempWidget.exe'),
        StringStruct(u'ProductName', u'CPU Temperature Widget'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    print("Created version_info.txt")


def clean_build():
    """Clean previous build artifacts."""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.pyc', '*.pyo']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}/...")
            shutil.rmtree(dir_name)
    
    # Clean pycache in subdirectories
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                path = os.path.join(root, dir_name)
                print(f"Cleaning {path}/...")
                shutil.rmtree(path)


def build():
    """Build the executable."""
    print("\n" + "="*60)
    print("Building CPU Temperature Widget")
    print("="*60 + "\n")
    
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Clean previous builds
    clean_build()
    
    # Create icon
    try:
        create_icon()
    except Exception as e:
        print(f"Warning: Could not create icon: {e}")
    
    # Create version info
    create_version_info()
    
    # Run PyInstaller
    print("\nRunning PyInstaller...")
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        'build.spec'
    ]
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        exe_path = Path('dist/CPUTempWidget.exe')
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print("\n" + "="*60)
            print("BUILD SUCCESSFUL!")
            print("="*60)
            print(f"\nExecutable: {exe_path.absolute()}")
            print(f"Size: {size_mb:.1f} MB")
            print("\nTo run, execute CPUTempWidget.exe")
            print("For best results, run as Administrator.")
        else:
            print("\nBuild completed but executable not found!")
            return 1
    else:
        print("\nBuild failed!")
        return result.returncode
    
    return 0


if __name__ == '__main__':
    sys.exit(build())

# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for macOS

import os
import sys

# Get the project root directory (parent of BuildTools)
spec_root = os.path.abspath(SPECPATH)
project_root = os.path.dirname(spec_root)

block_cipher = None

a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'src'), 'src'),
        (os.path.join(project_root, 'assets'), 'assets'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Exclude .manga files from the build
a.datas = [x for x in a.datas if not x[0].endswith('.manga')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MangaReader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'assets', 'icon.icns') if os.path.exists(os.path.join(project_root, 'assets', 'icon.icns')) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MangaReader',
)

app = BUNDLE(
    coll,
    name='MangaReader.app',
    icon=os.path.join(project_root, 'assets', 'icon.icns') if os.path.exists(os.path.join(project_root, 'assets', 'icon.icns')) else None,
    bundle_identifier='com.mangareader.app',
    info_plist={
        'CFBundleName': 'Manga Reader',
        'CFBundleDisplayName': 'Manga Reader',
        'CFBundleVersion': '0.0.3',
        'CFBundleShortVersionString': '0.0.3',
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '10.13.0',
    },
)

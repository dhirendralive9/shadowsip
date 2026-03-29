# -*- mode: python ; coding: utf-8 -*-
"""
ShadowSIP PyInstaller Spec
Build: pyinstaller shadowsip.spec
"""

import sys
import os

block_cipher = None

# Determine platform-specific options
is_windows = sys.platform == "win32"
is_linux = sys.platform.startswith("linux")

# Collect resource directories (skip if missing)
_resource_dirs = [
    ("resources/icons", "resources/icons"),
    ("resources/themes", "resources/themes"),
    ("resources/ringtones", "resources/ringtones"),
    ("resources/translations", "resources/translations"),
]
_datas = [(src, dst) for src, dst in _resource_dirs if os.path.isdir(src)]

a = Analysis(
    ["src/shadowsip/main.py"],
    pathex=[],
    binaries=[
        # Phase 1.2: Add pjsua2 shared library here
        # Windows: ("path/to/pjsua2.pyd", "."),
        # Linux: ("path/to/pjsua2.so", "."),
    ],
    datas=_datas,
    hiddenimports=[
        "PySide6.QtSvg",
        "PySide6.QtSvgWidgets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
        "PySide6.Qt3D",
        "PySide6.QtBluetooth",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtQuick",
        "PySide6.QtQuick3D",
        "PySide6.QtRemoteObjects",
        "PySide6.QtSensors",
        "PySide6.QtSerialPort",
        "PySide6.QtWebEngine",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
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
    name="ShadowSIP",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX can trigger antivirus false positives
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="resources/icons/shadowsip.ico" if is_windows and os.path.exists("resources/icons/shadowsip.ico") else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ShadowSIP",
)

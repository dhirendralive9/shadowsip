"""
Platform — OS-specific helpers for paths, resources, and detection.
"""

import os
import sys
import platform


def is_windows() -> bool:
    return sys.platform == "win32"


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def is_macos() -> bool:
    return sys.platform == "darwin"


def get_config_dir() -> str:
    """
    Get the application config directory.
    Windows: %APPDATA%/ShadowSIP/
    Linux: ~/.config/shadowsip/
    macOS: ~/Library/Application Support/ShadowSIP/
    """
    if is_windows():
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(base, "ShadowSIP")
    elif is_macos():
        return os.path.join(os.path.expanduser("~"), "Library",
                            "Application Support", "ShadowSIP")
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME",
                             os.path.join(os.path.expanduser("~"), ".config"))
        return os.path.join(xdg, "shadowsip")


def get_data_dir() -> str:
    """
    Get the application data directory (recordings, call history DB, etc).
    Windows: %LOCALAPPDATA%/ShadowSIP/
    Linux: ~/.local/share/shadowsip/
    """
    if is_windows():
        base = os.environ.get("LOCALAPPDATA", os.environ.get("APPDATA", "~"))
        return os.path.join(base, "ShadowSIP")
    elif is_macos():
        return os.path.join(os.path.expanduser("~"), "Library",
                            "Application Support", "ShadowSIP")
    else:
        xdg = os.environ.get("XDG_DATA_HOME",
                             os.path.join(os.path.expanduser("~"), ".local", "share"))
        return os.path.join(xdg, "shadowsip")


def get_resource_path(*parts) -> str:
    """
    Get path to a bundled resource file.
    Handles both development (src/resources/) and PyInstaller (_MEIPASS) layouts.
    """
    # PyInstaller frozen bundle
    if getattr(sys, "frozen", False):
        base = os.path.join(sys._MEIPASS, "resources")
    else:
        # Development: relative to project root
        base = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ))),
            "resources"
        )
    return os.path.join(base, *parts)


def get_platform_info() -> dict:
    """Get platform information for diagnostics."""
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "hostname": platform.node(),
    }

"""
AppConfig — Configuration management using INI file.
"""

import os
import configparser
import logging

from shadowsip.utils.platform import get_config_dir

logger = logging.getLogger(__name__)


class AppConfig:
    """
    Simple INI-based configuration manager.
    Stores settings in ~/.config/shadowsip/config.ini (Linux)
    or %APPDATA%/ShadowSIP/config.ini (Windows).
    """

    DEFAULTS = {
        "appearance": {
            "theme": "light",
            "font_size": "13",
        },
        "audio": {
            "input_device": "default",
            "output_device": "default",
            "ring_device": "default",
            "ringtone": "default.wav",
        },
        "sip": {
            "transport": "UDP",
            "stun_server": "stun.l.google.com:19302",
            "ice_enabled": "true",
            "srtp_enabled": "false",
        },
        "window": {
            "geometry": "",
        },
    }

    def __init__(self, config_path: str = None):
        self._config = configparser.ConfigParser()

        # Set defaults
        for section, values in self.DEFAULTS.items():
            if not self._config.has_section(section):
                self._config.add_section(section)
            for key, value in values.items():
                self._config.set(section, key, value)

        # Determine config path
        if config_path:
            self._path = config_path
        else:
            config_dir = get_config_dir()
            os.makedirs(config_dir, exist_ok=True)
            self._path = os.path.join(config_dir, "config.ini")

        # Load existing config
        if os.path.exists(self._path):
            self._config.read(self._path, encoding="utf-8")
            logger.info(f"Config loaded from: {self._path}")
        else:
            self.save()
            logger.info(f"Config created at: {self._path}")

    def get(self, section: str, key: str, fallback: str = "") -> str:
        """Get a config value."""
        return self._config.get(section, key, fallback=fallback)

    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """Get a boolean config value."""
        return self._config.getboolean(section, key, fallback=fallback)

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Get an integer config value."""
        return self._config.getint(section, key, fallback=fallback)

    def set(self, section: str, key: str, value: str):
        """Set a config value and save."""
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, key, str(value))
        self.save()

    def save(self):
        """Write config to disk."""
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                self._config.write(f)
        except OSError as e:
            logger.error(f"Failed to save config: {e}")

    @property
    def path(self) -> str:
        return self._path

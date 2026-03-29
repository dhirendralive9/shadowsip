"""
Logging — Application-wide logging configuration.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler

from shadowsip.utils.platform import get_config_dir


def setup_logging(level: int = logging.DEBUG):
    """
    Configure logging to both console and file.
    Log file: ~/.config/shadowsip/shadowsip.log
    """
    log_dir = get_config_dir()
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "shadowsip.log")

    # Root logger
    root = logging.getLogger()
    root.setLevel(level)

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-5s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )
    console.setFormatter(console_fmt)
    root.addHandler(console)

    # File handler (rotating, 5 MB max, keep 3 backups)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-5s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
    )
    file_handler.setFormatter(file_fmt)
    root.addHandler(file_handler)

    logging.info(f"Logging initialized. File: {log_file}")

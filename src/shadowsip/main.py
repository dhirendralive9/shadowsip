#!/usr/bin/env python3
"""
ShadowSIP — Universal Open-Source SIP Softphone
Entry point for the application.
"""

import sys
import os
import signal

# Allow clean Ctrl+C exit
signal.signal(signal.SIGINT, signal.SIG_DFL)


def main():
    """Main entry point."""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt, QCoreApplication
    from PySide6.QtGui import QIcon

    from shadowsip.app import ShadowSIPApp
    from shadowsip.utils.logger import setup_logging
    from shadowsip.utils.config import AppConfig
    from shadowsip.utils.platform import get_resource_path

    # High DPI support
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

    # Setup logging
    setup_logging()

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("ShadowSIP")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("ShadowPBX")
    app.setOrganizationDomain("shadowpbx.org")

    # Set application icon
    icon_path = get_resource_path("icons", "shadowsip.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Don't quit when last window is closed (we live in system tray)
    app.setQuitOnLastWindowClosed(False)

    # Load config
    config = AppConfig()

    # Apply theme
    theme = config.get("appearance", "theme", fallback="light")

    # Create and show main application
    shadow_app = ShadowSIPApp(config=config)
    shadow_app.apply_theme(theme)
    shadow_app.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

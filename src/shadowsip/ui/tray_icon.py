"""
TrayIcon — System tray integration with context menu.
"""

import logging
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from shadowsip.utils.platform import get_resource_path

logger = logging.getLogger(__name__)


class TrayIcon(QSystemTrayIcon):
    """System tray icon with status and quick actions."""

    def __init__(self, config, app_controller, parent=None):
        super().__init__(parent)
        self.config = config
        self.app_controller = app_controller

        # Set icon
        icon_path = get_resource_path("icons", "shadowsip.png")
        self.setIcon(QIcon(icon_path) if icon_path else QIcon())
        self.setToolTip("ShadowSIP — Offline")

        # Build context menu
        self.menu = QMenu()

        self.show_action = QAction("Show ShadowSIP")
        self.show_action.triggered.connect(app_controller.restore_from_tray)
        self.menu.addAction(self.show_action)

        self.menu.addSeparator()

        # Status submenu
        self.status_menu = self.menu.addMenu("Status")
        for status_name in ["Available", "DND", "Away", "Offline"]:
            action = QAction(status_name, self.status_menu)
            action.triggered.connect(
                lambda checked, s=status_name: self._set_status(s)
            )
            self.status_menu.addAction(action)

        self.menu.addSeparator()

        self.quit_action = QAction("Quit")
        self.quit_action.triggered.connect(app_controller.quit)
        self.menu.addAction(self.quit_action)

        self.setContextMenu(self.menu)

        # Double-click to restore
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.app_controller.restore_from_tray()
        elif reason == QSystemTrayIcon.Trigger:
            self.app_controller.restore_from_tray()

    def _set_status(self, status: str):
        """Set agent status."""
        logger.info(f"Status changed to: {status}")
        self.setToolTip(f"ShadowSIP — {status}")
        # TODO: Phase 4 — Sync with ShadowPBX

    def show_notification(self, title: str, message: str):
        """Show a tray notification balloon."""
        if self.supportsMessages():
            self.showMessage(title, message, QSystemTrayIcon.Information, 3000)

    def update_registration(self, registered: bool, account: str = ""):
        """Update tray tooltip based on registration state."""
        if registered:
            self.setToolTip(f"ShadowSIP — Registered\n{account}")
        else:
            self.setToolTip("ShadowSIP — Offline")

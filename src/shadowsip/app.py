"""
ShadowSIP Application — Main controller with SIP engine, DB, and UI.
"""

import os
import logging

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon, QFontDatabase

from shadowsip.db.database import Database
from shadowsip.core.sip_engine import SipEngine
from shadowsip.core.account_manager import AccountManager
from shadowsip.ui.main_window import MainWindow
from shadowsip.ui.tray_icon import TrayIcon
from shadowsip.utils.config import AppConfig
from shadowsip.utils.platform import get_resource_path

logger = logging.getLogger(__name__)


class ShadowSIPApp:
    """
    Top-level application controller.
    Manages database, SIP engine, account manager, UI, and theming.
    """

    def __init__(self, config: AppConfig):
        self.config = config
        self._current_theme = "light"

        # Load custom fonts
        self._load_fonts()

        # Initialize database
        self.db = Database()

        # Initialize SIP engine
        self.sip_engine = SipEngine()

        # Initialize account manager
        self.account_manager = AccountManager(
            db=self.db, sip_engine=self.sip_engine
        )

        # Wire account manager signals
        self.account_manager.registration_changed.connect(
            self._on_registration_changed
        )
        self.account_manager.error_occurred.connect(
            self._on_error
        )

        # Create main window (pass account_manager for settings)
        self.window = MainWindow(
            config=config,
            app_controller=self,
            account_manager=self.account_manager,
        )

        # Create system tray
        self.tray = TrayIcon(config=config, app_controller=self)

    def _load_fonts(self):
        """Load bundled fonts from resources."""
        fonts_dir = get_resource_path("fonts")
        if os.path.isdir(fonts_dir):
            for font_file in os.listdir(fonts_dir):
                if font_file.endswith((".ttf", ".otf")):
                    font_path = os.path.join(fonts_dir, font_file)
                    font_id = QFontDatabase.addApplicationFont(font_path)
                    if font_id >= 0:
                        families = QFontDatabase.applicationFontFamilies(font_id)
                        logger.debug(f"Loaded font: {families}")

    def show(self):
        """Show the main window and start SIP engine."""
        self.window.show()
        self.tray.show()

        # Start SIP engine + auto-register accounts
        self.account_manager.start()

        # Show mock mode warning if pjsua2 not available
        if not self.sip_engine.is_available:
            self.window.topbar.set_registration_status("mock", "pjsua2 not loaded")
            self.window.statusbar.update_call_info()

        logger.info("ShadowSIP started")

    def hide_to_tray(self):
        """Minimize to system tray."""
        self.window.hide()
        self.tray.show_notification(
            "ShadowSIP",
            "Running in background. Click tray icon to restore."
        )

    def restore_from_tray(self):
        """Restore window from system tray."""
        self.window.show()
        self.window.activateWindow()
        self.window.raise_()

    def apply_theme(self, theme_name: str):
        """Apply a theme to the entire application."""
        self._current_theme = theme_name
        theme_path = get_resource_path("themes", f"{theme_name}.qss")

        stylesheet = ""
        if os.path.exists(theme_path):
            with open(theme_path, "r", encoding="utf-8") as f:
                stylesheet = f.read()
        else:
            logger.warning(f"Theme file not found: {theme_path}")

        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet)

        self.config.set("appearance", "theme", theme_name)
        logger.info(f"Applied theme: {theme_name}")

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        new_theme = "dark" if self._current_theme == "light" else "light"
        self.apply_theme(new_theme)
        return new_theme

    @property
    def current_theme(self) -> str:
        return self._current_theme

    @Slot(int, str)
    def _on_registration_changed(self, account_id: int, state: str):
        """Handle registration state changes from account manager."""
        account = self.account_manager.get_account(account_id)
        if account:
            uri = f"{account['sip_user']}@{account['sip_domain']}"
            self.window.topbar.set_registration_status(state, uri)
            self.tray.update_registration(state == "registered", uri)

            if state == "registered":
                self.window.statusbar.update_call_info(
                    codec="G.711u", transport="UDP · ICE ready",
                    latency_ms=0, quality="good"
                )
            else:
                self.window.statusbar.update_call_info()

    @Slot(str)
    def _on_error(self, message: str):
        """Handle errors from account manager."""
        logger.error(f"Account error: {message}")

    def quit(self):
        """Clean shutdown."""
        logger.info("ShadowSIP shutting down...")
        self.account_manager.stop()
        self.db.close()
        self.tray.hide()
        QApplication.instance().quit()

"""
MainWindow — Primary application window with sidebar navigation.
"""

import logging

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QStackedWidget, QLabel, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon

from shadowsip.ui.icons import get_icon, get_pixmap
from shadowsip.ui.dialer import DialerPage
from shadowsip.utils.platform import get_resource_path

logger = logging.getLogger(__name__)


class SidebarButton(QPushButton):
    """Navigation button for the sidebar with Lucide SVG icons."""

    def __init__(self, icon_name: str, tooltip: str,
                 color: str = "#9E9E9E", active_color: str = "#0D7C5F",
                 parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarButton")
        self.setToolTip(tooltip)
        self.setFixedSize(42, 42)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setIconSize(QSize(20, 20))

        self._icon_name = icon_name
        self._color = color
        self._active_color = active_color
        self.setProperty("iconName", icon_name)

        # Set default icon
        self._update_icon()
        self.toggled.connect(lambda _: self._update_icon())

    def _update_icon(self):
        """Update icon color based on checked state."""
        c = self._active_color if self.isChecked() else self._color
        self.setIcon(get_icon(self._icon_name, color=c, size=20, stroke_width=1.8))

    def set_colors(self, color: str, active_color: str):
        """Update icon colors (for theme switching)."""
        self._color = color
        self._active_color = active_color
        self._update_icon()


class Sidebar(QWidget):
    """Left sidebar with navigation buttons."""

    page_changed = Signal(int)
    theme_toggle_requested = Signal()

    NAV_ITEMS = [
        ("dialpad", "Dialer"),
        ("contacts", "Contacts"),
        ("chat", "Chat"),
        ("history", "History"),
        ("video", "Video"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(64)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignHCenter)

        # Logo
        self.logo_btn = QPushButton()
        self.logo_btn.setObjectName("logoButton")
        self.logo_btn.setFixedSize(40, 40)
        self.logo_btn.setCursor(Qt.PointingHandCursor)
        self.logo_btn.setIcon(get_icon("phone", color="#FFFFFF", size=20, stroke_width=2.5))
        self.logo_btn.setIconSize(QSize(20, 20))
        layout.addWidget(self.logo_btn, alignment=Qt.AlignHCenter)
        layout.addSpacing(16)

        # Navigation buttons
        self.nav_buttons: list[SidebarButton] = []
        for i, (icon_name, tooltip) in enumerate(self.NAV_ITEMS):
            btn = SidebarButton(icon_name, tooltip)
            btn.clicked.connect(lambda checked, idx=i: self._on_nav_click(idx))
            layout.addWidget(btn, alignment=Qt.AlignHCenter)
            self.nav_buttons.append(btn)

        # Spacer
        layout.addStretch()

        # Theme toggle
        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("themeToggleButton")
        self.theme_btn.setFixedSize(42, 28)
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.setToolTip("Toggle theme")
        self.theme_btn.setIcon(get_icon("sun", color="#C48A1A", size=16, stroke_width=2))
        self.theme_btn.setIconSize(QSize(16, 16))
        self.theme_btn.clicked.connect(self._on_theme_toggle)
        layout.addWidget(self.theme_btn, alignment=Qt.AlignHCenter)
        layout.addSpacing(8)

        # Settings
        self.settings_btn = SidebarButton("settings", "Settings")
        layout.addWidget(self.settings_btn, alignment=Qt.AlignHCenter)
        layout.addSpacing(8)

        # User avatar
        self.avatar_btn = QPushButton("DK")
        self.avatar_btn.setObjectName("avatarButton")
        self.avatar_btn.setFixedSize(34, 34)
        self.avatar_btn.setCursor(Qt.PointingHandCursor)
        self.avatar_btn.setToolTip("Account")
        layout.addWidget(self.avatar_btn, alignment=Qt.AlignHCenter)

        # Set first button active
        if self.nav_buttons:
            self.nav_buttons[0].setChecked(True)

    def _on_nav_click(self, index: int):
        """Handle navigation button click."""
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.page_changed.emit(index)

    def _on_theme_toggle(self):
        """Handle theme toggle and update button icon."""
        self.theme_toggle_requested.emit()
        # Swap icon based on which theme we just switched TO
        # After toggle, check the app controller's current theme
        # For now, just alternate the icon
        current_icon = self.theme_btn.toolTip()
        if "light" not in str(self.theme_btn.property("currentIcon") or "sun"):
            self.theme_btn.setIcon(
                get_icon("sun", color="#C48A1A", size=16, stroke_width=2))
            self.theme_btn.setProperty("currentIcon", "sun")
        else:
            self.theme_btn.setIcon(
                get_icon("moon", color="#60A5FA", size=16, stroke_width=2))
            self.theme_btn.setProperty("currentIcon", "moon")

    def set_active(self, index: int):
        """Programmatically set active navigation page."""
        if 0 <= index < len(self.nav_buttons):
            self._on_nav_click(index)


class TopBar(QWidget):
    """Top bar with app name, registration status, and account info."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topBar")
        self.setFixedHeight(52)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        # Left: App name + status
        left = QHBoxLayout()
        left.setSpacing(10)

        self.app_name = QLabel("ShadowSIP")
        self.app_name.setObjectName("appName")

        self.status_badge = QLabel("offline")
        self.status_badge.setObjectName("statusBadge")
        self.status_badge.setProperty("status", "offline")

        left.addWidget(self.app_name)
        left.addWidget(self.status_badge)
        left.addStretch()
        layout.addLayout(left)

        # Right: Account info + indicator
        right = QHBoxLayout()
        right.setSpacing(8)

        self.account_label = QLabel("No account configured")
        self.account_label.setObjectName("accountLabel")

        self.online_dot = QLabel()
        self.online_dot.setObjectName("onlineDot")
        self.online_dot.setFixedSize(8, 8)
        self.online_dot.setProperty("state", "offline")

        right.addStretch()
        right.addWidget(self.account_label)
        right.addWidget(self.online_dot)
        layout.addLayout(right)

    def set_registration_status(self, status: str, account_uri: str = ""):
        """
        Update registration status display.

        Args:
            status: 'registered', 'trying', 'offline', 'error'
            account_uri: SIP account URI to display
        """
        self.status_badge.setText(status)
        self.status_badge.setProperty("status", status)
        # Force style refresh
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

        if account_uri:
            self.account_label.setText(account_uri)

        dot_state = "online" if status == "registered" else "offline"
        self.online_dot.setProperty("state", dot_state)
        self.online_dot.style().unpolish(self.online_dot)
        self.online_dot.style().polish(self.online_dot)


class StatusBar(QWidget):
    """Bottom status bar showing codec, transport, and network info."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusBar")
        self.setFixedHeight(32)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)

        self.codec_label = QLabel("No active call")
        self.codec_label.setObjectName("statusText")

        self.latency_label = QLabel("")
        self.latency_label.setObjectName("statusText")

        self.quality_dot = QLabel()
        self.quality_dot.setObjectName("qualityDot")
        self.quality_dot.setFixedSize(6, 6)

        layout.addWidget(self.codec_label)
        layout.addStretch()
        layout.addWidget(self.latency_label)
        layout.addWidget(self.quality_dot)

    def update_call_info(self, codec: str = "", transport: str = "",
                         latency_ms: int = 0, quality: str = "good"):
        """Update status bar with call information."""
        if codec:
            self.codec_label.setText(f"{codec} · {transport}")
            self.latency_label.setText(f"{latency_ms}ms")
        else:
            self.codec_label.setText("No active call")
            self.latency_label.setText("")

        self.quality_dot.setProperty("quality", quality)
        self.quality_dot.style().unpolish(self.quality_dot)
        self.quality_dot.style().polish(self.quality_dot)


class MainWindow(QMainWindow):
    """
    Primary application window.
    Layout: [Sidebar | TopBar + Content + StatusBar]
    """

    def __init__(self, config, app_controller, account_manager=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.app_controller = app_controller
        self.account_manager = account_manager

        self.setWindowTitle("ShadowSIP")
        self.setMinimumSize(880, 560)
        self.resize(920, 620)
        self.setObjectName("mainWindow")

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Root layout: sidebar + main area
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._on_page_changed)
        self.sidebar.theme_toggle_requested.connect(self._on_theme_toggle)
        self.sidebar.settings_btn.clicked.connect(self._open_settings)
        root_layout.addWidget(self.sidebar)

        # Main area (topbar + content + statusbar)
        main_area = QVBoxLayout()
        main_area.setContentsMargins(0, 0, 0, 0)
        main_area.setSpacing(0)

        # Top bar
        self.topbar = TopBar()
        main_area.addWidget(self.topbar)

        # Separator line
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        main_area.addWidget(sep)

        # Content stack
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentStack")

        # Add pages
        self.dialer_page = DialerPage(config=config)
        self.content_stack.addWidget(self.dialer_page)

        # Placeholder pages for Phase 2+
        for name in ["Contacts", "Chat", "History", "Video"]:
            placeholder = QLabel(f"{name}\n\nComing soon in Phase 2+")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setObjectName("placeholderPage")
            self.content_stack.addWidget(placeholder)

        main_area.addWidget(self.content_stack, stretch=1)

        # Status bar
        self.statusbar = StatusBar()
        self.statusbar.update_call_info(
            codec="G.711u", transport="UDP · ICE ready",
            latency_ms=42, quality="good"
        )
        main_area.addWidget(self.statusbar)

        root_layout.addLayout(main_area)

        # Restore window geometry
        self._restore_geometry()

    def _on_page_changed(self, index: int):
        """Switch content page."""
        if 0 <= index < self.content_stack.count():
            self.content_stack.setCurrentIndex(index)

    def _on_theme_toggle(self):
        """Toggle between light and dark theme."""
        new_theme = self.app_controller.toggle_theme()
        logger.info(f"Theme switched to: {new_theme}")

    def _open_settings(self):
        """Open the settings dialog."""
        from shadowsip.ui.settings_dialog import SettingsDialog

        dialog = SettingsDialog(
            account_manager=self.account_manager,
            config=self.config,
            parent=self,
        )
        dialog.exec()

    def _restore_geometry(self):
        """Restore saved window size and position."""
        geometry = self.config.get("window", "geometry", fallback="")
        if geometry:
            try:
                parts = geometry.split(",")
                if len(parts) == 4:
                    x, y, w, h = [int(p) for p in parts]
                    self.setGeometry(x, y, w, h)
            except (ValueError, IndexError):
                pass

    def closeEvent(self, event):
        """Override close to minimize to tray instead of quitting."""
        # Save geometry
        geo = self.geometry()
        self.config.set(
            "window", "geometry",
            f"{geo.x()},{geo.y()},{geo.width()},{geo.height()}"
        )

        # Minimize to tray
        self.app_controller.hide_to_tray()
        event.ignore()

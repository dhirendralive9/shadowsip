"""
DialerPage — Dial pad, number input, BLF extensions, and recent calls.
"""

import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QLabel, QLineEdit, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont

from shadowsip.ui.icons import get_icon, get_pixmap

logger = logging.getLogger(__name__)


class DialpadButton(QPushButton):
    """Single dialpad key (0-9, *, #)."""

    digit_pressed = Signal(str)

    def __init__(self, digit: str, sub_text: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("dialpadKey")
        self.digit = digit
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(56)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.clicked.connect(lambda: self.digit_pressed.emit(self.digit))

        # Layout with digit + sub label
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        digit_label = QLabel(digit)
        digit_label.setObjectName("keyDigit")
        digit_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(digit_label)

        if sub_text and sub_text.strip():
            sub_label = QLabel(sub_text)
            sub_label.setObjectName("keySub")
            sub_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(sub_label)


class NumberInput(QWidget):
    """Number input field with search icon and clear button."""

    text_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("numberInput")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)

        # Search icon
        self.search_icon = QLabel()
        self.search_icon.setObjectName("searchIcon")
        self.search_icon.setFixedSize(16, 16)
        self.search_icon.setPixmap(get_pixmap("search", color="#9E9E9E", size=16, stroke_width=2))
        layout.addWidget(self.search_icon)

        # Input field
        self.input = QLineEdit()
        self.input.setObjectName("numberField")
        self.input.setPlaceholderText("Enter number or search...")
        self.input.setFrame(False)
        self.input.textChanged.connect(self.text_changed.emit)
        layout.addWidget(self.input, stretch=1)

        # Clear button
        self.clear_btn = QPushButton("×")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.setFixedSize(24, 24)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self._clear)
        self.clear_btn.hide()
        layout.addWidget(self.clear_btn)

        self.input.textChanged.connect(
            lambda t: self.clear_btn.setVisible(len(t) > 0)
        )

    def _clear(self):
        self.input.clear()

    def append_digit(self, digit: str):
        """Append a digit to the input field."""
        self.input.setText(self.input.text() + digit)

    def backspace(self):
        """Remove last character."""
        text = self.input.text()
        if text:
            self.input.setText(text[:-1])

    @property
    def number(self) -> str:
        return self.input.text().strip()


class ExtensionCard(QWidget):
    """BLF extension card showing status and name."""

    clicked = Signal(str)

    def __init__(self, extension: str, name: str, status: str = "offline", parent=None):
        super().__init__(parent)
        self.setObjectName("extensionCard")
        self.setCursor(Qt.PointingHandCursor)
        self._extension = extension

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # Status dot
        self.dot = QLabel()
        self.dot.setObjectName("extDot")
        self.dot.setFixedSize(8, 8)
        self.dot.setProperty("state", status)
        layout.addWidget(self.dot)

        # Info
        info = QVBoxLayout()
        info.setSpacing(0)

        self.ext_label = QLabel(extension)
        self.ext_label.setObjectName("extNumber")

        self.name_label = QLabel(name)
        self.name_label.setObjectName("extName")

        info.addWidget(self.ext_label)
        info.addWidget(self.name_label)
        layout.addLayout(info)
        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._extension)
        super().mousePressEvent(event)

    def set_status(self, status: str):
        """Update extension status: 'online', 'busy', 'offline'."""
        self.dot.setProperty("state", status)
        self.dot.style().unpolish(self.dot)
        self.dot.style().polish(self.dot)


class CallHistoryEntry(QWidget):
    """Single call history entry."""

    call_clicked = Signal(str)

    def __init__(self, number: str, direction: str, duration: str,
                 time_ago: str, parent=None):
        super().__init__(parent)
        self.setObjectName("callEntry")
        self.setCursor(Qt.PointingHandCursor)
        self._number = number

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Direction arrow — SVG icon
        arrow_colors = {
            "outbound": "#0D7C5F",
            "inbound": "#2563EB",
            "missed": "#D94040",
        }
        arrow_icons = {
            "outbound": "arrow-up-right",
            "inbound": "arrow-down-left",
            "missed": "arrow-down-left",
        }
        arrow_color = arrow_colors.get(direction, "#9E9E9E")
        arrow_icon = arrow_icons.get(direction, "arrow-down-left")

        self.arrow = QLabel()
        self.arrow.setObjectName("callArrow")
        self.arrow.setFixedSize(18, 18)
        self.arrow.setAlignment(Qt.AlignCenter)
        self.arrow.setPixmap(get_pixmap(arrow_icon, color=arrow_color, size=18, stroke_width=2.5))
        self.arrow.setProperty("direction", direction)
        layout.addWidget(self.arrow)

        # Call info
        info = QVBoxLayout()
        info.setSpacing(0)
        self.number_label = QLabel(number)
        self.number_label.setObjectName("callNumber")
        self.meta_label = QLabel(f"{direction.capitalize()} · {duration}")
        self.meta_label.setObjectName("callMeta")
        info.addWidget(self.number_label)
        info.addWidget(self.meta_label)
        layout.addLayout(info, stretch=1)

        # Time
        self.time_label = QLabel(time_ago)
        self.time_label.setObjectName("callTime")
        layout.addWidget(self.time_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.call_clicked.emit(self._number)
        super().mousePressEvent(event)


class QuickActionButton(QWidget):
    """Quick action button (mic, speaker, DND, rec, auto)."""

    action_triggered = Signal(str)

    ICON_MAP = {
        "mic": "mic",
        "vol": "volume-2",
        "dnd": "ban",
        "rec": "disc",
        "auto": "zap",
    }

    # Colors: (normal_light, normal_dark, active_light, active_dark)
    COLOR_MAP = {
        "mic":  ("#555555", "#AAAAAA", "#0D7C5F", "#2DD4BF"),
        "vol":  ("#555555", "#AAAAAA", "#0D7C5F", "#2DD4BF"),
        "dnd":  ("#D94040", "#F87171", "#FFFFFF", "#FFFFFF"),
        "rec":  ("#555555", "#AAAAAA", "#D94040", "#F87171"),
        "auto": ("#555555", "#AAAAAA", "#C48A1A", "#FBBF24"),
    }

    def __init__(self, action_id: str, label: str, theme: str = "light", parent=None):
        super().__init__(parent)
        self._action_id = action_id
        self._theme = theme

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignHCenter)

        self.btn = QPushButton()
        self.btn.setObjectName("quickActionCircle")
        self.btn.setFixedSize(38, 38)
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setProperty("actionId", action_id)
        self.btn.setCheckable(True)
        self.btn.setIconSize(QSize(16, 16))
        self.btn.clicked.connect(self._on_click)
        layout.addWidget(self.btn, alignment=Qt.AlignHCenter)

        self.label = QLabel(label)
        self.label.setObjectName("quickActionLabel")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label, alignment=Qt.AlignHCenter)

        self._update_icon()
        self.btn.toggled.connect(lambda _: self._update_icon())

    def _on_click(self):
        self.action_triggered.emit(self._action_id)

    def _update_icon(self):
        """Update icon based on checked state and theme."""
        icon_name = self.ICON_MAP.get(self._action_id, "disc")
        colors = self.COLOR_MAP.get(self._action_id, ("#555555", "#AAAAAA", "#0D7C5F", "#2DD4BF"))

        if self.btn.isChecked():
            color = colors[2] if self._theme == "light" else colors[3]
        else:
            color = colors[0] if self._theme == "light" else colors[1]

        self.btn.setIcon(get_icon(icon_name, color=color, size=16, stroke_width=1.8))

    def set_theme(self, theme: str):
        """Update theme and refresh icon."""
        self._theme = theme
        self._update_icon()


class DialerPage(QWidget):
    """
    Complete dialer page with:
    - Left: Number input + dial pad + call button + quick actions
    - Right: BLF extensions + recent calls + status bar
    """

    call_requested = Signal(str)

    # Dialpad layout
    KEYS = [
        ("1", ""),    ("2", "ABC"),  ("3", "DEF"),
        ("4", "GHI"), ("5", "JKL"),  ("6", "MNO"),
        ("7", "PQRS"),("8", "TUV"),  ("9", "WXYZ"),
        ("*", ""),    ("0", "+"),    ("#", ""),
    ]

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.setObjectName("dialerPage")

        # Main horizontal split: dialer | right panel
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === Left: Dialer ===
        dialer_widget = QWidget()
        dialer_widget.setObjectName("dialerPanel")
        dialer_widget.setFixedWidth(290)
        dialer_layout = QVBoxLayout(dialer_widget)
        dialer_layout.setContentsMargins(22, 22, 22, 22)
        dialer_layout.setSpacing(0)

        # Number input
        self.number_input = NumberInput()
        dialer_layout.addWidget(self.number_input)
        dialer_layout.addSpacing(16)

        # Dial pad grid
        pad_grid = QGridLayout()
        pad_grid.setSpacing(7)
        self._dialpad_buttons = []

        for i, (digit, sub) in enumerate(self.KEYS):
            btn = DialpadButton(digit, sub)
            btn.digit_pressed.connect(self.number_input.append_digit)
            row, col = divmod(i, 3)
            pad_grid.addWidget(btn, row, col)
            self._dialpad_buttons.append(btn)

        dialer_layout.addLayout(pad_grid)
        dialer_layout.addSpacing(16)

        # Call button
        self.call_btn = QPushButton("  Call")
        self.call_btn.setObjectName("callButton")
        self.call_btn.setFixedHeight(48)
        self.call_btn.setCursor(Qt.PointingHandCursor)
        self.call_btn.setIcon(get_icon("phone", color="#FFFFFF", size=18, stroke_width=2.5))
        self.call_btn.setIconSize(QSize(18, 18))
        self.call_btn.clicked.connect(self._on_call)
        dialer_layout.addWidget(self.call_btn)
        dialer_layout.addSpacing(12)

        # Quick actions row
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)
        actions_layout.setAlignment(Qt.AlignCenter)

        self._quick_actions = []
        for action_id, label in [("mic", "Mic"), ("vol", "Vol"), ("dnd", "DND"), ("rec", "Rec"), ("auto", "Auto")]:
            qa = QuickActionButton(action_id, label)
            qa.action_triggered.connect(self._on_quick_action)
            actions_layout.addWidget(qa)
            self._quick_actions.append(qa)

        dialer_layout.addLayout(actions_layout)
        dialer_layout.addStretch()

        layout.addWidget(dialer_widget)

        # Vertical separator
        sep = QFrame()
        sep.setObjectName("verticalSep")
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        layout.addWidget(sep)

        # === Right: Extensions + Recent Calls ===
        right_widget = QWidget()
        right_widget.setObjectName("rightPanel")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(22, 22, 22, 22)
        right_layout.setSpacing(16)

        # Extensions section
        ext_title = QLabel("EXTENSIONS")
        ext_title.setObjectName("sectionTitle")
        right_layout.addWidget(ext_title)

        self.ext_grid = QGridLayout()
        self.ext_grid.setSpacing(7)

        # Empty — populated from SIP presence when extensions register
        self._ext_cards = []

        # Placeholder when no extensions
        self.ext_placeholder = QLabel("No extensions online")
        self.ext_placeholder.setObjectName("callMeta")
        self.ext_placeholder.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.ext_placeholder)

        right_layout.addLayout(self.ext_grid)

        # Recent calls section
        calls_title = QLabel("RECENT CALLS")
        calls_title.setObjectName("sectionTitle")
        right_layout.addWidget(calls_title)

        # Scrollable call list
        self.call_list_widget = QWidget()
        self.call_list_layout = QVBoxLayout(self.call_list_widget)
        self.call_list_layout.setContentsMargins(0, 0, 0, 0)
        self.call_list_layout.setSpacing(2)

        # Empty — populated from SQLite call history
        self.calls_placeholder = QLabel("No recent calls")
        self.calls_placeholder.setObjectName("callMeta")
        self.calls_placeholder.setAlignment(Qt.AlignCenter)
        self.call_list_layout.addWidget(self.calls_placeholder)

        self.call_list_layout.addStretch()

        scroll = QScrollArea()
        scroll.setObjectName("callListScroll")
        scroll.setWidget(self.call_list_widget)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        right_layout.addWidget(scroll, stretch=1)

        layout.addWidget(right_widget, stretch=1)

    def _on_call(self):
        """Handle call button press."""
        number = self.number_input.number
        if number:
            logger.info(f"Call requested: {number}")
            self.call_requested.emit(number)
        else:
            logger.debug("Call pressed with empty number")

    def _on_quick_action(self, action_id: str):
        """Handle quick action button."""
        logger.info(f"Quick action: {action_id}")
        # TODO: Implement in Phase 1.3

    def _on_ext_clicked(self, extension: str):
        """Handle extension card click — populate dialer."""
        self.number_input.input.setText(extension)
        logger.info(f"Extension clicked: {extension}")

    def _on_history_call(self, number: str):
        """Handle call history entry click — populate dialer."""
        self.number_input.input.setText(number)
        logger.info(f"History call clicked: {number}")

    def add_extension(self, extension: str, name: str, status: str = "offline"):
        """Add an extension card to the BLF grid."""
        card = ExtensionCard(extension, name, status)
        card.clicked.connect(self._on_ext_clicked)
        col = len(self._ext_cards) % 3
        row = len(self._ext_cards) // 3
        self.ext_grid.addWidget(card, row, col)
        self._ext_cards.append(card)

    def add_call_history(self, number: str, direction: str,
                         duration: str, time_ago: str):
        """Add an entry to the call history list."""
        entry = CallHistoryEntry(number, direction, duration, time_ago)
        entry.call_clicked.connect(self._on_history_call)
        # Insert at top
        self.call_list_layout.insertWidget(0, entry)

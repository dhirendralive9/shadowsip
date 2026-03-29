"""
Settings Dialog — Account management, audio settings, and preferences.
"""

import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QSpinBox, QListWidget, QListWidgetItem, QGroupBox,
    QFormLayout, QMessageBox, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize

from shadowsip.ui.icons import get_icon

logger = logging.getLogger(__name__)


class AccountForm(QWidget):
    """Form for adding/editing a SIP account."""

    saved = Signal(dict)       # Emits account data dict
    cancelled = Signal()
    deleted = Signal(int)      # Emits account_id

    def __init__(self, account_data: dict = None, parent=None):
        super().__init__(parent)
        self._account_id = account_data.get("id") if account_data else None
        self._editing = account_data is not None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Title
        title = QLabel("Edit Account" if self._editing else "Add Account")
        title.setObjectName("formTitle")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        # Form
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.display_name = QLineEdit()
        self.display_name.setPlaceholderText("My SIP Account")
        form.addRow("Display Name:", self.display_name)

        self.sip_user = QLineEdit()
        self.sip_user.setPlaceholderText("2001")
        form.addRow("SIP Username:", self.sip_user)

        self.sip_domain = QLineEdit()
        self.sip_domain.setPlaceholderText("pbx.webtobuzz.com")
        form.addRow("SIP Domain:", self.sip_domain)

        self.sip_password = QLineEdit()
        self.sip_password.setEchoMode(QLineEdit.Password)
        self.sip_password.setPlaceholderText("••••••••")
        form.addRow("Password:", self.sip_password)

        self.auth_user = QLineEdit()
        self.auth_user.setPlaceholderText("(same as username if blank)")
        form.addRow("Auth Username:", self.auth_user)

        self.transport = QComboBox()
        self.transport.addItems(["UDP", "TCP", "TLS"])
        form.addRow("Transport:", self.transport)

        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(5060)
        form.addRow("Port:", self.port)

        self.outbound_proxy = QLineEdit()
        self.outbound_proxy.setPlaceholderText("(optional)")
        form.addRow("Outbound Proxy:", self.outbound_proxy)

        layout.addLayout(form)

        # NAT section
        nat_group = QGroupBox("NAT Traversal")
        nat_layout = QFormLayout(nat_group)

        self.stun_server = QLineEdit()
        self.stun_server.setText("stun.l.google.com:19302")
        nat_layout.addRow("STUN Server:", self.stun_server)

        self.ice_enabled = QCheckBox("Enable ICE")
        self.ice_enabled.setChecked(True)
        nat_layout.addRow("", self.ice_enabled)

        self.srtp_enabled = QCheckBox("Enable SRTP (encryption)")
        nat_layout.addRow("", self.srtp_enabled)

        layout.addWidget(nat_group)

        # Options
        options_layout = QHBoxLayout()
        self.register_startup = QCheckBox("Register on startup")
        self.register_startup.setChecked(True)
        options_layout.addWidget(self.register_startup)

        self.is_default = QCheckBox("Default account")
        options_layout.addWidget(self.is_default)
        options_layout.addStretch()
        layout.addLayout(options_layout)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        if self._editing:
            self.delete_btn = QPushButton("Delete Account")
            self.delete_btn.setObjectName("dangerButton")
            self.delete_btn.setStyleSheet(
                "QPushButton { color: #D94040; border: 1px solid rgba(217,64,64,0.3); "
                "border-radius: 8px; padding: 8px 16px; } "
                "QPushButton:hover { background: rgba(217,64,64,0.1); }")
            self.delete_btn.clicked.connect(self._on_delete)
            btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(
            "QPushButton { border: 1px solid rgba(0,0,0,0.1); "
            "border-radius: 8px; padding: 8px 20px; } "
            "QPushButton:hover { background: rgba(0,0,0,0.05); }")
        self.cancel_btn.clicked.connect(self.cancelled.emit)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save & Register" if not self._editing else "Save")
        self.save_btn.setStyleSheet(
            "QPushButton { background: #0D7C5F; color: white; border: none; "
            "border-radius: 8px; padding: 8px 24px; font-weight: 600; } "
            "QPushButton:hover { background: #0A6B51; }")
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

        # Populate if editing
        if account_data:
            self._populate(account_data)

    def _populate(self, data: dict):
        """Fill form from account data."""
        self.display_name.setText(data.get("display_name", ""))
        self.sip_user.setText(data.get("sip_user", ""))
        self.sip_domain.setText(data.get("sip_domain", ""))
        self.sip_password.setText(data.get("sip_password", ""))
        self.auth_user.setText(data.get("auth_user", ""))
        self.outbound_proxy.setText(data.get("outbound_proxy", ""))
        self.stun_server.setText(data.get("stun_server", "stun.l.google.com:19302"))
        self.port.setValue(data.get("port", 5060))
        self.ice_enabled.setChecked(bool(data.get("ice_enabled", 1)))
        self.srtp_enabled.setChecked(bool(data.get("srtp_enabled", 0)))
        self.register_startup.setChecked(bool(data.get("register_on_startup", 1)))
        self.is_default.setChecked(bool(data.get("is_default", 0)))

        transport = data.get("transport", "UDP").upper()
        idx = self.transport.findText(transport)
        if idx >= 0:
            self.transport.setCurrentIndex(idx)

    def _on_save(self):
        """Validate and emit save signal."""
        user = self.sip_user.text().strip()
        domain = self.sip_domain.text().strip()

        if not user:
            QMessageBox.warning(self, "Validation", "SIP Username is required.")
            self.sip_user.setFocus()
            return
        if not domain:
            QMessageBox.warning(self, "Validation", "SIP Domain is required.")
            self.sip_domain.setFocus()
            return

        data = {
            "display_name": self.display_name.text().strip(),
            "sip_user": user,
            "sip_domain": domain,
            "sip_password": self.sip_password.text(),
            "auth_user": self.auth_user.text().strip(),
            "transport": self.transport.currentText(),
            "port": self.port.value(),
            "outbound_proxy": self.outbound_proxy.text().strip(),
            "stun_server": self.stun_server.text().strip(),
            "ice_enabled": self.ice_enabled.isChecked(),
            "srtp_enabled": self.srtp_enabled.isChecked(),
            "register_on_startup": self.register_startup.isChecked(),
            "is_default": self.is_default.isChecked(),
        }

        if self._account_id is not None:
            data["id"] = self._account_id

        self.saved.emit(data)

    def _on_delete(self):
        """Confirm and emit delete signal."""
        reply = QMessageBox.question(
            self, "Delete Account",
            f"Delete account {self.sip_user.text()}@{self.sip_domain.text()}?\n\n"
            "This will unregister and remove the account.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes and self._account_id is not None:
            self.deleted.emit(self._account_id)


class SettingsDialog(QDialog):
    """Settings dialog with tabs for Accounts, Audio, and General."""

    account_action = Signal(str, dict)  # action ("add"/"update"/"delete"), data

    def __init__(self, account_manager, config, parent=None):
        super().__init__(parent)
        self._account_manager = account_manager
        self._config = config

        self.setWindowTitle("ShadowSIP Settings")
        self.setMinimumSize(560, 480)
        self.resize(600, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Accounts tab
        self.accounts_tab = self._build_accounts_tab()
        self.tabs.addTab(self.accounts_tab, "Accounts")

        # Audio tab (placeholder for Phase 1.3)
        audio_tab = QLabel("Audio device settings will be available\nwhen PJSIP is connected.")
        audio_tab.setAlignment(Qt.AlignCenter)
        self.tabs.addTab(audio_tab, "Audio")

        # General tab
        general_tab = QLabel("General preferences coming soon.")
        general_tab.setAlignment(Qt.AlignCenter)
        self.tabs.addTab(general_tab, "General")

        layout.addWidget(self.tabs)

    def _build_accounts_tab(self) -> QWidget:
        """Build the accounts management tab."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left: Account list
        left = QVBoxLayout()
        left.setSpacing(8)

        list_header = QHBoxLayout()
        list_label = QLabel("SIP Accounts")
        list_label.setStyleSheet("font-weight: 600; font-size: 14px;")
        list_header.addWidget(list_label)
        list_header.addStretch()

        self.add_btn = QPushButton("+ Add")
        self.add_btn.setStyleSheet(
            "QPushButton { background: #0D7C5F; color: white; border: none; "
            "border-radius: 6px; padding: 6px 14px; font-weight: 600; font-size: 12px; } "
            "QPushButton:hover { background: #0A6B51; }")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self._show_add_form)
        list_header.addWidget(self.add_btn)
        left.addLayout(list_header)

        self.account_list = QListWidget()
        self.account_list.setFixedWidth(200)
        self.account_list.currentRowChanged.connect(self._on_account_selected)
        left.addWidget(self.account_list)
        layout.addLayout(left)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        layout.addWidget(sep)

        # Right: Form area (stacked)
        self.form_area = QVBoxLayout()
        self._current_form = None

        # Placeholder
        self._placeholder = QLabel("Select an account or add a new one.")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet("color: #9E9E9E; font-size: 14px;")
        self.form_area.addWidget(self._placeholder)

        layout.addLayout(self.form_area, stretch=1)

        # Load accounts
        self._refresh_account_list()

        return widget

    def _refresh_account_list(self):
        """Reload account list from database."""
        self.account_list.clear()
        accounts = self._account_manager.get_all_accounts()

        for acc in accounts:
            state = self._account_manager.get_reg_state(acc["id"])
            status_icon = "● " if state == "registered" else "○ "
            label = f"{status_icon}{acc['sip_user']}@{acc['sip_domain']}"
            if acc.get("is_default"):
                label += " ★"

            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, acc["id"])
            self.account_list.addItem(item)

    def _on_account_selected(self, row: int):
        """Show edit form for selected account."""
        item = self.account_list.item(row)
        if not item:
            return
        account_id = item.data(Qt.UserRole)
        account_data = self._account_manager.get_account(account_id)
        if account_data:
            self._show_edit_form(account_data)

    def _show_add_form(self):
        """Show blank form for adding a new account."""
        self._clear_form_area()
        form = AccountForm()
        form.saved.connect(self._on_account_saved)
        form.cancelled.connect(self._show_placeholder)
        self.form_area.addWidget(form)
        self._current_form = form

    def _show_edit_form(self, account_data: dict):
        """Show form for editing an existing account."""
        self._clear_form_area()
        form = AccountForm(account_data=account_data)
        form.saved.connect(self._on_account_saved)
        form.cancelled.connect(self._show_placeholder)
        form.deleted.connect(self._on_account_deleted)
        self.form_area.addWidget(form)
        self._current_form = form

    def _show_placeholder(self):
        """Show placeholder text in form area."""
        self._clear_form_area()
        self.form_area.addWidget(self._placeholder)
        self._placeholder.show()

    def _clear_form_area(self):
        """Remove current form from layout."""
        if self._current_form:
            self._current_form.setParent(None)
            self._current_form.deleteLater()
            self._current_form = None
        self._placeholder.hide()

    def _on_account_saved(self, data: dict):
        """Handle account save from form."""
        account_id = data.pop("id", None)

        if account_id is not None:
            # Update existing
            self._account_manager.update_account(account_id, **data)
            logger.info(f"Account updated: {data['sip_user']}@{data['sip_domain']}")
        else:
            # Add new
            account_id = self._account_manager.add_account(**data)
            logger.info(f"Account added: {data['sip_user']}@{data['sip_domain']}")

        self._refresh_account_list()
        self._show_placeholder()

    def _on_account_deleted(self, account_id: int):
        """Handle account deletion."""
        self._account_manager.delete_account(account_id)
        self._refresh_account_list()
        self._show_placeholder()

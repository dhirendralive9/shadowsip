"""
Settings Dialog — Clean native Qt form, explicitly clears inherited QSS.
"""
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QSpinBox, QListWidget, QListWidgetItem,
    QFormLayout, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette, QColor

logger = logging.getLogger(__name__)


class AccountForm(QWidget):
    saved = Signal(dict)
    cancelled = Signal()
    deleted = Signal(int)

    def __init__(self, account_data=None, parent=None):
        super().__init__(parent)
        # CRITICAL: Clear any inherited stylesheet so native sizing works
        self.setStyleSheet("")

        self._account_id = account_data.get("id") if account_data else None
        self._editing = account_data is not None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)

        title = QLabel("Edit Account" if self._editing else "Add Account")
        f = title.font()
        f.setPointSize(13)
        f.setBold(True)
        title.setFont(f)
        layout.addWidget(title)
        layout.addSpacing(6)

        # Use QFormLayout — the standard Qt way
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.DontWrapRows)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form.setVerticalSpacing(6)
        form.setHorizontalSpacing(12)

        self.display_name = QLineEdit()
        self.display_name.setPlaceholderText("My SIP Account")
        form.addRow("Display Name:", self.display_name)

        self.sip_user = QLineEdit()
        self.sip_user.setPlaceholderText("2001")
        form.addRow("Username:", self.sip_user)

        self.sip_domain = QLineEdit()
        self.sip_domain.setPlaceholderText("pbx.webtobuzz.com")
        form.addRow("Server:", self.sip_domain)

        # Password with eye button
        pw_w = QWidget()
        pw_w.setStyleSheet("")
        pw_l = QHBoxLayout(pw_w)
        pw_l.setContentsMargins(0, 0, 0, 0)
        pw_l.setSpacing(2)
        self.sip_password = QLineEdit()
        self.sip_password.setEchoMode(QLineEdit.Password)
        self.sip_password.setPlaceholderText("Enter password")
        pw_l.addWidget(self.sip_password)
        self.eye_btn = QPushButton("Show")
        self.eye_btn.setFixedWidth(50)
        self.eye_btn.clicked.connect(self._toggle_pw)
        pw_l.addWidget(self.eye_btn)
        form.addRow("Password:", pw_w)

        self.auth_user = QLineEdit()
        self.auth_user.setPlaceholderText("(same as username)")
        form.addRow("Auth User:", self.auth_user)

        self.transport = QComboBox()
        self.transport.addItems(["UDP", "TCP", "TLS"])
        form.addRow("Transport:", self.transport)

        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(5060)
        form.addRow("Port:", self.port)

        self.outbound_proxy = QLineEdit()
        self.outbound_proxy.setPlaceholderText("(optional)")
        form.addRow("Proxy:", self.outbound_proxy)

        self.stun_server = QLineEdit()
        self.stun_server.setText("stun.l.google.com:19302")
        form.addRow("STUN:", self.stun_server)

        layout.addLayout(form)
        layout.addSpacing(4)

        # Checkboxes
        cb = QHBoxLayout()
        self.ice_enabled = QCheckBox("ICE")
        self.ice_enabled.setChecked(True)
        cb.addWidget(self.ice_enabled)
        self.srtp_enabled = QCheckBox("SRTP")
        cb.addWidget(self.srtp_enabled)
        self.register_startup = QCheckBox("Auto-register")
        self.register_startup.setChecked(True)
        cb.addWidget(self.register_startup)
        self.is_default = QCheckBox("Default")
        cb.addWidget(self.is_default)
        cb.addStretch()
        layout.addLayout(cb)

        layout.addStretch()

        # Buttons
        btns = QHBoxLayout()
        if self._editing:
            d = QPushButton("Delete")
            d.clicked.connect(self._on_delete)
            btns.addWidget(d)
        btns.addStretch()
        c = QPushButton("Cancel")
        c.clicked.connect(self.cancelled.emit)
        btns.addWidget(c)
        s = QPushButton("Save & Register" if not self._editing else "Save")
        s.setDefault(True)
        s.clicked.connect(self._on_save)
        btns.addWidget(s)
        layout.addLayout(btns)

        if account_data:
            self._populate(account_data)

    def _toggle_pw(self):
        if self.sip_password.echoMode() == QLineEdit.Password:
            self.sip_password.setEchoMode(QLineEdit.Normal)
            self.eye_btn.setText("Hide")
        else:
            self.sip_password.setEchoMode(QLineEdit.Password)
            self.eye_btn.setText("Show")

    def _populate(self, d):
        self.display_name.setText(d.get("display_name", ""))
        self.sip_user.setText(d.get("sip_user", ""))
        self.sip_domain.setText(d.get("sip_domain", ""))
        self.sip_password.setText(d.get("sip_password", ""))
        self.auth_user.setText(d.get("auth_user", ""))
        self.outbound_proxy.setText(d.get("outbound_proxy", ""))
        self.stun_server.setText(d.get("stun_server", "stun.l.google.com:19302"))
        self.port.setValue(d.get("port", 5060))
        self.ice_enabled.setChecked(bool(d.get("ice_enabled", 1)))
        self.srtp_enabled.setChecked(bool(d.get("srtp_enabled", 0)))
        self.register_startup.setChecked(bool(d.get("register_on_startup", 1)))
        self.is_default.setChecked(bool(d.get("is_default", 0)))
        idx = self.transport.findText(d.get("transport", "UDP").upper())
        if idx >= 0:
            self.transport.setCurrentIndex(idx)

    def _on_save(self):
        user = self.sip_user.text().strip()
        domain = self.sip_domain.text().strip()
        if not user:
            QMessageBox.warning(self, "Required", "Username is required.")
            return
        if not domain:
            QMessageBox.warning(self, "Required", "Server is required.")
            return
        data = dict(
            display_name=self.display_name.text().strip(),
            sip_user=user, sip_domain=domain,
            sip_password=self.sip_password.text(),
            auth_user=self.auth_user.text().strip(),
            transport=self.transport.currentText(),
            port=self.port.value(),
            outbound_proxy=self.outbound_proxy.text().strip(),
            stun_server=self.stun_server.text().strip(),
            ice_enabled=self.ice_enabled.isChecked(),
            srtp_enabled=self.srtp_enabled.isChecked(),
            register_on_startup=self.register_startup.isChecked(),
            is_default=self.is_default.isChecked(),
        )
        if self._account_id is not None:
            data["id"] = self._account_id
        self.saved.emit(data)

    def _on_delete(self):
        if QMessageBox.question(self, "Delete",
            f"Delete {self.sip_user.text()}@{self.sip_domain.text()}?",
            QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            if self._account_id is not None:
                self.deleted.emit(self._account_id)


class SettingsDialog(QDialog):
    def __init__(self, account_manager, config, parent=None):
        super().__init__(parent)
        # Clear inherited stylesheet for this dialog
        self.setStyleSheet("")
        self._am = account_manager
        self.setWindowTitle("ShadowSIP Settings")
        self.resize(620, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()

        # Accounts tab
        tabs.addTab(self._build_accounts(), "Accounts")

        # Placeholder tabs
        a = QLabel("Audio settings — requires PJSIP.")
        a.setAlignment(Qt.AlignCenter)
        tabs.addTab(a, "Audio")
        g = QLabel("General preferences — coming soon.")
        g.setAlignment(Qt.AlignCenter)
        tabs.addTab(g, "General")

        layout.addWidget(tabs)

    def _build_accounts(self):
        w = QWidget()
        w.setStyleSheet("")
        h = QHBoxLayout(w)
        h.setContentsMargins(10, 10, 10, 10)
        h.setSpacing(10)

        # Left panel
        left = QVBoxLayout()
        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("<b>Accounts</b>"))
        hdr.addStretch()
        ab = QPushButton("+ Add")
        ab.clicked.connect(self._show_add)
        hdr.addWidget(ab)
        left.addLayout(hdr)

        self.account_list = QListWidget()
        self.account_list.setFixedWidth(200)
        self.account_list.currentRowChanged.connect(self._on_select)
        left.addWidget(self.account_list)
        h.addLayout(left)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        h.addWidget(sep)

        self._form_box = QVBoxLayout()
        self._form = None
        self._ph = QLabel("Select an account or add new.")
        self._ph.setAlignment(Qt.AlignCenter)
        self._form_box.addWidget(self._ph)
        h.addLayout(self._form_box, stretch=1)

        self._refresh()
        return w

    def _refresh(self):
        self.account_list.clear()
        for a in self._am.get_all_accounts():
            st = self._am.get_reg_state(a["id"])
            dot = "●" if st == "registered" else "○"
            star = " ★" if a.get("is_default") else ""
            it = QListWidgetItem(f"{dot} {a['sip_user']}@{a['sip_domain']}{star}")
            it.setData(Qt.UserRole, a["id"])
            self.account_list.addItem(it)

    def _on_select(self, row):
        it = self.account_list.item(row)
        if it:
            d = self._am.get_account(it.data(Qt.UserRole))
            if d:
                self._show_form(d)

    def _show_add(self):
        self._show_form(None)

    def _show_form(self, data):
        self._clear()
        f = AccountForm(account_data=data)
        f.saved.connect(self._on_saved)
        f.cancelled.connect(self._show_ph)
        f.deleted.connect(self._on_deleted)
        self._form_box.addWidget(f)
        self._form = f

    def _show_ph(self):
        self._clear()
        self._form_box.addWidget(self._ph)
        self._ph.show()

    def _clear(self):
        if self._form:
            self._form.setParent(None)
            self._form.deleteLater()
            self._form = None
        self._ph.hide()

    def _on_saved(self, data):
        aid = data.pop("id", None)
        if aid is not None:
            self._am.update_account(aid, **data)
        else:
            self._am.add_account(**data)
        self._refresh()
        self._show_ph()

    def _on_deleted(self, aid):
        self._am.delete_account(aid)
        self._refresh()
        self._show_ph()

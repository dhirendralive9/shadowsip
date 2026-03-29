"""
Account Manager — Bridges database, SIP engine, and UI.
Handles account CRUD, registration lifecycle, and state sync.
"""

import logging
from typing import Optional, Callable

from PySide6.QtCore import QObject, Signal, QTimer

from shadowsip.db.database import Database
from shadowsip.core.sip_engine import SipEngine, RegState

logger = logging.getLogger(__name__)


class AccountManager(QObject):
    """
    Manages SIP accounts — database persistence + SIP registration.
    Emits Qt signals for UI updates.
    """

    # Signals for UI binding
    registration_changed = Signal(int, str)      # account_id, state_str
    account_added = Signal(int)                    # account_id
    account_removed = Signal(int)                  # account_id
    account_updated = Signal(int)                  # account_id
    error_occurred = Signal(str)                   # error message

    def __init__(self, db: Database, sip_engine: SipEngine, parent=None):
        super().__init__(parent)
        self._db = db
        self._engine = sip_engine

        # Wire SIP engine callbacks
        self._engine.set_callbacks(
            on_reg_state=self._on_reg_state_changed,
            on_incoming_call=self._on_incoming_call,
        )

        # PJSIP event polling timer (since threadCnt=0)
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(20)  # 50 Hz
        self._poll_timer.timeout.connect(self._engine.poll_events)

    def start(self):
        """Start SIP engine and register startup accounts."""
        try:
            self._engine.start()
            self._poll_timer.start()
            logger.info("Account manager started")
        except Exception as e:
            self.error_occurred.emit(f"SIP engine start failed: {e}")
            logger.error(f"SIP engine start failed: {e}")
            return

        # Auto-register accounts flagged for startup
        accounts = self._db.get_startup_accounts()
        for acc in accounts:
            try:
                self.register(acc["id"])
            except Exception as e:
                logger.error(f"Auto-register failed for account {acc['id']}: {e}")

    def stop(self):
        """Stop polling and shutdown SIP engine."""
        self._poll_timer.stop()
        self._engine.shutdown()
        logger.info("Account manager stopped")

    # ==================== Account CRUD ====================

    def add_account(self, sip_user: str, sip_domain: str,
                    sip_password: str = "", display_name: str = "",
                    auth_user: str = "", transport: str = "UDP",
                    port: int = 5060, outbound_proxy: str = "",
                    stun_server: str = "stun.l.google.com:19302",
                    ice_enabled: bool = True, srtp_enabled: bool = False,
                    register_on_startup: bool = True,
                    is_default: bool = False,
                    auto_register: bool = True) -> int:
        """
        Add a new SIP account to the database and optionally register it.
        Returns the account ID.
        """
        account_id = self._db.add_account(
            sip_user=sip_user, sip_domain=sip_domain,
            sip_password=sip_password, display_name=display_name,
            auth_user=auth_user, transport=transport, port=port,
            outbound_proxy=outbound_proxy, stun_server=stun_server,
            ice_enabled=ice_enabled, srtp_enabled=srtp_enabled,
            register_on_startup=register_on_startup, is_default=is_default,
        )
        self.account_added.emit(account_id)
        logger.info(f"Account added: {sip_user}@{sip_domain} (id={account_id})")

        if auto_register and self._engine.is_started:
            self.register(account_id)

        return account_id

    def update_account(self, account_id: int, **kwargs) -> bool:
        """Update account fields in database. Re-registers if needed."""
        success = self._db.update_account(account_id, **kwargs)
        if success:
            self.account_updated.emit(account_id)

            # If SIP-critical fields changed, re-register
            critical_fields = {
                "sip_user", "sip_domain", "sip_password", "auth_user",
                "transport", "port", "outbound_proxy", "stun_server",
                "ice_enabled", "srtp_enabled"
            }
            if critical_fields & set(kwargs.keys()):
                if self._engine.get_account(account_id):
                    self.unregister(account_id)
                    self.register(account_id)

        return success

    def delete_account(self, account_id: int) -> bool:
        """Delete an account — unregister first if active."""
        if self._engine.get_account(account_id):
            self.unregister(account_id)

        success = self._db.delete_account(account_id)
        if success:
            self.account_removed.emit(account_id)
            logger.info(f"Account deleted: id={account_id}")
        return success

    def get_account(self, account_id: int) -> Optional[dict]:
        """Get account data from database."""
        return self._db.get_account(account_id)

    def get_all_accounts(self) -> list[dict]:
        """Get all accounts from database."""
        return self._db.get_all_accounts()

    # ==================== Registration ====================

    def register(self, account_id: int):
        """Register an account with the SIP server."""
        config = self._db.get_account(account_id)
        if not config:
            self.error_occurred.emit(f"Account {account_id} not found")
            return

        try:
            self._engine.register_account(account_id, config)
        except Exception as e:
            self.error_occurred.emit(
                f"Registration failed for {config['sip_user']}@{config['sip_domain']}: {e}"
            )

    def unregister(self, account_id: int):
        """Unregister an account from the SIP server."""
        self._engine.unregister_account(account_id)

    def get_reg_state(self, account_id: int) -> str:
        """Get the registration state string for an account."""
        sip_acc = self._engine.get_account(account_id)
        if sip_acc:
            return sip_acc.reg_state.value
        return RegState.UNREGISTERED.value

    # ==================== Callbacks ====================

    def _on_reg_state_changed(self, account_id: int, state: RegState):
        """Called by SIP engine when registration state changes."""
        self.registration_changed.emit(account_id, state.value)
        logger.info(f"Account {account_id} registration: {state.value}")

    def _on_incoming_call(self, account_id: int, call):
        """Called by SIP engine on incoming call."""
        # TODO: Phase 1.3 — route to CallManager
        logger.info(f"Incoming call on account {account_id}")

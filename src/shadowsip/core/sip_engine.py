"""
SIP Engine — PJSIP pjsua2 wrapper for SIP registration and call control.
Handles Endpoint lifecycle, account registration, and media configuration.

If pjsua2 is not installed, runs in MOCK mode for UI development.
"""

import logging
import threading
from typing import Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import pjsua2 — fall back to mock if not built yet
try:
    import pjsua2 as pj
    PJSIP_AVAILABLE = True
    logger.info("pjsua2 module loaded successfully")
except ImportError:
    PJSIP_AVAILABLE = False
    logger.warning("pjsua2 not available — running in MOCK mode (UI only)")


class RegState(Enum):
    """Registration states."""
    UNREGISTERED = "offline"
    TRYING = "trying"
    REGISTERED = "registered"
    ERROR = "error"


class SipAccount:
    """
    Represents a SIP account with registration state tracking.
    Wraps pjsua2.Account when PJSIP is available.
    """

    def __init__(self, account_id: int, config: dict,
                 on_reg_state: Callable = None,
                 on_incoming_call: Callable = None):
        self.db_id = account_id
        self.config = config
        self._on_reg_state = on_reg_state
        self._on_incoming_call = on_incoming_call
        self._reg_state = RegState.UNREGISTERED
        self._pj_account = None
        self._registered = False

        # Build SIP URI
        self.sip_uri = f"sip:{config['sip_user']}@{config['sip_domain']}"
        self.display_name = config.get("display_name", config["sip_user"])

    @property
    def reg_state(self) -> RegState:
        return self._reg_state

    @property
    def is_registered(self) -> bool:
        return self._reg_state == RegState.REGISTERED

    @property
    def uri(self) -> str:
        return f"{self.config['sip_user']}@{self.config['sip_domain']}"

    def _set_reg_state(self, state: RegState):
        """Update registration state and notify callback."""
        old = self._reg_state
        self._reg_state = state
        if old != state and self._on_reg_state:
            self._on_reg_state(self.db_id, state)


class _PjAccount(pj.Account if PJSIP_AVAILABLE else object):
    """
    pjsua2 Account subclass with callbacks.
    Only instantiated when PJSIP is available.
    """

    def __init__(self, sip_account: SipAccount):
        if PJSIP_AVAILABLE:
            super().__init__()
        self._sip_account = sip_account

    def onRegState(self, prm):
        """Called by pjsua2 when registration state changes."""
        info = self.getInfo()
        code = info.regLastErr if hasattr(info, 'regLastErr') else 0

        if info.regIsActive:
            self._sip_account._set_reg_state(RegState.REGISTERED)
            logger.info(f"Account {self._sip_account.uri} registered (code={info.regStatus})")
        elif info.regStatus // 100 == 2:
            self._sip_account._set_reg_state(RegState.REGISTERED)
        elif info.regStatus == 0:
            self._sip_account._set_reg_state(RegState.TRYING)
        else:
            self._sip_account._set_reg_state(RegState.ERROR)
            logger.error(f"Registration failed for {self._sip_account.uri}: {info.regStatus}")

    def onIncomingCall(self, prm):
        """Called by pjsua2 on incoming INVITE."""
        call = pj.Call(self, prm.callId)
        logger.info(f"Incoming call on {self._sip_account.uri}")
        if self._sip_account._on_incoming_call:
            self._sip_account._on_incoming_call(self._sip_account.db_id, call)


class SipEngine:
    """
    SIP Engine — manages PJSIP Endpoint and accounts.

    Usage:
        engine = SipEngine()
        engine.start()
        engine.register_account(account_config)
        ...
        engine.shutdown()
    """

    def __init__(self):
        self._endpoint = None
        self._accounts: dict[int, SipAccount] = {}  # db_id -> SipAccount
        self._started = False
        self._on_reg_state: Optional[Callable] = None
        self._on_incoming_call: Optional[Callable] = None

    @property
    def is_available(self) -> bool:
        """Whether pjsua2 is loaded."""
        return PJSIP_AVAILABLE

    @property
    def is_started(self) -> bool:
        return self._started

    def set_callbacks(self, on_reg_state: Callable = None,
                      on_incoming_call: Callable = None):
        """
        Set global callbacks.
        on_reg_state(account_db_id: int, state: RegState)
        on_incoming_call(account_db_id: int, call: pj.Call)
        """
        self._on_reg_state = on_reg_state
        self._on_incoming_call = on_incoming_call

    def start(self, nameserver: str = "", user_agent: str = "ShadowSIP/0.1"):
        """
        Initialize and start the PJSIP Endpoint.
        Must be called before registering accounts.
        """
        if not PJSIP_AVAILABLE:
            logger.warning("SIP Engine start skipped — pjsua2 not available (MOCK mode)")
            self._started = True  # Pretend started for UI
            return

        if self._started:
            logger.warning("SIP Engine already started")
            return

        try:
            # Create endpoint
            self._endpoint = pj.Endpoint()
            self._endpoint.libCreate()

            # Endpoint config
            ep_cfg = pj.EpConfig()
            ep_cfg.uaConfig.userAgent = user_agent
            ep_cfg.uaConfig.threadCnt = 0  # Required for Python — no internal threads
            ep_cfg.uaConfig.mainThreadOnly = True

            if nameserver:
                ep_cfg.uaConfig.nameserver.append(nameserver)

            # Logging
            ep_cfg.logConfig.level = 3
            ep_cfg.logConfig.consoleLevel = 3

            self._endpoint.libInit(ep_cfg)

            # Create UDP transport
            tp_cfg = pj.TransportConfig()
            tp_cfg.port = 0  # Random port
            self._endpoint.transportCreate(pj.PJSIP_TRANSPORT_UDP, tp_cfg)

            # Create TCP transport
            try:
                self._endpoint.transportCreate(pj.PJSIP_TRANSPORT_TCP, tp_cfg)
            except Exception as e:
                logger.warning(f"TCP transport creation failed: {e}")

            # Start endpoint
            self._endpoint.libStart()
            self._started = True
            logger.info("SIP Engine started successfully")

        except Exception as e:
            logger.error(f"SIP Engine start failed: {e}")
            raise

    def register_account(self, account_id: int, config: dict) -> SipAccount:
        """
        Register a SIP account.

        Args:
            account_id: Database ID of the account
            config: Account config dict from database

        Returns:
            SipAccount instance
        """
        sip_account = SipAccount(
            account_id=account_id,
            config=config,
            on_reg_state=self._on_reg_state,
            on_incoming_call=self._on_incoming_call,
        )

        if not PJSIP_AVAILABLE:
            # Mock mode — simulate registration
            logger.info(f"MOCK: Registering {sip_account.uri}")
            sip_account._set_reg_state(RegState.REGISTERED)
            self._accounts[account_id] = sip_account
            return sip_account

        try:
            sip_account._set_reg_state(RegState.TRYING)

            # Create pjsua2 account config
            acfg = pj.AccountConfig()
            acfg.idUri = f"sip:{config['sip_user']}@{config['sip_domain']}"

            if config.get("display_name"):
                acfg.idUri = f'"{config["display_name"]}" <sip:{config["sip_user"]}@{config["sip_domain"]}>'

            # Registrar
            acfg.regConfig.registrarUri = f"sip:{config['sip_domain']}:{config.get('port', 5060)}"
            acfg.regConfig.retryIntervalSec = 30
            acfg.regConfig.timeoutSec = 300

            # Auth credentials
            cred = pj.AuthCredInfo()
            cred.scheme = "digest"
            cred.realm = "*"
            cred.username = config.get("auth_user") or config["sip_user"]
            cred.dataType = 0  # Plain text password
            cred.data = config.get("sip_password", "")
            acfg.sipConfig.authCreds.append(cred)

            # Outbound proxy
            if config.get("outbound_proxy"):
                proxy = config["outbound_proxy"]
                if not proxy.startswith("sip:"):
                    proxy = f"sip:{proxy}"
                acfg.sipConfig.proxies.append(proxy)

            # NAT / STUN
            if config.get("stun_server"):
                acfg.natConfig.iceEnabled = bool(config.get("ice_enabled", True))
                # STUN is configured at Endpoint level, not per-account

            # SRTP
            if config.get("srtp_enabled"):
                acfg.mediaConfig.srtpUse = pj.PJMEDIA_SRTP_OPTIONAL

            # Transport preference
            transport = config.get("transport", "UDP").upper()
            if transport == "TCP":
                acfg.sipConfig.transportId = 1  # TCP transport index
            elif transport == "TLS":
                acfg.sipConfig.transportId = 2
            # UDP is default (index 0)

            # Create pjsua2 account
            pj_account = _PjAccount(sip_account)
            pj_account.create(acfg)
            sip_account._pj_account = pj_account

            self._accounts[account_id] = sip_account
            logger.info(f"Account registered: {sip_account.uri}")
            return sip_account

        except Exception as e:
            sip_account._set_reg_state(RegState.ERROR)
            logger.error(f"Account registration failed for {sip_account.uri}: {e}")
            raise

    def unregister_account(self, account_id: int):
        """Unregister and remove a SIP account."""
        sip_account = self._accounts.get(account_id)
        if not sip_account:
            return

        if PJSIP_AVAILABLE and sip_account._pj_account:
            try:
                sip_account._pj_account.setRegistration(False)
                # Give time for unregister
                import time
                time.sleep(0.5)
                sip_account._pj_account.shutdown()
            except Exception as e:
                logger.error(f"Unregister error: {e}")

        sip_account._set_reg_state(RegState.UNREGISTERED)
        del self._accounts[account_id]
        logger.info(f"Account unregistered: {sip_account.uri}")

    def get_account(self, account_id: int) -> Optional[SipAccount]:
        """Get a registered SIP account by database ID."""
        return self._accounts.get(account_id)

    def get_all_accounts(self) -> list[SipAccount]:
        """Get all registered accounts."""
        return list(self._accounts.values())

    def poll_events(self):
        """
        Poll PJSIP for events. Must be called periodically from a timer
        since we set threadCnt=0 for Python safety.
        """
        if PJSIP_AVAILABLE and self._endpoint and self._started:
            try:
                self._endpoint.libHandleEvents(10)  # 10ms timeout
            except Exception:
                pass

    def shutdown(self):
        """Shutdown the SIP engine and all accounts."""
        if not self._started:
            return

        logger.info("SIP Engine shutting down...")

        # Unregister all accounts
        for account_id in list(self._accounts.keys()):
            self.unregister_account(account_id)

        if PJSIP_AVAILABLE and self._endpoint:
            try:
                self._endpoint.libDestroy()
            except Exception as e:
                logger.error(f"Endpoint destroy error: {e}")
            self._endpoint = None

        self._started = False
        logger.info("SIP Engine shutdown complete")

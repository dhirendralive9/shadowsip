"""
Database — SQLite storage for accounts, call history, and settings.
Uses plain sqlite3 (no ORM dependency) for minimal footprint.
"""

import os
import sqlite3
import json
import logging
from typing import Optional
from contextlib import contextmanager

from shadowsip.utils.platform import get_data_dir

logger = logging.getLogger(__name__)

DB_VERSION = 1


class Database:
    """SQLite database manager."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            data_dir = get_data_dir()
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "shadowsip.db")

        self._path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")

        self._init_tables()
        logger.info(f"Database opened: {db_path}")

    def _init_tables(self):
        """Create tables if they don't exist."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT NOT NULL DEFAULT '',
                sip_user TEXT NOT NULL,
                sip_domain TEXT NOT NULL,
                sip_password TEXT NOT NULL DEFAULT '',
                auth_user TEXT DEFAULT '',
                transport TEXT DEFAULT 'UDP',
                port INTEGER DEFAULT 5060,
                outbound_proxy TEXT DEFAULT '',
                stun_server TEXT DEFAULT 'stun.l.google.com:19302',
                ice_enabled INTEGER DEFAULT 1,
                srtp_enabled INTEGER DEFAULT 0,
                register_on_startup INTEGER DEFAULT 1,
                is_default INTEGER DEFAULT 0,
                codec_priority TEXT DEFAULT '["PCMU/8000","PCMA/8000","opus/48000","G722/16000"]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS call_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                remote_uri TEXT NOT NULL,
                remote_name TEXT DEFAULT '',
                direction TEXT NOT NULL,
                duration_seconds INTEGER DEFAULT 0,
                status TEXT DEFAULT 'completed',
                codec_used TEXT DEFAULT '',
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ended_at DATETIME,
                recording_path TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_call_history_started
                ON call_history(started_at DESC);
            CREATE INDEX IF NOT EXISTS idx_call_history_remote
                ON call_history(remote_uri);
        """)
        self._conn.commit()

    @contextmanager
    def _cursor(self):
        """Context manager for cursor with auto-commit."""
        cursor = self._conn.cursor()
        try:
            yield cursor
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    # ==================== Accounts ====================

    def add_account(self, sip_user: str, sip_domain: str,
                    sip_password: str = "", display_name: str = "",
                    auth_user: str = "", transport: str = "UDP",
                    port: int = 5060, outbound_proxy: str = "",
                    stun_server: str = "stun.l.google.com:19302",
                    ice_enabled: bool = True, srtp_enabled: bool = False,
                    register_on_startup: bool = True,
                    is_default: bool = False) -> int:
        """Add a SIP account. Returns the account ID."""
        with self._cursor() as cur:
            # If this is default, unset other defaults
            if is_default:
                cur.execute("UPDATE accounts SET is_default = 0")

            cur.execute("""
                INSERT INTO accounts
                (display_name, sip_user, sip_domain, sip_password, auth_user,
                 transport, port, outbound_proxy, stun_server,
                 ice_enabled, srtp_enabled, register_on_startup, is_default)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (display_name, sip_user, sip_domain, sip_password, auth_user,
                  transport, port, outbound_proxy, stun_server,
                  int(ice_enabled), int(srtp_enabled),
                  int(register_on_startup), int(is_default)))
            return cur.lastrowid

    def update_account(self, account_id: int, **kwargs) -> bool:
        """Update account fields. Pass field=value pairs."""
        allowed = {
            "display_name", "sip_user", "sip_domain", "sip_password",
            "auth_user", "transport", "port", "outbound_proxy",
            "stun_server", "ice_enabled", "srtp_enabled",
            "register_on_startup", "is_default", "codec_priority"
        }
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False

        # Convert booleans to int
        for k in ("ice_enabled", "srtp_enabled", "register_on_startup", "is_default"):
            if k in fields:
                fields[k] = int(fields[k])

        if fields.get("is_default"):
            with self._cursor() as cur:
                cur.execute("UPDATE accounts SET is_default = 0")

        sets = ", ".join(f"{k} = ?" for k in fields)
        vals = list(fields.values()) + [account_id]

        with self._cursor() as cur:
            cur.execute(
                f"UPDATE accounts SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                vals
            )
            return cur.rowcount > 0

    def delete_account(self, account_id: int) -> bool:
        """Delete an account."""
        with self._cursor() as cur:
            cur.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            return cur.rowcount > 0

    def get_account(self, account_id: int) -> Optional[dict]:
        """Get a single account by ID."""
        cur = self._conn.execute(
            "SELECT * FROM accounts WHERE id = ?", (account_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def get_all_accounts(self) -> list[dict]:
        """Get all accounts."""
        cur = self._conn.execute(
            "SELECT * FROM accounts ORDER BY is_default DESC, id ASC"
        )
        return [dict(row) for row in cur.fetchall()]

    def get_default_account(self) -> Optional[dict]:
        """Get the default account."""
        cur = self._conn.execute(
            "SELECT * FROM accounts WHERE is_default = 1 LIMIT 1"
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def get_startup_accounts(self) -> list[dict]:
        """Get accounts flagged for auto-register on startup."""
        cur = self._conn.execute(
            "SELECT * FROM accounts WHERE register_on_startup = 1 ORDER BY is_default DESC"
        )
        return [dict(row) for row in cur.fetchall()]

    # ==================== Call History ====================

    def add_call_record(self, remote_uri: str, direction: str,
                        account_id: int = None, remote_name: str = "",
                        duration_seconds: int = 0, status: str = "completed",
                        codec_used: str = "", recording_path: str = "",
                        notes: str = "") -> int:
        """Add a call history record. Returns record ID."""
        with self._cursor() as cur:
            cur.execute("""
                INSERT INTO call_history
                (account_id, remote_uri, remote_name, direction,
                 duration_seconds, status, codec_used, recording_path, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (account_id, remote_uri, remote_name, direction,
                  duration_seconds, status, codec_used, recording_path, notes))
            return cur.lastrowid

    def get_call_history(self, limit: int = 50, offset: int = 0,
                         direction: str = None) -> list[dict]:
        """Get call history records."""
        query = "SELECT * FROM call_history"
        params = []
        if direction:
            query += " WHERE direction = ?"
            params.append(direction)
        query += " ORDER BY started_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cur = self._conn.execute(query, params)
        return [dict(row) for row in cur.fetchall()]

    # ==================== Settings ====================

    def get_setting(self, key: str, default: str = "") -> str:
        """Get a setting value."""
        cur = self._conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        row = cur.fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        """Set a setting value (upsert)."""
        with self._cursor() as cur:
            cur.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )

    def close(self):
        """Close the database connection."""
        self._conn.close()
        logger.info("Database closed")

"""SQLite database for tracking LINE↔Sendbird users and conversations."""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

logger = logging.getLogger(__name__)

_DB_PATH = Path(__file__).parent.parent.parent / "conversations.db"
_conn: sqlite3.Connection | None = None


def init_db(db_path: str | Path | None = None) -> None:
    """Create tables if they don't exist. Call once at startup."""
    global _conn
    path = str(db_path or _DB_PATH)
    _conn = sqlite3.connect(path, check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    _conn.execute("PRAGMA journal_mode=WAL")
    _conn.execute("PRAGMA foreign_keys=ON")

    _conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            line_user_id    TEXT    NOT NULL UNIQUE,
            sb_user_id      TEXT    NOT NULL UNIQUE,
            display_name    TEXT    DEFAULT '',
            created_at      TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_url     TEXT    NOT NULL,
            line_user_id    TEXT    NOT NULL,
            sb_user_id      TEXT    NOT NULL,
            status          TEXT    NOT NULL DEFAULT 'pending',
            created_at      TEXT    NOT NULL,
            updated_at      TEXT    NOT NULL,
            FOREIGN KEY (line_user_id) REFERENCES users(line_user_id)
        );

        CREATE INDEX IF NOT EXISTS idx_conv_channel ON conversations(channel_url);
        CREATE INDEX IF NOT EXISTS idx_conv_status  ON conversations(status);
        CREATE INDEX IF NOT EXISTS idx_conv_sb_user ON conversations(sb_user_id);
    """)
    _conn.commit()
    logger.info("[DB] Initialized at %s", path)


@contextmanager
def _get_conn() -> Generator[sqlite3.Connection, None, None]:
    if _conn is None:
        raise RuntimeError("Database not initialized — call init_db() first")
    yield _conn


# ── Users ──────────────────────────────────────────


def get_user_by_line_id(line_user_id: str) -> dict | None:
    """Look up a user by LINE user ID."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE line_user_id = ?", (line_user_id,)
        ).fetchone()
        return dict(row) if row else None


def get_user_by_sb_id(sb_user_id: str) -> dict | None:
    """Look up a user by Sendbird user ID."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE sb_user_id = ?", (sb_user_id,)
        ).fetchone()
        return dict(row) if row else None


def create_user(line_user_id: str, sb_user_id: str, display_name: str = "") -> dict:
    """Insert a new user. Returns the created row."""
    now = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO users (line_user_id, sb_user_id, display_name, created_at) "
            "VALUES (?, ?, ?, ?)",
            (line_user_id, sb_user_id, display_name, now),
        )
        conn.commit()
    logger.info("[DB] Created user line=%s sb=%s", line_user_id[:8], sb_user_id)
    return {"line_user_id": line_user_id, "sb_user_id": sb_user_id, "display_name": display_name}


# ── Conversations ──────────────────────────────────


def upsert_conversation(
    channel_url: str,
    line_user_id: str,
    sb_user_id: str,
    status: str = "pending",
) -> dict:
    """Create or update a conversation record."""
    now = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM conversations WHERE channel_url = ? AND sb_user_id = ?",
            (channel_url, sb_user_id),
        ).fetchone()

        if existing:
            conn.execute(
                "UPDATE conversations SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, existing["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO conversations "
                "(channel_url, line_user_id, sb_user_id, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (channel_url, line_user_id, sb_user_id, status, now, now),
            )
        conn.commit()

    logger.info("[DB] Conversation %s -> %s (user=%s)", channel_url[:20], status, sb_user_id)
    return {"channel_url": channel_url, "status": status}


def update_conversation_status(channel_url: str, status: str) -> bool:
    """Update conversation status by channel_url. Returns True if a row was updated."""
    now = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        cursor = conn.execute(
            "UPDATE conversations SET status = ?, updated_at = ? WHERE channel_url = ?",
            (status, now, channel_url),
        )
        conn.commit()
        updated = cursor.rowcount > 0

    if updated:
        logger.info("[DB] Channel %s -> %s", channel_url[:20], status)
    else:
        logger.warning("[DB] Channel %s not found for status update", channel_url[:20])
    return updated


def get_conversation_by_channel(channel_url: str) -> dict | None:
    """Get the latest conversation for a channel."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM conversations WHERE channel_url = ? ORDER BY updated_at DESC LIMIT 1",
            (channel_url,),
        ).fetchone()
        return dict(row) if row else None


def get_active_conversation_for_user(sb_user_id: str) -> dict | None:
    """Get the user's active (non-closed) conversation."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM conversations "
            "WHERE sb_user_id = ? AND status != 'closed' "
            "ORDER BY updated_at DESC LIMIT 1",
            (sb_user_id,),
        ).fetchone()
        return dict(row) if row else None

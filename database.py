import os
import json
import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_PATH    = os.getenv("DATABASE_PATH", "mailpilot.db")
ALERT_THRESHOLD  = 8.0  # instant Telegram alert
DIGEST_THRESHOLD = 4.0  # include in daily digest; below this → trash


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        yield conn
    finally:
        conn.close()


def init_db():
    try:
        with get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id     INTEGER PRIMARY KEY,
                    gmail_address   TEXT    NOT NULL,
                    filter_keywords TEXT,
                    digest_time     TEXT    DEFAULT '09:00',
                    is_active       INTEGER DEFAULT 0,
                    created_at      TEXT,
                    updated_at      TEXT
                );

                CREATE TABLE IF NOT EXISTS emails (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id       INTEGER NOT NULL,
                    message_id    TEXT    NOT NULL UNIQUE,
                    sender        TEXT,
                    subject       TEXT,
                    received_at   TEXT,
                    ai_score      REAL,
                    ai_reasoning  TEXT,
                    is_important  INTEGER DEFAULT 0,
                    needs_alert   INTEGER DEFAULT 0,
                    digest_sent   INTEGER DEFAULT 0,
                    created_at    TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_emails_user_digest
                    ON emails(user_id, digest_sent);

                CREATE INDEX IF NOT EXISTS idx_emails_user_date
                    ON emails(user_id, received_at);
            """)
            conn.commit()
        logger.info("Database ready: %s", DATABASE_PATH)
    except sqlite3.Error as e:
        logger.error("init_db failed: %s", e)
        raise


def upsert_user(telegram_id: int, gmail_address: str, filter_keywords: list,
                digest_time: str, is_active: int):
    now = _now_utc()
    try:
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO users
                    (telegram_id, gmail_address, filter_keywords, digest_time,
                     is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    gmail_address   = excluded.gmail_address,
                    filter_keywords = excluded.filter_keywords,
                    digest_time     = excluded.digest_time,
                    is_active       = excluded.is_active,
                    updated_at      = excluded.updated_at
            """, (telegram_id, gmail_address, json.dumps(filter_keywords),
                  digest_time, is_active, now, now))
            conn.commit()
    except sqlite3.Error as e:
        logger.error("upsert_user(%s) failed: %s", telegram_id, e)
        raise


def get_user(telegram_id: int) -> dict | None:
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
            ).fetchone()
        if row is None:
            return None
        user = dict(row)
        user["filter_keywords"] = json.loads(user["filter_keywords"] or "[]")
        return user
    except sqlite3.Error as e:
        logger.error("get_user(%s) failed: %s", telegram_id, e)
        return None


def get_all_active_users() -> list[dict]:
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM users WHERE is_active = 1"
            ).fetchall()
        users = []
        for row in rows:
            user = dict(row)
            user["filter_keywords"] = json.loads(user["filter_keywords"] or "[]")
            users.append(user)
        return users
    except sqlite3.Error as e:
        logger.error("get_all_active_users failed: %s", e)
        return []


def deactivate_user(telegram_id: int):
    try:
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET is_active = 0 WHERE telegram_id = ?",
                (telegram_id,)
            )
            conn.commit()
    except sqlite3.Error as e:
        logger.error("deactivate_user(%s) failed: %s", telegram_id, e)


def insert_email(user_id: int, message_id: str, sender: str, subject: str,
                 received_at: str, ai_score: float, ai_reasoning: str) -> bool:
    is_important = 1 if ai_score >= DIGEST_THRESHOLD else 0
    needs_alert  = 1 if ai_score >= ALERT_THRESHOLD  else 0
    try:
        with get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO emails
                    (user_id, message_id, sender, subject, received_at,
                     ai_score, ai_reasoning, is_important, needs_alert, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, message_id, sender, subject, received_at,
                  ai_score, ai_reasoning, is_important, needs_alert, _now_utc()))
            conn.commit()
            return cursor.rowcount == 1
    except sqlite3.Error as e:
        logger.error("insert_email(%s) failed: %s", message_id, e)
        return False


def get_unsent_emails(user_id: int) -> list[dict]:
    try:
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM emails
                WHERE user_id = ? AND is_important = 1 AND digest_sent = 0
                ORDER BY received_at ASC
            """, (user_id,)).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        logger.error("get_unsent_emails(%s) failed: %s", user_id, e)
        return []


def mark_digest_sent(email_ids: list[int]):
    if not email_ids:
        return
    placeholders = ",".join("?" * len(email_ids))
    try:
        with get_connection() as conn:
            conn.execute(
                f"UPDATE emails SET digest_sent = 1 WHERE id IN ({placeholders})",
                email_ids
            )
            conn.commit()
    except sqlite3.Error as e:
        logger.error("mark_digest_sent(%s) failed: %s", email_ids, e)


def get_recent_email_stats(user_id: int, hours: int = 24) -> dict:
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        with get_connection() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*)          AS total,
                    SUM(is_important) AS important
                FROM emails
                WHERE user_id = ? AND received_at >= ?
            """, (user_id, cutoff)).fetchone()
        return {
            "total":     int(row["total"]     or 0),
            "important": int(row["important"] or 0),
        }
    except sqlite3.Error as e:
        logger.error("get_recent_email_stats(%s) failed: %s", user_id, e)
        return {"total": 0, "important": 0}

# =============================================================================
# database.py — SQLite persistence layer for MailPilot
# =============================================================================
#
# PURPOSE:
#   All database reads and writes go through this module. Uses Python's
#   built-in sqlite3 — no ORM — to keep dependencies minimal and queries
#   explicit. A context-manager helper manages connection lifecycle so
#   callers never need to close connections manually.
#
# DATABASE FILE:
#   Location is read from the DATABASE_PATH environment variable.
#   Default: mailpilot.db in the current working directory.
#   The file is created automatically by init_db() on first startup.
#
# =============================================================================


# --- Imports ------------------------------------------------------------------
# os           — resolve DATABASE_PATH from environment
# json         — serialize/deserialize the filter_keywords list
# sqlite3      — built-in database driver
# datetime     — generate UTC ISO-8601 timestamps for created_at/updated_at
# contextlib   — @contextmanager decorator for the connection helper
# logging      — log errors and warnings from database operations


# --- Configuration ------------------------------------------------------------
# DATABASE_PATH  — read from env, default 'mailpilot.db'
# IMPORTANCE_THRESHOLD = 6.0
#   Emails with ai_score >= this value are flagged is_important=1.
#   Defined here so ai_filter.py and database.py share the same constant.


# =============================================================================
# SCHEMA
# =============================================================================

# --- TABLE: users -------------------------------------------------------------
#
#   telegram_id    INTEGER  PRIMARY KEY
#     Telegram user ID. Stable unique identifier supplied by the Telegram API.
#
#   gmail_address  TEXT     NOT NULL
#     The Gmail address the user wants to monitor.
#
#   filter_keywords TEXT
#     JSON-encoded list of strings, e.g. '["Python", "remote", "senior"]'.
#     Decoded back to a Python list by get_user().
#
#   digest_time    TEXT     DEFAULT '09:00'
#     HH:MM string (UTC). Used by bot.py to schedule the daily JobQueue job.
#
#   is_active      INTEGER  DEFAULT 0
#     Boolean flag: 1 = setup complete and Gmail authorized; 0 = not ready.
#     Only active users receive digest jobs and email polling.
#
#   created_at     TEXT
#     ISO-8601 UTC timestamp set once when the row is first inserted.
#
#   updated_at     TEXT
#     ISO-8601 UTC timestamp refreshed on every upsert_user() call.


# --- TABLE: emails ------------------------------------------------------------
#
#   id             INTEGER  PRIMARY KEY AUTOINCREMENT
#
#   user_id        INTEGER  NOT NULL
#     Foreign key → users.telegram_id.
#
#   message_id     TEXT     NOT NULL  UNIQUE
#     Gmail message ID string. The UNIQUE constraint combined with
#     INSERT OR IGNORE prevents the same email from being stored twice
#     even if the polling job runs more than once before a message is
#     marked as read.
#
#   sender         TEXT
#     Value of the "From" header (may include display name and address).
#
#   subject        TEXT
#     Value of the "Subject" header.
#
#   received_at    TEXT
#     ISO-8601 parsed from the "Date" header. Used for date-range queries
#     in get_recent_email_stats().
#
#   ai_score       REAL
#     Float 0.0–10.0 returned by ai_filter.score_email(). Stored as-is.
#
#   ai_reasoning   TEXT
#     One-sentence explanation returned by Claude alongside the score.
#     Included in the digest message shown to the user.
#
#   is_important   INTEGER  DEFAULT 0
#     Set to 1 during insert_email() when ai_score >= IMPORTANCE_THRESHOLD.
#
#   digest_sent    INTEGER  DEFAULT 0
#     Set to 1 by mark_digest_sent() after the email appears in a digest.
#     Prevents the same email from being sent in multiple digests.
#
#   created_at     TEXT
#     ISO-8601 UTC timestamp of when the row was inserted.
#
# INDEXES:
#   idx_emails_user_digest  ON emails(user_id, digest_sent)
#     Speeds up get_unsent_emails() which filters on both columns.
#
#   idx_emails_user_date    ON emails(user_id, received_at)
#     Speeds up get_recent_email_stats() date-range queries.


# =============================================================================
# CONNECTION HELPER
# =============================================================================

# def get_connection():  [used as a @contextmanager]
#
#   PURPOSE:
#     Yields a configured sqlite3.Connection and guarantees it is closed
#     even if an exception occurs inside the with-block.
#
#   CONFIGURATION APPLIED:
#     row_factory = sqlite3.Row   — columns accessible by name, not index
#     PRAGMA journal_mode = WAL   — allows concurrent readers during writes
#     PRAGMA busy_timeout = 5000  — wait up to 5 s before raising OperationalError
#                                   on a locked database (relevant if multiple
#                                   polling jobs overlap briefly)


# =============================================================================
# INITIALIZATION
# =============================================================================

# def init_db():
#
#   PURPOSE:
#     Create both tables and all indexes if they do not already exist.
#     Safe to call on every bot startup — uses CREATE IF NOT EXISTS.
#     Logs the database file path after successful initialization.
#
#   CALLED BY: bot.py → main() before the Application starts polling.


# =============================================================================
# USER CRUD
# =============================================================================

# def upsert_user(telegram_id, gmail_address, filter_keywords, digest_time, is_active):
#
#   PURPOSE:
#     Insert a new user row or update all mutable fields if the
#     telegram_id already exists. Atomically handles both cases with
#     INSERT INTO ... ON CONFLICT(telegram_id) DO UPDATE SET ...
#
#   SERIALIZATION:
#     filter_keywords list → json.dumps() before storing.
#     updated_at → current UTC ISO-8601 on every call.
#     created_at → only written on INSERT, preserved on UPDATE.
#
#   CALLED BY: bot.py → setup_step3_time() when the setup wizard completes.


# def get_user(telegram_id):
#
#   PURPOSE:
#     Fetch a single user by Telegram ID.
#
#   RETURNS:
#     dict with all columns (filter_keywords deserialized via json.loads),
#     or None if no row exists for this telegram_id.
#
#   CALLED BY: bot.py → start_handler, status_handler, digest_handler.


# def get_all_active_users():
#
#   PURPOSE:
#     Return all users where is_active = 1.
#
#   RETURNS:
#     List of dicts (same format as get_user).
#
#   CALLED BY: bot.py → main(), to re-register JobQueue digest jobs
#              after a bot restart so no scheduled digests are missed.


# def deactivate_user(telegram_id):
#
#   PURPOSE:
#     Set is_active = 0 for the given user.
#     Used when Gmail token refresh fails and the user must re-authorize.
#
#   CALLED BY: gmail_reader.py → authenticate() on RefreshError.


# =============================================================================
# EMAIL CRUD
# =============================================================================

# def insert_email(user_id, message_id, sender, subject, received_at,
#                  ai_score, ai_reasoning):
#
#   PURPOSE:
#     Persist a fetched and scored email to the database.
#
#   DUPLICATE HANDLING:
#     Uses INSERT OR IGNORE — silently skips rows whose message_id already
#     exists. Returns True if a new row was inserted, False if skipped.
#
#   is_important:
#     Computed inline: 1 if ai_score >= IMPORTANCE_THRESHOLD else 0.
#
#   CALLED BY: gmail_reader.py → fetch_and_store_emails().


# def get_unsent_emails(user_id):
#
#   PURPOSE:
#     Fetch all emails for a user that are important but not yet included
#     in any digest (is_important=1 AND digest_sent=0).
#
#   RETURNS:
#     List of dicts ordered by received_at ASC (oldest first).
#
#   CALLED BY: bot.py → digest_handler() and daily_digest_job().


# def mark_digest_sent(email_ids):
#
#   PURPOSE:
#     Bulk-update digest_sent = 1 for a list of email primary-key IDs
#     after a digest has been successfully sent to the user.
#
#   IMPLEMENTATION NOTE:
#     Build a parameterized IN clause dynamically:
#     "UPDATE emails SET digest_sent=1 WHERE id IN (?,?,?)"
#     with len(email_ids) placeholders to avoid SQL injection.
#
#   CALLED BY: bot.py → after a digest message is sent successfully.


# def get_recent_email_stats(user_id, hours=24):
#
#   PURPOSE:
#     Return total and important email counts for the last N hours.
#     Used by /status to show the user a quick activity summary.
#
#   RETURNS:
#     dict: {'total': int, 'important': int}
#
#   CALLED BY: bot.py → status_handler().

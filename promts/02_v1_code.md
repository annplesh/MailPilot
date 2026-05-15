# Prompt 02 — V1 Code Implementation

## Request sent to Claude AI

Implement **database.py** for MailPilot bot.

**Requirements:**

- SQLite database with two tables: `users` and `emails`
- Table `users`: telegram_id, gmail_address, filter_keywords, digest_time, is_active, created_at, updated_at
- Table `emails`: id, user_id, message_id (UNIQUE), sender, subject, received_at, ai_score, ai_reasoning, is_important, digest_sent, created_at
- Functions: `init_db`, `upsert_user`, `get_user`, `get_all_active_users`, `deactivate_user`, `insert_email`, `get_unsent_emails`, `mark_digest_sent`, `get_recent_email_stats`
- Load DATABASE_PATH from .env
- English comments
- Handle all errors with try/except

**Corrections requested before implementation:**

1. Use TWO thresholds instead of one:
   - ALERT_THRESHOLD = 8.0 → instant Telegram alert
   - DIGEST_THRESHOLD = 4.0 → add to daily digest
   - Below 4.0 → trash automatically

2. Add to SYSTEM_PROMPT in ai_filter.py:
   "Emails may be in any language (Spanish, English, Portuguese).
   Score based on content meaning, not language."

3. If keywords list is empty, use default:
   "any programming, development, freelance work"

4. On RateLimitError — wait 60 seconds before re-raising

## Result

Claude implemented database.py with all requirements.
Verified with: python -c "from database import init_db; init_db(); print('OK')"

## ai_filter.py — Request

Implement ai_filter.py with the same quality as database.py.

Requirements:

- ALERT_THRESHOLD = 8.0, DIGEST_THRESHOLD = 4.0
- Add to SYSTEM_PROMPT: "Emails may be in any language (Spanish, English, Portuguese). Score based on content meaning, not language."
- If keywords empty use default: "any programming, development, freelance work"
- On RateLimitError wait 60 seconds before re-raising

## gmail_reader.py — Request

Approved gmail_reader.py plan. Key decisions:

- MAX_MESSAGES = 50
- SCOPES: gmail.readonly + gmail.modify
- \_mark_as_read always called even for score 0
- RateLimitError breaks loop without re-raising
- Prefer text/plain over text/html for cleaner Claude input

## bot.py — Request

Approved. Implement bot.py — the main FSM bot file.

Key requirements:

- ConversationHandler with 3 states: START, SETUP, ACTIVE
- /setup wizard: 3 steps (Gmail, keywords, digest time)
- daily_digest_job via APScheduler
- \_send_alerts before \_send_digest
- allow_reentry=True
- Restart recovery for active users
- asyncio.to_thread() for Gmail and Claude calls
- HTML parse mode with html.escape()
- Fallback handler for unexpected input

## Result

All 4 files implemented and verified:

- database.py — 7/7 smoke tests passed
- ai_filter.py — constants and prompt verified
- gmail_reader.py — functions and constants verified
- bot.py — structure verified, bot starts successfully

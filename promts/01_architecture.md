# Prompt 01 — Architecture Planning

## Request sent to Claude AI

I am building a Telegram bot called **MailPilot** for freelancers.

**Business task:** Monitor a dedicated Gmail inbox for job search,
filter important emails using Claude AI, and send alerts/digest to Telegram.

**Scenarios:**

- User connects a dedicated Gmail inbox (not personal email)
- Bot scans emails, AI decides important vs spam
- Score 8-10 → instant Telegram alert
- Score 4-7 → added to daily digest sent at chosen time
- Score 1-3 → moved to trash automatically

**Data collected from user:**

- Gmail address of work inbox
- Tech stack / keywords to filter by
- Preferred digest time

**Where we store results:** SQLite database

**Where AI is needed:** Email importance scoring (Claude API)

**Where AI is NOT needed:** Gmail connection, Telegram message delivery

Please show (no code yet):

1. FSM state map for main scenario
2. What data is stored and where
3. List of integrations

---

## Response — FSM State Map

### States

- **START (0)** — /start command, welcome message, offer /setup
- **SETUP (1)** — 3-step wizard:
  - Step 1: Gmail address (validate @gmail.com)
  - Step 2: Keywords (comma-separated, minimum 1)
  - Step 3: Digest time (HH:MM format, UTC)
- **ACTIVE (2)** — monitoring mode:
  - /status — show current settings and stats
  - /digest — manual inbox check
  - /setup — re-configure (allow_reentry=True)

### Data stored in SQLite

**Table: users**

- telegram_id
- gmail_address
- filter_keywords (JSON array)
- digest_time
- is_active
- created_at, updated_at

**Table: emails**

- message_id (UNIQUE — deduplication)
- subject, sender, received_at
- ai_score, ai_reasoning
- is_important, needs_alert, digest_sent
- created_at

### Integrations

1. Telegram Bot API — user interface
2. Gmail API (OAuth2) — read and modify emails
3. Anthropic Claude API — importance scoring
4. SQLite — persistent storage
5. APScheduler — daily digest scheduling

### Scoring thresholds

- ALERT_THRESHOLD = 8.0 → instant Telegram alert
- DIGEST_THRESHOLD = 4.0 → daily digest
- Below 4.0 → trash automatically

### Unexpected input handling

- Invalid Gmail → "Please enter a valid @gmail.com address"
- Invalid time format → "Please use HH:MM format (e.g. 09:00)"
- Any text in wrong state → friendly error + redirect
- Unknown command → fallback_handler responds politely

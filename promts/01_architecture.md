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

- **START (0)** — User launches bot, sees welcome message
- **SETUP (1)** — User connects Gmail, sets keywords and digest time
- **ACTIVE (2)** — Bot monitors inbox 24/7, sends alerts and digest

### Data stored in SQLite

**Table: users**

- telegram_id
- gmail_address
- keywords
- digest_time
- state

**Table: emails**

- message_id (unique)
- subject
- sender
- score
- digest_sent
- created_at

### Integrations

1. Telegram Bot API — user interface
2. Gmail API (OAuth2) — read emails
3. Anthropic Claude API — score importance
4. SQLite — persistent storage

### Unexpected input handling

- User writes text when button expected → friendly error message
- User writes in wrong state → redirect to correct state
- Gmail connection fails → clear error with retry option

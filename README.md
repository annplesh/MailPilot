# MailPilot — Telegram Bot for Job Opportunity Monitoring

MailPilot monitors a dedicated Gmail inbox, scores every incoming email with
Claude AI (0–10), and sends you a curated daily digest of genuine job
opportunities directly in Telegram.

---

## Features

- Connects to a Gmail inbox via the official Gmail API (OAuth2, no password stored)
- Scores emails 0–10 with `claude-sonnet-4-6`; prompt caching reduces API costs
- Sends a daily digest at your chosen UTC time — only high-score emails included
- Configurable per-user keywords (e.g. Python, remote, senior, backend)
- `/digest` command for an on-demand digest at any time
- Handles unknown commands and unexpected input gracefully

---

## FSM Diagram

The bot uses a 3-state Finite State Machine managed by `ConversationHandler`:

```
         /start  (new user)
              │
              ▼
         ┌─────────┐
         │  START  │  No setup done yet.
         │   (0)   │  Only /setup is available.
         └────┬────┘
              │ /setup
              ▼
         ┌─────────┐
         │  SETUP  │  3-step configuration wizard:
         │   (1)   │    Step 1 — Gmail address  (@gmail.com validation)
         │         │    Step 2 — Filter keywords (comma-separated)
         │         │    Step 3 — Digest time     (HH:MM UTC)
         └────┬────┘
              │ Setup complete → user written to DB, JobQueue job scheduled
              ▼
         ┌─────────┐
         │ ACTIVE  │  Normal operation.
         │   (2)   │    /status — settings + last-24h email stats
         │         │    /digest — fetch + score + send digest now
         └─────────┘
              │
              └─ /setup re-enters SETUP from ACTIVE (allow_reentry=True)

All states: unknown commands or free text → fallback handler → command list
```

---

## Project Structure

```
jobpilot/
├── bot.py            # Entry point, FSM, all handlers, JobQueue scheduler
├── database.py       # SQLite CRUD — users and emails tables, no ORM
├── ai_filter.py      # Claude AI scoring with prompt caching
├── gmail_reader.py   # Gmail OAuth2, fetch, parse, mark-as-read
├── .env.example      # Environment variable template — copy to .env
├── requirements.txt  # Pinned Python dependencies
└── README.md         # This file
```

### Module dependency order (no circular imports)

```
database.py      ← no internal imports
ai_filter.py     ← no internal imports
gmail_reader.py  ← imports database, ai_filter
bot.py           ← imports database, gmail_reader
```

---

## Prerequisites

- Python 3.14 or newer
- A Telegram bot token (from @BotFather)
- An Anthropic API key (from [console.anthropic.com](https://console.anthropic.com/settings/keys))
- A Google Cloud project with the Gmail API enabled

---

## Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd jobpilot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your `TELEGRAM_BOT_TOKEN` and `ANTHROPIC_API_KEY`.

### 4. Obtain Gmail API credentials

1. Open [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Go to **APIs & Services → Library** and enable the **Gmail API**.
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
4. Choose **Desktop app** as the application type.
5. Click **Download JSON** and save the file as `credentials.json` in the project root.
6. Update `GMAIL_CREDENTIALS_FILE=credentials.json` in your `.env` if you saved it elsewhere.

On first bot startup, opening `/setup` will trigger a browser window asking you to
authorise Gmail access. After approval, a `token_<your_telegram_id>.json` file is
saved automatically. You will not need to authorise again unless the token is revoked.

### 5. Run the bot

```bash
python bot.py
```

---

## Usage

| Command   | State(s)      | Description                                       |
|-----------|---------------|---------------------------------------------------|
| `/start`  | Any           | Greet user; redirect to `/setup` if not set up   |
| `/setup`  | START, ACTIVE | Launch 3-step configuration wizard                |
| `/status` | ACTIVE        | Show current settings and last-24h email counts   |
| `/digest` | ACTIVE        | Fetch new emails, score them, and send digest now |

---

## Architecture Notes

**Sync vs async**
`gmail_reader.py` and `ai_filter.py` are synchronous modules. They are called
from async Telegram handlers via `asyncio.to_thread()` so network I/O does not
block the event loop.

**Prompt caching**
`ai_filter.py` sends the static system prompt with `cache_control: ephemeral`.
On a batch of 50 emails this saves roughly 49 × 800 = 39 200 cached input tokens
per polling cycle, significantly reducing Claude API costs.

**Duplicate prevention**
Gmail `message_id` values are stored with a `UNIQUE` constraint.
`INSERT OR IGNORE` silently skips any message already in the database, so
re-running the polling job is safe.

**Bot restart safety**
On startup, `bot.py` queries all active users and re-registers their `JobQueue`
digest jobs. No digest is missed after a crash or redeploy.

---

## Security Notes

- Never commit `.env`, `credentials.json`, or `token_*.json` to version control.
  Add them to `.gitignore` immediately.
- The Gmail OAuth token grants read and modify access to the monitored inbox.
  Use a **dedicated Gmail address** rather than your personal account.

---

## License

MIT

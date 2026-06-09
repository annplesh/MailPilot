# MailPilot

AI-powered Gmail monitoring bot for Telegram. Connects to a dedicated work inbox, scores every incoming email with Claude AI, and delivers urgent messages as instant alerts — everything else in a daily digest.

---

## What it does

MailPilot monitors a Gmail inbox continuously and routes each email based on an AI importance score (0–10):

- **Score 8–10** — instant Telegram alert sent immediately
- **Score 4–7** — added to a daily digest delivered at your chosen local time
- **Score 1–3** — moved to trash automatically and labeled in Gmail

You define what "important" means by providing keywords (supplier names, tech stack, client names). Claude uses them to personalise scoring for each user.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Bot framework | python-telegram-bot 22.7 |
| AI scoring | Anthropic Claude API — `claude-haiku-4-5-20251001` |
| Email access | Gmail API v1 via OAuth2 |
| Database | SQLite |
| Scheduling | APScheduler |
| Runtime | Python 3.14 |
| Config | python-dotenv |

AI parameters: `temperature=0.1`, `max_tokens=300`. Low temperature is intentional — email scoring is a classification task that requires consistent, deterministic output.

---

## Project Structure

```
mailpilot/
├── bot.py               # FSM states, all handlers, APScheduler digest jobs
├── ai_filter.py         # Claude API — email scoring and /help assistant
├── gmail_reader.py      # Gmail OAuth2, email fetching, auto-labeling
├── database.py          # All SQLite read/write operations
├── strings.py           # UI strings in English and Spanish
├── mailpilot_faq.txt    # FAQ context document used by /help
├── .env                 # Local secrets (never committed)
├── .env.example         # Template for required environment variables
├── promts/              # AI prompts log — full development history
└── tokens/              # Gmail OAuth tokens per user (never committed)
```

---

## FSM States

```
START  →  LANG  →  SETUP  →  ACTIVE
```

| State | Description |
|---|---|
| **START** | `/start` command. New users are shown a language selector. Returning users go directly to the commands menu. |
| **LANG** | Language selection: 🇬🇧 English or 🇪🇸 Español. Preference saved to database. Proceeds to SETUP automatically for new users. |
| **SETUP** | 4-step wizard: Gmail address → keywords → timezone → digest time. `allow_reentry=True` so active users can reconfigure at any time. |
| **ACTIVE** | Full monitoring mode. Inbox polled every 15 minutes. All commands available. |

---

## Commands

| Command | State | Description |
|---|---|---|
| `/start` | Any | Welcome message; shows language selector for new users |
| `/setup` | START, ACTIVE | Run the 4-step configuration wizard |
| `/status` | ACTIVE | Current settings and last-24h email counts |
| `/digest` | ACTIVE | Fetch inbox, score emails, and send digest immediately |
| `/ping` | Any | Confirm the bot is running |
| `/help` | Any | Ask a question about MailPilot — answered by Claude AI |
| `/reset` | Any | Clear `/help` conversation history |
| `/language` | Any | Change interface language (English / Spanish) |

`/digest`, `/status`, `/help`, `/reset`, and `/ping` are registered as standalone handlers outside the ConversationHandler so they work after a bot restart without requiring the user to send `/start` again.

---

## Gmail Auto-Labeling

After scoring each email, MailPilot creates and applies labels in Gmail so the bot's decisions are visible directly in the inbox:

| Score range | Gmail label |
|---|---|
| 8–10 | `MailPilot/Urgent` |
| 4–7 | `MailPilot/Digest` |
| 1–3 | `MailPilot/Spam` |

---

## Setup

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd mailpilot
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Fill in `.env`:

```env
TELEGRAM_BOT_TOKEN=        # from @BotFather
ANTHROPIC_API_KEY=         # from console.anthropic.com
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_DIR=tokens/
DATABASE_PATH=mailpilot.db
```

### 3. Set up Gmail OAuth credentials

1. Open [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Enable the **Gmail API** under APIs & Services → Library.
3. Create an **OAuth 2.0 Client ID** (application type: Desktop app) and download the JSON file.
4. Save it as `credentials.json` in the project root.
5. Add your Gmail address as a test user in the OAuth consent screen.

On first `/setup`, a browser window opens for Gmail authorisation. The resulting token is saved to `tokens/token_<telegram_id>.json` and refreshed automatically on subsequent runs.

### 4. Run

```bash
python bot.py
```

`mailpilot.db` is created automatically on first run. On restart, all active users are restored from the database and their daily digest jobs are rescheduled without requiring them to send `/start` again.

---

## Data Model

**Table: `users`**

| Column | Description |
|---|---|
| `telegram_id` | Primary key |
| `gmail_address` | Connected inbox |
| `filter_keywords` | JSON array of user-defined keywords |
| `digest_time` | Scheduled digest time (UTC, stored internally) |
| `language` | `"en"` or `"es"` (default: `"en"`) |
| `is_active` | Whether monitoring is enabled |
| `created_at`, `updated_at` | Timestamps |

**Table: `emails`**

| Column | Description |
|---|---|
| `message_id` | Gmail message ID — unique, used for deduplication |
| `subject`, `sender`, `received_at` | Email metadata |
| `ai_score`, `ai_reasoning` | Claude scoring output |
| `is_important`, `needs_alert` | Routing flags |
| `digest_sent` | Whether included in a sent digest |

---

## Future Plans

Based on the documented backlog in `promts/`:

- **Timezone feature completion** — AM/PM time input in `/setup` step 4 has a known input-parsing bug pending fix
- **Keywords display fix** — `/status` shows "Keywords: Keywords: ..." (prefix duplication bug, root cause identified, fix pending)
- **Multi-inbox support** — connect multiple Gmail accounts per user
- **Russian language** — third language option, deferred based on demand

---

## Never Commit

```
.env
credentials.json
tokens/
*.db
NOTES.md
```

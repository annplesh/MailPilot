# MailPilot ✈️

> AI-powered Gmail monitor that sends what matters to Telegram.

---

## What it does

MailPilot connects to a Gmail inbox, scores every incoming email with Claude AI (0–10), and routes results to Telegram based on the score:

- **Score ≥ 8** — instant Telegram alert
- **Score 4–7** — added to a daily digest sent at your chosen time
- **Score < 4** — filtered out silently

You define what "important" means by providing your own keywords. MailPilot uses them to personalise scoring for each user.

---

## How it works

**1. Connect Gmail**
Run `/setup` and authorise Gmail access via OAuth2. No password is stored — only a per-user token file.

**2. Set your keywords**
Tell the bot what to look for (e.g. `Python, backend, remote`). Keywords are passed to Claude alongside each email so scoring stays personalised even with a cached system prompt.

**3. Get alerts and digests**
High-priority emails arrive as instant Telegram messages. Everything else is batched into a daily digest at the time you choose.

---

## Commands

| Command   | Available in    | Description                                        |
|-----------|-----------------|----------------------------------------------------|
| `/start`  | Any state       | Welcome message; redirects to `/setup` if needed  |
| `/setup`  | START, ACTIVE   | 3-step wizard: Gmail address → keywords → time     |
| `/status` | ACTIVE          | Current settings and last-24 h email counts        |
| `/digest` | ACTIVE          | Fetch, score, and send digest immediately          |
| `/ping`   | Any state       | Confirm the bot is running                         |

---

## Tech stack

| Layer        | Technology                                      |
|--------------|-------------------------------------------------|
| Bot framework | python-telegram-bot 22.7 (async, ConversationHandler FSM) |
| AI scoring   | Anthropic Claude API — `claude-sonnet-4-6` with prompt caching |
| Email access | Gmail API via OAuth2 (`google-api-python-client`) |
| Storage      | SQLite — no ORM, explicit parameterised queries |
| Runtime      | Python 3.14                                     |

---

## Setup & run

### 1. Clone and install

```bash
git clone <repo-url>
cd mailpilot
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in `.env`:

```
TELEGRAM_BOT_TOKEN=...   # from @BotFather
ANTHROPIC_API_KEY=...    # from console.anthropic.com
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_DIR=.
DATABASE_PATH=mailpilot.db
DIGEST_TIME=09:00
LOG_LEVEL=INFO
```

### 3. Obtain Gmail credentials

1. Open [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Enable the **Gmail API** under APIs & Services → Library.
3. Create an **OAuth 2.0 Client ID** (Desktop app) and download the JSON file.
4. Save it as `credentials.json` in the project root (or update `GMAIL_CREDENTIALS_FILE`).

On first `/setup`, a browser window opens for Gmail authorisation. The resulting token is saved as `token_<telegram_id>.json` and refreshed automatically on subsequent runs.

### 4. Run

```bash
python bot.py
```

---

## Roadmap

- [ ] Multi-inbox support (multiple Gmail accounts per user)
- [ ] Web dashboard for email history
- [ ] Webhook mode for production deployment
- [ ] Docker image

## Goal

Write a complete README.md for MailPilot based on existing documentation.

## Prompt

Read all files in the prompts/ folder.
Based on their content, write a complete README.md for MailPilot.

README must include:

- Project description — MailPilot as an AI-powered Gmail monitoring bot
- Tech stack — Python, python-telegram-bot, Claude Haiku,
  Gmail OAuth2, SQLite, APScheduler
- Project structure — real file tree with all Python modules
- FSM states — START → LANG → SETUP → ACTIVE
- Setup instructions — pip install, .env setup, Gmail OAuth steps
- Commands overview — /start, /setup, /status, /digest,
  /help, /language, /ping, /reset
- Future plans — only what is documented in prompts/

Rules:

- Write only what is documented in prompts/
- No invented details, no placeholders
- No Next.js, no dashboard, no systemd — bot is not deployed yet
- No GPT comparison — not in documentation
- No invented case studies — use only real project context
- No deadlines — none are confirmed

Tone: professional, clear, in English.

## Status: ✅ DONE

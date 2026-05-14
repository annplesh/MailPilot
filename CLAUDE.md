# CLAUDE.md — MailPilot Project Instructions

## What is MailPilot

AI-powered email monitoring bot for freelancers.
Monitors a dedicated Gmail inbox, scores emails with Claude AI,
sends instant Telegram alerts for urgent messages and a daily digest for the rest.

## Stack

- Python 3.14
- python-telegram-bot 22.7
- Anthropic Claude API (claude-sonnet-4-20250514)
- Gmail API via OAuth2
- SQLite
- python-dotenv

## FSM States

- START (0) — welcome message, ask user to connect Gmail
- SETUP (1) — collect Gmail address, keywords, digest time
- ACTIVE (2) — monitoring mode, sending alerts and digest

## Scoring Logic

- Score 8–10 → instant Telegram alert
- Score 4–7 → added to daily digest
- Score 1–3 → moved to trash automatically

## File Responsibilities

- bot.py — FSM states, handlers, scheduler
- database.py — all SQLite read/write operations
- ai_filter.py — Claude API email scoring
- gmail_reader.py — Gmail OAuth2 + email reading

## Code Rules

- All comments in English
- Error handling in every function
- No hardcoded secrets — always use .env
- SQLite for all persistent data
- Handle unexpected user input gracefully

## Never Commit

- .env
- credentials.json
- tokens/
- \*.db
- NOTES.md

## Assignment Requirements

- [x] Minimum 2 FSM states — START → SETUP → ACTIVE
- [x] SQLite persistence — users and emails tables
- [x] .env + .env.example configured
- [ ] Unexpected input handling — fallback in all states
- [ ] Real result — instant alert or daily digest in Telegram

## Prompts Log

All AI prompts saved in /prompts folder:

- 01_architecture.md — project planning
- 02_v1_code.md — first working version
- 03_database.md — SQLite connection
- 04_fixes.md — user testing fixes

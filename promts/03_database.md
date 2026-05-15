# Prompt 03 — Database Persistence Verification

## Request sent to Claude AI

Verify that data persists after bot restart.

Steps to verify:

1. Run /setup in bot — enter Gmail, keywords, digest time
2. Stop bot (Ctrl+C)
3. Restart bot (python bot.py)
4. Check that user settings are saved in database

## Result

- Bot restarted successfully
- Active users loaded from database on startup
- Digest jobs rescheduled automatically for all active users
- Data persists between restarts ✅

## Database file

- mailpilot.db created automatically on first run
- Located in project root
- Protected by .gitignore (\*.db rule)

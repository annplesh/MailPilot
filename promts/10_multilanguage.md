# Prompt 10 — Multi-language Support (English + Spanish)

## Prompt 1 — Implementation plan

Show plan first, don't make changes yet.

Add multi-language support to MailPilot (English and Spanish).

Requirements:

1. Add language field to users table in database.py (default: "en")
2. After /start, ask new users to choose language with buttons:
   "🇬🇧 English" | "🇪🇸 Español"
3. Add /language command to change language at any time
4. All bot messages in start_handler, setup wizard, status, digest,
   ping, help, fallback — show in chosen language
5. Save language preference to database

Show plan only, no code changes.

## Prompt 2 — Implementation with edge case fixes

Accept the plan with these additional requirements:

1. Cache language in context.user_data at session start to avoid
   DB query on every handler call

2. In language_callback for new users — avoid double welcome message.
   After language selection just show language confirmation,
   then let user proceed to /setup naturally

3. If user sends /language during /setup wizard — show message
   "Please complete setup first" and return SETUP state unchanged

4. Architecture: STRINGS dict supports easy addition of new languages later

Apply all changes now.

## Prompt 3 — Add /language to commands list

In start_handler and fallback_handler, add /language to the commands list
in both "welcome back" and fallback messages.
Add after /reset:
"/language — cambiar idioma / change language"

No other changes.

## Prompt 4 — Show language selector in /setup if no language set

In setup_start handler, if user has no language set in database,
show language selection keyboard before starting setup wizard.
If language already set — proceed to setup as normal.

Additional requirement:
After language selection in language_callback, if user came from /setup
(no DB record), automatically start setup wizard immediately
without requiring user to send /setup again.
Use context.user_data["pending_setup"] = True flag to track this.

No other changes. Show plan first.

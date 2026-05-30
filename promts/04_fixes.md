# Prompt 04 — Fixes After Testing

## Bug 1 — APScheduler NoneType error ✅ FIXED

**Found during:** /setup step 3 testing
**Error:** AttributeError: 'NoneType' object has no attribute 'get_jobs_by_name'
**Fix applied:** Added None check before accessing job_queue in bot.py

## Bug 2 — Bot stops responding after failed OAuth ✅ FIXED

**Found during:** /digest testing with blocked Google account
**Fix needed:** Handle OAuth failure gracefully and send user a message instead of silently hanging.

## Bug 3 — No response feedback during /digest ✅ FIXED

**Found during:** testing /digest command
**Fix needed:**

- Send "⏳ Checking your inbox..." immediately when /digest is called
- Send error message if fetch fails with instructions to try again

## Bug 4 — Token file path constructed incorrectly ✅ FIXED

**Found during:** /digest testing
**Error:** Token file path included OAuth client ID instead of telegram_id
**Fix applied:** Fixed GMAIL_TOKEN_DIR in .env and updated gmail_reader.py

## Bug 5 — No auto-recovery after critical errors ✅ FIXED

**Found during:** testing
**Fix applied:** Implemented via \_fetch_with_retry() with 30s delay and one
retry, /ping command added, user error messages in digest_handler and
daily_digest_job.

## Bug 6 — JSON fences in Haiku response ✅ FIXED

**Found during:** model switch to claude-haiku
**Error:** Model wrapped JSON in `json` fences, raw JSON shown in Telegram

**Prompt used:**
In ai_filter.py, the model sometimes wraps JSON response in `json` fences.
Add explicit stripping of markdown fences before json.loads():

raw = response.content[0].text
raw = raw.strip()
if raw.startswith("`"):
    raw = re.sub(r'^`(?:json)?\n?', '', raw)
raw = re.sub(r'\n?```$', '', raw)

**Fix applied:** Added fence stripping in ai_filter.py before json.loads()

## Bug 7 — Bot ignores commands after restart without /start ✅ FIXED

**Found during:** live testing after bot restart
**Problem:** After bot restart, /digest, /status, /ping don't respond
until user sends /start first. FSM state is lost on restart.

**Prompt used:**
Fix Bug 7 — bot ignores commands after restart without /start.

After bot restart, active users in database cannot use /digest, /status,
/ping until they manually send /start. FSM state is lost on restart.

Fix: add /digest, /status, /help, /reset as standalone handlers
OUTSIDE the ConversationHandler, so they work regardless of FSM state.
Pattern already exists for /ping — use the same approach.

No other changes.
Show plan first.

## Bug 8 — AM/PM time format not accepted in /setup step 4 ⏳ PENDING

**Found during:** timezone feature testing

**Problem:** Bot rejects "9:00 AM" format despite regex seemingly correct.
Debug needed to see what text is actually received.

**Prompt used:**
In \_setup_step4_localtime in bot.py, add debug print at start of function:
print(f"DEBUG time input: {repr(text)}")
No other changes.

## Bug 8 — Keywords duplicated in /status ⏳ PENDING

**Found during:** post-migration testing
**Problem:** /status shows "Keywords: Keywords: React..." — word duplicated
**Cause:** keywords stored in DB already contains "Keywords: " prefix

**Prompt used:**
Attached: bot.py, strings.py, database.py

Bug: /status shows "Keywords: Keywords: React..." — the word "Keywords" is duplicated.

Show plan first, no code.

1. Find where /status response is built
2. Find where keywords are saved to DB and retrieved
3. Identify where the duplication occurs
4. Propose the minimal fix — one line change only

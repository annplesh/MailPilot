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

## Bug 7 — Bot ignores commands after restart without /start ⏳ PENDING

**Found during:** testing after bot restart
**Problem:** After bot restart, /digest and /ping don't respond
until user sends /start first. FSM state is lost on restart.

**Fix needed:**

- On restart, restore FSM state from database for active users
- Or: allow /digest and /ping outside FSM conversation handler

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

## Bug 5 — No auto-recovery after critical errors ⏳ PENDING

**Found during:** testing

**Fix needed:**

- When bot encounters critical error — wait 30 seconds and retry
- Add /ping command to check if bot is alive
- If retry fails — send user clear message to run /setup

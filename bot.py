import os
import asyncio
import html
import logging
import re
from datetime import time, timezone

from dotenv import load_dotenv
from google.auth.exceptions import RefreshError
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import database
import gmail_reader

logger = logging.getLogger(__name__)

# FSM state constants
START  = 0
SETUP  = 1
ACTIVE = 2


# =============================================================================
# /start
# =============================================================================

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user    = update.effective_user
    db_user = database.get_user(user.id)

    if db_user and db_user["is_active"]:
        await update.message.reply_text(
            f"Welcome back, {user.first_name}! Your Gmail digest is active.\n\n"
            "Use /status to see your settings or /digest to get today's important emails now."
        )
        return ACTIVE

    await update.message.reply_text(
        f"Hi {user.first_name}! I'm MailPilot ✈️\n\n"
        "I monitor your Gmail inbox and:\n"
        "\U0001f534 Send instant alerts for urgent emails\n"
        "\U0001f4cb Send a daily digest of important messages\n"
        "\U0001f5d1️ Filter out noise automatically\n\n"
        "You define what matters — set your own keywords.\n\n"
        "Commands:\n"
        "/setup — connect Gmail and configure filters\n"
        "/status — view your settings\n"
        "/digest — check inbox now\n"
        "/ping — check if bot is alive\n\n"
        "Run /setup to get started."
    )
    return START


# =============================================================================
# /setup — entry point + 3-step wizard
# =============================================================================

async def setup_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["setup_step"] = 1
    await update.message.reply_text(
        "Let's get you set up! (Step 1 of 3)\n\n"
        "Please send the Gmail address you want to monitor."
    )
    return SETUP


async def setup_dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Route incoming text to the correct wizard step."""
    step = context.user_data.get("setup_step", 1)
    if step == 1:
        return await _setup_step1_gmail(update, context)
    if step == 2:
        return await _setup_step2_keywords(update, context)
    return await _setup_step3_time(update, context)


async def _setup_step1_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip().lower()
    if not text.endswith("@gmail.com"):
        await update.message.reply_text(
            "That doesn't look like a Gmail address.\n"
            "Please try again (e.g. yourname@gmail.com)."
        )
        return SETUP

    context.user_data["gmail_address"]  = text
    context.user_data["setup_step"]     = 2
    await update.message.reply_text(
        "Step 2 of 3\n\n"
        "Enter the keywords I should look for, separated by commas.\n"
        "Example: Python, backend, remote, senior"
    )
    return SETUP


async def _setup_step2_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keywords = [kw.strip() for kw in update.message.text.split(",") if kw.strip()]
    if not keywords:
        await update.message.reply_text(
            "Please enter at least one keyword (e.g. Python)."
        )
        return SETUP

    context.user_data["keywords"]   = keywords
    context.user_data["setup_step"] = 3
    await update.message.reply_text(
        "Step 3 of 3\n\n"
        "What time should I send your daily digest? (UTC)\n"
        "Format: HH:MM — e.g. 09:00"
    )
    return SETUP


async def _setup_step3_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()

    if not re.match(r"^\d{2}:\d{2}$", text):
        await update.message.reply_text("Please use HH:MM format (e.g. 09:00).")
        return SETUP

    hh, mm = int(text[:2]), int(text[3:])
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        await update.message.reply_text(
            "Invalid time — hours must be 00–23 and minutes 00–59 (e.g. 09:00)."
        )
        return SETUP

    telegram_id   = update.effective_user.id
    gmail_address = context.user_data["gmail_address"]
    keywords      = context.user_data["keywords"]

    database.upsert_user(
        telegram_id=telegram_id,
        gmail_address=gmail_address,
        filter_keywords=keywords,
        digest_time=text,
        is_active=1,
    )

    time_obj = time(hour=hh, minute=mm, tzinfo=timezone.utc)
    _schedule_daily_digest(context.application, telegram_id, time_obj)

    await update.message.reply_text(
        f"Setup complete! I'll check your Gmail every day and send important "
        f"important emails at {text} UTC.\n\n"
        "Use /status to review your settings or /digest to trigger a digest right now."
    )
    context.user_data.clear()
    return ACTIVE


# =============================================================================
# /ping
# =============================================================================

async def ping_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("\U0001f7e2 I'm alive and monitoring your inbox.")


# =============================================================================
# /status
# =============================================================================

async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id
    user = database.get_user(telegram_id)

    if not user or not user["is_active"]:
        await update.message.reply_text("Setup required. Run /setup first.")
        return

    stats       = database.get_recent_email_stats(telegram_id, hours=24)
    kw_display  = ", ".join(user["filter_keywords"]) if user["filter_keywords"] else "none set"

    await update.message.reply_text(
        "MailPilot Status\n\n"
        f"Gmail: {user['gmail_address']}\n"
        f"Keywords: {kw_display}\n"
        f"Daily digest: {user['digest_time']} UTC\n\n"
        f"Last 24 h: {stats['total']} emails received, "
        f"{stats['important']} marked important\n\n"
        "Use /digest to get your current digest now."
    )


# =============================================================================
# /digest — manual trigger
# =============================================================================

async def digest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id
    user = database.get_user(telegram_id)

    if not user or not user["is_active"]:
        await update.message.reply_text("Setup required. Run /setup first.")
        return

    await update.message.reply_text("⏳ Checking your inbox...")

    try:
        await _fetch_with_retry(telegram_id, user["filter_keywords"])
        alert_count  = await _send_alerts(telegram_id, context.bot)
        digest_count = await _send_digest(telegram_id, context.bot)
        total        = alert_count + digest_count
    except RefreshError:
        await update.message.reply_text(
            "❌ Could not connect to Gmail. Please run /setup again."
        )
        return
    except Exception as e:
        logger.error("digest failed for user %s: %s", telegram_id, e)
        await update.message.reply_text(
            "❌ Could not fetch emails. Try /setup to reconnect."
        )
        return

    if total == 0:
        await update.message.reply_text("\U0001f4ed No new important emails.")
    else:
        await update.message.reply_text(f"Digest sent — {total} important email(s).")


# =============================================================================
# Scheduled daily job
# =============================================================================

async def daily_digest_job(context: CallbackContext) -> None:
    telegram_id = context.job.data
    user = database.get_user(telegram_id)

    if not user or not user["is_active"]:
        logger.info("Skipping daily digest for inactive user %s", telegram_id)
        return

    try:
        await _fetch_with_retry(telegram_id, user["filter_keywords"])
    except RefreshError:
        await context.bot.send_message(
            chat_id=telegram_id,
            text="Your Gmail authorization has expired. Run /setup to reconnect.",
        )
        return
    except Exception as e:
        logger.error("Daily fetch failed for user %s after retry: %s", telegram_id, e)
        await context.bot.send_message(
            chat_id=telegram_id,
            text="❌ Please run /setup to reconnect.",
        )
        return

    alert_count  = await _send_alerts(telegram_id, context.bot)
    digest_count = await _send_digest(telegram_id, context.bot)

    logger.info(
        "Daily digest sent to %s — %d alert(s), %d digest email(s)",
        telegram_id, alert_count, digest_count,
    )


# =============================================================================
# Fallback
# =============================================================================

async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Sorry, I didn't understand that.\n\n"
        "Available commands:\n"
        "/start  — restart the bot\n"
        "/setup  — connect Gmail and configure filters\n"
        "/status — view your settings and last 24 h stats\n"
        "/digest — get today's important emails now\n"
        "/ping   — check the bot is running"
    )


# =============================================================================
# Private helpers
# =============================================================================

async def _fetch_with_retry(telegram_id: int, keywords: list[str]) -> None:
    """Call fetch_and_store_emails; on transient failure wait 30 s and retry once.

    RefreshError is re-raised immediately — retrying a revoked token is pointless.
    Any exception on the second attempt propagates to the caller.
    """
    try:
        await asyncio.to_thread(
            gmail_reader.fetch_and_store_emails, telegram_id, keywords
        )
    except RefreshError:
        raise
    except Exception as e:
        logger.warning("Fetch failed for user %s, retrying in 30 s: %s", telegram_id, e)
        await asyncio.sleep(30)
        await asyncio.to_thread(
            gmail_reader.fetch_and_store_emails, telegram_id, keywords
        )


def _schedule_daily_digest(application: Application, telegram_id: int, digest_time: time) -> None:
    if application.job_queue is None:
        logger.warning("JobQueue not available — digest job not scheduled for user %s", telegram_id)
        return

    # Remove the existing job for this user before adding a new one.
    # Handles /setup re-entry where the user changes their digest time.
    for job in application.job_queue.get_jobs_by_name(f"digest_{telegram_id}"):
        job.schedule_removal()

    application.job_queue.run_daily(
        callback=daily_digest_job,
        time=digest_time,
        name=f"digest_{telegram_id}",
        data=telegram_id,
    )
    logger.info("Scheduled daily digest for user %s at %s UTC", telegram_id, digest_time)


async def _send_alerts(telegram_id: int, bot) -> int:
    """Send instant alert messages for high-scoring emails (needs_alert=1).

    Marks each alerted email as digest_sent so it does not appear again
    in the regular daily digest. Returns the number of alerts sent.
    """
    unsent = database.get_unsent_emails(telegram_id)
    alerts = [e for e in unsent if e["needs_alert"]]

    for e in alerts:
        text = (
            "<b>⚠️ Urgent email</b>\n\n"
            f"<b>From:</b> {html.escape(e['sender'] or '')}\n"
            f"<b>Subject:</b> {html.escape(e['subject'] or '')}\n"
            f"<b>Score:</b> {int(e['ai_score'])}/10\n"
            f"<i>{html.escape(e['ai_reasoning'] or '')}</i>"
        )
        await bot.send_message(chat_id=telegram_id, text=text, parse_mode=ParseMode.HTML)

    if alerts:
        database.mark_digest_sent([e["id"] for e in alerts])

    return len(alerts)


async def _send_digest(telegram_id: int, bot) -> int:
    """Send digest-priority emails (is_important=1, digest_sent=0).

    Each email is sent as a separate Telegram message to stay within
    the 4 096-character limit. Returns the number of emails sent.
    """
    unsent = database.get_unsent_emails(telegram_id)

    if not unsent:
        return 0

    # Header on the first email message to give context.
    header = f"<b>MailPilot Digest</b> — {len(unsent)} important email(s)\n\n"

    for idx, e in enumerate(unsent):
        prefix = header if idx == 0 else ""
        text = (
            f"{prefix}"
            f"<b>{html.escape(e['subject'] or '(no subject)')}</b>\n"
            f"From: {html.escape(e['sender'] or '')}\n"
            f"Score: {int(e['ai_score'])}/10\n"
            f"<i>{html.escape(e['ai_reasoning'] or '')}</i>"
        )
        await bot.send_message(chat_id=telegram_id, text=text, parse_mode=ParseMode.HTML)

    database.mark_digest_sent([e["id"] for e in unsent])
    return len(unsent)


# =============================================================================
# Application bootstrap
# =============================================================================

def main() -> None:
    load_dotenv()

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    database.init_db()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in .env")

    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start_handler),
            CommandHandler("setup", setup_start),
        ],
        states={
            START: [
                CommandHandler("setup", setup_start),
            ],
            SETUP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, setup_dispatch),
            ],
            ACTIVE: [
                CommandHandler("status", status_handler),
                CommandHandler("digest", digest_handler),
                CommandHandler("setup",  setup_start),   # allow reconfiguration
            ],
        },
        fallbacks=[
            CommandHandler("ping", ping_handler),
            MessageHandler(filters.ALL, fallback_handler),
        ],
        allow_reentry=True,
    )
    application.add_handler(conv_handler)

    # Re-register digest jobs for all active users so no one misses their
    # digest after a bot crash or redeploy.
    for user in database.get_all_active_users():
        try:
            hh, mm   = map(int, user["digest_time"].split(":"))
            time_obj = time(hour=hh, minute=mm, tzinfo=timezone.utc)
            _schedule_daily_digest(application, user["telegram_id"], time_obj)
        except Exception as e:
            logger.error(
                "Failed to reschedule digest for user %s: %s",
                user["telegram_id"], e,
            )

    logger.info("MailPilot is running. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

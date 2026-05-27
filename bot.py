import os
import asyncio
import html
import logging
import re
from datetime import time, timezone

from dotenv import load_dotenv
from google.auth.exceptions import RefreshError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import ai_filter
import database
import gmail_reader
from strings import t

logger = logging.getLogger(__name__)

# FSM state constants
START  = 0
SETUP  = 1
ACTIVE = 2
LANG   = 3

HELP_HISTORY_KEY = "help_history"
MAX_HELP_HISTORY = 10  # max messages stored (5 exchanges)


# =============================================================================
# Language helpers
# =============================================================================

def get_lang(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Return the user's language, caching in context.user_data to avoid repeat DB hits."""
    if "language" not in context.user_data:
        db_user = database.get_user(user_id)
        context.user_data["language"] = (db_user or {}).get("language") or "en"
    return context.user_data["language"]


def _language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
    ]])


# =============================================================================
# /start
# =============================================================================

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user    = update.effective_user
    db_user = database.get_user(user.id)

    if db_user and db_user["is_active"]:
        lang = get_lang(user.id, context)
        await update.message.reply_text(t(lang, "welcome_back", name=user.first_name))
        return ACTIVE

    # New (or inactive) user — ask language first
    await update.message.reply_text(
        t("en", "choose_language"),
        reply_markup=_language_keyboard(),
    )
    return LANG


# =============================================================================
# Language selection
# =============================================================================

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle inline button press for language selection."""
    query = update.callback_query
    await query.answer()

    lang    = query.data.split("_")[1]   # "lang_en" → "en"
    user_id = update.effective_user.id
    context.user_data["language"] = lang

    db_user = database.get_user(user_id)
    if db_user and db_user["is_active"]:
        database.set_user_language(user_id, lang)
        await query.edit_message_text(t(lang, "language_set"))
        return ACTIVE

    # New or inactive user — confirm language, let them proceed to /setup
    await query.edit_message_text(t(lang, "language_set_new"))
    return START


async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /language command for active or START-state users."""
    lang = get_lang(update.effective_user.id, context)
    await update.message.reply_text(
        t(lang, "choose_language"),
        reply_markup=_language_keyboard(),
    )
    return LANG


async def language_during_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /language command while setup wizard is in progress."""
    lang = get_lang(update.effective_user.id, context)
    await update.message.reply_text(t(lang, "setup_in_progress"))
    return SETUP


# =============================================================================
# /setup — entry point + 3-step wizard
# =============================================================================

async def setup_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_lang(update.effective_user.id, context)
    context.user_data["setup_step"] = 1
    await update.message.reply_text(t(lang, "setup_step1"))
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
    lang = get_lang(update.effective_user.id, context)
    text = update.message.text.strip().lower()
    if not text.endswith("@gmail.com"):
        await update.message.reply_text(t(lang, "setup_step1_invalid"))
        return SETUP

    context.user_data["gmail_address"]  = text
    context.user_data["setup_step"]     = 2
    await update.message.reply_text(t(lang, "setup_step2"))
    return SETUP


async def _setup_step2_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang     = get_lang(update.effective_user.id, context)
    keywords = [kw.strip() for kw in update.message.text.split(",") if kw.strip()]
    if not keywords:
        await update.message.reply_text(t(lang, "setup_step2_empty"))
        return SETUP

    context.user_data["keywords"]   = keywords
    context.user_data["setup_step"] = 3
    await update.message.reply_text(t(lang, "setup_step3"))
    return SETUP


async def _setup_step3_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_lang(update.effective_user.id, context)
    text = update.message.text.strip()

    if not re.match(r"^\d{2}:\d{2}$", text):
        await update.message.reply_text(t(lang, "setup_step3_invalid_format"))
        return SETUP

    hh, mm = int(text[:2]), int(text[3:])
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        await update.message.reply_text(t(lang, "setup_step3_invalid_range"))
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
        language=lang,
    )

    time_obj = time(hour=hh, minute=mm, tzinfo=timezone.utc)
    _schedule_daily_digest(context.application, telegram_id, time_obj)

    await update.message.reply_text(t(lang, "setup_complete", time=text))
    context.user_data.clear()
    return ACTIVE


# =============================================================================
# /ping
# =============================================================================

async def ping_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(update.effective_user.id, context)
    await update.message.reply_text(t(lang, "ping"))


# =============================================================================
# /status
# =============================================================================

async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id
    lang        = get_lang(telegram_id, context)
    user        = database.get_user(telegram_id)

    if not user or not user["is_active"]:
        await update.message.reply_text(t(lang, "setup_required"))
        return

    stats      = database.get_recent_email_stats(telegram_id, hours=24)
    kw_display = ", ".join(user["filter_keywords"]) if user["filter_keywords"] else "—"

    await update.message.reply_text(t(
        lang, "status_body",
        gmail=user["gmail_address"],
        keywords=kw_display,
        time=user["digest_time"],
        total=stats["total"],
        important=stats["important"],
    ))


# =============================================================================
# /digest — manual trigger
# =============================================================================

async def digest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id
    lang        = get_lang(telegram_id, context)
    user        = database.get_user(telegram_id)

    if not user or not user["is_active"]:
        await update.message.reply_text(t(lang, "setup_required"))
        return

    await update.effective_chat.send_action("typing")
    await update.message.reply_text(t(lang, "checking_inbox"))

    try:
        await _fetch_with_retry(telegram_id, user["filter_keywords"])
        alert_count  = await _send_alerts(telegram_id, context.bot, lang)
        digest_count = await _send_digest(telegram_id, context.bot, lang)
        total        = alert_count + digest_count
    except RefreshError:
        await update.message.reply_text(t(lang, "gmail_auth_error"))
        return
    except Exception as e:
        logger.error("digest failed for user %s: %s", telegram_id, e)
        await update.message.reply_text(t(lang, "fetch_error"))
        return

    if total == 0:
        await update.message.reply_text(t(lang, "no_emails"))
    else:
        await update.message.reply_text(t(lang, "digest_sent", total=total))


# =============================================================================
# Scheduled daily job
# =============================================================================

async def daily_digest_job(context: CallbackContext) -> None:
    telegram_id = context.job.data
    user        = database.get_user(telegram_id)

    if not user or not user["is_active"]:
        logger.info("Skipping daily digest for inactive user %s", telegram_id)
        return

    lang = user.get("language") or "en"

    try:
        await _fetch_with_retry(telegram_id, user["filter_keywords"])
    except RefreshError:
        await context.bot.send_message(
            chat_id=telegram_id,
            text=t(lang, "gmail_expired"),
        )
        return
    except Exception as e:
        logger.error("Daily fetch failed for user %s after retry: %s", telegram_id, e)
        await context.bot.send_message(
            chat_id=telegram_id,
            text=t(lang, "reconnect_error"),
        )
        return

    alert_count  = await _send_alerts(telegram_id, context.bot, lang)
    digest_count = await _send_digest(telegram_id, context.bot, lang)

    logger.info(
        "Daily digest sent to %s — %d alert(s), %d digest email(s)",
        telegram_id, alert_count, digest_count,
    )


# =============================================================================
# 15-minute polling job
# =============================================================================

async def polling_job(context: CallbackContext) -> None:
    for user in database.get_all_active_users():
        telegram_id = user["telegram_id"]
        lang        = user.get("language") or "en"
        try:
            await _fetch_with_retry(telegram_id, user["filter_keywords"])
        except RefreshError:
            await context.bot.send_message(
                chat_id=telegram_id,
                text=t(lang, "gmail_expired"),
            )
            continue
        except Exception as e:
            logger.warning("Polling fetch failed for user %s: %s", telegram_id, e)
            continue

        alert_count = await _send_alerts(telegram_id, context.bot, lang)
        if alert_count:
            logger.info(
                "Polling: sent %d alert(s) to user %s", alert_count, telegram_id
            )


# =============================================================================
# /help and /reset
# =============================================================================

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang     = get_lang(update.effective_user.id, context)
    question = " ".join(context.args or []).strip()
    if not question:
        await update.message.reply_text(t(lang, "help_no_question"))
        return

    history = context.user_data.get(HELP_HISTORY_KEY, [])
    history.append({"role": "user", "content": question})

    await update.effective_chat.send_action("typing")

    try:
        chunks = await asyncio.to_thread(ai_filter.search_knowledge_base, question)
        answer = await asyncio.to_thread(ai_filter.answer_help_question, history, chunks)
    except Exception as e:
        logger.error("help AI error for user %s: %s", update.effective_user.id, e)
        await update.message.reply_text(t(lang, "help_ai_error"))
        return

    history.append({"role": "assistant", "content": answer})
    context.user_data[HELP_HISTORY_KEY] = history[-MAX_HELP_HISTORY:]

    await update.message.reply_text(answer)


async def reset_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(update.effective_user.id, context)
    context.user_data.pop(HELP_HISTORY_KEY, None)
    await update.message.reply_text(t(lang, "history_cleared"))


# =============================================================================
# Fallback
# =============================================================================

async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(update.effective_user.id, context)
    await update.message.reply_text(t(lang, "unknown_command"))


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


async def _send_alerts(telegram_id: int, bot, lang: str = "en") -> int:
    """Send instant alert messages for high-scoring emails (needs_alert=1).

    Marks each alerted email as digest_sent so it does not appear again
    in the regular daily digest. Returns the number of alerts sent.
    """
    unsent = database.get_unsent_emails(telegram_id)
    alerts = [e for e in unsent if e["needs_alert"]]

    for e in alerts:
        text = (
            f"<b>{t(lang, 'alert_header')}</b>\n\n"
            f"<b>{t(lang, 'from_label')}:</b> {html.escape(e['sender'] or '')}\n"
            f"<b>{t(lang, 'subject_label')}:</b> {html.escape(e['subject'] or '')}\n"
            f"<b>{t(lang, 'score_label')}:</b> {int(e['ai_score'])}/10\n"
            f"<i>{html.escape(e['ai_reasoning'] or '')}</i>"
        )
        await bot.send_message(chat_id=telegram_id, text=text, parse_mode=ParseMode.HTML)

    if alerts:
        database.mark_digest_sent([e["id"] for e in alerts])

    return len(alerts)


async def _send_digest(telegram_id: int, bot, lang: str = "en") -> int:
    """Send digest-priority emails (is_important=1, digest_sent=0).

    Each email is sent as a separate Telegram message to stay within
    the 4 096-character limit. Returns the number of emails sent.
    """
    unsent = database.get_unsent_emails(telegram_id)

    if not unsent:
        return 0

    # Header on the first email message to give context.
    header = f"<b>{t(lang, 'digest_title', count=len(unsent))}</b>\n\n"

    for idx, e in enumerate(unsent):
        prefix = header if idx == 0 else ""
        text = (
            f"{prefix}"
            f"<b>{html.escape(e['subject'] or '(no subject)')}</b>\n"
            f"{t(lang, 'from_label')}: {html.escape(e['sender'] or '')}\n"
            f"{t(lang, 'score_label')}: {int(e['ai_score'])}/10\n"
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
            LANG: [
                CallbackQueryHandler(language_callback, pattern="^lang_"),
            ],
            START: [
                CommandHandler("setup", setup_start),
            ],
            SETUP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, setup_dispatch),
                CommandHandler("language", language_during_setup),
            ],
            ACTIVE: [
                CommandHandler("status",   status_handler),
                CommandHandler("digest",   digest_handler),
                CommandHandler("setup",    setup_start),
                CommandHandler("language", language_handler),
            ],
        },
        fallbacks=[
            CommandHandler("ping",     ping_handler),
            CommandHandler("help",     help_handler),
            CommandHandler("reset",    reset_handler),
            CommandHandler("language", language_handler),
            CallbackQueryHandler(language_callback, pattern="^lang_"),
            MessageHandler(filters.ALL, fallback_handler),
        ],
        allow_reentry=True,
    )
    application.add_handler(conv_handler)

    # Standalone fallbacks so commands work after restart (FSM state lost on restart)
    application.add_handler(CommandHandler("ping",     ping_handler))
    application.add_handler(CommandHandler("help",     help_handler))
    application.add_handler(CommandHandler("reset",    reset_handler))
    application.add_handler(CommandHandler("status",   status_handler))
    application.add_handler(CommandHandler("digest",   digest_handler))
    application.add_handler(CommandHandler("language", language_handler))
    application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))

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

    if application.job_queue is not None:
        application.job_queue.run_repeating(
            callback=polling_job,
            interval=15 * 60,
            first=10,
            name="polling",
        )
        logger.info("Polling job scheduled every 15 minutes")

    logger.info("MailPilot is running. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

import os
import base64
import email
import email.utils
import re
import logging
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import database
import ai_filter
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]

CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
GMAIL_TOKEN_DIR  = os.getenv("GMAIL_TOKEN_DIR", ".")
MAX_MESSAGES     = 50


# =============================================================================
# PUBLIC API
# =============================================================================

def authenticate(telegram_id: int):
    """Return an authenticated Gmail API service object for the given user."""
    token_path = Path(GMAIL_TOKEN_DIR) / f"token_{telegram_id}.json"
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            token_path.write_text(creds.to_json())
            logger.info("Token refreshed for user %s", telegram_id)
        except RefreshError:
            logger.warning("Token refresh failed for user %s — deactivating", telegram_id)
            token_path.unlink(missing_ok=True)
            database.deactivate_user(telegram_id)
            raise

    if not creds or not creds.valid:
        try:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Gmail credentials file not found: {CREDENTIALS_FILE!r}. "
                "Download credentials.json from Google Cloud Console. "
                "See README.md for instructions."
            )
        creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())
        logger.info("New token saved for user %s", telegram_id)

    return build("gmail", "v1", credentials=creds)


def fetch_and_store_emails(telegram_id: int, user_keywords: list[str]) -> int:
    """Fetch unread Gmail messages, score them, store results. Returns count of new rows."""
    service = authenticate(telegram_id)

    message_ids = _fetch_unread_message_ids(service)
    if not message_ids:
        logger.info("No new messages for user %s", telegram_id)
        return 0

    new_count = 0
    for message_id in message_ids:
        detail = _get_message_detail(service, message_id)
        if detail is None:
            continue

        try:
            score_result = ai_filter.score_email(
                subject=detail["subject"],
                body=detail["body"],
                keywords=user_keywords,
            )
        except ai_filter.anthropic.RateLimitError:
            # ai_filter already slept 60 s; stop the loop to avoid hammering the API.
            logger.warning("Rate limit reached for user %s — stopping fetch early", telegram_id)
            break

        inserted = database.insert_email(
            user_id=telegram_id,
            message_id=message_id,
            sender=detail["sender"],
            subject=detail["subject"],
            received_at=detail["received_at"],
            ai_score=score_result["score"],
            ai_reasoning=score_result["reasoning"],
        )

        # Mark as read regardless of score so the inbox stays clean.
        _mark_as_read(service, message_id)

        if inserted:
            new_count += 1

    logger.info("Stored %d new email(s) for user %s", new_count, telegram_id)
    return new_count


# =============================================================================
# PRIVATE HELPERS
# =============================================================================

def _fetch_unread_message_ids(service) -> list[str]:
    """Return a list of Gmail message IDs for unread inbox messages."""
    try:
        result = service.users().messages().list(
            userId="me",
            labelIds=["INBOX", "UNREAD"],
            maxResults=MAX_MESSAGES,
        ).execute()
        return [msg["id"] for msg in result.get("messages", [])]
    except HttpError as e:
        logger.error("Failed to list messages: %s", e)
        return []


def _get_message_detail(service, message_id: str) -> dict | None:
    """Fetch and parse a single Gmail message. Returns normalised dict or None on error."""
    try:
        msg = service.users().messages().get(
            userId="me", id=message_id, format="full"
        ).execute()
    except HttpError as e:
        logger.warning("Failed to fetch message %s: %s", message_id, e)
        return None

    payload = msg.get("payload", {})

    # Parse headers into a lookup dict.
    headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

    sender  = headers.get("From", "")
    subject = headers.get("Subject", "")

    raw_date = headers.get("Date", "")
    received_at = _parse_date(raw_date)

    body = _extract_body(payload)

    return {
        "sender":      sender,
        "subject":     subject,
        "received_at": received_at,
        "body":        body,
    }


def _parse_date(raw_date: str) -> str:
    """Convert an RFC-2822 Date header to ISO-8601 UTC string."""
    if not raw_date:
        return ""
    try:
        dt = email.utils.parsedate_to_datetime(raw_date)
        return dt.isoformat()
    except Exception:
        return raw_date  # store raw if parsing fails


def _extract_body(payload: dict) -> str:
    """Recursively extract plain-text body from a Gmail message payload."""
    mime_type = payload.get("mimeType", "")

    if mime_type.startswith("multipart/"):
        # Prefer text/plain; fall back to text/html.
        parts = payload.get("parts", [])
        plain = next((p for p in parts if p.get("mimeType") == "text/plain"), None)
        html  = next((p for p in parts if p.get("mimeType") == "text/html"), None)
        chosen = plain or html
        if chosen:
            return _extract_body(chosen)
        # Recurse into nested multipart parts.
        for part in parts:
            text = _extract_body(part)
            if text:
                return text
        return ""

    data = payload.get("body", {}).get("data")
    if not data:
        return ""

    decoded = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")

    # Strip HTML if needed.
    if "<html" in decoded.lower() or decoded.lstrip().startswith("<"):
        decoded = re.sub(r"<[^>]+>", " ", decoded)
        decoded = re.sub(r"\s+", " ", decoded).strip()

    return decoded


def _mark_as_read(service, message_id: str) -> None:
    """Remove the UNREAD label from a Gmail message."""
    try:
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()
    except HttpError as e:
        # Non-fatal — message was already processed and stored.
        logger.warning("Failed to mark message %s as read: %s", message_id, e)

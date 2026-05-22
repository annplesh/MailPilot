# MailPilot — Project Specification

**Client:** Small import company, LATAM (5–15 employees)
**Project:** AI-powered email monitoring bot

---

## 1. Task Description

The client receives 50–100 emails per day from suppliers, logistics companies,
and customs brokers. Manually reviewing this volume of mail throughout the day
creates a risk of missing time-sensitive messages — delayed responses to urgent
supplier requests can result in shipment holds, missed deadlines, or lost orders.

MailPilot is a Telegram bot that monitors the client's dedicated Gmail inbox
continuously, evaluates each incoming email by importance using AI, and routes
it to the client's Telegram account. Emails identified as urgent are delivered
as instant notifications. All other business emails are collected and sent as a
single daily summary at a time chosen by the client. Promotional content, spam,
and messages unrelated to the business are filtered out automatically and
generate no notifications.

The client controls what counts as "important" by providing their own keywords —
supplier names, product categories, logistics terms, or any other relevant
phrases. No technical knowledge is required to operate the system. All setup and
day-to-day interaction happen through a simple Telegram chat interface.

---

## 2. Scope — What Is Included

- Secure connection to one Gmail inbox via Google OAuth2 (no password stored)
- AI scoring of every incoming email on a 0–10 importance scale
- Instant Telegram notification for emails scoring 8 or above
- Daily digest of emails scoring 4–7, delivered at a client-chosen time (UTC)
- Automatic suppression of emails scoring below 4 (spam, irrelevant content)
- User-defined keywords for personalised scoring (supplier names, product codes,
  logistics terms, etc.)
- Bot commands accessible from Telegram:
  - /setup — connect Gmail and configure keywords and digest time
  - /digest — request today's digest immediately on demand
  - /status — view current settings and last-24h email summary
  - /ping — confirm the bot is running
  - /help — ask questions about how the bot works
- Email analysis in any language (Spanish, English, Portuguese)
- Automatic retry on transient errors; Telegram notification if Gmail
  reauthorisation is required

---

## 3. Scope — What Is NOT Included

- **Sending, replying to, or forwarding emails** — the system reads and
  notifies only; it does not write or send anything on the client's behalf
- **Multiple Gmail accounts** — one inbox per configured user; monitoring
  additional accounts requires a separate setup
- **Non-Gmail email providers** — Outlook, Yahoo, corporate Exchange, and
  other providers are not supported in this version
- **Web dashboard or mobile app** — Telegram is the only interface; there is
  no separate website, portal, or native app
- **CRM or task-management integration** — the bot delivers email summaries
  to Telegram and does not connect to HubSpot, Monday, Trello, or similar tools
- **Archiving, labelling, or organising emails inside Gmail** — the inbox
  structure is not modified beyond marking emails as read after processing

---

## 4. Acceptance Criteria

1. **Urgent email delivery.** An email from a monitored inbox that contains a
   configured keyword receives a score of 8 or higher and generates a Telegram
   notification within 5 minutes of receipt.

2. **Spam filtering.** A bulk promotional email (newsletter, platform
   announcement, unsubscribe confirmation) receives a score of 3 or lower and
   generates no Telegram notification.

3. **Daily digest.** The digest is delivered within 10 minutes of the
   configured time and contains all emails scored 4–7 since the previous digest,
   each showing sender, subject, score, and a one-sentence AI summary.

4. **Settings visibility.** Running /status returns the correct Gmail address,
   active keywords, digest time, and 24-hour email count without error.

5. **Gmail reconnection.** When Gmail authorisation expires or is revoked, the
   bot sends a Telegram notification and prompts the user to reconnect via
   /setup. The reconnection process completes in one /setup session.

6. **Keyword update.** Running /setup with an updated keyword list takes effect
   immediately — emails fetched in the same session reflect the new keywords.

7. **Resilience after errors.** If a Gmail fetch fails, the bot retries
   automatically once. If the retry also fails, the user receives a clear
   Telegram message and the bot continues operating normally.

---

## 5. Boundaries of Responsibility — AI-Specific Limitations

**Scoring accuracy is probabilistic, not guaranteed.**
The AI model evaluates each email based on its content, keywords, and language
patterns. It may occasionally classify a routine message as urgent or fail to
flag a genuinely time-sensitive one. No commitment to 100% accuracy is made,
and the system is intended as a notification aid, not a guaranteed alert system.

**The system depends on third-party services.**
MailPilot relies on Gmail API (Google), Telegram Bot API, and Anthropic Claude
API. Downtime, rate limits, or policy changes on any of these platforms are
outside the scope of this project and may temporarily affect availability.

**The AI does not understand business relationships.**
The model identifies urgency based on keywords and standard language signals.
It cannot infer that a particular supplier is strategically critical unless
their name or relevant terms are included in the configured keywords. Keyword
maintenance is the client's responsibility.

**No legal liability for missed notifications.**
MailPilot is a productivity tool. Business-critical decisions must not rely
solely on its alerts. The developer is not responsible for losses arising from
missed, delayed, or incorrectly classified email notifications.

# MailPilot — Demo Scenario

**Audience:** Import company owner (non-technical)
**Duration:** 20–30 minutes
**Prerequisites:** Bot running, Gmail connected, keywords pre-configured
with at least one supplier name, test emails prepared in advance

---

## Step-by-step demo order

### Step 1 — Setup and first impression (AC 4: Settings visibility)
**What to show:**
- Open Telegram, find the MailPilot bot
- Run /status — show that Gmail address, keywords, and digest time are saved
- Explain each field in plain language: "This is the inbox it watches,
  these are the words it looks for, this is when you get your daily summary"

**What to verify live:**
- /status returns correct values without error
- Keywords include at least one supplier name visible to the client

**Talking point:** "Everything is configured once in Telegram — no app
to install, no website to log into."

---

### Step 2 — Instant alert (AC 1: Urgent email delivery)
**What to show:**
- Send a test email to the monitored Gmail containing a configured keyword
  and urgency language (e.g. "URGENT: shipment delay — [Supplier Name]")
- Watch the Telegram notification arrive

**What to verify live:**
- Alert arrives within 5 minutes
- Message shows: sender, subject, AI score (8+), one-sentence reasoning
- Score is 8 or above

**Talking point:** "The AI read the email, saw it was from a known supplier
and contained urgent language, and scored it high enough to alert you
immediately — without you having to check your inbox."

---

### Step 3 — Spam filtering (AC 2: Spam filtering)
**What to show:**
- Send (or point to) a promotional email already in the inbox —
  a newsletter, platform notification, or "unsubscribe" message
- Trigger /digest or wait — confirm the promotional email does NOT appear

**What to verify live:**
- The promotional email scored 3 or below (visible if you check /digest output)
- No Telegram notification was generated for it

**Talking point:** "This type of email — newsletters, platform updates,
unsubscribe confirmations — is filtered out completely. It never reaches
your Telegram. You only see what matters."

---

### Step 4 — Manual digest (AC 3: Daily digest)
**What to show:**
- Run /digest to trigger the digest immediately without waiting for the
  scheduled time
- Show one or two medium-priority emails (score 4–7) appearing in the digest:
  a logistics update, a routine order acknowledgement

**What to verify live:**
- Digest arrives promptly after /digest is run
- Each email shows: subject, sender, score, AI summary sentence
- High-priority emails (already alerted in Step 2) do NOT appear again

**Talking point:** "This is your daily summary — everything that's relevant
but not urgent. You get one clean list instead of 40 unread emails."

---

### Step 5 — Keyword update (AC 6: Keyword update)
**What to show:**
- Run /setup and add a new keyword (e.g. a second supplier name or
  a product category like "customs clearance")
- Send a test email containing the new keyword
- Show the resulting alert or digest entry

**What to verify live:**
- New keyword takes effect in the same session — the next email scored
  after /setup uses the updated keywords
- Score reflects the new keyword presence

**Talking point:** "You control what the system watches for. Add a new
supplier, a product line, a deadline keyword — it starts working
immediately, no technical help needed."

---

### Step 6 — Resilience (AC 7: Resilience after errors)
**What to show (verbal, no live action needed):**
- Explain that if Gmail is temporarily unreachable, the bot waits 30 seconds
  and retries automatically
- If the retry fails, you receive a Telegram message asking you to reconnect
  via /setup — one command, 30 seconds

**Talking point:** "The bot doesn't go silent without telling you. If
something goes wrong, you'll know — and fixing it takes one command."

---

## Client questions and answers

**Q: What if an urgent email from a supplier gets a low score?**
A: This can happen if the email doesn't match any of your configured keywords
or uses unusual phrasing. The fix is to add the supplier's name or a key phrase
to your keyword list via /setup. You can also run /digest at any time to see
all medium-priority emails on demand, as a safety net.

**Q: Can it monitor two Gmail accounts — my personal one and the work one?**
A: The current version monitors one Gmail account per user. If you need to
cover a second inbox (e.g. a shared team address), that requires a separate
bot setup. This can be discussed as a future addition.

**Q: What if Telegram is down or I don't have signal?**
A: The bot runs on a server, not on your phone. It continues monitoring your
inbox regardless of your connection. When Telegram is available again, any
pending notifications will be delivered. No emails are lost.

**Q: How does the AI decide what is urgent?**
A: It reads the full subject and body of each email and looks for signals:
your keywords, urgency language ("urgent", "immediate", "deadline"),
sender type, and whether a specific action is requested. The score it assigns
reflects the combination of these signals. You can see its reasoning in
every notification — the one-sentence explanation below the score.

**Q: What does it cost to run?**
A: The main cost is the AI scoring API (Anthropic Claude), which processes
each email. At 50–100 emails per day, typical cost is under $2–5 USD per
month at current rates. Gmail and Telegram access are free. Server hosting
(if running 24/7) adds a small fixed cost depending on the provider.

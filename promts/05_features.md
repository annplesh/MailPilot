# Prompt 05 — Feature Backlog

## Feature 1 — Real-time alerts for urgent emails ⏳ PLANNED

**Identified during:** live testing

**Problem:** Bot only checks inbox once a day (scheduled) or on manual /digest.
Urgent emails are not delivered instantly.

**Solution:**

- Add polling job every 15–30 minutes
- If new email found with high AI score (8+) — send instant alert immediately
- Daily digest at 13:00 UTC remains for lower-priority emails

## Feature 2 — Auto-label emails in Gmail ⏳ PLANNED

**Identified during:** live testing

**Solution:**

- Urgent (score 8+) → label "MailPilot/Urgent"
- Important (score 5-7) → label "MailPilot/Digest"
- Irrelevant (score 1-4) → label "MailPilot/Filtered"

**Why:** User sees exactly what the bot did directly in Gmail inbox.
Builds trust and makes the product transparent.

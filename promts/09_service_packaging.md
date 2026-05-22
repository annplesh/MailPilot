# Prompt 09 — Service Packaging

## Prompt 1 — Generate project specification

Show plan first, don't make changes yet.

I have a project: MailPilot — AI-powered Telegram bot for Gmail monitoring.
The bot connects to a dedicated work Gmail inbox, scores every email
by importance (score 0-10) and sends to Telegram:

- score 8+ → instant alert
- score 4-7 → daily digest
- score <4 → filtered automatically

Client: owner of a small import company in LATAM (5-15 employees).
Receives 50-100 emails per day from suppliers, logistics companies, customs brokers.
Works via Gmail. Main pain point: missing urgent emails from key suppliers.

What we discussed in the meeting:

- Need to never miss urgent emails from key suppliers
- Daily digest for other emails
- Spam and irrelevant emails filtered automatically
- User sets their own keywords (supplier names, product categories)
- Bot works in Telegram

Help me write a project specification (ТЗ):

1. Task description (2-3 paragraphs, plain language, non-technical)
2. Scope — what is included (specific list)
3. Scope — what is NOT included (minimum 3 points)
4. Acceptance criteria (minimum 5 verifiable points)
5. Boundaries of responsibility (AI-specific limitations)

Style: professional, clear, understandable for non-technical reader.
Language: English.

## Prompt 2 — Generate demo scenario

Show plan first, don't make changes yet.

Create a new file demo_scenario.md in the project root.
This is a demonstration scenario for the client based on project_spec.md.

Include:

1. Order of showing features (by acceptance criteria)
2. What to verify live at each step
3. 3-5 questions the client might ask and how to answer them

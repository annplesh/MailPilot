# =============================================================================
# ai_filter.py — Claude AI email scoring for job opportunity detection
# =============================================================================
#
# PURPOSE:
#   Analyses an email's subject and body using the Anthropic SDK and returns
#   a structured importance score (0–10) with a one-sentence reasoning.
#   Results are used by database.py to decide whether an email is "important"
#   and should appear in the user's daily digest.
#
# DESIGN NOTES:
#   - A single module-level Anthropic client is reused across all calls
#     to avoid repeated connection setup overhead.
#   - The system prompt is long (~800 tokens) and identical for every call,
#     making it ideal for Anthropic's prompt caching feature. The first call
#     in a 5-minute window pays full input-token cost; subsequent calls within
#     the same window reuse the cache and cost significantly less.
#   - This module is intentionally synchronous. Async bot handlers in bot.py
#     call score_email() via asyncio.to_thread() to avoid blocking the event loop.
#
# =============================================================================


# --- Imports ------------------------------------------------------------------
# anthropic   — Anthropic client; reads ANTHROPIC_API_KEY from environment
# os          — access environment variables for configuration
# json        — parse Claude's structured JSON response
# re          — fallback regex extraction if JSON parsing fails
# logging     — log API errors, rate-limit warnings, and score results


# --- Client & Constants -------------------------------------------------------
# client = anthropic.Anthropic()
#   Module-level singleton. Automatically reads ANTHROPIC_API_KEY from env.
#   Reused across all score_email() calls.
#
# MODEL = "claude-sonnet-4-6"
#   The model used for all scoring requests.
#
# MAX_TOKENS = 512
#   Response is a short JSON object; 512 tokens is more than sufficient.
#
# BODY_TRUNCATION_LIMIT = 3000
#   Maximum characters of email body sent to Claude.
#   Keeps prompt size predictable and avoids context-length errors on
#   emails with large HTML content.


# =============================================================================
# SYSTEM PROMPT
# =============================================================================
#
# SYSTEM_PROMPT = """..."""
#
# PURPOSE:
#   Defines Claude's role as a job-opportunity email classifier and provides
#   a detailed scoring rubric. Must exceed 1024 tokens to qualify for
#   Anthropic's prompt caching (cache_control: ephemeral).
#
# STRUCTURE OF THE PROMPT:
#
#   1. ROLE DECLARATION
#      Instruct Claude that it is classifying emails for a freelance job seeker.
#      Emphasise that the goal is to surface genuine opportunities and suppress
#      noise (newsletters, marketing, system notifications).
#
#   2. SCORING RUBRIC (0–10 scale)
#      10 — Direct recruiter outreach: specific role title, company name, and
#            a clear invitation to apply or chat.
#       8 — Job board alert that exactly matches one or more of the user's keywords.
#       6 — Networking message from a contact that could plausibly lead to a referral
#            or introduction.
#       4 — Generic newsletter or digest from a job board with mixed listings;
#            some listings may match keywords but the email is not targeted.
#       2 — Promotional email from a job platform (e.g. "Upgrade your profile",
#            "Jobs you might like" without a keyword match).
#       0 — Spam, unsubscribe confirmations, out-of-office replies, receipts,
#            or any email with no connection to employment.
#
#   3. POSITIVE SIGNALS TO DETECT
#      - Specific role titles combined with seniority levels (e.g. "Senior Python Developer")
#      - Salary or compensation ranges mentioned explicitly
#      - Company name + phrases like "opportunity", "role", "position", "opening"
#      - Phrases indicating direct outreach: "your profile caught our eye",
#        "we'd like to speak with you", "are you open to opportunities"
#      - Apply links, job posting URLs, or interview scheduling links
#
#   4. NEGATIVE SIGNALS TO DETECT
#      - Marketing language: "limited time offer", "exclusive deal", "unsubscribe"
#      - Generic job-board digests where none of the listed roles match keywords
#      - System/transactional emails: password resets, login alerts, receipts
#      - Bulk "you have N new matches" notifications without specific role details
#
#   5. OUTPUT FORMAT INSTRUCTION
#      Instruct Claude to respond ONLY with a JSON object in this exact schema:
#      {
#        "score": <integer 0-10>,
#        "reasoning": "<one sentence explaining the score>",
#        "role_title": "<extracted job title or null if not found>",
#        "company": "<extracted company name or null if not found>"
#      }
#      No text outside the JSON object. No markdown code fences.


# =============================================================================
# MAIN FUNCTION
# =============================================================================

# def score_email(subject: str, body: str, keywords: list[str]) -> dict:
#
#   PURPOSE:
#     Send a single email to Claude for scoring. Returns a structured dict
#     with the importance score and metadata extracted by the model.
#
#   PARAMETERS:
#     subject   — The email Subject header string.
#     body      — Plain-text (or lightly cleaned HTML) email body.
#     keywords  — User's filter keywords list from the database,
#                 e.g. ["Python", "backend", "remote"].
#                 Injected into the user message so Claude can check for
#                 keyword relevance even if the system prompt is cached
#                 (cached system prompts do not vary per call).
#
#   RETURNS:
#     dict: {
#       'score':      int (0–10, clamped),
#       'reasoning':  str,
#       'role_title': str | None,
#       'company':    str | None
#     }
#
#   IMPLEMENTATION STEPS:
#
#   Step 1 — Truncate body
#     If len(body) > BODY_TRUNCATION_LIMIT, slice to that limit and append:
#     "\n[... email truncated for length ...]"
#     This prevents oversized emails (e.g. HTML newsletters) from blowing
#     the model's context window or inflating token costs.
#
#   Step 2 — Build user message
#     Compose a plain-text string:
#       "User's job-search keywords: Python, backend, remote
#        ---
#        Subject: <subject>
#        Body:
#        <body>"
#     The keywords are in the user turn (not the cached system prompt) so
#     they can vary per user without invalidating the cache.
#
#   Step 3 — Call the Anthropic API with prompt caching
#     client.messages.create(
#       model=MODEL,
#       max_tokens=MAX_TOKENS,
#       system=[
#         {
#           "type": "text",
#           "text": SYSTEM_PROMPT,
#           "cache_control": {"type": "ephemeral"}
#           # WHY: The system prompt is static and ~800 tokens.
#           # "ephemeral" caches it for 5 minutes after the first call.
#           # On a batch of 50 emails, this saves ~49 × 800 = 39 200 cached
#           # input tokens, reducing cost significantly.
#         }
#       ],
#       messages=[
#         {"role": "user", "content": user_message}
#       ]
#     )
#
#   Step 4 — Parse Claude's response
#     Extract response.content[0].text (the raw string).
#     Attempt json.loads() on the string.
#     On JSONDecodeError (model occasionally adds a preamble):
#       Use re.search(r'"score"\s*:\s*(\d+)', text) to extract the integer.
#       Return a minimal dict: {score: extracted, reasoning: raw_text,
#                               role_title: None, company: None}.
#
#   Step 5 — Validate and clamp score
#     score = max(0, min(10, int(parsed['score'])))
#     Guards against the model returning values like -1 or 11.
#
#   Step 6 — Return the final dict.
#
#   ERROR HANDLING:
#     anthropic.APIConnectionError
#       Log the error with the email subject. Return score=0 with
#       reasoning="API connection error — email not scored."
#
#     anthropic.RateLimitError
#       Log a WARNING. Re-raise the exception so the caller (gmail_reader.py)
#       can implement exponential backoff before retrying.
#
#     anthropic.APIStatusError
#       Log the HTTP status code and response body. Return score=0 with
#       reasoning="API error <status_code> — email not scored."
#
#     All log messages include the email subject for traceability.

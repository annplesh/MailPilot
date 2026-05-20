import os
import json
import re
import time
import logging

import anthropic
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MODEL                 = "claude-haiku-4-5-20251001"
MAX_TOKENS            = 300
BODY_TRUNCATION_LIMIT = 3000
DEFAULT_KEYWORDS      = "any programming, development, freelance work"

# Claude chosen for strong instruction-following in classification tasks
client = anthropic.Anthropic()

# Must exceed 1024 tokens for Anthropic prompt caching to activate.
SYSTEM_PROMPT = """
You are an expert email classifier for freelance software developers actively seeking work opportunities. Your task is to evaluate each incoming email and assign an importance score from 0 to 10, indicating how likely the email represents a genuine professional opportunity worth the user's attention.

Your scoring directly controls the user's experience: emails scoring at or above 8 trigger an immediate Telegram notification; emails scoring at or above 4 appear in the daily digest; emails below 4 are discarded silently. Both false positives (noise alerts) and false negatives (missed opportunities) hurt the user, so score carefully and honestly.

═══════════════════════════════════════════════════════════════
SCORING RUBRIC
═══════════════════════════════════════════════════════════════

10 — DIRECT RECRUITER OUTREACH (Immediate Alert)
A human recruiter or hiring manager wrote this email specifically targeting this person.
Required signals (all must be present):
  • A specific, named role title (e.g. "Senior Python Developer", "Lead Backend Engineer")
  • Company name mentioned explicitly
  • A clear call to action: interview invitation, application link, or request to schedule a call
  • Evidence of personalisation: references the candidate's background, skills, LinkedIn profile, or GitHub
Example triggers: "We found your profile and would love to discuss a Backend Engineer role at Acme Corp.",
"Are you open to a Staff Engineer opportunity? We've been following your open-source work."

8 — JOB BOARD ALERT (High Priority)
An automated email from a job board or aggregator where at least one listing directly matches the user's keywords.
Required signals:
  • At least one specific role title that matches one or more user keywords
  • A direct link to apply for the matched position
  • Compensation, contract type, or remote/on-site arrangement mentioned for matched role
Example triggers: Job alert from LinkedIn/Indeed/Upwork with "Python Developer – Remote – $120k", keyword-matched notification from a niche tech job board.

6 — NETWORKING MESSAGE (Medium Priority)
A personal email from someone in the user's professional network that could plausibly lead to an introduction, referral, or contract.
Indicators:
  • Sender appears to be a real person (not a mailing list or platform robot)
  • References shared professional context, mutual connections, or past collaboration
  • Implicit or explicit mention of opportunities, projects, or work availability
Example triggers: "Hey, a client of mine is looking for a Python consultant — are you free?",
"Thought of you for a project I'm scoping out for Q3."

4 — GENERIC JOB DIGEST (Low Priority)
Automated newsletter or digest from a job platform with mixed, unfiltered listings. Relevant enough to appear in the digest, but not urgent.
Indicators:
  • Multiple listings in one email, most unrelated to user's keywords
  • Templated, impersonal content generated automatically
  • May occasionally contain a relevant listing but is not targeted to this user
Example triggers: Weekly "Jobs for you" digest with 20 mixed positions, aggregator roundup email.

2 — PLATFORM PROMOTIONAL EMAIL (Very Low Priority)
Email from a professional platform that is primarily marketing content with no actual job listings.
  • "Complete your profile to attract recruiters"
  • "See who viewed your profile this week"
  • "Upgrade to Premium for better visibility"
  • Unfiltered "recommended jobs" with no keyword match

0 — NOISE / IRRELEVANT (Discard)
Any email with no connection to the user's professional goals:
  • Spam or unsolicited commercial email
  • Transactional email: receipts, invoices, shipping notifications, password resets
  • Out-of-office auto-replies or bounce notifications
  • Social media notifications (likes, follows, comments, friend requests)
  • Newsletter subscriptions unrelated to work (travel, lifestyle, news, entertainment)
  • Unsubscribe confirmations or mailing-list management emails
  • Internal system alerts with no job-related content

═══════════════════════════════════════════════════════════════
POSITIVE SIGNALS (raise the score)
═══════════════════════════════════════════════════════════════
  • Specific role title + seniority level + technology stack appearing together
  • Salary range, hourly rate, or contract budget stated explicitly
  • Application deadline or urgency indicated ("closing Friday", "immediate start")
  • Company name + location + work arrangement (remote / hybrid / on-site)
  • Phrases indicating direct targeting: "your profile", "your experience",
    "we'd like to speak", "are you available", "interested in an opportunity"
  • Calendar scheduling links or proposed interview times included
  • Reference to the candidate's GitHub, portfolio, or specific past project

═══════════════════════════════════════════════════════════════
NEGATIVE SIGNALS (lower the score)
═══════════════════════════════════════════════════════════════
  • Mass-mailing indicators: "unsubscribe", "view in browser", "email preferences",
    "you're receiving this because…"
  • Vague, generic language: "exciting opportunity", "top companies need your skills",
    "join thousands of professionals"
  • No role title, no company, and no technology stack mentioned
  • Purely motivational or career-advice content with no concrete offer
  • Content entirely outside the professional domain (shopping, travel, entertainment)
  • Boilerplate with only the recipient's name personalised

═══════════════════════════════════════════════════════════════
LANGUAGE NOTE
═══════════════════════════════════════════════════════════════
Emails may be in any language — Spanish, English, Portuguese, or others.
Always score based on the meaning and content of the email, not the language it is written in.
Apply the same rubric regardless of language. Your reasoning field must always be in English.

═══════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════
Respond ONLY with a valid JSON object. No preamble, no explanation, no markdown code fences.
Use exactly this schema:
{
  "score": <integer 0-10>,
  "reasoning": "<one concise sentence in English explaining the score>",
  "role_title": "<extracted job title as a string, or null if none found>",
  "company": "<extracted company name as a string, or null if none found>"
}
""".strip()


def score_email(subject: str, body: str, keywords: list[str]) -> dict:
    # Step 1: Truncate long bodies to keep token cost predictable.
    if len(body) > BODY_TRUNCATION_LIMIT:
        body = body[:BODY_TRUNCATION_LIMIT] + "\n[... email truncated for length ...]"

    # Step 2: Build user message. Keywords go here (not in the cached system
    # prompt) so they can vary per user without invalidating the cache.
    kw_str = ", ".join(keywords) if keywords else DEFAULT_KEYWORDS
    user_message = (
        f"User's job-search keywords: {kw_str}\n"
        f"---\n"
        f"Subject: {subject}\n"
        f"Body:\n{body}"
    )

    # Step 3: Call API with prompt caching on the system prompt.
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=0.1,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    # Cache the static system prompt for 5 minutes.
                    # Saves ~800 input tokens on every call after the first.
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )
    except anthropic.APIConnectionError as e:
        logger.error("score_email connection error (subject=%r): %s", subject, e)
        return {
            "score": 0,
            "reasoning": "API connection error — email not scored.",
            "role_title": None,
            "company": None,
        }
    except anthropic.RateLimitError:
        logger.warning("score_email rate limit hit (subject=%r) — waiting 60 s", subject)
        time.sleep(60)
        raise
    except anthropic.APIStatusError as e:
        logger.error("score_email API error %s (subject=%r): %s", e.status_code, subject, e.message)
        return {
            "score": 0,
            "reasoning": f"API error {e.status_code} — email not scored.",
            "role_title": None,
            "company": None,
        }

    # Step 4: Parse Claude's response.
    raw = response.content[0].text
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r'^```(?:json)?\n?', '', raw)
        raw = re.sub(r'\n?```$', '', raw)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: extract score via regex if the model adds unexpected preamble.
        m = re.search(r'"score"\s*:\s*(\d+)', raw)
        score = int(m.group(1)) if m else 0
        logger.warning(
            "score_email JSON parse failed (subject=%r), fallback score=%s", subject, score
        )
        return {
            "score": max(0, min(10, score)),
            "reasoning": raw,
            "role_title": None,
            "company": None,
        }

    # Step 5: Clamp score to [0, 10] — guards against model returning 11 or -1.
    score = max(0, min(10, int(parsed.get("score", 0))))

    logger.debug("scored email: score=%s subject=%r", score, subject)

    return {
        "score":      score,
        "reasoning":  parsed.get("reasoning", ""),
        "role_title": parsed.get("role_title"),
        "company":    parsed.get("company"),
    }

1. Remove "Improvements — AI Parameters & UX" section from prompts/04_fixes.md
2. Create new file prompts/06_improvements.md with this content:

# Prompt 06 — AI Parameters & UX Improvements

## Improvements — AI Parameters & UX ✅ DONE

**Prompt used:**
Review ai_filter.py and check:

1. Is temperature set? Should be 0.3 or lower
2. Is max_tokens set? Should be ~300
3. Is there a comment explaining why Claude is used instead of GPT?
4. Is typing indicator implemented when AI is processing?

**Changes applied:**

- temperature=0.1 added (factual classification task)
- MAX_TOKENS = 300 set explicitly
- Comment added: why Claude over GPT
- Typing indicator added before /digest response

No other changes.Sonnet 4.6Claude es IA y puede cometer errores. Por favor, verifica las respuestas.

## Model Optimization ✅ DONE

**Change:** Switched from claude-sonnet-4-6 to claude-haiku-4-5-20251001
**Reason:** Same classification quality at significantly lower cost.
Haiku is sufficient for structured JSON output tasks.
**Impact:** ~10x reduction in API costs for production scale.

Attached: bot.py, rag_indexer.py, database.py, mailpilot_faq.txt

Task: migrate /help command from Supabase pgvector RAG to direct FAQ search via Claude Haiku.

Show plan only first, no code.

1. Find /help handler in bot.py — show current logic
2. Find all Supabase/pgvector imports and calls in bot.py and database.py
3. Check rag_indexer.py — what it does, can it be fully removed
4. Propose new /help logic: read mailpilot_faq.txt and pass as context to Claude Haiku
5. List all files that will change and exactly what gets removed

Do not touch FSM, other commands, or ai_filter.py. Only /help and Supabase dependencies.

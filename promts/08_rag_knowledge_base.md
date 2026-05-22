# Prompt 08 — RAG Knowledge Base & Indexing

## Prompt 1 — Create FAQ document

Create a new file mailpilot_faq.txt in the project root with
frequently asked questions about MailPilot based on the
HELP_SYSTEM_PROMPT content in ai_filter.py.

Include at least 15 Q&A pairs covering:

- How scoring works
- How to set up Gmail
- What keywords do
- How digest and alerts work
- How /help and /reset work
- What happens to spam
- How to reconnect Gmail

Format: Q: ... A: ...

## Prompt 2 — Create indexing script

Show plan first, don't make changes yet.

Create a new file rag_indexer.py in the project root.
This script reads mailpilot_faq.txt, splits it into chunks,
creates embeddings using sentence-transformers (model: all-MiniLM-L6-v2),
and uploads them to Supabase documents table.

Requirements:

1. Load SUPABASE_URL and SUPABASE_KEY from .env
2. Read mailpilot_faq.txt
3. Split by Q&A pairs (each Q+A = one chunk)
4. Generate embeddings with sentence-transformers
5. Upload to Supabase documents table (content, embedding, metadata)
6. Print count of uploaded chunks at the end

No other changes.

## Prompt 3 — Debug Supabase insert error

In rag_indexer.py, the Supabase insert is failing with PGRST125
"Invalid path specified in request URL".

Debug the issue by printing the Supabase URL being used before
the insert call. Also try inserting just one row as a test.
Show plan first.

## Prompt 4 — Remove debug code from rag_indexer.py

In rag_indexer.py, remove the debug additions:

1. Remove the print(f"Supabase URL: ...") line
2. Remove the test insert block and replace with original single insert:
   client.table(TABLE).insert(rows).execute()
   print(f"Uploaded {len(rows)} chunk(s) to '{TABLE}'.")
   No other changes.

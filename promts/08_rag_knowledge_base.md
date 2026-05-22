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

## Prompt 5 — Connect RAG search to /help command

Show plan first, don't make changes yet.

Add RAG search to the /help command in MailPilot.

When user asks /help <question>:

1. Generate embedding for the question using sentence-transformers (all-MiniLM-L6-v2)
2. Search Supabase documents table for top 3 most similar chunks
3. Add found chunks as context to the AI prompt
4. Log found chunks to console for debugging
5. If no chunks found — AI uses HELP_SYSTEM_PROMPT only (fallback)

Changes needed:

- ai_filter.py: add search_knowledge_base(question) function
- ai_filter.py: update answer_help_question() to accept optional context
- bot.py: call search_knowledge_base before answer_help_question in help_handler

No other changes.

## Prompt 6 — Fix RAG search returning empty results

In ai_filter.py, search_knowledge_base() returns empty results.
The Supabase RPC match_documents works correctly when tested directly in SQL.

Fix the RPC call — the embedding vector may need to be passed differently.
Current code:
result = create_client(supabase_url, supabase_key).rpc(
"match_documents",
{"query_embedding": embedding, "match_count": top_k},
).execute()

Try passing embedding as a list directly and verify the parameter names
match the SQL function signature.
Show plan first.

## Prompt 7 — Fix embedding format for pgvector RPC ❌ NOT SOLVED

In ai_filter.py, in search_knowledge_base():
Replace embedding list with string format for pgvector:
embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
Result: still returns empty list.

## Prompt 8 — Debug RPC call with direct query ✅ SOLVED via Prompt 9

In ai_filter.py, in search_knowledge_base(),
replace embedding_str with direct SQL query instead of RPC.
Use supabase client to query documents table directly:

result = create_client(supabase_url, supabase_key).rpc(
"match_documents",
{"query_embedding": embedding, "match_count": top_k},
).execute()

Where embedding is the plain Python list from model.encode().tolist().
Also add: print(f"DEBUG result.data: {result.data}")
Show plan first.

## Prompt 9 — Replace RPC with direct table query for RAG search ✅ DONE

In ai_filter.py, replace the RPC call in search_knowledge_base()
with a direct table query approach:

1. Fetch all documents from Supabase (content and embedding columns)
2. Calculate cosine similarity in Python between query embedding and each document
3. Return top_k most similar content strings

This avoids the RPC match_documents function entirely.
Show plan first.

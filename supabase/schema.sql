-- =============================================================================
-- MailPilot — Supabase Schema
-- Run this script once to set up the database from scratch.
-- =============================================================================

-- 1. Enable pgvector extension
create extension if not exists vector;

-- 2. Create documents table for RAG knowledge base
create table if not exists documents (
  id bigserial primary key,
  content text,
  embedding vector(384),
  metadata jsonb
);

-- 3. Create vector index for similarity search
create index if not exists documents_embedding_idx
on documents using ivfflat (embedding vector_cosine_ops);

-- 4. Enable Row Level Security
alter table documents enable row level security;

-- 5. RLS policies
create policy "Allow read for anon"
on documents
for select
using (true);

create policy "Allow insert for anon"
on documents
for insert
with check (true);

-- 6. Grants for anon and authenticated roles
grant all on table documents to anon;
grant all on table documents to authenticated;
grant usage on sequence documents_id_seq to anon;
grant usage on sequence documents_id_seq to authenticated;

-- 7. match_documents function for RAG similarity search
CREATE OR REPLACE FUNCTION match_documents(query_embedding vector(384), match_count int)
RETURNS TABLE(content text, similarity float)
LANGUAGE sql STABLE AS $$
  SELECT content, 1 - (embedding <=> query_embedding) AS similarity
  FROM documents
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;

-- 8. Grant execute on function
grant execute on function match_documents(vector, int) to anon;
grant execute on function match_documents(vector, int) to authenticated;
grant select on documents to anon;
grant select on documents to authenticated;

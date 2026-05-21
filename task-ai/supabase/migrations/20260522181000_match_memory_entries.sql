-- Migration: match_memory_entries (RPC for vector recall)
-- Created: 2026-05-22
-- Purpose: Server-side cosine similarity for recallMemory. Avoids round-tripping
--          1536-dim vectors back to Node for client-side ranking.

CREATE OR REPLACE FUNCTION match_memory_entries(
  query_embedding vector(1536),
  match_tenant TEXT,
  match_type TEXT DEFAULT NULL,
  match_count INT DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  topic TEXT,
  content TEXT,
  type TEXT,
  tags TEXT[],
  importance TEXT,
  similarity FLOAT,
  created_at TIMESTAMPTZ
)
LANGUAGE sql STABLE
AS $$
  SELECT
    m.id,
    m.topic,
    m.content,
    m.type,
    m.tags,
    m.importance,
    1 - (m.embedding <=> query_embedding) AS similarity,
    m.created_at
  FROM memory_entries m
  WHERE m.tenant_id = match_tenant
    AND m.archived_at IS NULL
    AND m.embedding IS NOT NULL
    AND (match_type IS NULL OR m.type = match_type)
  ORDER BY m.embedding <=> query_embedding
  LIMIT match_count;
$$;

COMMENT ON FUNCTION match_memory_entries IS
  'Cosine-similarity recall for Task AI memory_entries. Server-side ranking, tenant-scoped, optional type filter.';

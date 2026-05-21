-- Migration: rag_chunks
-- Created: 2026-05-22
-- Purpose: Hybrid RAG store for Task AI (Phase 5).
--
-- Per M-06: dense alone is poor recall. We add BM25 (tsvector) + pgvector
-- HNSW + Reciprocal Rank Fusion in the query layer.
--
-- Multimodal: chunks can carry text (from PDF/docx/markdown), image
-- descriptions (from Vision LLM), or audio/video transcripts. The
-- `modality` column tags the original source so retrieval can boost
-- by modality if needed.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS rag_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  uploader_id TEXT NOT NULL,
  source_uri TEXT,                              -- e.g. supabase storage URL, or external
  source_kind TEXT NOT NULL CHECK (source_kind IN (
    'pdf', 'docx', 'markdown', 'txt', 'image', 'audio', 'video', 'webpage', 'manual'
  )),
  title TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'ready', 'failed')),
  total_chunks INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  archived_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_rag_documents_tenant
  ON rag_documents (tenant_id, created_at DESC)
  WHERE archived_at IS NULL;

CREATE TABLE IF NOT EXISTS rag_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  document_id UUID NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,
  chunk_index INT NOT NULL,
  modality TEXT NOT NULL DEFAULT 'text' CHECK (modality IN ('text', 'image', 'audio', 'video')),
  content TEXT NOT NULL,
  content_tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', coalesce(content, ''))) STORED,
  embedding vector(1536),                       -- gemini-embedding-2 @ 1536-dim Matryoshka
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rag_chunks_doc ON rag_chunks(document_id, chunk_index);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_tenant ON rag_chunks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_tsv ON rag_chunks USING GIN (content_tsv);

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_am WHERE amname = 'hnsw') THEN
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_rag_chunks_emb_hnsw
             ON rag_chunks USING hnsw (embedding vector_cosine_ops)
             WITH (m = 16, ef_construction = 64)';
  ELSE
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_rag_chunks_emb_ivf
             ON rag_chunks USING ivfflat (embedding vector_cosine_ops)
             WITH (lists = 100)';
  END IF;
END$$;

-- RLS: tenant isolation
ALTER TABLE rag_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_chunks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS rag_documents_tenant_iso ON rag_documents;
CREATE POLICY rag_documents_tenant_iso ON rag_documents
  FOR ALL
  USING (tenant_id = current_setting('app.tenant_id', true))
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

DROP POLICY IF EXISTS rag_chunks_tenant_iso ON rag_chunks;
CREATE POLICY rag_chunks_tenant_iso ON rag_chunks
  FOR ALL
  USING (tenant_id = current_setting('app.tenant_id', true))
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

-- Hybrid RRF: server-side function returns BOTH bm25 and dense ranks.
-- Caller applies Reciprocal Rank Fusion (k=60 is a common default).
CREATE OR REPLACE FUNCTION match_rag_chunks(
  query_embedding vector(1536),
  query_text TEXT,
  match_tenant TEXT,
  match_count INT DEFAULT 20
)
RETURNS TABLE (
  id UUID,
  document_id UUID,
  content TEXT,
  modality TEXT,
  metadata JSONB,
  dense_rank INT,
  bm25_rank INT,
  dense_score FLOAT,
  bm25_score FLOAT
)
LANGUAGE sql STABLE
AS $$
  WITH dense AS (
    SELECT c.id, c.document_id, c.content, c.modality, c.metadata,
           1 - (c.embedding <=> query_embedding) AS dense_score,
           row_number() OVER (ORDER BY c.embedding <=> query_embedding) AS dense_rank
    FROM rag_chunks c
    WHERE c.tenant_id = match_tenant AND c.embedding IS NOT NULL
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count * 3
  ),
  bm25 AS (
    SELECT c.id, c.document_id, c.content, c.modality, c.metadata,
           ts_rank_cd(c.content_tsv, plainto_tsquery('english', query_text)) AS bm25_score,
           row_number() OVER (ORDER BY ts_rank_cd(c.content_tsv, plainto_tsquery('english', query_text)) DESC) AS bm25_rank
    FROM rag_chunks c
    WHERE c.tenant_id = match_tenant
      AND c.content_tsv @@ plainto_tsquery('english', query_text)
    ORDER BY bm25_score DESC
    LIMIT match_count * 3
  ),
  combined AS (
    SELECT
      coalesce(d.id, b.id) AS id,
      coalesce(d.document_id, b.document_id) AS document_id,
      coalesce(d.content, b.content) AS content,
      coalesce(d.modality, b.modality) AS modality,
      coalesce(d.metadata, b.metadata) AS metadata,
      d.dense_rank,
      b.bm25_rank,
      coalesce(d.dense_score, 0) AS dense_score,
      coalesce(b.bm25_score, 0) AS bm25_score
    FROM dense d
    FULL OUTER JOIN bm25 b ON d.id = b.id
  )
  SELECT id, document_id, content, modality, metadata,
         dense_rank::INT, bm25_rank::INT, dense_score, bm25_score
  FROM combined
  ORDER BY (1.0 / (60 + coalesce(dense_rank, 1000))) + (1.0 / (60 + coalesce(bm25_rank, 1000))) DESC
  LIMIT match_count;
$$;

COMMENT ON FUNCTION match_rag_chunks IS
  'Hybrid retrieval (Phase 5). Returns both dense and BM25 ranks; caller does RRF fusion or trusts the inline ORDER BY (RRF k=60).';

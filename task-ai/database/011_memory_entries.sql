-- Migration: 011_memory_entries
-- Created: 2026-05-22
-- Purpose: Persistent memory tier for Onsite Task AI (Phase 1).
--
-- 4-tier memory model (ARCHITECTURE-V3 §7):
--   T1 — Session (in-process, this request only)
--   T2 — Conversation (in DB messages, already there)
--   T3 — Persistent ← THIS TABLE (pgvector, cross-session recall)
--   T4 — Knowledge graph (Phase 12, deferred)
--
-- gemini-embedding-2 at 1536-dim Matryoshka (M-01). Vectors written here
-- MUST come from this model — do NOT mix with gemini-embedding-001 output.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS memory_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Multi-tenant invariant: every row belongs to exactly one tenant + one user.
  -- tenant_id today = decodedJwt.user_id (single-user-per-tenant). When Onsite
  -- adds company-level tenancy we backfill from JWT claims.
  tenant_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  session_id TEXT,                              -- nullable: cross-session memories have no session

  topic TEXT NOT NULL,
  content TEXT NOT NULL,
  type TEXT NOT NULL CHECK (type IN (
    'fact',          -- "Arohan is in Bengaluru"
    'preference',    -- "User prefers Hindi-mix replies"
    'decision',      -- "Switched vendor X to vendor Y on May 5"
    'task',          -- "Follow up with Akshansh by Friday"
    'reminder',      -- like task but heartbeat surfaces at due_at
    'conversation',  -- distilled gist from chat
    'project',       -- "Soul Space has 4 workorders"
    'vendor',        -- "ABC Cement reliable, BCD late"
    'client'         -- generic client profile
  )),
  tags TEXT[] NOT NULL DEFAULT '{}',
  importance TEXT NOT NULL DEFAULT 'medium'
    CHECK (importance IN ('low', 'medium', 'high', 'critical')),

  -- Heartbeat (M-12): if set, the hourly scanner surfaces this memory as a nudge.
  -- e.g. "yesterday you mentioned reordering steel — that's due today."
  due_at TIMESTAMPTZ,
  surfaced_at TIMESTAMPTZ,                      -- last time heartbeat actually surfaced this

  -- Decay scoring: every recall bumps last_recalled. Decay job demotes
  -- low-importance entries that haven't been recalled in N days.
  recall_count INT NOT NULL DEFAULT 0,
  last_recalled_at TIMESTAMPTZ,

  embedding vector(1536),                       -- gemini-embedding-2 @ 1536-dim Matryoshka

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  archived_at TIMESTAMPTZ                        -- soft delete; kept for training-data audit
);

-- Tenant + type fan-out (most common access path)
CREATE INDEX IF NOT EXISTS idx_memory_entries_tenant
  ON memory_entries (tenant_id, type, importance, created_at DESC)
  WHERE archived_at IS NULL;

-- Heartbeat scanner: cron looks for due_at <= now() AND not yet surfaced
CREATE INDEX IF NOT EXISTS idx_memory_entries_due
  ON memory_entries (due_at)
  WHERE due_at IS NOT NULL AND archived_at IS NULL;

-- Tag filter (e.g. memories about "vendor:ABC Cement")
CREATE INDEX IF NOT EXISTS idx_memory_entries_tags
  ON memory_entries USING GIN (tags);

-- Vector ANN — HNSW is faster than ivfflat at our scale; pgvector >=0.5 needed.
-- Falls back gracefully if HNSW not available (try IVFFlat).
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_am WHERE amname = 'hnsw') THEN
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_memory_entries_emb_hnsw
             ON memory_entries USING hnsw (embedding vector_cosine_ops)
             WITH (m = 16, ef_construction = 64)';
  ELSE
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_memory_entries_emb_ivf
             ON memory_entries USING ivfflat (embedding vector_cosine_ops)
             WITH (lists = 100)';
  END IF;
END$$;

-- RLS: tenant isolation. Service role bypasses (server uses service_role for now).
ALTER TABLE memory_entries ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS memory_entries_tenant_iso ON memory_entries;
CREATE POLICY memory_entries_tenant_iso ON memory_entries
  FOR ALL
  USING (tenant_id = current_setting('app.tenant_id', true))
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

COMMENT ON TABLE memory_entries IS
  'Tier 3 (persistent) memory for Task AI. pgvector cosine search at 1536-dim. RLS enforces tenant isolation. Heartbeat scanner reads due_at for proactive nudges (M-12).';

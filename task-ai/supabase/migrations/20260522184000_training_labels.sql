-- Migration: training_labels
-- Created: 2026-05-22
-- Purpose: Best-not-minimal labeling per ARCHITECTURE-V3 §7.5 (Phase 7).
--
-- Existing pieces (already shipped, see STATE.md):
--   - task_ai_messages (thumbs feedback)
--   - /task-bot/admin (24h KPI dashboard)
--   - /api/task-bot/export-training-data (JSONL export)
--
-- New here: per-turn structured labels for instruction tuning + RAGAS eval.

CREATE TABLE IF NOT EXISTS training_labels (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  labeler_id TEXT NOT NULL,                     -- Onsite user_id of the human labeler
  message_id UUID,                              -- ref task_ai_messages.id (loose ref — message table may be archived)

  -- The original turn under review
  user_message TEXT NOT NULL,
  assistant_message TEXT NOT NULL,
  tool_calls JSONB DEFAULT '[]'::jsonb,

  -- Label
  verdict TEXT NOT NULL CHECK (verdict IN ('good', 'bad', 'partial', 'needs_fix')),
  corrected_response TEXT,                      -- the human-authored "what it should have said"
  notes TEXT,
  tags TEXT[] NOT NULL DEFAULT '{}',            -- e.g. {hallucination, missed_tool, wrong_uuid, language_off}

  -- RAGAS-style scores (0-1)
  relevance FLOAT CHECK (relevance >= 0 AND relevance <= 1),
  faithfulness FLOAT CHECK (faithfulness >= 0 AND faithfulness <= 1),
  completeness FLOAT CHECK (completeness >= 0 AND completeness <= 1),

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_training_labels_tenant
  ON training_labels(tenant_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_training_labels_verdict
  ON training_labels(verdict);

CREATE INDEX IF NOT EXISTS idx_training_labels_tags
  ON training_labels USING GIN (tags);

-- Golden set for offline eval. Each row = one canonical (user_input → expected_response)
-- pair. CI runs the bot against this set after every prompt change and reports drift.
CREATE TABLE IF NOT EXISTS golden_set (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  category TEXT NOT NULL,                       -- e.g. 'list_projects', 'create_dep', 'hallucination_guard'
  user_input TEXT NOT NULL,
  expected_tool TEXT,                           -- which tool MUST fire (null = chat-only response)
  expected_response_fragments TEXT[] NOT NULL DEFAULT '{}',  -- substrings that must appear
  forbidden_fragments TEXT[] NOT NULL DEFAULT '{}',
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_golden_set_category ON golden_set(category) WHERE active;

ALTER TABLE training_labels ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS training_labels_tenant_iso ON training_labels;
CREATE POLICY training_labels_tenant_iso ON training_labels
  FOR ALL
  USING (tenant_id = current_setting('app.tenant_id', true))
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

COMMENT ON TABLE training_labels IS 'Structured per-turn labels for instruction tuning + RAGAS eval (Phase 7).';
COMMENT ON TABLE golden_set IS 'Canonical eval set. CI re-runs after prompt changes to detect regressions.';

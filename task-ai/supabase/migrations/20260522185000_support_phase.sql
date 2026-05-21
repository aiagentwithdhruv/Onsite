-- Migration: support_phase
-- Created: 2026-05-22
-- Purpose: Add support-flow state machine column to session metadata (Phase 8).
-- Pattern lifted from hireai (M-10).

ALTER TABLE task_ai_session_meta
  ADD COLUMN IF NOT EXISTS support_phase TEXT
    CHECK (support_phase IS NULL OR support_phase IN ('triage', 'investigate', 'resolve', 'confirm', 'closed'));

ALTER TABLE task_ai_session_meta
  ADD COLUMN IF NOT EXISTS support_context JSONB DEFAULT '{}'::jsonb;

COMMENT ON COLUMN task_ai_session_meta.support_phase IS
  'Current state in the support flow state machine. null = not a support session.';

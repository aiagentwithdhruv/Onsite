-- Migration: project_anchor
-- Created: 2026-05-23
-- Purpose: Server-enforced project scoping per chat session (M-47).
--
-- Every chat is now anchored to exactly one project. The bot reads this
-- column at the start of each request and injects "ANCHOR: ..." into the
-- system prompt as a hardcoded fact — no more re-resolving project_id on
-- every turn (which was burning API budget AND causing UUID hallucination
-- when the bot re-did list_companies → list_projects per message).

ALTER TABLE task_ai_session_meta
  ADD COLUMN IF NOT EXISTS project_anchor JSONB;

-- Useful index for finding all sessions anchored to a project (admin queries)
CREATE INDEX IF NOT EXISTS idx_task_ai_session_meta_anchor_project
  ON task_ai_session_meta ((project_anchor->>'project_id'))
  WHERE project_anchor IS NOT NULL;

COMMENT ON COLUMN task_ai_session_meta.project_anchor IS
  'JSONB: {project_id, project_name, company_id, company_name, anchored_at}. Set after first project resolution in a session; never re-resolved while non-null.';

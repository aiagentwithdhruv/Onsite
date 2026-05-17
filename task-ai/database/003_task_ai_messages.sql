-- task_ai_messages — opt-in chat persistence designed for AI training.
--
-- Captures every user + assistant turn (plus tool metadata + outcomes + feedback)
-- so we can later export labeled training data for fine-tuning or RAG.
--
-- Privacy: only written when the user explicitly enables "SAVE" in the UI.
-- Service-role-only writes; RLS blocks all other roles.

create table if not exists task_ai_messages (
  id           uuid primary key default gen_random_uuid(),
  session_id   text not null,
  user_id      text,
  company_id   text,
  role         text not null check (role in ('user', 'assistant', 'system', 'tool')),
  content      text not null default '',
  card         jsonb,
  tool_name    text,
  tool_args    jsonb,
  tool_result  jsonb,
  success      boolean,
  feedback     text check (feedback in ('positive', 'negative')),
  model        text,
  source_env   text check (source_env in ('test', 'prod')),
  created_at   timestamptz not null default now()
);

create index if not exists idx_task_ai_messages_session
  on task_ai_messages (session_id, created_at);

create index if not exists idx_task_ai_messages_user
  on task_ai_messages (user_id, created_at);

create index if not exists idx_task_ai_messages_feedback
  on task_ai_messages (feedback)
  where feedback is not null;

create index if not exists idx_task_ai_messages_tool
  on task_ai_messages (tool_name, success, created_at)
  where tool_name is not null;

alter table task_ai_messages enable row level security;

-- No policies = no access for anon/authenticated. Service role bypasses RLS.
-- This is intentional — backend service role is the only writer/reader.

comment on table task_ai_messages is
  'Opt-in chat transcripts (user + assistant + tool) for Onsite Task AI. Source of future training data. Off by default — only written when user toggles SAVE.';

-- task_ai_session_meta — per-session metadata (title + locked project context).
--
-- Why this exists:
--   * Users want to rename "Hey Hi" → "Interior Project work" so they can
--     find chats again
--   * Once a chat is named after a project, the AI should treat THAT project
--     as the default for any unspecified reference in that chat (saves a
--     fan-out across 25 companies on every turn)
--
-- One row per (user_id, session_id). Service-role-only writes.

create table if not exists task_ai_session_meta (
  session_id        text primary key,
  user_id           text not null,
  title             text,
  project_context   jsonb,    -- {company_id, company_name, project_id, project_name, workorder_id}
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

create index if not exists idx_task_ai_session_meta_user
  on task_ai_session_meta (user_id, updated_at desc);

alter table task_ai_session_meta enable row level security;

-- No policies = service-role-only. Matches task_ai_messages.

comment on table task_ai_session_meta is
  'Per-session metadata for Onsite Task AI: user-facing title + AI-discovered project context that the bot reuses across turns.';

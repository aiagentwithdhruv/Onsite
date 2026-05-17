-- task_ai_actions: audit + telemetry for every Onsite Task AI tool execution.
-- Created 2026-05-17. Lives in the shared onsite-hub Supabase project (jfuvhaampbngijfxgnnf).
-- Scoped by company_id for tenant isolation.

CREATE TABLE IF NOT EXISTS task_ai_actions (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id     UUID NOT NULL,
    user_id        UUID NOT NULL,
    project_id     UUID,                 -- if known from tool args
    workorder_id   UUID,                 -- if known from tool args / response
    tool           TEXT NOT NULL,        -- e.g. create_task_dependency
    args           JSONB NOT NULL,       -- input args
    result_summary JSONB,                -- short success result (e.g. {dep_id, primary_name, secondary_name})
    success        BOOLEAN NOT NULL DEFAULT FALSE,
    error_message  TEXT,                 -- human-readable error if any
    error_code     TEXT,                 -- http status or onsite error code
    latency_ms     INTEGER,              -- total time including Claude + Onsite + Supabase
    model          TEXT,                 -- LLM model used
    source_env     TEXT NOT NULL DEFAULT 'prod',  -- 'prod' | 'test'
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Hot indices
CREATE INDEX IF NOT EXISTS idx_task_ai_actions_company_time
    ON task_ai_actions (company_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_task_ai_actions_user_time
    ON task_ai_actions (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_task_ai_actions_tool_time
    ON task_ai_actions (tool, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_task_ai_actions_project
    ON task_ai_actions (project_id, created_at DESC) WHERE project_id IS NOT NULL;

-- RLS
ALTER TABLE task_ai_actions ENABLE ROW LEVEL SECURITY;

-- Service-role-only writes (our Next.js API route uses SUPABASE_SERVICE_KEY).
-- No client-side direct access yet — future admin dashboard will add read policy
-- scoped by company_id via the user's JWT.

COMMENT ON TABLE task_ai_actions IS
    'Audit log of every Onsite Task AI tool execution. company_id scopes data per tenant. No customer chat content — only structured action metadata.';
COMMENT ON COLUMN task_ai_actions.args IS 'Raw tool args (no PII other than what the user typed and intended to send to Onsite).';
COMMENT ON COLUMN task_ai_actions.result_summary IS 'Compact summary of success result; full response NOT stored.';
COMMENT ON COLUMN task_ai_actions.latency_ms IS 'End-to-end latency for the action: Claude reasoning + Onsite API + Supabase write.';

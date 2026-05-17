-- Allow company_id and user_id to be NULL for failed actions where we couldn't
-- discover the IDs (e.g., 404 before any Onsite call succeeded).
ALTER TABLE task_ai_actions ALTER COLUMN company_id DROP NOT NULL;
ALTER TABLE task_ai_actions ALTER COLUMN user_id DROP NOT NULL;

-- Migration: documents (vision document AI)
-- Created: 2026-05-22
-- Purpose: Persist 2-pass extraction results from Gemini Vision (Phase 5.5).
--
-- Per M-03: pure Vision LLM = 95-97% acc. 2-pass (Flash → validators → Pro
-- on failures) = 99.5% at ~$0.10/doc. We persist the extracted structured
-- JSON + the validator status so the bot can re-query later without
-- re-running the OCR.

CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  uploader_id TEXT NOT NULL,
  source_uri TEXT,                              -- original file URL (Supabase storage)
  source_hash TEXT,                             -- sha256 of original — for dedup
  doc_type TEXT NOT NULL CHECK (doc_type IN (
    'invoice', 'purchase_order', 'boq', 'ra_bill', 'quotation',
    'material_receipt', 'site_photo', 'safety_incident', 'other'
  )),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'ready', 'needs_review', 'failed')),

  -- The structured JSON (per doc_type schema)
  extracted JSONB NOT NULL DEFAULT '{}'::jsonb,
  extracted_pass INT NOT NULL DEFAULT 0,        -- 0 = not extracted, 1 = Flash only, 2 = Flash+Pro

  -- Validator results: array of { field, passed, message }
  validator_results JSONB NOT NULL DEFAULT '[]'::jsonb,

  -- Cost tracking
  flash_cost_inr NUMERIC(10, 4) DEFAULT 0,
  pro_cost_inr NUMERIC(10, 4) DEFAULT 0,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  processed_at TIMESTAMPTZ,
  reviewed_at TIMESTAMPTZ,
  archived_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_documents_tenant
  ON documents (tenant_id, doc_type, created_at DESC)
  WHERE archived_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_documents_status
  ON documents (status)
  WHERE archived_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_hash
  ON documents (tenant_id, source_hash)
  WHERE source_hash IS NOT NULL;

-- RLS: tenant isolation
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS documents_tenant_iso ON documents;
CREATE POLICY documents_tenant_iso ON documents
  FOR ALL
  USING (tenant_id = current_setting('app.tenant_id', true))
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

COMMENT ON TABLE documents IS
  '2-pass Vision LLM extraction store. Pass 1 = Flash, Pass 2 = Pro on validator failures. status=needs_review when even Pro cannot satisfy validators.';

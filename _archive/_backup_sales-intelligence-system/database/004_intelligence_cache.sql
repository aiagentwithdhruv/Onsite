-- Intelligence data cache: stores uploaded CSV data in chunks for fast read/write
-- Run in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS intelligence_cache (
  id SERIAL PRIMARY KEY,
  chunk_index INTEGER NOT NULL,
  total_chunks INTEGER NOT NULL,
  total_rows INTEGER NOT NULL,
  rows_json TEXT NOT NULL,
  uploaded_by TEXT DEFAULT 'system',
  uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_intelligence_cache_chunk ON intelligence_cache(chunk_index);

-- Disable RLS for this table (internal cache, accessed via service role)
ALTER TABLE intelligence_cache ENABLE ROW LEVEL SECURITY;
CREATE POLICY intelligence_cache_service ON intelligence_cache FOR ALL USING (true) WITH CHECK (true);

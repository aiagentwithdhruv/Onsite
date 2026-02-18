-- Add Dhruv as app user (run in Supabase SQL Editor)
-- After running: create Auth user in Supabase Dashboard → Authentication → Users
--   Email: dhruv.tomar@onsiteteams.com, set a password.

INSERT INTO users (email, name, role, is_active)
VALUES (
  'dhruv.tomar@onsiteteams.com',
  'Dhruv Tomar',
  'admin',
  true
)
ON CONFLICT (email) DO UPDATE SET
  name = EXCLUDED.name,
  role = EXCLUDED.role,
  is_active = EXCLUDED.is_active,
  updated_at = NOW();

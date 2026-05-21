-- ============================================
-- Seed Data — Test with mock data before Zoho connects
-- Run AFTER 001_initial_schema.sql
-- ============================================

-- NOTE: Replace UUIDs and emails with real data from Onsite team.
-- These are mock records for testing the dashboard and agents.

-- ============================================
-- USERS (Sample team structure)
-- ============================================

-- Founder
INSERT INTO users (id, email, name, role, phone, zoho_user_id) VALUES
('00000000-0000-0000-0000-000000000001', 'sumit@onsite.team', 'Sumit (Founder)', 'founder', '919999900001', NULL);

-- Managers
INSERT INTO users (id, email, name, role, team, phone, zoho_user_id) VALUES
('00000000-0000-0000-0000-000000000002', 'manager1@onsite.team', 'Rahul (Manager)', 'manager', 'Team A', '919999900002', NULL),
('00000000-0000-0000-0000-000000000003', 'manager2@onsite.team', 'Priya (Manager)', 'manager', 'Team B', '919999900003', NULL);

-- Team Leads
INSERT INTO users (id, email, name, role, team, team_lead_id, phone, zoho_user_id) VALUES
('00000000-0000-0000-0000-000000000010', 'tl1@onsite.team', 'Amit (Team Lead)', 'team_lead', 'Team A', '00000000-0000-0000-0000-000000000002', '919999900010', NULL),
('00000000-0000-0000-0000-000000000011', 'tl2@onsite.team', 'Neha (Team Lead)', 'team_lead', 'Team B', '00000000-0000-0000-0000-000000000003', '919999900011', NULL);

-- Sales Reps (Team A)
INSERT INTO users (id, email, name, role, team, team_lead_id, phone, zoho_user_id) VALUES
('00000000-0000-0000-0000-000000000101', 'ravi@onsite.team', 'Ravi Kumar', 'rep', 'Team A', '00000000-0000-0000-0000-000000000010', '919999900101', NULL),
('00000000-0000-0000-0000-000000000102', 'sanjay@onsite.team', 'Sanjay Patel', 'rep', 'Team A', '00000000-0000-0000-0000-000000000010', '919999900102', NULL),
('00000000-0000-0000-0000-000000000103', 'vikram@onsite.team', 'Vikram Singh', 'rep', 'Team A', '00000000-0000-0000-0000-000000000010', '919999900103', NULL);

-- Sales Reps (Team B)
INSERT INTO users (id, email, name, role, team, team_lead_id, phone, zoho_user_id) VALUES
('00000000-0000-0000-0000-000000000201', 'anita@onsite.team', 'Anita Sharma', 'rep', 'Team B', '00000000-0000-0000-0000-000000000011', '919999900201', NULL),
('00000000-0000-0000-0000-000000000202', 'deepak@onsite.team', 'Deepak Gupta', 'rep', 'Team B', '00000000-0000-0000-0000-000000000011', '919999900202', NULL),
('00000000-0000-0000-0000-000000000203', 'pooja@onsite.team', 'Pooja Reddy', 'rep', 'Team B', '00000000-0000-0000-0000-000000000011', '919999900203', NULL);

-- Admin
INSERT INTO users (id, email, name, role, phone, zoho_user_id) VALUES
('00000000-0000-0000-0000-000000000999', 'admin@onsite.team', 'System Admin', 'admin', '919999900999', NULL);

-- ============================================
-- LEADS (Mock construction leads)
-- ============================================

INSERT INTO leads (id, zoho_lead_id, company, contact_name, phone, email, source, stage, deal_value, industry, geography, assigned_rep_id, last_activity_at, zoho_created_at) VALUES
-- Ravi's leads
('10000000-0000-0000-0000-000000000001', 'ZL001', 'ABC Construction Pvt Ltd', 'Rajesh Mehta', '919876500001', 'rajesh@abcconstruction.in', 'website', 'demo', 5000000, 'Construction', 'Mumbai', '00000000-0000-0000-0000-000000000101', NOW() - INTERVAL '2 days', NOW() - INTERVAL '30 days'),
('10000000-0000-0000-0000-000000000002', 'ZL002', 'Metro Builders', 'Sunil Agarwal', '919876500002', 'sunil@metrobuilders.in', 'referral', 'proposal', 8000000, 'Construction', 'Delhi', '00000000-0000-0000-0000-000000000101', NOW() - INTERVAL '1 day', NOW() - INTERVAL '20 days'),
('10000000-0000-0000-0000-000000000003', 'ZL003', 'Green Infra Solutions', 'Meera Kapoor', '919876500003', 'meera@greeninfra.in', 'cold_call', 'contacted', 2000000, 'Infrastructure', 'Bangalore', '00000000-0000-0000-0000-000000000101', NOW() - INTERVAL '10 days', NOW() - INTERVAL '45 days'),
('10000000-0000-0000-0000-000000000004', 'ZL004', 'Skyline Projects', 'Arjun Reddy', '919876500004', 'arjun@skylineprojects.in', 'website', 'new', 3500000, 'Real Estate', 'Hyderabad', '00000000-0000-0000-0000-000000000101', NOW() - INTERVAL '15 days', NOW() - INTERVAL '15 days'),

-- Sanjay's leads
('10000000-0000-0000-0000-000000000005', 'ZL005', 'Tata Projects Ltd', 'Vikash Kumar', '919876500005', 'vikash@tataprojects.in', 'referral', 'negotiation', 15000000, 'Construction', 'Mumbai', '00000000-0000-0000-0000-000000000102', NOW() - INTERVAL '1 day', NOW() - INTERVAL '60 days'),
('10000000-0000-0000-0000-000000000006', 'ZL006', 'Prestige Constructions', 'Lakshmi Narayan', '919876500006', 'lakshmi@prestige.in', 'ads', 'demo', 6000000, 'Real Estate', 'Chennai', '00000000-0000-0000-0000-000000000102', NOW() - INTERVAL '3 days', NOW() - INTERVAL '25 days'),

-- Anita's leads
('10000000-0000-0000-0000-000000000007', 'ZL007', 'DLF Infrastructure', 'Amit Verma', '919876500007', 'amit@dlf.in', 'website', 'proposal', 12000000, 'Real Estate', 'Gurgaon', '00000000-0000-0000-0000-000000000201', NOW() - INTERVAL '2 days', NOW() - INTERVAL '40 days'),
('10000000-0000-0000-0000-000000000008', 'ZL008', 'L&T Construction', 'Prashant Joshi', '919876500008', 'prashant@lnt.in', 'referral', 'contacted', 20000000, 'Infrastructure', 'Pune', '00000000-0000-0000-0000-000000000201', NOW() - INTERVAL '8 days', NOW() - INTERVAL '35 days'),
('10000000-0000-0000-0000-000000000009', 'ZL009', 'Oberoi Realty', 'Nisha Desai', '919876500009', 'nisha@oberoi.in', 'cold_call', 'new', 4000000, 'Real Estate', 'Mumbai', '00000000-0000-0000-0000-000000000201', NOW() - INTERVAL '20 days', NOW() - INTERVAL '20 days'),

-- Deepak's leads
('10000000-0000-0000-0000-000000000010', 'ZL010', 'Godrej Properties', 'Karan Malhotra', '919876500010', 'karan@godrej.in', 'ads', 'demo', 9000000, 'Real Estate', 'Mumbai', '00000000-0000-0000-0000-000000000202', NOW() - INTERVAL '1 day', NOW() - INTERVAL '15 days'),

-- Won deals (for "Match Past Wins")
('10000000-0000-0000-0000-000000000050', 'ZL050', 'Shapoorji Pallonji', 'Dev Sharma', '919876500050', 'dev@shapoorji.in', 'referral', 'won', 10000000, 'Construction', 'Mumbai', '00000000-0000-0000-0000-000000000101', NOW() - INTERVAL '60 days', NOW() - INTERVAL '120 days'),
('10000000-0000-0000-0000-000000000051', 'ZL051', 'Sobha Developers', 'Rina Patel', '919876500051', 'rina@sobha.in', 'website', 'won', 7500000, 'Real Estate', 'Bangalore', '00000000-0000-0000-0000-000000000201', NOW() - INTERVAL '45 days', NOW() - INTERVAL '90 days'),
('10000000-0000-0000-0000-000000000052', 'ZL052', 'Brigade Enterprises', 'Manoj Rao', '919876500052', 'manoj@brigade.in', 'referral', 'won', 5500000, 'Construction', 'Bangalore', '00000000-0000-0000-0000-000000000102', NOW() - INTERVAL '30 days', NOW() - INTERVAL '75 days');

-- ============================================
-- LEAD NOTES (Mock CRM notes)
-- ============================================

INSERT INTO lead_notes (lead_id, note_text, note_source, note_date) VALUES
('10000000-0000-0000-0000-000000000001', 'First call: Rajesh is interested in our project management module. He manages 3 active construction sites. Main pain: tracking material delivery across sites.', 'zoho', NOW() - INTERVAL '25 days'),
('10000000-0000-0000-0000-000000000001', 'Demo completed. Rajesh was impressed with the dashboard. Asked about mobile app availability. Wants pricing for 50 users.', 'zoho', NOW() - INTERVAL '10 days'),
('10000000-0000-0000-0000-000000000001', 'Follow-up call: He mentioned competitor Procore is also pitching. We need to highlight our India-specific features.', 'zoho', NOW() - INTERVAL '2 days'),

('10000000-0000-0000-0000-000000000002', 'Referral from Shapoorji. Metro Builders is expanding to 5 new sites. They need billing + project tracking. Decision maker is Sunil (MD).', 'zoho', NOW() - INTERVAL '18 days'),
('10000000-0000-0000-0000-000000000002', 'Proposal sent: Rs 50L annual + implementation. Sunil wants to discuss with his CFO. Meeting next week.', 'zoho', NOW() - INTERVAL '5 days'),

('10000000-0000-0000-0000-000000000005', 'Big deal. Tata Projects looking for enterprise solution for 200+ users. Current pain: using Excel for tracking.', 'zoho', NOW() - INTERVAL '45 days'),
('10000000-0000-0000-0000-000000000005', 'Negotiation phase. They want 20% discount. We offered 10% with 2-year commitment. Decision expected this month.', 'zoho', NOW() - INTERVAL '1 day'),

('10000000-0000-0000-0000-000000000007', 'DLF wants a POC on one project first. If successful, rollout to all 8 ongoing projects. Huge potential.', 'zoho', NOW() - INTERVAL '30 days'),
('10000000-0000-0000-0000-000000000007', 'POC running on their Gurgaon project. Amit (VP Projects) is the champion. CEO approval needed for company-wide.', 'zoho', NOW() - INTERVAL '2 days');

-- ============================================
-- LEAD ACTIVITIES (Mock calls/meetings)
-- ============================================

INSERT INTO lead_activities (lead_id, activity_type, subject, outcome, duration_minutes, performed_by, activity_date) VALUES
('10000000-0000-0000-0000-000000000001', 'call', 'Intro call', 'connected', 15, '00000000-0000-0000-0000-000000000101', NOW() - INTERVAL '25 days'),
('10000000-0000-0000-0000-000000000001', 'meeting', 'Product demo', 'completed', 45, '00000000-0000-0000-0000-000000000101', NOW() - INTERVAL '10 days'),
('10000000-0000-0000-0000-000000000001', 'call', 'Follow-up after demo', 'connected', 10, '00000000-0000-0000-0000-000000000101', NOW() - INTERVAL '2 days'),

('10000000-0000-0000-0000-000000000002', 'call', 'Referral intro', 'connected', 20, '00000000-0000-0000-0000-000000000101', NOW() - INTERVAL '18 days'),
('10000000-0000-0000-0000-000000000002', 'email', 'Proposal sent', 'delivered', NULL, '00000000-0000-0000-0000-000000000101', NOW() - INTERVAL '5 days'),
('10000000-0000-0000-0000-000000000002', 'call', 'Pricing discussion', 'connected', 30, '00000000-0000-0000-0000-000000000101', NOW() - INTERVAL '1 day'),

('10000000-0000-0000-0000-000000000005', 'meeting', 'Enterprise pitch', 'completed', 60, '00000000-0000-0000-0000-000000000102', NOW() - INTERVAL '45 days'),
('10000000-0000-0000-0000-000000000005', 'call', 'Negotiation call', 'connected', 25, '00000000-0000-0000-0000-000000000102', NOW() - INTERVAL '1 day'),

('10000000-0000-0000-0000-000000000010', 'call', 'Intro call', 'connected', 12, '00000000-0000-0000-0000-000000000202', NOW() - INTERVAL '10 days'),
('10000000-0000-0000-0000-000000000010', 'meeting', 'Demo session', 'completed', 40, '00000000-0000-0000-0000-000000000202', NOW() - INTERVAL '1 day');

-- ============================================
-- DONE. Now you can test the dashboard!
-- ============================================

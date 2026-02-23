# Sales Intelligence System — Test Cases

> Validation scenarios for the Sales Intelligence System. Use after deployment, feature changes, or agent modifications.

---

## Test 1: CSV Upload and Dashboard Population

**Input:**
- Upload `Onsite_Entire_Leads.csv` via Intelligence page
- CSV contains ~500 leads with all standard columns

**Expected:**
- [ ] Upload succeeds (200 response from `/api/intelligence/compute`)
- [ ] Intelligence dashboard populates with 8 tabs:
  - Sales, Overview, Pipeline, Team, Sources, Aging, Trends, Deep Dive
- [ ] `dashboard_summary` table has new JSONB record
- [ ] `agent_profiles` table populated for each unique `deal_owner`
- [ ] Smart Alerts generated (check `alerts` table)
- [ ] Revenue shows only `sale_done=1` records
- [ ] Revenue parsed correctly from "Rs. 42,000.00" format

**Failure indicators:**
- Empty tabs → check CSV column mapping
- Wrong revenue → check `Rs.` parsing logic
- Missing agents → check `deal_owner` extraction

---

## Test 2: Lead Scoring Accuracy

**Input: Hot Lead**
```
lead_name: "Rajesh Kumar"
company_name: "BuildPro Infrastructure Pvt Ltd"
annual_revenue: "Rs. 15,00,000.00"
demo_done: 1
demo_booked: 1
sale_done: 0
lead_status: "Contacted"
call_disposition: "Interested"
```

**Expected:**
- Score > 70
- Classification: HOT
- Reasoning mentions: demo completed, revenue > 10Cr threshold, active engagement
- Next action: "Schedule follow-up call within 24 hours"

**Input: Cold Lead**
```
lead_name: "Unknown"
company_name: ""
annual_revenue: ""
demo_done: 0
demo_booked: 0
lead_status: "Not Contacted"
call_disposition: ""
```

**Expected:**
- Score < 30
- Classification: COLD
- Reasoning mentions: no company info, no engagement, no revenue data
- Next action: "Add to automated drip campaign"

---

## Test 3: Morning Brief Generation

**Input:**
- Trigger: `POST /api/cron/morning-digest`
- Time: Should normally fire at 7:30 AM IST

**Expected:**
- [ ] Each deal owner with active leads gets a personalized brief
- [ ] Brief contains:
  - Today's priority actions (top 3 leads to call)
  - Hot signals from overnight (new demos, stage changes)
  - Pipeline snapshot (value vs target)
  - One coaching tip
- [ ] Brief under 300 words
- [ ] Delivered via configured channel (Telegram/email)
- [ ] `daily_briefs` table has new records
- [ ] Brief scoped to each rep's own leads only (not all leads)

---

## Test 4: Smart Alert Rules

**Input:** Upload CSV and verify these alerts trigger:

| Alert Rule | Trigger Condition | Expected Severity |
|-----------|------------------|------------------|
| Stale Lead | Lead not touched in >14 days | HIGH |
| Demo Dropout | `demo_booked=1`, `demo_done=0`, >7 days | HIGH |
| Low Conversion | Rep win rate <10% (>20 leads) | MEDIUM |
| Hot Prospect | Score >80, no follow-up scheduled | CRITICAL |
| Priority Overload | Rep has >5 HOT leads simultaneously | MEDIUM |
| Inactive Agent | Rep has 0 activity in last 7 days | HIGH |
| Top Performer | Rep has highest conversion this month | INFO |
| Revenue Milestone | Team revenue crosses target threshold | INFO |
| Pipeline Risk | Pipeline coverage <2x quota | HIGH |
| Follow-up Needed | Activity >3 days old with no next step | MEDIUM |

**Verify:**
- [ ] Alerts appear in `/alerts` page with correct severity badges
- [ ] Alert count shows in sidebar/header
- [ ] Mark-as-read works
- [ ] Correct alert delivered to correct rep (scoped by deal_owner)

---

## Test 5: Research Agent (On-Demand)

**Input:**
- Select a lead from the dashboard
- Click "Research" button (triggers `/api/research`)
- Lead: "Prestige Group" (large construction company)

**Expected:**
- [ ] Research completes in <30 seconds
- [ ] Response contains:
  - Company overview (from web search)
  - CRM history analysis (from lead notes)
  - Close strategy with talking points
  - Objection handling suggestions
  - Pricing recommendation
  - Risk factors
- [ ] Results saved to `lead_research` table
- [ ] Results displayed in Lead Detail page

---

## Test 6: Role-Based Access Control

| User Role | Expected Access |
|-----------|----------------|
| Sales Rep (deal_owner: "Rahul") | Only sees Rahul's leads and stats |
| Team Lead | Sees their team's data |
| Manager | Sees all teams |
| Founder | Everything + analytics + weekly reports |
| Admin (Dhruv) | Full access including settings, LLM config, user CRUD |

**Test Steps:**
1. Login as each role
2. Navigate to Dashboard → verify data scoping
3. Navigate to Intelligence → verify filtered view
4. Navigate to Admin → verify access denied for non-admins
5. Try API call with wrong role JWT → verify 403 response

---

## Test 7: Agent Profile Accuracy

**Input:** After CSV upload, check Agent Profiles page

**Expected per rep:**
- [ ] Total leads count matches CSV filter by deal_owner
- [ ] Conversion rate = sale_done / total_leads
- [ ] Active leads count correct
- [ ] Revenue = sum of annual_revenue where sale_done=1
- [ ] Strengths/concerns auto-generated and reasonable
- [ ] Monthly history chart populated

---

## Test 8: Weekly Report

**Input:**
- Trigger: `POST /api/cron/weekly-report` (normally Monday 8 AM)

**Expected:**
- [ ] Report generated with 7 sections:
  1. Executive Summary
  2. Pipeline Overview
  3. Per-Rep Scorecard
  4. Revenue Forecast
  5. Deals at Risk
  6. Wins/Losses This Week
  7. Recommendations
- [ ] Emailed to founder + managers
- [ ] Saved to `weekly_reports` table
- [ ] Uses correct column names (not `stage`/`company` mismatches)

**Known Issue:** `weekly_report.py` has column name mismatches (`stage` vs `status`, `company` vs `company_name`). Verify these are fixed before testing.

---

## Integration Test: End-to-End Flow

1. Upload CSV → dashboard populates
2. Alerts generated → check alert list
3. Morning brief fires → check Telegram
4. Click research on a lead → strategy returned
5. Admin changes LLM provider → next agent run uses new provider
6. Weekly report fires → email received

All 6 steps should work without errors. Check backend logs for any 500s.

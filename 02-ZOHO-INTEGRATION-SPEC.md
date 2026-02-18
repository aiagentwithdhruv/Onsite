# Zoho CRM Integration Spec

**This doc covers everything the developer needs to build the Zoho ↔ Supabase sync layer.**

---

## 1. Authentication (OAuth 2.0)

Zoho uses OAuth 2.0 with refresh tokens. **Tokens expire every 60 minutes.** The system MUST handle this automatically.

### Flow:
```
1. One-time: Admin authorizes app → gets authorization_code
2. Exchange code → get access_token (1 hour) + refresh_token (no expiry*)
3. Store refresh_token in Supabase (encrypted) or env var
4. Before EVERY API call: check if access_token expires in < 5 min
5. If yes: POST to /oauth/v2/token with refresh_token → get new access_token
6. If refresh fails: alert admin via email, log error, use cached data
```

*Note: Zoho refresh tokens don't expire but can be revoked. If revoked, manual re-auth needed.

### Token Refresh Endpoint:
```
POST https://accounts.zoho.in/oauth/v2/token
  grant_type=refresh_token
  refresh_token={stored_refresh_token}
  client_id={client_id}
  client_secret={client_secret}
```

### Store These Securely (env vars, NOT in code):
```
ZOHO_CLIENT_ID=
ZOHO_CLIENT_SECRET=
ZOHO_REFRESH_TOKEN=
ZOHO_ACCESS_TOKEN=          # auto-refreshed
ZOHO_TOKEN_EXPIRY=          # epoch timestamp
```

---

## 2. Rate Limits

Zoho CRM API limits (depends on plan):

| Plan | API Credits/Day | Credits/Minute |
|------|----------------|----------------|
| Standard | 5,000 | 100 |
| Professional | 10,000 | 100 |
| Enterprise | 25,000 | 200 |
| Ultimate | 50,000 | 200 |

**1 API call = 1 credit.** Bulk APIs count differently.

### Our Strategy:
- **Delta sync** (only changed records) reduces calls by ~80-90%
- **Batch requests** where possible (fetch 200 records per call, max)
- **Exponential backoff** on 429 (rate limit) responses
- **Track credit usage** in Supabase table `zoho_sync_log`

### Rate Limit Handling (Python):
```python
import time

async def zoho_api_call(endpoint, params, max_retries=3):
    for attempt in range(max_retries):
        response = await httpx.get(endpoint, params=params, headers=headers)

        if response.status_code == 429:
            wait_time = min(2 ** attempt * 10, 120)  # 10s, 20s, 40s... max 2min
            log.warning(f"Zoho rate limit hit. Waiting {wait_time}s...")
            await asyncio.sleep(wait_time)
            continue

        if response.status_code == 401:
            await refresh_zoho_token()
            continue

        response.raise_for_status()
        return response.json()

    raise ZohoRateLimitExceeded("Max retries hit for Zoho API")
```

---

## 3. Delta Sync Strategy

**Problem:** Fetching ALL leads/deals/notes every 2 hours wastes API credits and hits rate limits.

**Solution:** Use Zoho's `Modified_Time` filter to only fetch records changed since last sync.

### How It Works:
```
1. Store `last_sync_timestamp` in Supabase table `sync_state`
2. On each sync run:
   - Query Zoho: GET /Leads?criteria=(Modified_Time:greater_than:{last_sync_timestamp})
   - Upsert results into Supabase (ON CONFLICT zoho_lead_id DO UPDATE)
   - Update `last_sync_timestamp` to current time
3. Full re-sync: Once per day at 2 AM (safety net for missed changes)
```

### Sync Schedule:
| Sync Type | Schedule | What It Fetches |
|-----------|----------|----------------|
| Delta sync | Every 2 hours (8AM-10PM) | Only records changed since last sync |
| Full sync | 2 AM daily | Everything (safety net) |
| Webhook sync | Real-time | New leads only (via Zoho webhook) |

### Zoho API Endpoints to Use:

| Module | Endpoint | What We Get |
|--------|----------|------------|
| Leads | `GET /crm/v8/Leads` | All lead data: name, company, phone, email, source, stage, owner |
| Deals | `GET /crm/v8/Deals` | Deal value, stage, closing date, associated contacts |
| Contacts | `GET /crm/v8/Contacts` | Contact details linked to leads/deals |
| Notes | `GET /crm/v8/Notes` | All notes across leads/deals/contacts |
| Activities | `GET /crm/v8/Activities` | Calls, tasks, events, meetings |
| Call Logs | `GET /crm/v8/Calls` | Call duration, outcome, who called |
| Users | `GET /crm/v8/users` | Sales rep list with IDs (for mapping) |

### Field Mapping (Zoho → Supabase):

```
Zoho Lead Fields → leads table:
  id                → zoho_lead_id
  Company           → company
  Full_Name         → contact_name
  Phone             → phone
  Email             → email
  Lead_Source        → source
  Lead_Status        → stage
  Amount            → deal_value (if available, else from Deal)
  Owner.id          → assigned_rep_zoho_id (FK to users.zoho_user_id)
  Created_Time      → zoho_created_at
  Modified_Time     → zoho_modified_at
```

---

## 4. Zoho Webhook (for New Lead Instant Assign)

Set up a Zoho Workflow Rule that triggers on "Lead Creation":
- **Action:** Send webhook to `https://your-api.railway.app/api/webhooks/zoho/new-lead`
- **Payload:** Lead ID + basic fields
- **Our system:** Receives webhook → triggers Smart Assignment Agent → assigns rep → sends WhatsApp

### Webhook Validation:
```python
# Verify webhook is actually from Zoho (not spoofed)
# Zoho doesn't sign webhooks, so:
# 1. Accept webhook payload (lead_id)
# 2. Immediately re-fetch the lead from Zoho API to verify it exists
# 3. Only then proceed with assignment
```

---

## 5. Upsert Logic (Deduplication)

Every sync uses upsert to prevent duplicates:

```sql
INSERT INTO leads (zoho_lead_id, company, contact_name, phone, email, source, stage, deal_value, assigned_rep_id, zoho_created_at, zoho_modified_at, synced_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
ON CONFLICT (zoho_lead_id)
DO UPDATE SET
  company = EXCLUDED.company,
  contact_name = EXCLUDED.contact_name,
  phone = EXCLUDED.phone,
  email = EXCLUDED.email,
  source = EXCLUDED.source,
  stage = EXCLUDED.stage,
  deal_value = EXCLUDED.deal_value,
  assigned_rep_id = EXCLUDED.assigned_rep_id,
  zoho_modified_at = EXCLUDED.zoho_modified_at,
  synced_at = NOW();
```

---

## 6. Sync State Tracking

```sql
CREATE TABLE sync_state (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  module TEXT NOT NULL,                    -- 'leads', 'deals', 'notes', etc.
  last_sync_at TIMESTAMPTZ NOT NULL,
  records_synced INTEGER DEFAULT 0,
  status TEXT DEFAULT 'success',          -- 'success', 'partial', 'failed'
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

This lets you:
- Track when each module was last synced
- Debug sync failures
- Show sync status on admin dashboard

---

## 7. Error Scenarios & Handling

| Scenario | What Happens | Fallback |
|----------|-------------|----------|
| Zoho API down | Sync fails, retry in 30 min | Dashboard shows cached data + "Last synced: X hours ago" banner |
| Rate limit hit | Exponential backoff, retry | Queue remaining records for next sync window |
| OAuth token expired | Auto-refresh with refresh_token | If refresh fails: email admin, use cached data |
| Refresh token revoked | Can't auto-fix | Alert admin: "Zoho connection lost. Re-authorize in Admin Settings." |
| Zoho field changed | Sync partial fail for that field | Log error, continue syncing other fields, alert admin |
| Network timeout | Retry 3 times with backoff | Mark sync as "partial", try full sync next cycle |

# Runbook: Zoho CRM Credential Setup

> How to get OAuth credentials from Zoho CRM for the Sales Intelligence System integration.

---

## Pre-Checks

- [ ] Admin access to Onsite's Zoho CRM account
- [ ] Know the Zoho data center (likely `.in` for India accounts)
- [ ] Backend deployed with accessible callback URL

---

## Step 1: Register API Client in Zoho

1. Go to [Zoho API Console](https://api-console.zoho.in/) (use `.in` for India)
2. Click **Add Client** → **Server-based Applications**
3. Fill in:
   - **Client Name:** `Onsite Sales Intelligence`
   - **Homepage URL:** `https://intelligence.onsiteteams.com` (or your frontend URL)
   - **Authorized Redirect URI:** `https://<backend-url>/api/auth/zoho/callback`
4. Click **Create**
5. Note down:
   - **Client ID:** `1000.XXXXXXXXXXXX`
   - **Client Secret:** `XXXXXXXXXXXXXXXX`

---

## Step 2: Generate Authorization Code

1. Open this URL in a browser (replace placeholders):
   ```
   https://accounts.zoho.in/oauth/v2/auth?
     scope=ZohoCRM.modules.ALL,ZohoCRM.settings.ALL,ZohoCRM.users.ALL,ZohoCRM.notifications.ALL&
     client_id=<CLIENT_ID>&
     response_type=code&
     access_type=offline&
     redirect_uri=<REDIRECT_URI>&
     prompt=consent
   ```
2. Log in as Zoho admin
3. Grant permissions
4. You'll be redirected to the callback URL with `?code=<AUTH_CODE>`
5. Copy the authorization code (valid for ~2 minutes)

### Required Scopes:
| Scope | Why |
|-------|-----|
| `ZohoCRM.modules.ALL` | Read/write leads, deals, contacts, notes, activities |
| `ZohoCRM.settings.ALL` | Read field definitions, layouts, pipeline stages |
| `ZohoCRM.users.ALL` | Read sales rep info for assignment |
| `ZohoCRM.notifications.ALL` | Set up webhooks for real-time sync |

---

## Step 3: Exchange Auth Code for Tokens

```bash
curl -X POST https://accounts.zoho.in/oauth/v2/token \
  -d "grant_type=authorization_code" \
  -d "client_id=<CLIENT_ID>" \
  -d "client_secret=<CLIENT_SECRET>" \
  -d "redirect_uri=<REDIRECT_URI>" \
  -d "code=<AUTH_CODE>"
```

Response:
```json
{
  "access_token": "1000.XXXXXXXX",
  "refresh_token": "1000.XXXXXXXX",
  "api_domain": "https://www.zohoapis.in",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Save the refresh_token** — it doesn't expire unless revoked.

---

## Step 4: Configure Environment Variables

Set these in Railway (backend):

```bash
ZOHO_CLIENT_ID=1000.XXXXXXXXXXXX
ZOHO_CLIENT_SECRET=XXXXXXXXXXXXXXXX
ZOHO_REFRESH_TOKEN=1000.XXXXXXXXXXXX
ZOHO_API_DOMAIN=https://www.zohoapis.in
ZOHO_ACCOUNTS_URL=https://accounts.zoho.in
```

---

## Step 5: Set Up Webhooks (Real-Time Sync)

### In Zoho CRM:
1. Go to **Setup → Developer Space → Webhooks**
2. Create webhooks for:

| Module | Events | Webhook URL |
|--------|--------|------------|
| Leads | Create, Edit, Delete | `https://<backend>/api/webhooks/zoho/leads` |
| Deals | Create, Edit, Delete, Stage Change | `https://<backend>/api/webhooks/zoho/deals` |
| Notes | Create, Edit | `https://<backend>/api/webhooks/zoho/notes` |

3. Set notification URL format: **JSON**
4. Add these fields to each webhook payload:
   - Lead/Deal ID, Owner, Stage, Modified Time
   - Max 10 fields per webhook

### In Zoho Workflow Rules:
1. Go to **Setup → Automation → Workflow Rules**
2. Create rules that trigger webhooks:
   - Rule: "On Lead Create/Edit" → Action: Call webhook
   - Max 6 webhooks per workflow rule

---

## Step 6: Test the Integration

### Test 1: Token Refresh
```bash
curl -X POST https://accounts.zoho.in/oauth/v2/token \
  -d "grant_type=refresh_token" \
  -d "client_id=<CLIENT_ID>" \
  -d "client_secret=<CLIENT_SECRET>" \
  -d "refresh_token=<REFRESH_TOKEN>"
```
Expected: New access_token returned.

### Test 2: API Call
```bash
curl https://www.zohoapis.in/crm/v8/Leads?per_page=5 \
  -H "Authorization: Zoho-oauthtoken <ACCESS_TOKEN>"
```
Expected: JSON with lead records.

### Test 3: Webhook Delivery
1. Edit a lead in Zoho CRM
2. Check backend logs for incoming webhook
3. Verify lead updated in Supabase

### Test 4: Full Sync
```bash
curl -X POST https://<backend>/api/admin/sync/trigger \
  -H "Authorization: Bearer <JWT>"
```
Expected: Sync completes, `sync_state` table updated.

---

## Rate Limits to Know

| Limit | Value |
|-------|-------|
| API calls/day/org | Min 4,000, max 25,000 (or 500/user license) |
| GET records/request | Max 200 |
| Write records/request | Max 100 |
| Active tokens per refresh | Max 15 |
| Refresh requests/10 min | Max 10 |
| Webhook fields | Max 10 per webhook |
| Webhooks per workflow | Max 6 |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "INVALID_TOKEN" error | Refresh token expired or revoked. Re-do Steps 2-3 |
| "INVALID_URL_PATTERN" | Redirect URI doesn't match registered URI exactly |
| Rate limit hit (429) | Backend has tenacity retry with exponential backoff |
| Webhook not firing | Check workflow rule is active, webhook URL accessible |
| "AUTHENTICATION_FAILURE" | Use `.zohoapis.in` domain (not `.com`) for India accounts |
| Token refresh returning error | Max 15 active tokens — revoke old ones in API console |

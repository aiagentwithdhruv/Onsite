# Multi-Tenancy Architecture — Deep Dive

> How one deployment safely serves 10,000+ Onsite customers.

---

## The Hard Question (Sumit will ask this)

> *"If I have 10,000 customers, can one of them ever — through any bug, race, or attack — see another's tasks via this bot?"*

**Answer:** No. Structurally impossible in MVP. Here's why and how we keep it that way.

---

## Tenancy Model: Stateless-per-Request

```
                Tenant A's Browser          Tenant B's Browser
                       │                            │
                       │ JWT_A                      │ JWT_B
                       ▼                            ▼
                  POST /api/task-bot          POST /api/task-bot
                       │                            │
              ┌────────┴────────────────────────────┴────────┐
              │  Vercel Function (stateless)                  │
              │  - No DB connection                           │
              │  - No memory of previous requests             │
              │  - No filesystem writes                       │
              │  - Token lives only in this request lifecycle│
              └────────┬────────────────────────────┬────────┘
                       │                            │
                       │ Bearer JWT_A               │ Bearer JWT_B
                       ▼                            ▼
                  Onsite API                  Onsite API
                  (returns A's data)          (returns B's data)
```

The Vercel function does not know it's handling tenant A vs tenant B. It just proxies whatever JWT came in. Onsite's API does the actual tenancy check.

**The invariant:** Our service is a tenant-blind transport. We never decide who can see what.

---

## What Makes Isolation Trivial

| Concern | Mitigation |
|---------|-----------|
| **Cache leakage** | No cache (no Redis, no in-memory cache, no LRU) |
| **Database mis-query** | No database |
| **Session collision** | No sessions; conversation lives in browser only |
| **Filesystem cross-read** | Vercel functions have ephemeral, isolated filesystems |
| **Log file mix** | Logs contain only timing + status; no request body content |
| **LLM context leak** | Each LLM call is fresh; no kv-cache shared across customers |
| **Worker process reuse** | Vercel may reuse warm workers, but no mutable shared state exists |
| **Token in error message** | Errors from Onsite are pre-sanitized before display |

---

## Tenant Identity Flow

1. Customer logs into Onsite — Onsite issues JWT with embedded `user_id`, `uuid`, `exp`
2. Customer opens our bot; pastes JWT (MVP) or it's passed via postMessage (Phase 3)
3. JWT stored in `sessionStorage` (NOT `localStorage` — clears on tab close)
4. Each chat request sends `{messages, token}` to our API
5. Our API calls Onsite with `Authorization: Bearer <jwt>`
6. Onsite decodes JWT → resolves user → resolves company → scopes the response data
7. Our API receives company-scoped data, passes through to user

**At no point** does our service know the company_id beyond what's in the JWT. We don't decode the JWT. We don't need to.

---

## Stateful Features (Phase 3+) — Required Mitigations

When we add audit logs, conversation history, or per-customer preferences:

### Database choice: Supabase (Postgres + RLS)

**Why Supabase:**
- Row-Level Security is enforced by Postgres itself, not application code
- A bug in our code can't bypass RLS — even superuser queries get filtered
- Anon-key + JWT pattern: pass user's JWT to Supabase, RLS uses it for filtering

### Schema pattern

Every table has `company_id UUID NOT NULL` + RLS policy:

```sql
CREATE TABLE audit_log (
  id UUID PRIMARY KEY,
  company_id UUID NOT NULL,
  user_id UUID NOT NULL,
  tool_name TEXT,
  args JSONB,
  success BOOLEAN,
  created TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "tenant_isolation" ON audit_log
  FOR ALL
  USING (company_id = (current_setting('request.jwt.claims', true)::json ->> 'company_id')::uuid);
```

Every query gets filtered to the JWT's company_id automatically.

### Forbidden patterns (audit checklist)

- ❌ Service-role queries from user-facing API routes
- ❌ `SELECT * FROM audit_log` without WHERE company_id (RLS would block, but don't rely on it — write the filter)
- ❌ Cross-tenant joins
- ❌ Cron jobs reading multiple customers' data without an explicit batch boundary
- ❌ Logs that contain `company_id` + content together (separate streams)

---

## Threat Model

### Threats we defend against

| Threat | Mitigation |
|--------|-----------|
| Stolen JWT replayed by attacker | JWT exp validated by Onsite; we don't extend lifetime |
| XSS in chat → token exfiltration | Strict CSP; sessionStorage scoped to origin |
| Tenant A's browser bug sends to tenant B's API | Each request has its own JWT; no session pinning |
| Our service compromised | Nothing to steal (no DB, no logs of content) |
| LLM provider compromised | LLM never received JWT or sensitive PII |
| Onsite API compromised | Out of our scope — Onsite's responsibility |
| Tenant A admins write a malicious chat message | Affects only their own tenant; can't escalate |

### Threats we explicitly do NOT defend against

- Tenant's own admin abuses the bot to damage their own data (that's their problem; we provide audit log so they can investigate)
- Compromise of the customer's browser/device
- Compromise of Onsite's authentication system

---

## What an Audit Would Check

Quarterly review:

1. **Code grep:** Does any file in `src/` reference `process.env` for credentials beyond `OPENROUTER_API_KEY`? Should be no.
2. **Log inspection:** Does any log line contain a JWT? a UUID identifying a customer beyond company_id? task content? Should be no.
3. **Network mock:** Send a request with tenant A's JWT but tenant B's UUIDs in the body. Onsite should reject with 403. Verify.
4. **Concurrent request stress test:** Fire 100 simultaneous requests with 10 different JWTs. Each response must contain only data scoped to its JWT.
5. **Memory profiler:** After 1000 requests, does any tenant-identifying data persist in process memory? Should be no (V8 may not GC immediately, but no references should remain).
6. **Dependency review:** Did any new npm package get added that opens a network port, writes to disk, or maintains state?

---

## Cost of Tenancy at Scale

With 10,000 active customers:

- Vercel function calls: negligible (per-invocation pricing)
- LLM calls: ~$1,500/month (see [HLD § Cost](../HLD.md#6-cost-architecture))
- Bandwidth: also negligible (text-only conversations)
- **Total marginal cost per tenant: < ₹15/month**

If Sumit charges ₹100/user/month for this feature, gross margin is 85%+.

---

## Compliance Note

**India DPDP Act (Digital Personal Data Protection):**
- We don't store personal data in MVP → no DPA / consent flow needed
- Phase 3 audit log will contain user_id + tool_name + args → need:
  - Data inventory in DPDP audit
  - Customer data export endpoint
  - Customer data deletion endpoint
  - Retention policy (default: 90 days for audit; configurable)

**GDPR (if Onsite has EU customers):**
- Same principles, more paperwork
- Defer until Onsite has actual EU users (not in current customer base per the company doc)

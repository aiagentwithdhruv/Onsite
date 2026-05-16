# API Specs — Onsite v3

> Catalog of every Onsite API endpoint the bot uses or needs. Each entry has the exact request format Akshansh provided (or the format we need to request).

**Base URLs:**
- Test: `https://testapi.onsiteteams.in`
- Prod: `https://api.onsiteteams.in`

**Auth:** `Authorization: Bearer <jwt>` header on every call.

**Common patterns observed:**
- Routes follow `/apis/v3/<verb>/<resource>` (e.g., `/apis/v3/add/taskdependency`)
- POST for create/update; PATCH for status transitions (only `mark-start` so far)
- Responses include `monkey_patch_*` fields with denormalized join data
- Custom request headers used by Onsite frontend: `Project-Id`, `Project-Company-Id`, `enterprise-id`, `version-code` (not required for endpoints we've used)

---

## ✅ Built (specs received + integrated)

### 1. Create Task Dependency

**Endpoint:** `POST /apis/v3/add/taskdependency`

**Payload:**
```json
{
  "primary_ba_id": "bffa4dc0-ceba-4f66-b9f8-f915d95bd1ca",
  "secondary_ba_id": "4bbdb581-5e84-4667-92cc-e513f4851589",
  "type": "finish_to_start",
  "lag": 5
}
```

**Type enum:** `finish_to_start` | `finish_to_finish` | `start_to_start` | `start_to_finish`

**Server-side validations:**
- Both BAs must exist
- Both BAs must be **leaf nodes** (no children) — else `"only leaf node can be dependency"`
- Both BAs must be in the **same workorder** — else `"Primary and secondary task must be in the same workorder"`
- Both BAs must be different — else `"Primary and secondary task must be different"`
- Workorder must allow `ADD_TASK` policy for current user
- No cyclic dependencies (server runs cycle detection)
- `lag` must be ≤ 1000

**Success response (200):** Returns the created `TaskDependency` object with `monkey_patch_primary_ba` and `monkey_patch_secondary_ba` denormalized, plus side-effect: `UpdatedBillingActivity` array (re-computed parent dates/progress).

```json
{
  "task_dependency": {
    "id": "d374d749-0270-40fb-80c1-a672e9824341",
    "primary_ba_id": "22200f57-402b-4755-811c-faf67ed02135",
    "secondary_ba_id": "54a68548-e2b6-48f4-b883-94e75f156497",
    "type": "finish_to_start",
    "lag": 0,
    "workorder_id": "82949d5b-edeb-498e-90ba-9b6c250bdd3a",
    "company_id": "ceb9fce3-...",
    "created": "2026-05-16T20:02:55.088Z",
    ...
  },
  "updated_billing_activity": [...]
}
```

**Status:** ✅ Integrated as tool `create_task_dependency`

---

### 2. Record Task Progress

**Endpoint:** `POST /apis/v3/add/billingprogresshistory`

**Payload:**
```json
{
  "measurement": {"length": 0, "width": 0, "height": 0},
  "diff_quantity": 4,
  "location_id": "f636c742-4ff3-4bab-bd52-3ce783b1d536",
  "progress_date": "2026-05-16T07:08:44.263Z",
  "billing_sub_activity_id": "67f79921-6ba9-4898-bb32-a51a74b053d5",
  "notes": "custom notes here"
}
```

**Field notes:**
- `billing_sub_activity_id` is the sub-activity (a child of a BA), NOT the BA itself
- `location_id` appears unused in practice — real entries have empty string. Default to `""` in our requests.
- `measurement` defaults to `{length:0, width:0, height:0}` if not specifying dimensions
- `notes` optional
- `progress_date` ISO 8601 UTC

**Status:** ✅ Integrated as tool `record_task_progress`

---

## ⚠️ Observed but not integrated (specs needed)

### 3. Mark Task Started (status transition)

**Endpoint:** `PATCH /apis/v3/edit/progress/billingactivity/mark-start`

**Observed in Network tab.** Returns task data with updated status. No payload visible yet (probably just task ID in URL or empty body).

**Needs spec from Akshansh:**
- Full URL pattern (is there a task ID in the path?)
- Request body
- What fields update on the BA

**Status:** Endpoint URL known, body unknown.

---

## ❌ Need specs from Akshansh

### 4. List Projects

**Why we need it:** So bot can say "Soul Space project" instead of customer pasting a project UUID.

**Proposed endpoint:** `POST /apis/v3/list/project`

**Proposed payload:**
```json
{
  "company_id": "ceb9fce3-f5e4-49ce-8196-d09f3b510bb6",
  "search_query": "soul",   // optional
  "status": "Ongoing"        // optional
}
```

**Expected response:** Array of `{id, name, status, ...}`

---

### 5. List Billing Activities (Tasks)

**Why we need it:** So bot can disambiguate "Electrical panel" → ask "is it the one in Soul Space or HVAC Project?"

**Proposed endpoint:** `POST /apis/v3/list/billingactivity`

**Proposed payload:**
```json
{
  "project_id": "9f26e601-da18-431d-8af2-b68b373e930e",
  "workorder_id": "82949d5b-edeb-498e-90ba-9b6c250bdd3a",   // optional, narrows scope
  "search_query": "electrical",                              // optional
  "only_leaves": true                                        // optional, useful for dependency picker
}
```

**Expected response:** Array of `{id, name, parent_id, children_ids, workorder_id, ...}`

---

### 6. List Sub-Activities (Locations under a Task)

**Why we need it:** So bot can ask "log progress on Electrical panel Setup → Location 1, 2, or 3?"

**Proposed endpoint:** `POST /apis/v3/list/billingsubactivity`

**Proposed payload:**
```json
{
  "billing_activity_id": "22200f57-402b-4755-811c-faf67ed02135"
}
```

**Expected response:** Array of `{id, name, billing_activity_id, ...}` representing each sub-activity

---

### 7. Update Task Dependency

**Why we need it:** "Change that dependency to a 3-day lag" or "make it start-to-start instead"

**Proposed endpoint:** `POST /apis/v3/update/taskdependency`

**Proposed payload:**
```json
{
  "id": "d374d749-0270-40fb-80c1-a672e9824341",
  "type": "finish_to_start",   // optional
  "lag": 3                      // optional
}
```

**Validations expected:** Same lag/type constraints as create.

---

### 8. Delete Task Dependency

**Why we need it:** "Remove that dependency I just made" — clean undo

**Proposed endpoint:** `POST /apis/v3/delete/taskdependency`

**Proposed payload:**
```json
{
  "id": "d374d749-0270-40fb-80c1-a672e9824341"
}
```

**Side effect expected:** `UpdatedBillingActivity` array (parent dates/progress recompute, since dependency removal can shift schedules)

---

### 9. Add Billing Activity (Task or Sub-Task)

**Why we need it:** "Add a sub-task 'Wire Testing' under Electrical panel Setup, 2 days, 100 ft"

**Proposed endpoint:** `POST /apis/v3/add/billingactivity`

**Proposed payload:**
```json
{
  "workorder_id": "82949d5b-edeb-498e-90ba-9b6c250bdd3a",
  "parent_id": "22200f57-402b-4755-811c-faf67ed02135",   // null/empty for top-level task
  "name": "Wire Testing",
  "unit_id": "f1c70d20-62e0-444a-9f53-7b754a5c0e70",      // numbers / ft / sqm / etc.
  "estimated_quantity": 100,
  "start_date": "2026-05-20T00:00:00Z",                   // optional
  "end_date": "2026-05-22T00:00:00Z",                     // optional
  "assigned_to": ["<user_id>"]                            // optional
}
```

**Note:** Need to know if parent BA becomes non-leaf when a child is added (yes, presumably — and any dependencies on that BA become invalid?).

---

### 10. Update Billing Activity

**Why we need it:** "Rename that task" / "extend the deadline by 5 days" / "change quantity to 150"

**Proposed endpoint:** `POST /apis/v3/update/billingactivity`

**Proposed payload:**
```json
{
  "id": "22200f57-402b-4755-811c-faf67ed02135",
  "name": "Power Panel Setup",     // optional, only fields to change
  "end_date": "2026-05-05T00:00:00Z",
  "estimated_quantity": 8,
  ...
}
```

---

## WhatsApp template for requesting from Akshansh

```
Akshansh bhai, AI task bot ke liye 7 v3 API endpoints ke specs chahiye.
Same format jaise taskdependency wala diya tha — endpoint + method + payload + handler form input + valid enum values.

1. POST /apis/v3/list/project (filters: company_id, search_query, status)
2. POST /apis/v3/list/billingactivity (filters: project_id, workorder_id, search_query, only_leaves)
3. POST /apis/v3/list/billingsubactivity (filter: billing_activity_id)
4. POST /apis/v3/update/taskdependency (id + new type/lag)
5. POST /apis/v3/delete/taskdependency (id)
6. POST /apis/v3/add/billingactivity (workorder_id, parent_id, name, unit_id, etc.)
7. POST /apis/v3/update/billingactivity (id + fields to change)

Plus confirm the `mark-start` PATCH endpoint exact body.

Agar swagger / postman export hai poori v3 API ka, that's even better — I'll extract what I need.

Hum 7 features add karenge bot mein in 2 weeks, customers ko phir we'll show — Sumit ko impress karna hai.
```

---

## Response Format Conventions (observed)

Onsite API responses commonly include:

- `id` — UUID, primary key
- `company_id` — tenant scope
- `creator` — user_id who created
- `creator_company_user_id` — user's company-user record
- `delete: 0 | 1` — soft delete flag
- `created` / `updated` — ISO 8601 timestamps
- `monkey_patch_*` — denormalized join data (e.g., `monkey_patch_primary_ba` is the full BA object embedded in a dependency response)

Empty/null values often come back as `""` (empty string) rather than `null`. Handle both.

---

## Custom Headers (Onsite frontend sends; we currently don't)

Per the CORS allow-list, these headers are accepted:

```
Authorization, Content-Type, Origin, X-Requested-With,
Content-Length, Accept-Encoding, X-CSRF-Token,
enterprise-id, version-code, project-id, project_id,
project-company-id, project_company_id,
X-Razorpay-Signature, api-secret
```

Our bot currently sends only `Authorization` and `Content-Type` — that works for `add/taskdependency` and `add/billingprogresshistory`. If a future endpoint returns unexpected empty results or 400 errors, try replicating the headers the Onsite UI sends for that endpoint.

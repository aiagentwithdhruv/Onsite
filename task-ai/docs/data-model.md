# Data Model — Onsite Domain

> What the bot reads and writes. Understand this before writing tool logic.

---

## Top-Level Entities

```
Company
  └─ Projects (1:N)
       └─ Workorders (1:N)
            └─ Billing Activities (tree, 1:N from workorder)
                 └─ Sub-Activities (1:N from BA)
                      └─ Progress Entries (1:N from sub-activity)

TaskDependency — links two leaf BAs in the same workorder
```

---

## Entity Details

### Company

The tenant. Each Onsite customer = one Company.

Key fields:
- `id` (UUID) — tenant identifier; also encoded in JWT
- `name` — display ("Dhruv Construction")
- `subscription_*` — plan info (Business / Business+ / Enterprise)

The Bearer JWT encodes `company_id` indirectly via user_id; Onsite's API enforces tenant scope.

### Project

A construction project. Belongs to a Company.

Key fields:
- `id`, `name`, `company_id`
- `contractor`, `creator`, `creator_company_user_id`
- `admins[]`, `supervisors[]`, `contact_book[]`
- `status` — "Ongoing" | "Completed" | "On Hold" | etc.
- `customer_name`, `customer_company_name`, `address`

**Example:** Soul Space Project (`9f26e601-da18-431d-8af2-b68b373e930e`)

### Workorder

A scope of work within a project. A project can have multiple workorders (e.g., "Civil Work", "Electrical", "Plumbing").

Key fields:
- `id`, `project_id`, `creator_company_id`, `vendor_project_id`

**This is the unit of dependency scope.** Two tasks can only have a dependency if they're in the same workorder.

### Billing Activity (BA = "Task")

The main task entity. Lives in a tree under a workorder.

Key fields:
- `id`, `workorder_id`, `company_id`
- `name` — display ("Electrical panel Setup")
- `parent_id` — UUID of parent BA, empty string for top-level
- `children_ids[]` — empty array if leaf
- `type` — "item" | "category" (parents are categories)
- `unit_id`, `unit` — measurement unit ("numbers", "ft", "sqm", "kg", etc.)
- `estimated_quantity`, `completed_quantity` — progress measurement
- `start_date`, `end_date` — schedule
- `progress_status` — "NotStarted" | "Ongoing" | "Completed"
- `assigned_to[]` — array of user IDs
- `index` — display order within parent

**Tree example (Soul Space → Wiring Installation section):**
```
Insulation (parent, type=category)
  ├─ Wiring Installation (parent, type=category)
  │    ├─ flooring work (parent, has children)
  │    ├─ New Electric Test (leaf, BA: 1b8f2e76-...)
  │    ├─ Electrical panel Setup (leaf, BA: 22200f57-...)
  │    └─ Fixture and outlet installation (leaf, BA: 54a68548-...)
```

**Only leaves can have dependencies.** Internal nodes (parents) have computed dates/progress aggregated from children.

### Sub-Activity

A child unit under a BA. Sometimes shown in the UI as "Location 1", "Floor A", etc. — but it's not a real location entity, it's a sub-activity name.

Progress is **always** logged against a sub-activity, never directly against a BA.

Key fields:
- `id`, `billing_activity_id`
- `name` — display ("Location 1")

A new BA has zero sub-activities until one is manually added in Onsite UI.

### Progress Entry (BillingProgressHistory)

A single logged increment of work done.

Key fields:
- `id`
- `billing_sub_activity_id` — the sub-activity this progress belongs to (REQUIRED)
- `billing_activity_id` — the parent BA (denormalized, set by server)
- `diff_quantity` — amount added in this entry (e.g., +3 numbers)
- `completed_quantity` — running total (set by server)
- `progress_date` — when the work happened (ISO 8601)
- `notes` — free text
- `measurement` — optional `{length, width, height}` for dimensional work
- `location_id` — **appears unused; empty string in real entries**
- `creator`, `creator_company_user_id`
- `approval_flag` — "auto_approved" | other states

### Task Dependency

A link between two leaf BAs.

Key fields:
- `id`
- `primary_ba_id` — the predecessor (must finish/start before secondary)
- `secondary_ba_id` — the dependent (waits on primary)
- `type` — `finish_to_start` | `finish_to_finish` | `start_to_start` | `start_to_finish`
- `lag` — integer days, 0–999
- `workorder_id` — denormalized for scope check
- `company_id`

Side effects of creating a dependency:
1. Server recomputes `start_date` / `end_date` of secondary BA based on type + lag + primary's dates
2. Parent BAs (categories) up the tree get re-aggregated dates
3. Returns the dependency + a list of all updated BAs (`UpdatedBillingActivity[]`)

---

## Critical Relationships

```
Dependency.primary_ba_id   ──► BillingActivity.id  (must be leaf)
Dependency.secondary_ba_id ──► BillingActivity.id  (must be leaf)
Dependency.workorder_id    ──► Workorder.id
                             ▲ primary and secondary must share this workorder

ProgressEntry.billing_sub_activity_id ──► SubActivity.id
ProgressEntry.billing_activity_id     ──► BillingActivity.id (set by server, not client)

SubActivity.billing_activity_id ──► BillingActivity.id
BillingActivity.parent_id       ──► BillingActivity.id (or empty for root)
BillingActivity.workorder_id    ──► Workorder.id
Workorder.project_id            ──► Project.id
Project.company_id              ──► Company.id (tenant scope)
```

---

## Dependency Type Semantics

| Type | Meaning | Common Use |
|------|---------|------------|
| `finish_to_start` (FS) | Secondary starts ONLY after primary finishes | Most common; sequential work (brickwork → plastering) |
| `finish_to_finish` (FF) | Both must finish at the same time | Parallel-but-coupled (e.g., wiring + plumbing must complete together) |
| `start_to_start` (SS) | Both start at the same time | Parallel work (e.g., electrical and plumbing both start when civil work begins) |
| `start_to_finish` (SF) | Secondary must finish before primary starts | Rare; staging/preparation tasks |

With `lag`, there's an N-day offset between the trigger event and the dependent event. E.g., FS with lag=5 means "secondary starts 5 days after primary finishes."

---

## Server-Enforced Invariants (from handler code)

1. `primary_ba_id` and `secondary_ba_id` must exist and be different
2. Both BAs must be leaf nodes (no `children_ids`)
3. Both BAs must share the same `workorder_id`
4. No cyclic dependencies (server runs cycle detection on the existing dependency graph)
5. `lag` ≤ 1000
6. User must have `ADD_TASK` policy on the workorder's project

If any fails, server returns 400 with specific error message — surface verbatim to the user.

---

## Display Conventions (in Onsite UI)

- Tasks numbered hierarchically: `0`, `0.1`, `0.1.1`, etc.
- Leaf tasks have an `↳` icon in the tree
- Internal nodes (categories) expand/collapse with `▶ / ▼`
- Dependency icon `🔗` shows next to tasks with dependencies
- Format `0.2 FS` in the dependency column means "this task is FS-linked from task 0.2"

---

## Gotchas / Surprises

1. **`location_id` is misleading.** It exists in the schema but is empty in real data. Sub-activities (named "Location N") play the location role.
2. **New tasks have zero sub-activities.** Customers must add at least one in Onsite UI before progress can be logged. Bot should detect this and surface a helpful error.
3. **Adding a child to a leaf BA makes it non-leaf.** Existing dependencies on that BA might become invalid (or the server might allow them — TBD).
4. **`completed_quantity` can exceed `estimated_quantity`.** Onsite doesn't enforce a cap; tasks can be 110% done.
5. **`monkey_patch_*` fields are server-side joins.** Useful in responses for the bot to give natural-language summaries without extra API calls.
6. **`unit_id` is from a fixed library** (categories: `numbers`, `ft`, `sqm`, `sqft`, `kg`, `tons`, etc.). Need a list endpoint to enumerate.

# Test Results Log

> Every end-to-end test run, with what was tried and what happened. Living log.

---

## 2026-05-17 — Initial MVP verification

**Tester:** Dhruv Tomar (manual through UI)
**Environment:** Production (`api.onsiteteams.in`)
**Token source:** localStorage of `web.onsiteteams.com` for Dhruv Construction account

### Test 1: Create dependency via curl (bypass UI)

**Setup:**
- Correct JWT from `JSON.parse(localStorage.getItem('token')).token`
- Primary BA: `22200f57-402b-4755-811c-faf67ed02135` (Electrical panel Setup)
- Secondary BA: `54a68548-e2b6-48f4-b883-94e75f156497` (Fixture and outlet installation)

**Command:**
```bash
curl -X POST 'https://api.onsiteteams.in/apis/v3/add/taskdependency' \
  -H 'authorization: Bearer eyJhbG...' \
  -H 'Content-Type: application/json' \
  -d '{"primary_ba_id":"22200f57-...","secondary_ba_id":"54a68548-...","type":"finish_to_start","lag":0}'
```

**Result:** ✅ 200 OK. Dependency ID `d374d749-0270-40fb-80c1-a672e9824341` created.

**Verified in Onsite UI:** Yes — `0.2 FS` arrow appears on Gantt for Fixture and outlet installation.

---

### Test 2: Create dependency via chatbot UI

**Setup:** Same JWT, this time pasted into UI at `localhost:3001/task-bot`
- Primary BA: `1b8f2e76-bdd6-44c9-82c9-a8082aa5b243` (New Electric Test)
- Secondary BA: `22200f57-402b-4755-811c-faf67ed02135` (Electrical panel Setup)

**Message to bot:**
```
Create a finish-to-start dependency.
Primary task BA ID: 1b8f2e76-bdd6-44c9-82c9-a8082aa5b243 (New Electric Test).
Dependent task BA ID: 22200f57-402b-4755-811c-faf67ed02135 (Electrical panel Setup).
Lag: 0 days.
```

**Result:** ✅ Bot extracted args correctly, called API, returned formatted markdown table with success confirmation.
Dependency ID: `9ba0c664-c188-41f4-832e-93384b67625f`

**Verified in Onsite UI:** Yes.

---

### Test 3: Record progress via chatbot UI

**Setup:** Continuation of Test 2's conversation
- Sub-activity ID: `be32dae2-e675-4204-b0e7-f13e3094d7a0` (Location 1 under Electrical panel Setup)
- Quantity: +3 numbers

**Message to bot:**
```
Update progress on Electrical panel Setup.
Sub-activity ID (Location 1): be32dae2-e675-4204-b0e7-f13e3094d7a0
Add 3 numbers completed today.
Notes: Test progress entry from AI bot.
```

**Result:** ✅ API call succeeded. Progress entry visible in Onsite UI under Electrical panel Setup → Progress tab with text "3 numbers", note "Test progress entry from AI bot", created by "CEO Dhruv".

---

## Issues Found During Testing

### Issue 1: Token misread from screenshot (resolved during session)

**Symptom:** First attempt at Test 2 via UI returned `401 token signature is invalid`.

**Root cause:** I (Claude) OCR'd the token from a screenshot and confused `I` (capital i) with `l` (lowercase L). Token-paste with one char off → signature mismatch.

**Fix:** Pulled token programmatically from `localStorage` via Console; pasted exactly. Worked.

**Lesson logged in:** [MEMORY.md § JWT signature errors are usually OCR misreads](../MEMORY.md)

---

### Issue 2: `location_id` required but unused (resolved)

**Symptom:** Bot kept asking customer for location_id; customer had no way to find one.

**Root cause:** Tool schema marked `location_id` as required. Reality: real progress entries have empty string for this field.

**Fix:** Made `location_id` optional in tool schema. Default to `""` server-side.

**Lesson logged in:** [MEMORY.md § location_id is empty in real entries](../MEMORY.md)

---

## Test Coverage Gaps (to address in Phase 2)

- [ ] Test against `testapi.onsiteteams.in` (need test credentials)
- [ ] Test error cases: cyclic dependency, cross-workorder, lag > 999
- [ ] Test voice input flow (mic → speech → tool call)
- [ ] Test multi-turn conversation (bot remembers context)
- [ ] Test mobile viewport (375px width)
- [ ] Test concurrent requests (simulate 10 users)
- [ ] Test invalid token handling (expired, wrong env)
- [ ] Test very long task names (truncation)
- [ ] Test special characters in task names (Hindi, special Unicode)

---

## Automated Test Plan (Phase 2)

### Unit (vitest)
- Tool args parser — JSON.parse error handling
- Onsite error message extractor — handles all known error shapes
- Mini-markdown renderer — bold parsing edge cases

### Integration (vitest + testapi.onsiteteams.in)
- create_task_dependency happy path
- create_task_dependency cyclic-rejection
- create_task_dependency cross-workorder rejection
- record_task_progress happy path
- record_task_progress with invalid sub-activity ID

### LLM eval suite (custom)
- 20 representative customer utterances → expected tool name + args
- Run on every system prompt change
- Pass threshold: ≥18/20 correct

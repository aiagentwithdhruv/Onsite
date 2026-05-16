# Bug Tracker — Onsite Task AI

> Open + resolved issues. Severity: 🔴 critical / 🟠 high / 🟡 medium / 🟢 low.

---

## Open

### 🟡 BT-001 — Progress entry shows wrong date in Onsite UI

**Discovered:** 2026-05-17
**Impact:** Cosmetic. Bot logs progress with today's ISO date, but Onsite UI displays "Jul 14, 25" (or similar past date) for the entry.
**Hypothesis:** Onsite frontend may be using `updated` field instead of `progress_date`, or there's a display bug. Need to verify.
**Workaround:** Real `progress_date` is stored correctly in DB (verified in API response). Just a display layer issue.
**Owner:** TBD (Akshansh team if it's an Onsite bug)

---

### 🟡 BT-002 — Conversation memory loses tool-call context across turns

**Discovered:** 2026-05-17 (architectural review)
**Impact:** If a user creates a dependency, then asks "delete that one I just made", the bot doesn't have the dependency ID in its conversation memory (we only send user/assistant text, not the assistant's prior tool_calls).
**Fix path:** Phase 2 — preserve full message history including assistant tool_calls and tool results. Pass it all in subsequent requests.
**Workaround:** User must paste IDs explicitly until fixed.

---

### 🟡 BT-003 — Long JWT can break UI layout

**Discovered:** Not yet observed; identified during code review
**Impact:** A JWT with line breaks or unusual chars pasted into the input might break the password input styling. Untested.
**Fix:** Add `overflow: hidden` and `text-overflow: ellipsis` to token input (cosmetic).

---

### 🟢 BT-004 — Voice input language hardcoded to en-IN

**Discovered:** 2026-05-17
**Impact:** Hindi-speaking customers can't use voice input in their language.
**Fix path:** Phase 2 — add language toggle, set `recognition.lang` accordingly.

---

### 🟢 BT-005 — Sign-out button only clears sessionStorage, not msgs

**Discovered:** 2026-05-17
**Impact:** Minor. After sign-out, if a user signs back in, the previous conversation flashes briefly before the welcome message replaces it.
**Fix:** Clear `msgs` array in the sign-out handler.

---

## Resolved

### ✅ BT-R001 — `location_id` required → broken UX (2026-05-17)

**Discovered + resolved:** 2026-05-17
**Impact:** Bot kept asking for location_id; customers couldn't provide one because it's not surfaced in the UI.
**Root cause:** Tool schema marked `location_id` as required despite the API accepting empty string.
**Fix:** Made `location_id` optional, defaults to `""`.

---

### ✅ BT-R002 — JWT signature errors from OCR misread (2026-05-17)

**Discovered + resolved:** 2026-05-17
**Impact:** First UI test failed with `401 token signature invalid`.
**Root cause:** Claude (me) read the token from a screenshot OCR and confused `I` with `l`.
**Fix:** Use `JSON.parse(localStorage.getItem('token')).token` via browser console for programmatic, error-free copy. Documented in CLAUDE.md and MEMORY.md.

---

## Bug Categories We Watch For

### Security
- Token appearing in logs
- Token in URL params
- CSP misconfiguration
- Cross-tenant data leak

### Reliability
- Onsite API timeout handling
- LLM API timeout handling
- Browser hot-reload issues
- Voice API browser compatibility

### UX
- Latency over budget
- Confusing error messages
- Mobile viewport breakage
- Accessibility (screen reader, keyboard nav)

### Data integrity
- Wrong tool called for intent
- Tool args misextracted
- Race condition on rapid messages

---

## How to Report a Bug

1. Reproduce — confirm it's not transient
2. Note: env (test/prod), browser, viewport, exact message sent, exact error received
3. Add entry above with severity, impact, hypothesis (if any), workaround (if any)
4. Link to STATE.md if it affects a shipped capability

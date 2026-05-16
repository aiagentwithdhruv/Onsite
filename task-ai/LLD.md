# Low-Level Design — Onsite Task AI

**Owner:** Dhruv Tomar | **Status:** Draft v1.0 | **Last updated:** 2026-05-17

This document is the implementation reference: data shapes, API contracts, component code patterns, file layout. Reading order: [PRD](PRD.md) → [HLD](HLD.md) → this.

---

## 1. File Layout (production code)

All production code lives inside `onsite-hub/` since this product is a feature of that Next.js app.

```
Onsite/onsite-hub/src/
├── app/
│   ├── task-bot/
│   │   └── page.tsx                    # Chat UI (client component, ~380 LOC)
│   └── api/
│       └── task-bot/
│           └── route.ts                # Backend handler (Node runtime, ~250 LOC)
└── components/
    └── AppShell.tsx                    # Modified: skips PIN auth for /task-bot
```

**Why not a separate package?** Single deploy, shared env vars, shared brand styles. Splitting adds friction without isolation benefit (we already have request-level isolation via stateless design).

---

## 2. Data Contracts

### 2.1 Frontend ↔ Backend

**Request: `POST /api/task-bot`**
```ts
type Request = {
  messages: Array<{ role: 'user' | 'assistant'; content: string }>
  token: string         // Onsite Bearer JWT (without "Bearer " prefix)
  baseUrl: string       // "https://api.onsiteteams.in" | "https://testapi.onsiteteams.in"
}
```

**Response: `200 OK`**
```ts
type Response = {
  reply: string                    // assistant's final message to display
  tool_called: boolean             // whether Claude invoked a tool this turn
  success?: boolean                // only present if tool_called; true if API call succeeded
  tool_args?: Record<string, unknown>  // only if tool_called; for client-side display/debug
}
```

**Response: `4xx/5xx`**
```ts
type ErrorResponse = {
  error: string  // human-readable; never contains token or sensitive data
}
```

### 2.2 Frontend ↔ Browser State

```ts
// sessionStorage keys
'taskbot_token': string     // raw JWT, cleared on browser close
'taskbot_env': 'test' | 'prod'

// In-memory React state (lost on refresh, by design)
type ChatState = {
  msgs: Array<{ id: string; role: 'user' | 'assistant'; content: string; success?: boolean }>
  input: string
  loading: boolean
  listening: boolean
}
```

### 2.3 Backend ↔ OpenRouter (Claude)

**Request:**
```ts
{
  model: 'anthropic/claude-sonnet-4-6',
  messages: [
    { role: 'system', content: SYSTEM_PROMPT },
    ...userMessages,
    // After tool execution, append:
    // { role: 'assistant', content: null, tool_calls: [...] }
    // { role: 'tool', tool_call_id: '...', content: '...' }
  ],
  tools: TOOL_REGISTRY,
  tool_choice: 'auto',
  max_tokens: 1024,
  temperature: 0.3,
}
```

**Response (text reply):**
```ts
{
  choices: [{
    message: { role: 'assistant', content: 'Hi! How can I help...' },
    finish_reason: 'stop'
  }]
}
```

**Response (tool call):**
```ts
{
  choices: [{
    message: {
      role: 'assistant',
      content: null,
      tool_calls: [{
        id: 'call_abc123',
        type: 'function',
        function: {
          name: 'create_task_dependency',
          arguments: '{"primary_ba_id":"...","secondary_ba_id":"...","type":"finish_to_start","lag":0}'
        }
      }]
    },
    finish_reason: 'tool_calls'
  }]
}
```

### 2.4 Backend ↔ Onsite API

See [API-SPECS.md](API-SPECS.md) for every endpoint's request/response shape.

---

## 3. Tool Registry

Each tool corresponds to one Onsite API action. Adding a tool = three places to update:

1. **Tool schema** in `route.ts` `TOOLS` array (defines what Claude can request)
2. **Tool dispatch** in `route.ts` `if (toolName === ...)` block (handles the request)
3. **Documentation** in [API-SPECS.md](API-SPECS.md) (so future agents know what we have)

### 3.1 Phase 1 Tools (built)

| Tool name | Endpoint | Status |
|-----------|----------|--------|
| `create_task_dependency` | `POST /apis/v3/add/taskdependency` | ✅ |
| `record_task_progress` | `POST /apis/v3/add/billingprogresshistory` | ✅ |

### 3.2 Phase 2 Tools (planned)

| Tool name | Endpoint | Purpose |
|-----------|----------|---------|
| `list_projects` | `POST /apis/v3/list/project` | "Which project?" disambiguation |
| `list_tasks` | `POST /apis/v3/list/billingactivity` | Find tasks by name |
| `list_subactivities` | `POST /apis/v3/list/billingsubactivity` | "Which location?" disambiguation |
| `update_task_dependency` | `POST /apis/v3/update/taskdependency` | Change type/lag |
| `delete_task_dependency` | `POST /apis/v3/delete/taskdependency` | Remove dependency |
| `add_task` | `POST /apis/v3/add/billingactivity` | Create new task/sub-task |
| `update_task` | `POST /apis/v3/update/billingactivity` | Edit task name/dates/qty |
| `mark_task_started` | `PATCH /apis/v3/edit/progress/billingactivity/mark-start` | Status transition |

### 3.3 Tool Schema Pattern

```ts
{
  type: 'function',
  function: {
    name: '<lowercase_snake_case>',
    description: '<one-sentence what+when>',
    parameters: {
      type: 'object',
      properties: {
        field_name: {
          type: 'string' | 'number' | 'integer' | 'boolean',
          description: '<what this field is>',
          enum?: [...],     // for closed sets like dependency type
          minimum?: number, // for numeric constraints
          maximum?: number,
        },
        // ...
      },
      required: ['field1', 'field2', ...]   // only fields the API enforces
    }
  }
}
```

**Lesson from MVP:** Don't mark fields as `required` in the tool schema unless the API truly enforces them. `location_id` was originally required → Claude kept asking customers for it → broken UX. Now optional, defaults to empty string server-side.

---

## 4. System Prompt Pattern

The system prompt is the **only** place where we shape Claude's behavior. Key sections (current MVP prompt is ~60 lines):

```
1. Identity ("You are an AI assistant built into Onsite construction management software")
2. Domain glossary (BA, sub-activity, dependency types)
3. Tool usage rules (which tool for which intent)
4. Conversation style (warm, practical, short replies)
5. Error handling (how to phrase failures)
```

**Phase 2 additions:**
```
6. Language rule ("respond in the user's language, mix Hindi-English freely")
7. Pre-flight check rule ("before calling a destructive tool, summarize and ask 'confirm?'")
8. Domain heuristics ("typical dependency types in construction: brickwork→plastering=FS, etc.")
```

The prompt is checked into git (in `route.ts`); never load it from external source — that's a supply-chain risk vector.

---

## 5. Component-Level Detail

### 5.1 `page.tsx` — Chat UI

**Two screens controlled by `authed` state:**
- **Setup screen** (when `!authed`): logo, token input, env toggle, Start button
- **Chat screen** (when `authed`): header, messages list, suggestion chips (first turn only), input bar with mic+send

**Message rendering:**
- User messages: pink bubble (`#c73e5a`), right-aligned, plain text
- Assistant messages: subtle gray bubble (`bg-white/8`), left-aligned, mini-markdown parser (bold only)
- Tool-success messages: green-tinted bubble (`bg-emerald-900/40 border-emerald-500/30`)
- Tool-failure messages: red-tinted bubble (`bg-red-900/30 border-red-500/30`)

**Voice input:**
- Web Speech API (`window.SpeechRecognition` or `webkitSpeechRecognition`)
- `lang = 'en-IN'` for MVP; Phase 2: language toggle
- Result populates the text input; user can edit before sending
- Pulse animation on mic button while listening

**Input behavior:**
- Auto-growing textarea (max-height 7rem)
- Enter to send; Shift+Enter for newline
- Disabled state while `loading`

**Session lifecycle:**
- Mount: hydrate `token` + `env` from sessionStorage; if both present, auto-authenticate
- Sign out: clear sessionStorage, reset state

### 5.2 `route.ts` — Backend Handler

**Function structure:**
```ts
export async function POST(req: NextRequest) {
  // 1. Parse + validate request
  // 2. Build OAI messages array (with system prompt)
  // 3. callClaude(messages) → first response
  // 4. If response is tool_call:
  //      a. JSON.parse(toolCall.function.arguments) [try/catch]
  //      b. Switch on toolName → call appropriate Onsite endpoint
  //      c. Build follow-up messages including tool result
  //      d. callClaude(followUpMessages) → final reply
  //      e. Return {reply, tool_called: true, success}
  // 5. If response is plain text, return {reply, tool_called: false}
}
```

**Error boundaries:**
- Outer try/catch returns 500 with sanitized message
- LLM failure → fallback static reply ("AI is busy, try again")
- Onsite API failure → tool_result includes error, second LLM call rephrases

### 5.3 `AppShell.tsx` — Auth Bypass

```ts
if (pathname.startsWith('/task-bot')) return <>{children}</>
```

One line. Above the `if (!user) return <LoginScreen />` check. Must remain there.

---

## 6. Data Model (Onsite Domain)

See [docs/data-model.md](docs/data-model.md) for full ER diagram and field-by-field.

**Quick reference:**

```
Company {id, name, ...}
  └─ Projects {id, name, company_id, ...}
       └─ Workorders {id, project_id, ...}
            └─ Billing Activities {id, workorder_id, parent_id, children_ids[], ...}
                 (tree structure; leaves only can have dependencies)
                 └─ Sub-Activities {id, ba_id, name (e.g. "Location 1"), ...}
                      └─ Progress Entries {id, sub_activity_id, diff_quantity, date, notes}
                                      
TaskDependency {id, workorder_id, primary_ba_id, secondary_ba_id, type, lag}
  (only valid if both BAs are leaf nodes in the same workorder)
```

**Critical invariants enforced by Onsite API:**
1. Dependencies require both BAs to be leaf nodes
2. Dependencies require both BAs in the same workorder
3. No cyclic dependencies
4. lag ∈ [0, 1000]
5. Progress requires a sub-activity (not directly on the BA)

Our bot should know these invariants and pre-empt them where possible (Phase 2).

---

## 7. Code Patterns

### 7.1 Calling Claude via OpenRouter

```ts
async function callClaude(messages: OAIMessage[]) {
  const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
      'HTTP-Referer': 'https://onsite-hub.vercel.app',
      'X-Title': 'Onsite Task Bot',
    },
    body: JSON.stringify({
      model: 'anthropic/claude-sonnet-4-6',
      messages,
      tools: TOOLS,
      tool_choice: 'auto',
      max_tokens: 1024,
      temperature: 0.3,
    }),
  })
  if (!res.ok) throw new Error(`Claude API error ${res.status}`)
  const data = await res.json()
  return data.choices[0]
}
```

### 7.2 Calling Onsite API

```ts
async function callOnsite(baseUrl: string, path: string, token: string, body: object) {
  const res = await fetch(`${baseUrl}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  })
  if (res.ok) return { ok: true, data: await res.json() }
  const err = await res.json().catch(() => ({ message: res.statusText }))
  return { ok: false, error: err.message || err.error || `HTTP ${res.status}` }
}
```

### 7.3 Tool dispatch (switch pattern)

```ts
let toolResult: string
switch (toolName) {
  case 'create_task_dependency': {
    const r = await callOnsite(baseUrl, '/apis/v3/add/taskdependency', token, {
      primary_ba_id: args.primary_ba_id,
      secondary_ba_id: args.secondary_ba_id,
      type: args.type,
      lag: args.lag,
    })
    success = r.ok
    toolResult = r.ok ? JSON.stringify({success: true, id: r.data.id}) : JSON.stringify({error: r.error})
    break
  }
  // ... other tools
  default:
    toolResult = JSON.stringify({ error: 'Unknown tool' })
}
```

### 7.4 Tool-result message format (sent back to Claude)

```ts
{
  role: 'tool',
  tool_call_id: <toolCall.id>,
  content: <JSON.stringify of result or error>
}
```

---

## 8. Environment Variables

| Var | Where | Why | Required |
|-----|-------|-----|----------|
| `OPENROUTER_API_KEY` | onsite-hub/.env.local | LLM access via OpenRouter | Yes |
| (None for Onsite API) | — | Token comes from customer per-request | — |

No new env vars introduced by task-ai beyond what onsite-hub already has.

---

## 9. Testing Strategy

### 9.1 MVP (current)

- Manual end-to-end testing via UI against `testapi.onsiteteams.in` (when test creds available) and `api.onsiteteams.in` (verified 2026-05-17)
- curl-based smoke test in `docs/test-results.md`

### 9.2 Phase 2 (planned)

- **Integration tests:** `vitest` + real `testapi.onsiteteams.in` endpoint. Fixtures: 1 test project, 5 leaf BAs.
- **LLM eval suite:** 20 representative customer utterances → assert correct tool dispatched + correct args extracted. Run on every prompt change.
- **Tenant isolation test:** mock two JWTs, send interleaved requests, assert no data crossover.

### 9.3 Phase 3 (production)

- Synthetic user (cron job): every 30 min, send a known-good message → assert success. Alert if fails.
- Real-user monitoring: tool-call success rate dashboard.

---

## 10. Performance Budget

| Step | Budget | Measured (2026-05-17) |
|------|--------|----------------------|
| First Claude call | < 1.5s | ~1.2s avg |
| Onsite API call | < 0.8s | ~0.4s |
| Second Claude call (after tool) | < 1.2s | ~0.9s |
| **Total tool-call round-trip** | **< 3.5s** | **~2.5s avg** |
| Text-only reply | < 1.5s | ~1.0s |

If we exceed budget after Phase 2 features land:
1. Stream first Claude response to client (perceived latency win, no real change)
2. Move simple intent detection to Haiku (faster + cheaper)
3. Parallel-call Onsite when multiple read tools fire (e.g., list_projects + list_tasks in one turn)

---

## 11. Naming Conventions

- Tool names: `verb_noun` snake_case (e.g., `create_task_dependency`, not `taskDependencyCreate`)
- Onsite IDs in code: `ba_id`, `sub_activity_id`, `workorder_id`, `project_id`, `company_id` (always with the `_id` suffix)
- Internal types: PascalCase (e.g., `OAIMessage`, `ToolCall`)
- Files: kebab-case (`task-bot`, `data-model.md`)

---

## 12. Open Implementation Questions

1. **Should we add a request ID to logs?** Helpful for debugging customer reports, but adds plumbing. Decide when we have actual customer reports.
2. **Streaming response or buffered?** Streaming is nicer UX but our tool-call pattern requires two sequential LLM calls. Stream the second one only? Phase 2 decision.
3. **Should tool args be re-validated server-side via Zod?** Claude already gets the JSON schema; double validation = belt-and-suspenders. Add it if we see a single args-parsing bug in production.

---

## 13. References

- [HLD.md](HLD.md) — architecture, multi-tenancy
- [API-SPECS.md](API-SPECS.md) — endpoint catalog
- [docs/data-model.md](docs/data-model.md) — Onsite domain model
- [docs/decisions.md](docs/decisions.md) — ADRs

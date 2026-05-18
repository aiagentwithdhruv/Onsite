#!/usr/bin/env node
// 3-way end-to-end: Haiku 4.5 vs Gemini 2.0 Flash vs Gemini 3 Flash Preview
// Same 14 tests covering reads, actions, memory recall, ambiguity, Hindi, edge.

import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))
try {
  const env = readFileSync(resolve(__dirname, '../../onsite-hub/.env.local'), 'utf-8')
  for (const line of env.split('\n')) {
    const m = line.match(/^([A-Z_]+)=(.*)$/)
    if (m) process.env[m[1]] = m[2]
  }
} catch (e) { console.error('env load:', e.message) }

const OR_KEY = process.env.OPENROUTER_API_KEY
if (!OR_KEY) { console.error('OPENROUTER_API_KEY not set'); process.exit(1) }

const MODELS = [
  { key: 'haiku', id: 'anthropic/claude-haiku-4-5',      label: 'Haiku 4.5',           inCost: 1.00, outCost: 5.00 },
  { key: 'g2',    id: 'google/gemini-2.0-flash-001',     label: 'Gemini 2.0 Flash',    inCost: 0.10, outCost: 0.40 },
  { key: 'g3',    id: 'google/gemini-3-flash-preview',   label: 'Gemini 3 Flash Prev', inCost: 0.30, outCost: 2.50 },
]

const SYSTEM = `You are Onsite AI, a chat-first assistant for construction project management.

CRITICAL RULES:
- Users do NOT know UUIDs. NEVER ask for them. Resolve names via list_* tools.
- Workflow: list_companies → list_projects(search) → list_tasks(project_id, search) → list_subactivities → record_task_progress
- When list_projects returns ambiguous:true → ASK the user which one, don't silently pick.
- "this/that/last/undo" → use UUID from the most recent tool_call_result. NEVER re-ask for IDs.
- Multi-step user requests = call ALL needed tools in sequence, don't stop early.
- For "delete" → use list_progress_history → delete_task_progress with real UUID. NEVER fake a delete with a negative entry.
- Be concise (2-4 sentences).
- Respond in the user's language register (English / Hindi / Hindi-English mix).`

const TOOLS = [
  { type: 'function', function: { name: 'list_companies', description: 'List companies.', parameters: { type: 'object', properties: {}}}},
  { type: 'function', function: { name: 'list_projects', description: 'List projects. Pass search_query for name match. Returns ambiguous:true if name collides across companies.', parameters: { type: 'object', properties: { search_query: { type: 'string' }, company_id: { type: 'string' }}}}},
  { type: 'function', function: { name: 'list_tasks', description: 'List tasks in a project.', parameters: { type: 'object', properties: { project_id: { type: 'string' }, search_query: { type: 'string' }, only_leaves: { type: 'boolean' }}}}},
  { type: 'function', function: { name: 'list_subactivities', description: 'List sub-activities under a leaf task.', parameters: { type: 'object', properties: { billing_activity_id: { type: 'string' }}, required: ['billing_activity_id']}}},
  { type: 'function', function: { name: 'list_dependencies', description: 'List task dependencies.', parameters: { type: 'object', properties: { ba_id: { type: 'string' }}}}},
  { type: 'function', function: { name: 'list_progress_history', description: 'List individual progress entries with UUIDs.', parameters: { type: 'object', properties: { billing_sub_activity_id: { type: 'string' }}, required: ['billing_sub_activity_id']}}},
  { type: 'function', function: { name: 'get_project_stats', description: 'Project breakdown stats.', parameters: { type: 'object', properties: { project_id: { type: 'string' }, project_name: { type: 'string' }}}}},
  { type: 'function', function: { name: 'create_task_dependency', description: 'Create dep between two leaf tasks.', parameters: { type: 'object', properties: { primary_ba_id: { type: 'string' }, secondary_ba_id: { type: 'string' }, dep_type: { type: 'string', enum: ['finish_to_start','finish_to_finish','start_to_start','start_to_finish']}, lag: { type: 'integer' }}, required: ['primary_ba_id','secondary_ba_id','dep_type','lag']}}},
  { type: 'function', function: { name: 'update_task_dependency', description: 'Update dep.', parameters: { type: 'object', properties: { id: { type: 'string' }, lag: { type: 'integer' }}, required: ['id']}}},
  { type: 'function', function: { name: 'delete_task_dependency', description: 'Delete dep.', parameters: { type: 'object', properties: { id: { type: 'string' }}, required: ['id']}}},
  { type: 'function', function: { name: 'record_task_progress', description: 'Log progress. Returns progress_history_id.', parameters: { type: 'object', properties: { billing_sub_activity_id: { type: 'string' }, diff_quantity: { type: 'number' }, progress_date: { type: 'string' }, notes: { type: 'string' }}, required: ['billing_sub_activity_id','diff_quantity','progress_date']}}},
  { type: 'function', function: { name: 'delete_task_progress', description: 'Delete progress entry by UUID.', parameters: { type: 'object', properties: { id: { type: 'string' }}, required: ['id']}}},
  { type: 'function', function: { name: 'search_tasks', description: 'Fuzzy search tasks.', parameters: { type: 'object', properties: { query: { type: 'string' }}, required: ['query']}}},
  { type: 'function', function: { name: 'add_task', description: 'Create a new task.', parameters: { type: 'object', properties: { name: { type: 'string' }, project_id: { type: 'string' }}, required: ['name']}}},
]

function ok(r, allowed) { return r.firstTool && allowed.includes(r.firstTool) }

const TESTS = [
  { name: 'R1 — List my projects',                messages: [{ role: 'system', content: SYSTEM }, { role: 'user', content: 'show me all my projects' }], check: (r) => ok(r, ['list_projects','list_companies'])},
  { name: 'R2 — Project stats',                   messages: [{ role: 'system', content: SYSTEM }, { role: 'user', content: 'what is the breakdown of Soul Space?' }], check: (r) => ok(r, ['list_projects','list_companies','get_project_stats','search_tasks'])},
  { name: 'R3 — Find specific task',              messages: [{ role: 'system', content: SYSTEM }, { role: 'user', content: 'find tasks with "brickwork" in name' }], check: (r) => ok(r, ['search_tasks','list_companies'])},
  { name: 'R4 — List deps for a project',         messages: [{ role: 'system', content: SYSTEM }, { role: 'user', content: 'show me dependencies in Soul Space' }], check: (r) => ok(r, ['list_projects','list_companies','list_dependencies','search_tasks'])},
  { name: 'A1 — Create dep with names',           messages: [{ role: 'system', content: SYSTEM }, { role: 'user', content: 'In Soul Space, make Plastering depend on Brickwork — FS 1d lag' }], check: (r) => ok(r, ['list_projects','list_companies','list_tasks','search_tasks'])},
  { name: 'A2 — Log progress',                    messages: [{ role: 'system', content: SYSTEM }, { role: 'user', content: 'log +12 sqm on Gypsum board in Interior Project' }], check: (r) => ok(r, ['list_projects','list_companies','list_tasks','search_tasks'])},
  { name: 'A3 — Update dep lag',                  messages: [{ role: 'system', content: SYSTEM }, { role: 'user', content: 'change the Plastering→Painting dep to 3 day lag in Soul Space' }], check: (r) => ok(r, ['list_projects','list_companies','list_tasks','list_dependencies','search_tasks'])},
  { name: 'M1 — Delete just-logged progress',     messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'log +5 sqft on Block Wall' },
      { role: 'assistant', content: 'Done!', tool_calls: [{ id: 'c1', type: 'function', function: { name: 'record_task_progress', arguments: JSON.stringify({ billing_sub_activity_id: 'sub-1', diff_quantity: 5, progress_date: '2026-05-19' })}}]},
      { role: 'tool', tool_call_id: 'c1', content: JSON.stringify({ success: true, progress_history_id: 'PROG-UUID-abc-123', task_name: 'Block Wall', new_total: 25 })},
      { role: 'assistant', content: 'Logged +5 sqft on Block Wall. Total now 25 sqft.' },
      { role: 'user', content: 'delete this 5 sqft' },
    ], check: (r) => ok(r, ['delete_task_progress']) && (r.firstArgs || '').includes('PROG-UUID-abc-123')},
  { name: 'M2 — Undo just-created dep',           messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'create Brickwork→Plastering FS dep, 0 lag' },
      { role: 'assistant', content: 'Done.', tool_calls: [{ id: 'c1', type: 'function', function: { name: 'create_task_dependency', arguments: JSON.stringify({ primary_ba_id: 'task-1', secondary_ba_id: 'task-2', dep_type: 'finish_to_start', lag: 0 })}}]},
      { role: 'tool', tool_call_id: 'c1', content: JSON.stringify({ success: true, dep_id: 'DEP-UUID-xyz-456' })},
      { role: 'assistant', content: 'Created. ID: DEP-UUID-xyz-456' },
      { role: 'user', content: 'undo that' },
    ], check: (r) => ok(r, ['delete_task_dependency']) && (r.firstArgs || '').includes('DEP-UUID-xyz-456')},
  { name: 'D1 — Same name 2 companies',           messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'EPC PEB check' },
      { role: 'assistant', content: null, tool_calls: [{ id: 'c1', type: 'function', function: { name: 'list_projects', arguments: JSON.stringify({ search_query: 'EPC PEB' })}}]},
      { role: 'tool', tool_call_id: 'c1', content: JSON.stringify({
        ambiguous: true,
        exact_name_duplicates: [{ name: 'epc peb', count: 2, options: [
          { project_id: 'p-DHRUV', company_id: 'c-1', company_name: 'Dhruv Construction', status: 'Ongoing' },
          { project_id: 'p-ACME', company_id: 'c-2', company_name: 'Acme Builders', status: 'Completed' },
        ]}],
      })},
    ], check: (r) => !r.firstTool && /Dhruv|Acme/i.test(r.content || '')},
  { name: 'D2 — Resolve after ambiguity',         messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'EPC PEB stats' },
      { role: 'assistant', content: null, tool_calls: [{ id: 'c1', type: 'function', function: { name: 'list_projects', arguments: JSON.stringify({ search_query: 'EPC PEB' })}}]},
      { role: 'tool', tool_call_id: 'c1', content: JSON.stringify({
        ambiguous: true,
        exact_name_duplicates: [{ name: 'epc peb', count: 2, options: [
          { project_id: 'p-DHRUV', company_id: 'c-1', company_name: 'Dhruv Construction', status: 'Ongoing' },
          { project_id: 'p-ACME', company_id: 'c-2', company_name: 'Acme Builders', status: 'Completed' },
        ]}],
      })},
      { role: 'assistant', content: 'Two EPC PEBs exist. Dhruv Construction (Ongoing) or Acme Builders (Completed)?' },
      { role: 'user', content: 'dhruv' },
    ], check: (r) => ok(r, ['get_project_stats']) && /p-DHRUV/.test(r.firstArgs || '')},
  { name: 'L1 — Hindi action',                    messages: [{ role: 'system', content: SYSTEM }, { role: 'user', content: 'Soul Space mein wiring ke baad fixture installation, FS 0 lag dep banao' }], check: (r) => ok(r, ['list_projects','list_companies','search_tasks','list_tasks'])},
  { name: 'L2 — Hindi read',                      messages: [{ role: 'system', content: SYSTEM }, { role: 'user', content: 'Soul Space ka kya status hai? Progress kitna hua?' }], check: (r) => ok(r, ['list_projects','list_companies','get_project_stats','search_tasks'])},
  { name: 'E1 — Recovery from prior empty result', messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'log progress on Wiring' },
      { role: 'assistant', content: null, tool_calls: [{ id: 'c1', type: 'function', function: { name: 'list_projects', arguments: JSON.stringify({ search_query: 'Wiring' })}}]},
      { role: 'tool', tool_call_id: 'c1', content: JSON.stringify({ total: 0, projects: [] })},
      { role: 'assistant', content: 'No project called "Wiring" found. Is it a task name?' },
      { role: 'user', content: 'yes wiring is a task inside Soul Space, log +3' },
    ], check: (r) => ok(r, ['list_projects','list_tasks','search_tasks','list_companies']) && /soul/i.test(r.firstArgs || '')},
]

async function callModel(modelId, messages) {
  const start = Date.now()
  try {
    const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${OR_KEY}`, 'Content-Type': 'application/json', 'HTTP-Referer': 'https://onsite-hub.vercel.app', 'X-Title': '3way-test' },
      body: JSON.stringify({ model: modelId, messages, tools: TOOLS, tool_choice: 'auto', temperature: 0.1, max_tokens: 1500 }),
    })
    const elapsed = Date.now() - start
    const data = await res.json()
    if (!res.ok) return { ok: false, elapsed, error: data?.error?.message || `HTTP ${res.status}` }
    const choice = data.choices?.[0]
    const message = choice?.message || {}
    const tc = message.tool_calls?.[0]
    return {
      ok: true, elapsed,
      firstTool: tc?.function?.name,
      firstArgs: tc?.function?.arguments,
      content: message.content || '',
      inputTokens: data.usage?.prompt_tokens || 0,
      outputTokens: data.usage?.completion_tokens || 0,
    }
  } catch (err) { return { ok: false, elapsed: Date.now() - start, error: err.message } }
}

async function main() {
  console.log('\n═══════════════════════════════════════════════════════════════')
  console.log('  3-WAY: Haiku 4.5 vs Gemini 2.0 Flash vs Gemini 3 Flash Preview')
  console.log(`  ${TESTS.length} tests covering full surface area`)
  console.log('═══════════════════════════════════════════════════════════════\n')

  const stats = {}
  for (const m of MODELS) stats[m.key] = { pass: 0, in: 0, out: 0, latency: 0, failures: [] }

  for (const test of TESTS) {
    const results = {}
    for (const m of MODELS) {
      const r = await callModel(m.id, test.messages)
      const pass = r.ok && test.check(r)
      if (pass) stats[m.key].pass++
      else stats[m.key].failures.push({ name: test.name, tool: r.firstTool || '(text)', content: (r.content || '').slice(0, 80) })
      if (r.ok) {
        stats[m.key].in += r.inputTokens
        stats[m.key].out += r.outputTokens
        stats[m.key].latency += r.elapsed
      }
      results[m.key] = { pass, r }
    }
    const line = MODELS.map(m => {
      const { pass, r } = results[m.key]
      return `${m.label.slice(0,18).padEnd(18)} ${pass?'✅':'❌'} ${(r.elapsed/1000).toFixed(2)}s ${(r.firstTool || '(text)').slice(0,22).padEnd(22)}`
    }).join('  ')
    console.log(`${test.name.padEnd(36)} ${line}`)
  }

  console.log('\n═══════════════════════════════════════════════════════════════')
  console.log('  SCOREBOARD')
  console.log('═══════════════════════════════════════════════════════════════\n')
  console.log('Model                    Pass   Cost(14)   Per-prompt   Latency   vs Haiku cost')
  console.log('─'.repeat(85))

  const haikuCost = (stats.haiku.in * MODELS[0].inCost + stats.haiku.out * MODELS[0].outCost) / 1_000_000

  for (const m of MODELS) {
    const s = stats[m.key]
    const cost = (s.in * m.inCost + s.out * m.outCost) / 1_000_000
    const ratio = m.key === 'haiku' ? '1.0× (baseline)' : `${(haikuCost/cost).toFixed(1)}× cheaper`
    console.log(
      `${m.label.padEnd(24)} ${String(s.pass).padStart(2)}/${TESTS.length}    $${cost.toFixed(5)}    $${(cost/TESTS.length).toFixed(5)}    ${(s.latency/TESTS.length/1000).toFixed(2)}s     ${ratio}`
    )
  }

  // Per-model failures
  console.log('\n=== FAILURES ===')
  for (const m of MODELS) {
    if (stats[m.key].failures.length === 0) {
      console.log(`${m.label}: none ✅`)
    } else {
      console.log(`\n${m.label}:`)
      for (const f of stats[m.key].failures) console.log(`  ${f.name} — tool=${f.tool}`)
    }
  }
}

main().catch(e => { console.error(e); process.exit(1) })

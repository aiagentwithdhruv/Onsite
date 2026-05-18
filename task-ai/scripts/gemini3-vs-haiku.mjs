#!/usr/bin/env node
// Head-to-head: Gemini 3 Flash Preview vs Haiku 4.5
// Full surface area — 14 tests covering reads, actions, edge cases.

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

// Cost per 1M tokens
const MODELS = {
  haiku: { id: 'anthropic/claude-haiku-4-5', label: 'Haiku 4.5', inCost: 1.00, outCost: 5.00 },
  g3:    { id: 'google/gemini-3-flash-preview', label: 'Gemini 3 Flash Preview', inCost: 0.30, outCost: 2.50 },
}

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

// 14 tests covering the full surface
const TESTS = [
  // READS
  { name: 'R1 — List my projects', messages: [
    { role: 'system', content: SYSTEM },
    { role: 'user', content: 'show me all my projects' },
  ], check: (r) => ok(r, ['list_projects','list_companies'])},

  { name: 'R2 — Project stats', messages: [
    { role: 'system', content: SYSTEM },
    { role: 'user', content: 'what is the breakdown of Soul Space?' },
  ], check: (r) => ok(r, ['list_projects','list_companies','get_project_stats','search_tasks'])},

  { name: 'R3 — Find specific task', messages: [
    { role: 'system', content: SYSTEM },
    { role: 'user', content: 'find tasks with "brickwork" in name' },
  ], check: (r) => ok(r, ['search_tasks','list_companies'])},

  { name: 'R4 — List deps for a project', messages: [
    { role: 'system', content: SYSTEM },
    { role: 'user', content: 'show me dependencies in Soul Space' },
  ], check: (r) => ok(r, ['list_projects','list_companies','list_dependencies','search_tasks'])},

  // ACTIONS
  { name: 'A1 — Create dep with names', messages: [
    { role: 'system', content: SYSTEM },
    { role: 'user', content: 'In Soul Space, make Plastering depend on Brickwork — FS 1d lag' },
  ], check: (r) => ok(r, ['list_projects','list_companies','list_tasks','search_tasks'])},

  { name: 'A2 — Log progress', messages: [
    { role: 'system', content: SYSTEM },
    { role: 'user', content: 'log +12 sqm on Gypsum board in Interior Project' },
  ], check: (r) => ok(r, ['list_projects','list_companies','list_tasks','search_tasks'])},

  { name: 'A3 — Update dep lag', messages: [
    { role: 'system', content: SYSTEM },
    { role: 'user', content: 'change the Plastering→Painting dep to 3 day lag in Soul Space' },
  ], check: (r) => ok(r, ['list_projects','list_companies','list_tasks','list_dependencies','search_tasks'])},

  // MEMORY (RULE 0.5)
  { name: 'M1 — Delete just-logged progress', messages: [
    { role: 'system', content: SYSTEM },
    { role: 'user', content: 'log +5 sqft on Block Wall' },
    { role: 'assistant', content: 'Done!', tool_calls: [{ id: 'c1', type: 'function', function: { name: 'record_task_progress', arguments: JSON.stringify({ billing_sub_activity_id: 'sub-1', diff_quantity: 5, progress_date: '2026-05-19' })}}]},
    { role: 'tool', tool_call_id: 'c1', content: JSON.stringify({ success: true, progress_history_id: 'PROG-UUID-abc-123', task_name: 'Block Wall', new_total: 25 })},
    { role: 'assistant', content: 'Logged +5 sqft on Block Wall. Total now 25 sqft.' },
    { role: 'user', content: 'delete this 5 sqft' },
  ], check: (r) => ok(r, ['delete_task_progress']) && (r.firstArgs || '').includes('PROG-UUID-abc-123')},

  { name: 'M2 — Undo just-created dep', messages: [
    { role: 'system', content: SYSTEM },
    { role: 'user', content: 'create Brickwork→Plastering FS dep, 0 lag' },
    { role: 'assistant', content: 'Done.', tool_calls: [{ id: 'c1', type: 'function', function: { name: 'create_task_dependency', arguments: JSON.stringify({ primary_ba_id: 'task-1', secondary_ba_id: 'task-2', dep_type: 'finish_to_start', lag: 0 })}}]},
    { role: 'tool', tool_call_id: 'c1', content: JSON.stringify({ success: true, dep_id: 'DEP-UUID-xyz-456' })},
    { role: 'assistant', content: 'Created. ID: DEP-UUID-xyz-456' },
    { role: 'user', content: 'undo that' },
  ], check: (r) => ok(r, ['delete_task_dependency']) && (r.firstArgs || '').includes('DEP-UUID-xyz-456')},

  // AMBIGUITY (RULE 0.6)
  { name: 'D1 — Same name 2 companies', messages: [
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

  { name: 'D2 — Resolve after ambiguity', messages: [
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

  // HINDI / MULTILINGUAL
  { name: 'L1 — Hindi action', messages: [
    { role: 'system', content: SYSTEM },
    { role: 'user', content: 'Soul Space mein wiring ke baad fixture installation, FS 0 lag dep banao' },
  ], check: (r) => ok(r, ['list_projects','list_companies','search_tasks','list_tasks'])},

  { name: 'L2 — Hindi read', messages: [
    { role: 'system', content: SYSTEM },
    { role: 'user', content: 'Soul Space ka kya status hai? Progress kitna hua?' },
  ], check: (r) => ok(r, ['list_projects','list_companies','get_project_stats','search_tasks'])},

  // EDGE
  { name: 'E1 — Recovery from prior empty result', messages: [
    { role: 'system', content: SYSTEM },
    { role: 'user', content: 'log progress on Wiring' },
    { role: 'assistant', content: null, tool_calls: [{ id: 'c1', type: 'function', function: { name: 'list_projects', arguments: JSON.stringify({ search_query: 'Wiring' })}}]},
    { role: 'tool', tool_call_id: 'c1', content: JSON.stringify({ total: 0, projects: [] })},
    { role: 'assistant', content: 'No project called "Wiring" found. Is it a task name?' },
    { role: 'user', content: 'yes wiring is a task inside Soul Space, log +3' },
  ], check: (r) => ok(r, ['list_projects','list_tasks','search_tasks','list_companies']) && /soul/i.test(r.firstArgs || '')},
]

function ok(r, allowed) {
  return r.firstTool && allowed.includes(r.firstTool)
}

async function callModel(modelId, messages) {
  const start = Date.now()
  try {
    const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${OR_KEY}`, 'Content-Type': 'application/json', 'HTTP-Referer': 'https://onsite-hub.vercel.app', 'X-Title': 'G3-vs-Haiku' },
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
  console.log('  GEMINI 3 FLASH PREVIEW vs HAIKU 4.5 — End-to-end (14 tests)')
  console.log('═══════════════════════════════════════════════════════════════\n')

  let h = { pass: 0, fail: 0, in: 0, out: 0, latency: 0 }
  let g = { pass: 0, fail: 0, in: 0, out: 0, latency: 0 }
  const onlyH = [], onlyG = [], bothFail = []

  for (const test of TESTS) {
    const hR = await callModel(MODELS.haiku.id, test.messages)
    const gR = await callModel(MODELS.g3.id, test.messages)

    const hPass = hR.ok && test.check(hR)
    const gPass = gR.ok && test.check(gR)

    if (hPass) h.pass++; else h.fail++
    if (gPass) g.pass++; else g.fail++
    if (hR.ok) { h.in += hR.inputTokens; h.out += hR.outputTokens; h.latency += hR.elapsed }
    if (gR.ok) { g.in += gR.inputTokens; g.out += gR.outputTokens; g.latency += gR.elapsed }

    if (hPass && !gPass) onlyH.push({ name: test.name, gTool: gR.firstTool, gContent: (gR.content || '').slice(0, 100) })
    if (!hPass && gPass) onlyG.push({ name: test.name, hTool: hR.firstTool, hContent: (hR.content || '').slice(0, 100) })
    if (!hPass && !gPass) bothFail.push({ name: test.name, hTool: hR.firstTool, gTool: gR.firstTool })

    const hm = hPass ? '✅' : '❌'
    const gm = gPass ? '✅' : '❌'
    console.log(`${test.name.padEnd(40)}  H ${hm} ${(hR.elapsed/1000).toFixed(2)}s  ${(hR.firstTool || '(text)').padEnd(28)}  G ${gm} ${(gR.elapsed/1000).toFixed(2)}s  ${gR.firstTool || '(text)'}`)
  }

  const hCost = (h.in * MODELS.haiku.inCost + h.out * MODELS.haiku.outCost) / 1_000_000
  const gCost = (g.in * MODELS.g3.inCost + g.out * MODELS.g3.outCost) / 1_000_000

  console.log('\n═══════════════════════════════════════════════════════════════')
  console.log('  SCOREBOARD')
  console.log('═══════════════════════════════════════════════════════════════\n')
  console.log(`                       Haiku 4.5         Gemini 3 Flash Preview`)
  console.log(`Passed:                ${h.pass}/${TESTS.length}              ${g.pass}/${TESTS.length}`)
  console.log(`Total cost (14 tests): $${hCost.toFixed(5)}        $${gCost.toFixed(5)}`)
  console.log(`Per-prompt cost:       $${(hCost/TESTS.length).toFixed(5)}        $${(gCost/TESTS.length).toFixed(5)}`)
  console.log(`Avg latency:           ${(h.latency/TESTS.length/1000).toFixed(2)}s             ${(g.latency/TESTS.length/1000).toFixed(2)}s`)
  console.log(`Cost ratio: Haiku is ${(hCost/gCost).toFixed(1)}× more expensive than Gemini 3`)

  if (onlyH.length > 0) {
    console.log('\n=== Haiku-only wins (Gemini FAILED these) ===')
    for (const t of onlyH) console.log(`  ${t.name} — Gemini called: ${t.gTool || '(no tool)'}`)
  }
  if (onlyG.length > 0) {
    console.log('\n=== Gemini-only wins (Haiku FAILED these) ===')
    for (const t of onlyG) console.log(`  ${t.name} — Haiku called: ${t.hTool || '(no tool)'}`)
  }
  if (bothFail.length > 0) {
    console.log('\n=== Both failed ===')
    for (const t of bothFail) console.log(`  ${t.name} — Haiku: ${t.hTool||'(no tool)'}, Gemini: ${t.gTool||'(no tool)'}`)
  }

  if (onlyH.length === 0 && onlyG.length === 0 && bothFail.length === 0) {
    console.log('\n→ Both models perfect across all tests.')
  } else if (onlyH.length === 0 && bothFail.length === 0) {
    console.log('\n→ Gemini 3 matches or beats Haiku everywhere. Safe to default.')
  }
}

main().catch(e => { console.error(e); process.exit(1) })

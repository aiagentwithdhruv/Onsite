#!/usr/bin/env node
// Find prompts where Haiku fails but Sonnet succeeds. These are the
// REAL escalation cases — the only times we should pay Sonnet's premium.

import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))
try {
  const envPath = resolve(__dirname, '../../onsite-hub/.env.local')
  const env = readFileSync(envPath, 'utf-8')
  for (const line of env.split('\n')) {
    const m = line.match(/^([A-Z_]+)=(.*)$/)
    if (m) process.env[m[1]] = m[2]
  }
} catch (e) { console.error('env load:', e.message) }

const OR_KEY = process.env.OPENROUTER_API_KEY
if (!OR_KEY) { console.error('OPENROUTER_API_KEY not set'); process.exit(1) }

const SYSTEM = `You are Onsite AI for construction project management.
RULES:
- Users do NOT know UUIDs. Never ask for them. Resolve names via list_* tools.
- Workflow: list_companies → list_projects(search) → list_tasks(project_id, search)
- ambiguous:true in tool result → ASK which one, don't pick
- "this/that/last/undo" → use UUID from prior tool result
- Multi-step user requests = call ALL needed tools, don't stop early
- Never fake delete with negative entry — use list_progress_history → delete_task_progress
- Be concise.`

const TOOLS = [
  { type: 'function', function: { name: 'list_companies', description: 'List companies.', parameters: { type: 'object', properties: {}}}},
  { type: 'function', function: { name: 'list_projects', description: 'List projects. Pass search_query for name match.', parameters: { type: 'object', properties: { search_query: { type: 'string' }, company_id: { type: 'string' }}}}},
  { type: 'function', function: { name: 'list_tasks', description: 'List tasks in a project.', parameters: { type: 'object', properties: { project_id: { type: 'string' }, search_query: { type: 'string' }, only_leaves: { type: 'boolean' }}}}},
  { type: 'function', function: { name: 'list_subactivities', description: 'List sub-activities under a task.', parameters: { type: 'object', properties: { billing_activity_id: { type: 'string' }}, required: ['billing_activity_id']}}},
  { type: 'function', function: { name: 'list_dependencies', description: 'List deps.', parameters: { type: 'object', properties: { ba_id: { type: 'string' }}}}},
  { type: 'function', function: { name: 'list_progress_history', description: 'List progress entries for a sub-activity.', parameters: { type: 'object', properties: { billing_sub_activity_id: { type: 'string' }}, required: ['billing_sub_activity_id']}}},
  { type: 'function', function: { name: 'get_project_stats', description: 'Project breakdown stats.', parameters: { type: 'object', properties: { project_id: { type: 'string' }}}}},
  { type: 'function', function: { name: 'create_task_dependency', description: 'Create dep between two leaf tasks.', parameters: { type: 'object', properties: { primary_ba_id: { type: 'string' }, secondary_ba_id: { type: 'string' }, dep_type: { type: 'string' }, lag: { type: 'integer' }}, required: ['primary_ba_id','secondary_ba_id','dep_type','lag']}}},
  { type: 'function', function: { name: 'update_task_dependency', description: 'Update dep.', parameters: { type: 'object', properties: { id: { type: 'string' }, lag: { type: 'integer' }}, required: ['id']}}},
  { type: 'function', function: { name: 'delete_task_dependency', description: 'Delete dep.', parameters: { type: 'object', properties: { id: { type: 'string' }}, required: ['id']}}},
  { type: 'function', function: { name: 'record_task_progress', description: 'Log progress. Returns progress_history_id.', parameters: { type: 'object', properties: { billing_sub_activity_id: { type: 'string' }, diff_quantity: { type: 'number' }, progress_date: { type: 'string' }}, required: ['billing_sub_activity_id','diff_quantity','progress_date']}}},
  { type: 'function', function: { name: 'delete_task_progress', description: 'Delete progress entry by UUID.', parameters: { type: 'object', properties: { id: { type: 'string' }}, required: ['id']}}},
  { type: 'function', function: { name: 'search_tasks', description: 'Fuzzy search tasks.', parameters: { type: 'object', properties: { query: { type: 'string' }}, required: ['query']}}},
]

// Harder cases designed to surface Sonnet's edge over Haiku
const TESTS = [
  {
    name: 'H1 — Multi-action chain',
    messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'In Soul Space: 1) create Plastering→Painting FS dep with 2d lag, 2) then log +15 sqm on Plastering, 3) then show me the breakdown' },
    ],
    check: (r) => {
      // Best case: makes a plan + starts with the first tool
      const okStart = r.firstTool && ['list_projects','list_companies','search_tasks','list_tasks'].includes(r.firstTool)
      const planMentioned = /1\)|2\)|3\)|first|then|step/i.test(r.content)
      return { pass: okStart, reason: okStart ? 'started chain correctly' : `wrong start: ${r.firstTool}`, extra: planMentioned ? 'plan mentioned ✓' : '' }
    },
  },
  {
    name: 'H2 — Ambiguous follow-up after ambiguity',
    messages: [
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
      { role: 'assistant', content: 'Two EPC PEB projects exist. Dhruv Construction (Ongoing) or Acme Builders (Completed)?' },
      { role: 'user', content: 'the active one' },
    ],
    check: (r) => {
      // Must infer: Ongoing = Dhruv Construction → call get_project_stats with p-DHRUV
      const correct = r.firstTool === 'get_project_stats' && /p-DHRUV/.test(r.firstArgs || '')
      return { pass: correct, reason: correct ? 'inferred Dhruv from "active"' : `tool=${r.firstTool} args=${(r.firstArgs||'').slice(0,80)}` }
    },
  },
  {
    name: 'H3 — Delete by description (no UUID in context)',
    messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'delete yesterday\'s +5 sqm entry on Brickwork in Soul Space' },
    ],
    check: (r) => {
      // Best: starts the resolution chain (list_projects / search / etc.)
      const ok = r.firstTool && ['list_projects','list_companies','search_tasks','list_tasks','list_subactivities','list_progress_history'].includes(r.firstTool)
      return { pass: ok, reason: ok ? `started chain with ${r.firstTool}` : `wrong: ${r.firstTool||'(no tool)'}` }
    },
  },
  {
    name: 'H4 — Hindi action',
    messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'Soul Space mein wiring ke baad fixture installation, FS 0 lag dep banao' },
    ],
    check: (r) => {
      // Should call list_projects, not ask for clarification
      const ok = r.firstTool && ['list_projects','list_companies','search_tasks'].includes(r.firstTool)
      const asks = /clarify|specify|company|paste|provide|details/i.test(r.content)
      return { pass: ok && !asks, reason: ok ? (asks ? `tool ok but also asked: "${r.content.slice(0,80)}"` : `correct: ${r.firstTool}`) : `no tool, asked: "${r.content.slice(0,80)}"` }
    },
  },
  {
    name: 'H5 — Inferred intent (vague request)',
    messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'how am I doing this week?' },
    ],
    check: (r) => {
      // Reasonable response: call get_project_stats OR ask which project
      const callsTool = !!r.firstTool
      const asksQuestion = /which|specific|particular|project name/i.test(r.content)
      const pass = callsTool || asksQuestion
      return { pass, reason: callsTool ? `called ${r.firstTool}` : (asksQuestion ? 'asked which project ✓' : `unclear: ${r.content.slice(0,80)}`) }
    },
  },
  {
    name: 'H6 — Recovery from prior error',
    messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'log progress on Wiring' },
      { role: 'assistant', content: null, tool_calls: [{ id: 'c1', type: 'function', function: { name: 'list_projects', arguments: JSON.stringify({ search_query: 'Wiring' })}}]},
      { role: 'tool', tool_call_id: 'c1', content: JSON.stringify({ total: 0, projects: [] })},
      { role: 'assistant', content: 'I couldn\'t find a project called "Wiring". Did you mean a task name?' },
      { role: 'user', content: 'yes wiring is a task inside Soul Space, log +3' },
    ],
    check: (r) => {
      const ok = r.firstTool && ['list_projects','search_tasks','list_tasks','list_companies'].includes(r.firstTool)
      const usesSoulSpace = (r.firstArgs || '').toLowerCase().includes('soul')
      return { pass: ok && usesSoulSpace, reason: ok ? (usesSoulSpace ? `correct + scoped to Soul Space` : `tool ok but didn't scope: ${r.firstArgs}`) : `wrong: ${r.firstTool||'(no tool)'}` }
    },
  },
]

async function callModel(modelId, messages) {
  const start = Date.now()
  try {
    const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${OR_KEY}`, 'Content-Type': 'application/json', 'HTTP-Referer': 'https://onsite-hub.vercel.app', 'X-Title': 'Haiku vs Sonnet' },
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
  console.log('  HAIKU vs SONNET — Find what only Sonnet can do')
  console.log('═══════════════════════════════════════════════════════════════\n')

  let haikuPass = 0, sonnetPass = 0
  let onlyHaiku = 0, onlySonnet = 0, both = 0, neither = 0

  let g2Pass = 0, g3Pass = 0

  for (const test of TESTS) {
    console.log(`${test.name}`)
    const h = await callModel('anthropic/claude-haiku-4-5', test.messages)
    const s = await callModel('anthropic/claude-sonnet-4-6', test.messages)
    const g2 = await callModel('google/gemini-2.0-flash-001', test.messages)
    const g3 = await callModel('google/gemini-3-flash-preview', test.messages)

    let hEval = { pass: false, reason: 'call failed' }
    let sEval = { pass: false, reason: 'call failed' }
    let g2Eval = { pass: false, reason: 'call failed' }
    let g3Eval = { pass: false, reason: 'call failed' }
    if (h.ok) hEval = test.check(h)
    if (s.ok) sEval = test.check(s)
    if (g2.ok) g2Eval = test.check(g2)
    if (g3.ok) g3Eval = test.check(g3)

    if (hEval.pass) haikuPass++
    if (sEval.pass) sonnetPass++
    if (g2Eval.pass) g2Pass++
    if (g3Eval.pass) g3Pass++

    if (hEval.pass && sEval.pass) { both++; }
    else if (hEval.pass && !sEval.pass) { onlyHaiku++; }
    else if (!hEval.pass && sEval.pass) { onlySonnet++; }
    else { neither++; }

    const m = (ev) => ev.pass ? '✅' : '❌'
    console.log(`  Haiku  4.5    ${m(hEval)}  ${(h.elapsed/1000).toFixed(2)}s  in=${h.inputTokens||0} out=${h.outputTokens||0}  ${hEval.reason}`)
    console.log(`  Sonnet 4.6    ${m(sEval)}  ${(s.elapsed/1000).toFixed(2)}s  in=${s.inputTokens||0} out=${s.outputTokens||0}  ${sEval.reason}`)
    console.log(`  Gemini 2.0F   ${m(g2Eval)}  ${(g2.elapsed/1000).toFixed(2)}s  in=${g2.inputTokens||0} out=${g2.outputTokens||0}  ${g2Eval.reason}`)
    console.log(`  Gemini 3F pv  ${m(g3Eval)}  ${(g3.elapsed/1000).toFixed(2)}s  in=${g3.inputTokens||0} out=${g3.outputTokens||0}  ${g3Eval.reason}`)
    if (g3.ok && g3.content) console.log(`         g3 reply: "${g3.content.slice(0, 110).replace(/\n/g,' ')}"`)
    console.log()
  }

  console.log(`\nGemini 2.0 Flash: ${g2Pass}/${TESTS.length}`)
  console.log(`Gemini 3 Flash Preview: ${g3Pass}/${TESTS.length}`)

  console.log('═══════════════════════════════════════════════════════════════')
  console.log('  VERDICT')
  console.log('═══════════════════════════════════════════════════════════════\n')
  console.log(`Haiku passed:  ${haikuPass}/${TESTS.length}`)
  console.log(`Sonnet passed: ${sonnetPass}/${TESTS.length}`)
  console.log(``)
  console.log(`Both passed:        ${both}/${TESTS.length}`)
  console.log(`Only Sonnet won:    ${onlySonnet}/${TESTS.length}   ← Sonnet's real edge`)
  console.log(`Only Haiku won:     ${onlyHaiku}/${TESTS.length}`)
  console.log(`Neither passed:     ${neither}/${TESTS.length}`)

  if (onlySonnet === 0) {
    console.log(`\n→ Haiku covers everything Sonnet does on this set.`)
    console.log(`  Sonnet escalation only valuable for retries on hallucination guard.`)
  } else {
    console.log(`\n→ Sonnet wins ${onlySonnet} case(s) Haiku can't. These are the real escalation triggers.`)
  }
}

main().catch(e => { console.error(e); process.exit(1) })

#!/usr/bin/env node
// Stress-test Gemini 2.0 Flash against 8 realistic Onsite Task AI prompts
// covering the full surface area: reads, actions, multi-turn chains,
// ambiguous names, deletes, search.
//
// Run: node Onsite/task-ai/scripts/gemini-stress-test.mjs

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
} catch (e) {
  console.error('Could not load .env.local:', e.message)
}

const OR_KEY = process.env.OPENROUTER_API_KEY
if (!OR_KEY) { console.error('OPENROUTER_API_KEY not set'); process.exit(1) }

const MODEL = 'google/gemini-2.0-flash-001'
const COST_IN = 0.10  // $/M input
const COST_OUT = 0.40 // $/M output

// Use the real (trimmed) Onsite system prompt with the key rules
const SYSTEM = `You are Onsite AI, a chat-first assistant for construction project management.

CRITICAL RULES:
- Users do NOT know UUIDs. NEVER ask users for UUIDs / IDs.
- To find a project/task by NAME, call the list_* tools and resolve the UUID yourself.
- Workflow: list_companies → list_projects(search_query=NAME) → list_tasks(project_id, search_query=NAME).
- When list_projects returns ambiguous:true (multiple projects with same name in different companies), ASK the user which one — do not silently pick.
- Remember tool results in conversation context: if record_task_progress returned progress_history_id "abc", use that for the next delete — do not re-ask.
- For "delete this/that/last" → look at the most recent action's tool_call_result for the ID.
- NEVER fake a delete by creating a negative progress entry. Use list_progress_history → delete_task_progress with the real UUID.
- Be concise. 2-4 sentences for routine confirmations.`

// Full toolset
const TOOLS = [
  { type: 'function', function: { name: 'list_companies', description: 'Lists all companies.', parameters: { type: 'object', properties: {}, required: [] }}},
  { type: 'function', function: { name: 'list_projects', description: 'Lists projects across the user\'s companies. Accepts search_query. Returns ambiguous:true if names collide across companies.', parameters: { type: 'object', properties: { search_query: { type: 'string' }, company_id: { type: 'string' }}, required: []}}},
  { type: 'function', function: { name: 'list_tasks', description: 'Lists tasks (billing activities) in a project.', parameters: { type: 'object', properties: { project_id: { type: 'string' }, search_query: { type: 'string' }, only_leaves: { type: 'boolean' }}, required: []}}},
  { type: 'function', function: { name: 'list_subactivities', description: 'Lists sub-activities under a leaf task.', parameters: { type: 'object', properties: { billing_activity_id: { type: 'string' }}, required: ['billing_activity_id']}}},
  { type: 'function', function: { name: 'list_dependencies', description: 'Lists task dependencies.', parameters: { type: 'object', properties: { company_id: { type: 'string' }, ba_id: { type: 'string' }}, required: []}}},
  { type: 'function', function: { name: 'list_progress_history', description: 'Lists individual progress entries with UUIDs for a sub-activity. Use before delete_task_progress when you do not have the UUID in context.', parameters: { type: 'object', properties: { billing_sub_activity_id: { type: 'string' }}, required: ['billing_sub_activity_id']}}},
  { type: 'function', function: { name: 'get_project_stats', description: 'Returns Main/Sub/Leaf/WithDeps + progress mix.', parameters: { type: 'object', properties: { project_id: { type: 'string' }, project_name: { type: 'string' }}, required: []}}},
  { type: 'function', function: { name: 'create_task_dependency', description: 'Creates a dep between two leaf tasks.', parameters: { type: 'object', properties: { primary_ba_id: { type: 'string' }, secondary_ba_id: { type: 'string' }, dep_type: { type: 'string', enum: ['finish_to_start','finish_to_finish','start_to_start','start_to_finish']}, lag: { type: 'integer', minimum: 0 }}, required: ['primary_ba_id','secondary_ba_id','dep_type','lag']}}},
  { type: 'function', function: { name: 'update_task_dependency', description: 'Update dep lag or type.', parameters: { type: 'object', properties: { id: { type: 'string' }, type: { type: 'string' }, lag: { type: 'integer' }}, required: ['id']}}},
  { type: 'function', function: { name: 'delete_task_dependency', description: 'Delete a dep.', parameters: { type: 'object', properties: { id: { type: 'string' }}, required: ['id']}}},
  { type: 'function', function: { name: 'record_task_progress', description: 'Logs progress on a sub-activity. Returns progress_history_id of the new entry.', parameters: { type: 'object', properties: { billing_sub_activity_id: { type: 'string' }, diff_quantity: { type: 'number' }, progress_date: { type: 'string' }, notes: { type: 'string' }}, required: ['billing_sub_activity_id','diff_quantity','progress_date']}}},
  { type: 'function', function: { name: 'delete_task_progress', description: 'Removes a progress entry by UUID.', parameters: { type: 'object', properties: { id: { type: 'string' }}, required: ['id']}}},
  { type: 'function', function: { name: 'search_tasks', description: 'Fuzzy search tasks across project/company/top-5-companies.', parameters: { type: 'object', properties: { query: { type: 'string' }, project_id: { type: 'string' }, company_id: { type: 'string' }}, required: ['query']}}},
]

// 8 representative test cases — covering the full bot surface area.
// Each has a system message + 1+ turns. The LAST turn is what we evaluate.
// "expectedTool" can be a string OR an array (any of these is correct).
const TESTS = [
  {
    name: 'T1 — Read: list projects',
    messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'show me all my projects' },
    ],
    expectedTool: ['list_projects', 'list_companies'],
    expectedNotAsk: ['UUID', 'ID', 'paste'],
  },
  {
    name: 'T2 — Read: project stats',
    messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'what is the breakdown of Soul Space project?' },
    ],
    expectedTool: ['list_projects', 'list_companies', 'get_project_stats', 'search_tasks'],
    expectedNotAsk: ['UUID', 'ID', 'paste'],
  },
  {
    name: 'T3 — Action: create dependency by name',
    messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'In Soul Space, make Plastering depend on Brickwork — finish to start, 1 day lag' },
    ],
    expectedTool: ['list_projects', 'list_companies', 'list_tasks', 'search_tasks'],
    expectedNotAsk: ['UUID', 'ID', 'paste', 'workorder'],
  },
  {
    name: 'T4 — Action: log progress',
    messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'log +12 sqm on Gypsum board in the Interior Project' },
    ],
    expectedTool: ['list_projects', 'list_companies', 'list_tasks', 'search_tasks'],
    expectedNotAsk: ['UUID', 'ID', 'paste'],
  },
  {
    name: 'T5 — Multi-turn: delete just-created progress (RULE 0.5)',
    messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'log +5 sqft on Block Wall Construction' },
      { role: 'assistant', content: 'Done!', tool_calls: [{ id: 'call_1', type: 'function', function: { name: 'record_task_progress', arguments: JSON.stringify({ billing_sub_activity_id: 'sub-uuid-1', diff_quantity: 5, progress_date: '2026-05-19' })}}]},
      { role: 'tool', tool_call_id: 'call_1', content: JSON.stringify({ success: true, progress_history_id: 'PROGRESS-ENTRY-UUID-abc-123', task_name: 'Block Wall Construction', new_total: 25 })},
      { role: 'assistant', content: 'Logged +5 sqft on Block Wall Construction. Total is now 25 sqft.' },
      { role: 'user', content: 'delete this 5 sqft, I dont want it' },
    ],
    expectedTool: 'delete_task_progress',
    expectedArgContains: 'PROGRESS-ENTRY-UUID-abc-123',
    expectedNotAsk: ['UUID', 'ID', 'paste', 'check in the Onsite app', 'progress history'],
  },
  {
    name: 'T6 — Ambiguous project (RULE 0.6)',
    messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'EPC PEB check' },
      { role: 'assistant', content: null, tool_calls: [{ id: 'call_p1', type: 'function', function: { name: 'list_projects', arguments: JSON.stringify({ search_query: 'EPC PEB' })}}]},
      { role: 'tool', tool_call_id: 'call_p1', content: JSON.stringify({
        success: true,
        total: 2,
        ambiguous: true,
        must_disambiguate: 'Multiple projects share this exact name across different companies. DO NOT pick one — ask the user.',
        exact_name_duplicates: [{
          name: 'epc peb',
          count: 2,
          options: [
            { project_id: 'p-1', company_id: 'c-1', company_name: 'Dhruv Construction', status: 'Ongoing' },
            { project_id: 'p-2', company_id: 'c-2', company_name: 'Acme Builders', status: 'Completed' },
          ]
        }],
        projects: [
          { id: 'p-1', name: 'EPC PEB', company_id: 'c-1', company_name: 'Dhruv Construction', status: 'Ongoing' },
          { id: 'p-2', name: 'EPC PEB', company_id: 'c-2', company_name: 'Acme Builders', status: 'Completed' },
        ],
      })},
    ],
    expectedNoToolCall: true,  // SHOULD ask user, not silently call another tool
    expectedContentContains: ['Dhruv Construction', 'Acme Builders'],
    expectedNotAsk: ['UUID', 'paste'],
  },
  {
    name: 'T7 — Search: cross-project find',
    messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'find all tasks with "brickwork" in name across my projects' },
    ],
    expectedTool: ['search_tasks', 'list_companies'],
    expectedNotAsk: ['UUID', 'ID'],
  },
  {
    name: 'T8 — Hindi-English mix action',
    messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'Soul Space mein wiring ke baad fixture installation karna hai, FS dep banao 0 lag' },
    ],
    expectedTool: ['list_projects', 'list_companies', 'list_tasks', 'search_tasks'],
    expectedNotAsk: ['UUID', 'ID', 'paste', 'speak English'],
  },
]

async function call(messages) {
  const start = Date.now()
  let res, data
  try {
    res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${OR_KEY}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://onsite-hub.vercel.app',
        'X-Title': 'Onsite Task AI Gemini Stress Test',
      },
      body: JSON.stringify({
        model: MODEL,
        messages,
        tools: TOOLS,
        tool_choice: 'auto',
        temperature: 0.1,
        max_tokens: 1500,
      }),
    })
    data = await res.json()
    const elapsed = Date.now() - start
    if (!res.ok) return { ok: false, elapsed, error: data?.error?.message || `HTTP ${res.status}` }
    const choice = data.choices?.[0]
    const message = choice?.message || {}
    const toolCalls = message.tool_calls || []
    return {
      ok: true,
      elapsed,
      finishReason: choice?.finish_reason,
      firstTool: toolCalls[0]?.function?.name,
      firstArgs: toolCalls[0]?.function?.arguments,
      allTools: toolCalls.map(t => t.function?.name),
      content: message.content || '',
      inputTokens: data.usage?.prompt_tokens || 0,
      outputTokens: data.usage?.completion_tokens || 0,
    }
  } catch (err) {
    return { ok: false, elapsed: Date.now() - start, error: err.message }
  }
}

function evaluate(test, r) {
  if (!r.ok) return { pass: false, reasons: [`call failed: ${r.error}`] }
  const reasons = []
  let pass = true

  // Tool expectation
  if (test.expectedNoToolCall) {
    if (r.firstTool) {
      pass = false
      reasons.push(`should NOT have called a tool (called: ${r.firstTool})`)
    } else {
      reasons.push(`✓ no tool call (correctly asked user)`)
    }
  } else if (test.expectedTool) {
    const expected = Array.isArray(test.expectedTool) ? test.expectedTool : [test.expectedTool]
    if (!r.firstTool) {
      pass = false
      reasons.push(`expected tool call (${expected.join(' or ')}) but got text only`)
    } else if (!expected.includes(r.firstTool)) {
      pass = false
      reasons.push(`expected ${expected.join(' or ')}, got ${r.firstTool}`)
    } else {
      reasons.push(`✓ correct tool: ${r.firstTool}`)
    }
  }

  // Args contain expected UUID
  if (test.expectedArgContains && r.firstArgs) {
    if (r.firstArgs.includes(test.expectedArgContains)) {
      reasons.push(`✓ args contain expected ID`)
    } else {
      pass = false
      reasons.push(`args missing expected "${test.expectedArgContains}" — got: ${r.firstArgs.slice(0, 100)}`)
    }
  }

  // Content should contain certain strings (for ambiguity test)
  if (test.expectedContentContains) {
    for (const s of test.expectedContentContains) {
      if (r.content.includes(s)) {
        reasons.push(`✓ content mentions "${s}"`)
      } else {
        pass = false
        reasons.push(`content missing "${s}"`)
      }
    }
  }

  // Should NOT contain forbidden patterns
  if (test.expectedNotAsk) {
    for (const s of test.expectedNotAsk) {
      if (r.content.toLowerCase().includes(s.toLowerCase())) {
        pass = false
        reasons.push(`⚠ content contains forbidden "${s}"`)
      }
    }
  }

  return { pass, reasons }
}

function fmtMoney(n) { return `$${n.toFixed(5)}` }

async function main() {
  console.log('\n═══════════════════════════════════════════════════════════════')
  console.log('  GEMINI 2.0 FLASH — Stress Test (8 prompts × full surface area)')
  console.log('═══════════════════════════════════════════════════════════════\n')

  let totalIn = 0, totalOut = 0, totalLatency = 0, passCount = 0
  const results = []

  for (const test of TESTS) {
    process.stdout.write(`${test.name}\n`)
    const r = await call(test.messages)
    const ev = evaluate(test, r)
    if (!r.ok) {
      console.log(`  ❌ ${r.error}\n`)
      results.push({ name: test.name, ok: false, error: r.error })
      continue
    }
    totalIn += r.inputTokens
    totalOut += r.outputTokens
    totalLatency += r.elapsed
    if (ev.pass) passCount++
    const cost = (r.inputTokens * COST_IN + r.outputTokens * COST_OUT) / 1_000_000
    const verdict = ev.pass ? '✅ PASS' : '❌ FAIL'
    console.log(`  ${verdict}   ${(r.elapsed/1000).toFixed(2)}s   in=${r.inputTokens} out=${r.outputTokens}   ${fmtMoney(cost)}`)
    for (const reason of ev.reasons) console.log(`         ${reason}`)
    if (r.content && r.content.length > 0) console.log(`         reply: "${r.content.slice(0, 150).replace(/\n/g, ' ')}"`)
    console.log()
    results.push({
      name: test.name,
      ok: true,
      pass: ev.pass,
      reasons: ev.reasons,
      tool: r.firstTool,
      args: r.firstArgs,
      content: r.content.slice(0, 300),
      elapsed: r.elapsed,
      tokens: { in: r.inputTokens, out: r.outputTokens },
      cost,
    })
  }

  // Summary
  console.log('\n═══════════════════════════════════════════════════════════════')
  console.log('  VERDICT')
  console.log('═══════════════════════════════════════════════════════════════\n')
  console.log(`Passed:  ${passCount} / ${TESTS.length}`)
  console.log(`Failed:  ${TESTS.length - passCount}`)
  console.log(`Avg latency:  ${(totalLatency / TESTS.length / 1000).toFixed(2)}s`)
  console.log(`Total cost (8 prompts):  ${fmtMoney((totalIn * COST_IN + totalOut * COST_OUT) / 1_000_000)}`)
  console.log(`Avg cost per prompt:  ${fmtMoney((totalIn * COST_IN + totalOut * COST_OUT) / 1_000_000 / TESTS.length)}`)

  // Compare to Haiku baseline ($0.00130/prompt from earlier test)
  const avgCost = (totalIn * COST_IN + totalOut * COST_OUT) / 1_000_000 / TESTS.length
  const haikuCostPerPrompt = 0.00130
  const ratio = haikuCostPerPrompt / avgCost
  console.log(`\nCost ratio vs Haiku:  Gemini is ${ratio.toFixed(1)}× cheaper`)

  // List failures
  const failures = results.filter(r => r.ok && !r.pass)
  if (failures.length > 0) {
    console.log('\n=== FAILURES ===')
    for (const f of failures) {
      console.log(`\n${f.name}`)
      for (const reason of f.reasons) console.log(`  ${reason}`)
    }
  }
}

main().catch(e => { console.error(e); process.exit(1) })

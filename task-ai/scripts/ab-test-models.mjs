#!/usr/bin/env node
// A/B test alternative models against the Onsite Task AI tool-call pattern.
// Sends the same 2 representative prompts to each candidate model via
// OpenRouter and reports: latency, tokens, tool-call correctness.
//
// Run from repo root:
//   node Onsite/task-ai/scripts/ab-test-models.mjs
//
// Requires OPENROUTER_API_KEY in env (loaded from .env.local).

import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))

// Load .env.local
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
if (!OR_KEY) {
  console.error('OPENROUTER_API_KEY not set')
  process.exit(1)
}

// Models to test. Haiku and Sonnet are baselines we already know.
const MODELS = [
  { id: 'anthropic/claude-haiku-4-5', label: 'Haiku 4.5 (baseline)', inputCost: 1.00, outputCost: 5.00 },
  { id: 'anthropic/claude-sonnet-4-6', label: 'Sonnet 4.6 (baseline)', inputCost: 3.00, outputCost: 15.00 },
  // Closest available proxy for Gemini 3.1 Flash Lite is Gemini Flash 1.5 (tool-call capable)
  { id: 'google/gemini-flash-1.5', label: 'Gemini Flash 1.5', inputCost: 0.075, outputCost: 0.30 },
  { id: 'google/gemini-2.0-flash-001', label: 'Gemini 2.0 Flash', inputCost: 0.10, outputCost: 0.40 },
  { id: 'moonshotai/kimi-k2', label: 'Kimi K2', inputCost: 0.73, outputCost: 3.49 },
  { id: 'openai/gpt-4o-mini', label: 'GPT-4o-mini', inputCost: 0.15, outputCost: 0.60 },
  { id: 'openai/gpt-5-mini', label: 'GPT-5 Mini (if available)', inputCost: 0.75, outputCost: 4.50 },
  { id: 'x-ai/grok-2-1212', label: 'Grok 2', inputCost: 2.00, outputCost: 10.00 },
]

// Trimmed Onsite Task AI system prompt — keeps tool-call discipline rules
// without the full 700 lines (which would skew token comparison).
const SYSTEM = `You are Onsite AI, a chat-first assistant for construction project management. You have tools to look up companies, projects, tasks, and to create dependencies / log progress.

RULES:
- Users do NOT know UUIDs. Never ask for them.
- For NAMES, call list_* tools to resolve UUIDs yourself.
- When the user asks to look up something, call the appropriate tool with their NAME as search_query.
- When the user asks to do an action (create dep, log progress), call the appropriate action tool.
- Be concise. Don't ask clarifying questions if the intent is clear.`

// Two representative prompts — one read, one action.
const PROMPTS = [
  {
    name: 'READ — "show me my projects"',
    messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'show me all my projects' },
    ],
    expectedTool: 'list_projects',
  },
  {
    name: 'ACTION — "make Plastering depend on Brickwork"',
    messages: [
      { role: 'system', content: SYSTEM },
      { role: 'user', content: 'In Soul Space project, make Plastering depend on Brickwork (finish to start, lag 0)' },
    ],
    expectedTool: 'list_companies', // first step in resolution chain
  },
]

// Same tool definitions used by the real bot, slimmed.
const TOOLS = [
  {
    type: 'function',
    function: {
      name: 'list_companies',
      description: "Lists all companies the user has access to.",
      parameters: { type: 'object', properties: {}, required: [] },
    },
  },
  {
    type: 'function',
    function: {
      name: 'list_projects',
      description: "Lists projects with their names + IDs. Accepts a search_query to filter.",
      parameters: {
        type: 'object',
        properties: {
          company_id: { type: 'string' },
          search_query: { type: 'string', description: 'Substring to filter project names.' },
        },
        required: [],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'list_tasks',
      description: "Lists tasks (billing activities) in a project.",
      parameters: {
        type: 'object',
        properties: {
          project_id: { type: 'string' },
          search_query: { type: 'string' },
        },
        required: [],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'create_task_dependency',
      description: 'Creates a dependency between two leaf tasks.',
      parameters: {
        type: 'object',
        properties: {
          primary_ba_id: { type: 'string' },
          secondary_ba_id: { type: 'string' },
          dep_type: { type: 'string', enum: ['finish_to_start', 'finish_to_finish', 'start_to_start', 'start_to_finish'] },
          lag: { type: 'integer', minimum: 0 },
        },
        required: ['primary_ba_id', 'secondary_ba_id', 'dep_type', 'lag'],
      },
    },
  },
]

async function callModel(modelId, messages) {
  const start = Date.now()
  let res, data
  try {
    res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${OR_KEY}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://onsite-hub.vercel.app',
        'X-Title': 'Onsite Task AI A/B Test',
      },
      body: JSON.stringify({
        model: modelId,
        messages,
        tools: TOOLS,
        tool_choice: 'auto',
        temperature: 0.1,
        max_tokens: 1000,
      }),
    })
    const elapsed = Date.now() - start
    data = await res.json()
    if (!res.ok) {
      return { ok: false, elapsed, error: data?.error?.message || `HTTP ${res.status}`, raw: data }
    }
    const choice = data.choices?.[0]
    const message = choice?.message
    const toolCalls = message?.tool_calls || []
    const firstTool = toolCalls[0]?.function?.name
    const firstArgs = toolCalls[0]?.function?.arguments
    return {
      ok: true,
      elapsed,
      finishReason: choice?.finish_reason,
      firstTool,
      firstArgs,
      content: message?.content?.slice(0, 200) || '',
      inputTokens: data.usage?.prompt_tokens || 0,
      outputTokens: data.usage?.completion_tokens || 0,
    }
  } catch (err) {
    return { ok: false, elapsed: Date.now() - start, error: err.message }
  }
}

function fmtMoney(n) {
  return `$${n.toFixed(5)}`
}

async function main() {
  console.log('\n═══════════════════════════════════════════════════════════════')
  console.log('  ONSITE TASK AI — Model A/B Test')
  console.log('═══════════════════════════════════════════════════════════════\n')
  console.log(`Testing ${MODELS.length} models × ${PROMPTS.length} prompts = ${MODELS.length * PROMPTS.length} calls\n`)

  const results = []

  for (const prompt of PROMPTS) {
    console.log(`\n━━━ Prompt: ${prompt.name} ━━━`)
    console.log(`    Expected first tool: ${prompt.expectedTool}\n`)

    for (const model of MODELS) {
      process.stdout.write(`  ${model.label.padEnd(50)} `)
      const r = await callModel(model.id, prompt.messages)
      if (!r.ok) {
        console.log(`❌ ${r.error}`)
        results.push({ model: model.label, prompt: prompt.name, ok: false, error: r.error })
        continue
      }
      const correct = r.firstTool === prompt.expectedTool
      const correctMark = correct ? '✅' : (r.firstTool ? '⚠️ ' : '❌')
      const cost =
        (r.inputTokens * model.inputCost + r.outputTokens * model.outputCost) / 1_000_000
      console.log(
        `${correctMark} ${(r.elapsed / 1000).toFixed(2)}s  ` +
        `in=${String(r.inputTokens).padStart(4)} out=${String(r.outputTokens).padStart(3)}  ` +
        `${fmtMoney(cost)}  tool=${r.firstTool || '(none)'}`
      )
      results.push({
        model: model.label,
        modelId: model.id,
        prompt: prompt.name,
        ok: true,
        correctTool: correct,
        toolCalled: r.firstTool,
        latencyMs: r.elapsed,
        inputTokens: r.inputTokens,
        outputTokens: r.outputTokens,
        costUSD: cost,
        replyPreview: r.content,
      })
    }
  }

  // Summary
  console.log('\n\n═══════════════════════════════════════════════════════════════')
  console.log('  SUMMARY (ranked by avg cost per prompt)')
  console.log('═══════════════════════════════════════════════════════════════\n')

  const byModel = {}
  for (const r of results) {
    if (!r.ok) continue
    byModel[r.model] = byModel[r.model] || { runs: 0, totalCost: 0, totalLatency: 0, correctCount: 0 }
    byModel[r.model].runs++
    byModel[r.model].totalCost += r.costUSD
    byModel[r.model].totalLatency += r.latencyMs
    if (r.correctTool) byModel[r.model].correctCount++
  }

  const summary = Object.entries(byModel)
    .map(([model, s]) => ({
      model,
      avgCost: s.totalCost / s.runs,
      avgLatencyMs: s.totalLatency / s.runs,
      correctRate: `${s.correctCount}/${s.runs}`,
    }))
    .sort((a, b) => a.avgCost - b.avgCost)

  console.log('Model'.padEnd(50), 'AvgCost'.padStart(12), 'AvgLatency'.padStart(13), 'Tool✓'.padStart(8))
  console.log('-'.repeat(85))
  for (const s of summary) {
    console.log(
      s.model.padEnd(50),
      fmtMoney(s.avgCost).padStart(12),
      `${(s.avgLatencyMs / 1000).toFixed(2)}s`.padStart(13),
      s.correctRate.padStart(8)
    )
  }

  console.log('\nFull JSON:')
  console.log(JSON.stringify(results, null, 2))
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})

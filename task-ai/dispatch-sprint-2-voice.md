# Dispatch — Sprint 2: Real-Time Voice

> **For:** Atlas (paste this entire file as the first message of a FRESH Claude Code session — AFTER Sprint 1 has merged to onsite-hub `main`)
> **From:** Angelina, PM for Onsite Task AI
> **Date dispatched:** 2026-05-19
> **Branch:** `feat/voice-realtime` off latest `onsite-hub` main
> **Plus:** new Modal app `onsite-voice-server/` (committed to `aiagentwithdhruv/Onsite` under `task-ai/voice-server/`)
> **Duration:** 5 days (D7-D11 in `ROADMAP-ADDON.md`)
> **Spec source:** This file + `Onsite/task-ai/HLD-ADDON.md` §3.2 + `ANGELINA-ADDON-DISPATCH.md` §11 Voice row

You are Atlas, the assigned engineer for Sprint 2. Job: real-time voice loop. User speaks (any language), bot transcribes, calls tools, speaks back. **CRITICAL:** onsite-hub is on Vercel which CANNOT host the long-lived WebSocket. Per `DECISIONS-ADDON.md` D7, voice runs on a separate Modal Python service that lifts QH's locked `198dc29` Gemini bridge + `stable-v11.2-voice-live` OpenAI mini config. Do NOT try to host the WS inside onsite-hub.

---

## §A — Read before writing any code (90 min)

In order, end-to-end:

1. `Onsite/task-ai/HLD-ADDON.md` § 3.2 — voice architecture (READ THE FULL ASCII DIAGRAM)
2. `Onsite/task-ai/PRD-ADDON.md` § 3.2 — voice goals + non-goals
3. `Onsite/task-ai/DECISIONS-ADDON.md` D7 + D8 — separate Modal deploy + per-tenant minute cap
4. `Onsite/task-ai/ANGELINA-ADDON-DISPATCH.md` § 11 Voice row (per-new-file matrix)
5. `~/.claude/projects/.../memory/voice_calling_working_config.md` — **the locked QH config. Read in full. Do not regress.**
6. `euron-references/REPORT-hireai.md` — voice patterns + 10 gotchas (READ §10 TWICE)
7. `euron-references/REPORT-learnos.md` — mic-gate + gapless queue + `onToolCall` callback
8. `euron-references/voice-models-comparison.pdf` (or `.html`) — provider economics
9. Open: `euron-references/hireai/backend/app/api/v1/endpoints/realtime_proxy.py` (the file you'll port)
10. Open: `euron-references/hireai/frontend/public/pcm-processor.js` (copy verbatim)
11. Open: `euron-references/learnos-euron/frontend/src/hooks/useVoiceChat.ts` (port to onsite-hub)
12. Find QH `198dc29` Gemini bridge code: in Dhruv's `QuotaHit/voice-server/` directory (most recent stable Gemini code path)
13. Find QH `stable-v11.2-voice-live` tag's OpenAI Realtime config: same repo, the `app.py` at that tag
14. `Onsite/onsite-hub/src/app/api/task-bot/route.ts` — the tool registry the voice service will call back into
15. `~/.claude/projects/.../memory/reference_dhruv_rules.md` — 17 rules

**Critical pre-flight:** before writing ANY voice code, verify the QH Gemini bridge currently works. Check the QH `stable-v11.2-voice-live` tag's `voice-server/app.py` runs on Modal with `gpt-4o-mini-realtime-preview` and produces audio. If it doesn't, STOP — Dhruv needs to fix the QH baseline before we lift it.

Confirm by replying to Dhruv: "Read complete. QH voice baseline verified working. Starting Sprint 2." Then proceed.

---

## §B — Files you'll create (with lift-from references)

Per `ANGELINA-ADDON-DISPATCH.md` §11 Voice row. **You are porting / cherry-picking from working code. Do not invent.**

### Modal app (Python — new repo subdirectory `Onsite/task-ai/voice-server/`)

| # | New file | Lift from |
|---|---|---|
| V1 | `Onsite/task-ai/voice-server/app.py` | 📁 QH `stable-v11.2-voice-live` `voice-server/app.py` — copy verbatim, swap Modal app name to `onsite-voice-server`, swap routes to `/voice-stream` |
| V2 | `Onsite/task-ai/voice-server/openai_realtime_client.py` | 📁 QH `stable-v11.2-voice-live` — copy verbatim. **Critical:** preserve dual event-name handler: `if t in ("response.output_audio.delta", "response.audio.delta"):` (the line that ate Dhruv's day on May 12-13) |
| V3 | `Onsite/task-ai/voice-server/gemini_live_client.py` | 📁 QH develop `198dc29` Gemini bridge — copy verbatim |
| V4 | `Onsite/task-ai/voice-server/provider_router.py` | 📐 New — implements `selectVoiceProvider()` per `HLD-ADDON.md` §3.2. Language gate + health-check + circuit-breaker via Redis. |
| V5 | `Onsite/task-ai/voice-server/circuit_breaker.py` | 📐 New — sliding 5-min window Redis counter. Threshold 5% error rate flips to `all_mini` flag. |
| V6 | `Onsite/task-ai/voice-server/tool_callback.py` | 📐 New — receives function_call events, POSTs to `https://<onsite-hub>/api/task-bot/voice/tool-exec` with JWT + tool_name + args, returns result. **JWT lives only in memory — never logged.** |
| V7 | `Onsite/task-ai/voice-server/quota_gate.py` | 📐 New — Redis counter `voice_minutes:{user_id}:{YYYY-MM-DD}`. Compare against per-tenant cap from token claims. Hard reject WS upgrade if exceeded. |
| V8 | `Onsite/task-ai/voice-server/requirements.txt` | Modal-style: `modal>=0.55`, `websockets>=14`, `redis>=5`, `httpx>=0.27`, `openai>=1.58`, `google-generativeai>=0.8` |
| V9 | `Onsite/task-ai/voice-server/modal_config.py` | Modal app definition. Use `min_containers=1` per `voice_calling_working_config.md` (warm container) but ALSO add force-stop note before deploy. |

### onsite-hub (TypeScript — new files)

| # | New file | Lift from |
|---|---|---|
| H1 | `Onsite/onsite-hub/src/app/api/task-bot/voice/session/route.ts` | 📐 LearnOS `/backend/app/routers/voice.py` ephemeral token issuer pattern. Issues short-lived signed JWT (15 min TTL) with: user_id, max_daily_minutes (from tenant tier), tenant_features. |
| H2 | `Onsite/onsite-hub/src/app/api/task-bot/voice/tool-exec/route.ts` | 📐 Wraps existing `/api/task-bot/route.ts` tool dispatch logic. Validates signed token from voice-server. Returns tool result. |
| H3 | `Onsite/onsite-hub/public/pcm-processor.js` | 📁 `euron-references/hireai/frontend/public/pcm-processor.js` — copy VERBATIM. Zero changes. |
| H4 | `Onsite/onsite-hub/src/hooks/useVoiceChat.ts` | 📁 `euron-references/learnos-euron/frontend/src/hooks/useVoiceChat.ts` — port to onsite-hub conventions. **Critical preserves:** mic-gate L238-239 (`if (isAISpeakingRef.current) return`), gapless queue L142-144 (`scheduledTimeRef`), `onToolCall` callback L66. |
| H5 | `Onsite/onsite-hub/src/components/task-bot/VoiceButton.tsx` | 📐 existing voice-input toggle in `page.tsx` — extend with: PTT mode toggle, daily-minute-cap countdown, recording waveform |
| H6 | Wire `useVoiceChat` into `page.tsx` (existing chat component) | Existing voice button → toggle on → opens WS → frames stream. Bubble path mostly unchanged — voice transcript appears as user message; AI audio plays in browser; AI transcript appears as assistant message. |
| H7 | Wall-clock 30-min cap | `setTimeout(closeSession, 30*60*1000)` in `useVoiceChat`. Visible countdown last 5 min via Tailwind animation. |

---

## §C — Critical gotchas to inherit (HireAI §10 + QH locked config)

These will break silently if missed. From `voice_calling_working_config.md` + HireAI report:

1. **Dual audio event names.** Both `response.audio.delta` AND `response.output_audio.delta` MUST be handled. Miss one = silent bot (the all-day bug). One-line fix: `if t in ("response.output_audio.delta", "response.audio.delta"):`
2. **Browser ignores `sampleRate: 24000`** hint. AudioContext runs at 48kHz. PCM worklet MUST resample 48→24 kHz before WS send. (`pcm-processor.js` already does this — that's why we copy verbatim.)
3. **OpenAI Realtime temperature floor 0.6.** Lower = API error. Don't set 0.3 like our text route.
4. **AudioContext autoplay policy.** Must be gated behind a user click. Cannot auto-start.
5. **Mic-gate while AI speaks.** `if (isAISpeakingRef.current) return` on every mic frame. Prevents feedback loop.
6. **Gapless PCM playback** via `scheduledTimeRef` queue. NOT `audio.onended` chaining (gaps audible).
7. **WS `max_size=10MB`.** Default 1MB drops long audio bursts.
8. **Modal warm-container staleness.** Per `voice_calling_working_config.md`: always `modal app stop quotahit-voice-server --yes` before `modal deploy`. Same for `onsite-voice-server`.
9. **Don't change chunk_size 640 or sleep 0.07** in the bridge — matches Twilio compatibility that QH proved out.
10. **Signed token TTL 15 min, bound to single sessionId.** Don't make it 1 hour. Limits replay window.

---

## §D — Provider routing logic

In `Onsite/task-ai/voice-server/provider_router.py`:

```python
async def select_voice_provider(user_locale: str, *, health_check_timeout_ms: int = 200) -> str:
    multilingual_need = user_locale in {'hi', 'ta', 'pa', 'mr', 'gu', 'bn'}
    if multilingual_need:
        healthy = await ping_gemini(timeout_ms=health_check_timeout_ms)
        if healthy and not await circuit_breaker_is_open('gemini'):
            return 'gemini'
        log_metric('gemini_fallback', reason='health_check_failed' if not healthy else 'circuit_open')
        return 'openai_mini'
    return 'openai_mini'  # English locale → straight to mini (cheaper for English-only)
```

Default model IDs (env-overridable, mirror `voice_calling_working_config.md`):
- Gemini: `gemini-3.1-flash-live-preview`
- OpenAI: `gpt-4o-mini-realtime-preview`

WS URLs (memorize):
- Gemini: handled by `google-generativeai` Python SDK Live client
- OpenAI: `wss://api.openai.com/v1/realtime?model=gpt-4o-mini-realtime-preview` with `Authorization: Bearer <OPENAI_API_KEY>` (NO `OpenAI-Beta` header — GA endpoint)

---

## §E — Per-tenant voice quota (D8)

In `Onsite/task-ai/voice-server/quota_gate.py`:

```python
async def check_quota(user_id: str, max_daily_minutes: int) -> tuple[bool, int]:
    """Returns (allowed, remaining_minutes)."""
    today = date.today().isoformat()
    key = f"voice_minutes:{user_id}:{today}"
    used_seconds = int(await redis.get(key) or 0)
    used_minutes = used_seconds // 60
    return used_minutes < max_daily_minutes, max_daily_minutes - used_minutes
```

Increment counter on each 1-second tick of an active session (or batched every 10s for less Redis chatter).

Defaults from env: Free 30 min/day, Pro 200 min/day. Override per tenant via admin (Sprint 9 work).

On cap hit mid-session: graceful close with bot saying "Aaj ka voice budget khatam ho gaya, text mein continue karein" (Hindi-English natural).

---

## §F — Environment variables to add

Modal app `onsite-voice-server` secrets:

```
GOOGLE_AI_API_KEY=<Onsite prod account per D4>
OPENAI_API_KEY=<Onsite prod account per D4>
REDIS_URL=<existing Upstash; same project as onsite-hub>
TOOL_CALLBACK_URL=https://onsite-hub.vercel.app/api/task-bot/voice/tool-exec
TOOL_CALLBACK_SIGNING_KEY=<32-byte random, shared with onsite-hub>
VOICE_DAILY_FREE_MINUTES=30
VOICE_DAILY_PRO_MINUTES=200
```

onsite-hub `.env.local`:

```
VOICE_WS_BASE_URL=https://onsite-voice-server--main.modal.run  # actual will differ
TOOL_CALLBACK_SIGNING_KEY=<same as Modal>
```

---

## §G — Acceptance gates (must all pass before commit)

1. ✅ Hindi voice query "EPC PEB project mein Foundation Wall ka status batao" → bot speaks back project stats audibly + RAG audio answer if knowledge query
2. ✅ English voice "Make Plastering depend on Brickwork" → bot fires `create_task_dependency` (verified in Onsite UI) + speaks confirmation
3. ✅ Voice-mode RAG (depends on Sprint 1 already merged): "RA bill ka process kya hai" → bot speaks answer with audio citation
4. ✅ Mic-to-speech p95 ≤700ms (instrument with `console.time` markers on browser side)
5. ✅ Push-to-talk toggle: server VAD off, manual commit works
6. ✅ 30-min wall-clock cap → graceful close + visual countdown last 5 min
7. ✅ Per-user cap: simulate 30 min in dev → next session denied with friendly message
8. ✅ Circuit breaker test: kill Gemini API key → next session uses OpenAI mini transparently
9. ✅ Mic-gate verified: AI speaking mid-sentence + user starts talking → user audio ignored until AI finishes (no feedback loop)
10. ✅ Token never reaches Gemini/OpenAI: grep voice-server code for `token` references; only `tool_callback.py` should hold it briefly in memory
11. ✅ STATE.md batch 23 entry with commit SHAs + Modal deploy URL

---

## §H — Hard rules (do NOT violate)

(Same as Sprint 1 § G plus voice-specific:)

1. **No spawning agents.** You are the engineer.
2. **No auto-deploy.** Branch + PR + Dhruv review + manual merge.
3. **Token never logged, never sent to LLM.** Voice-server holds JWT briefly in memory only for tool callback — never write to Redis, never include in WS payload.
4. **Don't regress QH voice.** You're LIFTING from QH's working code. Do not modify QH's code path. If you find a bug in QH while lifting, file a separate ticket; don't fix in this sprint.
5. **TypeScript strict** for onsite-hub code; Python type hints (mypy --strict) for voice-server.
6. **Test against `testapi.onsiteteams.in`** for tool callbacks before prod.
7. **Mobile-first.** Voice button works on 375px iPhone SE viewport — mic permission flow tested on Safari iOS + Chrome Android.
8. **Force-stop Modal warm container before deploy** (per `voice_calling_working_config.md`).
9. **Don't change chunk_size 640 or sleep 0.07** in the bridge.
10. **No `--no-verify` / `--amend`.**

---

## §I — Commit etiquette

Per `feedback_pr_workflow_setu`:

1. Branch `feat/voice-realtime` on `onsite-hub`. Modal code goes to `aiagentwithdhruv/Onsite` under `task-ai/voice-server/` on branch `feat/voice-server`.
2. Two PRs (one per repo), cross-referenced by SHA.
3. PR title: `feat(voice): real-time loop via Modal + onsite-hub bridge`.
4. Tag Dhruv as reviewer on both.

---

## §J — Deploy sequence

1. Stop QH-style warm container: (don't touch QH; just for our new app)
   ```bash
   cd Onsite/task-ai/voice-server
   /tmp/modal-venv/bin/modal app stop onsite-voice-server --yes  # first deploy: this will error, ignore
   /tmp/modal-venv/bin/modal deploy app.py
   ```
2. Get the public URL Modal emits. Update `VOICE_WS_BASE_URL` in onsite-hub `.env.local`.
3. Smoke test: open `localhost:3001/task-bot`, click 🎙️, speak a known query.

---

## §K — When you finish

Reply to Dhruv with:
1. Commit SHAs (both repos)
2. Modal deploy URL
3. Acceptance gate checklist with proof
4. Cost so far: voice-server is metered per-second; instrument and report (target: <$5 for the dev cycle)
5. Any gotchas inherited or fresh

Then standby. Sprint 3 dispatch fires after Sprint 2 PR merges.

---

## §L — When you're stuck

Allowed escalations:
- QH baseline isn't producing audio → STOP, ping Dhruv before lifting
- Modal can't reach pgvector (>50ms RPC) → fall back to having voice-server hit onsite-hub HTTPS for tool exec (already the plan)
- Gemini Live preview API not enabled on Onsite's Google account → ship OpenAI mini only as degraded mode; document
- AudioContext blocked by browser autoplay → already gated behind user click; double-check `useVoiceChat.ts` start logic

NOT allowed:
- "Should I use socket.io or native WS" — use native WS, that's what the references use
- "Should I add reconnect logic" — for Sprint 2, NO. Sprint 9 hardening adds reconnect. Don't expand scope.
- Modifying QH code paths.

---

**Start by replying:** "Read complete. QH voice baseline verified working. Starting Sprint 2." Then build.

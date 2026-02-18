# LangGraph Agents Spec

**All 4 agents: state design, node definitions, prompts, error handling, and fallback strategies.**

---

## 1. Shared Architecture

### LLM Configuration
```python
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

# Primary: Claude Sonnet for complex reasoning
llm_sonnet = ChatAnthropic(model="claude-sonnet-4-5-20250929", temperature=0)

# Cheap: Claude Haiku for scoring/classification
llm_haiku = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)

# Fallback: GPT-4o when Claude is down
llm_fallback = ChatOpenAI(model="gpt-4o", temperature=0)

def get_llm(task_type: str):
    """Returns appropriate LLM with fallback."""
    model_map = {
        "scoring": llm_haiku,        # cheap, fast
        "ranking": llm_haiku,        # cheap, fast
        "stale_detection": None,     # no AI needed, pure logic
        "anomaly_detection": llm_haiku,
        "brief_generation": llm_sonnet,
        "research": llm_sonnet,      # needs best reasoning
        "close_strategy": llm_sonnet,
        "weekly_report": llm_sonnet,
        "assignment": llm_haiku,
    }
    return model_map.get(task_type, llm_sonnet)
```

### Fallback Strategy
```python
async def call_llm_with_fallback(llm_primary, prompt, fallback_llm=llm_fallback):
    """Try primary LLM, fall back to GPT-4o on failure."""
    try:
        response = await llm_primary.ainvoke(prompt)
        return response, llm_primary.model_name
    except Exception as e:
        log.warning(f"Primary LLM failed: {e}. Falling back to GPT-4o.")
        try:
            response = await fallback_llm.ainvoke(prompt)
            return response, fallback_llm.model_name
        except Exception as e2:
            log.error(f"Fallback LLM also failed: {e2}")
            raise AllLLMsFailedError("Both Claude and GPT-4o are down")
```

### Cost Tracking (wraps every AI call)
```python
async def tracked_llm_call(llm, prompt, agent_type, lead_id=None, user_id=None):
    """Call LLM and log usage to ai_usage_log table."""
    start = time.time()
    try:
        response, model_used = await call_llm_with_fallback(llm, prompt)
        duration = int((time.time() - start) * 1000)

        await supabase.table("ai_usage_log").insert({
            "agent_type": agent_type,
            "model": model_used,
            "input_tokens": response.usage_metadata.get("input_tokens", 0),
            "output_tokens": response.usage_metadata.get("output_tokens", 0),
            "cost_usd": calculate_cost(model_used, response.usage_metadata),
            "lead_id": lead_id,
            "triggered_by": user_id,
            "duration_ms": duration,
            "success": True,
        }).execute()

        return response
    except Exception as e:
        await supabase.table("ai_usage_log").insert({
            "agent_type": agent_type,
            "model": "failed",
            "success": False,
            "error_message": str(e),
        }).execute()
        raise
```

---

## 2. Agent 1: Daily Pipeline (Scheduled — 7:30 AM)

### State Definition
```python
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph

class DailyPipelineState(TypedDict):
    # Input
    leads: List[dict]              # raw leads from Supabase
    notes: dict                    # lead_id -> [notes]
    activities: dict               # lead_id -> [activities]
    reps: List[dict]               # all active reps

    # Processing
    scored_leads: List[dict]       # leads with AI scores
    stale_leads: List[dict]        # leads with 7+ days no activity
    anomalies: List[dict]          # detected anomalies

    # Output
    priority_lists: dict           # rep_id -> ordered lead list
    briefs: dict                   # rep_id -> brief text
    alerts_to_send: List[dict]     # alerts queue
    errors: List[str]              # any errors during processing
```

### Graph Definition
```python
graph = StateGraph(DailyPipelineState)

graph.add_node("fetch_crm_data", fetch_crm_data)
graph.add_node("score_leads", score_leads)
graph.add_node("rank_priority", rank_priority)
graph.add_node("detect_stale", detect_stale_leads)
graph.add_node("detect_anomalies", detect_anomalies)
graph.add_node("generate_briefs", generate_briefs)
graph.add_node("save_results", save_results)
graph.add_node("send_alerts", send_alerts)

graph.add_edge("fetch_crm_data", "score_leads")
graph.add_edge("score_leads", "rank_priority")
graph.add_edge("rank_priority", "detect_stale")
graph.add_edge("detect_stale", "detect_anomalies")
graph.add_edge("detect_anomalies", "generate_briefs")
graph.add_edge("generate_briefs", "save_results")
graph.add_edge("save_results", "send_alerts")

graph.set_entry_point("fetch_crm_data")
daily_pipeline = graph.compile()
```

### Node 1: Fetch CRM Data (No AI)
```python
async def fetch_crm_data(state: DailyPipelineState) -> dict:
    """Pull all open leads + notes + activities from Supabase (already synced from Zoho)."""
    leads = await supabase.table("leads").select("*").not_("stage", "in", "(won,lost)").execute()
    notes = await supabase.table("lead_notes").select("*").execute()
    activities = await supabase.table("lead_activities").select("*").execute()
    reps = await supabase.table("users").select("*").eq("role", "rep").eq("is_active", True).execute()

    # Group notes and activities by lead_id
    notes_by_lead = group_by(notes.data, "lead_id")
    activities_by_lead = group_by(activities.data, "lead_id")

    return {
        "leads": leads.data,
        "notes": notes_by_lead,
        "activities": activities_by_lead,
        "reps": reps.data,
    }
```

### Node 2: Score Leads (AI — Haiku, Batched)
```python
SCORING_PROMPT = """You are a sales lead scoring AI for a construction SaaS company.

Score each lead as HOT, WARM, or COLD with a numeric score (0-100) and a brief reason.

Scoring criteria:
- HOT (70-100): Recent engagement (call/demo in last 7 days), asked for pricing, high deal value, decision maker involved
- WARM (40-69): Some engagement, showed interest, but no recent activity or no pricing discussion
- COLD (0-39): No engagement in 14+ days, low deal value, no decision maker contact, wrong fit

For each lead, consider:
1. Days since last activity
2. Number of touchpoints
3. Deal value
4. Stage progression (are they moving forward?)
5. Notes content (objections, interest signals)
6. Source quality (referrals > website > cold calls typically)

Return JSON array:
[{{"lead_id": "...", "score": "hot|warm|cold", "score_numeric": 0-100, "reason": "brief explanation"}}]

LEADS DATA:
{leads_batch}
"""

async def score_leads(state: DailyPipelineState) -> dict:
    """Score leads in batches of 20 using Haiku (cost optimization)."""
    scored = []
    leads_with_context = enrich_leads_with_notes_and_activities(
        state["leads"], state["notes"], state["activities"]
    )

    # Only score leads with new activity since last score
    leads_to_score = filter_changed_since_last_score(leads_with_context)

    # Batch: 20 leads per API call
    for batch in chunk(leads_to_score, 20):
        prompt = SCORING_PROMPT.format(leads_batch=json.dumps(batch, default=str))
        response = await tracked_llm_call(
            llm_haiku, prompt, agent_type="daily_pipeline"
        )
        batch_scores = parse_json_response(response.content)
        scored.extend(batch_scores)

    # Keep existing scores for unchanged leads
    unchanged_scores = get_existing_scores_for_unchanged(state["leads"], leads_to_score)
    scored.extend(unchanged_scores)

    return {"scored_leads": scored}
```

### Node 3: Rank Priority (AI — Haiku)
```python
async def rank_priority(state: DailyPipelineState) -> dict:
    """Create ordered call list per rep. Hot leads first, then by recency."""
    priority_lists = {}
    for rep in state["reps"]:
        rep_leads = [l for l in state["scored_leads"] if l["assigned_rep_id"] == rep["id"]]
        # Sort: hot first, then by score_numeric desc, then by days_since_activity asc
        sorted_leads = sorted(rep_leads, key=lambda x: (
            -{"hot": 3, "warm": 2, "cold": 1}.get(x["score"], 0),
            -x.get("score_numeric", 0),
        ))
        priority_lists[rep["id"]] = [
            {"lead_id": l["lead_id"], "rank": i+1, "reason": l["reason"]}
            for i, l in enumerate(sorted_leads)
        ]
    return {"priority_lists": priority_lists}
```

### Node 4: Detect Stale Leads (No AI — Pure Logic)
```python
async def detect_stale_leads(state: DailyPipelineState) -> dict:
    """Find leads with no activity in 7+ days. Flag severity."""
    stale = []
    for lead in state["leads"]:
        if lead["stage"] in ("won", "lost"):
            continue
        days_inactive = (datetime.now() - parse_dt(lead["last_activity_at"])).days
        if days_inactive >= 7:
            severity = "critical" if days_inactive >= 14 else "warning"
            stale.append({
                "lead_id": lead["id"],
                "days_inactive": days_inactive,
                "severity": severity,
                "assigned_rep_id": lead["assigned_rep_id"],
            })
    return {"stale_leads": stale}
```

### Node 5: Detect Anomalies (AI — Haiku)
```python
async def detect_anomalies(state: DailyPipelineState) -> dict:
    """Compare this week vs last week. Flag drops in activity or pipeline changes."""
    # Fetch last week's metrics from Supabase
    this_week = calculate_weekly_metrics(state)
    last_week = await get_last_week_metrics()

    if not last_week:
        return {"anomalies": []}

    prompt = f"""Compare these two weeks of sales data and identify anomalies:

    THIS WEEK: {json.dumps(this_week)}
    LAST WEEK: {json.dumps(last_week)}

    Flag: activity drops >20%, pipeline value changes >30%, any rep with zero calls.
    Return JSON: [{{"type": "...", "description": "...", "severity": "high|medium|low", "rep_id": "..."}}]
    """
    response = await tracked_llm_call(llm_haiku, prompt, agent_type="daily_pipeline")
    return {"anomalies": parse_json_response(response.content)}
```

### Node 6: Generate Briefs (AI — Sonnet)
```python
BRIEF_PROMPT = """Generate a morning brief for sales rep {rep_name}.

Today's date: {date}
Their priority call list (ranked):
{priority_list}

Stale leads needing attention:
{stale_leads}

Write a concise, actionable morning brief. Format:
- Greeting
- Top 3 leads to call RIGHT NOW with specific reasons
- Any stale leads that need urgent attention
- One motivational line

Keep it under 300 words. This will be sent via WhatsApp so keep it clean and scannable.
"""

async def generate_briefs(state: DailyPipelineState) -> dict:
    """Generate personalized morning brief for each rep."""
    briefs = {}
    for rep in state["reps"]:
        rep_priorities = state["priority_lists"].get(rep["id"], [])
        rep_stale = [s for s in state["stale_leads"] if s["assigned_rep_id"] == rep["id"]]

        prompt = BRIEF_PROMPT.format(
            rep_name=rep["name"],
            date=datetime.now().strftime("%B %d, %Y"),
            priority_list=json.dumps(rep_priorities[:10]),
            stale_leads=json.dumps(rep_stale),
        )
        response = await tracked_llm_call(llm_sonnet, prompt, agent_type="daily_pipeline")
        briefs[rep["id"]] = response.content

    return {"briefs": briefs}
```

### Nodes 7-8: Save & Send (No AI)
```python
async def save_results(state: DailyPipelineState) -> dict:
    """Save all scores, rankings, briefs to Supabase."""
    # Upsert scores
    for score in state["scored_leads"]:
        await supabase.table("lead_scores").upsert(score).execute()

    # Save briefs
    for rep_id, brief in state["briefs"].items():
        await supabase.table("daily_briefs").upsert({
            "rep_id": rep_id,
            "brief_content": brief,
            "priority_list": state["priority_lists"].get(rep_id, []),
            "brief_date": date.today().isoformat(),
        }).execute()

    return state

async def send_alerts(state: DailyPipelineState) -> dict:
    """Send morning briefs via WhatsApp + Email."""
    alerts = []
    for rep in state["reps"]:
        brief = state["briefs"].get(rep["id"])
        if not brief:
            continue

        # WhatsApp
        if rep.get("whatsapp_opted_in") and rep.get("phone"):
            try:
                await send_whatsapp(rep["phone"], brief)
                alerts.append({"type": "morning_brief", "channel": "whatsapp", "target_user_id": rep["id"], "delivered": True})
            except Exception as e:
                log.error(f"WhatsApp failed for {rep['name']}: {e}")
                alerts.append({"type": "morning_brief", "channel": "whatsapp", "target_user_id": rep["id"], "delivered": False, "delivery_error": str(e)})

        # Email
        try:
            await send_email(rep["email"], f"Morning Brief - {date.today()}", brief)
            alerts.append({"type": "morning_brief", "channel": "email", "target_user_id": rep["id"], "delivered": True})
        except Exception as e:
            log.error(f"Email failed for {rep['name']}: {e}")

    # Save all alerts to DB
    for alert in alerts:
        await supabase.table("alerts").insert(alert).execute()

    # Send stale lead alerts
    for stale in state["stale_leads"]:
        if stale["severity"] == "critical":
            # Escalate to manager
            rep = next(r for r in state["reps"] if r["id"] == stale["assigned_rep_id"])
            await send_whatsapp(rep["phone"], f"URGENT: Lead inactive {stale['days_inactive']} days. Call today.")
            if rep.get("team_lead_id"):
                manager = await get_user(rep["team_lead_id"])
                await send_email(manager["email"], "Escalation: Stale leads", f"...")

    return {"alerts_to_send": alerts}
```

---

## 3. Agent 2: Research Agent (On-Demand)

### State Definition
```python
class ResearchState(TypedDict):
    lead_id: str
    requested_by: str              # user_id who clicked "Research"

    # Gathered data
    lead_data: dict
    crm_notes: List[dict]
    crm_activities: List[dict]
    web_research: dict

    # AI outputs
    notes_summary: str
    pain_points: List[str]
    objections: List[str]
    company_info: dict
    close_strategy: str
    talking_points: List[str]
    similar_deals: List[dict]
    pricing_suggestion: str

    # Meta
    errors: List[str]
    total_cost: float
```

### Graph (with parallel nodes where possible)
```python
graph = StateGraph(ResearchState)

graph.add_node("gather_crm_context", gather_crm_context)
graph.add_node("web_research", web_research)
graph.add_node("analyze_notes", analyze_notes)
graph.add_node("match_past_wins", match_past_wins)
graph.add_node("generate_close_strategy", generate_close_strategy)
graph.add_node("save_and_display", save_and_display)

# Parallel: web_research + analyze_notes can run simultaneously
graph.add_edge("gather_crm_context", "web_research")
graph.add_edge("gather_crm_context", "analyze_notes")
graph.add_edge("web_research", "match_past_wins")
graph.add_edge("analyze_notes", "match_past_wins")
graph.add_edge("match_past_wins", "generate_close_strategy")
graph.add_edge("generate_close_strategy", "save_and_display")

graph.set_entry_point("gather_crm_context")
research_agent = graph.compile()
```

### Node 4: Match Past Wins (pgvector)
```python
async def match_past_wins(state: ResearchState) -> dict:
    """Find similar WON deals using vector similarity.

    Similarity is based on:
    - Industry (same or adjacent)
    - Deal value range (within 2x)
    - Geography (same city/region)
    - Source (same lead source)
    - Company size (if available)

    Uses pgvector cosine similarity on lead embeddings.
    """
    lead = state["lead_data"]

    # Generate embedding for this lead's profile
    lead_text = f"""
    Industry: {lead.get('industry', 'unknown')}
    Deal value: {lead.get('deal_value', 0)}
    Source: {lead.get('source', 'unknown')}
    Geography: {lead.get('geography', 'unknown')}
    Company: {lead.get('company', '')}
    """
    embedding = await generate_embedding(lead_text)  # OpenAI ada-002

    # Find top 5 similar WON deals via pgvector
    similar = await supabase.rpc("match_similar_deals", {
        "query_embedding": embedding,
        "match_threshold": 0.7,
        "match_count": 5,
    }).execute()

    return {"similar_deals": similar.data}
```

#### Supabase function for vector search:
```sql
CREATE OR REPLACE FUNCTION match_similar_deals(
  query_embedding vector(1536),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  lead_id UUID,
  company TEXT,
  deal_value NUMERIC,
  source TEXT,
  industry TEXT,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    l.id AS lead_id,
    l.company,
    l.deal_value,
    l.source,
    l.industry,
    1 - (le.embedding <=> query_embedding) AS similarity
  FROM lead_embeddings le
  JOIN leads l ON l.id = le.lead_id
  WHERE l.stage = 'won'
  AND 1 - (le.embedding <=> query_embedding) > match_threshold
  ORDER BY le.embedding <=> query_embedding
  LIMIT match_count;
$$;
```

### Node 5: Generate Close Strategy (AI — Sonnet)
```python
CLOSE_STRATEGY_PROMPT = """You are a senior sales strategist for a construction SaaS company.

Based on all the research below, generate a clear close strategy for this deal.

LEAD: {lead_data}
COMPANY RESEARCH: {web_research}
ALL NOTES SUMMARY: {notes_summary}
PAIN POINTS IDENTIFIED: {pain_points}
OBJECTIONS RAISED: {objections}
SIMILAR DEALS THAT WON: {similar_deals}

Generate:
1. **Recommended approach** (2-3 sentences): How to close this deal
2. **Talking points** (3-5 bullets): What to say on the next call
3. **Objection handling** (for each objection identified): Prepared responses
4. **Pricing suggestion**: Based on deal value and similar won deals
5. **Suggested next step**: One specific action for the rep
6. **Risk factors**: What could kill this deal

Return as structured JSON.
"""
```

### Response Time Target: 15-30 seconds
The research agent runs async. Dashboard shows loading spinner, then the intel card appears via WebSocket update.

---

## 4. Agent 3: Smart Assignment (Webhook-Triggered)

```python
class AssignmentState(TypedDict):
    new_lead: dict
    all_reps: List[dict]
    rep_workloads: dict            # rep_id -> current lead count
    rep_track_records: dict        # rep_id -> {industry_wins, avg_deal_size, conversion_rate}
    assigned_rep: dict
    assignment_reason: str

ASSIGNMENT_PROMPT = """A new lead just came in. Assign it to the best sales rep.

NEW LEAD:
- Company: {company}
- Industry: {industry}
- Deal value: Rs {deal_value}
- Source: {source}
- Geography: {geography}

AVAILABLE REPS:
{reps_with_stats}

Rules:
1. Rep must have capacity (< 30 active leads)
2. Prefer reps with highest conversion rate in similar industry
3. Prefer reps in same geography if possible
4. If all equal, round-robin to rep with fewest leads

Return JSON: {{"rep_id": "...", "reason": "..."}}
"""
```

---

## 5. Agent 4: Weekly Report (Monday 8 AM)

Generates comprehensive weekly intelligence report for founder + managers.

### Sections Generated:
1. Pipeline summary (total leads, new, converted, lost)
2. Per-rep scorecard (calls, conversion, deals, revenue)
3. Source analysis (which sources convert best)
4. AI insights (patterns, anomalies, recommendations)
5. Revenue forecast (based on pipeline health)
6. Week-over-week trends

---

## 6. Error Handling Matrix

| Failure | Impact | Handling |
|---------|--------|----------|
| Claude API down at 7:30 AM | No morning briefs | Auto-fallback to GPT-4o. If both down: send last cached brief with "Scores from yesterday" note. |
| Supabase down | Nothing works | Retry 3x. If down: send error alert to admin. Dashboard shows "Service temporarily unavailable." |
| WhatsApp API down | No morning alerts | Fallback to email-only. Log delivery failure. Retry failed sends every 30 min for 2 hours. |
| Zoho sync fails | Stale CRM data | Dashboard shows "Last synced: X hours ago" warning. Agent uses cached data. |
| Research agent timeout | Rep waiting >30s | Show partial results if any nodes completed. "Research partially complete" message. |
| Single lead scoring fails | One lead unscored | Log error, continue scoring rest. Show "Score pending" on dashboard for that lead. |
| LangSmith down | No tracing | Non-blocking. Agent runs normally, just without trace logging. |

---

## 7. Prompt Testing Checklist

Before launch, test each prompt with REAL Zoho data:

- [ ] Scoring prompt: Test with 20 real leads. Do scores make sense?
- [ ] Brief prompt: Is the WhatsApp brief readable? Under 300 words?
- [ ] Research prompt: Does the close strategy feel actionable?
- [ ] Assignment prompt: Does it pick sensible reps?
- [ ] Weekly report: Are the insights useful or generic?
- [ ] Edge case: Lead with zero notes. Does scoring still work?
- [ ] Edge case: Lead with 50+ notes. Does it handle token limits?
- [ ] Edge case: New rep with no history. Does assignment work?

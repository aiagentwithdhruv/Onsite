"""Research Agent — deep-dives into a single lead on demand.

Called when a rep or manager requests research on a specific lead.
Gathers CRM data, performs web research, analyzes notes, matches past wins,
and generates a close strategy with talking points.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from app.core.llm import tracked_llm_call, get_llm
from app.core.supabase_client import get_supabase_admin

log = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class ResearchState(TypedDict):
    lead_id: str
    requested_by: str
    lead_data: dict
    crm_notes: list
    crm_activities: list
    web_research: str
    notes_summary: str
    pain_points: list
    objections: list
    company_info: dict
    close_strategy: str
    talking_points: list
    similar_deals: list
    errors: list


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

async def gather_context(state: ResearchState) -> ResearchState:
    """Pull all data for this lead from Supabase: lead record, notes, activities."""
    errors = list(state.get("errors", []))
    lead_id = state["lead_id"]

    try:
        db = get_supabase_admin()

        # Get lead record
        lead_resp = (
            db.table("leads")
            .select("*")
            .eq("id", lead_id)
            .single()
            .execute()
        )
        lead_data = lead_resp.data or {}

        if not lead_data:
            errors.append(f"Lead {lead_id} not found in database")
            return {**state, "lead_data": {}, "crm_notes": [], "crm_activities": [], "errors": errors}

        # Get all notes for this lead
        notes_resp = (
            db.table("lead_notes")
            .select("*")
            .eq("lead_id", lead_id)
            .order("created_at", desc=True)
            .execute()
        )
        crm_notes = notes_resp.data or []

        # Get all activities for this lead
        activities_resp = (
            db.table("lead_activities")
            .select("*")
            .eq("lead_id", lead_id)
            .order("created_at", desc=True)
            .execute()
        )
        crm_activities = activities_resp.data or []

        log.info(
            f"[ResearchAgent] Gathered context for {lead_data.get('company_name', lead_id)}: "
            f"{len(crm_notes)} notes, {len(crm_activities)} activities"
        )

        return {
            **state,
            "lead_data": lead_data,
            "crm_notes": crm_notes,
            "crm_activities": crm_activities,
        }

    except Exception as e:
        log.error(f"[ResearchAgent] gather_context failed: {e}")
        errors.append(f"gather_context: {str(e)}")
        return {**state, "lead_data": {}, "crm_notes": [], "crm_activities": [], "errors": errors}


async def web_research(state: ResearchState) -> ResearchState:
    """Use Claude to research the company on the web."""
    errors = list(state.get("errors", []))
    lead_data = state.get("lead_data", {})

    if not lead_data:
        return {**state, "web_research": "", "company_info": {}, "errors": errors}

    company_name = lead_data.get("company_name", "")
    contact_name = lead_data.get("contact_name", "")
    region = lead_data.get("region", "")
    industry = lead_data.get("industry", "construction")

    search_context = (
        f"Company: {company_name}\n"
        f"Contact: {contact_name}\n"
        f"Region: {region}\n"
        f"Industry: {industry}\n"
        f"Website: {lead_data.get('website', 'Unknown')}\n"
    )

    messages = [
        SystemMessage(content=(
            "You are a sales research analyst for Onsite Teams, a construction SaaS company "
            "in India that sells project management and workforce tools to builders, "
            "contractors, and real estate developers.\n\n"
            "Research the following company/contact. Provide:\n"
            "1. COMPANY OVERVIEW: What they do, size, key projects, reputation\n"
            "2. RECENT NEWS: Any recent projects, awards, expansions, hiring\n"
            "3. TECH ADOPTION: Do they use any software/tech tools? Digital maturity?\n"
            "4. DECISION-MAKER PROFILE: Contact's role, background, likely priorities\n"
            "5. CONSTRUCTION-SPECIFIC CONTEXT: Type of projects (residential/commercial/infra), "
            "scale, typical pain points for their segment\n"
            "6. COMPETITIVE LANDSCAPE: Are they likely using any competitors (PlanGrid, "
            "Procore, Buildertrend, or Indian alternatives)?\n\n"
            "Also return a structured JSON block at the end with key facts:\n"
            '```json\n{"company_size": "...", "project_types": [...], '
            '"estimated_revenue": "...", "tech_maturity": "low|medium|high", '
            '"key_projects": [...], "competitors_used": [...], '
            '"decision_maker_title": "...", "pain_indicators": [...]}\n```\n\n'
            "If you cannot find reliable info, say so. Do NOT fabricate data. "
            "Base your research on what a well-informed sales analyst would know "
            "about this type of company in the Indian construction market."
        )),
        HumanMessage(content=f"Research this lead:\n{search_context}"),
    ]

    try:
        response = await tracked_llm_call(
            "research",
            messages,
            lead_id=state["lead_id"],
            user_id=state.get("requested_by"),
        )
        research_text = response.content.strip()

        # Try to extract structured company_info from JSON block
        company_info = {}
        if "```json" in research_text:
            try:
                json_block = research_text.split("```json")[1].split("```")[0].strip()
                company_info = json.loads(json_block)
            except (json.JSONDecodeError, IndexError):
                log.warning("[ResearchAgent] Could not parse company_info JSON from research")

        log.info(f"[ResearchAgent] Web research complete for {company_name}")

        return {**state, "web_research": research_text, "company_info": company_info}

    except Exception as e:
        log.error(f"[ResearchAgent] web_research failed: {e}")
        errors.append(f"web_research: {str(e)}")
        return {**state, "web_research": "", "company_info": {}, "errors": errors}


async def analyze_notes(state: ResearchState) -> ResearchState:
    """Read ALL notes + call summaries. Extract pain points, objections, signals."""
    errors = list(state.get("errors", []))
    crm_notes = state.get("crm_notes", [])
    crm_activities = state.get("crm_activities", [])
    lead_data = state.get("lead_data", {})

    if not crm_notes and not crm_activities:
        return {
            **state,
            "notes_summary": "No CRM notes or activities found for this lead.",
            "pain_points": [],
            "objections": [],
        }

    # Build full CRM history
    notes_text = "CRM NOTES (newest first):\n"
    for note in crm_notes:
        notes_text += (
            f"[{note.get('created_at', '?')[:10]}] "
            f"By: {note.get('created_by_name', 'Unknown')} | "
            f"Type: {note.get('note_source', 'general')}\n"
            f"{note.get('note_text', '(empty)')}\n\n"
        )

    activities_text = "ACTIVITIES (newest first):\n"
    for act in crm_activities:
        activities_text += (
            f"[{act.get('created_at', '?')[:10]}] "
            f"{act.get('activity_type', '?')}: "
            f"{act.get('details', '(no description)')}\n"
            f"Outcome: {act.get('outcome', 'N/A')}\n\n"
        )

    full_context = (
        f"LEAD: {lead_data.get('company_name', 'Unknown')} "
        f"({lead_data.get('contact_name', 'Unknown')})\n"
        f"Status: {lead_data.get('status', '?')} | "
        f"Deal Value: Rs {lead_data.get('deal_value', 0):,.0f}\n\n"
        f"{notes_text}\n{activities_text}"
    )

    messages = [
        SystemMessage(content=(
            "You are a CRM analyst for a construction SaaS company (Onsite Teams). "
            "Analyze the complete CRM history for this lead and extract:\n\n"
            "1. NOTES SUMMARY: A concise timeline of the relationship (key interactions, "
            "who spoke to whom, what was discussed)\n"
            "2. PAIN POINTS: Specific problems the prospect mentioned or implied. "
            "In construction SaaS, common ones include:\n"
            "   - Tracking worker attendance across sites\n"
            "   - Project delay visibility\n"
            "   - Material wastage / procurement chaos\n"
            "   - Subcontractor coordination\n"
            "   - Cash flow / billing delays\n"
            "   - Safety compliance tracking\n"
            "   - Scaling from X to Y projects\n"
            "3. OBJECTIONS: Anything the prospect pushed back on:\n"
            "   - Price too high\n"
            "   - Workers won't adopt tech\n"
            "   - Already using Excel/WhatsApp\n"
            "   - Need to check with partner/boss\n"
            "   - Not the right time\n"
            "   - Want features we don't have\n"
            "4. INTEREST SIGNALS: Positive buying signals detected\n\n"
            "Return as JSON:\n"
            '{"notes_summary": "...", "pain_points": ["..."], '
            '"objections": ["..."], "interest_signals": ["..."]}\n\n'
            "ONLY valid JSON, no markdown wrapping."
        )),
        HumanMessage(content=full_context),
    ]

    try:
        response = await tracked_llm_call(
            "research",
            messages,
            lead_id=state["lead_id"],
            user_id=state.get("requested_by"),
        )
        raw_text = response.content.strip()

        # Clean up potential markdown wrapping
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

        analysis = json.loads(raw_text)

        log.info(
            f"[ResearchAgent] Note analysis complete: "
            f"{len(analysis.get('pain_points', []))} pain points, "
            f"{len(analysis.get('objections', []))} objections"
        )

        return {
            **state,
            "notes_summary": analysis.get("notes_summary", ""),
            "pain_points": analysis.get("pain_points", []),
            "objections": analysis.get("objections", []),
        }

    except Exception as e:
        log.error(f"[ResearchAgent] analyze_notes failed: {e}")
        errors.append(f"analyze_notes: {str(e)}")
        return {
            **state,
            "notes_summary": "Analysis failed — review notes manually.",
            "pain_points": [],
            "objections": [],
            "errors": errors,
        }


async def match_past_wins(state: ResearchState) -> ResearchState:
    """Query Supabase for won deals in same industry/geography/deal range.
    Simple SQL query for now — vector search comes later."""
    errors = list(state.get("errors", []))
    lead_data = state.get("lead_data", {})
    similar_deals = []

    if not lead_data:
        return {**state, "similar_deals": [], "errors": errors}

    try:
        db = get_supabase_admin()

        industry = lead_data.get("industry", "")
        region = lead_data.get("region", "")
        deal_value = lead_data.get("deal_value", 0)

        # Define deal value range (50% to 200% of current deal)
        min_value = deal_value * 0.5 if deal_value else 0
        max_value = deal_value * 2.0 if deal_value else 999999999

        # Query won deals with matching criteria
        # Try industry + region match first
        query = (
            db.table("leads")
            .select("id, company_name, contact_name, industry, region, deal_value, "
                    "status, closed_at, assigned_rep_id, score_reasoning")
            .eq("status", "won")
        )

        if industry:
            query = query.eq("industry", industry)

        won_resp = query.execute()
        won_deals = won_resp.data or []

        # Score similarity (simple heuristic)
        for deal in won_deals:
            similarity_score = 0
            reasons = []

            # Industry match
            if deal.get("industry") == industry and industry:
                similarity_score += 40
                reasons.append("Same industry")

            # Region match
            if deal.get("region") == region and region:
                similarity_score += 30
                reasons.append("Same region")

            # Deal value range
            d_value = deal.get("deal_value", 0) or 0
            if min_value <= d_value <= max_value:
                similarity_score += 20
                reasons.append("Similar deal size")

            # Only include if at least somewhat similar
            if similarity_score >= 30:
                similar_deals.append({
                    "deal_id": deal["id"],
                    "company_name": deal.get("company_name", "Unknown"),
                    "deal_value": d_value,
                    "region": deal.get("region", ""),
                    "industry": deal.get("industry", ""),
                    "similarity_score": similarity_score,
                    "match_reasons": reasons,
                    "closed_at": deal.get("closed_at"),
                })

        # Sort by similarity score
        similar_deals.sort(key=lambda d: -d["similarity_score"])
        similar_deals = similar_deals[:5]  # Top 5

        # Get notes from the best matching won deals for context
        if similar_deals:
            top_deal_ids = [d["deal_id"] for d in similar_deals[:3]]
            deal_notes_resp = (
                db.table("lead_notes")
                .select("lead_id, note_text, note_source")
                .in_("lead_id", top_deal_ids)
                .in_("note_source", ["closing_note", "call_summary", "general", "zoho", "csv_import"])
                .order("note_date", desc=True)
                .limit(10)
                .execute()
            )
            deal_notes = deal_notes_resp.data or []

            # Attach notes to deals
            notes_by_deal: dict[str, list] = {}
            for n in deal_notes:
                notes_by_deal.setdefault(n["lead_id"], []).append(n.get("note_text", ""))

            for deal in similar_deals:
                deal["winning_notes"] = notes_by_deal.get(deal["deal_id"], [])[:3]

        log.info(f"[ResearchAgent] Found {len(similar_deals)} similar won deals")

        return {**state, "similar_deals": similar_deals, "errors": errors}

    except Exception as e:
        log.error(f"[ResearchAgent] match_past_wins failed: {e}")
        errors.append(f"match_past_wins: {str(e)}")
        return {**state, "similar_deals": [], "errors": errors}


async def generate_strategy(state: ResearchState) -> ResearchState:
    """Generate close strategy with talking points, objection handling, pricing."""
    errors = list(state.get("errors", []))
    lead_data = state.get("lead_data", {})

    if not lead_data:
        return {
            **state,
            "close_strategy": "No lead data available for strategy generation.",
            "talking_points": [],
            "errors": errors,
        }

    # Build comprehensive context
    company_name = lead_data.get("company_name", "Unknown")
    contact_name = lead_data.get("contact_name", "Unknown")

    # Similar deals context
    similar_deals_text = ""
    for deal in state.get("similar_deals", []):
        similar_deals_text += (
            f"- {deal['company_name']} (Rs {deal.get('deal_value', 0):,.0f}) "
            f"— {', '.join(deal.get('match_reasons', []))}\n"
        )
        for note in deal.get("winning_notes", []):
            similar_deals_text += f"  Winning note: {note[:150]}\n"
    if not similar_deals_text:
        similar_deals_text = "(No similar won deals found)"

    full_context = (
        f"LEAD: {company_name}\n"
        f"Contact: {contact_name} ({lead_data.get('contact_title', 'Unknown title')})\n"
        f"Status: {lead_data.get('status', '?')}\n"
        f"Deal Value: Rs {lead_data.get('deal_value', 0):,.0f}\n"
        f"Region: {lead_data.get('region', '?')}\n"
        f"Industry: {lead_data.get('industry', '?')}\n"
        f"Source: {lead_data.get('source', '?')}\n\n"
        f"WEB RESEARCH:\n{state.get('web_research', '(none)')[:1500]}\n\n"
        f"COMPANY INFO:\n{json.dumps(state.get('company_info', {}), indent=2)[:500]}\n\n"
        f"NOTES SUMMARY:\n{state.get('notes_summary', '(none)')}\n\n"
        f"PAIN POINTS:\n{chr(10).join('- ' + p for p in state.get('pain_points', [])) or '(none detected)'}\n\n"
        f"OBJECTIONS:\n{chr(10).join('- ' + o for o in state.get('objections', [])) or '(none detected)'}\n\n"
        f"SIMILAR WON DEALS:\n{similar_deals_text}"
    )

    messages = [
        SystemMessage(content=(
            "You are a senior sales strategist for Onsite Teams, a construction SaaS company "
            "in India. You help sales reps close deals with builders, contractors, and "
            "real estate developers.\n\n"
            "Based on the comprehensive research below, generate:\n\n"
            "1. CLOSE STRATEGY (2-3 paragraphs):\n"
            "   - Recommended approach (consultative/demo-driven/urgency/reference)\n"
            "   - Key value proposition tailored to their specific pain points\n"
            "   - Timeline suggestion (when to push for close)\n"
            "   - Who else to involve (their team, our team)\n\n"
            "2. TALKING POINTS (5-7 bullet points):\n"
            "   - Opening line for the next call\n"
            "   - Key pain point to address first\n"
            "   - Reference to similar companies using Onsite (from won deals)\n"
            "   - Feature demo to focus on\n"
            "   - ROI argument specific to their scale\n"
            "   - Urgency trigger if applicable\n"
            "   - Closing question\n\n"
            "3. OBJECTION HANDLING:\n"
            "   For each detected objection, provide a specific counter with "
            "   construction-industry context.\n\n"
            "4. PRICING SUGGESTION:\n"
            "   Based on deal size, company type, and similar won deals, suggest:\n"
            "   - Recommended plan/tier\n"
            "   - Whether to offer a pilot/trial\n"
            "   - Any discounts (if justified)\n"
            "   - Payment structure suggestion\n\n"
            "Return as JSON:\n"
            '{"close_strategy": "...", "talking_points": ["..."], '
            '"objection_handling": [{"objection": "...", "counter": "..."}], '
            '"pricing_suggestion": {"plan": "...", "trial": "...", "discount": "...", '
            '"payment_structure": "..."}}\n\n'
            "Be specific, actionable, and practical. No generic advice. "
            "Everything should be tailored to THIS specific lead."
        )),
        HumanMessage(content=full_context),
    ]

    try:
        response = await tracked_llm_call(
            "research",
            messages,
            lead_id=state["lead_id"],
            user_id=state.get("requested_by"),
        )
        raw_text = response.content.strip()

        # Clean up potential markdown wrapping
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

        strategy_data = json.loads(raw_text)

        close_strategy = strategy_data.get("close_strategy", "")
        talking_points = strategy_data.get("talking_points", [])

        # Append objection handling and pricing to the strategy text
        objection_handling = strategy_data.get("objection_handling", [])
        pricing_suggestion = strategy_data.get("pricing_suggestion", {})

        # Build full strategy text for storage
        full_strategy = close_strategy + "\n\n"

        if objection_handling:
            full_strategy += "OBJECTION HANDLING:\n"
            for oh in objection_handling:
                full_strategy += (
                    f"  Objection: {oh.get('objection', '')}\n"
                    f"  Counter: {oh.get('counter', '')}\n\n"
                )

        if pricing_suggestion:
            full_strategy += "PRICING SUGGESTION:\n"
            full_strategy += f"  Plan: {pricing_suggestion.get('plan', 'N/A')}\n"
            full_strategy += f"  Trial: {pricing_suggestion.get('trial', 'N/A')}\n"
            full_strategy += f"  Discount: {pricing_suggestion.get('discount', 'N/A')}\n"
            full_strategy += f"  Payment: {pricing_suggestion.get('payment_structure', 'N/A')}\n"

        log.info(
            f"[ResearchAgent] Strategy generated for {company_name}: "
            f"{len(talking_points)} talking points"
        )

        return {
            **state,
            "close_strategy": full_strategy,
            "talking_points": talking_points,
        }

    except Exception as e:
        log.error(f"[ResearchAgent] generate_strategy failed: {e}")
        errors.append(f"generate_strategy: {str(e)}")
        return {
            **state,
            "close_strategy": "Strategy generation failed. Review research data manually.",
            "talking_points": [],
            "errors": errors,
        }


async def save_research(state: ResearchState) -> ResearchState:
    """Save complete research results to lead_research table in Supabase."""
    errors = list(state.get("errors", []))
    lead_id = state["lead_id"]
    now_iso = datetime.now(IST).isoformat()

    try:
        db = get_supabase_admin()

        research_record = {
            "lead_id": lead_id,
            "requested_by": state.get("requested_by"),
            "web_research": state.get("web_research", ""),
            "company_info": state.get("company_info", {}),
            "notes_summary": state.get("notes_summary", ""),
            "pain_points": state.get("pain_points", []),
            "objections": state.get("objections", []),
            "close_strategy": state.get("close_strategy", ""),
            "talking_points": state.get("talking_points", []),
            "similar_deals": [
                {
                    "company_name": d.get("company_name"),
                    "deal_value": d.get("deal_value"),
                    "similarity_score": d.get("similarity_score"),
                    "match_reasons": d.get("match_reasons"),
                }
                for d in state.get("similar_deals", [])
            ],
            "errors": errors,
            "researched_at": now_iso,
        }

        # Upsert — if research already exists for this lead, update it
        db.table("lead_research").upsert(
            research_record, on_conflict="lead_id"
        ).execute()

        # Also update the lead record to mark that research is available
        db.table("leads").update({
            "has_research": True,
            "last_researched_at": now_iso,
        }).eq("id", lead_id).execute()

        log.info(f"[ResearchAgent] Saved research for lead {lead_id}")

    except Exception as e:
        log.error(f"[ResearchAgent] save_research failed: {e}")
        errors.append(f"save_research: {str(e)}")

    return {**state, "errors": errors}


# ---------------------------------------------------------------------------
# Graph Construction
# ---------------------------------------------------------------------------

def build_research_graph() -> StateGraph:
    """Build the LangGraph StateGraph for the research agent.

    Flow: gather_context -> (web_research + analyze_notes in parallel) ->
          match_past_wins -> generate_strategy -> save_research
    """
    graph = StateGraph(ResearchState)

    # Add nodes
    graph.add_node("gather_context", gather_context)
    graph.add_node("web_research", web_research)
    graph.add_node("analyze_notes", analyze_notes)
    graph.add_node("match_past_wins", match_past_wins)
    graph.add_node("generate_strategy", generate_strategy)
    graph.add_node("save_research", save_research)

    # Set entry point
    graph.set_entry_point("gather_context")

    # After gathering context, run web_research and analyze_notes in parallel
    graph.add_edge("gather_context", "web_research")
    graph.add_edge("gather_context", "analyze_notes")

    # Both parallel branches converge into match_past_wins
    graph.add_edge("web_research", "match_past_wins")
    graph.add_edge("analyze_notes", "match_past_wins")

    # Linear from here
    graph.add_edge("match_past_wins", "generate_strategy")
    graph.add_edge("generate_strategy", "save_research")
    graph.add_edge("save_research", END)

    return graph


# ---------------------------------------------------------------------------
# Public Entry Point
# ---------------------------------------------------------------------------

async def run_research_agent(lead_id: str, user_id: str) -> dict:
    """Compile and run the research agent graph for a specific lead.

    Args:
        lead_id: The UUID of the lead to research.
        user_id: The UUID of the user who requested the research.

    Returns:
        The final state dict with all research results.
    """
    log.info(f"[ResearchAgent] Starting research for lead {lead_id} (requested by {user_id})")
    start_time = datetime.now(IST)

    graph = build_research_graph()
    app = graph.compile()

    initial_state: ResearchState = {
        "lead_id": lead_id,
        "requested_by": user_id,
        "lead_data": {},
        "crm_notes": [],
        "crm_activities": [],
        "web_research": "",
        "notes_summary": "",
        "pain_points": [],
        "objections": [],
        "company_info": {},
        "close_strategy": "",
        "talking_points": [],
        "similar_deals": [],
        "errors": [],
    }

    final_state = await app.ainvoke(initial_state)

    duration = (datetime.now(IST) - start_time).total_seconds()
    log.info(
        f"[ResearchAgent] Completed in {duration:.1f}s for "
        f"{final_state.get('lead_data', {}).get('company_name', lead_id)} — "
        f"{len(final_state.get('talking_points', []))} talking points, "
        f"{len(final_state.get('similar_deals', []))} similar deals, "
        f"{len(final_state.get('errors', []))} errors"
    )

    # Log research run
    try:
        db = get_supabase_admin()
        db.table("pipeline_runs").insert({
            "pipeline_type": "research",
            "started_at": start_time.isoformat(),
            "completed_at": datetime.now(IST).isoformat(),
            "duration_seconds": round(duration, 1),
            "lead_id": lead_id,
            "triggered_by": user_id,
            "errors": final_state.get("errors", []),
            "success": len(final_state.get("errors", [])) == 0,
        }).execute()
    except Exception as e:
        log.warning(f"[ResearchAgent] Failed to log research run: {e}")

    return final_state

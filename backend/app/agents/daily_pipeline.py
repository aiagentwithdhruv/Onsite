"""Daily Pipeline Agent — scores leads, ranks priority, generates briefs.

Runs at 7:30 AM IST every day. Processes all open leads, scores them with AI,
detects stale leads and anomalies, generates per-rep morning briefs, and
delivers them via WhatsApp + Email.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from app.core.llm import tracked_llm_call, get_llm
from app.core.supabase_client import get_supabase_admin
from app.services.whatsapp import send_whatsapp_message
from app.services.email import send_email

log = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class DailyPipelineState(TypedDict):
    leads: list              # raw leads from DB
    notes: dict              # lead_id -> [notes]
    activities: dict         # lead_id -> [activities]
    reps: list               # active reps
    scored_leads: list       # leads with AI scores
    stale_leads: list        # leads with 7+ days no activity
    anomalies: list          # detected anomalies
    priority_lists: dict     # rep_id -> ordered lead list
    briefs: dict             # rep_id -> brief text
    errors: list


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

async def fetch_data(state: DailyPipelineState) -> DailyPipelineState:
    """Pull open leads, notes, activities, and reps from Supabase."""
    errors = list(state.get("errors", []))
    try:
        db = get_supabase_admin()

        # Open leads (not won/lost)
        leads_resp = (
            db.table("leads")
            .select("*")
            .in_("status", ["new", "contacted", "qualified", "proposal", "negotiation"])
            .execute()
        )
        leads = leads_resp.data or []

        lead_ids = [l["id"] for l in leads]

        # Notes for all open leads
        notes_map: dict[str, list] = {}
        if lead_ids:
            notes_resp = (
                db.table("notes")
                .select("*")
                .in_("lead_id", lead_ids)
                .order("created_at", desc=True)
                .execute()
            )
            for note in (notes_resp.data or []):
                notes_map.setdefault(note["lead_id"], []).append(note)

        # Activities for all open leads
        activities_map: dict[str, list] = {}
        if lead_ids:
            activities_resp = (
                db.table("activities")
                .select("*")
                .in_("lead_id", lead_ids)
                .order("created_at", desc=True)
                .execute()
            )
            for act in (activities_resp.data or []):
                activities_map.setdefault(act["lead_id"], []).append(act)

        # Active reps
        reps_resp = (
            db.table("users")
            .select("*")
            .eq("role", "rep")
            .eq("is_active", True)
            .execute()
        )
        reps = reps_resp.data or []

        log.info(f"[DailyPipeline] Fetched {len(leads)} leads, {len(reps)} reps")

        return {
            **state,
            "leads": leads,
            "notes": notes_map,
            "activities": activities_map,
            "reps": reps,
        }

    except Exception as e:
        log.error(f"[DailyPipeline] fetch_data failed: {e}")
        errors.append(f"fetch_data: {str(e)}")
        return {
            **state,
            "leads": [],
            "notes": {},
            "activities": {},
            "reps": [],
            "errors": errors,
        }


async def score_leads(state: DailyPipelineState) -> DailyPipelineState:
    """Batch score leads (20 per batch) using AI. Only re-scores leads with
    new activity since their last score."""
    errors = list(state.get("errors", []))
    leads = state.get("leads", [])
    notes = state.get("notes", {})
    activities = state.get("activities", {})
    scored_leads = []

    if not leads:
        return {**state, "scored_leads": [], "errors": errors}

    # Determine which leads need re-scoring
    leads_to_score = []
    for lead in leads:
        last_scored = lead.get("last_scored_at")
        last_activity = lead.get("last_activity_at")

        # Score if never scored, or if new activity since last score
        if not last_scored or (last_activity and last_activity > last_scored):
            leads_to_score.append(lead)
        else:
            # Keep existing score
            scored_leads.append(lead)

    log.info(
        f"[DailyPipeline] Scoring {len(leads_to_score)} leads "
        f"({len(scored_leads)} already up-to-date)"
    )

    # Process in batches of 20
    batch_size = 20
    for i in range(0, len(leads_to_score), batch_size):
        batch = leads_to_score[i : i + batch_size]

        # Build context for each lead in this batch
        batch_context = []
        for lead in batch:
            lid = lead["id"]
            lead_notes = notes.get(lid, [])
            lead_activities = activities.get(lid, [])

            recent_notes_text = "\n".join(
                f"  - [{n.get('created_at', '?')[:10]}] {n.get('content', '')[:200]}"
                for n in lead_notes[:5]
            ) or "  (no notes)"

            recent_activities_text = "\n".join(
                f"  - [{a.get('created_at', '?')[:10]}] {a.get('activity_type', '?')}: {a.get('description', '')[:150]}"
                for a in lead_activities[:5]
            ) or "  (no activities)"

            batch_context.append(
                f"LEAD #{lid}:\n"
                f"  Company: {lead.get('company_name', 'Unknown')}\n"
                f"  Contact: {lead.get('contact_name', 'Unknown')}\n"
                f"  Status: {lead.get('status', '?')}\n"
                f"  Deal Value: {lead.get('deal_value', 0)}\n"
                f"  Source: {lead.get('source', '?')}\n"
                f"  Region: {lead.get('region', '?')}\n"
                f"  Industry: {lead.get('industry', '?')}\n"
                f"  Created: {lead.get('created_at', '?')[:10] if lead.get('created_at') else '?'}\n"
                f"  Last Activity: {lead.get('last_activity_at', 'Never')}\n"
                f"  Recent Notes:\n{recent_notes_text}\n"
                f"  Recent Activities:\n{recent_activities_text}"
            )

        scoring_prompt = "\n\n---\n\n".join(batch_context)

        messages = [
            SystemMessage(content=(
                "You are a lead-scoring AI for a construction SaaS company (Onsite Teams) "
                "that sells project management and workforce tools to builders, contractors, "
                "and real estate developers in India.\n\n"
                "SCORING CRITERIA:\n"
                "- HOT (80-100): Active engagement in last 3 days, asked for pricing/demo, "
                "decision-maker involved, deal value > 3L, in proposal/negotiation stage, "
                "referral lead, or urgent project timeline mentioned.\n"
                "- WARM (40-79): Responded in last 7 days, showed feature interest, "
                "mid-range deal (1-3L), qualified status, has upcoming project, "
                "contacted multiple times with positive signals.\n"
                "- COLD (0-39): No response in 7+ days, low deal value (<1L), "
                "new lead with no engagement, unclear requirements, "
                "no decision-maker access, or budget concerns raised.\n\n"
                "SIGNALS TO LOOK FOR:\n"
                "- Positive: demo requests, pricing questions, team mentions, "
                "timeline urgency, referral source, site visit scheduled\n"
                "- Negative: 'will get back', budget issues, competitor mentions, "
                "'not now', ghosting pattern, junior contact only\n\n"
                "For EACH lead, return a JSON object with:\n"
                '  {"lead_id": "...", "score_label": "hot|warm|cold", "score_numeric": 0-100, '
                '"reasoning": "1-2 sentence explanation", "next_action": "suggested next step"}\n\n'
                "Return a JSON array of these objects. ONLY valid JSON, no markdown."
            )),
            HumanMessage(content=f"Score these {len(batch)} leads:\n\n{scoring_prompt}"),
        ]

        try:
            response = await tracked_llm_call(
                "scoring", messages, user_id="system_daily_pipeline"
            )
            raw_text = response.content.strip()

            # Clean up potential markdown wrapping
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

            scores = json.loads(raw_text)

            # Merge scores back into lead dicts
            score_by_id = {s["lead_id"]: s for s in scores}
            for lead in batch:
                lid = lead["id"]
                if lid in score_by_id:
                    lead["score_label"] = score_by_id[lid]["score_label"]
                    lead["score_numeric"] = score_by_id[lid]["score_numeric"]
                    lead["score_reasoning"] = score_by_id[lid].get("reasoning", "")
                    lead["score_next_action"] = score_by_id[lid].get("next_action", "")
                else:
                    lead["score_label"] = "cold"
                    lead["score_numeric"] = 20
                    lead["score_reasoning"] = "No AI score returned for this lead."
                    lead["score_next_action"] = "Review manually."
                scored_leads.append(lead)

        except Exception as e:
            log.error(f"[DailyPipeline] Scoring batch failed: {e}")
            errors.append(f"score_leads batch {i // batch_size}: {str(e)}")
            # Assign default cold score to failed batch
            for lead in batch:
                lead["score_label"] = "cold"
                lead["score_numeric"] = 10
                lead["score_reasoning"] = "Scoring failed — manual review needed."
                lead["score_next_action"] = "Review manually."
                scored_leads.append(lead)

    return {**state, "scored_leads": scored_leads, "errors": errors}


async def rank_priority(state: DailyPipelineState) -> DailyPipelineState:
    """Sort scored leads per rep: hot first, then by score_numeric descending."""
    scored_leads = state.get("scored_leads", [])
    reps = state.get("reps", [])

    label_order = {"hot": 0, "warm": 1, "cold": 2}
    priority_lists: dict[str, list] = {}

    for rep in reps:
        rep_id = rep["id"]
        rep_leads = [
            l for l in scored_leads
            if l.get("assigned_rep_id") == rep_id
        ]

        # Sort: hot > warm > cold, then by numeric score descending
        rep_leads.sort(
            key=lambda l: (
                label_order.get(l.get("score_label", "cold"), 2),
                -(l.get("score_numeric", 0)),
            )
        )

        priority_lists[rep_id] = rep_leads

    # Leads with no assigned rep go to "unassigned"
    unassigned = [
        l for l in scored_leads
        if not l.get("assigned_rep_id")
    ]
    if unassigned:
        unassigned.sort(
            key=lambda l: (
                label_order.get(l.get("score_label", "cold"), 2),
                -(l.get("score_numeric", 0)),
            )
        )
        priority_lists["unassigned"] = unassigned

    log.info(
        f"[DailyPipeline] Ranked leads for {len(priority_lists)} rep(s)"
    )

    return {**state, "priority_lists": priority_lists}


async def detect_stale(state: DailyPipelineState) -> DailyPipelineState:
    """Find leads with no activity in 7+ days. Mark severity levels."""
    scored_leads = state.get("scored_leads", [])
    now = datetime.now(IST)
    stale_leads = []

    for lead in scored_leads:
        last_activity_str = lead.get("last_activity_at")
        if not last_activity_str:
            # Never had activity — treat as 30 days stale
            days_stale = 30
        else:
            try:
                # Parse ISO timestamp
                last_activity = datetime.fromisoformat(
                    last_activity_str.replace("Z", "+00:00")
                )
                days_stale = (now - last_activity).days
            except (ValueError, TypeError):
                days_stale = 30

        if days_stale >= 7:
            severity = "critical" if days_stale >= 14 else "warning"
            stale_leads.append({
                "lead_id": lead["id"],
                "company_name": lead.get("company_name", "Unknown"),
                "contact_name": lead.get("contact_name", "Unknown"),
                "assigned_rep_id": lead.get("assigned_rep_id"),
                "days_stale": days_stale,
                "severity": severity,
                "deal_value": lead.get("deal_value", 0),
                "score_label": lead.get("score_label", "cold"),
                "score_numeric": lead.get("score_numeric", 0),
            })

    stale_leads.sort(key=lambda s: -s["days_stale"])

    log.info(
        f"[DailyPipeline] Found {len(stale_leads)} stale leads "
        f"({sum(1 for s in stale_leads if s['severity'] == 'critical')} critical)"
    )

    return {**state, "stale_leads": stale_leads}


async def detect_anomalies(state: DailyPipelineState) -> DailyPipelineState:
    """Compare this week vs last week activity metrics. Flag drops."""
    errors = list(state.get("errors", []))
    anomalies = []

    try:
        db = get_supabase_admin()
        now = datetime.now(IST)
        this_week_start = (now - timedelta(days=7)).isoformat()
        last_week_start = (now - timedelta(days=14)).isoformat()
        last_week_end = (now - timedelta(days=7)).isoformat()

        # This week's activities per rep
        this_week_resp = (
            db.table("activities")
            .select("user_id, id")
            .gte("created_at", this_week_start)
            .execute()
        )
        this_week_data = this_week_resp.data or []

        # Last week's activities per rep
        last_week_resp = (
            db.table("activities")
            .select("user_id, id")
            .gte("created_at", last_week_start)
            .lt("created_at", last_week_end)
            .execute()
        )
        last_week_data = last_week_resp.data or []

        # Count per rep
        this_week_counts: dict[str, int] = {}
        for a in this_week_data:
            uid = a.get("user_id", "unknown")
            this_week_counts[uid] = this_week_counts.get(uid, 0) + 1

        last_week_counts: dict[str, int] = {}
        for a in last_week_data:
            uid = a.get("user_id", "unknown")
            last_week_counts[uid] = last_week_counts.get(uid, 0) + 1

        # Build summary for AI analysis
        reps = state.get("reps", [])
        rep_name_map = {r["id"]: r.get("full_name", r.get("email", "Unknown")) for r in reps}

        metrics_text = "WEEKLY ACTIVITY COMPARISON:\n\n"
        for rep in reps:
            rid = rep["id"]
            tw = this_week_counts.get(rid, 0)
            lw = last_week_counts.get(rid, 0)
            name = rep_name_map.get(rid, "Unknown")
            pct_change = ((tw - lw) / lw * 100) if lw > 0 else (100 if tw > 0 else 0)
            metrics_text += (
                f"  {name}: This week={tw}, Last week={lw}, Change={pct_change:+.0f}%\n"
            )

        # Also include overall pipeline metrics
        total_leads = len(state.get("leads", []))
        hot_count = sum(
            1 for l in state.get("scored_leads", []) if l.get("score_label") == "hot"
        )
        stale_count = len(state.get("stale_leads", []))
        metrics_text += (
            f"\nPIPELINE SUMMARY:\n"
            f"  Total open leads: {total_leads}\n"
            f"  Hot leads: {hot_count}\n"
            f"  Stale leads (7+ days): {stale_count}\n"
        )

        messages = [
            SystemMessage(content=(
                "You are an anomaly detection agent for a construction SaaS sales team. "
                "Analyze the weekly activity comparison below. Flag any concerning patterns:\n"
                "- Rep activity dropped by 30%+ week-over-week\n"
                "- A rep has zero activities this week\n"
                "- Hot leads are declining while pipeline is growing (conversion issue)\n"
                "- Stale lead count is above 40% of total pipeline\n\n"
                "Return a JSON array of anomalies. Each anomaly:\n"
                '{"type": "activity_drop|zero_activity|conversion_issue|stale_pipeline", '
                '"severity": "critical|warning|info", '
                '"rep_id": "...|null", '
                '"description": "human-readable explanation", '
                '"recommendation": "what to do about it"}\n\n'
                "If no anomalies, return an empty array []. ONLY valid JSON, no markdown."
            )),
            HumanMessage(content=metrics_text),
        ]

        response = await tracked_llm_call(
            "anomaly_detection", messages, user_id="system_daily_pipeline"
        )
        raw_text = response.content.strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

        anomalies = json.loads(raw_text)

        log.info(f"[DailyPipeline] Detected {len(anomalies)} anomalies")

    except Exception as e:
        log.error(f"[DailyPipeline] detect_anomalies failed: {e}")
        errors.append(f"detect_anomalies: {str(e)}")

    return {**state, "anomalies": anomalies, "errors": errors}


async def generate_briefs(state: DailyPipelineState) -> DailyPipelineState:
    """Generate a personalized morning brief for each rep using Sonnet."""
    errors = list(state.get("errors", []))
    reps = state.get("reps", [])
    priority_lists = state.get("priority_lists", {})
    stale_leads = state.get("stale_leads", [])
    anomalies = state.get("anomalies", [])
    briefs: dict[str, str] = {}

    for rep in reps:
        rep_id = rep["id"]
        rep_name = rep.get("full_name", rep.get("email", "Rep"))
        rep_leads = priority_lists.get(rep_id, [])

        if not rep_leads:
            briefs[rep_id] = (
                f"Good morning {rep_name}! No active leads assigned to you today. "
                "Check with your manager for new assignments."
            )
            continue

        # Build lead summary
        hot_leads = [l for l in rep_leads if l.get("score_label") == "hot"]
        warm_leads = [l for l in rep_leads if l.get("score_label") == "warm"]
        cold_leads = [l for l in rep_leads if l.get("score_label") == "cold"]

        # Top 5 leads detail
        top_leads_text = ""
        for idx, lead in enumerate(rep_leads[:5], 1):
            top_leads_text += (
                f"{idx}. {lead.get('company_name', 'Unknown')} "
                f"({lead.get('contact_name', '?')}) — "
                f"{lead.get('score_label', '?').upper()} ({lead.get('score_numeric', 0)}/100) "
                f"— Deal: Rs {lead.get('deal_value', 0):,.0f}\n"
                f"   Next action: {lead.get('score_next_action', 'Follow up')}\n"
            )

        # Stale leads for this rep
        rep_stale = [s for s in stale_leads if s.get("assigned_rep_id") == rep_id]
        stale_text = ""
        if rep_stale:
            stale_text = f"\nSTALE LEADS ({len(rep_stale)}):\n"
            for s in rep_stale[:3]:
                stale_text += (
                    f"- {s['company_name']} — {s['days_stale']} days inactive "
                    f"[{s['severity'].upper()}]\n"
                )

        # Rep-specific anomalies
        rep_anomalies = [a for a in anomalies if a.get("rep_id") == rep_id]
        anomaly_text = ""
        if rep_anomalies:
            anomaly_text = "\nALERTS:\n"
            for a in rep_anomalies:
                anomaly_text += f"- {a['description']}\n"

        context = (
            f"REP: {rep_name}\n"
            f"DATE: {datetime.now(IST).strftime('%A, %d %B %Y')}\n\n"
            f"PIPELINE SNAPSHOT:\n"
            f"  Hot: {len(hot_leads)} | Warm: {len(warm_leads)} | Cold: {len(cold_leads)} "
            f"| Total: {len(rep_leads)}\n\n"
            f"TOP LEADS:\n{top_leads_text}"
            f"{stale_text}"
            f"{anomaly_text}"
        )

        messages = [
            SystemMessage(content=(
                "You are a sales coach for a construction SaaS company (Onsite Teams). "
                "Generate a concise morning brief for a sales rep. The brief will be sent "
                "via WhatsApp, so keep it UNDER 300 words and use simple formatting "
                "(no markdown, use plain text with line breaks and emojis for readability).\n\n"
                "STRUCTURE:\n"
                "1. Greeting with date and pipeline summary (1 line)\n"
                "2. TOP 3 LEADS TO CALL (with specific action for each)\n"
                "3. Stale leads warning (if any) with nudge to re-engage\n"
                "4. Any alerts or anomalies\n"
                "5. Motivational one-liner to start the day\n\n"
                "Be specific, actionable, and direct. No fluff. "
                "Use the rep's first name. Construction SaaS context — "
                "these are builders, contractors, and developers in India."
            )),
            HumanMessage(content=context),
        ]

        try:
            response = await tracked_llm_call(
                "brief_generation", messages, user_id="system_daily_pipeline"
            )
            briefs[rep_id] = response.content.strip()
        except Exception as e:
            log.error(f"[DailyPipeline] Brief generation failed for {rep_name}: {e}")
            errors.append(f"generate_briefs ({rep_name}): {str(e)}")
            # Fallback brief
            top3 = rep_leads[:3]
            fallback_lines = [
                f"Good morning {rep_name}!",
                f"You have {len(rep_leads)} active leads "
                f"({len(hot_leads)} hot, {len(warm_leads)} warm).",
                "",
                "Top leads to call:",
            ]
            for idx, lead in enumerate(top3, 1):
                fallback_lines.append(
                    f"{idx}. {lead.get('company_name', '?')} — "
                    f"{lead.get('score_label', '?').upper()}"
                )
            briefs[rep_id] = "\n".join(fallback_lines)

    log.info(f"[DailyPipeline] Generated briefs for {len(briefs)} reps")

    return {**state, "briefs": briefs, "errors": errors}


async def save_results(state: DailyPipelineState) -> DailyPipelineState:
    """Upsert lead scores and save briefs to Supabase."""
    errors = list(state.get("errors", []))
    scored_leads = state.get("scored_leads", [])
    briefs = state.get("briefs", {})
    now_iso = datetime.now(IST).isoformat()

    try:
        db = get_supabase_admin()

        # Upsert lead scores
        for lead in scored_leads:
            try:
                db.table("leads").update({
                    "score_label": lead.get("score_label"),
                    "score_numeric": lead.get("score_numeric"),
                    "score_reasoning": lead.get("score_reasoning", ""),
                    "score_next_action": lead.get("score_next_action", ""),
                    "last_scored_at": now_iso,
                }).eq("id", lead["id"]).execute()
            except Exception as e:
                log.warning(f"[DailyPipeline] Score upsert failed for {lead['id']}: {e}")
                errors.append(f"save_score ({lead['id']}): {str(e)}")

        # Save briefs (schema: brief_content, priority_list JSONB required)
        for rep_id, brief_text in briefs.items():
            if rep_id == "unassigned":
                continue
            try:
                plist = state.get("priority_lists", {}).get(rep_id, [])
                priority_list = [{"lead_id": l.get("id"), "score_label": l.get("score_label")} for l in plist[:50]]
                db.table("daily_briefs").insert({
                    "rep_id": rep_id,
                    "brief_content": brief_text,
                    "priority_list": priority_list,
                    "lead_count": len(plist),
                    "hot_count": sum(1 for l in plist if l.get("score_label") == "hot"),
                    "stale_count": sum(
                        1 for s in state.get("stale_leads", [])
                        if s.get("assigned_rep_id") == rep_id
                    ),
                }).execute()
            except Exception as e:
                log.warning(f"[DailyPipeline] Brief save failed for {rep_id}: {e}")
                errors.append(f"save_brief ({rep_id}): {str(e)}")

        # Save anomalies
        for anomaly in state.get("anomalies", []):
            try:
                db.table("anomalies").insert({
                    "type": anomaly.get("type", "unknown"),
                    "severity": anomaly.get("severity", "info"),
                    "rep_id": anomaly.get("rep_id"),
                    "description": anomaly.get("description", ""),
                    "recommendation": anomaly.get("recommendation", ""),
                    "detected_at": now_iso,
                }).execute()
            except Exception as e:
                log.warning(f"[DailyPipeline] Anomaly save failed: {e}")

        log.info(
            f"[DailyPipeline] Saved {len(scored_leads)} scores, "
            f"{len(briefs)} briefs, {len(state.get('anomalies', []))} anomalies"
        )

    except Exception as e:
        log.error(f"[DailyPipeline] save_results failed: {e}")
        errors.append(f"save_results: {str(e)}")

    return {**state, "errors": errors}


async def send_alerts(state: DailyPipelineState) -> DailyPipelineState:
    """Send briefs via WhatsApp (Gupshup) + Email (Resend). Log all alerts."""
    errors = list(state.get("errors", []))
    briefs = state.get("briefs", {})
    reps = state.get("reps", [])
    db = get_supabase_admin()

    rep_map = {r["id"]: r for r in reps}

    for rep_id, brief_text in briefs.items():
        if rep_id == "unassigned":
            continue

        rep = rep_map.get(rep_id)
        if not rep:
            continue

        rep_name = rep.get("full_name", rep.get("email", "Rep"))
        phone = rep.get("phone")
        email_addr = rep.get("email")

        # Send WhatsApp
        whatsapp_sent = False
        if phone:
            try:
                await send_whatsapp_message(
                    to=phone,
                    message=brief_text,
                )
                whatsapp_sent = True
                log.info(f"[DailyPipeline] WhatsApp sent to {rep_name}")
            except Exception as e:
                log.warning(f"[DailyPipeline] WhatsApp failed for {rep_name}: {e}")
                errors.append(f"whatsapp ({rep_name}): {str(e)}")

        # Send Email
        email_sent = False
        if email_addr:
            today_str = datetime.now(IST).strftime("%d %b %Y")
            try:
                await send_email(
                    to=email_addr,
                    subject=f"Your Morning Brief — {today_str}",
                    body=brief_text,
                )
                email_sent = True
                log.info(f"[DailyPipeline] Email sent to {rep_name}")
            except Exception as e:
                log.warning(f"[DailyPipeline] Email failed for {rep_name}: {e}")
                errors.append(f"email ({rep_name}): {str(e)}")

        # Log the alert
        try:
            db.table("alerts").insert({
                "type": "daily_brief",
                "rep_id": rep_id,
                "channel_whatsapp": whatsapp_sent,
                "channel_email": email_sent,
                "content_preview": brief_text[:200],
                "sent_at": datetime.now(IST).isoformat(),
            }).execute()
        except Exception as e:
            log.warning(f"[DailyPipeline] Alert log failed for {rep_name}: {e}")

    # Send manager summary if there are critical stale leads or anomalies
    critical_stale = [s for s in state.get("stale_leads", []) if s["severity"] == "critical"]
    critical_anomalies = [a for a in state.get("anomalies", []) if a.get("severity") == "critical"]

    if critical_stale or critical_anomalies:
        try:
            managers = (
                db.table("users")
                .select("*")
                .in_("role", ["manager", "founder"])
                .eq("is_active", True)
                .execute()
            ).data or []

            summary_lines = [
                f"MANAGER ALERT — {datetime.now(IST).strftime('%d %b %Y')}",
                "",
            ]

            if critical_stale:
                summary_lines.append(
                    f"{len(critical_stale)} CRITICAL stale leads (14+ days no activity):"
                )
                for s in critical_stale[:5]:
                    summary_lines.append(
                        f"  - {s['company_name']} ({s['days_stale']} days) "
                        f"— Deal: Rs {s.get('deal_value', 0):,.0f}"
                    )
                summary_lines.append("")

            if critical_anomalies:
                summary_lines.append(f"{len(critical_anomalies)} CRITICAL anomalies:")
                for a in critical_anomalies[:3]:
                    summary_lines.append(f"  - {a['description']}")
                summary_lines.append("")

            manager_summary = "\n".join(summary_lines)

            for mgr in managers:
                mgr_phone = mgr.get("phone")
                if mgr_phone:
                    try:
                        await send_whatsapp_message(to=mgr_phone, message=manager_summary)
                    except Exception:
                        pass

                mgr_email = mgr.get("email")
                if mgr_email:
                    try:
                        await send_email(
                            to=mgr_email,
                            subject=f"ALERT: {len(critical_stale)} stale leads, "
                                    f"{len(critical_anomalies)} anomalies",
                            body=manager_summary,
                        )
                    except Exception:
                        pass

        except Exception as e:
            log.warning(f"[DailyPipeline] Manager alert failed: {e}")

    return {**state, "errors": errors}


# ---------------------------------------------------------------------------
# Graph Construction
# ---------------------------------------------------------------------------

def build_daily_pipeline_graph() -> StateGraph:
    """Build the LangGraph StateGraph for the daily pipeline."""
    graph = StateGraph(DailyPipelineState)

    # Add nodes
    graph.add_node("fetch_data", fetch_data)
    graph.add_node("score_leads", score_leads)
    graph.add_node("rank_priority", rank_priority)
    graph.add_node("detect_stale", detect_stale)
    graph.add_node("detect_anomalies", detect_anomalies)
    graph.add_node("generate_briefs", generate_briefs)
    graph.add_node("save_results", save_results)
    graph.add_node("send_alerts", send_alerts)

    # Set entry point
    graph.set_entry_point("fetch_data")

    # Define edges: linear pipeline
    graph.add_edge("fetch_data", "score_leads")
    graph.add_edge("score_leads", "rank_priority")
    graph.add_edge("rank_priority", "detect_stale")
    graph.add_edge("detect_stale", "detect_anomalies")
    graph.add_edge("detect_anomalies", "generate_briefs")
    graph.add_edge("generate_briefs", "save_results")
    graph.add_edge("save_results", "send_alerts")
    graph.add_edge("send_alerts", END)

    return graph


# ---------------------------------------------------------------------------
# Public Entry Point
# ---------------------------------------------------------------------------

async def run_daily_pipeline() -> dict:
    """Compile and run the daily pipeline graph. Returns final state."""
    log.info("[DailyPipeline] Starting daily pipeline run")
    start_time = datetime.now(IST)

    graph = build_daily_pipeline_graph()
    app = graph.compile()

    initial_state: DailyPipelineState = {
        "leads": [],
        "notes": {},
        "activities": {},
        "reps": [],
        "scored_leads": [],
        "stale_leads": [],
        "anomalies": [],
        "priority_lists": {},
        "briefs": {},
        "errors": [],
    }

    final_state = await app.ainvoke(initial_state)

    duration = (datetime.now(IST) - start_time).total_seconds()
    log.info(
        f"[DailyPipeline] Completed in {duration:.1f}s — "
        f"{len(final_state.get('scored_leads', []))} leads scored, "
        f"{len(final_state.get('briefs', {}))} briefs generated, "
        f"{len(final_state.get('errors', []))} errors"
    )

    # Log pipeline run
    try:
        db = get_supabase_admin()
        db.table("pipeline_runs").insert({
            "pipeline_type": "daily",
            "started_at": start_time.isoformat(),
            "completed_at": datetime.now(IST).isoformat(),
            "duration_seconds": round(duration, 1),
            "leads_scored": len(final_state.get("scored_leads", [])),
            "briefs_generated": len(final_state.get("briefs", {})),
            "stale_leads_found": len(final_state.get("stale_leads", [])),
            "anomalies_found": len(final_state.get("anomalies", [])),
            "errors": final_state.get("errors", []),
            "success": len(final_state.get("errors", [])) == 0,
        }).execute()
    except Exception as e:
        log.warning(f"[DailyPipeline] Failed to log pipeline run: {e}")

    return final_state

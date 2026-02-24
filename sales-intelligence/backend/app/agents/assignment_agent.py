"""Smart Assignment Agent — assigns new leads to the best-fit sales rep.

Uses AI (Haiku) to evaluate rep capacity, track record, and geography match
to make intelligent lead assignments. Sends WhatsApp alert to the assigned rep.
"""

import json
import logging
from datetime import datetime, timedelta, timezone

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import tracked_llm_call
from app.core.supabase_client import get_supabase_admin
from app.services.whatsapp import send_whatsapp_message

log = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))


async def assign_new_lead(lead_id: str) -> dict:
    """Assign a new lead to the best-fit sales rep.

    Logic:
    1. Get the lead data
    2. Get all active reps with their lead counts and conversion rates
    3. Use Haiku to pick the best rep based on capacity, track record, geography
    4. Update lead.assigned_rep_id in Supabase
    5. Send WhatsApp alert to assigned rep

    Args:
        lead_id: UUID of the lead to assign.

    Returns:
        dict with assignment result including rep_id, rep_name, and reasoning.
    """
    db = get_supabase_admin()
    now = datetime.now(IST)

    # ------------------------------------------------------------------
    # 1. Get the lead data
    # ------------------------------------------------------------------
    try:
        lead_resp = (
            db.table("leads")
            .select("*")
            .eq("id", lead_id)
            .single()
            .execute()
        )
        lead = lead_resp.data
    except Exception as e:
        log.error(f"[AssignmentAgent] Failed to fetch lead {lead_id}: {e}")
        return {"success": False, "error": f"Lead not found: {str(e)}"}

    if not lead:
        return {"success": False, "error": f"Lead {lead_id} not found"}

    # Check if already assigned
    if lead.get("assigned_rep_id"):
        log.info(
            f"[AssignmentAgent] Lead {lead_id} already assigned to {lead['assigned_rep_id']}"
        )
        return {
            "success": True,
            "already_assigned": True,
            "rep_id": lead["assigned_rep_id"],
        }

    # ------------------------------------------------------------------
    # 2. Get all active reps with metrics
    # ------------------------------------------------------------------
    try:
        reps_resp = (
            db.table("users")
            .select("*")
            .eq("role", "rep")
            .eq("is_active", True)
            .execute()
        )
        reps = reps_resp.data or []
    except Exception as e:
        log.error(f"[AssignmentAgent] Failed to fetch reps: {e}")
        return {"success": False, "error": f"Could not fetch reps: {str(e)}"}

    if not reps:
        log.warning("[AssignmentAgent] No active reps found for assignment")
        return {"success": False, "error": "No active reps available"}

    # Get lead counts per rep (open leads only)
    rep_metrics = []
    for rep in reps:
        rep_id = rep["id"]

        try:
            # Count open leads assigned to this rep
            open_leads_resp = (
                db.table("leads")
                .select("id", count="exact")
                .eq("assigned_rep_id", rep_id)
                .in_("status", ["new", "contacted", "qualified", "proposal", "negotiation"])
                .execute()
            )
            open_lead_count = open_leads_resp.count or 0

            # Count won deals in last 90 days
            ninety_days_ago = (now - timedelta(days=90)).isoformat()
            won_resp = (
                db.table("leads")
                .select("id", count="exact")
                .eq("assigned_rep_id", rep_id)
                .eq("status", "won")
                .gte("closed_at", ninety_days_ago)
                .execute()
            )
            won_count = won_resp.count or 0

            # Count total closed deals (won + lost) in last 90 days for conversion rate
            total_closed_resp = (
                db.table("leads")
                .select("id", count="exact")
                .eq("assigned_rep_id", rep_id)
                .in_("status", ["won", "lost"])
                .gte("closed_at", ninety_days_ago)
                .execute()
            )
            total_closed = total_closed_resp.count or 0

            conversion_rate = (won_count / total_closed * 100) if total_closed > 0 else 0

            # Get regions the rep has won deals in
            region_resp = (
                db.table("leads")
                .select("region")
                .eq("assigned_rep_id", rep_id)
                .eq("status", "won")
                .execute()
            )
            won_regions = list(set(
                r["region"] for r in (region_resp.data or [])
                if r.get("region")
            ))

            # Get industries the rep has won deals in
            industry_resp = (
                db.table("leads")
                .select("industry")
                .eq("assigned_rep_id", rep_id)
                .eq("status", "won")
                .execute()
            )
            won_industries = list(set(
                r["industry"] for r in (industry_resp.data or [])
                if r.get("industry")
            ))

            rep_metrics.append({
                "rep_id": rep_id,
                "rep_name": rep.get("full_name", rep.get("email", "Unknown")),
                "phone": rep.get("phone"),
                "email": rep.get("email"),
                "open_lead_count": open_lead_count,
                "won_last_90d": won_count,
                "conversion_rate": round(conversion_rate, 1),
                "won_regions": won_regions,
                "won_industries": won_industries,
                "region": rep.get("region", ""),
            })

        except Exception as e:
            log.warning(f"[AssignmentAgent] Metrics fetch failed for rep {rep_id}: {e}")
            rep_metrics.append({
                "rep_id": rep_id,
                "rep_name": rep.get("full_name", rep.get("email", "Unknown")),
                "phone": rep.get("phone"),
                "email": rep.get("email"),
                "open_lead_count": 999,  # Treat as at capacity if we can't check
                "won_last_90d": 0,
                "conversion_rate": 0,
                "won_regions": [],
                "won_industries": [],
                "region": rep.get("region", ""),
            })

    # ------------------------------------------------------------------
    # 3. Use Haiku to pick the best rep
    # ------------------------------------------------------------------
    lead_context = (
        f"NEW LEAD TO ASSIGN:\n"
        f"  Company: {lead.get('company_name', 'Unknown')}\n"
        f"  Contact: {lead.get('contact_name', 'Unknown')}\n"
        f"  Region: {lead.get('region', 'Unknown')}\n"
        f"  Industry: {lead.get('industry', 'Unknown')}\n"
        f"  Deal Value: Rs {lead.get('deal_value', 0):,.0f}\n"
        f"  Source: {lead.get('source', 'Unknown')}\n"
    )

    reps_context = "AVAILABLE REPS:\n\n"
    for rm in rep_metrics:
        at_capacity = rm["open_lead_count"] >= 30
        reps_context += (
            f"  Rep: {rm['rep_name']} (ID: {rm['rep_id']})\n"
            f"    Open Leads: {rm['open_lead_count']}/30 {'[AT CAPACITY]' if at_capacity else ''}\n"
            f"    Won (90d): {rm['won_last_90d']} | Conversion: {rm['conversion_rate']}%\n"
            f"    Region: {rm.get('region', 'N/A')}\n"
            f"    Won Regions: {', '.join(rm['won_regions']) or 'None yet'}\n"
            f"    Won Industries: {', '.join(rm['won_industries']) or 'None yet'}\n\n"
        )

    messages = [
        SystemMessage(content=(
            "You are a sales assignment AI for Onsite Teams, a construction SaaS company "
            "in India. You need to assign a new lead to the best-fit sales rep.\n\n"
            "ASSIGNMENT CRITERIA (in priority order):\n"
            "1. CAPACITY: Rep must have fewer than 30 open leads. Never assign to a rep at "
            "   or above capacity unless all reps are at capacity.\n"
            "2. TRACK RECORD: Prefer reps with higher conversion rates and more wins.\n"
            "3. GEOGRAPHY MATCH: Prefer reps who have won deals in the same region. "
            "   Regional knowledge matters in construction (local regulations, builders network).\n"
            "4. INDUSTRY MATCH: Prefer reps with wins in the same industry segment.\n"
            "5. LOAD BALANCING: If two reps are otherwise equal, pick the one with fewer "
            "   open leads to balance workload.\n\n"
            "Return JSON:\n"
            '{"assigned_rep_id": "...", "rep_name": "...", "reasoning": "1-2 sentence explanation", '
            '"confidence": "high|medium|low"}\n\n'
            "ONLY valid JSON, no markdown."
        )),
        HumanMessage(content=f"{lead_context}\n{reps_context}"),
    ]

    try:
        response = await tracked_llm_call(
            "assignment", messages, lead_id=lead_id, user_id="system_assignment"
        )
        raw_text = response.content.strip()

        # Clean markdown wrapping
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

        decision = json.loads(raw_text)
        assigned_rep_id = decision.get("assigned_rep_id")
        assigned_rep_name = decision.get("rep_name", "Unknown")
        reasoning = decision.get("reasoning", "")
        confidence = decision.get("confidence", "medium")

    except Exception as e:
        log.error(f"[AssignmentAgent] AI assignment failed: {e}")
        # Fallback: assign to rep with fewest open leads and capacity
        available = [r for r in rep_metrics if r["open_lead_count"] < 30]
        if not available:
            available = rep_metrics  # All at capacity, pick least loaded anyway

        available.sort(key=lambda r: r["open_lead_count"])
        fallback_rep = available[0]
        assigned_rep_id = fallback_rep["rep_id"]
        assigned_rep_name = fallback_rep["rep_name"]
        reasoning = (
            f"AI assignment failed. Fallback: assigned to {assigned_rep_name} "
            f"(fewest open leads: {fallback_rep['open_lead_count']})"
        )
        confidence = "low"

    if not assigned_rep_id:
        return {"success": False, "error": "No rep could be selected"}

    # ------------------------------------------------------------------
    # 4. Update lead.assigned_rep_id in Supabase
    # ------------------------------------------------------------------
    try:
        db.table("leads").update({
            "assigned_rep_id": assigned_rep_id,
            "assigned_at": now.isoformat(),
            "assignment_reasoning": reasoning,
        }).eq("id", lead_id).execute()

        # Log the assignment as an activity
        db.table("lead_activities").insert({
            "lead_id": lead_id,
            "performed_by": assigned_rep_id,
            "activity_type": "assignment",
            "details": (
                f"Lead auto-assigned to {assigned_rep_name}. "
                f"Reason: {reasoning} (Confidence: {confidence})"
            ),
            "activity_date": now.isoformat(),
        }).execute()

        log.info(
            f"[AssignmentAgent] Assigned lead {lead_id} "
            f"({lead.get('company_name', '?')}) to {assigned_rep_name}"
        )

    except Exception as e:
        log.error(f"[AssignmentAgent] DB update failed: {e}")
        return {"success": False, "error": f"Database update failed: {str(e)}"}

    # ------------------------------------------------------------------
    # 5. Send WhatsApp alert to assigned rep
    # ------------------------------------------------------------------
    assigned_rep_data = next(
        (r for r in rep_metrics if r["rep_id"] == assigned_rep_id), None
    )
    phone = assigned_rep_data.get("phone") if assigned_rep_data else None

    if phone:
        alert_message = (
            f"New Lead Assigned!\n\n"
            f"Company: {lead.get('company_name', 'Unknown')}\n"
            f"Contact: {lead.get('contact_name', 'Unknown')}\n"
            f"Deal Value: Rs {lead.get('deal_value', 0):,.0f}\n"
            f"Region: {lead.get('region', 'N/A')}\n"
            f"Source: {lead.get('source', 'N/A')}\n\n"
            f"Action: Review and reach out within 2 hours for best results."
        )

        try:
            await send_whatsapp_message(to=phone, message=alert_message)
            log.info(f"[AssignmentAgent] WhatsApp alert sent to {assigned_rep_name}")
        except Exception as e:
            log.warning(
                f"[AssignmentAgent] WhatsApp alert failed for {assigned_rep_name}: {e}"
            )

    # Log the alert
    try:
        db.table("alerts").insert({
            "type": "lead_assignment",
            "rep_id": assigned_rep_id,
            "lead_id": lead_id,
            "channel_whatsapp": phone is not None,
            "channel_email": False,
            "content_preview": (
                f"New lead: {lead.get('company_name', '?')} "
                f"(Rs {lead.get('deal_value', 0):,.0f})"
            ),
            "sent_at": now.isoformat(),
        }).execute()
    except Exception as e:
        log.warning(f"[AssignmentAgent] Alert log failed: {e}")

    return {
        "success": True,
        "lead_id": lead_id,
        "assigned_rep_id": assigned_rep_id,
        "assigned_rep_name": assigned_rep_name,
        "reasoning": reasoning,
        "confidence": confidence,
    }

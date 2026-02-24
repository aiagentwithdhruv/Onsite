"""Lead management routes — serves priority leads from dashboard_summary.

Individual leads are NOT bulk-stored in Supabase (free-tier storage constraint).
Instead, hot_prospects and stale_leads are served from the pre-computed
dashboard_summary.  Lead detail/actions still work for any leads that
exist in the leads table (e.g. manually created or from Zoho sync).
"""

import logging
import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.supabase_client import get_supabase_admin

log = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class LeadActionRequest(BaseModel):
    action: str  # called, not_reachable, meeting_scheduled, won, lost
    note: str | None = None


class PaginatedLeadsResponse(BaseModel):
    leads: list[dict]
    total: int
    page: int
    per_page: int
    total_pages: int


# ---------------------------------------------------------------------------
# Stage mapping for quick actions
# ---------------------------------------------------------------------------

ACTION_TO_STAGE = {
    "called": "contacted",
    "not_reachable": "not_reachable",
    "meeting_scheduled": "meeting_scheduled",
    "won": "won",
    "lost": "lost",
}


def _summary_lead_to_lead(item: dict, category: str, owner: str) -> dict:
    """Convert a hot_prospect or stale_lead from dashboard_summary into a lead-shaped dict."""
    name = item.get("name", "Unknown")
    phone = item.get("phone", "")
    company = item.get("company", "")
    # Generate a stable deterministic ID from name+phone
    raw = f"{name}-{phone}-{company}"
    lead_id = f"summary-{hashlib.md5(raw.encode()).hexdigest()[:16]}"

    if category == "hot":
        stage = item.get("stage", "prospect")
        score = "hot"
        score_numeric = 85
    else:
        stage = "stale"
        score = "cold"
        score_numeric = 20

    return {
        "id": lead_id,
        "zoho_lead_id": None,
        "company": company or None,
        "contact_name": name,
        "email": None,
        "phone": phone or None,
        "source": None,
        "stage": stage,
        "deal_value": item.get("deal_value"),
        "industry": "Construction",
        "geography": None,
        "assigned_rep_id": None,
        "assigned_rep_name": owner,
        "last_activity_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "score": score,
        "score_numeric": score_numeric,
        "days_stale": item.get("days"),
        "status": item.get("status"),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_model=PaginatedLeadsResponse)
@router.get("", response_model=PaginatedLeadsResponse)
async def list_leads(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    score_filter: Optional[str] = Query(None, description="Filter by score: hot, warm, cold"),
    stage_filter: Optional[str] = Query(None, description="Filter by stage"),
    search: Optional[str] = Query(None, description="Search by name, company, email, or phone"),
    sort_by: Optional[str] = Query(None, description="Sort: score, deal_value, last_activity, created_at"),
    limit: Optional[int] = Query(None, description="Override per_page limit"),
    user: dict = Depends(get_current_user),
):
    """List priority leads from dashboard_summary (hot prospects + stale leads)."""
    try:
        db = get_supabase_admin()
        is_rep = user.get("role") in ("rep", "sales_rep")

        # Fetch dashboard_summary
        r = db.table("dashboard_summary").select(
            "summary_by_owner, aging_data, total_leads"
        ).eq("id", "current").maybe_single().execute()

        if not r.data:
            return PaginatedLeadsResponse(leads=[], total=0, page=page, per_page=per_page, total_pages=0)

        summary = r.data
        by_owner = summary.get("summary_by_owner") or {}
        global_aging = summary.get("aging_data") or {}

        # Build leads list from hot_prospects + stale_leads
        all_leads = []

        if is_rep:
            # Rep sees only their deal_owner's leads
            owner_name = user.get("deal_owner_name") or ""
            owner_data = by_owner.get(owner_name, {})
            aging = owner_data.get("aging_data") or {}

            for item in (aging.get("hot_prospects") or []):
                all_leads.append(_summary_lead_to_lead(item, "hot", owner_name))
            for item in (aging.get("stale_leads") or []):
                all_leads.append(_summary_lead_to_lead(item, "stale", owner_name))
        else:
            # Manager sees all owners' leads
            for owner_name, owner_data in by_owner.items():
                aging = owner_data.get("aging_data") or {}
                for item in (aging.get("hot_prospects") or []):
                    all_leads.append(_summary_lead_to_lead(item, "hot", owner_name))
                for item in (aging.get("stale_leads") or []):
                    all_leads.append(_summary_lead_to_lead(item, "stale", owner_name))

            # Also add global hot/stale if not duplicate
            seen_ids = {l["id"] for l in all_leads}
            for item in (global_aging.get("hot_prospects") or []):
                owner = item.get("owner", "")
                lead = _summary_lead_to_lead(item, "hot", owner)
                if lead["id"] not in seen_ids:
                    all_leads.append(lead)
                    seen_ids.add(lead["id"])
            for item in (global_aging.get("stale_leads") or []):
                owner = item.get("owner", "")
                lead = _summary_lead_to_lead(item, "stale", owner)
                if lead["id"] not in seen_ids:
                    all_leads.append(lead)
                    seen_ids.add(lead["id"])

        # Apply filters
        if score_filter:
            all_leads = [l for l in all_leads if l.get("score") == score_filter]
        if stage_filter:
            all_leads = [l for l in all_leads if l.get("stage") == stage_filter]
        if search:
            q = search.lower()
            all_leads = [l for l in all_leads if
                         q in (l.get("contact_name") or "").lower() or
                         q in (l.get("company") or "").lower() or
                         q in (l.get("phone") or "").lower()]

        # Sort: hot leads first by default
        if sort_by == "score":
            all_leads.sort(key=lambda l: l.get("score_numeric", 0), reverse=True)
        elif sort_by == "deal_value":
            all_leads.sort(key=lambda l: l.get("deal_value") or 0, reverse=True)
        else:
            # Default: hot first, then stale
            all_leads.sort(key=lambda l: l.get("score_numeric", 0), reverse=True)

        # Paginate
        actual_per_page = limit if limit else per_page
        total = len(all_leads)
        total_pages = max(1, (total + actual_per_page - 1) // actual_per_page)
        offset = (page - 1) * actual_per_page
        page_leads = all_leads[offset:offset + actual_per_page]

        return PaginatedLeadsResponse(
            leads=page_leads,
            total=total,
            page=page,
            per_page=actual_per_page,
            total_pages=total_pages,
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error listing leads: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch leads")


@router.get("/{lead_id}")
async def get_lead(lead_id: str, user: dict = Depends(get_current_user)):
    """Get a single lead — checks leads table first, falls back to summary data."""
    try:
        db = get_supabase_admin()

        # Try the leads table first (for real persisted leads)
        if not lead_id.startswith("summary-"):
            try:
                lead_result = (
                    db.table("leads")
                    .select("*")
                    .eq("id", lead_id)
                    .single()
                    .execute()
                )

                if lead_result.data:
                    lead = lead_result.data

                    if user["role"] in ("rep", "sales_rep") and lead.get("assigned_rep_id") != user["id"]:
                        raise HTTPException(status_code=403, detail="Not authorized to view this lead")

                    # Latest score
                    score_result = (
                        db.table("lead_scores").select("*")
                        .eq("lead_id", lead_id).order("scored_at", desc=True).limit(1).execute()
                    )
                    lead["latest_score"] = score_result.data[0] if score_result.data else None

                    # Recent activities (last 20)
                    activities_result = (
                        db.table("lead_activities").select("*")
                        .eq("lead_id", lead_id).order("activity_date", desc=True).limit(20).execute()
                    )
                    lead["activities"] = activities_result.data or []

                    # Notes
                    notes_result = (
                        db.table("lead_notes").select("*")
                        .eq("lead_id", lead_id).order("note_date", desc=True).limit(20).execute()
                    )
                    lead["notes"] = notes_result.data or []

                    lead["research"] = None
                    return {"lead": lead}
            except Exception:
                pass

        # Fallback: construct from summary data (for summary-xxx IDs)
        r = db.table("dashboard_summary").select("summary_by_owner, aging_data").eq("id", "current").maybe_single().execute()
        if not r.data:
            raise HTTPException(status_code=404, detail="Lead not found")

        by_owner = r.data.get("summary_by_owner") or {}
        global_aging = r.data.get("aging_data") or {}

        # Search through all owners for the matching lead
        for owner_name, owner_data in by_owner.items():
            aging = owner_data.get("aging_data") or {}
            for item in (aging.get("hot_prospects") or []):
                lead = _summary_lead_to_lead(item, "hot", owner_name)
                if lead["id"] == lead_id:
                    lead["activities"] = []
                    lead["notes"] = []
                    lead["latest_score"] = {"score": "hot", "score_numeric": 85}
                    lead["research"] = None
                    return {"lead": lead}
            for item in (aging.get("stale_leads") or []):
                lead = _summary_lead_to_lead(item, "stale", owner_name)
                if lead["id"] == lead_id:
                    lead["activities"] = []
                    lead["notes"] = []
                    lead["latest_score"] = {"score": "cold", "score_numeric": 20}
                    lead["research"] = None
                    return {"lead": lead}

        raise HTTPException(status_code=404, detail="Lead not found")

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error fetching lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch lead details")


@router.post("/{lead_id}/action")
async def lead_action(lead_id: str, payload: LeadActionRequest, user: dict = Depends(get_current_user)):
    """Quick action on a lead — only works for leads persisted in the leads table."""
    if payload.action not in ACTION_TO_STAGE:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action '{payload.action}'. Valid actions: {list(ACTION_TO_STAGE.keys())}",
        )

    if lead_id.startswith("summary-"):
        raise HTTPException(
            status_code=400,
            detail="Actions are not available for summary leads. Connect Zoho CRM to enable lead actions.",
        )

    try:
        db = get_supabase_admin()

        lead_result = db.table("leads").select("id, assigned_rep_id, stage").eq("id", lead_id).single().execute()
        if not lead_result.data:
            raise HTTPException(status_code=404, detail="Lead not found")

        lead = lead_result.data

        if user["role"] in ("rep", "sales_rep") and lead.get("assigned_rep_id") != user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to update this lead")

        new_stage = ACTION_TO_STAGE[payload.action]
        now = datetime.now(timezone.utc).isoformat()

        db.table("leads").update({
            "stage": new_stage,
            "last_activity_at": now,
            "updated_at": now,
        }).eq("id", lead_id).execute()

        db.table("lead_activities").insert({
            "lead_id": lead_id,
            "activity_type": "call" if payload.action in ("called", "not_reachable") else "meeting",
            "subject": f"Marked as {payload.action.replace('_', ' ')}",
            "outcome": payload.action,
            "performed_by": user["id"],
            "activity_date": now,
        }).execute()

        if payload.note:
            db.table("lead_notes").insert({
                "lead_id": lead_id,
                "note_text": payload.note,
                "note_source": "manual",
                "created_by": user["id"],
                "note_date": now,
            }).execute()

        return {
            "message": f"Lead updated to '{new_stage}'",
            "lead_id": lead_id,
            "new_stage": new_stage,
            "action": payload.action,
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error performing action on lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update lead")


@router.get("/{lead_id}/timeline")
async def lead_timeline(lead_id: str, user: dict = Depends(get_current_user)):
    """Get full timeline for a lead."""
    if lead_id.startswith("summary-"):
        return {
            "lead_id": lead_id,
            "lead_name": "Summary Lead",
            "timeline": [],
            "total_events": 0,
        }

    try:
        db = get_supabase_admin()

        lead_result = db.table("leads").select("id, assigned_rep_id, contact_name").eq("id", lead_id).single().execute()
        if not lead_result.data:
            raise HTTPException(status_code=404, detail="Lead not found")

        lead = lead_result.data

        if user["role"] in ("rep", "sales_rep") and lead.get("assigned_rep_id") != user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to view this lead's timeline")

        activities_result = (
            db.table("lead_activities").select("*")
            .eq("lead_id", lead_id).order("activity_date", desc=False).execute()
        )
        notes_result = (
            db.table("lead_notes").select("*")
            .eq("lead_id", lead_id).order("note_date", desc=False).execute()
        )

        timeline = []
        for activity in (activities_result.data or []):
            timeline.append({
                "type": "activity",
                "timestamp": activity.get("activity_date"),
                "activity_type": activity.get("activity_type"),
                "description": activity.get("subject") or activity.get("details", ""),
                "outcome": activity.get("outcome"),
                "data": activity,
            })
        for note in (notes_result.data or []):
            timeline.append({
                "type": "note",
                "timestamp": note.get("note_date"),
                "description": note.get("note_text"),
                "source": note.get("note_source"),
                "data": note,
            })
        timeline.sort(key=lambda x: x.get("timestamp") or "")

        return {
            "lead_id": lead_id,
            "lead_name": lead.get("contact_name"),
            "timeline": timeline,
            "total_events": len(timeline),
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error fetching timeline for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch lead timeline")

"""Lead management routes — list, detail, actions, timeline."""

import logging
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
    user: dict = Depends(get_current_user),
):
    """List leads with pagination, filtering, and role-based access."""
    try:
        db = get_supabase_admin()
        offset = (page - 1) * per_page

        # Base query with latest score
        query = db.table("leads").select("*, lead_scores(score, score_numeric, scored_at)", count="exact")

        # Role-based filtering: reps see only their own leads
        if user["role"] in ("rep", "sales_rep"):
            query = query.eq("assigned_rep_id", user["id"])

        # Stage filter
        if stage_filter:
            query = query.eq("stage", stage_filter)

        # Search across contact_name, company, email, phone
        if search:
            query = query.or_(
                f"contact_name.ilike.%{search}%,"
                f"company.ilike.%{search}%,"
                f"email.ilike.%{search}%,"
                f"phone.ilike.%{search}%"
            )

        # Order by most recent first, then paginate
        query = query.order("created_at", desc=True).range(offset, offset + per_page - 1)

        result = query.execute()

        total = result.count if result.count is not None else 0
        total_pages = max(1, (total + per_page - 1) // per_page)

        # Flatten the latest score into each lead
        leads = []
        for lead in (result.data or []):
            scores = lead.pop("lead_scores", []) or []
            if scores:
                latest = sorted(scores, key=lambda s: s.get("scored_at", ""), reverse=True)[0]
                lead["score"] = latest.get("score")
                lead["score_numeric"] = latest.get("score_numeric")
            else:
                lead["score"] = None
                lead["score_numeric"] = None
            leads.append(lead)

        return PaginatedLeadsResponse(
            leads=leads,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error listing leads: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch leads")


@router.get("/{lead_id}")
async def get_lead(lead_id: str, user: dict = Depends(get_current_user)):
    """Get a single lead with latest score, recent activities, and notes."""
    try:
        db = get_supabase_admin()

        # Fetch lead
        lead_result = (
            db.table("leads")
            .select("*")
            .eq("id", lead_id)
            .single()
            .execute()
        )

        if not lead_result.data:
            raise HTTPException(status_code=404, detail="Lead not found")

        lead = lead_result.data

        # Reps can only view their own leads
        if user["role"] in ("rep", "sales_rep") and lead.get("assigned_rep_id") != user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to view this lead")

        # Latest score
        score_result = (
            db.table("lead_scores")
            .select("*")
            .eq("lead_id", lead_id)
            .order("scored_at", desc=True)
            .limit(1)
            .execute()
        )
        lead["latest_score"] = score_result.data[0] if score_result.data else None

        # Recent activities (last 20)
        activities_result = (
            db.table("lead_activities")
            .select("*")
            .eq("lead_id", lead_id)
            .order("activity_date", desc=True)
            .limit(20)
            .execute()
        )
        lead["activities"] = activities_result.data or []

        # Notes
        notes_result = (
            db.table("lead_notes")
            .select("*")
            .eq("lead_id", lead_id)
            .order("note_date", desc=True)
            .limit(20)
            .execute()
        )
        lead["notes"] = notes_result.data or []

        # Research results (latest)
        research_result = (
            db.table("lead_research")
            .select("*")
            .eq("lead_id", lead_id)
            .order("researched_at", desc=True)
            .limit(1)
            .execute()
        )
        lead["research"] = research_result.data[0] if research_result.data else None

        return {"lead": lead}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error fetching lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch lead details")


@router.post("/{lead_id}/action")
async def lead_action(lead_id: str, payload: LeadActionRequest, user: dict = Depends(get_current_user)):
    """Quick action on a lead: mark as called, not_reachable, meeting_scheduled, won, lost."""
    if payload.action not in ACTION_TO_STAGE:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action '{payload.action}'. Valid actions: {list(ACTION_TO_STAGE.keys())}",
        )

    try:
        db = get_supabase_admin()

        # Verify lead exists and user has access
        lead_result = db.table("leads").select("id, assigned_rep_id, stage").eq("id", lead_id).single().execute()
        if not lead_result.data:
            raise HTTPException(status_code=404, detail="Lead not found")

        lead = lead_result.data

        # Reps can only act on their own leads
        if user["role"] in ("rep", "sales_rep") and lead.get("assigned_rep_id") != user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to update this lead")

        new_stage = ACTION_TO_STAGE[payload.action]
        now = datetime.now(timezone.utc).isoformat()

        # Update lead stage + last activity
        db.table("leads").update({
            "stage": new_stage,
            "last_activity_at": now,
            "updated_at": now,
        }).eq("id", lead_id).execute()

        # Log the activity
        db.table("lead_activities").insert({
            "lead_id": lead_id,
            "activity_type": "call" if payload.action in ("called", "not_reachable") else "meeting",
            "subject": f"Marked as {payload.action.replace('_', ' ')}",
            "outcome": payload.action,
            "performed_by": user["id"],
            "activity_date": now,
        }).execute()

        # If a note was provided, save it
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
    """Get full timeline for a lead — activities + notes in chronological order."""
    try:
        db = get_supabase_admin()

        # Verify lead exists and user has access
        lead_result = db.table("leads").select("id, assigned_rep_id, contact_name").eq("id", lead_id).single().execute()
        if not lead_result.data:
            raise HTTPException(status_code=404, detail="Lead not found")

        lead = lead_result.data

        if user["role"] in ("rep", "sales_rep") and lead.get("assigned_rep_id") != user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to view this lead's timeline")

        # Fetch activities
        activities_result = (
            db.table("lead_activities")
            .select("*")
            .eq("lead_id", lead_id)
            .order("activity_date", desc=False)
            .execute()
        )

        # Fetch notes
        notes_result = (
            db.table("lead_notes")
            .select("*")
            .eq("lead_id", lead_id)
            .order("note_date", desc=False)
            .execute()
        )

        # Merge and sort chronologically
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

        # Sort by timestamp ascending (oldest first)
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

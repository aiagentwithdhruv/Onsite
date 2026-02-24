"""Research routes — trigger and retrieve AI research for leads."""

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.supabase_client import get_supabase_admin

log = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class ResearchTriggerResponse(BaseModel):
    message: str
    lead_id: str
    status: str


class ResearchStatusResponse(BaseModel):
    lead_id: str
    status: str
    researched_at: str | None = None


# ---------------------------------------------------------------------------
# Background task wrapper
# ---------------------------------------------------------------------------

async def _run_research_background(lead_id: str, user_id: str):
    """Run the research agent in the background."""
    db = get_supabase_admin()
    try:
        from app.agents.research_agent import run_research_agent

        result = await run_research_agent(lead_id=lead_id, triggered_by=user_id)

        # Update research record with results
        update_data = {
            "status": "complete",
            "researched_at": datetime.now(timezone.utc).isoformat(),
        }
        if isinstance(result, dict):
            for key in ["company_info", "web_research", "notes_summary", "close_strategy", "pricing_suggestion"]:
                if key in result:
                    update_data[key] = result[key]
            if "pain_points" in result:
                update_data["pain_points"] = result["pain_points"]
            if "talking_points" in result:
                update_data["talking_points"] = result["talking_points"]

        db.table("lead_research").update(update_data).eq("lead_id", lead_id).eq("status", "in_progress").execute()
        log.info(f"Research completed for lead {lead_id}")

    except ImportError:
        log.warning("research_agent not yet implemented, marking research as failed")
        db.table("lead_research").update({
            "status": "failed",
            "researched_at": datetime.now(timezone.utc).isoformat(),
        }).eq("lead_id", lead_id).eq("status", "in_progress").execute()

    except Exception as e:
        log.error(f"Research failed for lead {lead_id}: {e}")
        db.table("lead_research").update({
            "status": "failed",
            "researched_at": datetime.now(timezone.utc).isoformat(),
        }).eq("lead_id", lead_id).eq("status", "in_progress").execute()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/{lead_id}", response_model=ResearchTriggerResponse)
async def trigger_research(lead_id: str, user: dict = Depends(get_current_user)):
    """Trigger AI research for a lead. Runs asynchronously in the background."""
    try:
        db = get_supabase_admin()

        lead_result = db.table("leads").select("id, contact_name, assigned_rep_id").eq("id", lead_id).single().execute()
        if not lead_result.data:
            raise HTTPException(status_code=404, detail="Lead not found")

        lead = lead_result.data

        if user["role"] in ("rep", "sales_rep") and lead.get("assigned_rep_id") != user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to research this lead")

        # Check if research is already in progress
        existing = (
            db.table("lead_research")
            .select("id, status")
            .eq("lead_id", lead_id)
            .eq("status", "in_progress")
            .execute()
        )
        if existing.data:
            return ResearchTriggerResponse(
                message="Research is already in progress for this lead",
                lead_id=lead_id,
                status="in_progress",
            )

        now = datetime.now(timezone.utc).isoformat()

        # Upsert research record (lead_id is UNIQUE in lead_research)
        # Delete any existing failed/complete record first, then insert fresh
        db.table("lead_research").delete().eq("lead_id", lead_id).execute()
        db.table("lead_research").insert({
            "lead_id": lead_id,
            "status": "in_progress",
            "model_used": "claude-sonnet",
            "researched_at": now,
        }).execute()

        asyncio.create_task(_run_research_background(lead_id, user["id"]))

        return ResearchTriggerResponse(
            message="Research started. Check status for updates.",
            lead_id=lead_id,
            status="in_progress",
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error triggering research for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start research")


@router.get("/{lead_id}")
async def get_research(lead_id: str, user: dict = Depends(get_current_user)):
    """Get the latest research results for a lead."""
    try:
        db = get_supabase_admin()

        lead_result = db.table("leads").select("id, assigned_rep_id").eq("id", lead_id).single().execute()
        if not lead_result.data:
            raise HTTPException(status_code=404, detail="Lead not found")

        if user["role"] in ("rep", "sales_rep") and lead_result.data.get("assigned_rep_id") != user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to view this lead's research")

        result = (
            db.table("lead_research")
            .select("*")
            .eq("lead_id", lead_id)
            .limit(1)
            .execute()
        )

        if not result.data:
            return {
                "lead_id": lead_id,
                "status": "not_found",
                "message": "No research has been run for this lead yet.",
                "research": None,
            }

        research = result.data[0]

        return {
            "lead_id": lead_id,
            "status": research.get("status", "unknown"),
            "research": research,
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error fetching research for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch research results")


@router.get("/{lead_id}/status", response_model=ResearchStatusResponse)
async def research_status(lead_id: str, user: dict = Depends(get_current_user)):
    """Check the status of research for a lead."""
    try:
        db = get_supabase_admin()

        lead_result = db.table("leads").select("id, assigned_rep_id").eq("id", lead_id).single().execute()
        if not lead_result.data:
            raise HTTPException(status_code=404, detail="Lead not found")

        if user["role"] in ("rep", "sales_rep") and lead_result.data.get("assigned_rep_id") != user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        result = (
            db.table("lead_research")
            .select("status, researched_at")
            .eq("lead_id", lead_id)
            .limit(1)
            .execute()
        )

        if not result.data:
            return ResearchStatusResponse(lead_id=lead_id, status="not_found")

        record = result.data[0]
        return ResearchStatusResponse(
            lead_id=lead_id,
            status=record.get("status", "unknown"),
            researched_at=record.get("researched_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error checking research status for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to check research status")

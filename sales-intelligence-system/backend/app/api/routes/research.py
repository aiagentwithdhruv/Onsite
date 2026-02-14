"""Research routes — trigger and retrieve AI research for leads."""

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
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
    status: str  # in_progress, completed, failed, not_found
    started_at: str | None = None
    completed_at: str | None = None


# ---------------------------------------------------------------------------
# Background task wrapper
# ---------------------------------------------------------------------------

async def _run_research_background(lead_id: str, user_id: str):
    """Run the research agent in the background and update status on completion."""
    db = get_supabase_admin()
    try:
        # Import here to avoid circular imports and allow graceful failure
        from app.agents.research_agent import run_research_agent

        result = await run_research_agent(lead_id=lead_id, triggered_by=user_id)

        # Update research status to completed
        db.table("research_results").update({
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "results": result if isinstance(result, dict) else {"summary": str(result)},
        }).eq("lead_id", lead_id).eq("status", "in_progress").execute()

        log.info(f"Research completed for lead {lead_id}")

    except ImportError:
        log.warning("research_agent not yet implemented, marking research as failed")
        db.table("research_results").update({
            "status": "failed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "error_message": "Research agent not yet implemented",
        }).eq("lead_id", lead_id).eq("status", "in_progress").execute()

    except Exception as e:
        log.error(f"Research failed for lead {lead_id}: {e}")
        db.table("research_results").update({
            "status": "failed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "error_message": str(e)[:500],
        }).eq("lead_id", lead_id).eq("status", "in_progress").execute()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/{lead_id}", response_model=ResearchTriggerResponse)
async def trigger_research(lead_id: str, user: dict = Depends(get_current_user)):
    """Trigger AI research for a lead. Runs asynchronously in the background.

    Returns immediately with a status of 'in_progress'. Poll GET /{lead_id}/status
    to check completion.
    """
    try:
        db = get_supabase_admin()

        # Verify lead exists
        lead_result = db.table("leads").select("id, name, assigned_to").eq("id", lead_id).single().execute()
        if not lead_result.data:
            raise HTTPException(status_code=404, detail="Lead not found")

        lead = lead_result.data

        # Reps can only research their own leads
        if user["role"] in ("rep", "sales_rep") and lead.get("assigned_to") != user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to research this lead")

        # Check if research is already in progress
        existing = (
            db.table("research_results")
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

        # Create a research_results record with in_progress status
        db.table("research_results").insert({
            "lead_id": lead_id,
            "status": "in_progress",
            "triggered_by": user["id"],
            "started_at": now,
            "created_at": now,
        }).execute()

        # Kick off background research
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
    """Get the latest completed research results for a lead."""
    try:
        db = get_supabase_admin()

        # Verify lead exists and user has access
        lead_result = db.table("leads").select("id, assigned_to").eq("id", lead_id).single().execute()
        if not lead_result.data:
            raise HTTPException(status_code=404, detail="Lead not found")

        if user["role"] in ("rep", "sales_rep") and lead_result.data.get("assigned_to") != user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to view this lead's research")

        # Get the most recent research result (completed or in_progress)
        result = (
            db.table("research_results")
            .select("*")
            .eq("lead_id", lead_id)
            .order("created_at", desc=True)
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
    """Check the status of research for a lead (in_progress, completed, failed, not_found)."""
    try:
        db = get_supabase_admin()

        # Verify lead exists
        lead_result = db.table("leads").select("id, assigned_to").eq("id", lead_id).single().execute()
        if not lead_result.data:
            raise HTTPException(status_code=404, detail="Lead not found")

        if user["role"] in ("rep", "sales_rep") and lead_result.data.get("assigned_to") != user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to check this lead's research status")

        # Get most recent research record
        result = (
            db.table("research_results")
            .select("status, started_at, completed_at")
            .eq("lead_id", lead_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not result.data:
            return ResearchStatusResponse(
                lead_id=lead_id,
                status="not_found",
            )

        record = result.data[0]
        return ResearchStatusResponse(
            lead_id=lead_id,
            status=record.get("status", "unknown"),
            started_at=record.get("started_at"),
            completed_at=record.get("completed_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error checking research status for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to check research status")

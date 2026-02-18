"""Daily brief routes — today's brief, history, manager access to rep briefs."""

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.auth import get_current_user, require_manager
from app.core.supabase_client import get_supabase_admin

log = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class BriefHistoryResponse(BaseModel):
    briefs: list[dict]
    total: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _today_str() -> str:
    """Return today's date as ISO string."""
    return date.today().isoformat()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/today")
async def get_today_brief(user: dict = Depends(get_current_user)):
    """Get the current user's daily brief for today."""
    try:
        db = get_supabase_admin()
        today = _today_str()

        result = (
            db.table("daily_briefs")
            .select("*")
            .eq("rep_id", user["id"])
            .eq("brief_date", today)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not result.data:
            return {
                "brief": None,
                "message": "No brief generated for today yet. Briefs are generated each morning.",
                "brief_date": today,
            }

        return {
            "brief": result.data[0],
            "brief_date": today,
        }

    except Exception as e:
        log.error(f"Error fetching today's brief: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch daily brief")


@router.get("/history", response_model=BriefHistoryResponse)
async def get_brief_history(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(14, ge=1, le=90),
    user: dict = Depends(get_current_user),
):
    """List past daily briefs for the current user with optional date filtering."""
    try:
        db = get_supabase_admin()
        offset = (page - 1) * per_page

        query = (
            db.table("daily_briefs")
            .select("*", count="exact")
            .eq("rep_id", user["id"])
        )

        if date_from:
            query = query.gte("brief_date", date_from)
        if date_to:
            query = query.lte("brief_date", date_to)

        query = query.order("brief_date", desc=True).range(offset, offset + per_page - 1)

        result = query.execute()

        total = result.count if result.count is not None else 0

        return BriefHistoryResponse(
            briefs=result.data or [],
            total=total,
        )

    except Exception as e:
        log.error(f"Error fetching brief history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch brief history")


@router.get("/{rep_id}/today")
async def get_rep_brief_today(rep_id: str, user: dict = Depends(require_manager)):
    """Manager-only: Get a specific rep's daily brief for today."""
    try:
        db = get_supabase_admin()
        today = _today_str()

        # Verify the rep exists
        rep_result = db.table("users").select("id, name, role").eq("id", rep_id).single().execute()
        if not rep_result.data:
            raise HTTPException(status_code=404, detail="Rep not found")

        # Fetch their brief
        result = (
            db.table("daily_briefs")
            .select("*")
            .eq("rep_id", rep_id)
            .eq("brief_date", today)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        rep_info = rep_result.data

        if not result.data:
            return {
                "brief": None,
                "rep": {
                    "id": rep_info["id"],
                    "name": rep_info.get("name"),
                    "role": rep_info.get("role"),
                },
                "message": f"No brief generated for {rep_info.get('name', 'this rep')} today.",
                "brief_date": today,
            }

        return {
            "brief": result.data[0],
            "rep": {
                "id": rep_info["id"],
                "name": rep_info.get("name"),
                "role": rep_info.get("role"),
            },
            "brief_date": today,
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error fetching rep {rep_id} brief: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch rep's daily brief")

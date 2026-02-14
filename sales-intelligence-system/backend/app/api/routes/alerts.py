"""Alert routes — list alerts, mark as read, unread count."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.supabase_client import get_supabase_admin

log = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class AlertListResponse(BaseModel):
    alerts: list[dict]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    unread_count: int


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False, description="Show only unread alerts"),
    user: dict = Depends(get_current_user),
):
    """List alerts for the current user, ordered with unread first then by recency."""
    try:
        db = get_supabase_admin()
        offset = (page - 1) * per_page

        # Build query
        query = (
            db.table("alerts")
            .select("*", count="exact")
            .eq("user_id", user["id"])
        )

        if unread_only:
            query = query.eq("is_read", False)

        # Order: unread first, then most recent
        query = (
            query
            .order("is_read", desc=False)  # False (unread) before True (read)
            .order("created_at", desc=True)
            .range(offset, offset + per_page - 1)
        )

        result = query.execute()
        total = result.count if result.count is not None else 0

        # Get unread count separately for the badge
        unread_result = (
            db.table("alerts")
            .select("id", count="exact")
            .eq("user_id", user["id"])
            .eq("is_read", False)
            .execute()
        )
        unread_count = unread_result.count if unread_result.count is not None else 0

        return AlertListResponse(
            alerts=result.data or [],
            total=total,
            unread_count=unread_count,
        )

    except Exception as e:
        log.error(f"Error listing alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch alerts")


@router.patch("/{alert_id}/read")
async def mark_alert_read(alert_id: str, user: dict = Depends(get_current_user)):
    """Mark a single alert as read."""
    try:
        db = get_supabase_admin()

        # Verify the alert belongs to this user
        alert_result = (
            db.table("alerts")
            .select("id, user_id, is_read")
            .eq("id", alert_id)
            .single()
            .execute()
        )

        if not alert_result.data:
            raise HTTPException(status_code=404, detail="Alert not found")

        if alert_result.data["user_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to modify this alert")

        if alert_result.data.get("is_read"):
            return {"message": "Alert already marked as read", "alert_id": alert_id}

        # Mark as read
        db.table("alerts").update({
            "is_read": True,
            "read_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", alert_id).execute()

        return {"message": "Alert marked as read", "alert_id": alert_id}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error marking alert {alert_id} as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark alert as read")


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(user: dict = Depends(get_current_user)):
    """Return the count of unread alerts for the current user (for notification badges)."""
    try:
        db = get_supabase_admin()

        result = (
            db.table("alerts")
            .select("id", count="exact")
            .eq("user_id", user["id"])
            .eq("is_read", False)
            .execute()
        )

        count = result.count if result.count is not None else 0

        return UnreadCountResponse(unread_count=count)

    except Exception as e:
        log.error(f"Error fetching unread count: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch unread count")

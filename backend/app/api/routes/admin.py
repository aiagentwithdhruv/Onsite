"""Admin routes — user management, sync status, AI usage tracking."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.auth import get_current_user, require_admin, require_manager
from app.core.supabase_client import get_supabase_admin

log = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class CreateUserRequest(BaseModel):
    email: str
    name: str
    role: str = "rep"
    team: str | None = None
    password: str


class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    team: Optional[str] = None
    is_active: Optional[bool] = None
    name: Optional[str] = None


VALID_ROLES = {"rep", "team_lead", "manager", "founder", "admin"}


# ---------------------------------------------------------------------------
# Routes: User Management
# ---------------------------------------------------------------------------

@router.get("/users")
async def list_users(
    role_filter: Optional[str] = Query(None),
    active_only: bool = Query(False),
    user: dict = Depends(require_manager),
):
    """List all users in the system. Managers and admins only."""
    try:
        db = get_supabase_admin()
        query = db.table("users").select("*")

        if role_filter:
            query = query.eq("role", role_filter)
        if active_only:
            query = query.eq("is_active", True)

        query = query.order("created_at", desc=True)
        result = query.execute()

        return {"users": result.data or [], "total": len(result.data or [])}

    except Exception as e:
        log.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")


@router.post("/users")
async def create_user(payload: CreateUserRequest, user: dict = Depends(require_admin)):
    """Create a new user. Admin only."""
    if payload.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role '{payload.role}'. Valid: {sorted(VALID_ROLES)}")

    try:
        db = get_supabase_admin()

        existing = db.table("users").select("id").eq("email", payload.email).execute()
        if existing.data:
            raise HTTPException(status_code=409, detail="A user with this email already exists")

        # Create in Supabase Auth
        auth_response = db.auth.admin.create_user({
            "email": payload.email,
            "password": payload.password,
            "email_confirm": True,
        })

        if not auth_response.user:
            raise HTTPException(status_code=500, detail="Failed to create auth user")

        supabase_user_id = str(auth_response.user.id)
        now = datetime.now(timezone.utc).isoformat()

        user_record = {
            "auth_id": supabase_user_id,
            "email": payload.email,
            "name": payload.name,
            "role": payload.role,
            "team": payload.team,
            "is_active": True,
            "created_at": now,
        }

        db.table("users").insert(user_record).execute()

        return {"message": f"User '{payload.name}' created successfully", "user": user_record}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.patch("/users/{user_id}")
async def update_user(user_id: str, payload: UpdateUserRequest, user: dict = Depends(require_admin)):
    """Update a user's role, team, active status, or name. Admin only."""
    try:
        db = get_supabase_admin()

        existing = db.table("users").select("id, email, role").eq("id", user_id).single().execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="User not found")

        if user_id == user["id"] and payload.is_active is False:
            raise HTTPException(status_code=400, detail="You cannot deactivate your own account")

        if user_id == user["id"] and payload.role and payload.role not in ("founder", "admin"):
            raise HTTPException(status_code=400, detail="You cannot remove your own admin access")

        if payload.role and payload.role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail=f"Invalid role '{payload.role}'.")

        update_data = {}
        if payload.role is not None:
            update_data["role"] = payload.role
        if payload.team is not None:
            update_data["team"] = payload.team
        if payload.is_active is not None:
            update_data["is_active"] = payload.is_active
        if payload.name is not None:
            update_data["name"] = payload.name

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        db.table("users").update(update_data).eq("id", user_id).execute()

        updated = db.table("users").select("*").eq("id", user_id).single().execute()

        return {"message": "User updated successfully", "user": updated.data}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")


# ---------------------------------------------------------------------------
# Routes: Zoho Sync
# ---------------------------------------------------------------------------

@router.get("/sync-status")
async def get_sync_status(user: dict = Depends(require_manager)):
    """Show last Zoho sync times per module."""
    try:
        db = get_supabase_admin()

        result = (
            db.table("sync_state")
            .select("*")
            .order("last_sync_at", desc=True)
            .execute()
        )

        if not result.data:
            return {"sync_status": [], "message": "No sync records found. Syncs may not have run yet."}

        latest_by_module: dict[str, dict] = {}
        for record in result.data:
            module = record.get("module", "unknown")
            if module not in latest_by_module:
                latest_by_module[module] = record

        sync_status = []
        for module, record in sorted(latest_by_module.items()):
            sync_status.append({
                "module": module,
                "last_sync_at": record.get("last_sync_at"),
                "status": record.get("status", "unknown"),
                "records_synced": record.get("records_synced", 0),
                "error_message": record.get("error_message"),
            })

        return {"sync_status": sync_status}

    except Exception as e:
        log.error(f"Error fetching sync status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch sync status")


@router.post("/sync/trigger")
async def trigger_sync(user: dict = Depends(require_admin)):
    """Manually trigger a Zoho CRM sync. Admin only."""
    try:
        db = get_supabase_admin()
        now = datetime.now(timezone.utc).isoformat()

        db.table("sync_state").insert({
            "module": "manual_trigger",
            "status": "pending",
            "last_sync_at": now,
            "records_synced": 0,
        }).execute()

        return {
            "message": "Sync trigger recorded. Zoho sync will be connected once credentials are configured.",
            "triggered_by": user["id"],
            "triggered_at": now,
            "status": "pending",
        }

    except Exception as e:
        log.error(f"Error triggering sync: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger sync")


# ---------------------------------------------------------------------------
# Routes: AI Usage
# ---------------------------------------------------------------------------

@router.get("/ai-usage")
async def get_ai_usage(user: dict = Depends(require_manager)):
    """Show AI cost summary: today, this week, this month."""
    try:
        db = get_supabase_admin()
        now = datetime.now(timezone.utc)

        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        week_start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

        def _aggregate_usage(data: list[dict]) -> dict:
            total_calls = len(data)
            total_input = sum(r.get("input_tokens", 0) for r in data)
            total_output = sum(r.get("output_tokens", 0) for r in data)
            total_cost = sum(float(r.get("cost_usd", 0)) for r in data)

            by_agent: dict[str, dict] = {}
            for r in data:
                agent = r.get("agent_type", "unknown")
                if agent not in by_agent:
                    by_agent[agent] = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
                by_agent[agent]["calls"] += 1
                by_agent[agent]["input_tokens"] += r.get("input_tokens", 0)
                by_agent[agent]["output_tokens"] += r.get("output_tokens", 0)
                by_agent[agent]["cost_usd"] += float(r.get("cost_usd", 0))

            for agent_data in by_agent.values():
                agent_data["cost_usd"] = round(agent_data["cost_usd"], 4)

            return {
                "total_calls": total_calls,
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_cost_usd": round(total_cost, 4),
                "by_agent": [{"agent_type": k, **v} for k, v in sorted(by_agent.items(), key=lambda x: x[1]["cost_usd"], reverse=True)],
            }

        month_result = (
            db.table("ai_usage_log")
            .select("*")
            .gte("created_at", month_start)
            .eq("success", True)
            .execute()
        )
        month_data = month_result.data or []

        today_data = [r for r in month_data if r.get("created_at", "") >= today_start]
        week_data = [r for r in month_data if r.get("created_at", "") >= week_start]

        return {
            "today": _aggregate_usage(today_data),
            "this_week": _aggregate_usage(week_data),
            "this_month": _aggregate_usage(month_data),
        }

    except Exception as e:
        log.error(f"Error fetching AI usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch AI usage data")

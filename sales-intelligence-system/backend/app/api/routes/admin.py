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
    full_name: str
    role: str = "rep"  # rep, manager, founder, admin
    team: str | None = None
    password: str  # Initial password — user should change on first login


class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    team: Optional[str] = None
    is_active: Optional[bool] = None
    full_name: Optional[str] = None


class UserItem(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    role: str
    team: str | None = None
    is_active: bool = True
    created_at: str | None = None


class SyncStatusItem(BaseModel):
    module: str
    last_sync_at: str | None = None
    status: str
    records_synced: int = 0


class AIUsageSummary(BaseModel):
    period: str
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    by_agent: list[dict] = []


VALID_ROLES = {"rep", "sales_rep", "manager", "founder", "admin"}


# ---------------------------------------------------------------------------
# Routes: User Management
# ---------------------------------------------------------------------------

@router.get("/users")
async def list_users(
    role_filter: Optional[str] = Query(None, description="Filter by role"),
    active_only: bool = Query(False, description="Show only active users"),
    user: dict = Depends(require_manager),
):
    """List all users in the system. Accessible by managers and admins."""
    try:
        db = get_supabase_admin()

        query = db.table("users").select("*")

        if role_filter:
            query = query.eq("role", role_filter)

        if active_only:
            query = query.eq("is_active", True)

        query = query.order("created_at", desc=True)

        result = query.execute()

        return {
            "users": result.data or [],
            "total": len(result.data or []),
        }

    except Exception as e:
        log.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")


@router.post("/users")
async def create_user(payload: CreateUserRequest, user: dict = Depends(require_admin)):
    """Create a new user. Admin only.

    Creates the user in Supabase Auth and then inserts a record in the users table.
    """
    if payload.role not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{payload.role}'. Valid roles: {sorted(VALID_ROLES)}",
        )

    try:
        db = get_supabase_admin()

        # Check if email already exists in users table
        existing = (
            db.table("users")
            .select("id")
            .eq("email", payload.email)
            .execute()
        )
        if existing.data:
            raise HTTPException(status_code=409, detail="A user with this email already exists")

        # Create in Supabase Auth
        auth_response = db.auth.admin.create_user({
            "email": payload.email,
            "password": payload.password,
            "email_confirm": True,  # Auto-confirm since admin is creating
        })

        if not auth_response.user:
            raise HTTPException(status_code=500, detail="Failed to create auth user")

        supabase_user_id = str(auth_response.user.id)
        now = datetime.now(timezone.utc).isoformat()

        # Insert into our users table
        user_record = {
            "id": supabase_user_id,
            "email": payload.email,
            "full_name": payload.full_name,
            "role": payload.role,
            "team": payload.team,
            "is_active": True,
            "created_at": now,
        }

        db.table("users").insert(user_record).execute()

        return {
            "message": f"User '{payload.full_name}' created successfully",
            "user": user_record,
        }

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

        # Verify user exists
        existing = db.table("users").select("id, email, role").eq("id", user_id).single().execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="User not found")

        # Prevent self-deactivation
        if user_id == user["id"] and payload.is_active is False:
            raise HTTPException(status_code=400, detail="You cannot deactivate your own account")

        # Prevent self-demotion from admin
        if user_id == user["id"] and payload.role and payload.role not in ("founder", "admin"):
            raise HTTPException(status_code=400, detail="You cannot remove your own admin access")

        # Validate role if provided
        if payload.role and payload.role not in VALID_ROLES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role '{payload.role}'. Valid roles: {sorted(VALID_ROLES)}",
            )

        # Build update dict with only provided fields
        update_data = {}
        if payload.role is not None:
            update_data["role"] = payload.role
        if payload.team is not None:
            update_data["team"] = payload.team
        if payload.is_active is not None:
            update_data["is_active"] = payload.is_active
        if payload.full_name is not None:
            update_data["full_name"] = payload.full_name

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        db.table("users").update(update_data).eq("id", user_id).execute()

        # Fetch updated record
        updated = db.table("users").select("*").eq("id", user_id).single().execute()

        return {
            "message": "User updated successfully",
            "user": updated.data,
        }

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
    """Show last Zoho sync times per module (Leads, Contacts, Deals, Activities)."""
    try:
        db = get_supabase_admin()

        result = (
            db.table("sync_log")
            .select("*")
            .order("synced_at", desc=True)
            .execute()
        )

        if not result.data:
            return {
                "sync_status": [],
                "message": "No sync records found. Syncs may not have run yet.",
            }

        # Get the most recent sync per module
        latest_by_module: dict[str, dict] = {}
        for record in result.data:
            module = record.get("module", "unknown")
            if module not in latest_by_module:
                latest_by_module[module] = record

        sync_status = []
        for module, record in sorted(latest_by_module.items()):
            sync_status.append({
                "module": module,
                "last_sync_at": record.get("synced_at"),
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
    """Manually trigger a Zoho CRM sync. Admin only.

    TODO: Connect to actual Zoho sync service once credentials are configured.
    Currently returns a placeholder response.
    """
    try:
        db = get_supabase_admin()
        now = datetime.now(timezone.utc).isoformat()

        # Log the manual trigger attempt
        db.table("sync_log").insert({
            "module": "manual_trigger",
            "status": "pending",
            "triggered_by": user["id"],
            "synced_at": now,
            "records_synced": 0,
        }).execute()

        # TODO: Once Zoho credentials are configured, import and call the sync service:
        # from app.services.zoho_sync import trigger_full_sync
        # asyncio.create_task(trigger_full_sync(triggered_by=user["id"]))

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
    """Show AI cost summary: today, this week, this month.

    Aggregates data from the ai_usage_log table.
    """
    try:
        db = get_supabase_admin()
        now = datetime.now(timezone.utc)

        # Define time boundaries
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        week_start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

        def _aggregate_usage(data: list[dict]) -> dict:
            """Aggregate usage records into a summary."""
            total_calls = len(data)
            total_input = sum(r.get("input_tokens", 0) for r in data)
            total_output = sum(r.get("output_tokens", 0) for r in data)
            total_cost = sum(float(r.get("cost_usd", 0)) for r in data)

            # Breakdown by agent type
            by_agent: dict[str, dict] = {}
            for r in data:
                agent = r.get("agent_type", "unknown")
                if agent not in by_agent:
                    by_agent[agent] = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
                by_agent[agent]["calls"] += 1
                by_agent[agent]["input_tokens"] += r.get("input_tokens", 0)
                by_agent[agent]["output_tokens"] += r.get("output_tokens", 0)
                by_agent[agent]["cost_usd"] += float(r.get("cost_usd", 0))

            # Round costs
            for agent_data in by_agent.values():
                agent_data["cost_usd"] = round(agent_data["cost_usd"], 4)

            return {
                "total_calls": total_calls,
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_cost_usd": round(total_cost, 4),
                "by_agent": [
                    {"agent_type": k, **v}
                    for k, v in sorted(by_agent.items(), key=lambda x: x[1]["cost_usd"], reverse=True)
                ],
            }

        # Fetch this month's data (covers today and this week too)
        month_result = (
            db.table("ai_usage_log")
            .select("*")
            .gte("created_at", month_start)
            .eq("success", True)
            .execute()
        )
        month_data = month_result.data or []

        # Filter subsets for today and this week
        today_data = [r for r in month_data if r.get("created_at", "") >= today_start]
        week_data = [r for r in month_data if r.get("created_at", "") >= week_start]

        # Breakdown by model for the month
        model_breakdown: dict[str, dict] = {}
        for r in month_data:
            model = r.get("model", "unknown")
            if model not in model_breakdown:
                model_breakdown[model] = {"calls": 0, "cost_usd": 0.0}
            model_breakdown[model]["calls"] += 1
            model_breakdown[model]["cost_usd"] += float(r.get("cost_usd", 0))

        for model_data in model_breakdown.values():
            model_data["cost_usd"] = round(model_data["cost_usd"], 4)

        return {
            "today": _aggregate_usage(today_data),
            "this_week": _aggregate_usage(week_data),
            "this_month": _aggregate_usage(month_data),
            "model_breakdown": [
                {"model": k, **v}
                for k, v in sorted(model_breakdown.items(), key=lambda x: x[1]["cost_usd"], reverse=True)
            ],
        }

    except Exception as e:
        log.error(f"Error fetching AI usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch AI usage data")

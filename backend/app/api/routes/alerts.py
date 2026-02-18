"""Alert routes — list alerts, mark as read, notification preferences, Telegram link."""

import logging
import secrets
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.supabase_client import get_supabase_admin
from app.services.telegram import get_bot_username

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
@router.get("", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False, description="Show only unread alerts"),
    user: dict = Depends(get_current_user),
):
    """List alerts for the current user."""
    try:
        db = get_supabase_admin()
        offset = (page - 1) * per_page

        query = (
            db.table("alerts")
            .select("*", count="exact")
            .eq("target_user_id", user["id"])
        )

        if unread_only:
            query = query.is_("read_at", "null")

        query = (
            query
            .order("sent_at", desc=True)
            .range(offset, offset + per_page - 1)
        )

        result = query.execute()
        total = result.count if result.count is not None else 0

        # Get unread count
        unread_result = (
            db.table("alerts")
            .select("id", count="exact")
            .eq("target_user_id", user["id"])
            .is_("read_at", "null")
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

        alert_result = (
            db.table("alerts")
            .select("id, target_user_id, read_at")
            .eq("id", alert_id)
            .single()
            .execute()
        )

        if not alert_result.data:
            raise HTTPException(status_code=404, detail="Alert not found")

        if alert_result.data["target_user_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to modify this alert")

        if alert_result.data.get("read_at"):
            return {"message": "Alert already marked as read", "alert_id": alert_id}

        db.table("alerts").update({
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
    """Return the count of unread alerts for the current user."""
    try:
        db = get_supabase_admin()

        result = (
            db.table("alerts")
            .select("id", count="exact")
            .eq("target_user_id", user["id"])
            .is_("read_at", "null")
            .execute()
        )

        count = result.count if result.count is not None else 0

        return UnreadCountResponse(unread_count=count)

    except Exception as e:
        log.error(f"Error fetching unread count: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch unread count")


# ---------------------------------------------------------------------------
# Notification delivery (Telegram, WhatsApp, Email)
# ---------------------------------------------------------------------------

class NotificationPreferencesResponse(BaseModel):
    notify_via_telegram: bool
    notify_via_discord: bool
    notify_via_whatsapp: bool
    notify_via_email: bool
    telegram_linked: bool
    discord_linked: bool


class NotificationPreferencesUpdate(BaseModel):
    notify_via_telegram: bool | None = None
    notify_via_discord: bool | None = None
    notify_via_whatsapp: bool | None = None
    notify_via_email: bool | None = None
    discord_webhook_url: str | None = None


@router.get("/notification-preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(user: dict = Depends(get_current_user)):
    """Get current user's alert delivery preferences."""
    return NotificationPreferencesResponse(
        notify_via_telegram=bool(user.get("notify_via_telegram")),
        notify_via_discord=bool(user.get("notify_via_discord")),
        notify_via_whatsapp=bool(user.get("notify_via_whatsapp", True)),
        notify_via_email=bool(user.get("notify_via_email", True)),
        telegram_linked=bool(user.get("telegram_chat_id")),
        discord_linked=bool(user.get("discord_webhook_url")),
    )


@router.patch("/notification-preferences")
async def update_notification_preferences(
    body: NotificationPreferencesUpdate,
    user: dict = Depends(get_current_user),
):
    """Update which channels to use for smart alerts (Telegram, WhatsApp, Email)."""
    try:
        db = get_supabase_admin()
        updates = {}
        if body.notify_via_telegram is not None:
            updates["notify_via_telegram"] = body.notify_via_telegram
        if body.notify_via_discord is not None:
            updates["notify_via_discord"] = body.notify_via_discord
        if body.notify_via_whatsapp is not None:
            updates["notify_via_whatsapp"] = body.notify_via_whatsapp
        if body.notify_via_email is not None:
            updates["notify_via_email"] = body.notify_via_email
        if body.discord_webhook_url is not None:
            updates["discord_webhook_url"] = (body.discord_webhook_url or "").strip() or None
        if not updates:
            return {"message": "No changes", "preferences": user}
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        db.table("users").update(updates).eq("id", user["id"]).execute()
        return {"message": "Updated", "preferences": {**user, **updates}}
    except Exception as e:
        log.error("Update notification prefs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update preferences")


@router.get("/telegram-link-token")
async def get_telegram_link_token(user: dict = Depends(get_current_user)):
    """Generate a one-time token and return the Telegram link. User opens link, sends /start to bot; we link chat_id."""
    try:
        db = get_supabase_admin()
        token = secrets.token_urlsafe(12)
        expires = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
        db.table("telegram_link_tokens").insert({
            "token": token,
            "user_id": user["id"],
            "expires_at": expires,
        }).execute()

        bot_username = get_bot_username()
        link = f"https://t.me/{bot_username}?start={token}" if bot_username else None
        return {
            "token": token,
            "link": link,
            "bot_username": bot_username,
            "expires_in_minutes": 15,
            "instructions": "Open the link and tap Start in Telegram. Your account will be linked for alert delivery.",
        }
    except Exception as e:
        log.error("Telegram link token: %s", e)
        raise HTTPException(status_code=500, detail="Failed to generate link")


@router.post("/telegram-webhook")
async def telegram_webhook(payload: dict):
    """Telegram Bot webhook: on /start <token>, link chat_id to user and enable Telegram alerts."""
    try:
        message = (payload.get("message") or {}).get("text") or ""
        chat_id = (payload.get("message") or {}).get("chat", {}).get("id")
        if not message.strip().lower().startswith("/start"):
            return {"ok": True}
        parts = message.strip().split()
        token = parts[1] if len(parts) > 1 else None
        if not token or not chat_id:
            return {"ok": True}

        db = get_supabase_admin()
        now_iso = datetime.now(timezone.utc).isoformat()
        row = db.table("telegram_link_tokens").select("user_id").eq("token", token).gt("expires_at", now_iso).maybe_single().execute()
        if not row.data:
            return {"ok": True}

        user_id = row.data["user_id"]
        db.table("users").update({
            "telegram_chat_id": str(chat_id),
            "notify_via_telegram": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", user_id).execute()
        db.table("telegram_link_tokens").delete().eq("token", token).execute()

        # Optional: send reply via Telegram
        from app.services.telegram import send_telegram_message
        await send_telegram_message(str(chat_id), "✅ Linked! You'll receive Onsite smart alerts here.")

        return {"ok": True}
    except Exception as e:
        log.exception("Telegram webhook error")
        return {"ok": True}

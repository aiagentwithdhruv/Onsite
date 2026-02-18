"""Deliver smart alerts to users via Telegram, Discord, WhatsApp, and Email."""

import logging
from app.core.supabase_client import get_supabase_admin
from app.services.telegram import send_telegram_message
from app.services.discord import send_discord_webhook
from app.services.whatsapp import send_whatsapp_message
from app.services.email import send_email

log = logging.getLogger(__name__)


# Template constants for consistent notifications (2–3 per day)
_SEP = "─────────────────"
_HEADER = "📬 ONSITE"


def _format_alert_message(alert: dict) -> str:
    """Structured single alert for Telegram/WhatsApp; keep under ~4k chars."""
    title = (alert.get("title") or alert.get("message") or "Alert")[:200]
    msg = (alert.get("message") or "").strip()
    severity = (alert.get("severity") or "medium").upper()
    agent = (alert.get("agent_name") or "").strip()
    severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "ℹ️"}.get(severity.lower(), "🔔")
    lines = [
        _HEADER,
        _SEP,
        f"{severity_emoji} [{severity}] {title}",
        _SEP,
    ]
    if msg and msg != title:
        lines.append(msg[:3500])
    if agent and agent != "system":
        lines.append("")
        lines.append(f"👤 {agent}")
    return "\n".join(lines)


def format_batched_alerts(alerts: list[dict], max_items: int = 10) -> str:
    """One structured message for multiple alerts (e.g. after CSV upload). Keeps under ~4k chars."""
    if not alerts:
        return ""
    severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "ℹ️"}
    lines = [
        _HEADER,
        "📋 Smart Alerts Summary",
        _SEP,
        f"You have {len(alerts)} new alert(s).",
        "",
    ]
    for i, a in enumerate(alerts[:max_items]):
        sev = (a.get("severity") or "medium").upper()
        em = severity_emoji.get(sev.lower(), "•")
        title = (a.get("title") or a.get("message") or "Alert")[:120]
        lines.append(f"{em} {title}")
    if len(alerts) > max_items:
        lines.append(f"… and {len(alerts) - max_items} more.")
    lines.append("")
    lines.append(_SEP)
    lines.append("View all in app → Alerts")
    return "\n".join(lines)


def _channel_result(status: str, reason: str | None = None, error: str | None = None) -> dict:
    """Normalized per-channel result for API and logging."""
    out = {"status": status}
    if reason:
        out["reason"] = reason
    if error:
        out["error"] = error
    return out


async def _deliver_one_alert(alert: dict, user: dict, alert_id: str | None = None) -> dict:
    """Send one alert to one user on all enabled channels.
    Returns { telegram, discord, whatsapp, email } each as { status, reason?, error? }."""
    results = {
        "telegram": _channel_result("skipped", reason="disabled"),
        "discord": _channel_result("skipped", reason="disabled"),
        "whatsapp": _channel_result("skipped", reason="disabled"),
        "email": _channel_result("skipped", reason="disabled"),
    }
    text = _format_alert_message(alert)
    title = (alert.get("title") or alert.get("message") or "Smart Alert")[:150]
    db = get_supabase_admin()

    # 1. Telegram (priority)
    if user.get("notify_via_telegram") and user.get("telegram_chat_id"):
        r = await send_telegram_message(user["telegram_chat_id"], text)
        results["telegram"] = _channel_result(
            r.get("status", "error"),
            reason=r.get("reason"),
            error=r.get("error"),
        )
        if db:
            try:
                db.table("alert_delivery_log").insert({
                    "alert_id": alert_id,
                    "user_id": user["id"],
                    "channel": "telegram",
                    "status": r.get("status", "error"),
                    "error_message": r.get("error"),
                }).execute()
            except Exception:
                pass
    elif user.get("notify_via_telegram") and not user.get("telegram_chat_id"):
        results["telegram"] = _channel_result("skipped", reason="no_chat_id")

    # 2. Discord (webhook URL)
    if user.get("notify_via_discord") and user.get("discord_webhook_url"):
        r = await send_discord_webhook(user["discord_webhook_url"], text)
        results["discord"] = _channel_result(r.get("status", "error"), error=r.get("error"))
        if db:
            try:
                db.table("alert_delivery_log").insert({
                    "alert_id": alert_id,
                    "user_id": user["id"],
                    "channel": "discord",
                    "status": r.get("status", "error"),
                    "error_message": r.get("error"),
                }).execute()
            except Exception:
                pass

    # 3. WhatsApp
    if user.get("notify_via_whatsapp") and user.get("phone"):
        r = await send_whatsapp_message(user["phone"], text)
        results["whatsapp"] = _channel_result(r.get("status", "error"), error=r.get("error"))
        if db:
            try:
                db.table("alert_delivery_log").insert({
                    "alert_id": alert_id,
                    "user_id": user["id"],
                    "channel": "whatsapp",
                    "status": r.get("status", "error"),
                    "error_message": r.get("error"),
                }).execute()
            except Exception:
                pass

    # 4. Email
    if user.get("notify_via_email") and user.get("email"):
        body = text.replace("\n", "<br>\n")
        html = f"<div style='font-family: sans-serif; max-width: 600px;'><pre style='white-space: pre-wrap;'>{body}</pre></div>"
        r = await send_email(user["email"], f"[Onsite Alert] {title}", html, html=True)
        results["email"] = _channel_result(r.get("status", "error"), error=r.get("error"))
        if db:
            try:
                db.table("alert_delivery_log").insert({
                    "alert_id": alert_id,
                    "user_id": user["id"],
                    "channel": "email",
                    "status": r.get("status", "error"),
                    "error_message": r.get("error"),
                }).execute()
            except Exception:
                pass

    return results


async def deliver_alerts_to_users(alerts: list[dict]) -> dict:
    """For each alert, load target user and send to their enabled channels (Telegram → WhatsApp → Email).

    Args:
        alerts: List of alert dicts with target_user_id, title, message, severity, agent_name.
                Can include optional 'id' if already saved (for delivery log).

    Returns:
        { "delivered": count, "users_reached": set of user ids, "errors": list of strings }
    """
    if not alerts:
        return {"delivered": 0, "users_reached": [], "errors": []}

    db = get_supabase_admin()
    user_ids = list({a["target_user_id"] for a in alerts})
    users_result = db.table("users").select("id, email, name, phone, telegram_chat_id, notify_via_telegram, discord_webhook_url, notify_via_discord, notify_via_whatsapp, notify_via_email").in_("id", user_ids).execute()
    user_map = {u["id"]: u for u in (users_result.data or [])}

    delivered = 0
    users_reached = set()
    errors = []

    for alert in alerts:
        uid = alert.get("target_user_id")
        user = user_map.get(uid) if uid else None
        if not user:
            errors.append(f"User {uid} not found for alert")
            continue

        alert_id = alert.get("id")
        try:
            r = await _deliver_one_alert(alert, user, alert_id)
            if any((r.get(c) or {}).get("status") == "sent" for c in ("telegram", "discord", "whatsapp", "email")):
                delivered += 1
                users_reached.add(uid)
            for ch in ("telegram", "discord", "whatsapp", "email"):
                s = (r.get(ch) or {}).get("status")
                if s in ("error", "failed"):
                    err_msg = (r.get(ch) or {}).get("error") or ""
                    errors.append(f"{ch.title()} failed for {user.get('email', uid)}: {err_msg}")
        except Exception as e:
            log.exception("Delivery failed for alert to %s", user.get("email"))
            errors.append(f"Delivery error for {user.get('email', uid)}: {e}")

    log.info("Alert delivery: %s alerts, %s users reached, %s errors", len(alerts), len(users_reached), len(errors))
    return {"delivered": delivered, "users_reached": list(users_reached), "errors": errors}


async def deliver_batched_alerts_to_users(alerts: list[dict]) -> dict:
    """Send one batched message per user (2–3 notifications per day style). Groups by target_user_id."""
    if not alerts:
        return {"delivered": 0, "users_reached": [], "errors": []}
    from collections import defaultdict
    by_user: dict[str, list[dict]] = defaultdict(list)
    for a in alerts:
        uid = a.get("target_user_id")
        if uid:
            by_user[uid].append(a)
    db = get_supabase_admin()
    user_ids = list(by_user.keys())
    users_result = db.table("users").select(
        "id, email, name, phone, telegram_chat_id, notify_via_telegram, discord_webhook_url, "
        "notify_via_discord, notify_via_whatsapp, notify_via_email"
    ).in_("id", user_ids).execute()
    user_map = {u["id"]: u for u in (users_result.data or [])}
    delivered = 0
    users_reached = []
    errors = []
    for uid, user_alerts in by_user.items():
        user = user_map.get(uid)
        if not user:
            continue
        text = format_batched_alerts(user_alerts)
        if not text:
            continue
        try:
            r = await deliver_message_to_user(user, text, subject="Smart Alerts Summary")
            if any((r.get(c) or {}).get("status") == "sent" for c in ("telegram", "discord", "whatsapp", "email")):
                delivered += 1
                users_reached.append(uid)
        except Exception as e:
            log.warning("Batched alert delivery failed for %s: %s", user.get("email"), e)
            errors.append(f"{user.get('email', uid)}: {e}")
    log.info("Batched alert delivery: %s users reached, %s errors", len(users_reached), len(errors))
    return {"delivered": delivered, "users_reached": users_reached, "errors": errors}


async def deliver_message_to_user(user: dict, text: str, subject: str = "Onsite Update") -> dict:
    """Send one plain message to one user on all enabled channels (Telegram, Discord, WhatsApp, Email).
    user must have id, telegram_chat_id, discord_webhook_url, phone, email, notify_via_*.
    Returns { telegram, discord, whatsapp, email } status."""
    fake_alert = {"title": subject, "message": text, "severity": "info"}
    return await _deliver_one_alert(fake_alert, user, alert_id=None)

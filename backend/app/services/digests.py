"""Afternoon and evening digests: build and send to users from Intelligence summary + agent profiles."""

import logging
from app.core.supabase_client import get_supabase_admin
from app.services.alert_delivery import deliver_message_to_user

log = logging.getLogger(__name__)


def _load_summary_and_profiles():
    """Load dashboard_summary (with summary_by_owner) and agent_profiles from DB."""
    db = get_supabase_admin()
    summary_row = db.table("dashboard_summary").select("*").eq("id", "current").maybe_single().execute()
    if not summary_row.data:
        return None, {}, []
    full = summary_row.data
    by_owner = full.get("summary_by_owner") or {}

    profiles_row = db.table("agent_profiles").select("*").order("name").execute()
    profiles = list(profiles_row.data or [])
    return full, by_owner, profiles  # full may be used later


def _profile_for_owner(profiles: list[dict], owner_name: str) -> dict | None:
    for p in profiles:
        if (p.get("name") or "").strip() == owner_name:
            return p
    return None


def _kpis_from_summary(s: dict) -> dict:
    k = s.get("kpis") or {}
    ins = s.get("insights") or {}
    return {
        "total": k.get("total") or 0,
        "stale_30": ins.get("stale_30") or 0,
        "demo_booked": k.get("demo_booked") or 0,
        "demo_done": k.get("demo_done") or 0,
        "sale_done": k.get("sale_done") or 0,
    }


def build_afternoon_digest(owner_name: str, summary_slice: dict | None, profile: dict | None) -> str:
    """Build 'rest of day' digest for one rep."""
    name = owner_name.split()[0] if owner_name else "there"
    lines = [f"📋 Rest of day — {name}", ""]
    if not summary_slice and not profile:
        lines.append("No pipeline data loaded. Upload a CSV in Intelligence to get your digest.")
        return "\n".join(lines)

    kpis = _kpis_from_summary(summary_slice) if summary_slice else {}
    perf = (profile or {}).get("performance") or {}
    stale = perf.get("stale_30") or kpis.get("stale_30") or 0
    demo_booked = perf.get("demo_booked") or kpis.get("demo_booked") or 0
    demo_done = perf.get("demos_done") or perf.get("demo_done") or kpis.get("demo_done") or 0
    pending_demos = max(0, demo_booked - demo_done)

    lines.append(f"• Stale leads (30+ days): {stale}")
    lines.append(f"• Pending demos (booked, not done): {pending_demos}")
    next_action = perf.get("next_best_action")
    if next_action:
        lines.append("")
        lines.append(f"Next: {next_action}")
    return "\n".join(lines)


def build_evening_summary(owner_name: str, summary_slice: dict | None, profile: dict | None) -> str:
    """Build 'tomorrow prep' summary for one rep."""
    name = owner_name.split()[0] if owner_name else "there"
    lines = [f"🌙 Evening summary — {name}", ""]
    if not summary_slice and not profile:
        lines.append("No pipeline data. Upload a CSV in Intelligence to get your summary.")
        return "\n".join(lines)

    perf = (profile or {}).get("performance") or {}
    next_action = perf.get("next_best_action")
    stale = perf.get("stale_30") or 0
    total = perf.get("total_leads") or 0

    lines.append("Tomorrow:")
    lines.append(f"• {total} leads in your pipeline")
    if stale > 0:
        lines.append(f"• {stale} stale leads to follow up")
    if next_action:
        lines.append("")
        lines.append(f"Your next action: {next_action}")
    return "\n".join(lines)


async def send_afternoon_digests_to_all() -> dict:
    """Load summary + profiles, for each user with deal_owner and at least one channel enabled, build and send afternoon digest."""
    _, by_owner, profiles = _load_summary_and_profiles()
    if not by_owner and not profiles:
        log.info("Digests: no summary or profiles, skipping afternoon")
        return {"sent": 0, "errors": []}

    db = get_supabase_admin()
    users = db.table("users").select(
        "id, email, name, deal_owner_name, phone, telegram_chat_id, discord_webhook_url, "
        "notify_via_telegram, notify_via_discord, notify_via_whatsapp, notify_via_email"
    ).eq("is_active", True).execute()
    user_list = users.data or []
    sent = 0
    errors = []
    for u in user_list:
        if not (u.get("notify_via_telegram") or u.get("notify_via_discord") or u.get("notify_via_whatsapp") or u.get("notify_via_email")):
            continue
        deal_owner = (u.get("deal_owner_name") or "").strip()
        if not deal_owner:
            first = (u.get("name") or "").split()[0] or (u.get("email") or "").split("@")[0]
            matches = [n for n in (by_owner or {}) if n and (n == first or n.startswith(first + " ") or first in n)]
            deal_owner = matches[0] if len(matches) == 1 else ""
        summary_slice = (by_owner or {}).get(deal_owner) if deal_owner else None
        profile = _profile_for_owner(profiles, deal_owner) if deal_owner else None
        text = build_afternoon_digest(deal_owner or u.get("name", "there"), summary_slice, profile)
        try:
            r = await deliver_message_to_user(u, text, subject="Rest of day")
            if any(s == "sent" for s in r.values()):
                sent += 1
        except Exception as e:
            log.warning("Afternoon digest send failed for %s: %s", u.get("email"), e)
            errors.append(f"{u.get('email')}: {e}")
    log.info("Afternoon digests: sent=%s, errors=%s", sent, len(errors))
    return {"sent": sent, "errors": errors}


async def send_evening_summaries_to_all() -> dict:
    """Same as afternoon but evening template."""
    _, by_owner, profiles = _load_summary_and_profiles()
    if not by_owner and not profiles:
        log.info("Digests: no summary or profiles, skipping evening")
        return {"sent": 0, "errors": []}

    db = get_supabase_admin()
    users = db.table("users").select(
        "id, email, name, deal_owner_name, phone, telegram_chat_id, discord_webhook_url, "
        "notify_via_telegram, notify_via_discord, notify_via_whatsapp, notify_via_email"
    ).eq("is_active", True).execute()
    user_list = users.data or []
    sent = 0
    errors = []
    for u in user_list:
        if not (u.get("notify_via_telegram") or u.get("notify_via_discord") or u.get("notify_via_whatsapp") or u.get("notify_via_email")):
            continue
        deal_owner = (u.get("deal_owner_name") or "").strip()
        if not deal_owner:
            first = (u.get("name") or "").split()[0] or (u.get("email") or "").split("@")[0]
            matches = [n for n in (by_owner or {}) if n and (n == first or n.startswith(first + " ") or first in n)]
            deal_owner = matches[0] if len(matches) == 1 else ""
        summary_slice = (by_owner or {}).get(deal_owner) if deal_owner else None
        profile = _profile_for_owner(profiles, deal_owner) if deal_owner else None
        text = build_evening_summary(deal_owner or u.get("name", "there"), summary_slice, profile)
        try:
            r = await deliver_message_to_user(u, text, subject="Tomorrow's focus")
            if any(s == "sent" for s in r.values()):
                sent += 1
        except Exception as e:
            log.warning("Evening summary send failed for %s: %s", u.get("email"), e)
            errors.append(f"{u.get('email')}: {e}")
    log.info("Evening summaries: sent=%s, errors=%s", sent, len(errors))
    return {"sent": sent, "errors": errors}

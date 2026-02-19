"""Generate per-rep daily briefs from Intelligence summary + agent profiles (no Zoho)."""

import logging
from datetime import date

from app.core.supabase_client import get_supabase_admin

log = logging.getLogger(__name__)


def _first_name(name: str) -> str:
    return (name or "").strip().split()[0] or ""


def _profile_for_owner(profiles: list[dict], owner_name: str) -> dict | None:
    for p in profiles:
        if (p.get("name") or "").strip() == owner_name:
            return p
    return None


def build_brief_text(owner_name: str, summary_slice: dict | None, profile: dict | None) -> str:
    """Build morning-style brief from summary + profile."""
    name = _first_name(owner_name) or "there"
    lines = [f"Good morning {name}!", ""]
    if not summary_slice and not profile:
        lines.append("No pipeline data yet. Upload a CSV in Intelligence to get your daily brief.")
        return "\n".join(lines)

    kpis = (summary_slice or {}).get("kpis") or {}
    ins = (summary_slice or {}).get("insights") or {}
    perf = (profile or {}).get("performance") or {}
    stale = perf.get("stale_30") or ins.get("stale_30") or 0
    demo_booked = perf.get("demo_booked") or kpis.get("demo_booked") or 0
    demo_done = perf.get("demos_done") or perf.get("demo_done") or kpis.get("demo_done") or 0
    pending_demos = max(0, demo_booked - demo_done)
    total = perf.get("total_leads") or kpis.get("total") or 0

    lines.append(f"You have {total} leads in your pipeline.")
    if stale > 0:
        lines.append(f"• {stale} leads untouched 30+ days — follow up today.")
    if pending_demos > 0:
        lines.append(f"• {pending_demos} demos booked but not done — complete this week.")
    next_action = perf.get("next_best_action")
    if next_action:
        lines.append("")
        lines.append(f"Next: {next_action}")
    action_items = (summary_slice or {}).get("action_items") or []
    if action_items and not next_action:
        first = action_items[0]
        if first.get("title"):
            lines.append("")
            lines.append(f"Priority: {first.get('title')}")
    return "\n".join(lines)


def generate_and_save_intelligence_briefs() -> dict:
    """Load summary + profiles, map deal_owner -> users, build brief, upsert daily_briefs.
    Returns { generated: int, errors: list }."""
    db = get_supabase_admin()
    summary_row = db.table("dashboard_summary").select("*").eq("id", "current").maybe_single().execute()
    if not summary_row.data:
        log.info("Intelligence briefs: no summary")
        return {"generated": 0, "errors": []}
    full = summary_row.data
    by_owner = full.get("summary_by_owner") or {}

    profiles_row = db.table("agent_profiles").select("*").order("name").execute()
    profiles = list(profiles_row.data or [])

    users_row = db.table("users").select("id, name, email, deal_owner_name").eq("is_active", True).execute()
    users = users_row.data or []
    today = date.today().isoformat()
    generated = 0
    errors = []

    for u in users:
        deal_owner = (u.get("deal_owner_name") or "").strip()
        if not deal_owner:
            first = _first_name(u.get("name") or "") or (u.get("email") or "").split("@")[0]
            matches = [n for n in by_owner if n and (n == first or n.startswith(first + " ") or first in n)]
            deal_owner = matches[0] if len(matches) == 1 else ""
        if not deal_owner:
            continue
        summary_slice = by_owner.get(deal_owner)
        profile = _profile_for_owner(profiles, deal_owner)
        text = build_brief_text(deal_owner, summary_slice, profile)
        try:
            db.table("daily_briefs").upsert(
                {
                    "rep_id": u["id"],
                    "brief_content": text,
                    "priority_list": [],
                    "brief_date": today,
                },
                on_conflict="rep_id,brief_date",
            ).execute()
            generated += 1
        except Exception as e:
            log.warning("Intelligence brief save failed for %s: %s", u.get("email"), e)
            errors.append(f"{u.get('email')}: {e}")

    log.info("Intelligence briefs: generated=%s, errors=%s", generated, len(errors))
    return {"generated": generated, "errors": errors}

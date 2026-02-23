"""Agent Profiles: per-person performance memory for sales reps/deal owners."""

import json
import logging
from datetime import datetime, timezone
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.auth import get_current_user
from app.core.supabase_client import get_supabase_admin

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def list_profiles(user: dict = Depends(get_current_user)):
    """List all agent profiles."""
    try:
        db = get_supabase_admin()
        result = db.table("agent_profiles").select("*").order("name").execute()
        return {"profiles": result.data or [], "total": len(result.data or [])}
    except Exception as e:
        log.error(f"List profiles error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load profiles")


@router.get("/{agent_id}")
async def get_profile(agent_id: str, user: dict = Depends(get_current_user)):
    """Get a single agent profile."""
    try:
        db = get_supabase_admin()
        result = db.table("agent_profiles").select("*").eq("id", agent_id).maybe_single().execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Agent not found")
        return result.data
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Get profile error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load profile")


class NoteInput(BaseModel):
    text: str


@router.post("/{agent_id}/notes")
async def add_note(agent_id: str, note: NoteInput, user: dict = Depends(get_current_user)):
    """Add a manual note to an agent profile."""
    try:
        db = get_supabase_admin()
        profile = db.table("agent_profiles").select("notes").eq("id", agent_id).maybe_single().execute()
        if not profile.data:
            raise HTTPException(status_code=404, detail="Agent not found")

        existing_notes = profile.data.get("notes", []) or []
        existing_notes.append({
            "text": note.text,
            "added_by": user.get("email", "unknown"),
            "added_at": datetime.now(timezone.utc).isoformat(),
        })

        db.table("agent_profiles").update({
            "notes": existing_notes,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }).eq("id", agent_id).execute()

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Add note error: {e}")
        raise HTTPException(status_code=500, detail="Failed to add note")


def _parse_date(s: str):
    if not s or not s.strip():
        return None
    for fmt in ["%b %d, %Y %I:%M %p", "%b %d, %Y", "%d %b, %Y %H:%M:%S", "%d %b, %Y"]:
        try:
            return datetime.strptime(s.strip().strip('"'), fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(s.strip())
    except Exception:
        return None


def _days_since(date_str: str) -> int | None:
    d = _parse_date(date_str)
    if not d:
        return None
    now = datetime.now(timezone.utc)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return (now - d).days


def compute_agent_profiles(rows: list[dict]) -> list[dict]:
    """Compute per-deal-owner profiles from CSV data."""
    now = datetime.now(timezone.utc).isoformat()

    owner_leads: dict[str, list[dict]] = {}
    for r in rows:
        owner = (r.get("deal_owner") or "").strip()
        if not owner or owner in ("Onsite", "Offline Campaign"):
            continue
        owner_leads.setdefault(owner, []).append(r)

    profiles = []
    for owner, leads in owner_leads.items():
        total = len(leads)
        if total < 5:
            continue

        demos = sum(1 for r in leads if r.get("demo_done") == "1")
        sales = sum(1 for r in leads if r.get("sale_done") == "1")
        purchased = sum(1 for r in leads if r.get("lead_status") == "Purchased")
        demo_booked = sum(1 for r in leads if r.get("demo_booked") == "1")
        priority = sum(1 for r in leads if r.get("lead_status") == "Priority")
        prospects = sum(1 for r in leads if r.get("is_prospect") == "1" or "Prospect" in (r.get("sales_stage") or ""))

        stale_30 = sum(1 for r in leads if (_days_since(r.get("last_touched_date_new", "")) or 0) > 30
                       and r.get("lead_status") not in ("Purchased", "Rejected", "DTA"))

        mgr = next((r.get("lead_owner_manager", "") for r in leads if r.get("lead_owner_manager")), "")

        # Revenue
        total_revenue = 0
        total_price = 0
        for r in leads:
            try: total_revenue += float((r.get("annual_revenue") or "0").replace(",", ""))
            except: pass
            try: total_price += float((r.get("price_pitched") or "0").replace(",", ""))
            except: pass

        # Top sources
        src_counts = Counter(r.get("lead_source", "").strip() for r in leads if r.get("lead_source", "").strip())
        top_sources = [s for s, _ in src_counts.most_common(5)]

        # Top regions
        reg_counts = Counter(r.get("state_mobile", "").strip() or r.get("region", "").strip() for r in leads if (r.get("state_mobile") or r.get("region", "")).strip())
        top_regions = [s for s, _ in reg_counts.most_common(5)]

        # Conversion rates
        demo_rate = round(demos / max(total, 1) * 100, 2)
        sale_rate = round(sales / max(total, 1) * 100, 2)
        demo_to_sale = round(sales / max(demos, 1) * 100, 2) if demos else 0

        # Monthly trend
        monthly: dict[str, dict] = {}
        for r in leads:
            d = _parse_date(r.get("user_date", ""))
            if not d:
                continue
            key = f"{d.year}-{d.month:02d}"
            if key not in monthly:
                monthly[key] = {"leads": 0, "demos": 0, "sales": 0}
            monthly[key]["leads"] += 1
            if r.get("demo_done") == "1": monthly[key]["demos"] += 1
            if r.get("sale_done") == "1": monthly[key]["sales"] += 1

        sorted_months = sorted(monthly.keys())[-12:]
        monthly_history = [{"month": m, **monthly[m]} for m in sorted_months]

        # Strengths & concerns (rule-based)
        strengths = []
        concerns = []

        if sale_rate > 5:
            strengths.append(f"Strong closer: {sale_rate}% conversion rate")
        if demo_to_sale > 20:
            strengths.append(f"Good demo-to-sale: {demo_to_sale}% of demos convert")
        if stale_30 == 0:
            strengths.append("No stale leads — consistent follow-up")
        if top_sources:
            strengths.append(f"Best with: {', '.join(top_sources[:2])} leads")
        if total > 200:
            strengths.append(f"High volume handler: {total} leads managed")

        if sale_rate < 2 and total > 50:
            concerns.append(f"Low conversion: {sale_rate}% — needs coaching")
        if stale_30 > 10:
            concerns.append(f"{stale_30} leads untouched 30+ days — follow-up needed")
        if demo_booked > 0 and demos / max(demo_booked, 1) < 0.5:
            concerns.append(f"Demo completion low: {demos}/{demo_booked} booked → done")
        if priority > 20:
            concerns.append(f"{priority} priority leads still pending")

        # Recent activity check
        recent_touch = sum(1 for r in leads if (_days_since(r.get("last_touched_date_new", "")) or 999) <= 7)
        if recent_touch > 10:
            strengths.append(f"Active this week: {recent_touch} leads touched in 7 days")
        elif recent_touch == 0 and total > 20:
            concerns.append("No activity in last 7 days")

        performance = {
            "total_leads": total,
            "demo_booked": demo_booked,
            "demos_done": demos,
            "sales_done": sales,
            "purchased": purchased,
            "priority": priority,
            "prospects": prospects,
            "stale_30": stale_30,
            "demo_rate": demo_rate,
            "sale_rate": sale_rate,
            "demo_to_sale": demo_to_sale,
            "total_revenue": total_revenue,
            "total_price_pitched": total_price,
            "recent_7d_touches": recent_touch,
        }

        patterns = {
            "top_sources": top_sources,
            "top_regions": top_regions,
            "avg_leads_per_month": round(total / max(len(monthly), 1), 1),
        }

        slug = owner.lower().replace(" ", "_").replace(".", "_")
        profiles.append({
            "id": slug,
            "name": owner,
            "role": "deal_owner",
            "manager": mgr,
            "performance": performance,
            "patterns": patterns,
            "strengths": strengths[:6],
            "concerns": concerns[:6],
            "monthly_history": monthly_history,
            "last_updated": now,
        })

    profiles.sort(key=lambda p: -(p["performance"]["total_leads"]))
    return profiles


def save_agent_profiles(profiles: list[dict]):
    """Upsert agent profiles to Supabase, preserving manual notes."""
    db = get_supabase_admin()

    for profile in profiles:
        existing = db.table("agent_profiles").select("notes").eq("id", profile["id"]).maybe_single().execute()
        if existing.data:
            profile["notes"] = existing.data.get("notes", []) or []

        db.table("agent_profiles").upsert(profile).execute()

    log.info(f"Saved {len(profiles)} agent profiles")

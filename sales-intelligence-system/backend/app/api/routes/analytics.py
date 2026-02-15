"""Analytics routes — rep performance, pipeline funnel, source analysis, conversion trends."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.supabase_client import get_supabase_admin

log = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_STAGES = [
    "new", "contacted", "not_reachable", "meeting_scheduled",
    "demo", "proposal", "negotiation", "won", "lost",
]


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/rep-performance")
async def rep_performance(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
):
    """Get rep performance metrics."""
    try:
        db = get_supabase_admin()
        is_manager = user["role"] in ("manager", "team_lead", "founder", "admin")

        if is_manager:
            users_result = (
                db.table("users")
                .select("id, name, role")
                .eq("is_active", True)
                .execute()
            )
            rep_ids = [u["id"] for u in (users_result.data or [])]
            rep_map = {u["id"]: u.get("name", "Unknown") for u in (users_result.data or [])}
        else:
            rep_ids = [user["id"]]
            rep_map = {user["id"]: user.get("name", "Unknown")}

        if not rep_ids:
            return {"performance": [], "period": {"date_from": date_from, "date_to": date_to}}

        performance = []

        for rep_id in rep_ids:
            query = db.table("leads").select("id, stage", count="exact").eq("assigned_rep_id", rep_id)

            if date_from:
                query = query.gte("created_at", date_from)
            if date_to:
                query = query.lte("created_at", date_to + "T23:59:59Z")

            result = query.execute()
            leads = result.data or []
            total = len(leads)

            stage_counts = {}
            for lead in leads:
                stage = lead.get("stage", "new")
                stage_counts[stage] = stage_counts.get(stage, 0) + 1

            contacted = sum(stage_counts.get(s, 0) for s in ["contacted", "demo", "meeting_scheduled", "proposal", "negotiation", "won", "lost"])
            meetings = sum(stage_counts.get(s, 0) for s in ["demo", "meeting_scheduled", "proposal", "negotiation", "won"])
            won = stage_counts.get("won", 0)
            lost = stage_counts.get("lost", 0)

            performance.append({
                "user_id": rep_id,
                "name": rep_map.get(rep_id, "Unknown"),
                "total_leads": total,
                "contacted": contacted,
                "meetings": meetings,
                "won": won,
                "lost": lost,
                "conversion_rate": _safe_rate(won, total),
            })

        performance.sort(key=lambda x: x["conversion_rate"], reverse=True)

        return {
            "performance": performance,
            "period": {"date_from": date_from, "date_to": date_to},
        }

    except Exception as e:
        log.error(f"Error fetching rep performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch rep performance")


@router.get("/pipeline-funnel")
async def pipeline_funnel(user: dict = Depends(get_current_user)):
    """Get lead counts by pipeline stage for the funnel view."""
    try:
        db = get_supabase_admin()

        query = db.table("leads").select("stage")

        if user["role"] in ("rep", "sales_rep"):
            query = query.eq("assigned_rep_id", user["id"])

        result = query.execute()
        leads = result.data or []

        stage_counts = {}
        for lead in leads:
            stage = lead.get("stage", "new")
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

        funnel = []
        for stage in VALID_STAGES:
            funnel.append({"stage": stage, "count": stage_counts.get(stage, 0)})

        for stage, count in stage_counts.items():
            if stage not in VALID_STAGES:
                funnel.append({"stage": stage, "count": count})

        total = sum(item["count"] for item in funnel)

        return {"funnel": funnel, "total_leads": total}

    except Exception as e:
        log.error(f"Error fetching pipeline funnel: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch pipeline funnel")


@router.get("/source-analysis")
async def source_analysis(user: dict = Depends(get_current_user)):
    """Get conversion rates broken down by lead source."""
    try:
        db = get_supabase_admin()

        query = db.table("leads").select("source, stage")

        if user["role"] in ("rep", "sales_rep"):
            query = query.eq("assigned_rep_id", user["id"])

        result = query.execute()
        leads = result.data or []

        source_data: dict[str, dict] = {}
        for lead in leads:
            source = lead.get("source") or "unknown"
            if source not in source_data:
                source_data[source] = {"total": 0, "won": 0, "lost": 0}
            source_data[source]["total"] += 1
            stage = lead.get("stage", "")
            if stage == "won":
                source_data[source]["won"] += 1
            elif stage == "lost":
                source_data[source]["lost"] += 1

        sources = []
        for source, data in sorted(source_data.items(), key=lambda x: x[1]["total"], reverse=True):
            sources.append({
                "source": source,
                "total_leads": data["total"],
                "won": data["won"],
                "lost": data["lost"],
                "conversion_rate": _safe_rate(data["won"], data["total"]),
            })

        return {"sources": sources}

    except Exception as e:
        log.error(f"Error fetching source analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch source analysis")


@router.get("/conversion-trends")
async def conversion_trends(
    weeks: int = Query(12, ge=1, le=52),
    user: dict = Depends(get_current_user),
):
    """Get weekly conversion trend data."""
    try:
        db = get_supabase_admin()

        now = datetime.now(timezone.utc)
        start_date = (now - timedelta(weeks=weeks)).isoformat()

        query = (
            db.table("leads")
            .select("created_at, stage")
            .gte("created_at", start_date)
        )

        if user["role"] in ("rep", "sales_rep"):
            query = query.eq("assigned_rep_id", user["id"])

        result = query.execute()
        leads = result.data or []

        weekly_data: dict[str, dict] = {}
        for lead in leads:
            created_at = lead.get("created_at", "")
            if not created_at:
                continue
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                week_label = f"{dt.isocalendar()[0]}-W{dt.isocalendar()[1]:02d}"
            except (ValueError, AttributeError):
                continue

            if week_label not in weekly_data:
                weekly_data[week_label] = {"total": 0, "won": 0}
            weekly_data[week_label]["total"] += 1
            if lead.get("stage") == "won":
                weekly_data[week_label]["won"] += 1

        trends = []
        for week in sorted(weekly_data.keys()):
            data = weekly_data[week]
            trends.append({
                "week": week,
                "total_leads": data["total"],
                "won": data["won"],
                "conversion_rate": _safe_rate(data["won"], data["total"]),
            })

        return {"trends": trends, "weeks_requested": weeks}

    except Exception as e:
        log.error(f"Error fetching conversion trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversion trends")

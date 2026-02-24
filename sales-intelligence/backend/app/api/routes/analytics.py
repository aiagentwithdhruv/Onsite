"""Analytics routes — reads pre-computed data from dashboard_summary.

All analytics are computed at CSV upload time and stored in dashboard_summary.
This avoids querying the leads table (which is kept minimal for free-tier storage).
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import get_current_user
from app.core.supabase_client import get_supabase_admin

log = logging.getLogger(__name__)

router = APIRouter()


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def _get_summary(user: dict) -> dict:
    """Fetch dashboard_summary, scoped to deal_owner for reps."""
    db = get_supabase_admin()
    r = db.table("dashboard_summary").select("*").eq("id", "current").maybe_single().execute()
    if not r.data:
        return {}

    summary = r.data
    is_rep = user.get("role") in ("rep", "sales_rep")

    if is_rep:
        owner_name = user.get("deal_owner_name") or ""
        by_owner = summary.get("summary_by_owner") or {}
        owner_data = by_owner.get(owner_name)
        if owner_data:
            return owner_data
        return {}

    return summary


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/rep-performance")
async def rep_performance(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
):
    """Rep performance from pre-computed team_data in dashboard_summary."""
    try:
        summary = _get_summary(user)
        if not summary:
            return {"performance": [], "period": {"date_from": date_from, "date_to": date_to}}

        team_data = summary.get("team_data") or {}
        owners = team_data.get("owners") or []

        is_rep = user.get("role") in ("rep", "sales_rep")

        performance = []
        for owner in owners:
            name = owner.get("name", "Unknown")
            total = owner.get("total", 0)
            demos = owner.get("demos", 0)
            sales = owner.get("sales", 0)
            stale = owner.get("stale", 0)
            priority = owner.get("priority", 0)

            # Map to expected frontend shape
            performance.append({
                "user_id": name,
                "name": name,
                "total_leads": total,
                "contacted": total - stale,
                "meetings": demos,
                "won": sales,
                "lost": 0,
                "conversion_rate": _safe_rate(sales, total),
                "total_value": owner.get("revenue", 0),
            })

        # For reps, filter to just their data
        if is_rep:
            owner_name = user.get("deal_owner_name") or user.get("name", "")
            performance = [p for p in performance if p["name"] == owner_name]

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
    """Pipeline funnel from pre-computed charts data in dashboard_summary."""
    try:
        summary = _get_summary(user)
        if not summary:
            return {"funnel": [], "total_leads": 0}

        charts = summary.get("charts") or {}

        # Use charts.funnel (label/value format) and charts.stage (name/value format)
        funnel_data = charts.get("funnel") or []
        stage_data = charts.get("stage") or []

        funnel = []

        # Funnel data: [{label: "Total Leads", value: 299781}, ...]
        for item in funnel_data:
            funnel.append({
                "stage": item.get("label", "unknown"),
                "count": item.get("value", 0),
            })

        # If no funnel data, use stage data: [{name: "3. Sale Done", value: 2490}, ...]
        if not funnel and stage_data:
            for item in stage_data:
                funnel.append({
                    "stage": item.get("name", "unknown"),
                    "count": item.get("value", 0),
                })

        total = summary.get("total_leads") or sum(item["count"] for item in funnel)

        return {"funnel": funnel, "total_leads": total}

    except Exception as e:
        log.error(f"Error fetching pipeline funnel: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch pipeline funnel")


@router.get("/source-analysis")
async def source_analysis(user: dict = Depends(get_current_user)):
    """Source analysis from pre-computed source_data in dashboard_summary."""
    try:
        summary = _get_summary(user)
        if not summary:
            return {"sources": []}

        source_data = summary.get("source_data") or {}
        source_types = source_data.get("source_type") or []
        campaigns = source_data.get("campaigns") or []

        # Combine both source types
        sources = []
        for item in source_types:
            name = item.get("name", "unknown")
            total = item.get("value", 0)
            sources.append({
                "source": name,
                "total_leads": total,
                "won": 0,
                "lost": 0,
                "conversion_rate": 0,
            })

        # Enrich with campaign data if available
        campaign_map = {c.get("name", ""): c for c in campaigns}
        for s in sources:
            c = campaign_map.get(s["source"])
            if c:
                s["won"] = c.get("won", 0)
                s["conversion_rate"] = _safe_rate(c.get("won", 0), s["total_leads"])

        sources.sort(key=lambda x: x["total_leads"], reverse=True)

        return {"sources": sources}

    except Exception as e:
        log.error(f"Error fetching source analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch source analysis")


@router.get("/conversion-trends")
async def conversion_trends(
    weeks: int = Query(12, ge=1, le=52),
    user: dict = Depends(get_current_user),
):
    """Conversion trends from pre-computed trend_data (monthly) in dashboard_summary."""
    try:
        summary = _get_summary(user)
        if not summary:
            return {"trends": [], "weeks_requested": weeks}

        trend_data = summary.get("trend_data") or []

        trends = []
        for item in trend_data:
            month = item.get("month", "")
            total = item.get("leads", 0)
            sales = item.get("sales", 0)
            demos = item.get("demos", 0)

            trends.append({
                "week": month,
                "total_leads": total,
                "won": sales,
                "conversion_rate": _safe_rate(sales, total),
                "demos": demos,
                "demo_rate": item.get("demoRate", 0),
            })

        return {"trends": trends, "weeks_requested": weeks}

    except Exception as e:
        log.error(f"Error fetching conversion trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversion trends")

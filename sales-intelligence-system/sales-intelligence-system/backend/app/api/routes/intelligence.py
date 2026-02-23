"""Intelligence: upload CSV → compute analytics server-side → store summary in Supabase."""

import csv
import io
import json
import logging
from datetime import datetime, timezone
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.core.auth import get_current_user
from app.core.supabase_client import get_supabase_admin

log = logging.getLogger(__name__)
router = APIRouter()

IMPORTANT_KEYWORDS = [
    'studio','corpo','indus','energ','civil','hous','found','struc',
    'limit','agency','contrac','home','servi','trad','associ','world','space','company','private',
    'cons','infra','tech','inte','enter','dev','build','engg','constru','plan','proj','arch','des','real',
    'prop','site','firm','group','hold','estate','pvt','llp','llc','eng','decor',
]


def _matches_important(name: str) -> bool:
    if not name:
        return False
    raw = name.lower()
    return any(k in raw for k in IMPORTANT_KEYWORDS)


def _parse_date(s: str):
    if not s or not s.strip():
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        pass
    for fmt in ["%b %d, %Y %I:%M %p", "%b %d, %Y", "%d %b, %Y %H:%M:%S", "%d %b, %Y"]:
        try:
            return datetime.strptime(s.strip().strip('"'), fmt)
        except Exception:
            continue
    try:
        d = datetime.fromisoformat(s.strip())
        return d
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


def _top_counts(rows: list[dict], field: str, limit: int = 15) -> list[dict]:
    c = Counter(r.get(field, '').strip() for r in rows if r.get(field, '').strip())
    return [{"name": n, "value": v} for n, v in c.most_common(limit)]


def _compute_summary(rows: list[dict], file_name: str, user_email: str) -> dict:
    """Compute full dashboard summary from raw CSV rows."""
    total = len(rows)

    # KPIs
    demo_booked = sum(1 for r in rows if r.get('demo_booked') == '1')
    demo_done = sum(1 for r in rows if r.get('demo_done') == '1' or r.get('lead_status') == 'Demo Done')
    sale_done = sum(1 for r in rows if r.get('sale_done') == '1')
    purchased = sum(1 for r in rows if r.get('lead_status') == 'Purchased')
    priority = sum(1 for r in rows if r.get('lead_status') == 'Priority')
    prospects = sum(1 for r in rows if r.get('is_prospect') == '1' or 'Prospect' in (r.get('sales_stage') or ''))
    qualified = sum(1 for r in rows if r.get('lead_status') == 'Qualified')
    important = sum(1 for r in rows if _matches_important(r.get('company_name', '') or r.get('lead_name', '')))

    total_revenue = 0
    total_price = 0
    for r in rows:
        try:
            total_revenue += float((r.get('annual_revenue') or '0').replace(',', ''))
        except Exception:
            pass
        try:
            total_price += float((r.get('price_pitched') or '0').replace(',', ''))
        except Exception:
            pass

    kpis = {
        "total": total, "demo_booked": demo_booked, "demo_done": demo_done,
        "sale_done": sale_done, "purchased": purchased, "priority": priority,
        "prospects": prospects, "qualified": qualified, "important_companies": important,
        "total_revenue": total_revenue, "total_price_pitched": total_price,
    }

    # Charts data
    status_dist = _top_counts(rows, 'lead_status', 15)
    source_dist = _top_counts(rows, 'lead_source', 15)
    region_dist = _top_counts(rows, 'region', 10)
    stage_dist = _top_counts(rows, 'sales_stage', 10)
    disposition_dist = _top_counts(rows, 'call_disposition', 12)

    # Funnel
    trial_count = sum(1 for r in rows if r.get('trial_activated') == '1')
    prospect_count = sum(1 for r in rows if r.get('is_prospect') == '1')
    funnel = [
        {"label": "Total Leads", "value": total},
        {"label": "Demo Booked", "value": demo_booked},
        {"label": "Demo Done", "value": demo_done},
        {"label": "Trial Activated", "value": trial_count},
        {"label": "Prospect", "value": prospect_count},
        {"label": "Sale Done", "value": sale_done},
        {"label": "Purchased", "value": purchased},
    ]

    # Demo metrics
    demo_not_done = max(0, demo_booked - demo_done)
    demo_metrics = [
        {"name": "Demo Done", "value": demo_done},
        {"name": "Booked (Not Done)", "value": demo_not_done},
        {"name": "No Demo Booked", "value": total - demo_booked},
    ]

    charts = {
        "status": status_dist, "source": source_dist, "region": region_dist,
        "stage": stage_dist, "disposition": disposition_dist,
        "funnel": funnel, "demo_metrics": demo_metrics,
    }

    # Insights
    top_source = source_dist[0] if source_dist else None
    stale_30 = sum(1 for r in rows if (_days_since(r.get('last_touched_date_new', '')) or 999) > 30 and r.get('lead_status') not in ('Purchased', 'Rejected', 'DTA'))

    # Source conversion stats
    src_stats = {}
    for r in rows:
        src = (r.get('lead_source') or '').strip()
        if not src:
            continue
        if src not in src_stats:
            src_stats[src] = {"total": 0, "demo": 0, "sale": 0}
        src_stats[src]["total"] += 1
        if r.get('demo_done') == '1':
            src_stats[src]["demo"] += 1
        if r.get('sale_done') == '1':
            src_stats[src]["sale"] += 1

    best_source = max(
        ((k, v["sale"] / max(v["total"], 1)) for k, v in src_stats.items() if v["total"] >= 100),
        key=lambda x: x[1], default=None
    )
    worst_source = min(
        ((k, v["sale"] / max(v["total"], 1)) for k, v in src_stats.items() if v["total"] >= 100),
        key=lambda x: x[1], default=None
    )

    # Deal owner stats
    owner_stats = {}
    for r in rows:
        own = (r.get('deal_owner') or '').strip()
        if not own or own in ('Onsite', 'Offline Campaign'):
            continue
        if own not in owner_stats:
            owner_stats[own] = {"total": 0, "demo": 0, "sale": 0}
        owner_stats[own]["total"] += 1
        if r.get('demo_done') == '1':
            owner_stats[own]["demo"] += 1
        if r.get('sale_done') == '1':
            owner_stats[own]["sale"] += 1

    top_closer = max(
        ((k, v["sale"] / max(v["total"], 1), v["total"]) for k, v in owner_stats.items() if v["total"] >= 100),
        key=lambda x: x[1], default=None
    )

    bookedNotDone = max(0, demo_booked - demo_done)
    demo_rate = (demo_done / total * 100) if total else 0
    sale_rate = (sale_done / total * 100) if total else 0

    insights = {
        "demo_rate": round(demo_rate, 1),
        "sale_rate": round(sale_rate, 1),
        "top_source": top_source,
        "stale_30": stale_30,
        "booked_not_done": bookedNotDone,
        "best_source": {"name": best_source[0], "rate": round(best_source[1] * 100, 2), "total": src_stats[best_source[0]]["total"]} if best_source else None,
        "worst_source": {"name": worst_source[0], "rate": round(worst_source[1] * 100, 2), "total": src_stats[worst_source[0]]["total"]} if worst_source else None,
        "top_closer": {"name": top_closer[0], "rate": round(top_closer[1] * 100, 2), "total": top_closer[2]} if top_closer else None,
        "important_count": important,
        "source_conversion": [
            {"name": k, "total": v["total"], "saleRate": round(v["sale"] / max(v["total"], 1) * 100, 2), "demoRate": round(v["demo"] / max(v["total"], 1) * 100, 2)}
            for k, v in sorted(src_stats.items(), key=lambda x: -x[1]["total"])[:15]
        ],
    }

    # Team data (by deal_owner)
    manager_data = []
    mgr_counts = Counter(r.get('lead_owner_manager', '').strip() for r in rows if r.get('lead_owner_manager', '').strip())
    for mgr, cnt in mgr_counts.most_common(10):
        ml = [r for r in rows if r.get('lead_owner_manager') == mgr]
        demos = sum(1 for r in ml if r.get('demo_done') == '1')
        sales = sum(1 for r in ml if r.get('sale_done') == '1')
        pri = sum(1 for r in ml if r.get('lead_status') == 'Priority')
        manager_data.append({"name": mgr, "total": cnt, "demos": demos, "sales": sales, "priority": pri})

    owner_table = []
    for own, cnt in Counter(r.get('deal_owner', '').strip() for r in rows if r.get('deal_owner', '').strip() and r.get('deal_owner', '').strip() not in ('Onsite', 'Offline Campaign')).most_common(20):
        ol = [r for r in rows if r.get('deal_owner') == own]
        mgr = next((r.get('lead_owner_manager', '') for r in ol if r.get('lead_owner_manager')), '-')
        dd = sum(1 for r in ol if r.get('demo_done') == '1')
        sd = sum(1 for r in ol if r.get('sale_done') == '1')
        pri = sum(1 for r in ol if r.get('lead_status') == 'Priority')
        stale = sum(1 for r in ol if (_days_since(r.get('last_touched_date_new', '')) or 0) > 30 and r.get('lead_status') not in ('Purchased', 'Rejected', 'DTA'))
        owner_table.append({"name": own, "manager": mgr, "total": cnt, "demos": dd, "sales": sd, "priority": pri, "stale": stale})

    team_data = {"managers": manager_data, "owners": owner_table}

    # Source data
    source_type_dist = _top_counts(rows, 'lead_source_type', 10)
    campaign_dist = _top_counts(rows, 'campaign_name', 15)
    source_data = {"source_type": source_type_dist, "campaigns": campaign_dist}

    # Aging data
    now = datetime.now(timezone.utc)
    age_buckets = {'0-7d': 0, '8-30d': 0, '31-90d': 0, '91-180d': 0, '181-365d': 0, '1-2yr': 0, '2yr+': 0}
    touch_buckets = {'0-7d': 0, '8-14d': 0, '15-30d': 0, '31-60d': 0, '61-90d': 0, '90d+': 0, 'Never': 0}

    stale_leads = []
    hot_prospects = []

    for r in rows:
        ud = _days_since(r.get('user_date', ''))
        if ud is not None:
            if ud <= 7: age_buckets['0-7d'] += 1
            elif ud <= 30: age_buckets['8-30d'] += 1
            elif ud <= 90: age_buckets['31-90d'] += 1
            elif ud <= 180: age_buckets['91-180d'] += 1
            elif ud <= 365: age_buckets['181-365d'] += 1
            elif ud <= 730: age_buckets['1-2yr'] += 1
            else: age_buckets['2yr+'] += 1

        lt = _days_since(r.get('last_touched_date_new', ''))
        if lt is None:
            touch_buckets['Never'] += 1
        elif lt <= 7: touch_buckets['0-7d'] += 1
        elif lt <= 14: touch_buckets['8-14d'] += 1
        elif lt <= 30: touch_buckets['15-30d'] += 1
        elif lt <= 60: touch_buckets['31-60d'] += 1
        elif lt <= 90: touch_buckets['61-90d'] += 1
        else: touch_buckets['90d+'] += 1

        # Stale leads (top 50)
        active_statuses = {'Priority', 'Follow Up', 'Qualified', 'Demo Booked', 'Demo Done', 'User not attend session'}
        if lt and lt > 30 and r.get('lead_status') in active_statuses and len(stale_leads) < 50:
            stale_leads.append({"name": r.get('lead_name', '-'), "status": r.get('lead_status', '-'), "owner": r.get('deal_owner', '-'), "days": lt, "phone": r.get('lead_phone', '-')})

        # Hot prospects
        if r.get('sales_stage') in ('Very High Prospect', 'High Prospect') and len(hot_prospects) < 50:
            hot_prospects.append({"name": r.get('lead_name', '-'), "stage": r.get('sales_stage', '-'), "owner": r.get('deal_owner', '-'), "company": r.get('company_name', '-'), "phone": r.get('lead_phone', '-')})

    stale_leads.sort(key=lambda x: -x['days'])
    aging_data = {
        "age_dist": [{"name": k, "value": v} for k, v in age_buckets.items()],
        "touch_dist": [{"name": k, "value": v} for k, v in touch_buckets.items()],
        "stale_leads": stale_leads[:50],
        "hot_prospects": hot_prospects[:50],
    }

    # Trends (monthly)
    monthly = {}
    for r in rows:
        d = _parse_date(r.get('user_date', ''))
        if not d:
            continue
        key = f"{d.year}-{d.month:02d}"
        if key not in monthly:
            monthly[key] = {"leads": 0, "demos": 0, "sales": 0, "purchased": 0}
        monthly[key]["leads"] += 1
        if r.get('demo_done') == '1': monthly[key]["demos"] += 1
        if r.get('sale_done') == '1': monthly[key]["sales"] += 1
        if r.get('lead_status') == 'Purchased': monthly[key]["purchased"] += 1

    sorted_months = sorted(monthly.keys())[-24:]
    trend_data = [
        {"month": m, **monthly[m],
         "demoRate": round(monthly[m]["demos"] / max(monthly[m]["leads"], 1) * 100, 1),
         "saleRate": round(monthly[m]["sales"] / max(monthly[m]["leads"], 1) * 100, 1)}
        for m in sorted_months
    ]

    # Deep dive
    profession_dist = _top_counts(rows, 'user_profession', 12)
    team_size_dist = _top_counts(rows, 'Team_size', 10)
    state_dist = _top_counts(rows, 'state_mobile', 20)
    prequal_dist = [{"name": f"Stage {d['name']}", "value": d["value"]} for d in _top_counts(rows, 'pre_qualification', 10)]

    # Recent notes (top 50)
    notes_leads = sorted(
        (r for r in rows if (r.get('lead_notes') or '').strip() and len(r.get('lead_notes', '').strip()) > 10),
        key=lambda r: r.get('notes_date', '') or '', reverse=True
    )[:50]
    notes_intel = [
        {"name": r.get('lead_name', '-'), "status": r.get('lead_status', '-'), "stage": r.get('sales_stage', '-'),
         "owner": r.get('deal_owner', '-'), "date": r.get('notes_date', '-'),
         "preview": (r.get('lead_notes', '') or '').replace('\n', ' ')[:120]}
        for r in notes_leads
    ]

    deep_dive = {
        "profession": profession_dist, "team_size": team_size_dist,
        "state": state_dist, "prequal": prequal_dist, "notes": notes_intel,
    }

    return {
        "id": "current",
        "kpis": kpis,
        "charts": charts,
        "insights": insights,
        "team_data": team_data,
        "source_data": source_data,
        "aging_data": aging_data,
        "trend_data": trend_data,
        "deep_dive": deep_dive,
        "action_items": [],
        "total_leads": total,
        "file_name": file_name,
        "uploaded_by": user_email,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/summary")
async def get_summary(user: dict = Depends(get_current_user)):
    """Load dashboard summary from Supabase."""
    try:
        db = get_supabase_admin()
        result = db.table("dashboard_summary").select("*").eq("id", "current").maybe_single().execute()
        if result.data:
            return result.data
        return {"has_data": False}
    except Exception as e:
        log.error(f"Load summary error: {e}")
        return {"has_data": False}


@router.post("/upload")
async def upload_and_compute(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Upload CSV, compute analytics server-side, store summary in Supabase (~1-2MB)."""
    try:
        content = await file.read()
        text = content.decode("utf-8", errors="replace")
        if text.startswith("\ufeff"):
            text = text[1:]

        reader = csv.DictReader(io.StringIO(text))
        rows = [dict(r) for r in reader if (r.get("lead_name") or "").strip()]

        if not rows:
            raise HTTPException(status_code=400, detail="No valid rows in CSV")

        log.info(f"Intelligence upload: {len(rows)} rows from {file.filename}")

        summary = _compute_summary(rows, file.filename or "upload.csv", user.get("email", "unknown"))

        db = get_supabase_admin()
        db.table("dashboard_summary").upsert(summary).execute()

        # Compute and save agent profiles
        from app.api.routes.agents import compute_agent_profiles, save_agent_profiles
        profiles = compute_agent_profiles(rows)
        try:
            save_agent_profiles(profiles)
            log.info(f"Agent profiles saved: {len(profiles)} agents")
        except Exception as e:
            log.warning(f"Agent profile save failed (non-fatal): {e}")

        log.info(f"Summary saved: {len(rows)} leads → ~{len(json.dumps(summary)) // 1024}KB, {len(profiles)} agents")

        return {"success": True, "total_rows": len(rows), "summary_size_kb": len(json.dumps(summary)) // 1024, "agents_updated": len(profiles)}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.delete("/summary")
async def clear_summary(user: dict = Depends(get_current_user)):
    """Clear dashboard summary."""
    try:
        db = get_supabase_admin()
        db.table("dashboard_summary").delete().eq("id", "current").execute()
        return {"success": True}
    except Exception as e:
        log.error(f"Clear error: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear")

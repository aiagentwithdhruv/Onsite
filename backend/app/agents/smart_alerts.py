"""Smart Alert Agent: analyzes CSV data and generates actionable alerts for the sales team."""

import re
import logging
from datetime import datetime, timezone
from collections import Counter

from app.core.supabase_client import get_supabase_admin

log = logging.getLogger(__name__)


def _parse_currency(val: str) -> float:
    if not val:
        return 0.0
    cleaned = re.sub(r'[Rr][Ss]\.?\s*', '', val).replace('₹', '').replace(',', '').strip()
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0


def _parse_date(s: str):
    if not s or not s.strip():
        return None
    for fmt in ["%b %d, %Y %I:%M %p", "%b %d, %Y", "%d %b, %Y %H:%M:%S", "%d %b, %Y"]:
        try:
            return datetime.strptime(s.strip().strip('"'), fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
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


def generate_smart_alerts(rows: list[dict], user_id: str) -> list[dict]:
    """Analyze CSV rows and produce actionable alerts."""
    alerts: list[dict] = []
    now_iso = datetime.now(timezone.utc).isoformat()
    total = len(rows)
    if total == 0:
        return alerts

    # ---- Per-owner stats ----
    owners: dict[str, dict] = {}
    for r in rows:
        own = (r.get("deal_owner") or "").strip()
        if not own or own in ("Onsite", "Offline Campaign"):
            continue
        if own not in owners:
            owners[own] = {"leads": 0, "demos": 0, "sales": 0, "stale30": 0,
                           "stale14": 0, "priority": 0, "revenue": 0,
                           "hot_prospects": [], "recent_7d": 0, "demo_booked": 0}
        o = owners[own]
        o["leads"] += 1
        if r.get("demo_done") == "1":
            o["demos"] += 1
        if r.get("demo_booked") == "1":
            o["demo_booked"] += 1
        if r.get("sale_done") == "1" or r.get("lead_status") == "Purchased":
            o["sales"] += 1
            o["revenue"] += _parse_currency(r.get("annual_revenue", ""))
        if r.get("lead_status") == "Priority":
            o["priority"] += 1

        lt = _days_since(r.get("last_touched_date_new", ""))
        active = r.get("lead_status") not in ("Purchased", "Rejected", "DTA")
        if lt is not None and active:
            if lt > 30:
                o["stale30"] += 1
            if lt > 14:
                o["stale14"] += 1
        if lt is not None and lt <= 7:
            o["recent_7d"] += 1

        stage = r.get("sales_stage", "")
        if stage in ("Very High Prospect", "High Prospect"):
            o["hot_prospects"].append(r.get("lead_name", "-"))

    # Global stats
    total_sales = sum(o["sales"] for o in owners.values())
    total_leads_owned = sum(o["leads"] for o in owners.values())
    avg_conv = (total_sales / max(total_leads_owned, 1)) * 100

    def add(alert_type: str, severity: str, title: str, message: str, agent: str = "", meta: dict | None = None):
        alerts.append({
            "alert_type": alert_type,
            "severity": severity,
            "title": title,
            "message": message,
            "target_user_id": user_id,
            "lead_id": None,
            "channel": "email",
            "sent_at": now_iso,
            "delivered": True,
            "created_at": now_iso,
            "agent_name": agent or "system",
            "metadata": meta or {},
        })

    # ---- ALERT RULES ----

    # 1. Stale Lead Alert (30+ days untouched)
    for own, o in owners.items():
        if o["stale30"] >= 10:
            add("stale_30d", "critical", f"🔴 {own}: {o['stale30']} Stale Leads",
                f"{own} has {o['stale30']} active leads untouched for 30+ days. "
                f"These need immediate follow-up or reassignment.",
                agent=own, meta={"stale_count": o["stale30"], "owner": own})
        elif o["stale14"] >= 15:
            add("stale_14d", "high", f"🟠 {own}: {o['stale14']} Leads Going Cold",
                f"{own} has {o['stale14']} leads untouched for 14+ days. "
                f"Schedule follow-ups before they go stale.",
                agent=own, meta={"stale_count": o["stale14"], "owner": own})

    # 2. Demo Dropout Alert
    for own, o in owners.items():
        if o["demo_booked"] >= 20:
            done_rate = o["demos"] / max(o["demo_booked"], 1) * 100
            if done_rate < 50:
                add("demo_dropout", "high",
                    f"⚠️ {own}: Only {done_rate:.0f}% Demos Completed",
                    f"{own} booked {o['demo_booked']} demos but only {o['demos']} happened ({done_rate:.0f}%). "
                    f"{o['demo_booked'] - o['demos']} demos were missed or cancelled.",
                    agent=own, meta={"booked": o["demo_booked"], "done": o["demos"], "owner": own})

    # 3. Low Conversion Alert
    for own, o in owners.items():
        if o["leads"] >= 100:
            conv = o["sales"] / max(o["leads"], 1) * 100
            if conv < avg_conv * 0.5:
                add("low_conversion", "high",
                    f"📉 {own}: {conv:.1f}% Conversion (Team avg: {avg_conv:.1f}%)",
                    f"{own} is converting at {conv:.1f}% — less than half the team average of {avg_conv:.1f}%. "
                    f"{o['sales']} sales from {o['leads']} leads. Needs coaching or lead reassignment.",
                    agent=own, meta={"conv": round(conv, 1), "avg": round(avg_conv, 1), "owner": own})

    # 4. Hot Prospect Alert
    for own, o in owners.items():
        if len(o["hot_prospects"]) >= 3:
            names = ", ".join(o["hot_prospects"][:5])
            add("hot_no_followup", "high",
                f"🔥 {own}: {len(o['hot_prospects'])} Hot Prospects Need Attention",
                f"{own} has {len(o['hot_prospects'])} high/very-high prospects: {names}. "
                f"Prioritize these for demos and closures.",
                agent=own, meta={"prospects": o["hot_prospects"][:10], "owner": own})

    # 5. Priority Overload
    for own, o in owners.items():
        if o["priority"] >= 25:
            add("priority_overload", "high",
                f"⚡ {own}: {o['priority']} Priority Leads Pending",
                f"{own} has {o['priority']} leads in Priority status. "
                f"This is too many to handle effectively — consider redistribution.",
                agent=own, meta={"priority_count": o["priority"], "owner": own})

    # 6. Inactive Agent (no activity in 7 days with 20+ leads)
    for own, o in owners.items():
        if o["recent_7d"] == 0 and o["leads"] >= 20:
            add("inactive_agent", "critical",
                f"🚨 {own}: Zero Activity in 7 Days",
                f"{own} has {o['leads']} leads but zero touches in the last 7 days. "
                f"Requires immediate check-in — leads are going cold.",
                agent=own, meta={"leads": o["leads"], "owner": own})

    # 7. Top Performer Recognition
    top_closers = sorted(owners.items(), key=lambda x: -x[1]["sales"])
    if top_closers and top_closers[0][1]["sales"] >= 10:
        best = top_closers[0]
        conv = best[1]["sales"] / max(best[1]["leads"], 1) * 100
        add("top_performer", "info",
            f"🏆 Top Closer: {best[0]} with {best[1]['sales']} Sales",
            f"{best[0]} leads the team with {best[1]['sales']} sales ({conv:.1f}% conversion). "
            f"Revenue: ₹{best[1]['revenue'] / 100000:.1f}L. Share their best practices!",
            agent=best[0], meta={"sales": best[1]["sales"], "revenue": best[1]["revenue"], "owner": best[0]})

    # 8. Revenue Milestone
    total_revenue = sum(o["revenue"] for o in owners.values())
    if total_revenue >= 10000000:
        add("revenue_milestone", "info",
            f"💰 Revenue Milestone: ₹{total_revenue / 10000000:.2f}Cr Total Sales",
            f"Team has generated ₹{total_revenue / 10000000:.2f}Cr in total revenue from {total_sales} sales. "
            f"Average deal size: ₹{total_revenue / max(total_sales, 1) / 100000:.1f}L.",
            meta={"total_revenue": total_revenue, "total_sales": total_sales})

    # 9. Pipeline Risk — too many leads stuck in same status
    status_counts = Counter(r.get("lead_status", "").strip() for r in rows if r.get("lead_status", "").strip())
    for status, cnt in status_counts.most_common(5):
        if status in ("Follow Up", "Qualified", "Demo Booked") and cnt > total * 0.15:
            pct = cnt / total * 100
            add("pipeline_risk", "medium",
                f"📊 Pipeline Bottleneck: {cnt:,} Leads Stuck in '{status}'",
                f"{pct:.1f}% of all leads ({cnt:,}) are in '{status}' status. "
                f"This indicates a bottleneck — review processes for this stage.",
                meta={"status": status, "count": cnt, "pct": round(pct, 1)})

    # 10. Follow-up needed — overall stale summary
    total_stale_30 = sum(o["stale30"] for o in owners.values())
    if total_stale_30 > 100:
        add("follow_up_needed", "critical",
            f"🔴 {total_stale_30:,} Leads Untouched 30+ Days Across Team",
            f"The team has {total_stale_30:,} active leads with no activity in 30+ days. "
            f"Top contributors: {', '.join(n for n, o in sorted(owners.items(), key=lambda x: -x[1]['stale30'])[:3])}.",
            meta={"total_stale": total_stale_30})

    # Sort: critical first, then high, medium, info
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    alerts.sort(key=lambda a: severity_order.get(a["severity"], 5))

    return alerts


def save_alerts(alerts: list[dict]):
    """Save generated alerts to Supabase, clearing old smart alerts first."""
    if not alerts:
        return 0

    db = get_supabase_admin()

    user_id = alerts[0]["target_user_id"]
    try:
        db.table("alerts").delete().eq("target_user_id", user_id).eq("delivered", True).is_("read_at", "null").execute()
    except Exception as e:
        log.warning(f"Failed to clear old alerts: {e}")

    saved = 0
    for alert in alerts:
        try:
            db.table("alerts").insert(alert).execute()
            saved += 1
        except Exception as e:
            log.warning(f"Failed to save alert '{alert.get('title', '')}': {e}")

    log.info(f"Smart Alert Agent: generated {len(alerts)} alerts, saved {saved}")
    return saved

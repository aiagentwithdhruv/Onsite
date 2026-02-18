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
    for fmt in ["%b %d, %Y %I:%M %p", "%b %d, %Y", "%d %b, %Y %I:%M %p", "%d %b, %Y %H:%M:%S", "%d %b, %Y"]:
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


def _get_followup_date(row: dict) -> str | None:
    """Get Followup Date from row; CSV may use 'Followup Date', 'followup_date', etc."""
    for key in ("Followup Date", "followup_date", "followup date", "FollowupDate"):
        val = row.get(key)
        if val and (val or "").strip():
            return (val or "").strip()
    return None


def _get_notes_remarks(row: dict) -> str:
    """Get combined notes and remarks from row for smart intelligence. Multiple possible column names."""
    parts = []
    for key in ("notes", "remarks", "Notes", "Remarks", "note", "remark", "Notes and Remarks", "comments", "Comments"):
        val = row.get(key)
        if val and (val or "").strip():
            parts.append((val or "").strip())
    return " ".join(parts) if parts else ""


def _get_lead_phone(row: dict) -> str:
    """Get lead phone from row for action (call back)."""
    for key in ("phone", "Phone", "lead_phone", "contact_number", "Phone Number", "mobile", "Mobile"):
        val = row.get(key)
        if val and (val or "").strip():
            return (val or "").strip()
    return ""


# Keywords in notes/remarks that suggest the lead needs action (call back, follow up, etc.)
_NOTES_ACTION_KEYWORDS = (
    "call", "callback", "follow up", "followup", "interested", "will buy", "ready", "demo",
    "meeting", "schedule", "tomorrow", "next week", "confirm", "pending", "waiting",
    "urgent", "asap", "revert", "replied", "said", "asked", "promised", "commit",
)


def _days_until_followup(date_str: str) -> int | None:
    """Days until date (positive = future, 0 = today, negative = overdue). None if unparseable."""
    d = _parse_date(date_str)
    if not d:
        return None
    now = datetime.now(timezone.utc)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    d_date = d.date() if hasattr(d, "date") else d.replace(tzinfo=None).date()
    now_date = now.date() if hasattr(now, "date") else now.replace(tzinfo=None).date()
    return (d_date - now_date).days


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
                           "hot_prospects": [], "recent_7d": 0, "demo_booked": 0,
                           "followup_overdue": [], "followup_due_today": [], "followup_due_tomorrow": [],
                           "leads_with_notes": []}
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

        # Followup Date (CRM field) — alert when overdue, due today, or due tomorrow
        followup_str = _get_followup_date(r)
        if followup_str and active:
            days = _days_until_followup(followup_str)
            if days is not None:
                name = r.get("lead_name", "-")
                if days < 0:
                    o["followup_overdue"].append(name)
                elif days == 0:
                    o["followup_due_today"].append(name)
                elif days == 1:
                    o["followup_due_tomorrow"].append(name)

        # Notes / Remarks — use for smart alerts: leads with notes may need action
        notes_text = _get_notes_remarks(r)
        if active and notes_text:
            # Prefer leads where notes suggest action (keywords) or any non-empty note
            snippet = (notes_text[:120] + "…") if len(notes_text) > 120 else notes_text
            has_action_hint = any(kw in notes_text.lower() for kw in _NOTES_ACTION_KEYWORDS)
            o["leads_with_notes"].append({
                "name": r.get("lead_name", "-"),
                "phone": _get_lead_phone(r),
                "snippet": snippet,
                "action_hint": has_action_hint,
            })

    # Global stats
    total_sales = sum(o["sales"] for o in owners.values())
    total_leads_owned = sum(o["leads"] for o in owners.values())
    avg_conv = (total_sales / max(total_leads_owned, 1)) * 100

    def add(alert_type: str, severity: str, title: str, message: str, agent: str = "", meta: dict | None = None):
        full_message = f"{title}\n\n{message}" if title != message else message
        alerts.append({
            "alert_type": alert_type,
            "severity": severity,
            "title": title,
            "message": full_message,
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

    # 11. Followup Date (CRM) — overdue
    for own, o in owners.items():
        overdue = o.get("followup_overdue") or []
        if len(overdue) >= 3:
            names = ", ".join(overdue[:5])
            add("followup_overdue", "critical",
                f"📅 {own}: {len(overdue)} Follow-ups Overdue",
                f"{own} has {len(overdue)} leads with Followup Date in the past: {names}. "
                f"Reach out or reschedule in CRM.",
                agent=own, meta={"count": len(overdue), "owner": own, "leads": overdue[:10]})
        elif len(overdue) == 1:
            add("followup_overdue", "high",
                f"📅 {own}: 1 Follow-up Overdue — {overdue[0]}",
                f"Followup Date has passed for {overdue[0]}. Update in CRM or contact the lead.",
                agent=own, meta={"count": 1, "owner": own, "leads": overdue})

    # 12. Followup Date — due today
    for own, o in owners.items():
        due_today = o.get("followup_due_today") or []
        if due_today:
            names = ", ".join(due_today[:5])
            add("followup_due_today", "high",
                f"📅 {own}: {len(due_today)} Follow-up(s) Due Today",
                f"{own} has {len(due_today)} lead(s) with Followup Date today: {names}. "
                f"Don’t miss these touchpoints.",
                agent=own, meta={"count": len(due_today), "owner": own, "leads": due_today[:10]})

    # 13. Followup Date — due tomorrow (reminder)
    for own, o in owners.items():
        due_tomorrow = o.get("followup_due_tomorrow") or []
        if len(due_tomorrow) >= 5:
            names = ", ".join(due_tomorrow[:5])
            add("followup_due_tomorrow", "medium",
                f"📅 {own}: {len(due_tomorrow)} Follow-ups Due Tomorrow",
                f"{own} has {len(due_tomorrow)} follow-ups scheduled for tomorrow: {names}. "
                f"Plan your day accordingly.",
                agent=own, meta={"count": len(due_tomorrow), "owner": own, "leads": due_tomorrow[:10]})

    # 14. Notes / Remarks — leads with notes need attention; send lead details so rep can act
    for own, o in owners.items():
        with_notes = o.get("leads_with_notes") or []
        action_leads = [x for x in with_notes if x.get("action_hint")]
        # Alert if: (a) any notes suggest action (call back, follow up, etc.), or (b) 5+ leads have notes
        if action_leads or len(with_notes) >= 5:
            to_show = action_leads if action_leads else with_notes
            to_show = to_show[:10]  # cap for message size
            lines = [
                f"{own} has {len(with_notes)} lead(s) with notes/remarks. Review and take action.",
                "",
            ]
            for i, item in enumerate(to_show, 1):
                name = item.get("name") or "—"
                phone = item.get("phone") or "No number"
                snippet = (item.get("snippet") or "")[:80]
                lines.append(f"{i}. {name} — {phone}")
                if snippet:
                    lines.append(f"   Note: {snippet}")
                lines.append("")
            title = f"📝 {own}: {len(with_notes)} Leads With Notes Need Action"
            if action_leads:
                title = f"📝 {own}: {len(action_leads)} Leads With Actionable Notes (call/follow up)"
            add("notes_need_action", "high" if action_leads else "medium",
                title,
                "\n".join(lines).strip(),
                agent=own,
                meta={"owner": own, "count": len(with_notes), "action_count": len(action_leads), "leads": to_show})

    # Sort: critical first, then high, medium, info
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    alerts.sort(key=lambda a: severity_order.get(a["severity"], 5))

    return alerts


# Original schema (001) allowed alert_type values — use 'custom' for any other
_LEGACY_ALERT_TYPES = frozenset({
    "morning_brief", "new_lead", "stale_7d", "stale_14d",
    "hot_no_followup", "deal_won", "deal_lost",
    "weekly_report", "performance_drop", "custom",
})


def _row_minimal(alert: dict) -> dict:
    """Row for base alerts table (001) only — no severity/title columns."""
    alert_type = alert.get("alert_type") or "custom"
    if alert_type not in _LEGACY_ALERT_TYPES:
        alert_type = "custom"
    return {
        "alert_type": alert_type,
        "message": alert.get("message") or alert.get("title") or "Alert",
        "target_user_id": alert["target_user_id"],
        "lead_id": None,
        "channel": "email",
        "sent_at": alert.get("sent_at") or datetime.now(timezone.utc).isoformat(),
        "delivered": True,
    }


# alert_type values allowed after migration 007 (broader than legacy)
_EXTENDED_ALERT_TYPES = _LEGACY_ALERT_TYPES | frozenset({
    "stale_30d", "low_conversion", "demo_dropout", "priority_overload",
    "inactive_agent", "top_performer", "revenue_milestone", "pipeline_risk", "follow_up_needed",
    "followup_overdue", "followup_due_today", "followup_due_tomorrow",
    "notes_need_action",
})


def _row_full(alert: dict) -> dict:
    """Full row including severity, title, agent_name (after migration 007)."""
    alert_type = alert.get("alert_type") or "custom"
    if alert_type not in _EXTENDED_ALERT_TYPES:
        alert_type = "custom"
    now_iso = alert.get("sent_at") or datetime.now(timezone.utc).isoformat()
    msg = alert.get("message") or alert.get("title") or "Alert"
    return {
        "alert_type": alert_type,
        "message": msg,
        "target_user_id": alert["target_user_id"],
        "lead_id": None,
        "channel": "email",
        "sent_at": now_iso,
        "delivered": True,
        "severity": alert.get("severity") or "medium",
        "title": (alert.get("title") or msg.split("\n")[0] or "Alert")[:500],
        "agent_name": alert.get("agent_name") or "system",
        "metadata": alert.get("metadata") or {},
        "created_at": now_iso,
    }


def save_alerts(alerts: list[dict]) -> int:
    """Save generated alerts to Supabase. Uses full row (severity, title, etc.) when migration 007 applied."""
    if not alerts:
        return 0

    db = get_supabase_admin()
    user_id = alerts[0]["target_user_id"]

    try:
        db.table("alerts").delete().eq("target_user_id", user_id).eq("delivered", True).is_("read_at", "null").execute()
    except Exception as e:
        log.warning("Failed to clear old alerts: %s", e)

    saved = 0
    use_full = True  # try full row first
    for alert in alerts:
        row = _row_full(alert) if use_full else _row_minimal(alert)
        try:
            db.table("alerts").insert(row).execute()
            saved += 1
        except Exception as e:
            if use_full:
                use_full = False
                row = _row_minimal(alert)
                try:
                    db.table("alerts").insert(row).execute()
                    saved += 1
                except Exception as e2:
                    log.warning("Failed to save alert %s: %s", alert.get("title", "")[:50], e2)
            else:
                log.warning("Failed to save alert %s: %s", alert.get("title", "")[:50], e)

    log.info("Smart Alert Agent: generated %s alerts, saved %s", len(alerts), saved)
    return saved

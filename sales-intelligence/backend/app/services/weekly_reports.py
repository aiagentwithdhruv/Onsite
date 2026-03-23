"""Weekly WhatsApp Reports — Friday review + Monday kickoff.

Friday 6 PM IST:  Team Overview (managers) + Rep Scorecard (each rep) + Hygiene Report Card (managers)
Monday 8 AM IST:  Stale Pipeline (each rep) + Quick Wins (each rep)
"""

import csv
import glob
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from app.core.rep_contacts import REP_CONTACTS, MANAGER_PHONES, DEMO_TARGET
from app.services.whatsapp import send_whatsapp_message

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean(val: str | None) -> str:
    return (val or "").strip()


def _parse_rupee(val: str | None) -> float:
    if not val:
        return 0
    val = val.strip().replace("Rs.", "").replace("₹", "").replace(",", "").strip()
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0


def _parse_date(d: str | None) -> datetime | None:
    if not d:
        return None
    for fmt in [
        "%b %d, %Y %I:%M %p",     # "Dec 17, 2025 01:54 PM" (Zoho last_touched_date)
        "%d %b, %Y %H:%M:%S",     # "17 Dec, 2025 13:54:00"
        "%d %b, %Y",              # "17 Dec, 2025"
        "%b %d, %Y",              # "Dec 17, 2025"
        "%Y-%m-%d",               # "2025-12-17"
        "%d-%b-%Y",               # "17-Dec-2025"
        "%d %b, %Y %I:%M %p",    # "17 Dec, 2025 01:54 PM"
    ]:
        try:
            return datetime.strptime(d.strip(), fmt)
        except (ValueError, TypeError):
            continue
    return None


def _fmt_lakhs(val: float) -> str:
    """Format number as ₹X.XXL or ₹X,XXX."""
    if val >= 100000:
        return f"₹{val/100000:.1f}L"
    elif val >= 1000:
        return f"₹{val:,.0f}"
    elif val > 0:
        return f"₹{val:.0f}"
    return "₹0"


def _days_since(date_str: str | None) -> int:
    dt = _parse_date(date_str)
    if not dt:
        return 999
    return (datetime.now() - dt).days


# ---------------------------------------------------------------------------
# CSV Loader
# ---------------------------------------------------------------------------

def _load_csv_data() -> list[dict]:
    """Load the latest Last_Touched_Query CSV from sales-intelligence folder."""
    base = Path(__file__).resolve().parent.parent.parent  # backend/
    pattern = str(base / "Last_Touched_Query*.csv")
    # Also check parent (sales-intelligence/)
    pattern2 = str(base.parent / "Last_Touched_Query*.csv")

    files = glob.glob(pattern) + glob.glob(pattern2)
    if not files:
        log.error("No Last_Touched_Query CSV found")
        return []

    # Pick the newest file
    latest = max(files, key=lambda f: Path(f).stat().st_mtime)
    log.info(f"Loading CSV: {latest}")

    with open(latest, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _get_rep_leads(rows: list[dict], deal_owner: str) -> list[dict]:
    """Filter leads for a specific deal owner."""
    owner_lower = deal_owner.lower()
    return [
        r for r in rows
        if owner_lower in (_clean(r.get("deal_owner", "")).lower())
        or owner_lower in (_clean(r.get("lead_owner", "")).lower())
    ]


def _current_month_demos(rows: list[dict]) -> list[dict]:
    """Filter demos done in the current month by demo_date."""
    now = datetime.now()
    demos = []
    for r in rows:
        dd = _clean(r.get("demo_date", ""))
        dt = _parse_date(dd)
        if dt and dt.year == now.year and dt.month == now.month:
            demos.append(r)
    return demos


# ---------------------------------------------------------------------------
# Metrics Computation
# ---------------------------------------------------------------------------

def _compute_all_rep_metrics(demos: list[dict], all_rows: list[dict]) -> dict:
    """Compute metrics for all reps from current month demos."""
    rep_data = defaultdict(lambda: {
        "demos": 0, "sales": 0, "revenue": 0,
        "missing_remark": 0, "missing_price": 0, "missing_followup": 0,
        "vhp": 0, "hp": 0, "prospect": 0,
        "pipeline_value": 0,
    })

    for r in demos:
        owner = _clean(r.get("deal_owner", "")) or _clean(r.get("lead_owner", ""))
        if not owner:
            continue
        d = rep_data[owner]
        d["demos"] += 1
        if "3. Sale Done" in _clean(r.get("sales_stage", "")):
            d["sales"] += 1
            d["revenue"] += _parse_rupee(r.get("price_pitched", ""))
        if not _clean(r.get("remark", "")):
            d["missing_remark"] += 1
        if not _parse_rupee(r.get("price_pitched", "")):
            d["missing_price"] += 1
        if not _clean(r.get("exp_closure_date", "")):
            d["missing_followup"] += 1

        stage = _clean(r.get("sales_stage", ""))
        if "Very High" in stage:
            d["vhp"] += 1
        elif stage == "High Prospect":
            d["hp"] += 1
        elif "1. Prospect" in stage:
            d["prospect"] += 1
        d["pipeline_value"] += _parse_rupee(r.get("price_pitched", ""))

    return dict(rep_data)


# ---------------------------------------------------------------------------
# Report 1: Team Overview (Managers only)
# ---------------------------------------------------------------------------

def generate_team_overview(demos: list[dict], all_rows: list[dict]) -> str:
    rep_metrics = _compute_all_rep_metrics(demos, all_rows)
    now = datetime.now()
    month = now.strftime("%B %Y")

    total_demos = sum(d["demos"] for d in rep_metrics.values())
    total_sales = sum(d["sales"] for d in rep_metrics.values())
    total_revenue = sum(d["revenue"] for d in rep_metrics.values())

    # All-time pipeline
    vhp_all = [r for r in all_rows if "Very High" in _clean(r.get("sales_stage", ""))]
    hp_all = [r for r in all_rows if _clean(r.get("sales_stage", "")) == "High Prospect"]
    prospect_all = [r for r in all_rows if "1. Prospect" in _clean(r.get("sales_stage", ""))]
    pipeline = (
        sum(_parse_rupee(r.get("price_pitched", "")) for r in vhp_all)
        + sum(_parse_rupee(r.get("price_pitched", "")) for r in hp_all)
        + sum(_parse_rupee(r.get("price_pitched", "")) for r in prospect_all)
    )

    # Conversion ranking
    ranked = sorted(rep_metrics.items(), key=lambda x: -x[1]["sales"] / max(x[1]["demos"], 1))
    ranked = [(o, d) for o, d in ranked if d["demos"] >= 3]

    # Top 3 / Bottom 3
    top3 = ranked[:3]
    bottom3 = ranked[-3:] if len(ranked) >= 6 else ranked[max(0, len(ranked)-3):]

    lines = [
        f"📊 ONSITE — Team Overview | {month}",
        "═══════════════════════════\n",
        f"🎯 Demos: {total_demos} / {DEMO_TARGET} target ({total_demos - DEMO_TARGET:+d})",
        f"💰 Sales: {total_sales} deals | {_fmt_lakhs(total_revenue)}",
        f"📈 Pipeline: {_fmt_lakhs(pipeline)} (VHP: {len(vhp_all)} | HP: {len(hp_all)} | Prospect: {len(prospect_all)})\n",
        "🏆 CONVERSION RANKING",
        "─────────────────",
    ]

    for i, (owner, d) in enumerate(ranked[:10], 1):
        conv = d["sales"] / d["demos"] * 100 if d["demos"] else 0
        hygiene = (1 - d["missing_remark"] / max(d["demos"], 1)) * 100
        lines.append(f"{i}. {owner}: {conv:.0f}% ({d['sales']}/{d['demos']}) | Data: {hygiene:.0f}%")

    lines.append("\n✅ TOP PERFORMERS")
    lines.append("─────────────────")
    for owner, d in top3:
        conv = d["sales"] / d["demos"] * 100 if d["demos"] else 0
        lines.append(f"  {owner} — {conv:.0f}% conversion, {d['demos']} demos")

    lines.append("\n⚠️ NEEDS ATTENTION")
    lines.append("─────────────────")
    for owner, d in bottom3:
        conv = d["sales"] / d["demos"] * 100 if d["demos"] else 0
        hygiene = (1 - d["missing_remark"] / max(d["demos"], 1)) * 100
        lines.append(f"  {owner} — {conv:.0f}% conversion, {hygiene:.0f}% data filled")

    lines.append("\n— Onsite Sales Intelligence")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Report 2: Rep Scorecard (Per rep)
# ---------------------------------------------------------------------------

def generate_rep_scorecard(demos: list[dict], all_rows: list[dict], deal_owner: str) -> str:
    rep_metrics = _compute_all_rep_metrics(demos, all_rows)
    me = rep_metrics.get(deal_owner, {})
    if not me or me.get("demos", 0) == 0:
        return ""

    # Rank
    ranked = sorted(rep_metrics.items(), key=lambda x: -x[1]["sales"] / max(x[1]["demos"], 1))
    ranked = [(o, d) for o, d in ranked if d["demos"] >= 3]
    my_rank = next((i for i, (o, _) in enumerate(ranked, 1) if o == deal_owner), len(ranked))
    total_reps = len(ranked)

    # Team averages
    avg_demos = sum(d["demos"] for d in rep_metrics.values()) / max(len(rep_metrics), 1)
    avg_conv = sum(d["sales"] for d in rep_metrics.values()) / max(sum(d["demos"] for d in rep_metrics.values()), 1) * 100

    my_conv = me["sales"] / me["demos"] * 100 if me["demos"] else 0
    hygiene_remark = (1 - me["missing_remark"] / max(me["demos"], 1)) * 100
    hygiene_price = (1 - me["missing_price"] / max(me["demos"], 1)) * 100

    # My pipeline from all rows
    my_leads = _get_rep_leads(all_rows, deal_owner)
    my_vhp = len([r for r in my_leads if "Very High" in _clean(r.get("sales_stage", ""))])
    my_hp = len([r for r in my_leads if _clean(r.get("sales_stage", "")) == "High Prospect"])
    my_pipeline = sum(
        _parse_rupee(r.get("price_pitched", ""))
        for r in my_leads
        if _clean(r.get("sales_stage", "")) in ("Very High Prospect", "High Prospect")
    )

    now = datetime.now()
    month = now.strftime("%B %Y")
    name = REP_CONTACTS.get(deal_owner, {}).get("name", deal_owner.split()[0])

    lines = [
        f"📋 ONSITE — {name}'s Scorecard | {month}",
        "═══════════════════════════\n",
        f"🎯 Demos Done: {me['demos']}",
        f"💰 Sales Closed: {me['sales']} | {_fmt_lakhs(me['revenue'])}",
        f"📊 Conversion: {my_conv:.0f}% (team avg: {avg_conv:.0f}%)",
        f"🏅 Rank: #{my_rank} out of {total_reps} reps\n",
        "📝 DATA HYGIENE",
        "─────────────────",
        f"  Remarks filled: {hygiene_remark:.0f}%{'  ✅' if hygiene_remark >= 80 else '  ❌ needs improvement'}",
        f"  Price pitched: {hygiene_price:.0f}%{'  ✅' if hygiene_price >= 80 else '  ❌ needs improvement'}",
        f"\n🔥 YOUR PIPELINE",
        "─────────────────",
        f"  Very High Prospect: {my_vhp}",
        f"  High Prospect: {my_hp}",
        f"  Pipeline Value: {_fmt_lakhs(my_pipeline)}",
    ]

    if my_conv > avg_conv:
        lines.append(f"\n🌟 You're above team average! Keep it up {name}!")
    else:
        lines.append(f"\n💪 Push harder {name} — close {my_vhp} VHP leads to jump up!")

    lines.append("\n— Onsite Sales Intelligence")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Report 3: Stale Pipeline Alert (Per rep)
# ---------------------------------------------------------------------------

def generate_stale_pipeline(all_rows: list[dict], deal_owner: str) -> str:
    my_leads = _get_rep_leads(all_rows, deal_owner)
    hot = [
        r for r in my_leads
        if _clean(r.get("sales_stage", "")) in ("Very High Prospect", "High Prospect", "1. Prospect")
    ]

    stale = []
    for r in hot:
        lt = _clean(r.get("last_touched_date_new", "")) or _clean(r.get("last_touched_date", ""))
        days = _days_since(lt)
        if days >= 7:
            stale.append((days, r))
    stale.sort(key=lambda x: -x[0])

    if not stale:
        return ""

    total_at_risk = sum(_parse_rupee(r.get("price_pitched", "")) for _, r in stale)
    name = REP_CONTACTS.get(deal_owner, {}).get("name", deal_owner.split()[0])

    lines = [
        f"⚠️ ONSITE — Stale Leads Alert | {name}",
        "═══════════════════════════",
        f"\n{len(stale)} hot leads NOT touched in 7+ days!",
        f"💰 Pipeline at risk: {_fmt_lakhs(total_at_risk)}\n",
        "📞 TOP 10 — CALL ASAP",
        "─────────────────",
    ]

    for i, (days, r) in enumerate(stale[:10], 1):
        phone = _clean(r.get("lead_phone", ""))
        remark = _clean(r.get("remark", ""))
        price = _parse_rupee(r.get("price_pitched", ""))
        stage = _clean(r.get("sales_stage", ""))
        price_str = f" | {_fmt_lakhs(price)}" if price else ""
        remark_str = f'\n   📝 "{remark[:70]}"' if remark else "\n   📝 No remark ❌"
        lines.append(f"{i}. {phone} | {stage} | {days}d ago{price_str}{remark_str}")

    lines.append(f'\n💡 Script: "Hi, checking in — we\'ve added new features. Quick 5-min update?"')
    lines.append("\n— Onsite Sales Intelligence")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Report 4: Quick Wins (Per rep)
# ---------------------------------------------------------------------------

def generate_quick_wins(all_rows: list[dict], deal_owner: str) -> str:
    my_leads = _get_rep_leads(all_rows, deal_owner)

    # Score leads for "closability"
    positive_signals = [
        "will get back", "will discuss", "will pay", "will finalize", "will proceed",
        "will purchase", "interested", "trial", "quote sent", "sent quote",
        "will start", "will close", "liked", "good demo",
    ]

    scored = []
    for r in my_leads:
        stage = _clean(r.get("sales_stage", ""))
        if stage in ("3. Sale Done", "4. Secondary Sales", "2. Not Interested After Demo",
                      "Rejected", "User not attend session", ""):
            continue
        if stage not in ("Very High Prospect", "High Prospect", "1. Prospect", "Demo Done", "Demo Booked"):
            continue

        score = 0
        remark = _clean(r.get("remark", "")).lower()
        notes = _clean(r.get("lead_notes", "")).lower()
        price = _parse_rupee(r.get("price_pitched", ""))

        if price > 0:
            score += 20
        if price <= 50000 and price > 0:
            score += 15  # small = fast close
        if _clean(r.get("trial_activated", "")).lower() in ("1", "yes", "true"):
            score += 25
        if "Very High" in stage:
            score += 20
        elif stage == "High Prospect":
            score += 15
        for sig in positive_signals:
            if sig in remark or sig in notes:
                score += 10
                break
        # Recent touch = warmer
        days = _days_since(_clean(r.get("last_touched_date_new", "")))
        if days <= 7:
            score += 15
        elif days <= 14:
            score += 10
        elif days <= 30:
            score += 5

        if score >= 20:
            scored.append((score, r))

    scored.sort(key=lambda x: -x[0])

    if not scored:
        return ""

    name = REP_CONTACTS.get(deal_owner, {}).get("name", deal_owner.split()[0])

    lines = [
        f"⚡ ONSITE — Quick Wins | {name}",
        "═══════════════════════════",
        "\nTop 5 leads most likely to close:\n",
    ]

    for i, (score, r) in enumerate(scored[:5], 1):
        phone = _clean(r.get("lead_phone", ""))
        remark = _clean(r.get("remark", ""))
        price = _parse_rupee(r.get("price_pitched", ""))
        stage = _clean(r.get("sales_stage", ""))
        lt = _clean(r.get("last_touched_date_new", ""))
        price_str = f" | {_fmt_lakhs(price)}" if price else ""

        lines.append(f"{i}️⃣ {phone} | {stage}{price_str}")
        if remark:
            lines.append(f"   📝 {remark[:80]}")
        if lt:
            lines.append(f"   📅 Last touch: {lt[:12]}")
        lines.append("")

    total_val = sum(_parse_rupee(r.get("price_pitched", "")) for _, r in scored[:5])
    if total_val:
        lines.append(f"📞 Close all 5 = {_fmt_lakhs(total_val)} revenue!")

    lines.append("\n— Onsite Sales Intelligence")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Report 5: Data Hygiene Report Card (Managers / Team group)
# ---------------------------------------------------------------------------

def generate_hygiene_report(demos: list[dict]) -> str:
    rep_metrics = defaultdict(lambda: {"demos": 0, "has_remark": 0, "has_price": 0})

    for r in demos:
        owner = _clean(r.get("deal_owner", "")) or _clean(r.get("lead_owner", ""))
        if not owner:
            continue
        rep_metrics[owner]["demos"] += 1
        if _clean(r.get("remark", "")):
            rep_metrics[owner]["has_remark"] += 1
        if _parse_rupee(r.get("price_pitched", "")):
            rep_metrics[owner]["has_price"] += 1

    total_demos = sum(d["demos"] for d in rep_metrics.values())

    # Sort by hygiene score (best first)
    ranked = sorted(
        [(o, d) for o, d in rep_metrics.items() if d["demos"] >= 3],
        key=lambda x: -x[1]["has_remark"] / max(x[1]["demos"], 1),
    )

    now = datetime.now()
    month = now.strftime("%B %Y")

    lines = [
        f"📋 ONSITE — Friday Report Card | {month}",
        "═══════════════════════════\n",
        f"🎯 Demos this month: {total_demos} / {DEMO_TARGET} target",
        f"{'✅ On track!' if total_demos >= DEMO_TARGET * 0.8 else '❌ Behind target — need ' + str(DEMO_TARGET - total_demos) + ' more demos'}\n",
        "📊 DATA HYGIENE LEADERBOARD",
        "─────────────────",
    ]

    for i, (owner, d) in enumerate(ranked, 1):
        pct = d["has_remark"] / d["demos"] * 100
        price_pct = d["has_price"] / d["demos"] * 100
        if pct >= 90:
            grade = "A+ 🏆"
        elif pct >= 75:
            grade = "A"
        elif pct >= 50:
            grade = "B"
        elif pct >= 25:
            grade = "C"
        else:
            grade = "D ❌"
        lines.append(f"  {i}. {owner}: {pct:.0f}% remarks | {price_pct:.0f}% price | {grade}")

    # Shoutouts
    if ranked:
        lines.append(f"\n🌟 SHOUTOUT: {ranked[0][0]} — best data hygiene!")
        if len(ranked) >= 2:
            lines.append(f"🌟 Runner-up: {ranked[1][0]}")

    lines.append("\n📌 REMINDER: After every demo, update:")
    lines.append("  ✅ Remark — What happened?")
    lines.append("  ✅ Price Pitched — What you quoted")
    lines.append("  ✅ Follow-up Date — Next call when?")
    lines.append("\nBetter data = Better follow-ups = More sales 💰")
    lines.append("\n— Onsite Sales Intelligence")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Orchestrators
# ---------------------------------------------------------------------------

async def send_friday_reports():
    """Friday 6 PM IST — Week review: Team Overview + Rep Scorecards + Hygiene Report Card."""
    log.info("Starting Friday weekly review reports...")
    rows = _load_csv_data()
    if not rows:
        log.error("No CSV data found, skipping Friday reports")
        return {"status": "failed", "error": "no_csv_data"}

    demos = _current_month_demos(rows)
    results = {"sent": 0, "failed": 0, "reports": []}

    # Report 1: Team Overview → Managers
    overview = generate_team_overview(demos, rows)
    for phone in MANAGER_PHONES:
        try:
            r = await send_whatsapp_message(phone=phone, message=overview, name="Manager", use_template=False)
            if r.get("status") == "sent":
                results["sent"] += 1
            else:
                results["failed"] += 1
            results["reports"].append({"type": "team_overview", "phone": phone, "status": r.get("status")})
        except Exception as e:
            log.error(f"Failed to send team overview to {phone}: {e}")
            results["failed"] += 1

    # Report 2: Rep Scorecard → Each rep
    for deal_owner, contact in REP_CONTACTS.items():
        scorecard = generate_rep_scorecard(demos, rows, deal_owner)
        if not scorecard:
            continue
        try:
            r = await send_whatsapp_message(
                phone=contact["phone"], message=scorecard,
                name=contact["name"], use_template=False,
            )
            if r.get("status") == "sent":
                results["sent"] += 1
            else:
                results["failed"] += 1
            results["reports"].append({"type": "scorecard", "rep": deal_owner, "status": r.get("status")})
        except Exception as e:
            log.error(f"Failed to send scorecard to {deal_owner}: {e}")
            results["failed"] += 1

    # Report 5: Hygiene Report Card → Managers
    hygiene = generate_hygiene_report(demos)
    for phone in MANAGER_PHONES:
        try:
            r = await send_whatsapp_message(phone=phone, message=hygiene, name="Manager", use_template=False)
            if r.get("status") == "sent":
                results["sent"] += 1
            else:
                results["failed"] += 1
            results["reports"].append({"type": "hygiene_report", "phone": phone, "status": r.get("status")})
        except Exception as e:
            log.error(f"Failed to send hygiene report to {phone}: {e}")
            results["failed"] += 1

    log.info(f"Friday reports done: {results['sent']} sent, {results['failed']} failed")
    return results


async def send_monday_reports():
    """Monday 8 AM IST — Week kickoff: Stale Pipeline + Quick Wins per rep."""
    log.info("Starting Monday weekly kickoff reports...")
    rows = _load_csv_data()
    if not rows:
        log.error("No CSV data found, skipping Monday reports")
        return {"status": "failed", "error": "no_csv_data"}

    results = {"sent": 0, "failed": 0, "reports": []}

    for deal_owner, contact in REP_CONTACTS.items():
        # Report 3: Stale Pipeline
        stale = generate_stale_pipeline(rows, deal_owner)
        if stale:
            try:
                r = await send_whatsapp_message(
                    phone=contact["phone"], message=stale,
                    name=contact["name"], use_template=False,
                )
                if r.get("status") == "sent":
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                results["reports"].append({"type": "stale_pipeline", "rep": deal_owner, "status": r.get("status")})
            except Exception as e:
                log.error(f"Failed to send stale pipeline to {deal_owner}: {e}")
                results["failed"] += 1

        # Report 4: Quick Wins
        wins = generate_quick_wins(rows, deal_owner)
        if wins:
            try:
                r = await send_whatsapp_message(
                    phone=contact["phone"], message=wins,
                    name=contact["name"], use_template=False,
                )
                if r.get("status") == "sent":
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                results["reports"].append({"type": "quick_wins", "rep": deal_owner, "status": r.get("status")})
            except Exception as e:
                log.error(f"Failed to send quick wins to {deal_owner}: {e}")
                results["failed"] += 1

    # Also send stale + quick wins summary to managers
    for phone in MANAGER_PHONES:
        # Managers get a condensed version
        all_stale = []
        for r in rows:
            stage = _clean(r.get("sales_stage", ""))
            if stage not in ("Very High Prospect", "High Prospect"):
                continue
            lt = _clean(r.get("last_touched_date_new", "")) or _clean(r.get("last_touched_date", ""))
            days = _days_since(lt)
            if days >= 7:
                all_stale.append(r)

        if all_stale:
            msg = (
                f"📊 ONSITE — Monday Pipeline Alert\n"
                f"═══════════════════════════\n\n"
                f"⚠️ {len(all_stale)} hot leads (VHP+HP) untouched 7+ days across team.\n"
                f"💰 Pipeline at risk: {_fmt_lakhs(sum(_parse_rupee(r.get('price_pitched','')) for r in all_stale))}\n\n"
                f"Reports sent to each rep with their individual stale leads + quick wins.\n\n"
                f"— Onsite Sales Intelligence"
            )
            try:
                await send_whatsapp_message(phone=phone, message=msg, name="Manager", use_template=False)
                results["sent"] += 1
            except Exception as e:
                log.error(f"Failed to send manager summary to {phone}: {e}")

    log.info(f"Monday reports done: {results['sent']} sent, {results['failed']} failed")
    return results

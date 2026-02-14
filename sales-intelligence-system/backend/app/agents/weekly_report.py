"""Weekly Report Agent — runs every Monday 8 AM, generates comprehensive report for founder + managers."""

import json
import logging
from datetime import datetime, timedelta, timezone, date

from app.core.llm import tracked_llm_call
from app.core.supabase_client import get_supabase_admin
from app.services.email import send_weekly_report_email

log = logging.getLogger(__name__)

WEEKLY_REPORT_PROMPT = """You are a senior sales analytics AI for a construction SaaS company (Onsite Teams).
Generate a comprehensive weekly sales intelligence report.

DATA FOR THIS WEEK ({week_start} to {week_end}):

PIPELINE SUMMARY:
{pipeline_summary}

PER-REP PERFORMANCE:
{rep_performance}

LEAD SOURCE BREAKDOWN:
{source_breakdown}

DEALS WON THIS WEEK:
{deals_won}

DEALS LOST THIS WEEK:
{deals_lost}

STALE LEADS (7+ days no activity):
{stale_count} leads with no activity

LAST WEEK'S METRICS (for comparison):
{last_week_metrics}

Generate a report with these sections:

1. **Executive Summary** (3-4 sentences: what happened this week, key wins, key concerns)

2. **Pipeline Health**
   - Total leads, new leads this week, stage distribution
   - Pipeline value by stage
   - Week-over-week change

3. **Team Performance Scorecard**
   - For each rep: calls made, leads handled, conversion rate, revenue
   - Traffic light status: GREEN (on track), YELLOW (needs attention), RED (action required)
   - Who's outperforming, who needs support

4. **Source Analysis**
   - Which lead sources are converting best
   - Cost-per-acquisition insights if data available
   - Recommendation: where to invest more

5. **AI Insights** (the most valuable section)
   - Patterns you see in the data
   - Anomalies or concerning trends
   - Specific actionable recommendations (e.g., "Ravi has 4 hot leads but made only 2 calls this week. Schedule a check-in.")
   - Predictions: deals likely to close this month based on stage + activity

6. **Revenue Forecast**
   - Expected closings this month based on pipeline health
   - Confidence level (high/medium/low) for each deal

7. **Action Items for Next Week**
   - Top 3 things the team should focus on

Keep it data-driven, specific, and actionable. No generic advice. Reference actual names, companies, and numbers.
Format for email readability (headers, bullets, bold for key numbers).
"""


async def run_weekly_report():
    """Generate and send weekly report."""
    db = get_supabase_admin()
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)
    last_week_start = week_start - timedelta(days=7)

    log.info(f"Generating weekly report for {week_start} to {week_end}")

    # Gather all data
    try:
        # Pipeline summary
        pipeline = db.table("leads").select("stage, deal_value").not_("stage", "in", "(won,lost)").execute()
        pipeline_summary = _summarize_pipeline(pipeline.data)

        # Rep performance (use the view)
        rep_perf = db.table("v_rep_performance").select("*").execute()

        # Source breakdown
        source_data = db.table("leads").select("source, stage, deal_value").execute()
        source_breakdown = _summarize_sources(source_data.data)

        # Deals won/lost this week
        won = db.table("leads").select("company, deal_value, assigned_rep_id, contact_name").eq(
            "stage", "won"
        ).gte("updated_at", week_start.isoformat()).execute()

        lost = db.table("leads").select("company, deal_value, assigned_rep_id, contact_name").eq(
            "stage", "lost"
        ).gte("updated_at", week_start.isoformat()).execute()

        # Stale leads count
        stale = db.table("leads").select("id", count="exact").not_(
            "stage", "in", "(won,lost)"
        ).lt("last_activity_at", (today - timedelta(days=7)).isoformat()).execute()

        # Last week's report for comparison
        last_report = db.table("weekly_reports").select("metrics").eq(
            "week_start", last_week_start.isoformat()
        ).execute()
        last_week_metrics = json.dumps(last_report.data[0]["metrics"]) if last_report.data else "No data from last week"

        # Build prompt
        prompt = WEEKLY_REPORT_PROMPT.format(
            week_start=week_start.isoformat(),
            week_end=week_end.isoformat(),
            pipeline_summary=json.dumps(pipeline_summary, default=str),
            rep_performance=json.dumps(rep_perf.data, default=str),
            source_breakdown=json.dumps(source_breakdown, default=str),
            deals_won=json.dumps(won.data, default=str),
            deals_lost=json.dumps(lost.data, default=str),
            stale_count=stale.count if stale.count else 0,
            last_week_metrics=last_week_metrics,
        )

        # Generate report with Sonnet
        response = await tracked_llm_call("weekly_report", [{"role": "user", "content": prompt}])
        report_content = response.content

        # Save to DB
        metrics = {
            "pipeline": pipeline_summary,
            "rep_performance": rep_perf.data,
            "source_breakdown": source_breakdown,
            "deals_won": len(won.data),
            "deals_lost": len(lost.data),
            "stale_leads": stale.count or 0,
        }

        db.table("weekly_reports").upsert({
            "report_content": report_content,
            "insights": report_content,  # Full report as insights
            "metrics": metrics,
            "week_start": week_start.isoformat(),
        }, on_conflict="week_start").execute()

        # Send to founder + managers
        managers = db.table("users").select("email, name").in_(
            "role", ["founder", "manager"]
        ).eq("is_active", True).execute()

        for user in managers.data:
            await send_weekly_report_email(
                to=user["email"],
                report_content=report_content,
                week_str=f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}",
            )

            # Log alert
            db.table("alerts").insert({
                "alert_type": "weekly_report",
                "message": f"Weekly report for {week_start.isoformat()}",
                "target_user_id": user.get("id", managers.data[0].get("id")),
                "channel": "email",
                "delivered": True,
            }).execute()

        log.info(f"Weekly report generated and sent to {len(managers.data)} recipients")
        return {"status": "success", "recipients": len(managers.data)}

    except Exception as e:
        log.error(f"Weekly report failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}


def _summarize_pipeline(leads: list) -> dict:
    """Summarize pipeline by stage."""
    summary = {}
    for lead in leads:
        stage = lead.get("stage", "unknown")
        if stage not in summary:
            summary[stage] = {"count": 0, "value": 0}
        summary[stage]["count"] += 1
        summary[stage]["value"] += float(lead.get("deal_value") or 0)
    return summary


def _summarize_sources(leads: list) -> dict:
    """Summarize leads by source with conversion rates."""
    sources = {}
    for lead in leads:
        source = lead.get("source", "unknown")
        if source not in sources:
            sources[source] = {"total": 0, "won": 0, "lost": 0, "value": 0}
        sources[source]["total"] += 1
        if lead.get("stage") == "won":
            sources[source]["won"] += 1
            sources[source]["value"] += float(lead.get("deal_value") or 0)
        elif lead.get("stage") == "lost":
            sources[source]["lost"] += 1

    # Add conversion rates
    for source in sources.values():
        closed = source["won"] + source["lost"]
        source["conversion_rate"] = round(source["won"] / closed * 100, 1) if closed > 0 else 0

    return sources

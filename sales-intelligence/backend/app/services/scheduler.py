"""APScheduler — runs agents on schedule."""

import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

log = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _run_daily_pipeline():
    """Wrapper for daily pipeline agent."""
    try:
        from app.agents.daily_pipeline import run_daily_pipeline
        log.info("Starting daily pipeline agent (7:30 AM run)")
        await run_daily_pipeline()
        log.info("Daily pipeline complete")
    except Exception as e:
        log.error(f"Daily pipeline failed: {e}", exc_info=True)


async def _run_delta_sync():
    """Wrapper for Zoho delta sync."""
    try:
        from app.services.zoho_sync import run_delta_sync
        log.info("Starting delta sync")
        await run_delta_sync()
    except Exception as e:
        log.error(f"Delta sync failed: {e}", exc_info=True)


async def _run_full_sync():
    """Wrapper for Zoho full sync (safety net)."""
    try:
        from app.services.zoho_sync import run_full_sync
        log.info("Starting full sync (2 AM safety net)")
        await run_full_sync()
    except Exception as e:
        log.error(f"Full sync failed: {e}", exc_info=True)


async def _run_weekly_report():
    """Wrapper for weekly report agent."""
    try:
        from app.agents.weekly_report import run_weekly_report
        log.info("Starting weekly report agent (Monday 8 AM)")
        await run_weekly_report()
    except Exception as e:
        log.error(f"Weekly report failed: {e}", exc_info=True)


async def _run_morning_digest():
    """Morning digest: today's focus. Part of 2–3 daily notifications."""
    try:
        from app.services.digests import send_morning_digests_to_all
        log.info("Starting morning digest (8 AM)")
        result = await send_morning_digests_to_all()
        log.info("Morning digest done: sent=%s", result.get("sent", 0))
    except Exception as e:
        log.error("Morning digest failed: %s", e, exc_info=True)


async def _run_afternoon_digest():
    """Afternoon digest: rest of day. Part of 2–3 daily notifications."""
    try:
        from app.services.digests import send_afternoon_digests_to_all
        log.info("Starting afternoon digest (2 PM)")
        result = await send_afternoon_digests_to_all()
        log.info("Afternoon digest done: sent=%s", result.get("sent", 0))
    except Exception as e:
        log.error("Afternoon digest failed: %s", e, exc_info=True)


async def _run_evening_summary():
    """Evening summary: tomorrow's focus. Part of 2–3 daily notifications."""
    try:
        from app.services.digests import send_evening_summaries_to_all
        log.info("Starting evening summary (6 PM)")
        result = await send_evening_summaries_to_all()
        log.info("Evening summary done: sent=%s", result.get("sent", 0))
    except Exception as e:
        log.error("Evening summary failed: %s", e, exc_info=True)


async def _run_followup_check():
    """Check for due follow-ups and send reminders. Every 15 min."""
    try:
        from app.services.followup_reminders import check_and_send_reminders
        result = await check_and_send_reminders()
        if result.get("sent", 0) > 0:
            log.info("Follow-up reminders: sent %s", result["sent"])
    except Exception as e:
        log.error("Follow-up check failed: %s", e, exc_info=True)


async def _run_morning_followup_summary():
    """Send morning summary of today's follow-ups to each rep. 8 AM IST."""
    try:
        from app.services.followup_reminders import send_morning_followup_summary
        log.info("Starting morning follow-up summary (8 AM)")
        result = await send_morning_followup_summary()
        log.info("Morning follow-up summary: sent=%s", result.get("sent", 0))
    except Exception as e:
        log.error("Morning follow-up summary failed: %s", e, exc_info=True)


async def _run_friday_weekly_review():
    """Friday 6 PM IST — Team Overview + Rep Scorecards + Hygiene Report Card."""
    try:
        from app.services.weekly_reports import send_friday_reports
        log.info("Starting Friday weekly review (6 PM)")
        result = await send_friday_reports()
        log.info("Friday review done: sent=%s, failed=%s", result.get("sent", 0), result.get("failed", 0))
    except Exception as e:
        log.error("Friday weekly review failed: %s", e, exc_info=True)


async def _run_monday_weekly_kickoff():
    """Monday 8 AM IST — Stale Pipeline + Quick Wins per rep."""
    try:
        from app.services.weekly_reports import send_monday_reports
        log.info("Starting Monday weekly kickoff (8 AM)")
        result = await send_monday_reports()
        log.info("Monday kickoff done: sent=%s, failed=%s", result.get("sent", 0), result.get("failed", 0))
    except Exception as e:
        log.error("Monday weekly kickoff failed: %s", e, exc_info=True)


def start_scheduler():
    """Start all scheduled jobs. Called on app startup."""
    # Daily pipeline: 7:30 AM IST (2:00 AM UTC)
    scheduler.add_job(
        _run_daily_pipeline,
        "cron",
        hour=2, minute=0,  # 7:30 AM IST = 2:00 AM UTC
        id="daily_pipeline",
        replace_existing=True,
    )

    # Delta sync: every 2 hours during business hours (8 AM - 10 PM IST)
    scheduler.add_job(
        _run_delta_sync,
        "cron",
        hour="2,4,6,8,10,12,14,16",  # UTC hours covering IST business hours
        minute=30,
        id="delta_sync",
        replace_existing=True,
    )

    # Full sync: 2 AM IST (8:30 PM UTC previous day)
    scheduler.add_job(
        _run_full_sync,
        "cron",
        hour=20, minute=30,  # 2 AM IST = 8:30 PM UTC
        id="full_sync",
        replace_existing=True,
    )

    # Weekly report: Monday 8 AM IST (2:30 AM UTC)
    scheduler.add_job(
        _run_weekly_report,
        "cron",
        day_of_week="mon",
        hour=2, minute=30,
        id="weekly_report",
        replace_existing=True,
    )

    # 2–3 daily notifications (UTC: 8 AM IST = 2:30, 2 PM IST = 8:30, 6 PM IST = 12:30)
    scheduler.add_job(
        _run_morning_digest,
        "cron",
        hour=2, minute=30,
        id="morning_digest",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_afternoon_digest,
        "cron",
        hour=8, minute=30,
        id="afternoon_digest",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_evening_summary,
        "cron",
        hour=12, minute=30,
        id="evening_summary",
        replace_existing=True,
    )

    # Follow-up reminders: every 15 minutes during business hours (8 AM - 8 PM IST = 2:30 - 14:30 UTC)
    scheduler.add_job(
        _run_followup_check,
        "interval",
        minutes=15,
        id="followup_check",
        replace_existing=True,
    )

    # Morning follow-up summary: 8 AM IST (2:30 AM UTC)
    scheduler.add_job(
        _run_morning_followup_summary,
        "cron",
        hour=2, minute=30,
        id="morning_followup_summary",
        replace_existing=True,
    )

    # Friday weekly review: 6 PM IST (12:30 PM UTC)
    scheduler.add_job(
        _run_friday_weekly_review,
        "cron",
        day_of_week="fri",
        hour=12, minute=30,
        id="friday_weekly_review",
        replace_existing=True,
    )

    # Monday weekly kickoff: 8 AM IST (2:30 AM UTC)
    scheduler.add_job(
        _run_monday_weekly_kickoff,
        "cron",
        day_of_week="mon",
        hour=2, minute=45,  # 8:15 AM IST (offset from other 8 AM jobs)
        id="monday_weekly_kickoff",
        replace_existing=True,
    )

    scheduler.start()
    log.info(
        "Scheduler started: daily_pipeline, delta_sync, full_sync, weekly_report, "
        "morning_digest (8AM), afternoon_digest (2PM), evening_summary (6PM), "
        "followup_check (every 15min), morning_followup_summary (8AM), "
        "friday_weekly_review (Fri 6PM), monday_weekly_kickoff (Mon 8:15AM)"
    )


def stop_scheduler():
    """Stop scheduler on app shutdown."""
    if scheduler.running:
        scheduler.shutdown()
        log.info("Scheduler stopped")

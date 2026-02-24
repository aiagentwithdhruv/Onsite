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

    scheduler.start()
    log.info("Scheduler started: daily_pipeline (7:30AM), delta_sync (every 2h), full_sync (2AM), weekly_report (Mon 8AM)")


def stop_scheduler():
    """Stop scheduler on app shutdown."""
    if scheduler.running:
        scheduler.shutdown()
        log.info("Scheduler stopped")

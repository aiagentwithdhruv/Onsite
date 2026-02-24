"""Cron endpoints for scheduled jobs (afternoon digest, evening summary, intelligence briefs).
Call from n8n or system cron. Optional: set X-Cron-Secret header to match settings.secret_key."""

import logging
from fastapi import APIRouter, Header, HTTPException

from app.core.config import get_settings
from app.services.digests import send_morning_digests_to_all, send_afternoon_digests_to_all, send_evening_summaries_to_all
from app.services.intelligence_brief import generate_and_save_intelligence_briefs

log = logging.getLogger(__name__)
router = APIRouter()


def _check_cron_secret(x_cron_secret: str | None = Header(None, alias="X-Cron-Secret")):
    """Optional: require X-Cron-Secret to match settings.secret_key to prevent public abuse."""
    settings = get_settings()
    if not settings.secret_key or settings.secret_key == "change-this":
        return  # dev: allow without secret
    if not x_cron_secret or x_cron_secret.strip() != settings.secret_key:
        raise HTTPException(status_code=403, detail="Invalid or missing X-Cron-Secret")


@router.post("/morning-digest")
async def trigger_morning_digest(x_cron_secret: str | None = Header(None, alias="X-Cron-Secret")):
    """Send morning 'today's focus' digest. One of 2–3 daily notifications. Schedule e.g. 8 AM."""
    _check_cron_secret(x_cron_secret)
    result = await send_morning_digests_to_all()
    return {"ok": True, **result}


@router.post("/afternoon-digest")
async def trigger_afternoon_digest(x_cron_secret: str | None = Header(None, alias="X-Cron-Secret")):
    """Send afternoon 'rest of day' digest. One of 2–3 daily notifications. Schedule e.g. 2 PM."""
    _check_cron_secret(x_cron_secret)
    result = await send_afternoon_digests_to_all()
    return {"ok": True, **result}


@router.post("/evening-summary")
async def trigger_evening_summary(x_cron_secret: str | None = Header(None, alias="X-Cron-Secret")):
    """Send evening summary to all users. Schedule e.g. 6 PM."""
    _check_cron_secret(x_cron_secret)
    result = await send_evening_summaries_to_all()
    return {"ok": True, **result}


@router.post("/generate-intelligence-briefs")
async def trigger_generate_intelligence_briefs(x_cron_secret: str | None = Header(None, alias="X-Cron-Secret")):
    """Generate today's briefs from Intelligence summary + agent profiles (no Zoho). Schedule e.g. 7 AM or call after CSV upload."""
    _check_cron_secret(x_cron_secret)
    result = generate_and_save_intelligence_briefs()
    return {"ok": True, **result}

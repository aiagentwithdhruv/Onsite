"""Webhook receivers — Zoho CRM real-time lead sync via workflow webhooks.

Instead of polling Zoho with OAuth, Zoho pushes lead updates to us via
workflow rules → webhook action. Same pattern as the existing Zoho → Gallabox
webhook (Gallabox_1), but pointed at our API.

Two Zoho workflows:
  Workflow 1 (lead-update): Fires on status/source/stage changes → syncs lead data
  Workflow 2 (follow-up):   Fires on follow-up date changes → schedules reminders
"""

import json
import logging
import hashlib
from datetime import datetime, timezone, date, time as dt_time

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.supabase_client import get_supabase_admin

log = logging.getLogger(__name__)
router = APIRouter()


# --- Pydantic Models ---

class ZohoFieldValues(BaseModel):
    lead_status: str | None = None
    sales_stage: str | None = None
    state_mobile: str | None = None
    lead_source: str | None = None
    marketing_method: str | None = None
    whatsapp_marketing: str | None = None
    demo_booked_time: str | None = None
    demo_booked_date: str | None = None
    demo_meeting_link: str | None = None
    # Follow-up fields
    follow_up_date: str | None = None
    follow_up_time: str | None = None
    follow_up_note: str | None = None
    # Tracking dates
    last_touch_date: str | None = None
    lead_source_date: str | None = None
    # Deal context
    deal_owner: str | None = None
    remarks: str | None = None

    class Config:
        extra = "allow"


class ZohoLeadWebhook(BaseModel):
    """Payload from Zoho CRM workflow webhook."""
    name: str | None = None
    email: str | None = None
    phone: list[str] | str | None = None
    fieldValues: ZohoFieldValues | None = None
    zoho_lead_id: str | None = None
    company: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    deal_owner: str | None = None

    class Config:
        extra = "allow"


# --- Helpers ---

def _extract_phone(phone_field) -> str:
    """Extract clean phone from various formats Zoho sends."""
    if isinstance(phone_field, list):
        phone = phone_field[0] if phone_field else ""
    elif isinstance(phone_field, str):
        phone = phone_field
    else:
        phone = ""
    return phone.strip().replace("+", "").replace(" ", "").replace("-", "")


def _generate_lead_id(email: str, phone: str, name: str) -> str:
    """Generate a stable zoho_lead_id for webhook-sourced leads."""
    key = f"{email or ''}-{phone or ''}-{name or ''}".lower().strip()
    return f"zoho-wh-{hashlib.md5(key.encode()).hexdigest()[:16]}"


def _parse_date(val: str | None) -> str | None:
    """Try to parse a date string into ISO format. Returns None on failure."""
    if not val or val.strip() in ("", "null", "None"):
        return None
    val = val.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(val, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _parse_time(val: str | None) -> str | None:
    """Try to parse a time string into HH:MM format."""
    if not val or val.strip() in ("", "null", "None"):
        return None
    val = val.strip().upper()
    for fmt in ("%I:%M %p", "%H:%M:%S", "%H:%M", "%I:%M%p", "%I %p"):
        try:
            return datetime.strptime(val, fmt).strftime("%H:%M")
        except ValueError:
            continue
    return None


def _map_stage(lead_status: str | None, sales_stage: str | None) -> str:
    """Map Zoho Lead Status / Sales Stage to our simplified pipeline stage."""
    status = (lead_status or "").strip().lower()
    stage = (sales_stage or "").strip().lower()

    stage_map = {
        "1": "new",
        "2": "contacted",
        "3": "demo_done",
        "4": "follow_up",
        "5": "negotiation",
        "6": "closed_won",
        "7": "closed_lost",
        "8": "closed_lost",
        "9": "disqualified",
    }

    # Match by number prefix (e.g., "3. Demo Done" → "3" → "demo_done")
    for prefix, mapped in stage_map.items():
        if status.startswith(f"{prefix}.") or status.startswith(f"{prefix} "):
            return mapped

    # Fallback to keyword matching
    for keyword, mapped in [
        ("won", "closed_won"), ("lost", "closed_lost"),
        ("negotiat", "negotiation"), ("demo", "demo_done"),
        ("follow", "follow_up"), ("contact", "contacted"),
        ("engage", "contacted"),
    ]:
        if keyword in status or keyword in stage:
            return mapped

    return "new"


def _verify_secret(x_webhook_secret: str | None):
    """Verify webhook secret header. Raises HTTPException if invalid."""
    settings = get_settings()
    if settings.secret_key and settings.secret_key != "change-this":
        if x_webhook_secret != settings.secret_key:
            log.warning("Zoho webhook: invalid secret")
            raise HTTPException(status_code=401, detail="Invalid webhook secret")


# ---------------------------------------------------------------------------
# Webhook 1: Lead Update (status, source, stage, deal owner, etc.)
# ---------------------------------------------------------------------------

@router.post("/zoho/lead-update")
async def zoho_lead_webhook(
    request: Request,
    x_webhook_secret: str | None = Header(None, alias="X-Webhook-Secret"),
):
    """Receive real-time lead updates from Zoho CRM.

    Fires on: Lead Status, Lead Source, Sales Stage, Marketing Method changes.
    """
    _verify_secret(x_webhook_secret)

    try:
        raw_body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    leads_data = raw_body if isinstance(raw_body, list) else [raw_body]

    db = get_supabase_admin()
    if not db:
        raise HTTPException(status_code=503, detail="Database unavailable")

    results = []
    for lead_raw in leads_data:
        try:
            lead = ZohoLeadWebhook(**lead_raw)
            result = await _process_lead_webhook(db, lead, lead_raw)
            results.append(result)
        except Exception as e:
            log.error(f"Zoho webhook: error processing lead: {e}")
            results.append({"status": "error", "error": str(e)})

    log.info(f"Zoho lead-update webhook: processed {len(results)} lead(s)")
    return {"ok": True, "processed": len(results), "results": results}


# ---------------------------------------------------------------------------
# Webhook 2: Follow-Up Update (date, time, notes)
# ---------------------------------------------------------------------------

@router.post("/zoho/follow-up")
async def zoho_followup_webhook(
    request: Request,
    x_webhook_secret: str | None = Header(None, alias="X-Webhook-Secret"),
):
    """Receive follow-up date/time changes from Zoho CRM.

    Fires on: Follow Up Date, Follow Up Time, Remarks changes.
    Stores the follow-up schedule so our reminder system can alert reps.
    """
    _verify_secret(x_webhook_secret)

    try:
        raw_body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    leads_data = raw_body if isinstance(raw_body, list) else [raw_body]

    db = get_supabase_admin()
    if not db:
        raise HTTPException(status_code=503, detail="Database unavailable")

    results = []
    for lead_raw in leads_data:
        try:
            lead = ZohoLeadWebhook(**lead_raw)
            result = await _process_followup_webhook(db, lead, lead_raw)
            results.append(result)
        except Exception as e:
            log.error(f"Zoho follow-up webhook: error: {e}")
            results.append({"status": "error", "error": str(e)})

    log.info(f"Zoho follow-up webhook: processed {len(results)} lead(s)")
    return {"ok": True, "processed": len(results), "results": results}


# ---------------------------------------------------------------------------
# Lead processing
# ---------------------------------------------------------------------------

async def _process_lead_webhook(db, lead: ZohoLeadWebhook, raw: dict) -> dict:
    """Process a lead update from Zoho webhook."""
    phone = _extract_phone(lead.phone)
    fv = lead.fieldValues or ZohoFieldValues()

    zoho_id = lead.zoho_lead_id or raw.get("id") or _generate_lead_id(
        lead.email or "", phone, lead.name or ""
    )

    contact_name = lead.name or ""
    if lead.first_name or lead.last_name:
        contact_name = f"{lead.first_name or ''} {lead.last_name or ''}".strip()

    # Core lead data (always safe — these columns exist in original schema)
    lead_data = {
        "zoho_lead_id": zoho_id,
        "contact_name": contact_name,
        "email": lead.email or "",
        "phone": phone,
        "source": fv.lead_source or "",
        "stage": _map_stage(fv.lead_status, fv.sales_stage),
        "geography": fv.state_mobile or "",
        "company": lead.company or raw.get("company", ""),
        "zoho_modified_at": datetime.now(timezone.utc).isoformat(),
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }

    # Extended fields (added by migration 013 — gracefully skip if missing)
    extended = {}
    deal_owner_name = fv.deal_owner or lead.deal_owner or raw.get("deal_owner") or raw.get("owner_name")
    if deal_owner_name:
        extended["deal_owner"] = deal_owner_name
    if fv.remarks:
        extended["remarks"] = fv.remarks
    if fv.marketing_method:
        extended["marketing_method"] = fv.marketing_method
    if fv.whatsapp_marketing:
        extended["whatsapp_marketing"] = fv.whatsapp_marketing
    if fv.demo_booked_date:
        extended["demo_booked_date"] = _parse_date(fv.demo_booked_date)
    if fv.demo_booked_time:
        extended["demo_booked_time"] = fv.demo_booked_time
    if fv.demo_meeting_link:
        extended["demo_meeting_link"] = fv.demo_meeting_link
    if fv.last_touch_date:
        parsed = _parse_date(fv.last_touch_date)
        if parsed:
            extended["last_touch_date"] = parsed
    if fv.lead_source_date:
        parsed = _parse_date(fv.lead_source_date)
        if parsed:
            extended["lead_source_date"] = parsed
    if fv.follow_up_date:
        parsed = _parse_date(fv.follow_up_date)
        if parsed:
            extended["follow_up_date"] = parsed
            extended["follow_up_reminded"] = False  # Reset reminder on new date
    if fv.follow_up_time:
        parsed = _parse_time(fv.follow_up_time)
        if parsed:
            extended["follow_up_time"] = parsed
    if fv.follow_up_note:
        extended["follow_up_note"] = fv.follow_up_note

    # Try upserting with extended fields, fall back to core-only if columns missing
    try:
        db.table("leads").upsert({**lead_data, **extended}, on_conflict="zoho_lead_id").execute()
    except Exception as e:
        if "does not exist" in str(e) or "Could not find" in str(e):
            log.warning("Extended columns not yet migrated, using core fields only")
            db.table("leads").upsert(lead_data, on_conflict="zoho_lead_id").execute()
        else:
            raise

    # Map deal owner to assigned_rep
    if deal_owner_name:
        try:
            rep = db.table("users").select("id").eq(
                "deal_owner_name", deal_owner_name
            ).maybe_single().execute()
            if rep and rep.data:
                db.table("leads").update(
                    {"assigned_rep_id": rep.data["id"]}
                ).eq("zoho_lead_id", zoho_id).execute()
        except Exception:
            pass

    return {"status": "upserted", "zoho_lead_id": zoho_id, "stage": lead_data["stage"]}


async def _process_followup_webhook(db, lead: ZohoLeadWebhook, raw: dict) -> dict:
    """Process a follow-up date/time change from Zoho webhook."""
    phone = _extract_phone(lead.phone)
    fv = lead.fieldValues or ZohoFieldValues()

    zoho_id = lead.zoho_lead_id or raw.get("id") or _generate_lead_id(
        lead.email or "", phone, lead.name or ""
    )

    contact_name = lead.name or ""
    if lead.first_name or lead.last_name:
        contact_name = f"{lead.first_name or ''} {lead.last_name or ''}".strip()

    follow_up_date = _parse_date(fv.follow_up_date or raw.get("follow_up_date", ""))
    follow_up_time = _parse_time(fv.follow_up_time or raw.get("follow_up_time", ""))
    remarks = fv.remarks or raw.get("remarks", "")
    deal_owner_name = fv.deal_owner or lead.deal_owner or raw.get("deal_owner") or raw.get("owner_name", "")

    if not follow_up_date:
        return {"status": "skipped", "reason": "no_follow_up_date", "zoho_lead_id": zoho_id}

    # Upsert the lead with follow-up info
    lead_data = {
        "zoho_lead_id": zoho_id,
        "contact_name": contact_name,
        "email": lead.email or "",
        "phone": phone,
        "zoho_modified_at": datetime.now(timezone.utc).isoformat(),
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }

    follow_up_fields = {
        "follow_up_date": follow_up_date,
        "follow_up_reminded": False,  # Reset — new follow-up date means new reminders
    }
    if follow_up_time:
        follow_up_fields["follow_up_time"] = follow_up_time
    if remarks:
        follow_up_fields["remarks"] = remarks
    if deal_owner_name:
        follow_up_fields["deal_owner"] = deal_owner_name

    try:
        db.table("leads").upsert(
            {**lead_data, **follow_up_fields}, on_conflict="zoho_lead_id"
        ).execute()
    except Exception as e:
        if "does not exist" in str(e) or "Could not find" in str(e):
            log.error("Follow-up columns not yet migrated! Run migration 013_followup_fields.sql")
            db.table("leads").upsert(lead_data, on_conflict="zoho_lead_id").execute()
            return {"status": "partial", "error": "follow_up columns missing — run migration 013"}
        raise

    # Add a note for the follow-up
    lead_row = db.table("leads").select("id").eq(
        "zoho_lead_id", zoho_id
    ).maybe_single().execute()

    if lead_row and lead_row.data:
        time_str = f" at {follow_up_time}" if follow_up_time else ""
        note = f"Follow-up scheduled: {follow_up_date}{time_str}"
        if remarks:
            note += f"\nRemarks: {remarks}"

        db.table("lead_notes").insert({
            "lead_id": lead_row.data["id"],
            "note_text": note,
            "note_source": "zoho",
            "note_date": datetime.now(timezone.utc).isoformat(),
        }).execute()

    log.info(f"Follow-up set for {contact_name or zoho_id}: {follow_up_date} {follow_up_time or ''}")
    return {
        "status": "follow_up_set",
        "zoho_lead_id": zoho_id,
        "follow_up_date": follow_up_date,
        "follow_up_time": follow_up_time,
    }


# ---------------------------------------------------------------------------
# Status endpoint
# ---------------------------------------------------------------------------

@router.get("/zoho/status")
async def zoho_webhook_status():
    """Check webhook receiver status and recent follow-ups."""
    db = get_supabase_admin()
    if not db:
        return {"status": "error", "detail": "Database unavailable"}

    stats = {"status": "ok", "webhook_receiver": "active"}

    try:
        result = db.table("leads").select("id", count="exact").execute()
        stats["total_leads"] = result.count or 0
    except Exception:
        stats["total_leads"] = 0

    try:
        result = db.table("leads").select("id", count="exact").like(
            "zoho_lead_id", "zoho-wh-%"
        ).execute()
        stats["webhook_sourced_leads"] = result.count or 0
    except Exception:
        stats["webhook_sourced_leads"] = 0

    # Count leads with follow-ups due today
    try:
        today = date.today().isoformat()
        result = db.table("leads").select("id", count="exact").eq(
            "follow_up_date", today
        ).eq("follow_up_reminded", False).execute()
        stats["followups_due_today"] = result.count or 0
    except Exception:
        stats["followups_due_today"] = "migration_needed"

    stats["endpoints"] = {
        "lead_update": "POST /api/webhooks/zoho/lead-update",
        "follow_up": "POST /api/webhooks/zoho/follow-up",
        "status": "GET /api/webhooks/zoho/status",
    }

    return stats

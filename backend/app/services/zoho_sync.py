"""Zoho CRM sync service — delta sync with OAuth token refresh."""

import logging
import time
from datetime import datetime, timezone
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import get_settings
from app.core.supabase_client import get_supabase_admin

log = logging.getLogger(__name__)

# In-memory token cache (refreshed automatically)
_token_cache = {
    "access_token": None,
    "expires_at": 0,
}


class ZohoRateLimitError(Exception):
    pass


class ZohoAuthError(Exception):
    pass


# --- Token Management ---

async def get_access_token() -> str:
    """Get valid Zoho access token, refreshing if needed."""
    now = time.time()

    # Return cached token if still valid (with 5 min buffer)
    if _token_cache["access_token"] and _token_cache["expires_at"] > now + 300:
        return _token_cache["access_token"]

    return await refresh_access_token()


async def refresh_access_token() -> str:
    """Refresh Zoho OAuth access token using refresh_token."""
    settings = get_settings()

    if not settings.zoho_refresh_token:
        raise ZohoAuthError("Zoho refresh token not configured")

    url = "https://accounts.zoho.in/oauth/v2/token"
    params = {
        "grant_type": "refresh_token",
        "refresh_token": settings.zoho_refresh_token,
        "client_id": settings.zoho_client_id,
        "client_secret": settings.zoho_client_secret,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, params=params)
        data = response.json()

        if "access_token" not in data:
            error = data.get("error", "unknown")
            log.error(f"Zoho token refresh failed: {error}")
            raise ZohoAuthError(f"Token refresh failed: {error}")

        _token_cache["access_token"] = data["access_token"]
        _token_cache["expires_at"] = time.time() + data.get("expires_in", 3600)

        log.info("Zoho access token refreshed successfully")
        return data["access_token"]


# --- API Calls ---

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=10, max=120),
    retry=retry_if_exception_type(ZohoRateLimitError),
)
async def zoho_api_get(endpoint: str, params: dict | None = None) -> dict:
    """Make authenticated GET request to Zoho CRM API with retry."""
    settings = get_settings()
    token = await get_access_token()

    url = f"{settings.zoho_api_domain}/crm/v8/{endpoint}"
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url, headers=headers, params=params or {})

        if response.status_code == 429:
            log.warning("Zoho rate limit hit. Will retry with backoff.")
            raise ZohoRateLimitError("Rate limit exceeded")

        if response.status_code == 401:
            log.info("Zoho token expired mid-request. Refreshing...")
            await refresh_access_token()
            # Retry with new token
            headers["Authorization"] = f"Zoho-oauthtoken {_token_cache['access_token']}"
            response = await client.get(url, headers=headers, params=params or {})

        if response.status_code == 204:
            return {"data": []}  # No records

        response.raise_for_status()
        return response.json()


# --- Sync Functions ---

async def sync_module(module: str, last_sync_at: str | None = None) -> int:
    """Sync a Zoho CRM module using delta sync.

    Args:
        module: Zoho module name (Leads, Deals, Contacts, etc.)
        last_sync_at: ISO timestamp for delta sync. If None, does full sync.

    Returns:
        Number of records synced.
    """
    db = get_supabase_admin()
    records_synced = 0
    page = 1
    has_more = True

    while has_more:
        params = {
            "per_page": 200,
            "page": page,
            "sort_by": "Modified_Time",
            "sort_order": "asc",
        }

        # Delta: only fetch records modified since last sync
        if last_sync_at:
            params["criteria"] = f"(Modified_Time:greater_than:{last_sync_at})"

        try:
            result = await zoho_api_get(module, params)
            records = result.get("data", [])

            if not records:
                break

            # Process based on module type
            if module == "Leads":
                await _upsert_leads(db, records)
            elif module == "Notes":
                await _upsert_notes(db, records)
            elif module in ("Activities", "Calls"):
                await _upsert_activities(db, records, module.lower())

            records_synced += len(records)
            has_more = result.get("info", {}).get("more_records", False)
            page += 1

        except ZohoRateLimitError:
            log.warning(f"Rate limited during {module} sync at page {page}. Stopping.")
            break
        except Exception as e:
            log.error(f"Error syncing {module} page {page}: {e}")
            break

    return records_synced


async def _upsert_leads(db, records: list):
    """Upsert leads from Zoho into Supabase."""
    for record in records:
        lead_data = {
            "zoho_lead_id": str(record["id"]),
            "company": record.get("Company", ""),
            "contact_name": record.get("Full_Name", ""),
            "phone": record.get("Phone", ""),
            "email": record.get("Email", ""),
            "source": record.get("Lead_Source", ""),
            "stage": record.get("Lead_Status", "new"),
            "deal_value": float(record["Amount"]) if record.get("Amount") else None,
            "industry": record.get("Industry", ""),
            "geography": record.get("City", record.get("State", "")),
            "zoho_created_at": record.get("Created_Time"),
            "zoho_modified_at": record.get("Modified_Time"),
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }

        # Map Zoho owner to our user
        if record.get("Owner", {}).get("id"):
            owner_result = db.table("users").select("id").eq(
                "zoho_user_id", str(record["Owner"]["id"])
            ).execute()
            if owner_result.data:
                lead_data["assigned_rep_id"] = owner_result.data[0]["id"]

        db.table("leads").upsert(lead_data, on_conflict="zoho_lead_id").execute()


async def _upsert_notes(db, records: list):
    """Upsert notes from Zoho into Supabase."""
    for record in records:
        # Find which lead this note belongs to
        parent_id = record.get("Parent_Id", {}).get("id")
        if not parent_id:
            continue

        lead_result = db.table("leads").select("id").eq(
            "zoho_lead_id", str(parent_id)
        ).execute()
        if not lead_result.data:
            continue

        note_data = {
            "zoho_note_id": str(record["id"]),
            "lead_id": lead_result.data[0]["id"],
            "note_text": record.get("Note_Content", ""),
            "note_source": "zoho",
            "note_date": record.get("Created_Time"),
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }

        db.table("lead_notes").upsert(note_data, on_conflict="zoho_note_id").execute()


async def _upsert_activities(db, records: list, source: str):
    """Upsert activities/calls from Zoho into Supabase."""
    for record in records:
        what_id = record.get("What_Id", {}).get("id") or record.get("$se_module_id")
        if not what_id:
            continue

        lead_result = db.table("leads").select("id").eq(
            "zoho_lead_id", str(what_id)
        ).execute()
        if not lead_result.data:
            continue

        # Determine activity type
        if source == "calls":
            activity_type = "call"
        else:
            activity_type = record.get("Activity_Type", "task").lower()

        activity_data = {
            "zoho_activity_id": str(record["id"]),
            "lead_id": lead_result.data[0]["id"],
            "activity_type": activity_type,
            "subject": record.get("Subject", ""),
            "details": record.get("Description", ""),
            "outcome": record.get("Call_Result", record.get("Status", "")),
            "duration_minutes": record.get("Call_Duration_in_seconds", 0) // 60 if record.get("Call_Duration_in_seconds") else None,
            "activity_date": record.get("Activity_Date", record.get("Created_Time")),
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }

        db.table("lead_activities").upsert(activity_data, on_conflict="zoho_activity_id").execute()

    # Update last_activity_at on leads (denormalized for fast stale detection)
    lead_ids = set()
    for record in records:
        what_id = record.get("What_Id", {}).get("id") or record.get("$se_module_id")
        if what_id:
            lr = db.table("leads").select("id").eq("zoho_lead_id", str(what_id)).execute()
            if lr.data:
                lead_ids.add(lr.data[0]["id"])

    for lid in lead_ids:
        latest = db.table("lead_activities").select("activity_date").eq(
            "lead_id", lid
        ).order("activity_date", desc=True).limit(1).execute()
        if latest.data:
            db.table("leads").update(
                {"last_activity_at": latest.data[0]["activity_date"]}
            ).eq("id", lid).execute()


# --- Full Sync Runner ---

async def run_delta_sync() -> dict:
    """Run delta sync for all modules. Called every 2 hours."""
    db = get_supabase_admin()
    results = {}
    start = time.time()

    modules = ["Leads", "Notes", "Calls"]

    for module in modules:
        # Get last sync time for this module
        sync_record = db.table("sync_state").select("last_sync_at").eq(
            "module", module.lower()
        ).order("created_at", desc=True).limit(1).execute()

        last_sync = sync_record.data[0]["last_sync_at"] if sync_record.data else None

        try:
            count = await sync_module(module, last_sync)
            status = "success"
            error = None
        except Exception as e:
            count = 0
            status = "failed"
            error = str(e)[:500]
            log.error(f"Sync failed for {module}: {e}")

        results[module] = {"count": count, "status": status}

        # Log sync state
        db.table("sync_state").insert({
            "module": module.lower(),
            "last_sync_at": datetime.now(timezone.utc).isoformat(),
            "records_synced": count,
            "sync_type": "delta" if last_sync else "full",
            "status": status,
            "error_message": error,
            "duration_seconds": int(time.time() - start),
        }).execute()

    duration = int(time.time() - start)
    log.info(f"Delta sync complete in {duration}s: {results}")
    return results


async def run_full_sync() -> dict:
    """Run full sync (no date filter). Called at 2 AM daily."""
    db = get_supabase_admin()
    results = {}
    start = time.time()

    for module in ["Leads", "Notes", "Calls"]:
        try:
            count = await sync_module(module, last_sync_at=None)
            results[module] = {"count": count, "status": "success"}
        except Exception as e:
            results[module] = {"count": 0, "status": "failed"}
            log.error(f"Full sync failed for {module}: {e}")

        db.table("sync_state").insert({
            "module": module.lower(),
            "last_sync_at": datetime.now(timezone.utc).isoformat(),
            "records_synced": results[module]["count"],
            "sync_type": "full",
            "status": results[module]["status"],
            "duration_seconds": int(time.time() - start),
        }).execute()

    log.info(f"Full sync complete: {results}")
    return results

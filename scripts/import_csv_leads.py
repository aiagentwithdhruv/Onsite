"""Import real leads from Onsite_Entire_Leads.csv into Supabase."""

import csv
import sys
import random
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sales-intelligence" / "backend"))
from app.core.supabase_client import get_supabase_admin

CSV_PATH = "/Users/apple/Documents/Agentic Ai Hub/Calud_Code/n8n/Onsite/Onsite_Entire_Leads.csv"
MAX_LEADS = 500

STAGE_MAP = {
    "1. Prospect": "prospect",
    "High Prospect": "prospect",
    "Very High Prospect": "negotiation",
    "Not Able to Connect after Prospect": "contacted",
    "2. Not Interested After Demo": "lost",
    "3. Sale Done": "won",
    "4. Secondary Sales": "won",
}

STATUS_TO_STAGE = {
    "User not attend session": "new",
    "Session Completed": "demo",
    "Demo booked": "demo",
    "Demo Booked": "demo",
    "Session scheduled": "demo",
    "Paid User": "won",
    "Trial Activated": "contacted",
}


def parse_date(val: str) -> str | None:
    if not val or not val.strip():
        return None
    val = val.strip().strip('"')
    for fmt in [
        "%b %d, %Y %I:%M %p",
        "%b %d, %Y",
        "%d %b, %Y %H:%M:%S",
        "%d %b, %Y %H:%M:%M",
        "%d-%b-%Y",
        "%Y-%m-%d",
    ]:
        try:
            dt = datetime.strptime(val, fmt)
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue
    return None


def main():
    db = get_supabase_admin()

    # Get existing users
    users_result = db.table("users").select("id,name,email,role").execute()
    existing_users = {u["name"]: u["id"] for u in users_result.data or []}
    dhruv_id = None
    for u in users_result.data or []:
        if "dhruv" in u["name"].lower():
            dhruv_id = u["id"]
            break

    # Check existing leads
    check = db.table("leads").select("id", count="exact").limit(1).execute()
    existing_count = check.count or 0
    if existing_count > 0:
        print(f"  Already {existing_count} leads in DB. Skipping to avoid duplicates.")
        print("  To reimport, delete existing leads first.")
        return

    # Read CSV
    print(f"Reading CSV: {CSV_PATH}")
    rows = []
    with open(CSV_PATH, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"  Total rows in CSV: {len(rows)}")

    # Filter to recent leads with data
    scored_rows = []
    for row in rows:
        score = 0
        if row.get("lead_phone", "").strip():
            score += 1
        if row.get("company_name", "").strip():
            score += 1
        if row.get("Lead_email", "").strip():
            score += 1
        if row.get("sales_stage", "").strip():
            score += 2
        if row.get("lead_notes", "").strip():
            score += 1
        if row.get("price_pitched", "").strip():
            score += 2
        if row.get("demo_done", "").strip() == "1":
            score += 2
        if row.get("lead_owner_manager", "").strip().lower().startswith("dhruv"):
            score += 3
        scored_rows.append((score, row))

    scored_rows.sort(key=lambda x: -x[0])
    selected = [r for _, r in scored_rows[:MAX_LEADS]]
    print(f"  Selected {len(selected)} leads (top quality)")

    # Create rep users for deal owners not yet in DB
    deal_owner_names = set()
    for row in selected:
        owner = row.get("deal_owner", "").strip()
        if owner and owner not in existing_users and owner != "Onsite" and owner != "Offline Campaign":
            deal_owner_names.add(owner)

    if deal_owner_names:
        print(f"  Creating {len(deal_owner_names)} rep users for deal owners...")
        for name in deal_owner_names:
            slug = name.lower().replace(" ", ".")
            email = f"{slug}@onsite.team"
            try:
                result = db.table("users").insert({
                    "name": name,
                    "email": email,
                    "role": "rep",
                    "is_active": True,
                }).execute()
                if result.data:
                    existing_users[name] = result.data[0]["id"]
                    print(f"    + {name}")
            except Exception as e:
                print(f"    WARN: {name}: {str(e)[:80]}")

    # Insert leads
    print(f"  Inserting {len(selected)} leads...")
    inserted = 0
    batch = []
    for row in selected:
        zoho_id = row.get("zoho_lead_id", "").strip()
        if not zoho_id:
            zoho_id = row.get("lead_id", "").strip()
        if not zoho_id:
            continue

        stage_raw = row.get("sales_stage", "").strip()
        status_raw = row.get("lead_status", "").strip()
        stage = STAGE_MAP.get(stage_raw) or STATUS_TO_STAGE.get(status_raw, "new")

        deal_val = None
        pp = row.get("price_pitched", "").strip()
        if pp:
            try:
                deal_val = float(pp.replace(",", ""))
            except ValueError:
                pass

        owner_name = row.get("deal_owner", "").strip()
        rep_id = existing_users.get(owner_name)
        if not rep_id:
            rep_id = dhruv_id

        lead_data = {
            "zoho_lead_id": zoho_id,
            "company": row.get("company_name", "").strip() or None,
            "contact_name": row.get("lead_name", "").strip() or None,
            "phone": row.get("lead_phone", "").strip() or None,
            "email": row.get("Lead_email", "").strip() or None,
            "source": row.get("lead_source", "").strip() or None,
            "stage": stage,
            "deal_value": deal_val,
            "industry": row.get("Construction_type", "").strip() or "Construction",
            "geography": row.get("state_mobile", "").strip() or row.get("lead_city", "").strip() or None,
            "assigned_rep_id": rep_id,
            "zoho_created_at": parse_date(row.get("lead_created_date", "")),
            "last_activity_at": parse_date(row.get("last_touched_date_new", "") or row.get("last_touched_date", "")),
        }
        batch.append(lead_data)

        if len(batch) >= 50:
            try:
                db.table("leads").insert(batch).execute()
                inserted += len(batch)
                print(f"    {inserted}/{len(selected)} inserted")
            except Exception as e:
                print(f"    WARN batch insert: {str(e)[:120]}")
                for item in batch:
                    try:
                        db.table("leads").insert(item).execute()
                        inserted += 1
                    except Exception:
                        pass
            batch = []

    if batch:
        try:
            db.table("leads").insert(batch).execute()
            inserted += len(batch)
        except Exception as e:
            for item in batch:
                try:
                    db.table("leads").insert(item).execute()
                    inserted += 1
                except Exception:
                    pass

    print(f"  Done: {inserted} leads inserted")

    # Add lead notes
    print("  Adding lead notes...")
    leads_result = db.table("leads").select("id,zoho_lead_id").execute()
    lead_id_map = {l["zoho_lead_id"]: l["id"] for l in leads_result.data or []}
    notes_count = 0
    notes_batch = []
    for row in selected:
        zoho_id = row.get("zoho_lead_id", "").strip() or row.get("lead_id", "").strip()
        notes_text = row.get("lead_notes", "").strip()
        if not notes_text or zoho_id not in lead_id_map:
            continue
        notes_batch.append({
            "lead_id": lead_id_map[zoho_id],
            "note_text": notes_text[:2000],
            "note_source": "zoho",
            "note_date": parse_date(row.get("notes_date", "")),
        })
        if len(notes_batch) >= 50:
            try:
                db.table("lead_notes").insert(notes_batch).execute()
                notes_count += len(notes_batch)
            except Exception:
                pass
            notes_batch = []
    if notes_batch:
        try:
            db.table("lead_notes").insert(notes_batch).execute()
            notes_count += len(notes_batch)
        except Exception:
            pass
    print(f"    {notes_count} notes inserted")

    # Add lead scores (assign hot/warm/cold based on data quality)
    print("  Adding lead scores...")
    scores_batch = []
    for row in selected:
        zoho_id = row.get("zoho_lead_id", "").strip() or row.get("lead_id", "").strip()
        if zoho_id not in lead_id_map:
            continue
        stage_raw = row.get("sales_stage", "").strip()
        has_demo = row.get("demo_done", "").strip() == "1"
        has_notes = bool(row.get("lead_notes", "").strip())
        has_price = bool(row.get("price_pitched", "").strip())

        if stage_raw in ("Very High Prospect", "3. Sale Done", "4. Secondary Sales") or has_price:
            score, label, reason = random.randint(75, 95), "hot", "High engagement with demo/pricing"
        elif stage_raw in ("1. Prospect", "High Prospect") or has_demo:
            score, label, reason = random.randint(50, 74), "warm", "Prospect with demo activity"
        elif has_notes:
            score, label, reason = random.randint(30, 55), "warm", "Has CRM notes and activity"
        else:
            score, label, reason = random.randint(10, 35), "cold", "New lead, minimal engagement"

        scores_batch.append({
            "lead_id": lead_id_map[zoho_id],
            "score": label,
            "score_numeric": score,
            "score_reason": reason,
            "model_used": "seed-import",
        })

    for i in range(0, len(scores_batch), 50):
        chunk = scores_batch[i:i+50]
        try:
            db.table("lead_scores").insert(chunk).execute()
        except Exception as e:
            print(f"    WARN scores: {str(e)[:80]}")
    print(f"    {len(scores_batch)} scores inserted")

    print()
    print("Import complete! Refresh the dashboard.")


if __name__ == "__main__":
    main()

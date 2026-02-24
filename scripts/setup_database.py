"""
Setup script: Deploy schema, seed data, and create test auth user in Supabase.
Run this ONCE to initialize the database.

Usage:
    python3 setup_database.py
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# Load env from backend/.env
env_path = Path(__file__).parent.parent / "sales-intelligence" / "backend" / ".env"
env_vars = {}
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            env_vars[key.strip()] = val.strip()

SUPABASE_URL = env_vars.get("SUPABASE_URL", "")
SERVICE_KEY = env_vars.get("SUPABASE_SERVICE_KEY", "")

if not SUPABASE_URL or not SERVICE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in sales-intelligence/backend/.env")
    sys.exit(1)


def supabase_sql(sql: str) -> dict:
    """Execute SQL via Supabase REST RPC (pg_net) endpoint."""
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
    }
    data = json.dumps({"query": sql}).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"error": body, "status": e.code}


def supabase_rest(method: str, path: str, body: dict = None) -> dict:
    """Call Supabase REST API."""
    url = f"{SUPABASE_URL}{path}"
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        return {"error": body_text, "status": e.code}


def supabase_admin_create_user(email: str, password: str) -> dict:
    """Create a user via Supabase Auth Admin API."""
    url = f"{SUPABASE_URL}/auth/v1/admin/users"
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
    }
    data = json.dumps({
        "email": email,
        "password": password,
        "email_confirm": True,
    }).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"error": body, "status": e.code}


def supabase_admin_list_users() -> list:
    """List users via Supabase Auth Admin API."""
    url = f"{SUPABASE_URL}/auth/v1/admin/users"
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            return result.get("users", [])
    except urllib.error.HTTPError:
        return []


def insert_row(table: str, row: dict) -> dict:
    """Insert a row via Supabase REST API."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    data = json.dumps(row).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            return result[0] if isinstance(result, list) and result else result
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"error": body, "status": e.code}


def check_table_exists(table: str) -> bool:
    """Check if a table exists by trying to select from it."""
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=id&limit=1"
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return True
    except urllib.error.HTTPError:
        return False


def update_row(table: str, column: str, value: str, data: dict) -> dict:
    """Update a row via Supabase REST API."""
    url = f"{SUPABASE_URL}/rest/v1/{table}?{column}=eq.{value}"
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="PATCH")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"error": body, "status": e.code}


# =====================================================
# MAIN
# =====================================================

def main():
    print("=" * 60)
    print("Sales Intelligence System — Database Setup")
    print("=" * 60)
    print(f"Supabase URL: {SUPABASE_URL}")
    print()

    # Step 1: Check if tables already exist
    print("[1/4] Checking if database is already set up...")
    if check_table_exists("users"):
        print("  -> Tables already exist! Skipping schema deployment.")
        print("  -> If you want to reset, drop tables manually in Supabase SQL Editor.")
    else:
        print("  -> Tables not found. You need to run the SQL schema manually.")
        print()
        print("  IMPORTANT: Copy the contents of database/001_initial_schema.sql")
        print("  and paste into the Supabase SQL Editor at:")
        print(f"  {SUPABASE_URL.replace('.supabase.co', '')}")
        print("  -> Go to SQL Editor -> New Query -> Paste -> Run")
        print()
        input("  Press Enter after you've run the schema SQL...")

        if not check_table_exists("users"):
            print("  ERROR: Tables still not found. Please run the schema SQL first.")
            sys.exit(1)

    # Step 2: Seed data via REST API
    print()
    print("[2/4] Seeding data...")

    # Check if already seeded
    url = f"{SUPABASE_URL}/rest/v1/users?select=id&limit=1"
    headers = {"apikey": SERVICE_KEY, "Authorization": f"Bearer {SERVICE_KEY}"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        existing = json.loads(resp.read())

    if existing:
        print(f"  -> Users table already has {len(existing)}+ records. Skipping seed.")
    else:
        print("  Inserting users...")
        users = [
            {"id": "00000000-0000-0000-0000-000000000001", "email": "sumit@onsite.team", "name": "Sumit (Founder)", "role": "founder", "phone": "919999900001"},
            {"id": "00000000-0000-0000-0000-000000000002", "email": "manager1@onsite.team", "name": "Rahul (Manager)", "role": "manager", "team": "Team A", "phone": "919999900002"},
            {"id": "00000000-0000-0000-0000-000000000003", "email": "manager2@onsite.team", "name": "Priya (Manager)", "role": "manager", "team": "Team B", "phone": "919999900003"},
            {"id": "00000000-0000-0000-0000-000000000010", "email": "tl1@onsite.team", "name": "Amit (Team Lead)", "role": "team_lead", "team": "Team A", "team_lead_id": "00000000-0000-0000-0000-000000000002", "phone": "919999900010"},
            {"id": "00000000-0000-0000-0000-000000000011", "email": "tl2@onsite.team", "name": "Neha (Team Lead)", "role": "team_lead", "team": "Team B", "team_lead_id": "00000000-0000-0000-0000-000000000003", "phone": "919999900011"},
            {"id": "00000000-0000-0000-0000-000000000101", "email": "ravi@onsite.team", "name": "Ravi Kumar", "role": "rep", "team": "Team A", "team_lead_id": "00000000-0000-0000-0000-000000000010", "phone": "919999900101"},
            {"id": "00000000-0000-0000-0000-000000000102", "email": "sanjay@onsite.team", "name": "Sanjay Patel", "role": "rep", "team": "Team A", "team_lead_id": "00000000-0000-0000-0000-000000000010", "phone": "919999900102"},
            {"id": "00000000-0000-0000-0000-000000000103", "email": "vikram@onsite.team", "name": "Vikram Singh", "role": "rep", "team": "Team A", "team_lead_id": "00000000-0000-0000-0000-000000000010", "phone": "919999900103"},
            {"id": "00000000-0000-0000-0000-000000000201", "email": "anita@onsite.team", "name": "Anita Sharma", "role": "rep", "team": "Team B", "team_lead_id": "00000000-0000-0000-0000-000000000011", "phone": "919999900201"},
            {"id": "00000000-0000-0000-0000-000000000202", "email": "deepak@onsite.team", "name": "Deepak Gupta", "role": "rep", "team": "Team B", "team_lead_id": "00000000-0000-0000-0000-000000000011", "phone": "919999900202"},
            {"id": "00000000-0000-0000-0000-000000000203", "email": "pooja@onsite.team", "name": "Pooja Reddy", "role": "rep", "team": "Team B", "team_lead_id": "00000000-0000-0000-0000-000000000011", "phone": "919999900203"},
            {"id": "00000000-0000-0000-0000-000000000999", "email": "admin@onsite.team", "name": "System Admin", "role": "admin", "phone": "919999900999"},
        ]

        for u in users:
            result = insert_row("users", u)
            if "error" in result:
                print(f"    WARN: Failed to insert {u['email']}: {result['error'][:100]}")
            else:
                print(f"    + {u['name']} ({u['role']})")

        print("  Inserting leads...")
        leads = [
            {"id": "10000000-0000-0000-0000-000000000001", "zoho_lead_id": "ZL001", "company": "ABC Construction Pvt Ltd", "contact_name": "Rajesh Mehta", "phone": "919876500001", "email": "rajesh@abcconstruction.in", "source": "website", "stage": "demo", "deal_value": 5000000, "industry": "Construction", "geography": "Mumbai", "assigned_rep_id": "00000000-0000-0000-0000-000000000101"},
            {"id": "10000000-0000-0000-0000-000000000002", "zoho_lead_id": "ZL002", "company": "Metro Builders", "contact_name": "Sunil Agarwal", "phone": "919876500002", "email": "sunil@metrobuilders.in", "source": "referral", "stage": "proposal", "deal_value": 8000000, "industry": "Construction", "geography": "Delhi", "assigned_rep_id": "00000000-0000-0000-0000-000000000101"},
            {"id": "10000000-0000-0000-0000-000000000003", "zoho_lead_id": "ZL003", "company": "Green Infra Solutions", "contact_name": "Meera Kapoor", "phone": "919876500003", "email": "meera@greeninfra.in", "source": "cold_call", "stage": "contacted", "deal_value": 2000000, "industry": "Infrastructure", "geography": "Bangalore", "assigned_rep_id": "00000000-0000-0000-0000-000000000101"},
            {"id": "10000000-0000-0000-0000-000000000004", "zoho_lead_id": "ZL004", "company": "Skyline Projects", "contact_name": "Arjun Reddy", "phone": "919876500004", "email": "arjun@skylineprojects.in", "source": "website", "stage": "new", "deal_value": 3500000, "industry": "Real Estate", "geography": "Hyderabad", "assigned_rep_id": "00000000-0000-0000-0000-000000000101"},
            {"id": "10000000-0000-0000-0000-000000000005", "zoho_lead_id": "ZL005", "company": "Tata Projects Ltd", "contact_name": "Vikash Kumar", "phone": "919876500005", "email": "vikash@tataprojects.in", "source": "referral", "stage": "negotiation", "deal_value": 15000000, "industry": "Construction", "geography": "Mumbai", "assigned_rep_id": "00000000-0000-0000-0000-000000000102"},
            {"id": "10000000-0000-0000-0000-000000000006", "zoho_lead_id": "ZL006", "company": "Prestige Constructions", "contact_name": "Lakshmi Narayan", "phone": "919876500006", "email": "lakshmi@prestige.in", "source": "ads", "stage": "demo", "deal_value": 6000000, "industry": "Real Estate", "geography": "Chennai", "assigned_rep_id": "00000000-0000-0000-0000-000000000102"},
            {"id": "10000000-0000-0000-0000-000000000007", "zoho_lead_id": "ZL007", "company": "DLF Infrastructure", "contact_name": "Amit Verma", "phone": "919876500007", "email": "amit@dlf.in", "source": "website", "stage": "proposal", "deal_value": 12000000, "industry": "Real Estate", "geography": "Gurgaon", "assigned_rep_id": "00000000-0000-0000-0000-000000000201"},
            {"id": "10000000-0000-0000-0000-000000000008", "zoho_lead_id": "ZL008", "company": "L&T Construction", "contact_name": "Prashant Joshi", "phone": "919876500008", "email": "prashant@lnt.in", "source": "referral", "stage": "contacted", "deal_value": 20000000, "industry": "Infrastructure", "geography": "Pune", "assigned_rep_id": "00000000-0000-0000-0000-000000000201"},
            {"id": "10000000-0000-0000-0000-000000000009", "zoho_lead_id": "ZL009", "company": "Oberoi Realty", "contact_name": "Nisha Desai", "phone": "919876500009", "email": "nisha@oberoi.in", "source": "cold_call", "stage": "new", "deal_value": 4000000, "industry": "Real Estate", "geography": "Mumbai", "assigned_rep_id": "00000000-0000-0000-0000-000000000201"},
            {"id": "10000000-0000-0000-0000-000000000010", "zoho_lead_id": "ZL010", "company": "Godrej Properties", "contact_name": "Karan Malhotra", "phone": "919876500010", "email": "karan@godrej.in", "source": "ads", "stage": "demo", "deal_value": 9000000, "industry": "Real Estate", "geography": "Mumbai", "assigned_rep_id": "00000000-0000-0000-0000-000000000202"},
            {"id": "10000000-0000-0000-0000-000000000050", "zoho_lead_id": "ZL050", "company": "Shapoorji Pallonji", "contact_name": "Dev Sharma", "phone": "919876500050", "email": "dev@shapoorji.in", "source": "referral", "stage": "won", "deal_value": 10000000, "industry": "Construction", "geography": "Mumbai", "assigned_rep_id": "00000000-0000-0000-0000-000000000101"},
            {"id": "10000000-0000-0000-0000-000000000051", "zoho_lead_id": "ZL051", "company": "Sobha Developers", "contact_name": "Rina Patel", "phone": "919876500051", "email": "rina@sobha.in", "source": "website", "stage": "won", "deal_value": 7500000, "industry": "Real Estate", "geography": "Bangalore", "assigned_rep_id": "00000000-0000-0000-0000-000000000201"},
            {"id": "10000000-0000-0000-0000-000000000052", "zoho_lead_id": "ZL052", "company": "Brigade Enterprises", "contact_name": "Manoj Rao", "phone": "919876500052", "email": "manoj@brigade.in", "source": "referral", "stage": "won", "deal_value": 5500000, "industry": "Construction", "geography": "Bangalore", "assigned_rep_id": "00000000-0000-0000-0000-000000000102"},
        ]

        for l in leads:
            result = insert_row("leads", l)
            if "error" in result:
                print(f"    WARN: Failed to insert lead {l['company']}: {result['error'][:100]}")
            else:
                print(f"    + {l['company']} ({l['stage']})")

        print("  Inserting lead notes...")
        notes = [
            {"lead_id": "10000000-0000-0000-0000-000000000001", "note_text": "First call: Rajesh is interested in our project management module. He manages 3 active construction sites. Main pain: tracking material delivery across sites.", "note_source": "zoho"},
            {"lead_id": "10000000-0000-0000-0000-000000000001", "note_text": "Demo completed. Rajesh was impressed with the dashboard. Asked about mobile app availability. Wants pricing for 50 users.", "note_source": "zoho"},
            {"lead_id": "10000000-0000-0000-0000-000000000002", "note_text": "Referral from Shapoorji. Metro Builders is expanding to 5 new sites. They need billing + project tracking.", "note_source": "zoho"},
            {"lead_id": "10000000-0000-0000-0000-000000000005", "note_text": "Big deal. Tata Projects looking for enterprise solution for 200+ users. Current pain: using Excel for tracking.", "note_source": "zoho"},
            {"lead_id": "10000000-0000-0000-0000-000000000005", "note_text": "Negotiation phase. They want 20% discount. We offered 10% with 2-year commitment. Decision expected this month.", "note_source": "zoho"},
            {"lead_id": "10000000-0000-0000-0000-000000000007", "note_text": "DLF wants a POC on one project first. If successful, rollout to all 8 ongoing projects. Huge potential.", "note_source": "zoho"},
        ]

        for n in notes:
            result = insert_row("lead_notes", n)
            if "error" in result:
                print(f"    WARN: note insert failed: {result['error'][:80]}")
            else:
                print(f"    + Note for lead {n['lead_id'][:8]}...")

        print("  Inserting lead activities...")
        activities = [
            {"lead_id": "10000000-0000-0000-0000-000000000001", "activity_type": "call", "subject": "Intro call", "outcome": "connected", "duration_minutes": 15, "performed_by": "00000000-0000-0000-0000-000000000101", "activity_date": "2026-02-10T10:00:00Z"},
            {"lead_id": "10000000-0000-0000-0000-000000000001", "activity_type": "meeting", "subject": "Product demo", "outcome": "completed", "duration_minutes": 45, "performed_by": "00000000-0000-0000-0000-000000000101", "activity_date": "2026-02-12T14:00:00Z"},
            {"lead_id": "10000000-0000-0000-0000-000000000002", "activity_type": "call", "subject": "Referral intro", "outcome": "connected", "duration_minutes": 20, "performed_by": "00000000-0000-0000-0000-000000000101", "activity_date": "2026-02-08T11:00:00Z"},
            {"lead_id": "10000000-0000-0000-0000-000000000005", "activity_type": "meeting", "subject": "Enterprise pitch", "outcome": "completed", "duration_minutes": 60, "performed_by": "00000000-0000-0000-0000-000000000102", "activity_date": "2026-02-05T10:00:00Z"},
            {"lead_id": "10000000-0000-0000-0000-000000000010", "activity_type": "meeting", "subject": "Demo session", "outcome": "completed", "duration_minutes": 40, "performed_by": "00000000-0000-0000-0000-000000000202", "activity_date": "2026-02-14T15:00:00Z"},
        ]

        for a in activities:
            result = insert_row("lead_activities", a)
            if "error" in result:
                print(f"    WARN: activity insert failed: {result['error'][:80]}")
            else:
                print(f"    + {a['activity_type']}: {a['subject']}")

    # Step 3: Create test auth user
    print()
    print("[3/4] Creating test auth user...")

    TEST_EMAIL = "sumit@onsite.team"
    TEST_PASSWORD = "Onsite2026!"

    # Check existing auth users
    existing_users = supabase_admin_list_users()
    existing_emails = [u.get("email") for u in existing_users]

    if TEST_EMAIL in existing_emails:
        print(f"  -> Auth user '{TEST_EMAIL}' already exists.")
        auth_user = next(u for u in existing_users if u.get("email") == TEST_EMAIL)
        auth_id = auth_user["id"]
    else:
        result = supabase_admin_create_user(TEST_EMAIL, TEST_PASSWORD)
        if "error" in result:
            print(f"  ERROR creating auth user: {result['error'][:200]}")
            print("  You may need to create the user manually in Supabase dashboard.")
            auth_id = None
        else:
            auth_id = result.get("id")
            print(f"  + Created auth user: {TEST_EMAIL} (ID: {auth_id})")

    # Step 4: Link auth user to seed data
    if auth_id:
        print()
        print("[4/4] Linking auth user to seed data user...")
        result = update_row("users", "email", TEST_EMAIL, {"auth_id": auth_id})
        if isinstance(result, list) and result:
            print(f"  + Linked auth_id={auth_id} to founder user")
        elif isinstance(result, dict) and "error" in result:
            print(f"  WARN: Could not link: {result['error'][:100]}")
        else:
            print(f"  + Updated founder user with auth_id")

    print()
    print("=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print()
    print("Login credentials:")
    print(f"  Email:    {TEST_EMAIL}")
    print(f"  Password: {TEST_PASSWORD}")
    print()
    print("Next steps:")
    print("  1. Start backend:  cd backend && python3 -m uvicorn app.main:app --reload --port 8000")
    print("  2. Start frontend: cd frontend && npm run dev")
    print("  3. Open http://localhost:5173 and login!")
    print()


if __name__ == "__main__":
    main()

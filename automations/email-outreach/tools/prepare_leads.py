#!/usr/bin/env python3
"""
Prepare Leads — Parse from Apollo CSV, Zoho CRM, Google Sheets, or JSON into Instantly format.
Usage: python tools/prepare_leads.py --source apollo-csv --input leads.csv --region us --output .tmp/leads.json
"""

import argparse
import csv
import json
import os
import sys
import urllib.request
import urllib.error


def parse_apollo_csv(filepath, region=None, sender_name="Akshansh - Onsite Teams"):
    """Parse Apollo.io export CSV."""
    leads = []
    skipped = {"no_email": 0, "invalid": 0, "duplicate": 0}
    seen = set()

    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = (row.get("Email") or "").strip().lower()
            if not email or "@" not in email:
                skipped["no_email"] += 1
                continue
            if (row.get("Email Status") or "").strip().lower() == "bounced":
                skipped["invalid"] += 1
                continue
            if email in seen:
                skipped["duplicate"] += 1
                continue
            seen.add(email)

            leads.append({
                "email": email,
                "first_name": (row.get("First Name") or "").strip(),
                "last_name": (row.get("Last Name") or "").strip(),
                "company_name": (row.get("Company Name") or row.get("Company Name for Emails") or "").strip(),
                "custom_variables": {
                    "firstName": (row.get("First Name") or "").strip(),
                    "lastName": (row.get("Last Name") or "").strip(),
                    "companyName": (row.get("Company Name") or "").strip(),
                    "city": (row.get("City") or row.get("Company City") or "").strip(),
                    "senderName": sender_name,
                    "title": (row.get("Title") or "").strip(),
                    "phone": (row.get("Mobile Phone") or row.get("Work Direct Phone") or "").strip(),
                    "website": (row.get("Website") or "").strip(),
                }
            })

    print(f"[prepare_leads] Parsed {len(leads)} leads from Apollo CSV (skipped: {skipped})", file=sys.stderr)
    return {"status": "success", "source": "apollo_csv", "region": region,
            "total_parsed": len(leads), "skipped": skipped, "leads": leads}


def parse_google_sheet(sheet_id, region=None, sender_name="Akshansh - Onsite Teams"):
    """Parse leads from a Google Sheet via export URL (public or shared)."""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode('utf-8-sig')
    except Exception as e:
        return {"error": f"Failed to fetch Google Sheet: {e}"}

    import io
    reader = csv.DictReader(io.StringIO(content))
    leads = []
    seen = set()

    for row in reader:
        # Try multiple column name patterns
        email = (row.get("Email") or row.get("email") or row.get("Email Address") or "").strip().lower()
        if not email or "@" not in email or email in seen:
            continue
        seen.add(email)

        first_name = (row.get("First Name") or row.get("first_name") or row.get("Name") or "").strip()
        company = (row.get("Company") or row.get("Company Name") or row.get("company") or "").strip()
        city = (row.get("City") or row.get("city") or row.get("Location") or "").strip()

        leads.append({
            "email": email,
            "first_name": first_name,
            "last_name": (row.get("Last Name") or row.get("last_name") or "").strip(),
            "company_name": company,
            "custom_variables": {
                "firstName": first_name,
                "companyName": company,
                "city": city,
                "senderName": sender_name,
            }
        })

    print(f"[prepare_leads] Parsed {len(leads)} leads from Google Sheet", file=sys.stderr)
    return {"status": "success", "source": "google_sheet", "total_parsed": len(leads), "leads": leads}


def parse_zoho_crm(region=None, sender_name="Akshansh - Onsite Teams"):
    """Fetch leads from Zoho CRM."""
    cid = os.environ.get("ZOHO_CID")
    cs = os.environ.get("ZOHO_CS")
    rt = os.environ.get("ZOHO_RT")
    if not all([cid, cs, rt]):
        return {"error": "Missing ZOHO_CID, ZOHO_CS, ZOHO_RT in .env"}

    # Get access token
    token_url = f"https://accounts.zoho.in/oauth/v2/token?grant_type=refresh_token&client_id={cid}&client_secret={cs}&refresh_token={rt}"
    try:
        req = urllib.request.Request(token_url, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            token_data = json.loads(resp.read().decode())
            access_token = token_data.get("access_token")
            if not access_token:
                return {"error": f"Zoho auth failed: {token_data}"}
    except Exception as e:
        return {"error": f"Zoho auth failed: {e}"}

    # Fetch leads
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    leads_url = "https://www.zohoapis.in/crm/v2/Leads?per_page=200"
    try:
        req = urllib.request.Request(leads_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return {"error": f"Zoho API failed: {e}"}

    region_map = {
        "us": ["united states", "usa", "us"],
        "australia": ["australia"],
        "middle_east": ["uae", "united arab emirates", "dubai", "saudi arabia", "qatar"],
        "india": ["india"],
    }

    leads = []
    seen = set()
    for zl in data.get("data", []):
        email = (zl.get("Email") or "").strip().lower()
        if not email or "@" not in email or email in seen:
            continue
        seen.add(email)

        country = (zl.get("Country") or "").lower()
        if region and region in region_map:
            if country not in region_map[region]:
                continue

        first_name = zl.get("First_Name") or ""
        leads.append({
            "email": email,
            "first_name": first_name,
            "last_name": zl.get("Last_Name") or "",
            "company_name": zl.get("Company") or "",
            "custom_variables": {
                "firstName": first_name,
                "companyName": zl.get("Company") or "",
                "city": zl.get("City") or "",
                "senderName": sender_name,
            }
        })

    print(f"[prepare_leads] Fetched {len(leads)} leads from Zoho CRM (region={region})", file=sys.stderr)
    return {"status": "success", "source": "zoho_crm", "region": region,
            "total_parsed": len(leads), "leads": leads}


def parse_json_file(filepath, sender_name="Akshansh - Onsite Teams"):
    """Parse raw JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    raw = data if isinstance(data, list) else data.get("leads", [])
    leads = []
    seen = set()

    for lead in raw:
        email = (lead.get("email") or lead.get("Email") or "").strip().lower()
        if not email or "@" not in email or email in seen:
            continue
        seen.add(email)

        first_name = lead.get("first_name") or lead.get("firstName") or lead.get("First Name") or ""
        company = lead.get("company_name") or lead.get("companyName") or lead.get("Company Name") or ""
        leads.append({
            "email": email,
            "first_name": first_name,
            "last_name": lead.get("last_name") or lead.get("lastName") or "",
            "company_name": company,
            "custom_variables": {
                "firstName": first_name,
                "companyName": company,
                "city": lead.get("city") or lead.get("City") or "",
                "senderName": sender_name,
            }
        })

    return {"status": "success", "source": "json_file", "total_parsed": len(leads), "leads": leads}


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

    parser = argparse.ArgumentParser(description="Prepare leads for Instantly campaigns")
    parser.add_argument("--source", required=True,
                        choices=["apollo-csv", "zoho-crm", "google-sheet", "json"])
    parser.add_argument("--input", help="File path (CSV/JSON) or Google Sheet ID")
    parser.add_argument("--output", help="Output JSON file")
    parser.add_argument("--region", choices=["us", "australia", "middle_east", "india"])
    parser.add_argument("--sender-name", default="Akshansh - Onsite Teams")
    args = parser.parse_args()

    if args.source == "apollo-csv":
        result = parse_apollo_csv(args.input, args.region, args.sender_name)
    elif args.source == "google-sheet":
        result = parse_google_sheet(args.input, args.region, args.sender_name)
    elif args.source == "zoho-crm":
        result = parse_zoho_crm(args.region, args.sender_name)
    elif args.source == "json":
        result = parse_json_file(args.input, args.sender_name)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"[prepare_leads] Written to {args.output}", file=sys.stderr)
    else:
        print(json.dumps(result, indent=2))

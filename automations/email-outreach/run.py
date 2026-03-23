#!/usr/bin/env python3
"""
Onsite Email Outreach — Zero-manual cold email automation.

Commands:
  python run.py dns-check                     # Check all Onsite domains
  python run.py status                        # Show accounts + campaigns
  python run.py create --name "Houston" --region us --leads leads.csv --source apollo-csv
  python run.py create --name "India CRM" --region india --source zoho-crm
  python run.py create --name "UAE Sheet" --region middle_east --source google-sheet --leads SHEET_ID
  python run.py analytics                     # Show all campaign analytics
  python run.py analytics --campaign-id ID    # Specific campaign
  python run.py pause --campaign-id ID        # Emergency stop
  python run.py resume --campaign-id ID       # Resume sending
"""

import argparse
import json
import os
import sys

# Add tools to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))

# Load env files (check multiple locations)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATHS = [
    os.path.join(SCRIPT_DIR, '..', '.env'),       # Onsite/automations/.env (primary)
    os.path.join(SCRIPT_DIR, '..', '..', '.env'),  # Onsite/.env (fallback)
    os.path.join(SCRIPT_DIR, '..', '..', 'onsite-hub', '.env.local'),  # onsite-hub
]
for env_path in ENV_PATHS:
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, val = line.partition('=')
                    os.environ.setdefault(key.strip(), val.strip())

TMP_DIR = os.path.join(os.path.dirname(__file__), '.tmp')
os.makedirs(TMP_DIR, exist_ok=True)

# Default sending accounts (rotate across domains for deliverability)
DEFAULT_ACCOUNTS = [
    "akshansh@onsitesteam.com",
    "anjali.bajaj@onsitesteam.com",
]

TIMEZONE_MAP = {
    "us": "America/Chicago",
    "australia": "Australia/Perth",
    "middle_east": "Asia/Dubai",
    "india": "Asia/Kolkata",
}


def cmd_dns_check(args):
    """Check DNS for all Onsite domains."""
    from dns_check import check_domain
    domains = ["onsitesteam.com", "onsiteteams.online", "onsite-teams.com", "onsiteteams.com"]

    print("\n" + "=" * 60)
    print("  ONSITE EMAIL DOMAIN HEALTH CHECK")
    print("=" * 60)

    all_ok = True
    for domain in domains:
        result = check_domain(domain)
        status_icon = "✅" if result["health"] == "HEALTHY" else "❌" if result["health"] == "CRITICAL" else "⚠️"
        print(f"\n  {status_icon} {domain} — {result['health']} ({result['score']}/100)")
        print(f"     SPF: {result['spf']['status']}  DKIM: {result['dkim']['status']}  DMARC: {result['dmarc']['status']}  MX: {result['mx']['status']}")

        if result['fixes_needed']:
            all_ok = False
            for fix in result['fixes_needed']:
                print(f"     [{fix['priority']}] {fix['record']}: {fix['fix']}")

    if all_ok:
        print("\n  All domains healthy! Ready to send.")
    else:
        print("\n  ⚠️  Fix DNS issues above before launching campaigns.")
    print()


def cmd_status(args):
    """Show SMTP account status."""
    from smtp_sender import list_accounts_status
    result = list_accounts_status()
    if not result.get("accounts"):
        print("\n  Fill in SMTP passwords in Onsite/automations/.env")
        print("  Then run: python run.py status\n")


def cmd_create(args):
    """Create and send a campaign via SMTP."""
    from smtp_sender import get_accounts, send_campaign
    from instantly_api import SEQUENCES
    from prepare_leads import (parse_apollo_csv, parse_zoho_crm,
                                parse_google_sheet, parse_json_file)

    region = args.region
    name = args.name
    source = args.source
    sender_name = args.sender_name or "Akshansh - Onsite Teams"

    print(f"\n{'='*60}")
    print(f"  CAMPAIGN: {name}")
    print(f"  Region: {region} | Source: {source}")
    print(f"{'='*60}")

    # Step 1: Prepare leads
    print("\n  [1/3] Preparing leads...")
    if source == "apollo-csv":
        if not args.leads:
            print("  ❌ --leads <path-to-csv> required for apollo-csv"); return
        lead_result = parse_apollo_csv(args.leads, region, sender_name)
    elif source == "zoho-crm":
        lead_result = parse_zoho_crm(region, sender_name)
    elif source == "google-sheet":
        if not args.leads:
            print("  ❌ --leads <sheet-id> required for google-sheet"); return
        lead_result = parse_google_sheet(args.leads, region, sender_name)
    elif source == "json":
        if not args.leads:
            print("  ❌ --leads <path-to-json> required for json"); return
        lead_result = parse_json_file(args.leads, sender_name)
    else:
        print(f"  ❌ Unknown source: {source}"); return

    if "error" in lead_result:
        print(f"  ❌ Lead prep failed: {lead_result['error']}"); return

    leads = lead_result.get("leads", [])
    print(f"  ✅ {len(leads)} leads ready")

    if len(leads) == 0:
        print("  ⚠️  No leads found. Check your source."); return

    # Save leads to .tmp
    leads_file = os.path.join(TMP_DIR, f"{name.lower().replace(' ', '_')}_leads.json")
    with open(leads_file, 'w') as f:
        json.dump(lead_result, f, indent=2)
    print(f"     Saved to {leads_file}")

    # Step 2: Get SMTP account
    print("\n  [2/3] Checking SMTP account...")
    smtp_accounts = get_accounts()
    acc_name = args.account or (list(smtp_accounts.keys())[0] if smtp_accounts else None)
    if not acc_name or acc_name not in smtp_accounts:
        print(f"  ❌ No valid SMTP account. Update passwords in .env")
        print(f"     Available: {list(smtp_accounts.keys()) if smtp_accounts else 'none'}")
        return
    account = smtp_accounts[acc_name]
    print(f"  ✅ Using: {account['email']}")

    # Step 3: Get sequences
    seqs = SEQUENCES.get(region)
    if not seqs:
        print(f"  ❌ No sequences for region: {region}"); return

    # Step 3: Send (or dry run)
    print(f"\n  [3/3] {'DRY RUN — previewing' if args.dry_run else 'SENDING'} emails...")
    result = send_campaign(account, leads, seqs, region, args.daily_limit, args.dry_run)

    # Save log
    log_file = os.path.join(TMP_DIR, f"{name.lower().replace(' ', '_')}_log.json")
    with open(log_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n  {'🏁 DRY RUN COMPLETE' if args.dry_run else '🚀 CAMPAIGN SENT'}: {name}")
    print(f"     Account: {account['email']}")
    print(f"     Sent: {result.get('sent', 0)}/{min(len(leads), args.daily_limit)}")
    print(f"     Errors: {result.get('errors', 0)}")
    print(f"     Log: {log_file}")
    if args.dry_run:
        print(f"\n     To send for real: python run.py send --name \"{name}\" --region {region} --source {source} --leads {args.leads or 'zoho-crm'} --account {acc_name}")
    print()


def cmd_analytics(args):
    """Show campaign logs from .tmp/"""
    import glob as g
    log_files = sorted(g.glob(os.path.join(TMP_DIR, "*_log.json")))

    print(f"\n{'='*60}")
    print(f"  CAMPAIGN LOGS")
    print(f"{'='*60}")

    if not log_files:
        print("\n  No campaigns sent yet.")
        print("  Run: python run.py send --name 'Test' --region us --source apollo-csv --leads file.csv")
        print()
        return

    for lf in log_files:
        with open(lf) as f:
            log = json.load(f)
        name = os.path.basename(lf).replace("_log.json", "").replace("_", " ").title()
        print(f"\n  📊 {name}")
        print(f"     Account: {log.get('account','?')} | Region: {log.get('region','?')}")
        print(f"     Sent: {log.get('sent',0)} | Errors: {log.get('errors',0)} | Dry run: {log.get('dry_run',False)}")
        print(f"     Time: {log.get('timestamp','?')}")
    print()


def cmd_test(args):
    """Send a test email to verify SMTP works."""
    from smtp_sender import get_accounts, test_account
    accounts = get_accounts()
    if not args.account or args.account not in accounts:
        print(f"❌ --account required. Available: {list(accounts.keys())}")
        return
    if not args.to:
        print("❌ --to <email> required")
        return
    result = test_account(accounts[args.account], args.to)
    icon = "✅" if result["status"] == "sent" else "❌"
    print(f"{icon} {result}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Onsite Email Outreach — Zero-manual cold email automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py dns-check                                    # Check domain health
  python run.py status                                       # Show SMTP accounts
  python run.py test --account akshansh --to me@example.com  # Test email
  python run.py send --name "Houston" --region us --source apollo-csv --leads houston.csv --dry-run
  python run.py send --name "Houston" --region us --source apollo-csv --leads houston.csv --account akshansh
  python run.py send --name "India CRM" --region india --source zoho-crm --account taniya
  python run.py send --name "UAE" --region middle_east --source google-sheet --leads SHEET_ID
  python run.py logs                                         # Show send history
        """)

    sub = parser.add_subparsers(dest="command")

    # dns-check
    sub.add_parser("dns-check", help="Check DNS for all Onsite domains")

    # status
    sub.add_parser("status", help="Show SMTP accounts status")

    # test
    p_test = sub.add_parser("test", help="Send a test email")
    p_test.add_argument("--account", required=True, help="Account name (akshansh, anjali, taniya)")
    p_test.add_argument("--to", required=True, help="Recipient email")

    # send (was 'create')
    p_send = sub.add_parser("send", help="Send campaign via SMTP")
    p_send.add_argument("--name", required=True, help="Campaign name")
    p_send.add_argument("--region", required=True, choices=["us", "australia", "middle_east", "india"])
    p_send.add_argument("--source", required=True, choices=["apollo-csv", "zoho-crm", "google-sheet", "json"])
    p_send.add_argument("--leads", help="CSV/JSON file path or Google Sheet ID")
    p_send.add_argument("--account", help="SMTP account name (akshansh, anjali, taniya)")
    p_send.add_argument("--sender-name", default="Akshansh - Onsite Teams")
    p_send.add_argument("--daily-limit", type=int, default=25)
    p_send.add_argument("--dry-run", action="store_true", help="Preview without sending")

    # logs
    sub.add_parser("logs", help="Show campaign send logs")

    args = parser.parse_args()

    commands = {
        "dns-check": cmd_dns_check,
        "status": cmd_status,
        "test": cmd_test,
        "send": cmd_create,
        "logs": cmd_analytics,
    }

    if not args.command:
        parser.print_help()
    elif args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()

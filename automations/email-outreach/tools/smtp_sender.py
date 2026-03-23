#!/usr/bin/env python3
"""
SMTP Sender — Send emails directly via Zoho SMTP. Replaces Instantly.
Usage: python tools/smtp_sender.py --action test --account akshansh --to test@example.com
       python tools/smtp_sender.py --action send-campaign --leads .tmp/leads.json --region us --account akshansh
"""

import argparse
import imaplib
import json
import os
import smtplib
import ssl
import sys
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# ─── ACCOUNT CONFIG ──────────────────────────────────────

def get_accounts():
    """Load all SMTP accounts from env."""
    accounts = {}

    # Pattern: SMTP_{NAME}_EMAIL + SMTP_{NAME}_PASSWORD
    prefixes = {
        "akshansh": ("SMTP_AKSHANSH_EMAIL", "SMTP_AKSHANSH_PASSWORD", "Akshansh Agarwal - Onsite Teams"),
        "akshansh2": ("SMTP_AKSHANSH2_EMAIL", "SMTP_AKSHANSH2_PASSWORD", "Akshansh Agarwal - Onsite Teams"),
        "anjali": ("SMTP_ANJALI_EMAIL", "SMTP_ANJALI_PASSWORD", "Anjali Bajaj - Onsite Teams"),
        "taniya": ("SMTP_TANIYA_EMAIL", "SMTP_TANIYA_PASSWORD", "Taniya Malhotra - Onsite Teams"),
        "akshansh_online": ("SMTP_AKSHANSH_ONLINE_EMAIL", "SMTP_AKSHANSH_ONLINE_PASSWORD", "Akshansh Agarwal - Onsite Teams"),
    }

    for name, (email_key, pass_key, display_name) in prefixes.items():
        email = os.environ.get(email_key, "")
        password = os.environ.get(pass_key, "")
        if email and password and password != "PASTE_PASSWORD_HERE":
            accounts[name] = {
                "email": email,
                "password": password,
                "display_name": display_name,
                "host": os.environ.get("SMTP_HOST", "smtp.zoho.in"),
                "port": int(os.environ.get("SMTP_PORT", "465")),
            }

    return accounts


def get_smtp_connection(account):
    """Create SMTP connection with SSL."""
    context = ssl.create_default_context()
    server = smtplib.SMTP_SSL(account["host"], account["port"], context=context)
    server.login(account["email"], account["password"])
    return server


# ─── SENDING ─────────────────────────────────────────────

def send_email(account, to_email, subject, html_body, reply_to=None):
    """Send a single email via SMTP."""
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{account['display_name']} <{account['email']}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to

    # Add unsubscribe header (helps deliverability)
    msg["List-Unsubscribe"] = f"<mailto:{account['email']}?subject=unsubscribe>"

    msg.attach(MIMEText(html_body, "html"))

    try:
        server = get_smtp_connection(account)
        server.sendmail(account["email"], to_email, msg.as_string())
        server.quit()

        # Save to Sent folder via IMAP so it shows in Zoho Mail
        try:
            imap_host = account["host"].replace("smtp.", "imap.")
            imap = imaplib.IMAP4_SSL(imap_host, 993)
            imap.login(account["email"], account["password"])
            imap.append("Sent", "\\Seen", None, msg.as_bytes())
            imap.logout()
        except Exception:
            pass  # Non-critical — email still sent even if IMAP save fails

        return {"status": "sent", "to": to_email, "from": account["email"]}
    except smtplib.SMTPAuthenticationError as e:
        return {"status": "auth_error", "to": to_email, "error": str(e)}
    except smtplib.SMTPRecipientsRefused as e:
        return {"status": "bounced", "to": to_email, "error": str(e)}
    except Exception as e:
        return {"status": "error", "to": to_email, "error": str(e)}


def send_campaign(account, leads, sequences, region, daily_limit=25, dry_run=False):
    """
    Send first email in sequence to all leads.
    Respects daily limit. Logs everything.
    """
    seq = sequences[0]  # First email only (follow-ups are separate runs)
    sent = 0
    errors = []
    results = []

    print(f"\n{'='*50}", file=sys.stderr)
    print(f"  SENDING CAMPAIGN", file=sys.stderr)
    print(f"  From: {account['email']}", file=sys.stderr)
    print(f"  Leads: {len(leads)}", file=sys.stderr)
    print(f"  Daily limit: {daily_limit}", file=sys.stderr)
    print(f"  Dry run: {dry_run}", file=sys.stderr)
    print(f"{'='*50}\n", file=sys.stderr)

    for i, lead in enumerate(leads[:daily_limit]):
        email = lead.get("email", "")
        if not email:
            continue

        # Replace template variables
        custom = lead.get("custom_variables", {})
        subject = seq["subject"]
        body = seq["body"]

        for key, val in custom.items():
            subject = subject.replace(f"{{{{{key}}}}}", val or "")
            body = body.replace(f"{{{{{key}}}}}", val or "")

        # Replace senderName with account display name
        sender_short = account["display_name"].split(" - ")[0]  # "Akshansh Agarwal"
        body = body.replace("{{senderName}}", sender_short)
        subject = subject.replace("{{senderName}}", sender_short)

        if dry_run:
            print(f"  [DRY RUN] Would send to: {email} | Subject: {subject[:50]}", file=sys.stderr)
            results.append({"status": "dry_run", "to": email, "subject": subject})
            sent += 1
            continue

        # Send with rate limiting (2-5 sec between emails for deliverability)
        result = send_email(account, email, subject, body)
        results.append(result)

        if result["status"] == "sent":
            sent += 1
            print(f"  [{sent}/{min(len(leads), daily_limit)}] ✅ {email}", file=sys.stderr)
        elif result["status"] == "auth_error":
            print(f"  ❌ Auth failed for {account['email']} — check password in .env", file=sys.stderr)
            errors.append(result)
            break  # Stop on auth error
        else:
            print(f"  ⚠️  {email}: {result['status']}", file=sys.stderr)
            errors.append(result)

        # Rate limit: random 3-7 second delay between emails
        if not dry_run and i < min(len(leads), daily_limit) - 1:
            import random
            delay = random.uniform(3, 7)
            time.sleep(delay)

    # Log results
    log = {
        "timestamp": datetime.now().isoformat(),
        "account": account["email"],
        "region": region,
        "total_leads": len(leads),
        "daily_limit": daily_limit,
        "sent": sent,
        "errors": len(errors),
        "dry_run": dry_run,
        "results": results,
    }

    return log


# ─── TEST ────────────────────────────────────────────────

def test_account(account, to_email):
    """Send a test email to verify SMTP works."""
    html = f"""
    <div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
      <div style="background:linear-gradient(135deg,#1a0b50,#2d1670);padding:28px 24px;text-align:center;border-radius:8px 8px 0 0;">
        <img src="https://www.onsiteteams.com/_next/image?url=%2Fimages%2Flogo-white.webp&w=384&q=75" alt="Onsite Teams" height="36">
      </div>
      <div style="background:#fff;padding:32px 28px;border-radius:0 0 8px 8px;border:1px solid #eee;">
        <h2 style="color:#1a0b50;margin-top:0;">SMTP Test — {account['email']}</h2>
        <p>This email was sent directly via <strong>Zoho SMTP</strong> (no Instantly).</p>
        <p><strong>Account:</strong> {account['email']}<br>
        <strong>Server:</strong> {account['host']}:{account['port']}<br>
        <strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p style="background:#f0fdf4;padding:12px;border-radius:6px;">
          If you see this email, SMTP is working correctly for this account.
        </p>
      </div>
    </div>
    """

    result = send_email(account, to_email, f"[SMTP Test] {account['email']} — {datetime.now().strftime('%H:%M')}", html)
    return result


def list_accounts_status():
    """List all configured accounts and their status."""
    accounts = get_accounts()

    print(f"\n{'='*50}", file=sys.stderr)
    print(f"  SMTP ACCOUNTS STATUS", file=sys.stderr)
    print(f"{'='*50}", file=sys.stderr)

    if not accounts:
        print("\n  ❌ No accounts configured. Update passwords in .env", file=sys.stderr)
        return {"status": "no_accounts", "accounts": []}

    results = []
    for name, acc in accounts.items():
        try:
            server = get_smtp_connection(acc)
            server.quit()
            status = "OK"
            icon = "✅"
        except smtplib.SMTPAuthenticationError:
            status = "AUTH_FAILED"
            icon = "❌"
        except Exception as e:
            status = f"ERROR: {str(e)[:50]}"
            icon = "⚠️"

        print(f"  {icon} {name:20s} {acc['email']:40s} {status}", file=sys.stderr)
        results.append({"name": name, "email": acc["email"], "status": status})

    print(file=sys.stderr)
    return {"status": "success", "accounts": results}


# ─── MAIN ────────────────────────────────────────────────

if __name__ == "__main__":
    # Load env
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for env_path in [
        os.path.join(script_dir, '..', '..', '.env'),
        os.path.join(script_dir, '..', '..', '..', '.env'),
    ]:
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, _, v = line.partition('=')
                        os.environ.setdefault(k.strip(), v.strip())

    parser = argparse.ArgumentParser(description="SMTP Email Sender for Onsite")
    parser.add_argument("--action", required=True,
                        choices=["test", "status", "send-campaign"])
    parser.add_argument("--account", help="Account name (akshansh, anjali, taniya, etc.)")
    parser.add_argument("--to", help="Test recipient email")
    parser.add_argument("--leads", help="Leads JSON file")
    parser.add_argument("--region", choices=["us", "australia", "middle_east", "india"])
    parser.add_argument("--daily-limit", type=int, default=25)
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    parser.add_argument("--output", help="Output JSON file")
    args = parser.parse_args()

    if args.action == "status":
        result = list_accounts_status()

    elif args.action == "test":
        if not args.account or not args.to:
            print("❌ --account and --to required for test"); sys.exit(1)
        accounts = get_accounts()
        if args.account not in accounts:
            print(f"❌ Account '{args.account}' not found. Available: {list(accounts.keys())}"); sys.exit(1)
        result = test_account(accounts[args.account], args.to)
        print(f"{'✅' if result['status'] == 'sent' else '❌'} {result}", file=sys.stderr)

    elif args.action == "send-campaign":
        if not args.leads or not args.region:
            print("❌ --leads and --region required"); sys.exit(1)

        # Load sequences from instantly_api (reuse same templates)
        from instantly_api import SEQUENCES
        seqs = SEQUENCES.get(args.region)
        if not seqs:
            print(f"❌ No sequences for region: {args.region}"); sys.exit(1)

        # Load leads
        with open(args.leads) as f:
            data = json.load(f)
        leads = data.get("leads", data) if isinstance(data, dict) else data

        # Get account
        accounts = get_accounts()
        acc_name = args.account or list(accounts.keys())[0] if accounts else None
        if not acc_name or acc_name not in accounts:
            print(f"❌ No valid account. Configure passwords in .env"); sys.exit(1)

        result = send_campaign(accounts[acc_name], leads, seqs, args.region,
                               args.daily_limit, args.dry_run)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
    else:
        print(json.dumps(result, indent=2))

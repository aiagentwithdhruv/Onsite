#!/usr/bin/env python3
"""
Instantly API — Create campaigns, add leads, monitor analytics, manage accounts.
Usage: python tools/instantly_api.py --action list-accounts
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

BASE_URL = "https://api.instantly.ai/api/v2"


def _headers():
    key = os.environ.get("INSTANTLY_API_KEY")
    if not key:
        print("ERROR: INSTANTLY_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _request(method, endpoint, payload=None, params=None, retries=2):
    url = f"{BASE_URL}{endpoint}"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())

    for attempt in range(retries + 1):
        req = urllib.request.Request(url, method=method, headers=_headers())
        if payload:
            req.data = json.dumps(payload).encode("utf-8")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body.strip() else {"status": "ok"}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            if e.code == 429 and attempt < retries:
                print(f"Rate limited, waiting 30s (attempt {attempt+1})", file=sys.stderr)
                time.sleep(30)
                continue
            return {"error": f"HTTP {e.code}", "detail": error_body}
        except Exception as e:
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}


# ─── ACCOUNTS ────────────────────────────────────────────

def list_accounts():
    result = _request("GET", "/accounts", params={"limit": 100})
    if "error" in result:
        return result
    accounts = result.get("items", result if isinstance(result, list) else [])
    return {"status": "success", "count": len(accounts), "accounts": [
        {"email": a.get("email"), "status": a.get("status"),
         "warmup_enabled": a.get("warmup_enabled"),
         "daily_limit": a.get("daily_limit"),
         "health_score": a.get("warmup_health_score"),
         "emails_sent_today": a.get("emails_sent_today", 0)}
        for a in accounts
    ]}


# ─── CAMPAIGNS ───────────────────────────────────────────

def list_campaigns():
    result = _request("GET", "/campaigns", params={"limit": 100})
    if "error" in result:
        return result
    campaigns = result.get("items", result if isinstance(result, list) else [])
    return {"status": "success", "count": len(campaigns), "campaigns": [
        {"id": c.get("id"), "name": c.get("name"), "status": c.get("status"),
         "leads_count": c.get("leads_count", 0)}
        for c in campaigns
    ]}


def create_campaign(name, sequences, accounts, schedule=None, daily_limit=25):
    if not schedule:
        schedule = {
            "name": "Weekday Schedule",
            "days": {"1": True, "2": True, "3": True, "4": True, "5": True},
            "timing": {"from": "09:00", "to": "17:00"},
            "timezone": "America/Chicago"
        }

    steps = []
    for i, seq in enumerate(sequences):
        step = {"subject": seq["subject"] if i == 0 else "", "body": seq["body"]}
        if i > 0:
            step["delay"] = seq.get("delay_days", 3)
            step["type"] = "follow_up"
        steps.append(step)

    payload = {
        "name": name,
        "sequences": [{"steps": steps}],
        "campaign_schedule": {"schedules": [schedule]},
        "email_list": accounts,
        "daily_limit": daily_limit,
        "stop_on_reply": True,
        "stop_on_auto_reply": True,
        "link_tracking": False,
        "open_tracking": True,
        "text_only": False,
    }

    result = _request("POST", "/campaigns", payload=payload)
    if "error" not in result:
        print(f"Campaign created: {name} (ID: {result.get('id')})", file=sys.stderr)
    return result


def add_leads(campaign_id, leads):
    batch_size = 1000
    total_added = 0
    errors = []
    for i in range(0, len(leads), batch_size):
        batch = leads[i:i + batch_size]
        result = _request("POST", "/leads", payload={"campaign_id": campaign_id, "leads": batch})
        if "error" in result:
            errors.append({"batch": i // batch_size, "error": result})
        else:
            added = result.get("leads_added", len(batch))
            total_added += added
            print(f"Added batch {i // batch_size + 1}: {added} leads", file=sys.stderr)
    return {"status": "success" if not errors else "partial",
            "total_added": total_added, "errors": errors}


def pause_campaign(campaign_id):
    return _request("POST", f"/campaigns/{campaign_id}/pause")


def resume_campaign(campaign_id):
    return _request("POST", f"/campaigns/{campaign_id}/resume")


# ─── ANALYTICS ───────────────────────────────────────────

def get_analytics(campaign_id=None):
    params = {"limit": 100}
    if campaign_id:
        params["campaign_id"] = campaign_id
    result = _request("GET", "/analytics/campaign/overview", params=params)
    if "error" in result:
        return result
    data = result if isinstance(result, list) else result.get("items", [result])
    return {"status": "success", "analytics": [
        {"campaign_id": i.get("campaign_id"), "campaign_name": i.get("campaign_name"),
         "leads_count": i.get("leads_count", 0), "emails_sent": i.get("emails_sent", 0),
         "opens": i.get("opens", 0), "replies": i.get("replies", 0),
         "bounces": i.get("bounces", 0), "open_rate": i.get("open_rate", "0%"),
         "reply_rate": i.get("reply_rate", "0%"), "bounce_rate": i.get("bounce_rate", "0%")}
        for i in data
    ]}


# ─── EMAIL SEQUENCES ────────────────────────────────────

SEQUENCES = {
    "us": [
        {"subject": "{{companyName}} — still using spreadsheets for site tracking?",
         "body": """<p>Hi {{firstName}},</p>
<p>Quick question — how is {{companyName}} currently tracking labor hours, materials, and costs across your job sites?</p>
<p>Most contractors I speak with in {{city}} are still using spreadsheets or paper timesheets. That usually means 10-15 hours/week wasted on admin and 10-30% cost overruns they can't catch in time.</p>
<p>We built <strong>Onsite Teams</strong> for exactly this. It's a mobile-first platform used by 10,000+ construction companies to manage:</p>
<ul><li>Real-time labor tracking with GPS attendance</li><li>Material & inventory management across sites</li><li>BOQ and cost tracking with automated daily reports</li><li>Purchase orders, RFQs, and vendor management</li></ul>
<p>At <strong>$200/user/year</strong>, it's a fraction of what Procore or Buildertrend charges — and it takes 1-2 weeks to implement, not months.</p>
<p>Free trial (no card): <a href="https://web.onsiteteams.com/">https://web.onsiteteams.com/</a></p>
<p>Or if you'd prefer a quick 15-min walkthrough, I'm happy to show you how it works for a team like yours.</p>
<p>Best,<br>{{senderName}}<br>Onsite Teams | 10,000+ Companies Globally<br>www.onsiteteams.com</p>""",
         "delay_days": 0},
        {"subject": "",
         "body": """<p>Hi {{firstName}},</p>
<p>Following up with a real example.</p>
<p>A 45-person contracting firm managing 6 active sites was losing 12+ hours/week on manual timesheets. After switching to Onsite Teams:</p>
<ul><li>Payroll processing: 3 days → 4 hours</li><li>Material waste reduced by 15%</li><li>Real-time visibility across all sites</li><li>Cost savings: 7% on overall project costs</li></ul>
<p>For a team of 20: $4,000/year ($333/month for the entire team). Less than one missed delivery.</p>
<p><strong>Full refund within 30 days</strong> — no questions asked.</p>
<p>Want to see a quick demo? Just reply with a time that works.</p>
<p>{{senderName}}</p>""",
         "delay_days": 3},
        {"subject": "",
         "body": """<p>Hi {{firstName}},</p>
<p>Last note from me — I know you're busy running job sites, not reading emails.</p>
<p>→ Free trial: <a href="https://web.onsiteteams.com/">https://web.onsiteteams.com/</a><br>
→ $200/user/year (10-20x cheaper than Procore)<br>
→ 10,000+ construction companies use it<br>
→ 30-day money-back guarantee<br>
→ Live in 1-2 weeks, not months</p>
<p>If managing labor, materials, or costs across sites is ever a headache for {{companyName}}, give it a 10-minute look.</p>
<p>Best,<br>{{senderName}}<br>Onsite Teams<br>www.onsiteteams.com</p>""",
         "delay_days": 4},
    ],
    "australia": [
        {"subject": "{{companyName}} — tracking labour & materials across sites?",
         "body": """<p>Hi {{firstName}},</p>
<p>I came across {{companyName}} while researching construction firms in {{city}}.</p>
<p>How are you currently managing labour attendance, material costs, and daily progress reports across your sites?</p>
<p>We work with 10,000+ construction companies globally. <strong>Onsite Teams</strong> is mobile-first — supervisors log everything from their phones:</p>
<ul><li>GPS-based labour attendance & shift tracking</li><li>Material & inventory management with purchase orders</li><li>BOQ management (quantities, rates, cost comparison)</li><li>Daily progress reports with photos from site</li><li>Payroll processing & petty cash tracking</li></ul>
<p>Pricing: <strong>$200/user/year (Business)</strong> or $250/user/year (Business+). A fraction of Procore — implementation in 1-2 weeks.</p>
<p>Free trial: <a href="https://web.onsiteteams.com/">https://web.onsiteteams.com/</a></p>
<p>Cheers,<br>{{senderName}}<br>Onsite Teams | 10,000+ Companies | ISO Certified<br>www.onsiteteams.com</p>""",
         "delay_days": 0},
        {"subject": "",
         "body": """<p>Hi {{firstName}},</p>
<p>Quick follow-up with numbers:</p>
<p>→ 7% average reduction in project costs<br>→ 70% faster payroll processing<br>→ 15% less material wastage<br>→ Real-time site visibility</p>
<p>For 15 users: Business $3,000/year ($250/month total). <strong>30-day money-back guarantee.</strong></p>
<p>Worth a look: <a href="https://web.onsiteteams.com/">https://web.onsiteteams.com/</a></p>
<p>{{senderName}}</p>""",
         "delay_days": 3},
        {"subject": "",
         "body": """<p>Hi {{firstName}},</p>
<p>Final follow-up:</p>
<p>→ Free trial: <a href="https://web.onsiteteams.com/">https://web.onsiteteams.com/</a><br>→ $200/user/year (vs Procore $2,388+)<br>→ 10,000+ companies trust it<br>→ Running on your team's phones in 10 minutes</p>
<p>All the best with your projects.</p>
<p>Cheers,<br>{{senderName}}</p>""",
         "delay_days": 4},
    ],
    "middle_east": [
        {"subject": "{{companyName}} — labour & project management",
         "body": """<p>Hi {{firstName}},</p>
<p>Noticed {{companyName}} operates in the {{city}} construction market.</p>
<p>We work with 100+ construction companies across the UAE — <strong>Onsite Teams</strong> helps manage:</p>
<ul><li>Labour attendance with GPS (critical for large UAE sites)</li><li>Material procurement and inventory</li><li>BOQ tracking and automated cost reports</li><li>Daily site progress with photo documentation</li><li>Payroll for multi-nationality workforces</li></ul>
<p>Average client saves 7% on project costs. Pricing: <strong>$200/user/year</strong>.</p>
<p>Free trial: <a href="https://web.onsiteteams.com/">https://web.onsiteteams.com/</a></p>
<p>10,000+ companies globally | ISO certified | $600M+ in projects managed</p>
<p>Would you be open to a 15-min demo?</p>
<p>Best,<br>{{senderName}}<br>Onsite Teams<br>www.onsiteteams.com</p>""",
         "delay_days": 0},
        {"subject": "",
         "body": """<p>Hi {{firstName}},</p>
<p>A Dubai client (50+ workers, 4 sites) was spending 15+ hours/week on manual reporting. After Onsite Teams:</p>
<ul><li>Instant supervisor reports (mobile app)</li><li>Automated purchase orders & stock alerts</li><li>70% faster payment processing</li><li>GPS attendance eliminated buddy punching</li></ul>
<p>25 users: $5,000/year ($417/month total). <strong>30-day money-back guarantee.</strong></p>
<p>{{senderName}}</p>""",
         "delay_days": 3},
        {"subject": "",
         "body": """<p>Hi {{firstName}},</p>
<p>Last note:</p>
<p>→ Free trial: <a href="https://web.onsiteteams.com/">https://web.onsiteteams.com/</a><br>→ $200/user/year<br>→ 100+ UAE companies use it<br>→ ISO certified, VC-backed ($1.72M raised)<br>→ Live in 1-2 weeks</p>
<p>If labour tracking or project cost control matters for {{companyName}}, just reply.</p>
<p>Best,<br>{{senderName}}</p>""",
         "delay_days": 4},
    ],
    "india": [
        {"subject": "{{companyName}} — site pe kaam track ho raha hai?",
         "body": """<p>Hi {{firstName}},</p>
<p>{{companyName}} mein abhi labour attendance, material, aur daily progress kaise track hota hai — WhatsApp groups aur Excel?</p>
<p><strong>Onsite Teams</strong> se 10,000+ construction companies manage karti hain:</p>
<ul><li>GPS-based attendance (buddy punching khatam)</li><li>Material & inventory tracking (koi cheez miss nahi hogi)</li><li>BOQ management (quantities, rates, cost comparison)</li><li>Daily progress photos from site</li><li>Payroll & petty cash processing</li></ul>
<p>Pricing: <strong>₹500/user/month</strong> (Business) ya ₹625/user/month (Business+)</p>
<p>Free trial — no card needed: <a href="https://web.onsiteteams.com/">https://web.onsiteteams.com/</a></p>
<p>15 minute demo? Just reply "Yes".</p>
<p>Regards,<br>{{senderName}}<br>Onsite Teams | 10,000+ Companies | ISO Certified<br>www.onsiteteams.com</p>""",
         "delay_days": 0},
        {"subject": "",
         "body": """<p>Hi {{firstName}},</p>
<p>Ek real example — 45 workers, 6 sites wali company:</p>
<ul><li>Payroll: 3 din se 4 ghante</li><li>Material waste: 15% kam</li><li>Real-time sabhi sites ki visibility</li><li>7% overall project cost savings</li></ul>
<p>20 users ke liye: ₹10,000/month (poori team). Ek missed delivery se bhi kam.</p>
<p><strong>30-din money-back guarantee.</strong> Risk zero.</p>
<p>Demo dekhna hai? Reply karo.</p>
<p>{{senderName}}</p>""",
         "delay_days": 3},
        {"subject": "",
         "body": """<p>Hi {{firstName}},</p>
<p>Last message — short mein:</p>
<p>→ Free trial: <a href="https://web.onsiteteams.com/">https://web.onsiteteams.com/</a><br>→ ₹500/user/month<br>→ 10,000+ companies use karte hain<br>→ 30-din refund guarantee<br>→ 1-2 hafton mein live</p>
<p>Agar {{companyName}} ke liye labour, material, ya cost tracking headache hai — ek baar try karo.</p>
<p>{{senderName}}<br>Onsite Teams<br>www.onsiteteams.com</p>""",
         "delay_days": 4},
    ],
}


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

    parser = argparse.ArgumentParser(description="Instantly.ai API automation")
    parser.add_argument("--action", required=True,
                        choices=["list-accounts", "list-campaigns", "create-campaign",
                                 "add-leads", "get-analytics", "pause", "resume", "show-sequences"])
    parser.add_argument("--name", help="Campaign name")
    parser.add_argument("--region", choices=["us", "australia", "middle_east", "india"])
    parser.add_argument("--accounts", help="Comma-separated sender emails")
    parser.add_argument("--campaign-id", help="Campaign ID")
    parser.add_argument("--input", help="Input JSON file (for add-leads)")
    parser.add_argument("--output", help="Output JSON file")
    parser.add_argument("--daily-limit", type=int, default=25)
    args = parser.parse_args()

    if args.action == "list-accounts":
        result = list_accounts()
    elif args.action == "list-campaigns":
        result = list_campaigns()
    elif args.action == "create-campaign":
        if not args.name or not args.region:
            result = {"error": "--name and --region required"}
        else:
            seqs = SEQUENCES.get(args.region)
            if not seqs:
                result = {"error": f"Unknown region: {args.region}"}
            else:
                accs = args.accounts.split(",") if args.accounts else []
                tz = {"us": "America/Chicago", "australia": "Australia/Perth",
                      "middle_east": "Asia/Dubai", "india": "Asia/Kolkata"}.get(args.region, "America/Chicago")
                schedule = {"name": "Weekday", "days": {"1": True, "2": True, "3": True, "4": True, "5": True},
                            "timing": {"from": "09:00", "to": "17:00"}, "timezone": tz}
                result = create_campaign(args.name, seqs, accs, schedule, args.daily_limit)
    elif args.action == "add-leads":
        if not args.campaign_id or not args.input:
            result = {"error": "--campaign-id and --input required"}
        else:
            with open(args.input) as f:
                data = json.load(f)
            leads = data.get("leads", data) if isinstance(data, dict) else data
            result = add_leads(args.campaign_id, leads)
    elif args.action == "get-analytics":
        result = get_analytics(args.campaign_id)
    elif args.action == "pause":
        result = pause_campaign(args.campaign_id)
    elif args.action == "resume":
        result = resume_campaign(args.campaign_id)
    elif args.action == "show-sequences":
        result = SEQUENCES

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
    else:
        print(json.dumps(result, indent=2))

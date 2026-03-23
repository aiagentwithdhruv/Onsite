#!/usr/bin/env python3
"""
AUTOMATION 6: Ad Fatigue & Dying Campaign Alert
Schedule: Weekly Monday 9 AM

Uses Facebook Ads API to detect:
- Campaigns with increasing CPL (cost per lead)
- Ad sets with high frequency (audience fatigue)
- Campaigns with zero leads but still spending
Sends report to Dhruv + Akshansh.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from whatsapp import send_text
from config import MANAGERS

TODAY = datetime.now()
TODAY_STR = TODAY.strftime("%Y-%m-%d")
LAST_30 = (TODAY - timedelta(days=30)).strftime("%Y-%m-%d")
LAST_7 = (TODAY - timedelta(days=7)).strftime("%Y-%m-%d")

# FB Ads config
FB_TOKEN = os.environ.get("FB_ACCESS_TOKEN", "")
FB_AD_ACCOUNT = "act_3176065209371338"
FB_API_VERSION = "v21.0"
FB_BASE = f"https://graph.facebook.com/{FB_API_VERSION}"

# Try to load token from MCP env or .env
if not FB_TOKEN:
    env_path = "/Volumes/Dhruv_SSD/AIwithDhruv/Claude/Onsite/sales-intelligence/backend/.env"
    try:
        with open(env_path) as f:
            for line in f:
                if line.startswith("FB_ACCESS_TOKEN="):
                    FB_TOKEN = line.split("=", 1)[1].strip().strip('"')
                    break
    except FileNotFoundError:
        pass

# Also try the MCP settings for the token
if not FB_TOKEN:
    settings_path = os.path.expanduser("~/.claude/projects/-Volumes-Dhruv-SSD-AIwithDhruv-Claude/settings.json")
    try:
        with open(settings_path) as f:
            settings = json.load(f)
            for server in settings.get("mcpServers", {}).values():
                env = server.get("env", {})
                if "FB_ACCESS_TOKEN" in env:
                    FB_TOKEN = env["FB_ACCESS_TOKEN"]
                    break
    except (FileNotFoundError, json.JSONDecodeError):
        pass


def fb_api(endpoint: str, params: dict = None) -> dict:
    if not FB_TOKEN:
        return {"error": "No FB_ACCESS_TOKEN found"}
    p = params or {}
    p["access_token"] = FB_TOKEN
    qs = urllib.parse.urlencode(p)
    url = f"{FB_BASE}/{endpoint}?{qs}"
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"error": str(e), "body": body}


def run():
    print(f"=== AD FATIGUE ALERT — {TODAY_STR} ===\n")

    if not FB_TOKEN:
        print("ERROR: No FB_ACCESS_TOKEN found. Set it in .env or MCP settings.")
        return

    # 1. Get campaigns with spend in last 30 days
    campaigns = fb_api(f"{FB_AD_ACCOUNT}/campaigns", {
        "fields": "name,status,objective",
        "filtering": json.dumps([{"field": "effective_status", "operator": "IN", "value": ["ACTIVE"]}]),
        "limit": 50,
    })

    if "error" in campaigns:
        print(f"FB API error: {campaigns}")
        return

    campaign_list = campaigns.get("data", [])
    print(f"Active campaigns: {len(campaign_list)}")

    # 2. Get insights for each campaign (last 7 days vs previous 7 days)
    alerts = []
    campaign_data = []

    for camp in campaign_list:
        cid = camp["id"]
        cname = camp["name"]

        # Last 7 days
        recent = fb_api(f"{cid}/insights", {
            "fields": "spend,impressions,clicks,actions,cost_per_action_type,frequency",
            "time_range": json.dumps({"since": LAST_7, "until": TODAY_STR}),
        })

        # Previous 7-14 days
        prev_start = (TODAY - timedelta(days=14)).strftime("%Y-%m-%d")
        previous = fb_api(f"{cid}/insights", {
            "fields": "spend,impressions,clicks,actions,cost_per_action_type,frequency",
            "time_range": json.dumps({"since": prev_start, "until": LAST_7}),
        })

        r_data = recent.get("data", [{}])
        p_data = previous.get("data", [{}])

        if not r_data:
            continue

        r = r_data[0] if r_data else {}
        p = p_data[0] if p_data else {}

        spend_recent = float(r.get("spend", 0))
        spend_prev = float(p.get("spend", 0))
        freq_recent = float(r.get("frequency", 0))

        # Count leads from actions
        leads_recent = 0
        leads_prev = 0
        cpl_recent = 0
        cpl_prev = 0

        for action in r.get("actions", []):
            if action.get("action_type") == "lead":
                leads_recent = int(action.get("value", 0))
        for cpa in r.get("cost_per_action_type", []):
            if cpa.get("action_type") == "lead":
                cpl_recent = float(cpa.get("value", 0))

        for action in p.get("actions", []):
            if action.get("action_type") == "lead":
                leads_prev = int(action.get("value", 0))
        for cpa in p.get("cost_per_action_type", []):
            if cpa.get("action_type") == "lead":
                cpl_prev = float(cpa.get("value", 0))

        camp_info = {
            "name": cname,
            "spend_7d": spend_recent,
            "leads_7d": leads_recent,
            "cpl_7d": cpl_recent,
            "spend_prev": spend_prev,
            "leads_prev": leads_prev,
            "cpl_prev": cpl_prev,
            "frequency": freq_recent,
        }
        campaign_data.append(camp_info)

        # Alert conditions
        # a) CPL increased >30%
        if cpl_prev > 0 and cpl_recent > 0 and cpl_recent > cpl_prev * 1.3:
            pct = int((cpl_recent - cpl_prev) / cpl_prev * 100)
            alerts.append(f"*CPL UP {pct}%* — {cname}\n  Rs.{cpl_prev:.0f} → Rs.{cpl_recent:.0f}")

        # b) Frequency >3 (audience fatigue)
        if freq_recent > 3.0:
            alerts.append(f"*AUDIENCE FATIGUE* — {cname}\n  Frequency: {freq_recent:.1f} (>3.0 = burnt out)")

        # c) Spending but zero leads
        if spend_recent > 1000 and leads_recent == 0:
            alerts.append(f"*ZERO LEADS* — {cname}\n  Spent Rs.{spend_recent:.0f} in 7 days, 0 leads")

        # d) Leads crashed >50%
        if leads_prev > 5 and leads_recent < leads_prev * 0.5:
            pct = int((leads_prev - leads_recent) / leads_prev * 100)
            alerts.append(f"*LEADS DOWN {pct}%* — {cname}\n  {leads_prev} → {leads_recent} (7-day)")

    # Build report
    msg = f"*AD PERFORMANCE ALERT — {TODAY_STR}*\n\n"

    if alerts:
        msg += f"*{len(alerts)} Issues Detected:*\n\n"
        for i, alert in enumerate(alerts, 1):
            msg += f"{i}. {alert}\n\n"
    else:
        msg += "No critical issues. All campaigns performing within normal range.\n\n"

    # Campaign summary
    msg += f"*Active Campaigns (7-day):*\n"
    for c in sorted(campaign_data, key=lambda x: x["spend_7d"], reverse=True)[:8]:
        if c["spend_7d"] > 0:
            msg += f"- {c['name'][:30]}: Rs.{c['spend_7d']:.0f} spend"
            if c["leads_7d"] > 0:
                msg += f" | {c['leads_7d']} leads | Rs.{c['cpl_7d']:.0f} CPL"
            else:
                msg += f" | 0 leads"
            msg += "\n"

    msg += f"\n_Onsite Sales Intelligence_"

    # Send to Dhruv + Akshansh (not Sumit — he's sales, not marketing)
    print(f"\nAlerts found: {len(alerts)}")
    ad_recipients = {k: v for k, v in MANAGERS.items() if k in ("Dhruv", "Akshansh")}
    if not ad_recipients:
        ad_recipients = MANAGERS  # fallback (test mode)
    print(f"\nSending to {', '.join(ad_recipients.keys())}...")
    for name, phone in ad_recipients.items():
        r = send_text(phone, msg, name)
        print(f"  {name}: {r.get('status', 'FAILED')}")

    print(f"\nDone. Campaigns checked: {len(campaign_data)} | Alerts: {len(alerts)}")


if __name__ == "__main__":
    run()

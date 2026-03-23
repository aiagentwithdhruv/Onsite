#!/usr/bin/env python3
"""
AUTOMATION 3: Daily Rep Scorecard on WhatsApp
Schedule: Daily 9 AM

Pulls each rep's MTD numbers from Zoho CRM:
- Demos done this month
- Sales (Subscribed) this month
- Pipeline (VH/HP/Demo Booked counts)
- Follow-ups due today
Sends personalized WhatsApp to each rep + summary to managers.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime
from zoho import coql_count, coql_paginate
from whatsapp import send_text
from config import SALES_REPS, PRE_SALES, MANAGERS

TODAY = datetime.now()
MONTH_START = TODAY.strftime("%Y-%m-01")
TODAY_STR = TODAY.strftime("%Y-%m-%d")
MONTH_NAME = TODAY.strftime("%B %Y")
DAY_NUM = TODAY.day


def run():
    print(f"=== DAILY SCORECARD — {TODAY_STR} ===\n")

    # Team-wide numbers
    total_demos = coql_count(
        f"SELECT COUNT(id) as total FROM Leads "
        f"WHERE Demo_Done_Date between '{MONTH_START}' and '{TODAY_STR}'"
    )

    total_sales = coql_count(
        f"SELECT COUNT(id) as total FROM Leads "
        f"WHERE Sale_Done_Date between '{MONTH_START}' and '{TODAY_STR}'"
    )

    # Pipeline
    vh = coql_count("SELECT COUNT(id) as total FROM Leads WHERE Sales_Stage = 'Very High Prospect'")
    hp = coql_count("SELECT COUNT(id) as total FROM Leads WHERE Sales_Stage = 'High Prospect'")
    demo_booked = coql_count("SELECT COUNT(id) as total FROM Leads WHERE Lead_Status = '6. Demo booked'")
    followups_today = coql_count(
        f"SELECT COUNT(id) as total FROM Leads "
        f"WHERE Lead_Task between '{TODAY_STR}T00:00:00+05:30' and '{TODAY_STR}T23:59:59+05:30'"
    )

    print(f"MTD Demos: {total_demos} | Sales: {total_sales}")
    print(f"Pipeline — VH: {vh} | HP: {hp} | Demo Booked: {demo_booked}")
    print(f"Follow-ups today: {followups_today}")

    # Per-rep demos this month (pull all and count locally since CRM owner = "Team")
    demo_leads = coql_paginate(
        f"SELECT Calling_Agent, Demo_Done_Date FROM Leads "
        f"WHERE Demo_Done_Date between '{MONTH_START}' and '{TODAY_STR}'"
    )

    # Count by Calling_Agent (pre-sales person who did the demo)
    from collections import Counter
    demo_by_agent = Counter()
    for l in demo_leads:
        agent = l.get("Calling_Agent") or "Unknown"
        demo_by_agent[agent] += 1

    # Manager summary
    mgr_msg = f"*DAILY SCORECARD — {TODAY_STR}*\n"
    mgr_msg += f"Day {DAY_NUM} of {MONTH_NAME}\n\n"
    mgr_msg += f"*Team MTD:*\n"
    mgr_msg += f"Demos: *{total_demos}*\n"
    mgr_msg += f"Sales: *{total_sales}*\n\n"
    mgr_msg += f"*Pipeline:*\n"
    mgr_msg += f"VH Prospects: {vh}\n"
    mgr_msg += f"High Prospects: {hp}\n"
    mgr_msg += f"Demo Booked: {demo_booked}\n"
    mgr_msg += f"Follow-ups Today: {followups_today}\n\n"

    if demo_by_agent:
        mgr_msg += f"*Demos MTD by Person:*\n"
        for agent, count in demo_by_agent.most_common(15):
            mgr_msg += f"  {agent}: {count}\n"

    mgr_msg += f"\n_Onsite Sales Intelligence_"

    # Send to managers
    print("\nSending to managers...")
    for name, phone in MANAGERS.items():
        r = send_text(phone, mgr_msg, name)
        print(f"  {name}: {r.get('status', 'FAILED')}")

    # Rep message — motivational + pipeline reminder
    rep_msg = f"*Good Morning! Day {DAY_NUM} of {MONTH_NAME}*\n\n"
    rep_msg += f"*Team so far:* {total_demos} demos | {total_sales} sales\n\n"
    rep_msg += f"*Today's Focus:*\n"
    rep_msg += f"- {followups_today} follow-ups due today\n"
    rep_msg += f"- {demo_booked} demos pending in pipeline\n"
    rep_msg += f"- {vh + hp} hot prospects waiting\n\n"
    rep_msg += "Check your CRM follow-up dates. Update remarks after every demo.\n\n"
    rep_msg += f"_Onsite Sales Intelligence — {TODAY_STR}_"

    # Send to all reps
    print("\nSending to reps...")
    all_team = {**SALES_REPS, **PRE_SALES}
    for name, phone in all_team.items():
        r = send_text(phone, rep_msg, name)
        print(f"  {name}: {r.get('status', 'FAILED')}")

    print(f"\nDone. Demos MTD: {total_demos} | Sales: {total_sales}")


if __name__ == "__main__":
    run()

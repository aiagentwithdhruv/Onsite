#!/usr/bin/env python3
"""
AUTOMATION 1: Follow-Up Date Alerts
Schedule: Daily 8 AM

Queries Zoho CRM for leads with follow-up dates that are:
- Due today
- Overdue (past date)
Groups by rep and sends WhatsApp alert.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from collections import defaultdict
from zoho import coql_paginate
from whatsapp import send_text
from config import SALES_REPS, MANAGERS

TODAY = datetime.now().strftime("%Y-%m-%d")
YESTERDAY = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
THREE_DAYS_AGO = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")


def run():
    print(f"=== FOLLOW-UP ALERTS — {TODAY} ===\n")

    # 1. Get leads with follow-up date today or overdue
    today_leads = coql_paginate(
        f"SELECT Company, Full_Name, Phone, Email, Lead_Task, Sales_Stage, Lead_Status, Owner "
        f"FROM Leads WHERE Lead_Task between '{TODAY}T00:00:00+05:30' and '{TODAY}T23:59:59+05:30'"
    )
    print(f"Follow-ups due today: {len(today_leads)}")

    overdue_leads = coql_paginate(
        f"SELECT Company, Full_Name, Phone, Email, Lead_Task, Sales_Stage, Lead_Status, Owner "
        f"FROM Leads WHERE Lead_Task < '{TODAY}T00:00:00+05:30' "
        f"and Lead_Task > '2026-01-01T00:00:00+05:30' "
        f"and Lead_Status not in ('12. Subscribed', '11. Rejected', '10. Not Interested (Not Potential)', 'Junk Lead')"
    )
    print(f"Overdue follow-ups: {len(overdue_leads)}")

    # 2. Build manager summary
    total_today = len(today_leads)
    total_overdue = len(overdue_leads)

    # 3. Separate urgent (>3 days overdue)
    urgent = []
    for l in overdue_leads:
        fu_date = str(l.get("Lead_Task", ""))[:10]
        if fu_date and fu_date < THREE_DAYS_AGO:
            urgent.append(l)

    # 4. Build manager report
    manager_msg = f"*FOLLOW-UP ALERT — {TODAY}*\n\n"
    manager_msg += f"Due Today: *{total_today}*\n"
    manager_msg += f"Overdue: *{total_overdue}*\n"
    manager_msg += f"Urgent (>3 days): *{len(urgent)}*\n\n"

    if today_leads:
        manager_msg += "*Today's Follow-Ups:*\n"
        for i, l in enumerate(today_leads[:15], 1):
            company = l.get("Company") or l.get("Full_Name") or "?"
            stage = l.get("Sales_Stage") or l.get("Lead_Status") or ""
            email = l.get("Email") or ""
            manager_msg += f"{i}. {company}"
            if stage:
                manager_msg += f" ({stage})"
            if email:
                manager_msg += f"\n   {email}"
            manager_msg += "\n"
        if len(today_leads) > 15:
            manager_msg += f"\n...and {len(today_leads) - 15} more\n"

    if urgent:
        manager_msg += f"\n*URGENT — Overdue >3 Days:*\n"
        for i, l in enumerate(urgent[:10], 1):
            company = l.get("Company") or l.get("Full_Name") or "?"
            fu = str(l.get("Lead_Task", ""))[:10]
            email = l.get("Email") or ""
            manager_msg += f"{i}. {company} (due: {fu})"
            if email:
                manager_msg += f"\n   {email}"
            manager_msg += "\n"

    manager_msg += "\n_Onsite Sales Intelligence_"

    # 5. Send to managers
    print("\nSending to managers...")
    for name, phone in MANAGERS.items():
        r = send_text(phone, manager_msg, name)
        print(f"  {name}: {r.get('status', 'FAILED')}")

    # 6. Send summary to team (today's count only, not full list)
    team_msg = f"*Good Morning!*\n\n"
    team_msg += f"*{total_today}* follow-ups due today across the team.\n"
    team_msg += f"*{total_overdue}* are overdue — check your CRM.\n\n"
    team_msg += "Open Zoho → Leads → Check your Follow-up Date column.\n"
    team_msg += "Don't let hot leads go cold!\n\n"
    team_msg += f"_Onsite Sales Intelligence — {TODAY}_"

    print("\nSending to reps...")
    for name, phone in SALES_REPS.items():
        r = send_text(phone, team_msg, name)
        print(f"  {name}: {r.get('status', 'FAILED')}")

    print(f"\nDone. Today: {total_today} | Overdue: {total_overdue} | Urgent: {len(urgent)}")


if __name__ == "__main__":
    run()

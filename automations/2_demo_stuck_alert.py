#!/usr/bin/env python3
"""
AUTOMATION 2: Demo Booked → No Demo Done Alert
Schedule: Daily 9 AM

Finds leads stuck in "6. Demo booked" status where demo hasn't been done.
Flags leads >3 days old as warnings, >7 days as urgent.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from zoho import coql_paginate, coql_count
from whatsapp import send_text
from config import MANAGERS

TODAY = datetime.now().strftime("%Y-%m-%d")
THREE_DAYS_AGO = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
SEVEN_DAYS_AGO = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")


def run():
    print(f"=== DEMO STUCK ALERT — {TODAY} ===\n")

    # Total demo booked with no demo done
    total = coql_count(
        "SELECT COUNT(id) as total FROM Leads "
        "WHERE Lead_Status = '6. Demo booked' and Demo_Done_Date is null"
    )
    print(f"Total stuck (demo booked, not done): {total}")

    # Booked >7 days ago — URGENT
    urgent_leads = coql_paginate(
        f"SELECT Company, Full_Name, Phone, Email, Lead_Assigned_Time, Lead_Source, Owner "
        f"FROM Leads WHERE Lead_Status = '6. Demo booked' and Demo_Done_Date is null "
        f"and Lead_Assigned_Time < '{SEVEN_DAYS_AGO}T00:00:00+05:30'"
    )
    print(f"Urgent (>7 days): {len(urgent_leads)}")

    # Booked 3-7 days ago — WARNING
    warning_leads = coql_paginate(
        f"SELECT Company, Full_Name, Phone, Email, Lead_Assigned_Time, Lead_Source "
        f"FROM Leads WHERE Lead_Status = '6. Demo booked' and Demo_Done_Date is null "
        f"and Lead_Assigned_Time between '{SEVEN_DAYS_AGO}T00:00:00+05:30' and '{THREE_DAYS_AGO}T23:59:59+05:30'"
    )
    print(f"Warning (3-7 days): {len(warning_leads)}")

    # Recent (<3 days) — just count
    recent = total - len(urgent_leads) - len(warning_leads)

    # Build report
    msg = f"*DEMO STUCK ALERT — {TODAY}*\n\n"
    msg += f"*{total}* leads are in 'Demo Booked' but demo NOT done.\n\n"
    msg += f"URGENT (>7 days stuck): *{len(urgent_leads)}*\n"
    msg += f"Warning (3-7 days): *{len(warning_leads)}*\n"
    msg += f"Recent (<3 days): *{recent}*\n"

    if urgent_leads:
        msg += f"\n*URGENT — Book or Remove These:*\n"
        for i, l in enumerate(urgent_leads[:12], 1):
            company = l.get("Company") or l.get("Full_Name") or "?"
            source = l.get("Lead_Source") or ""
            email = l.get("Email") or ""
            phone = l.get("Phone") or ""
            msg += f"{i}. *{company}*"
            if source:
                msg += f" ({source})"
            contact = email or phone
            if contact:
                msg += f"\n   {contact}"
            msg += "\n"
        if len(urgent_leads) > 12:
            msg += f"\n...and {len(urgent_leads) - 12} more urgent\n"

    if warning_leads:
        msg += f"\n*WARNING — Follow Up This Week:*\n"
        for i, l in enumerate(warning_leads[:8], 1):
            company = l.get("Company") or l.get("Full_Name") or "?"
            source = l.get("Lead_Source") or ""
            msg += f"{i}. {company}"
            if source:
                msg += f" ({source})"
            msg += "\n"
        if len(warning_leads) > 8:
            msg += f"\n...and {len(warning_leads) - 8} more\n"

    msg += f"\nEach demo = Rs.8,305 avg revenue. Don't waste booked demos!"
    msg += f"\n\n_Onsite Sales Intelligence — {TODAY}_"

    # Send to managers
    print("\nSending to managers...")
    for name, phone in MANAGERS.items():
        r = send_text(phone, msg, name)
        print(f"  {name}: {r.get('status', 'FAILED')}")

    print(f"\nDone. Total stuck: {total} | Urgent: {len(urgent_leads)} | Warning: {len(warning_leads)}")


if __name__ == "__main__":
    run()

#!/usr/bin/env python3
"""
AUTOMATION 4: CRM Hygiene Report
Schedule: Every Friday 5 PM

Checks this week's demos for data completeness:
- Remarks/Notes filled?
- Price Pitched filled?
- Follow-up date set?
Per-rep hygiene score sent to managers.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from collections import defaultdict
from zoho import coql_paginate
from whatsapp import send_text
from config import MANAGERS

TODAY = datetime.now()
WEEK_START = (TODAY - timedelta(days=TODAY.weekday())).strftime("%Y-%m-%d")
TODAY_STR = TODAY.strftime("%Y-%m-%d")
MONTH_START = TODAY.strftime("%Y-%m-01")


def run():
    print(f"=== CRM HYGIENE REPORT — {TODAY_STR} ===\n")

    # Pull all demos this month with relevant fields
    demos = coql_paginate(
        f"SELECT Company, Owner, Business_Type, Price_PItched, Lead_Task, Demo_Done_Date "
        f"FROM Leads WHERE Demo_Done_Date between '{MONTH_START}' and '{TODAY_STR}'"
    )
    print(f"Demos this month: {len(demos)}")

    if not demos:
        print("No demos found. Skipping.")
        return

    # Analyze
    total = len(demos)
    remarks_filled = 0
    price_filled = 0
    followup_set = 0

    for d in demos:
        remark = d.get("Business_Type")
        price = d.get("Price_PItched")
        fu = d.get("Lead_Task")

        if remark and str(remark).strip() not in ("", "null", "None"):
            remarks_filled += 1
        if price is not None:
            price_filled += 1
        if fu is not None:
            followup_set += 1

    remarks_pct = remarks_filled * 100 // total if total else 0
    price_pct = price_filled * 100 // total if total else 0
    fu_pct = followup_set * 100 // total if total else 0

    # Build report
    msg = f"*CRM HYGIENE REPORT — {MONTH_START} to {TODAY_STR}*\n\n"
    msg += f"Total Demos: *{total}*\n\n"

    msg += f"*Data Completeness:*\n"
    msg += f"Remarks/Notes: {remarks_filled}/{total} ({remarks_pct}%) "
    msg += f"{'OK' if remarks_pct >= 80 else 'NEEDS IMPROVEMENT'}\n"
    msg += f"Price Pitched: {price_filled}/{total} ({price_pct}%) "
    msg += f"{'OK' if price_pct >= 80 else 'NEEDS IMPROVEMENT'}\n"
    msg += f"Follow-up Set: {followup_set}/{total} ({fu_pct}%) "
    msg += f"{'OK' if fu_pct >= 80 else 'NEEDS IMPROVEMENT'}\n"

    # Gaps
    msg += f"\n*Missing Data:*\n"
    msg += f"No Remarks: *{total - remarks_filled}* demos\n"
    msg += f"No Price Pitched: *{total - price_filled}* demos\n"
    msg += f"No Follow-up Date: *{total - followup_set}* demos\n"

    # Companies with no remarks (sample)
    no_remarks = [d for d in demos if not d.get("Business_Type") or str(d.get("Business_Type", "")).strip() in ("", "null", "None")]
    if no_remarks:
        msg += f"\n*Sample — Demos Without Remarks:*\n"
        for d in no_remarks[:8]:
            company = d.get("Company") or "?"
            demo_date = str(d.get("Demo_Done_Date", ""))[:10]
            msg += f"- {company} ({demo_date})\n"
        if len(no_remarks) > 8:
            msg += f"...and {len(no_remarks) - 8} more\n"

    msg += f"\n*Target:* 80%+ on all three fields."
    msg += f"\nReps: Please update your CRM after every demo!"
    msg += f"\n\n_Onsite Sales Intelligence — {TODAY_STR}_"

    # Send to managers
    print("\nSending to managers...")
    for name, phone in MANAGERS.items():
        r = send_text(phone, msg, name)
        print(f"  {name}: {r.get('status', 'FAILED')}")

    print(f"\nDone. Remarks: {remarks_pct}% | Price: {price_pct}% | Follow-up: {fu_pct}%")


if __name__ == "__main__":
    run()

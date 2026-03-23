#!/usr/bin/env python3
"""
AUTOMATION 5: Website + WhatsApp Lead Priority Alert
Schedule: Every 4 hours (or daily 8 AM + 2 PM)

Finds new leads from Website and Customer Support WhatsApp sources
that haven't been contacted yet. These convert best — prioritize!
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from zoho import coql_paginate, coql_count
from whatsapp import send_text
from config import MANAGERS, SALES_REPS

TODAY = datetime.now()
TODAY_STR = TODAY.strftime("%Y-%m-%d")
YESTERDAY = (TODAY - timedelta(days=1)).strftime("%Y-%m-%d")
THREE_DAYS_AGO = (TODAY - timedelta(days=3)).strftime("%Y-%m-%d")


def run():
    print(f"=== HOT SOURCE ALERT — {TODAY_STR} ===\n")

    hot_sources = ["2.Website", "4.Customer Support WA"]
    all_hot_leads = []

    for source in hot_sources:
        # New leads from hot sources in last 3 days, not yet demo done
        leads = coql_paginate(
            f"SELECT Company, Full_Name, Phone, Email, Lead_Source, Lead_Status, Created_Time "
            f"FROM Leads WHERE Lead_Source = '{source}' "
            f"and Created_Time > '{THREE_DAYS_AGO}T00:00:00+05:30' "
            f"and Demo_Done_Date is null "
            f"and Lead_Status not in ('12. Subscribed', '11. Rejected', '10. Not Interested (Not Potential)', 'Junk Lead')"
        )
        print(f"{source}: {len(leads)} untouched leads (last 3 days)")
        for l in leads:
            l["_source_label"] = "Website" if "Website" in source else "WhatsApp"
        all_hot_leads.extend(leads)

    # Also check for high-value sources
    for source in ["8. Client Referral", "3. Inbound Demo Req."]:
        leads = coql_paginate(
            f"SELECT Company, Full_Name, Phone, Email, Lead_Source, Lead_Status, Created_Time "
            f"FROM Leads WHERE Lead_Source = '{source}' "
            f"and Created_Time > '{THREE_DAYS_AGO}T00:00:00+05:30' "
            f"and Demo_Done_Date is null "
            f"and Lead_Status not in ('12. Subscribed', '11. Rejected', '10. Not Interested (Not Potential)', 'Junk Lead')"
        )
        if leads:
            print(f"{source}: {len(leads)} untouched leads (last 3 days)")
            for l in leads:
                l["_source_label"] = source.split(".")[-1].strip()
            all_hot_leads.extend(leads)

    if not all_hot_leads:
        print("No hot untouched leads. All good!")
        return

    # Count by source
    from collections import Counter
    by_source = Counter(l["_source_label"] for l in all_hot_leads)

    # Build alert
    msg = f"*HOT LEAD ALERT — {TODAY_STR}*\n\n"
    msg += f"*{len(all_hot_leads)}* high-converting leads NOT YET contacted:\n\n"

    for src, count in by_source.most_common():
        msg += f"*{src}:* {count} leads\n"

    msg += f"\nThese sources convert *2-3x better* than paid ads.\n"
    msg += f"*Contact them TODAY — speed wins deals.*\n\n"

    msg += f"*Top Leads to Call:*\n"
    for i, l in enumerate(all_hot_leads[:12], 1):
        company = l.get("Company") or l.get("Full_Name") or "?"
        src = l.get("_source_label", "")
        phone = l.get("Phone") or ""
        email = l.get("Email") or ""
        status = l.get("Lead_Status") or ""

        msg += f"{i}. *{company}* ({src})"
        if status:
            msg += f" — {status}"
        contact = phone or email
        if contact:
            msg += f"\n   {contact}"
        msg += "\n"

    if len(all_hot_leads) > 12:
        msg += f"\n...and {len(all_hot_leads) - 12} more in CRM\n"

    msg += f"\n_Onsite Sales Intelligence_"

    # Send to managers
    print("\nSending to managers...")
    for name, phone in MANAGERS.items():
        r = send_text(phone, msg, name)
        print(f"  {name}: {r.get('status', 'FAILED')}")

    # Shorter alert to reps
    rep_msg = f"*HOT LEADS ALERT*\n\n"
    rep_msg += f"*{len(all_hot_leads)}* Website & WhatsApp leads from last 3 days haven't been contacted.\n\n"
    rep_msg += "These convert 2-3x better than paid leads.\n"
    rep_msg += "Check your CRM → Filter by Website & WA source → Call NOW!\n\n"
    rep_msg += f"_Onsite Sales Intelligence — {TODAY_STR}_"

    print("\nSending to reps...")
    for name, phone in SALES_REPS.items():
        r = send_text(phone, rep_msg, name)
        print(f"  {name}: {r.get('status', 'FAILED')}")

    print(f"\nDone. Hot untouched leads: {len(all_hot_leads)}")


if __name__ == "__main__":
    run()

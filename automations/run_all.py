#!/usr/bin/env python3
"""
Master runner — executes all Phase 1 automations.

Usage:
  python3 run_all.py              # Run all 6
  python3 run_all.py 1            # Run only automation 1
  python3 run_all.py 1 3 5        # Run specific ones
  python3 run_all.py --test       # Dry run (Dhruv only)
  python3 run_all.py --list       # List all automations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

AUTOMATIONS = {
    "1": ("Follow-Up Date Alerts", "1_followup_alerts"),
    "2": ("Demo Booked → No Demo Alert", "2_demo_stuck_alert"),
    "3": ("Daily Rep Scorecard", "3_daily_scorecard"),
    "4": ("CRM Hygiene Report", "4_crm_hygiene"),
    "5": ("Website/WA Hot Lead Alert", "5_hot_source_alert"),
    "6": ("Ad Fatigue Alert", "6_ad_fatigue_alert"),
}


def main():
    args = sys.argv[1:]

    if "--list" in args:
        print("=== ONSITE PHASE 1 AUTOMATIONS ===\n")
        for num, (name, module) in AUTOMATIONS.items():
            print(f"  {num}. {name} ({module}.py)")
        print("\nUsage: python3 run_all.py [1-6] [--test]")
        return

    # Which to run
    nums = [a for a in args if a.isdigit() and a in AUTOMATIONS]
    if not nums:
        nums = list(AUTOMATIONS.keys())

    test_mode = "--test" in args

    if test_mode:
        print("TEST MODE — Messages will only go to Dhruv\n")
        # Override team to just Dhruv
        import config
        config.SALES_REPS = {}
        config.PRE_SALES = {}
        config.MANAGERS = {"Dhruv": "918770101822"}
        config.ALL_TEAM = {}

    print(f"Running {len(nums)} automation(s)...\n")

    for num in nums:
        name, module_name = AUTOMATIONS[num]
        print(f"\n{'='*60}")
        print(f"  [{num}] {name}")
        print(f"{'='*60}\n")

        try:
            module = __import__(module_name)
            module.run()
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"  ALL DONE — {len(nums)} automations executed")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

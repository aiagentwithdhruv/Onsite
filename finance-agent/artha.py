#!/usr/bin/env python3
"""
ARTHA — Onsite Finance & Sales query tool (deterministic, no LLM).

Every finance number Dhruv/Claude reports comes from THIS script, never from
a model's head. Run it, read the real numbers, answer.

Usage:
  python3 artha.py summary                 # total revenue, counts (2026)
  python3 artha.py by-person               # revenue per sales person (normalized)
  python3 artha.py by-region               # revenue per region
  python3 artha.py by-month                # monthly revenue trend
  python3 artha.py by-plan                 # revenue per plan type
  python3 artha.py person "Desi"           # one person's detail
  python3 artha.py desi-reconcile          # Desi IDR collection vs commission/salary
  python3 artha.py --file data/sales_all_history.csv summary   # all-time instead of 2026

Data source: data/sales_2026.csv (main) — `Amount` column = sale value in INR.
"""
import csv, re, sys
from collections import defaultdict

DEFAULT_FILE = "data/sales_2026.csv"

# Rep name normalization — the sheet has the same person under multiple spellings,
# which splits their true total. Canonical name on the left key's value.
# EDIT THIS MAP as Dhruv confirms identities.
# CONFIRMED 2026-05-30 (Dhruv): "Amit" and "Amit Kumar" are TWO DIFFERENT people.
#   "Amit"       -> Amit Udagatti (Amit U)
#   "Amit Kumar" -> Amit Mishra
# They stay separate; we only relabel the sheet's ambiguous spellings to real names.
NAME_MAP = {
    "k kiran": "Kiran",
    "kiran": "Kiran",
    "hitangi arora": "Hitangi",
    "hitangi": "Hitangi",
    "muneera tabassum": "Muneera",
    "muneera": "Muneera",
    "ayushh kumar": "Ayushh",
    "ayushh": "Ayushh",
    "amit": "Amit Udagatti",
    "amit kumar": "Amit Mishra",
    # case variants collapse automatically via .lower() lookup below
}

# Currency: the main sheet `Amount` is ALREADY in INR. Desi's debit file is in IDR.
# Conversion confirmed from Desi's own sheet: 15,225,000 IDR = 867.79 USD
#   -> IDR/USD ~= 17,544 ; with USD/INR ~= 85 -> 1 INR ~= 206 IDR (approx).
# Her salary 3,000,000 IDR/mo == ~16,000 INR -> 187.5 IDR/INR.
# CONFIRM the standard rate with Dhruv. Used only for the Desi reconciliation view.
IDR_PER_INR = 187.5  # TODO: confirm standard rate with Dhruv


def num(s):
    s = re.sub(r"[^0-9.]", "", str(s or ""))
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


def canon(name):
    n = (name or "Unknown").strip()
    return NAME_MAP.get(n.lower(), n)


def load(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8", errors="replace")))
    return [r for r in rows if num(r.get("Amount")) > 0]


def fmt(n):
    """Indian formatting: lakh/crore."""
    n = float(n)
    if n >= 1e7:
        return f"INR {n/1e7:.2f} Cr ({n:,.0f})"
    if n >= 1e5:
        return f"INR {n/1e5:.2f} L ({n:,.0f})"
    return f"INR {n:,.0f}"


def summary(rows):
    total = sum(num(r["Amount"]) for r in rows)
    print(f"Sales:   {len(rows)}")
    print(f"Revenue: {fmt(total)}")
    print(f"Avg deal: {fmt(total/len(rows)) if rows else 0}")


def by_key(rows, key, label):
    agg = defaultdict(lambda: [0, 0.0])
    for r in rows:
        k = canon(r.get(key)) if key == "Sales Person" else (r.get(key) or "Unknown").strip()
        agg[k][0] += 1
        agg[k][1] += num(r["Amount"])
    print(f"=== {label} ===")
    for k, (c, a) in sorted(agg.items(), key=lambda x: -x[1][1]):
        print(f"  {k:22} {c:4} sales  {fmt(a)}")


def by_month(rows):
    agg = defaultdict(lambda: [0, 0.0])
    for r in rows:
        m = (r.get("Month_Year") or r.get("Payment Month") or "?").strip()
        agg[m][0] += 1
        agg[m][1] += num(r["Amount"])
    print("=== By Month ===")
    for m, (c, a) in sorted(agg.items()):
        print(f"  {m:10} {c:4} sales  {fmt(a)}")


def person(rows, name):
    target = canon(name)
    sel = [r for r in rows if canon(r.get("Sales Person")) == target]
    total = sum(num(r["Amount"]) for r in sel)
    print(f"=== {target} ===")
    print(f"Sales: {len(sel)}   Revenue: {fmt(total)}")
    for r in sorted(sel, key=lambda r: r.get("Payment Date") or ""):
        print(f"  {r.get('Payment Date',''):12} {r.get('Company Name','')[:30]:30} {fmt(num(r['Amount']))}")


# Desi ledger — payments she has ALREADY sent to Onsite (confirmed receipts).
# 2026-04-23: $867.79 via card (Razorpay pay_SgsBdGmwUkqtWy) = Rp15,225,000.
DESI_PAYMENTS_IDR = [
    ("2026-04-23", 15_225_000, "$867.79 card, Razorpay pay_SgsBdGmwUkqtWy"),
]
# Salary months counted in the current reconciliation (Jan–Jun 2026 = 6 months).
DESI_SALARY_MONTHS = 6
DESI_SALARY_IDR_PER_MONTH = 3_000_000


def desi_reconcile():
    """Match Desi's IDR debit file against her INR sales in the main sheet."""
    path = "data/desi_debit_to_onsite.csv"
    rows = list(csv.reader(open(path, encoding="utf-8", errors="replace")))
    collected = 0.0
    print("=== Desi — IDR collections (from her debit file) ===")
    for r in rows[1:]:
        if not r or not r[0] or r[0].strip() in ("Total", ""):
            continue
        if r[0].strip().startswith(("Bonus", "Salary", "Amount", "remaining")):
            continue
        price = num(r[4]) if len(r) > 4 else 0
        if price:
            collected += price
            print(f"  {r[0]:12} {r[1][:24]:24} Rp{price:,.0f}")
    commission = collected * 0.10
    salary = DESI_SALARY_MONTHS * DESI_SALARY_IDR_PER_MONTH
    owed = collected - commission - salary
    paid = sum(p[1] for p in DESI_PAYMENTS_IDR)
    outstanding = owed - paid
    print(f"\n  Total collected:       Rp{collected:,.0f}  (~{fmt(collected/IDR_PER_INR)})")
    print(f"  Desi commission (10%): Rp{commission:,.0f}")
    print(f"  Salary ({DESI_SALARY_MONTHS} mo x 3M):    Rp{salary:,.0f}")
    print(f"  = Owed to Onsite:      Rp{owed:,.0f}")
    for d, amt, note in DESI_PAYMENTS_IDR:
        print(f"  PAID {d}: Rp{amt:,.0f}  ({note})")
    print(f"  >> OUTSTANDING:        Rp{outstanding:,.0f}  (~{fmt(outstanding/IDR_PER_INR)})")
    print(f"  Blocker: Desi waiting on Onsite INVOICE to compute tax + pay remaining.")
    print(f"  NOTE: main-sheet Desi amounts are in INR; this file is what Desi physically collected in IDR.")


def main():
    args = sys.argv[1:]
    path = DEFAULT_FILE
    if "--file" in args:
        i = args.index("--file")
        path = args[i + 1]
        del args[i : i + 2]
    cmd = args[0] if args else "summary"

    if cmd == "desi-reconcile":
        return desi_reconcile()

    rows = load(path)
    if cmd == "summary":
        summary(rows)
    elif cmd == "by-person":
        by_key(rows, "Sales Person", "Revenue by Sales Person")
    elif cmd == "by-region":
        by_key(rows, "Region", "Revenue by Region")
    elif cmd == "by-plan":
        by_key(rows, "Plan Type ", "Revenue by Plan")
    elif cmd == "by-month":
        by_month(rows)
    elif cmd == "person" and len(args) > 1:
        person(rows, args[1])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()

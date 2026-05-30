# ARTHA — Onsite Finance & Sales Agent

> **अर्थ (Artha)** = wealth / prosperity / the pursuit of means. Onsite's money brain.
> **Owner:** Dhruv Tomar | **For:** Onsite Teams (Abeyaantrix Technology Pvt Ltd)
> **Status:** Live data loaded 2026-05-30. Deterministic query tool working.
> **One-line:** *"Ask anything about Onsite's money — sold this year, top rep, by region, Desi's books — get a real number from the sheet, never a guess."*

---

## How Artha works (the rule)

**Every number comes from `artha.py`, never from a model's head.** The script reads the
real sheet and computes. Claude runs it, reads the output, answers. No invented figures.

```bash
cd Onsite/finance-agent
python3 artha.py summary          # total revenue + count (2026)
python3 artha.py by-person        # revenue per rep (names normalized)
python3 artha.py by-region        # India / Middle East / SE Asia / US
python3 artha.py by-month         # monthly trend
python3 artha.py by-plan          # by plan type
python3 artha.py person "Desi"    # one rep's deal list
python3 artha.py desi-reconcile   # Desi's IDR collection vs commission/salary
python3 artha.py --file data/sales_all_history.csv summary   # all-time
```

---

## The data (in `data/`)

| File | What | Rows |
|---|---|---|
| `sales_2026.csv` | **MAIN sheet** — every 2026 sale. `Amount` = sale value in **INR**. | 717 |
| `sales_all_history.csv` | All-time history, same columns | ~5,800 |
| `desi_debit_to_onsite.csv` | Desi's IDR collections + her commission/salary reconciliation | 14 sales |

**Key columns (main sheet):** `Amount` (sale value, INR), `Sales Person` (= the team member),
`Payment Date` (when customer bought), `Region` (1.India / 2.Middle East / 4.SE Asia / 5.US),
`Plan Type`, `Company Name`, `Invoice Status` (holds invoice no. e.g. `ON/25-26/1226`), `Subscription Start/Expiry`.

**Field truth (confirmed by Dhruv 2026-05-30):**
- **Sale amount = `Amount`** (already in INR). *(This corrects the earlier Zoho note — the live CRM `Annual_Revenue` field was wrong; the real source is this sheet's `Amount`.)*
- **Sales Person = team member.** Each rep IS tracked individually. There is no separate "team" grouping yet — the rep is the unit.
- **Payment Date = purchase date.**

---

## Current numbers (2026, from `artha.py` — 2026-05-30)

- **Total: INR 3.13 Cr** (₹31,252,867) across **715 sales**, avg deal ₹43,710
- **Top reps:** Kiran ₹75.8L (133) · Sunil ₹52.3L (246) · Anjali ₹29.9L (33) · Gayatri ₹22.0L · Bhavya ₹20.8L
- **By region:** India ₹2.63 Cr (674) · Middle East ₹31.6L (24) · SE Asia ₹15.9L (15) · US ₹2.0L (1)
- **Desi (SE Asia/Indonesia):** ₹12.8L across 11 sales on the main sheet

> Re-run `artha.py` for live figures — these are a snapshot.

---

## ⚠️ Data-quality issues (fix for accuracy)

1. **Rep name fragmentation** — the sheet spells the same person many ways, splitting their total.
   `artha.py` normalizes via `NAME_MAP`. Already merged: **Kiran = Kiran + K Kiran** (133 sales, was hidden),
   Hitangi = Hitangi Arora, Muneera = Muneera tabassum, Ayushh = AYUSHH/ayushh/Ayushh kumar.
   **Still ambiguous — confirm with Dhruv:** is **"Amit" the same person as "Amit Kumar"**? (kept separate for now)
2. **Desi reconciliation mismatch** — her IDR debit file shows ~₹3.75L collected (Rp70.28M), but the main
   sheet attributes ₹12.8L to "Desi". Gap = deals she sourced but the customer paid Onsite directly (INR),
   vs deals she collected in IDR to her BCA. These are two different books — reconcile before trusting either alone.

---

## Desi's compensation model (Indonesia / SE Asia)

Desi Yulia handles Indonesian clients. She collects payment in **IDR** to her BCA account, then:
- **10% commission** on every sale she collects (e.g. Rp70.28M collected → Rp7.03M commission)
- **Salary: 3,000,000 IDR/month ≈ ₹16,000 INR/month** (we standardize to INR)
- **Sends the rest to Onsite:** `net = collected − commission − salary`

**Currency standard:** our books are in **INR**. The main sheet's Desi amounts are already INR.
Her debit file is in IDR. Rate from her own sheet: 15,225,000 IDR = 867.79 USD (≈17,544 IDR/USD);
her 3M IDR salary ≈ ₹16k → ~187.5 IDR/INR. **Confirm the standard rate with Dhruv** (`IDR_PER_INR` in artha.py).

---

## What Artha answers today (no extra build)

✅ Total / period revenue · by rep · by region · by plan · by month · per-rep deal list · Desi reconciliation.
All from the two sheets, deterministically.

## What needs one input from Dhruv before it works

- **Teams** — right now the unit is the individual rep (Dhruv confirmed "deal owner = teams" → each
  salesperson is their own line). If reps later group into named teams, add a `rep → team` map.
- **Targets / quotas** — none in the data yet. Supply per-rep monthly goals → Artha can show % attainment.
- **Invoices paid/unpaid** — sheet has invoice numbers but not payment status. To answer "what's
  outstanding", need a paid/unpaid source (or add a status column).
- **CRM (future)** — Dhruv: "later CRM here, the measure things will be for Desi." When the live CRM
  feeds in, Artha points at it instead of/in addition to the CSV.

---

## TODO (remaining work)

- [ ] Confirm: is **"Amit" = "Amit Kumar"**? (and any other split names) → update `NAME_MAP`
- [ ] Confirm the **IDR→INR standard rate** → set `IDR_PER_INR` in artha.py
- [ ] **Reconcile Desi:** match her IDR debit file line-by-line against her main-sheet rows; explain the ₹3.75L vs ₹12.8L gap
- [ ] Decide **teams**: stay per-rep, or add a rep→team grouping map
- [ ] Add **targets** per rep (if they exist) → quota-attainment view
- [ ] Add **invoice paid/unpaid** source → "what's outstanding" view
- [ ] Optional: auto-refresh from the live Google Sheet instead of manual CSV drop
- [ ] Optional: weekly revenue digest to Sumit (reuse Task AI supervisor pattern)

---

## Structure (one place, as Dhruv asked)

```
Onsite/finance-agent/
├── CLAUDE.md          ← this — Artha's context (read first)
├── artha.py           ← deterministic query tool (all numbers come from here)
└── data/
    ├── sales_2026.csv            (main)
    ├── sales_all_history.csv     (all-time)
    └── desi_debit_to_onsite.csv  (Desi's IDR book)
```

**No separate bot.** Artha is this folder. Drop new sheet exports into `data/`, run `artha.py`, ask Claude. When the data grows or CRM connects, this is where it plugs in.

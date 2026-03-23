---
name: onsite-data-analytics
description: CSV and data analysis for Onsite — field bible, date parsing, revenue parsing, report patterns. Use when working with Zoho exports, Last_Touched_Query CSV, or building reports.
---

# Onsite Data Analytics — CSV Bible

## Source

- **File:** `Last_Touched_Query (3).csv` (or equivalent Zoho export). ~300K rows, 85 columns. Encoding UTF-8 with BOM.

---

## Date Parsing (Critical)

Zoho uses multiple formats. Try all:

```python
def parse_date(d):
    if not d or not d.strip(): return None
    for fmt in ["%b %d, %Y %I:%M %p", "%d %b, %Y %H:%M:%S",
                "%d %b, %Y", "%b %d, %Y", "%Y-%m-%d", "%d-%b-%Y"]:
        try: return datetime.strptime(d.strip(), fmt)
        except: continue
    return None
```

| Field | Use for |
|-------|---------|
| `lead_assigned_time` | When lead assigned |
| `demo_date` | When demo happened |
| `sale_done_date` | **Revenue attribution — use this** |
| `lead_source_date` | When lead entered |
| `last_touched_date` | Last activity (not `last_touched_date_new`) |

---

## Revenue (Danger Zone)

| Field | Meaning | Use? |
|-------|---------|------|
| `annual_revenue` | Money in Rs. | **Yes** — strip "Rs." |
| `Revenue` | Score 10/20/50 | **Never** for money |
| `price_pitched` | Quoted | Pipeline only |

```python
def parse_revenue(val):
    if not val: return 0
    val = val.replace("Rs.", "").replace("₹", "").replace(",", "").strip()
    try: return float(val)
    except: return 0
```

---

## People & Source

- Rep: `deal_owner`. Pre-sales: `pre_sales_person` (Jyoti/Shruti/Chadni). Lead: `lead_name`, `Lead_email` (capital L), `lead_phone`. Campaign: `campaign_name`, `Adset_name`, `ad_name`, `lead_source`.

---

## Report Patterns

- **Monthly revenue:** Filter `sale_done_date` in month, sum `annual_revenue`.
- **By rep:** Group by `deal_owner`, same date/revenue rules.
- **By source:** Group by `lead_source` or `campaign_name`, attribute by `sale_done_date`.

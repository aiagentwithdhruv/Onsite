---
name: onsite-sales
description: Sales analysis for Onsite — reps, pipeline, demos, revenue, deal tracking. Use when analyzing sales data, rep performance, pipeline, or Zoho/CRM exports.
---

# Onsite Sales Analysis

## CSV Fields (Critical)

| Use | Field | Notes |
|-----|-------|--------|
| Revenue (money) | `annual_revenue` | Has "Rs." prefix — parse it. **Only** field for revenue. |
| Revenue score | `Revenue` | **Never** use for money — it's 10/20/50 score. |
| Rep | `deal_owner` | Full name as in CSV. |
| Demo date | `demo_date` | When demo happened. |
| Sale date | `sale_done_date` | **Use for revenue attribution.** |
| Quoted price | `price_pitched` | Pipeline only. |
| Stage | `sales_stage`, `lead_status` | Pipeline state. |

**Deal owners (exact):** Anjali Bajaj, Sunil Demo, Bhavya Pattegudde Janappa, Mohan C, Gayatri Surlkar, Shailendra Gour, Amit Balasaheb Udagatti, Hitangi, Amit Kumar, Desi Yulia.

**Revenue parsing:**
```python
def parse_revenue(val):
    if not val: return 0
    val = val.replace("Rs.", "").replace("₹", "").replace(",", "").strip()
    try: return float(val)
    except: return 0
```

---

## Analysis Patterns

1. **Rep scorecard (per month):** Demos = count where `demo_date` in month and `deal_owner` = rep. Sales = count where `sale_done_date` in month. Revenue = sum `annual_revenue` for those sales.
2. **Pipeline:** Group by `lead_status` for leads with no `sale_done_date`. Hot = demo done, no sale, good company.
3. **Attribution:** Revenue always by `sale_done_date` month and rep, not by demo or lead-assign date.

---

## Key Metrics (Feb 2026 Ref)

- ~10 reps, ~304 demos, 42 sales, 14% conversion, ~Rs.76K avg deal.
- Revenue ~Rs.31.9L/month (flat Rs.25–35L band). Growth levers: trial revival, pipeline revival, Google Ads call-through, conversion 14%→18%.

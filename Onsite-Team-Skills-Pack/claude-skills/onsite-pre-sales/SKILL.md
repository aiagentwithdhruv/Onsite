---
name: onsite-pre-sales
description: Pre-sales analysis for Onsite — demo booking, Jyoti/Shruti/Chadni, ME capacity, lead qualification. Use when discussing pre-sales workload or ME assignment.
---

# Onsite Pre-Sales Analysis

## CSV Fields

| Field | Column | Notes |
|-------|--------|--------|
| Pre-sales person | `pre_sales_person` | "Jyoti", "Shruti", "Chadni", or blank (direct) |
| Demo date | `demo_date` | When demo was booked/done |
| Lead assigned time | `lead_assigned_time` | When lead given to pre-sales |
| Pre-qualification | `pre_qualification` | 1=VHP, 2=HP, 3=Medium, 4=Low |

---

## Analysis Patterns

1. **Pre-sales workload:** Per `pre_sales_person` per month: demos booked (where they set and demo_date in month), split ME vs India if needed. Demos per working day = total/22.
2. **ME capacity:** Track ME demos by person; flag single-point failure if only one does ME.
3. **Callable pool (e.g. ME churn):** Filter ME + lead_status in [NATC, User not attend session, DTA, Priority, Follow Up], no demo_date, no sale_done_date, not rejected/junk. Sort: no-shows first, then Follow Up, Priority, NATC, DTA.
4. **Pre-sales × rep:** Cross-tab `pre_sales_person` × `deal_owner`, count demos — shows who feeds whom.

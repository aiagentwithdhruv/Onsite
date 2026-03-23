---
name: onsite-marketing
description: Marketing analysis for Onsite — campaigns, ads, lead sources, CAC, channel ROI. Use when analyzing ad performance, lead sources, or campaign attribution.
---

# Onsite Marketing Analysis

## CSV Fields

| Field | Column | Notes |
|-------|--------|--------|
| Campaign | `campaign_name` | FB campaign. |
| Adset | `Adset_name` | Capital A. |
| Ad | `ad_name` | Creative name. |
| Lead source | `lead_source` | Channel. |
| Lead source type | `lead_source_type` | Category. |

**Attribution:** Revenue = `sale_done_date` month + campaign/source of that lead. **Never** attribute revenue to lead-assign or demo month.

**Lead source examples:** Facebook Instaform, 2. Website, 4. Customer Support WA, 9. Outbound, 25. Google AD, 10. Instagram Ad, 8. Client Referral, BNI Data, 26. Linkedin Database, 6. Gallabox, 33. Email Campaign.

---

## Analysis Patterns

1. **Campaign performance (per month):** Leads = count where `lead_assigned_time` in month and campaign matches. Demos = those with `demo_date`. Sales = count where `sale_done_date` in month and campaign matches. Revenue = sum `annual_revenue` for those.
2. **Channel ROI:** Revenue per lead source; use `sale_done_date` for revenue attribution.
3. **Creative:** Map `ad_name` to revenue to see which creatives drive sales.

---

## Benchmarks

- Website conversion ~39% (high intent). Google AD short cycle. Demo→sale 14% (target 18%+). Support WA 26% demo→sale (strong).

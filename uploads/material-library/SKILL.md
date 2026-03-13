# Material Library Upload — Skill Doc

> Convert any material master/procurement list to Onsite Material Library upload format

---

## Onsite Upload Format

**Template:** `templates/Material  library upload (new)-template.csv`

| Column | Required | Notes |
|--------|----------|-------|
| material name | Yes | Unique name, no duplicates |
| Unit | Yes | Must match Onsite valid units |
| category | No | e.g., Electrical, Civil, Structural, Tools, Consumables, Safety Items |
| description | No | Specs, brands, remarks — good for searchability |
| hsn code | No | HSN/SAC code for GST |
| gst | No | Integer percent (18, 5, 28) — NOT decimal (0.18) |

---

## Valid Units (Onsite Material Library)

nos, meter, RMT, sqm, sqft, cum, cft, kg, tonne, points, lumpsum, bags, each, pcs, set, pair, Bundle, Litre, roll, box, trip, lot

---

## Unit Mapping (Common Source → Onsite)

| Source | Onsite |
|--------|--------|
| Mtr, Mtrs, mtr | meter |
| Nos, NOS, Nos., No., No | nos |
| KG, Kg, Kg., kg | kg |
| LTR, Ltr | Litre |
| Pkt | nos |
| PICS, pcs, Pcs | pcs |
| BUNDLE, Bundle | Bundle |
| Beg, Bags | bags |
| Sqr-ft, Sq.ft, SFT | sqft |
| CFT / Cum, Cum | cum |
| LS, Lumpsum | lumpsum |
| Rmt, RMT | RMT |
| Sqft, SQFT | sqft |

---

## GST Conversion

- If source stores as decimal (0.18, 0.05, 0.28) → multiply by 100 → 18, 5, 28
- If source stores as integer (18, 5, 28) → use as-is
- Common: Electrical = 18%, Civil = 5-28%, Safety = 18%

---

## Converter Checklist

1. Read source file (xlsx/csv)
2. Map headers to: material name, Unit, category, description, hsn code, gst
3. Fix units using mapping table above
4. Convert GST decimal → integer
5. Deduplicate names (append item code if duplicate)
6. Skip empty/header-only rows
7. Build description from specs + brands + remarks
8. Validate: no duplicate names, all units valid
9. Output CSV with exact 6-column header

---

## Fixes Completed

| # | Date | Source File | Items | Notes |
|---|------|------------|-------|-------|
| 1 | 2026-03-13 | Material_Procurement_System.xlsx | 173 | 6 categories, 14 unit types mapped, brands in description |

---

## Patterns Learned

1. GST stored as decimal (0.18) — common in Excel templates
2. "PICS" = pcs (typo variant)
3. "Beg" = bags (Hindi-influenced)
4. "CFT / Cum" = cum (dual unit notation)
5. "Sqr-ft" = sqft (hyphenated variant)
6. Consumable category rows sometimes have no unit/GST — skip or default
7. Brands stored in 3 separate columns — concatenate into description
8. Item codes like MAT-001, ELE-01, STR-01, TOOL-01 — useful for dedup

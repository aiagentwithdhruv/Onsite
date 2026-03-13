# Material Library — Error Log (Self-Learning)

> Every time a material file is converted, append what was wrong and how it was fixed.

---

## 2026-03-13 — Material_Procurement_System.xlsx
**Source:** Anjali Bajaj (Onsite Official) — forwarded from client
**Items:** 173 materials (175 total, 2 skipped — consumable headers)
**Categories:** Electrical (63), Structural (56), Civil (24), Tools (20), Safety Items (10)
**Issues found:**
- Issue: GST stored as decimal (0.18) → Fix: Multiply by 100 → 18
- Issue: 14 unit variants (Mtr, NOS, Nos., KG, LTR, PICS, Pkt, Beg, Sqr-ft, CFT/Cum, BUNDLE) → Fix: Mapped all to Onsite valid units
- Issue: Brands in 3 separate columns (Brand 1/2/3) → Fix: Concatenated into description field
- Issue: 2 consumable rows had no unit or GST → Fix: Skipped (category headers, not materials)
- Issue: Extra spaces in names ("Wire 4 sq mm  Yellow") → Fix: Collapsed whitespace
**Result:** Material_Library_FIXED.csv (173 items, 0 errors)

---

## Patterns Learned

| # | Pattern | Fix |
|---|---------|-----|
| 1 | GST as decimal (0.18, 0.05, 0.28) | ×100 → integer |
| 2 | PICS = pcs | typo variant |
| 3 | Beg = bags | Hindi-influenced |
| 4 | CFT / Cum = cum | dual unit notation |
| 5 | Sqr-ft = sqft | hyphenated variant |
| 6 | Consumable headers (no unit/GST) | skip row |
| 7 | Multiple brand columns | concatenate to description |
| 8 | Item codes (MAT-001, ELE-01, STR-01) | use for dedup |

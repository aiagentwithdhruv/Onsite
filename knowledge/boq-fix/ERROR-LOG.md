# BOQ Fix — Error Log (Self-Learning)

> Every time a file is fixed, append what was wrong and how it was fixed.
> This file grows over time — the skill gets smarter with every fix.

---

## How to Read This Log

Each entry follows this format:
```
## [Date] — [Original Filename]
**Type:** BOQ / Rate Library / Material Stock / Quotation
**Issues found:**
- Issue: [what was wrong] → Fix: [how fixed]
**New pattern:** [if any new issue type discovered, also add to SKILL.md]
```

---

## Historical Fixes (Pre-Skill, from Jan 2026 BOQ work)

### 2026-01-22 — BOQ_HVAC (HVAC Bill of Quantities)
**Type:** BOQ
**Issues found:**
- Issue: Raw Excel export had no hierarchical numbering → Fix: Applied 3-level numbering (1 → 1.1 → 1.1.1)
- Issue: Long descriptions with commas not quoted → Fix: Wrapped in double quotes
- Issue: Units inconsistent (No., Nos, Rmt mixed) → Fix: Standardized to Nos., Rm
- Issue: Zero prices left as `0` → Fix: Kept as `0` (valid — means "to be quoted")
**Result:** BOQ_HVAC_Formatted.csv, BOQ_HVAC_Formatted_2.csv

### 2026-01-22 — Trial BOQ GDC (Government FHTC Project)
**Type:** BOQ
**Issues found:**
- Issue: Original had `Type` column instead of `Serial no.` → Fix: Renamed column
- Issue: Cost code column had sub-item letters (a, b, c) instead of codes → Fix: Moved letters to description, left cost code for actual codes
- Issue: 3 iterations needed (FORMATTED → FIXED → CLEAN) → Fix: Each pass caught more issues
- Issue: Sub-items used sequential numbers (1, 2, 3) under each section instead of hierarchical → Fix: Converted to 5.1, 5.2, 5.3 format
**New pattern:** Government project BOQs often use `Type` column header instead of `Serial no.`
**Result:** Trial_BOQ_GDC_CLEAN.csv

### 2026-01-22 — say_infra Rate Library
**Type:** Rate Library
**Issues found:**
- Issue: Prices had leading spaces and currency formatting ("  310.00 ") → Fix: Trimmed and stripped formatting
- Issue: Column order didn't match spec → Fix: Reordered to Item Name, Item Code, Unit, Sales Price, SAC, Description, Cost Code
- Issue: 2 iterations needed (CORRECTED → FIXED) → Fix: Second pass caught spacing issues
**New pattern:** Rate libraries from field teams often have invisible whitespace in price columns
**Result:** say_infra_Rate_Library_FIXED.csv

### 2026-01-22 — brandshell Material Stock
**Type:** Material Stock
**Issues found:**
- Issue: Duplicate entries (same item, multiple rows) → Fix: Deduplicated, keeping latest/highest quantity
- Issue: 3 iterations needed (UPDATED → UPDATED_3 → DEDUPLICATED) → Fix: Progressive cleanup
**New pattern:** Material stock exports from ERP often contain duplicates from multiple warehouse entries
**Result:** brandshell-material-DEDUPLICATED.csv

### 2026-01-22 — antony BOQ Final
**Type:** BOQ
**Issues found:**
- Issue: Large file (119KB, many items) → Fix: Processed in full, maintained hierarchy
- Issue: "Sheet 1" in filename indicated raw Google Sheets export → Fix: Cleaned headers
**New pattern:** Files named "Sheet 1" or "Sheet1" are raw exports, always need full cleanup

### 2026-01-21 — Test-BOQ Standardization
**Type:** BOQ
**Issues found:**
- Issue: Alphabetic section numbering (A, B, C) → Fix: Converted to numeric (1, 2, 3)
- Issue: Numbers reset in each section → Fix: Applied hierarchical numbering
- Issue: No clear parent relationships → Fix: Created 3-level hierarchy
- Issue: Limited columns → Fix: Expanded to full 10-column BOQ spec
- Issue: No standard format → Fix: Applied industry-standard BOQ format
**New pattern:** Many BOQs use A/B/C lettering for main sections — always convert to numeric
**Result:** Test-BOQ-Standardized.csv (see BOQ_Standardization_Report.txt for full details)

---

## Patterns Learned So Far

1. **Government project BOQs** use `Type` column, not `Serial no.`
2. **Rate libraries from field teams** have invisible whitespace in prices
3. **Material stock exports** from ERP contain duplicate entries
4. **Files named "Sheet 1"** are raw exports needing full cleanup
5. **A/B/C lettering** in main sections must be converted to 1/2/3
6. **Most files need 2-3 passes** — first pass catches structure, second catches data quality
7. **Zero prices are valid** — means "to be quoted" not "error"
8. **Commas inside descriptions** break CSV — always quote fields with commas
9. **Indian number format** (1,50,000) must be converted to standard (150000)
10. **HSN 9954** is the default for construction services

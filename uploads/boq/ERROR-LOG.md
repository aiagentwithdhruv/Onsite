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

## 2026-03-01 — Bhuj Airport BOQ (1).csv
**Type:** BOQ
**Client:** Airport construction project (Bhuj)
**Error message:** `Error convert unitSalePrice_float64 : row not valid 0`
**Issues found:**
- Issue: 23 parent/section header rows had space character ` ` in Unit Sale Price column (not empty, a literal space) → Fix: `row[6].strip()` on all rows
- Issue: 169 rows had non-standard unit names (Cum, Sqm, Kg, Quintal, Each, Nos, Meter, Liters, mtr, point, sq.mtr, Job, JOB, Set) → Fix: Applied UNIT_MAP conversion to valid Onsite units
**New patterns:**
- **Space ≠ empty in CSV**: A single space character in a numeric column causes float64 parse failure. Always `.strip()` ALL numeric columns.
- **Airport/infrastructure BOQs** use engineering unit abbreviations (Cum for cum, Sqm for sqm) — capitalize differently than Onsite expects
- **"Job" and "JOB"** should map to `nos` (it's a unit of work counted as individual items)
**Result:** Bhuj_Airport_BOQ_FIXED.csv (245 data rows, 23 spaces fixed, 169 units standardized)

---

## 2026-03-01 — road_project_boq (1).csv
**Type:** BOQ
**Client:** Road construction project
**Error message:** `Unit not found in onsite database ls, no, rm, month, ha, mt`
**Issues found:**
- Issue: 9 column headers completely wrong (Type→Serial Number, Description→Item Name, Code→Item code, Unit→unit, Tax Percentage→GST Percent, Quantity→Estimated Quantity, Rate→Unit Sale Price, SAC/HSN→HSN Code, Narration→Notes) → Fix: Full header rename
- Issue: 207 rows had invalid units (LS, No, Rm, Month, Ha, MT, Km) → Fix: Unit mapping (LS→lumpsum, No→nos, Rm→RMT, Month→Monthly, Ha→sqm, MT→tonne, Km→km)
- Issue: 1 row had `Ha` (hectare) unit which doesn't exist in Onsite → Fix: Converted to sqm with qty×10000, price÷10000 (1 Ha = 10,000 sqm)
**New patterns:**
- **Road project BOQs** use different column naming convention (Type, Description, Code, Narration)
- **"Ha" (hectare)** must be converted to sqm with quantity/price adjustment (×10000/÷10000)
- **"Month"** maps to `Monthly` (capital M, Onsite's time-based unit)
- **"No"** (singular) is common in road BOQs — maps to `nos`
- **"LS"** (Lump Sum) very common in road/civil BOQs — maps to `lumpsum`
- **9 wrong headers** = the entire file used accounting/ERP column names, not Onsite names
**Result:** Road_Project_BOQ_FIXED.csv (272 data rows, 9 headers fixed, 207 units standardized)

---

## 2026-03-01 — Final BOQ.csv
**Type:** BOQ
**Client:** Pradeep Pancholi Business Plus (Yogyata Onsite Team WhatsApp group)
**Error message:** `Error convert strIndex_int64 : row not valid 1`
**Issues found:**
- Issue: ALL serial numbers were text-based codes (EX.1, EX.1A, EX.1B, CON.1, CON.11, FIN.1, etc.) instead of numeric → Fix: Converted to numeric hierarchy — parent rows (no unit/qty) become section numbers (1, 2, 3...), child rows become items (1.01, 1.02, 2.01...)
- Issue: 8 column headers wrong (Sr.No→Serial Number, Item Description→Item Name, Unit→unit, GST %→GST Percent, Qty→Estimated Quantity, Rate→Unit Sale Price, HSN/SAC→HSN Code, Remarks→Notes) → Fix: Header rename
- Issue: 59 rows had invalid units (rmt→RMT, lump sum→lumpsum) → Fix: Unit standardization
- Issue: 3 rows had commas in quantities (3,604.00 → 3604.00) → Fix: Strip commas from all numeric fields
**New patterns:**
- **Text-code serial numbers** (EX.1, CON.11, FIN.1) are a NEW error type — caused `strIndex_int64` error. Different from letter-only (a, b, c) or A/B/C section errors.
- **Conversion logic for text codes:** Detect parent rows (rows with no unit, quantity, or price) → assign section numbers sequentially. Detect child rows → assign item numbers under their parent section.
- **"lump sum" (two words)** must become `lumpsum` (one word)
- **Commas in Indian quantity format** (3,604.00) must be stripped — not just prices but quantities too
- **"Sr.No"** is another header variant for Serial Number (in addition to "Type" from govt BOQs)
- **Client BOQs from WhatsApp** often have multiple simultaneous issues (headers + serials + units + number formatting)
**Result:** Final_BOQ_FIXED.csv (214 data rows, serial numbers rebuilt, 8 headers fixed, 59 units standardized, 3 quantity commas removed)

---

## 2026-03-02 — Final BOQ.csv (v2 fix — trailing zero issue)
**Type:** BOQ
**Client:** Pradeep Pancholi Business Plus (same file, client feedback)
**Error message:** (no upload error — DISPLAY issue) `3.10` showing as `3.1` in Onsite UI
**Client feedback (WhatsApp):** "Isme na 3.9 ke baar 3.1 aa rha instead of 3.10. Ye bahut common issue h AI se pahle bi aa rha tha."
**Root cause:** v1 fix used flat 2-level numbering (X.01, X.02, ..., X.10). Onsite strips trailing zeros from decimal serial numbers, so `3.10` displays as `3.1`.
**Why it happened:** Original text-code BOQ (EX.1, CON.11, etc.) has natural sub-grouping, but v1 fix lumped all items under a single parent → sections had 10+ items → `.10` appeared.
**Fix (v2):**
1. Parsed original text codes to identify prefix groups (EX, CON, FW, RF, SS, WAL, WF, FLR, WPR, RD, WS, MIS)
2. Created proper 3-level hierarchy: Section (prefix) → Sub-section (number group) → Item (suffix)
3. Implemented `skip_serial()` function to skip multiples of 10 at every decimal level
4. Sequence: 1, 2, ..., 9, 11, 12, ... (skips 10, 20, 30, etc.)
**Stats:**
- 12 sections, 81 sub-sections, 133 items (226 total rows)
- 0 trailing zero issues
- 0 duplicate serials, 0 missing parents, 0 invalid units
- Max children per parent: 9 (down from 97 in v1!)
**New patterns:**
- **Onsite strips trailing zeros** from decimal serial numbers. `X.10` → `X.1`, `X.20` → `X.2`. This is a platform behavior, NOT an upload error.
- **Always parse original BOQ code prefixes** to create proper sub-grouping — don't flatten into 2 levels
- **Skip multiples of 10** at every decimal level to avoid display confusion
- **3-level hierarchy** is safer than 2-level for BOQs with many items per section
- **Max 9 children per parent** should be the target to completely avoid trailing zero issues
**Result:** Final_BOQ_FIXED.csv v2 (226 rows, 12 sections, all checks passed)

---

## 2026-03-10 — Sample BOQ (Electrical Works, MAX SQUARE II, Noida)
**Type:** BOQ (Tender — no rates)
**Source:** Sample BOQ.xlsx (Sheet: BOQ, 1608 rows)
**Issues found:**
- Issue: .xlsx format with 2 sheets (summary + BOQ data) → Fix: openpyxl to read, use summary references for section boundaries
- Issue: 12 sections labeled A-L with letter-based serial numbering → Fix: Map A=1, B=2... L=13 (skip 10)
- Issue: Floating-point serial numbers (1.2000000000000002) → Fix: round(sno, 4) + strip trailing zeros
- Issue: Per-section numbering resets (each section starts from 1) → Fix: Global renumber under section parents
- Issue: Units Pt/Pt.→points, RM→RMT, No.→nos, Set→set → Fix: Unit mapping
- Issue: "RO"/"R.O" in quantity field (Rate Only) → Fix: Leave qty blank
- Issue: 1285 spec/note rows (roman numerals, sub-descriptions) without unit/qty → Fix: Used as sub-group parents where they match item grouping
- Issue: No rate/price columns (tender document) → Fix: Leave Unit Sale Price empty, still valid for Onsite
- Issue: 4 columns only (S.NO, Description, Unit, Qty) vs Onsite's 10 → Fix: Pad remaining columns with defaults
**New patterns:** Floating-point serials, tender BOQ (no rates), section-letter mapping, .xlsx multi-sheet, "RO" qty, "Pt" unit
**Result:** Sample_BOQ_FIXED.csv (373 rows: 12 sections + 38 sub-groups + 323 items, all checks passed)

---

## 2026-03-10 — BoM (AirForce, Elevator + Civil works)
**Type:** BoM → BOQ conversion
**Source:** BoM.xlsx (Sheet1, 15 items)
**Issues found:**
- Issue: BoM format (Item Name + Description as separate columns) ≠ BOQ format → Fix: Use Description as Item Name, short name as Notes
- Issue: Excel interpreted "1:4:8" and "1:1:2" as datetime.time objects → Fix: Convert time back to string
- Issue: Units CUM→cum, KG→kg, SQM→sqm, RM→RMT → Fix: Unit mapping
- Issue: No serial number hierarchy (flat 1-15) → Fix: Created parent "AirForce" + children 1.1-1.16
- Issue: No HSN codes → Fix: Added default 9954
- Issue: GST only in summary row formula (18%) → Fix: Applied 18% to all items
**Result:** BoM_BOQ_FIXED.csv (16 rows: 1 parent + 15 items, all checks passed)

---

## 2026-03-02 — Skyfall Final BOQ of Bachelor Hostel - Jaisalmer
**Type:** BOQ
**Client:** Skyfall project (via Sunil Onsite Teams)
**Error message:** `Unit not found in onsite database tonn, rm, ppoint, no, pmeter, per job, metre`
**Issues found:**
- Issue: 6 headers wrong (SERIAL NO.→Serial Number, ITEM→Item Name, Qty→Estimated Quantity, Sale price→Unit Sale Price, HSN code→HSN Code, Cost code→Cost Code, Description→Notes) → Fix: Header rename
- Issue: 12 distinct invalid units across 377 rows (Tonn→tonne, Rm→RMT, PPoint→points, No→nos, Pmeter→meter, Per Job→lumpsum, Rmt→RMT, Metre→meter, Cum→cum, Sqm→sqm, Kg→kg, Nos→nos) → Fix: Unit mapping
- Issue: 15 trailing zero serials across 4 hierarchy levels (10.10, 10.10.1, 10.10.1.1, 19.10, 19.20, 20.10, 20.10.1-4, 41.3.10, 41.4.10, 41.10, 41.10.1-2) → Fix: Full renumber skipping multiples of 10 at all levels
- Issue: 377 rows missing HSN code → Fix: Added default 9954
- Issue: 4-level hierarchy (e.g., 10.10.1.1) not handled by previous fix scripts → Fix: Extended renumber function to support levels 1-4
**New patterns:**
- **"PPoint"** = "Per Point" (electrical wiring) — maps to `points`
- **"Pmeter"** = "Per meter" — maps to `meter`
- **"Per Job"** — maps to `lumpsum` (different from "Job" which maps to `nos`)
- **"Tonn"** (misspelling) — maps to `tonne`
- **"Metre"** (British spelling) — maps to `meter`
- **4-level hierarchies** exist in large BOQs (civil + electrical + HVAC combined) — renumber function MUST handle levels 1-4
- **"SERIAL NO."** (with period) is another header variant for Serial Number
- **"Sale price"** (lowercase p) is another header variant for Unit Sale Price
- **Large BOQs (377+ rows)** often have multiple sections hitting .10/.20 — always renumber ALL serials proactively
**Result:** Skyfall_Final_BOQ_FIXED.csv (377 data rows, 6 headers fixed, 12 unit types mapped, 15 trailing zeros fixed, 377 HSN codes added, all checks passed)

---

## 2026-03-12 — Breakup for ERP ONSITER1.xlsx
**Type:** BOQ (ERP Breakup → Onsite BOQ conversion)
**Client:** Subrata Singha / Shailendra (Onsite official)
**Source:** 3-sheet Excel (Information + Project-1 + Project-2), 343 rows each project
**Issues found:**
- Issue: ERP format has separate Sale QTY/Rate (main items) and Purchase QTY/Rate (sub-items) → Fix: Map Sale data to main items, Purchase data to sub-items
- Issue: Units Nos→nos, Mtr.→meter, No.→nos, Pkt→nos, Mtrs→meter, Kg.→kg, Each→each → Fix: Unit mapping
- Issue: "Total of Item" summary rows mixed with data → Fix: Filter out rows containing "Total of Item" or "PROJECT"
- Issue: Formula cells (starting with "=") in quantity/rate columns → Fix: Return empty string for unresolved formulas
- Issue: No hierarchical structure (flat main + sub numbering like 1, 1.1, 1.2...) → Fix: Created 3-level hierarchy (1 project parent → 1.1-1.7 main items → 1.1.1-1.1.N materials)
- Issue: Sub-item serial .10 would cause trailing zero display → Fix: Skip multiples of 10 in sub-numbering
- Issue: Make/brand info (KEI, AKG, ABB, Polycab, Legrand, etc.) needed preservation → Fix: Added as "Make: X" in Notes column
**New patterns:**
- **ERP Breakup files** have dual pricing: Sale (for client billing) vs Purchase (for material costing). Main items use Sale, breakup sub-items use Purchase
- **"Pkt"** (Packet) maps to `nos` — used for consumables like PVC sleeves
- **"Mtrs"** (plural of Mtr) maps to `meter`
- **"Kg."** (with period) maps to `kg`
- **Multi-project sheets** in same workbook — generate separate output CSV per project
- **Make/brand data** should go in Notes column (not lost)
**Result:** ERP_Breakup_Project_1_BOQ.csv + ERP_Breakup_Project_2_BOQ.csv (57 rows each: 1 parent + 7 main + 49 breakup, all checks passed)

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
11. **Space ≠ empty in CSV** — a single space in numeric columns (Unit Sale Price, Quantity) causes float64 parse failure. Always `.strip()` ALL numeric columns.
12. **Airport/infrastructure BOQs** use engineering abbreviations (Cum, Sqm, Kg) — different case than Onsite expects
13. **Road project BOQs** use entirely different column names (Type, Description, Code, Narration, Rate)
14. **"Ha" (hectare)** doesn't exist in Onsite — convert to sqm with qty×10000, price÷10000
15. **Text-code serial numbers** (EX.1, CON.11, FIN.1) are a distinct error type from letter-only (a, b, c). Requires parent/child detection + sequential numbering.
16. **"lump sum" (two words)** and **"Lump Sum"** must become `lumpsum` (one word, lowercase)
17. **Client BOQs from WhatsApp** typically have 3-4 simultaneous issues (headers + serials + units + number formatting)
18. **"Sr.No"** is another common header variant for Serial Number
19. **"Job"/"JOB"** units should map to `nos`
20. **"Month"** maps to `Monthly` (capital M) in Onsite
21. **Always strip commas from BOTH quantities AND prices** — Indian format commas appear in both
22. **Onsite strips trailing zeros** from decimal serial numbers: `X.10` → `X.1`. This is a DISPLAY issue, not an upload error, but causes client confusion.
23. **Skip multiples of 10** in serial number sub-levels to avoid trailing zero display: .9 → .11 (skip .10)
24. **Parse original text-code prefixes** (EX, CON, FW, etc.) to create proper 3-level hierarchy — don't flatten
25. **Max 9 children per parent** is the target — prevents `.10` from ever appearing
26. **3-level hierarchy > 2-level** for complex BOQs with many items per section
27. **"PPoint"** (Per Point) maps to `points` — common in electrical BOQs for wiring points
28. **"Pmeter"** (Per meter) maps to `meter` — field shorthand
29. **"Per Job"** maps to `lumpsum` — different from "Job" (which maps to `nos`)
30. **"Tonn"** (misspelling) maps to `tonne` — watch for creative spelling variations
31. **"Metre"** (British) maps to `meter` — British vs American spelling
32. **4-level hierarchies** require renumber function to handle levels 1-4 (large combined BOQs: civil+electrical+HVAC)
33. **"SERIAL NO."** and **"Sale price"** are additional header variants
34. **Large BOQs (300+ rows)** almost always have trailing zero issues — renumber ALL serials proactively, don't just fix the flagged ones
35. **Excel .xlsx BOQs** need `openpyxl` — `pip3 install openpyxl`. Some have 2+ sheets (summary + data)
36. **Floating-point serial numbers** in Excel — `1.2000000000000002` instead of `1.2`. Always `round(sno, 4)` and strip trailing zeros
37. **"Pt" / "Pt."** (Points) maps to `points` — used in electrical wiring BOQs for wiring points
38. **"RO" / "R.O"** in quantity = "Rate Only" — no quantity specified, leave blank for Onsite
39. **Tender BOQs have NO rates** — only S.No, Description, Unit, Qty. Leave Unit Sale Price empty. Still valid for Onsite upload
40. **Section-letter serials** (A., B., C. ... L.) must be mapped to numeric (1, 2, 3... skip 10)
41. **Per-section numbering resets** — many large BOQs restart serial numbers within each section. Must be globally renumbered
42. **Spec/note rows** (roman numerals i, ii, iii... or letters a, b, c without unit/qty) are sub-descriptions, not items — use as sub-group parents or skip
43. **Summary sheets** in Excel reference data rows — use `TOTAL CARRIED TO SUMMARY` markers as section boundaries
44. **BoM (Bill of Materials) ≠ BOQ** — BoM has Item Name + Description as separate cols; combine Description as Item Name, short name as Notes
45. **ERP Breakup files** have dual pricing columns: Sale QTY/Rate (client billing) vs Purchase QTY/Rate (material costing). Main items use Sale data, breakup sub-items use Purchase data
46. **"Pkt"** (Packet) maps to `nos` — used for consumables like PVC sleeves, gutkha
47. **"Mtrs"** (plural of Mtr) maps to `meter` — yet another meter variant
48. **"Kg."** (with period) maps to `kg` — common in formal BOQs
49. **Multi-project workbooks** — same Excel file contains separate project sheets. Generate one CSV per project sheet
50. **Make/brand info** (KEI, Polycab, ABB, Legrand etc.) should be preserved in Notes column as "Make: X"
51. **Formula cells** (starting with "=") in numeric columns should return empty — openpyxl data_only=True doesn't always resolve them

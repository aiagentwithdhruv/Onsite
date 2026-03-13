# BOQ Fix — All Error Scenarios & Solutions

> **Master reference for EVERY possible Onsite upload error.**
> Covers: BOQ, Material Library, Material Stock, Rate Library.
> Updated after every fix. If a new error appears, add it here.

**Last updated:** 2026-03-02
**Total scenarios:** 48+
**Fixes completed:** 10

---

## Quick Lookup: Error Message → Fix

Copy-paste the Onsite error message here to find the fix instantly.

| Error Message | Category | Jump To |
|---|---|---|
| `Error convert strindex_int64 : row not valid N` | Serial Number | [S1](#s1-letter-based-serial-numbers) |
| `Error convert strIndex_int64 : row not valid N` | Serial Number | [S2](#s2-text-code-serial-numbers) |
| `row not valid for serial_number` | Serial Number | [S3](#s3-duplicate-serial-numbers) |
| `Parent Serial Number not valid` | Serial Number | [S4](#s4-missing-parent-hierarchy) |
| `Error convert unitSalePrice_float64 : row not valid N` | Numeric | [N1](#n1-space-in-unit-sale-price) or [N2](#n2-commas-in-price) |
| `Error convert unitSalePrice_float64` | Numeric | [N2](#n2-commas-in-price) |
| `Error convert quantity_float64` | Numeric | [N3](#n3-commas-in-quantity) |
| `Unit not found in onsite database` | Units | [U1](#u1-invalid-unit-names) |
| `Invalid rows found in file` | Missing Fields | [F1](#f1-missing-required-fields) |
| `Material stock already exist for material 'X'` | Stock | [M1](#m1-stock-already-exists) |
| `Material 'X' does not exist in library` | Stock | [M2](#m2-material-not-in-library) |
| `Opening Stock must be >= 0` | Stock | [M3](#m3-negative-stock-value) |
| `Duplicate material name` | Library | [L1](#l1-duplicate-material-name) |
| (Upload fails silently — no error) | File Format | [FF1](#ff1-encoding-issues) |

---

## SECTION 1: Serial Number Errors

### S1: Letter-based serial numbers
**Error:** `Error convert strindex_int64 : row not valid N`
**Cause:** Serial numbers are letters (a, b, c, d) or (A, B, C)
**Seen in:** Test BOQ, Government BOQs
**Fix:** Convert letters to numeric hierarchy — a→2.01, b→2.02, c→2.03 under parent section. A/B/C section headers → 1, 2, 3.
**Status:** SEEN 2x (Jan 2026)

### S2: Text-code serial numbers
**Error:** `Error convert strIndex_int64 : row not valid N`
**Cause:** Serial numbers are text codes like EX.1, EX.1A, CON.11, FIN.1, PLB.3
**Seen in:** Final BOQ (Pradeep Pancholi, Mar 2026)
**Fix:**
1. Detect parent rows (no unit, no quantity, no price)
2. Assign section numbers sequentially: 1, 2, 3...
3. Detect child rows (have unit/quantity/price)
4. Assign items under parent: 1.01, 1.02, 2.01, 2.02...
**Status:** SEEN 1x (Mar 2026)

### S3: Duplicate serial numbers
**Error:** `row not valid for serial_number`
**Cause:** Two or more rows have the same serial number
**Seen in:** BOQ with merged sections
**Fix:** Ensure every serial number is unique. If numbers reset per section, apply hierarchical numbering.
**Status:** SEEN (Jan 2026)

### S4: Missing parent hierarchy
**Error:** `Parent Serial Number not valid`
**Cause:** Child row exists without parent (e.g., 2.1 exists but 2 doesn't, or 2.1.1 without 2.1)
**Seen in:** Various
**Fix:** Insert missing parent rows. Every child must have a valid parent above it.
**Rules:**
- `2.1` requires `2` to exist
- `2.1.1` requires `2.1` to exist
- `1.0.1` is INVALID (parent `1.0` doesn't exist — use `1.1` instead)
**Status:** DOCUMENTED (not directly seen as error)

### S5: Trailing zero display issue (X.10 → X.1)
**Error:** No upload error — but `.10` displays as `.1` in Onsite UI, causing confusion
**Cause:** Onsite strips trailing zeros from decimal serial numbers: `3.10` → `3.1`, `5.20` → `5.2`
**Seen in:** Final BOQ v1 fix (client: Pradeep Pancholi, Mar 2026)
**Client feedback:** "3.9 ke baar 3.1 aa rha instead of 3.10"
**Root cause of too many children:** Flat 2-level numbering (X.01, X.02, ...) lumps unrelated items under one parent. When a section exceeds 9 items, .10 appears.
**Fix (3-part):**
1. **Use original code grouping** — parse prefix-based hierarchy (EX, CON, FW, etc.) to create proper 3-level sections
2. **Skip multiples of 10** — at every decimal level, skip .10, .20, .30, etc. (go .9 → .11 → .12)
3. **Keep max 9 children per parent** — if a group has 10+ items, the 10th gets .11 (skipping .10)
**Skip function:**
```python
def next_num(n):
    n += 1
    while n % 10 == 0:
        n += 1
    return n
# Sequence: 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, ...
```
**Note:** Renumber function MUST support up to 4-level hierarchy (X.Y.Z.W) — seen in Skyfall BOQ (Mar 2026)
**Status:** SEEN 2x, FIXED (Mar 2026 — Final BOQ, Skyfall BOQ)

### S6: Hyphens or slashes in serial numbers
**Error:** `Error convert strindex_int64`
**Cause:** Serial numbers like `1-1`, `1/1`, `2-3`
**Fix:** Replace with dot notation: `1.1`, `2.3`
**Status:** NOT YET SEEN (anticipated)

### S7: Numbers reset per section
**Error:** Upload succeeds but data structure is wrong (items misplaced)
**Cause:** Each section uses 1, 2, 3 again instead of hierarchical 2.1, 2.2, 2.3
**Seen in:** Trial BOQ GDC (Jan 2026)
**Fix:** Apply hierarchical numbering based on section context
**Status:** SEEN 1x

---

## SECTION 2: Numeric Field Errors

### N1: Space in Unit Sale Price
**Error:** `Error convert unitSalePrice_float64 : row not valid 0`
**Cause:** A literal space character ` ` in the Unit Sale Price column (not empty — a space)
**Seen in:** Bhuj Airport BOQ (Mar 2026) — 23 parent rows had spaces
**Fix:** `.strip()` ALL cells in numeric columns (Unit Sale Price, Estimated Quantity, GST Percent)
**Key insight:** Space ≠ empty in CSV. A cell with a space fails float64 parsing.
**Status:** SEEN 1x (Mar 2026)

### N2: Commas in price
**Error:** `Error convert unitSalePrice_float64`
**Cause:** Indian number format with commas: `7,257.97` or `1,50,000`
**Fix:** Strip ALL commas from price column: `7257.97`, `150000`
**Status:** SEEN (multiple times)

### N3: Commas in quantity
**Error:** `Error convert quantity_float64`
**Cause:** Commas in quantity: `3,604.00`, `1,266`
**Seen in:** Final BOQ (Mar 2026)
**Fix:** Strip ALL commas from quantity column
**Status:** SEEN 1x (Mar 2026)

### N4: Currency symbols in price
**Error:** `Error convert unitSalePrice_float64`
**Cause:** `Rs.5000`, `₹5000`, `INR 5000`, `$5000`
**Fix:** Strip currency symbols and text, keep only numbers
**Status:** NOT YET SEEN (anticipated)

### N5: GST as text/percentage
**Error:** `Invalid rows found in file` or silent failure
**Cause:** `18%` or `0.18` instead of `18`
**Fix:** Strip `%` symbol. If decimal < 1, multiply by 100.
**Status:** NOT YET SEEN (anticipated)

### N6: Zero prices (NOT an error)
**Note:** A price of `0` is VALID — means "to be quoted later"
**Do not:** Flag zero prices as errors or remove them
**Status:** CONFIRMED (Jan 2026)

### N7: Negative values
**Error:** Not documented explicitly
**Cause:** Negative quantity or price
**Fix:** Flag for review. May be valid for credit notes but typically an error in BOQ.
**Status:** NOT YET SEEN (anticipated)

---

## SECTION 3: Unit Errors

### U1: Invalid unit names
**Error:** `Unit not found in onsite database ls, no, rm, month, ha, mt`
**Cause:** Units not in Onsite's valid list (case-sensitive!)
**Seen in:** Road Project BOQ, Bhuj Airport BOQ, Final BOQ (all Mar 2026)
**Fix:** Apply unit mapping (see MASTER UNIT MAP below)

### U2: Hectare (Ha) unit
**Error:** `Unit not found in onsite database ha`
**Cause:** `Ha`/`ha` doesn't exist in Onsite
**Seen in:** Road Project BOQ (Mar 2026)
**Fix:** Convert to `sqm` with math adjustment:
- Quantity: multiply by 10,000 (1 Ha = 10,000 sqm)
- Unit Sale Price: divide by 10,000 (to keep total cost same)
**Status:** SEEN 1x (Mar 2026)

### U3: Two-word units
**Error:** `Unit not found in onsite database lump sum`
**Cause:** `lump sum`, `Lump Sum`, `LUMP SUM` (two words)
**Seen in:** Final BOQ (Mar 2026)
**Fix:** Join to `lumpsum` (one word, lowercase)
**Status:** SEEN 1x (Mar 2026)

---

### MASTER UNIT MAP (Comprehensive)

| Invalid Input | Valid Output | Notes |
|---|---|---|
| `Nos`, `NOS`, `Nos.`, `No`, `No.`, `NO` | `nos` | Lowercase, no period |
| `Mtr`, `M`, `mtr`, `MTR` | `meter` | Full spelling |
| `Rm`, `RM`, `rmt`, `Rmt` | `RMT` | Uppercase |
| `Sq m`, `Sq M`, `SQM`, `Sqm` | `sqm` | Lowercase, no space |
| `SQFT`, `Sq ft` | `sqft` | Lowercase, no space |
| `M3`, `cu.m`, `Cum`, `CUM` | `cum` | Lowercase |
| `M2`, `sq.m`, `sq.mtr` | `sqm` | Lowercase |
| `Kg`, `KG`, `kgs` | `kg` | Lowercase, no 's' |
| `L`, `ltr`, `Ltr`, `Liters`, `LITERS`, `liters` | `Litre` | Capital L |
| `LS`, `L.S.`, `ls`, `lump sum`, `Lump Sum`, `LUMP SUM` | `lumpsum` | One word |
| `Ton`, `MT`, `mt` | `tonne` | Full spelling |
| `Boxes`, `Sheets`, `Job`, `JOB`, `job` | `nos` | Use nos |
| `Pieces` | `pcs` | Use pcs |
| `Each`, `EACH` | `each` | Lowercase |
| `Quintal`, `QUINTAL` | `quintal` | Lowercase |
| `Set`, `SET` | `set` | Lowercase |
| `point`, `Point`, `PPoint` | `points` | Plural / "Per Point" |
| `Pmeter` | `meter` | "Per meter" field shorthand |
| `Per Job`, `per job` | `lumpsum` | "Per Job" = lumpsum |
| `Tonn`, `tonn`, `TONN` | `tonne` | Misspelling |
| `Ha`, `ha`, `HA` | `sqm` | qty×10000, price÷10000 |
| `Month`, `month`, `MONTH` | `Monthly` | Capital M |
| `Km`, `KM` | `km` | Lowercase |
| `Acre` | `sqm` | qty×4047, price÷4047 (anticipated) |
| `Feet`, `FEET` | `ft` | Short form (anticipated) |
| `Inch` | `in` | Short form (anticipated) |
| `Metre`, `Metres` | `meter` | Americanize — SEEN in Skyfall BOQ |
| `Litres` | `Litre` | Singular (anticipated) |
| `Bags`, `BAGS` | `bags` | Lowercase (anticipated) |
| `Running Meter`, `R.M.`, `r.m.` | `RMT` | Standard form (anticipated) |
| `Square Meter`, `Sq. Mtr.` | `sqm` | Standard form (anticipated) |
| `Cubic Meter`, `Cu. Mtr.` | `cum` | Standard form (anticipated) |
| `Kilogram`, `Kilograms` | `kg` | Short form (anticipated) |
| `Tonne`, `TONNE` | `tonne` | Lowercase (anticipated) |
| `Numbers`, `NUMBERS` | `numbers` | Lowercase (anticipated) |
| `Pair`, `PAIR` | `pair` | Lowercase (anticipated) |
| `Bundle`, `BUNDLE` | `Bundle` | Capital B — Onsite requires this case! |

---

## SECTION 4: Column Header Errors

### H1: Wrong column headers (Government/Road BOQs)
**Cause:** Government and road project BOQs use ERP/accounting column names
**Seen in:** Road Project BOQ (Mar 2026), Trial BOQ GDC (Jan 2026)
**Fix:** Map headers:

| Source Header | Onsite Header |
|---|---|
| `Type` | `Serial Number` |
| `Description` | `Item Name` |
| `Code` | `Item code` |
| `Unit` | `unit` (case matters!) |
| `Tax Percentage` | `GST Percent` |
| `Quantity` | `Estimated Quantity` |
| `Rate` | `Unit Sale Price` |
| `SAC/HSN` | `HSN Code` |
| `Narration` | `Notes` |

### H2: Wrong column headers (Client BOQs)
**Cause:** Client-generated BOQs with non-standard naming
**Seen in:** Final BOQ (Mar 2026)
**Fix:** Map headers:

| Source Header | Onsite Header |
|---|---|
| `Sr.No` / `Sr. No.` / `S.No` / `Sl.No` / `SERIAL NO.` | `Serial Number` |
| `Item Description` | `Item Name` |
| `GST %` | `GST Percent` |
| `Qty` / `Qty.` | `Estimated Quantity` |
| `Rate` / `Rate (Rs.)` | `Unit Sale Price` |
| `HSN/SAC` | `HSN Code` |
| `Remarks` | `Notes` |

### H3: Missing columns entirely
**Cause:** BOQ has fewer than 10 columns
**Fix:** Add missing columns with defaults:
- `Item code` → empty
- `HSN Code` → `9954` (construction default)
- `Cost Code` → empty
- `Notes` → empty
- `GST Percent` → `18` (construction default)

### H4: Extra columns
**Cause:** BOQ has columns not in Onsite spec (Amount, Total, Subtotal, etc.)
**Fix:** Remove extra columns. Keep only the 10 Onsite columns in exact order.
**Status:** NOT YET SEEN (anticipated)

---

## SECTION 5: File Format Errors

### FF1: Encoding issues
**Error:** Upload fails silently (no error message)
**Cause:** File not UTF-8 encoded, or has UTF-8 BOM
**Fix:** Re-save as UTF-8 without BOM
**Status:** NOT YET SEEN (anticipated)

### FF2: Wrong delimiter
**Error:** Upload fails silently or all data in one column
**Cause:** Tab-separated or semicolon-separated instead of comma
**Fix:** Convert to comma-separated CSV
**Status:** NOT YET SEEN (anticipated)

### FF3: Blank rows in middle of data
**Error:** Rows after blank are ignored, or validation fails
**Cause:** Empty rows between data rows
**Fix:** Remove all blank rows within data range
**Status:** DOCUMENTED (not directly seen)

### FF4: Hidden rows/columns from Excel
**Error:** Upload includes unexpected data
**Cause:** Hidden rows/columns in original Excel file
**Fix:** Unhide all, remove hidden content before CSV export
**Status:** NOT YET SEEN (anticipated)

### FF5: Multi-line descriptions (newlines in cells)
**Error:** Row count mismatch
**Cause:** Description has newline characters inside a cell
**Fix:** Use Python `csv` module (handles quoted multi-line fields correctly). Do NOT use simple line splitting.
**Seen in:** Multiple BOQs with long construction descriptions
**Status:** HANDLED (all our scripts use csv module)

### FF6: Smart quotes / Unicode quotes
**Error:** Silent data corruption
**Cause:** `"` or `"` instead of standard `"`
**Fix:** Replace all smart quotes with standard ASCII double quotes
**Status:** NOT YET SEEN (anticipated)

### FF7: Special characters in fields
**Error:** Various parsing failures
**Cause:** Characters like `™ © ® ° ²` in material names
**Fix:** Replace with ASCII equivalents or remove
**Status:** NOT YET SEEN (anticipated)

---

## SECTION 6: Material Stock Upload Errors

### M1: Stock already exists
**Error:** `Material stock already exist for material 'X'`
**Cause:** A stock entry for this material already exists in the project
**Fix:** Skip this material, or use the stock update feature instead of upload
**Status:** DOCUMENTED (not directly handled by us)

### M2: Material not in library
**Error:** `Material 'X' does not exist in library`
**Cause:** Material name in stock CSV doesn't EXACTLY match library name (case-sensitive, including typos!)
**Fix:** Export library first, then match names exactly. Known names with typos:
- `2.5 gaugrwire` (not "gauge wire")
- `8 "block` (space before quote)
- `Brsh paint` (not "Brush")
- `Wellding Electrode 2.5 MM -` (trailing hyphen)
- `Concret Mixture` (not "Concrete")
- `Holand 6cm grey - Interlock` (not "Holland")
- `cement I` (lowercase c, space, capital I)
- `hollow bloks` (not "blocks")
- `Fixtures (Sinks, Toilets, Fauc...` (truncated name)
**Status:** SEEN (Jan 2026, brandshell Material Stock)

### M3: Negative stock value
**Error:** `Opening Stock must be >= 0`
**Cause:** Negative number or blank in Opening Stock field
**Fix:** Use `0` or positive number. Empty = error, must be explicit `0`.
**Status:** DOCUMENTED

### M4: Duplicate material in same file
**Error:** `Duplicate material name`
**Cause:** Same material name appears twice in the upload CSV
**Fix:** Deduplicate — keep first occurrence, or highest quantity if merging
**Seen in:** brandshell Material Stock (Jan 2026)
**Status:** SEEN 1x

---

## SECTION 7: Material Library Upload Errors

### L1: Duplicate material name
**Error:** `Duplicate material name`
**Cause:** Same name exists in uploaded file or already in library
**Fix:** Remove duplicates from file, check existing library
**Status:** DOCUMENTED

### L2: Invalid category
**Error:** Not documented — may create new category silently
**Cause:** Category doesn't match existing ones
**Fix:** Use known categories (note: system has typos!):
```
Civil, Electrical, Plumbing, HVAC, Paint & Coatings, Steel & Metal,
Concrete & Masonry, Wiring, carpentry (lowercase c!), Roofing, ceiling (lowercase c!),
Equipment, Safety, Fuel, Site & Landscaping, Asset, Safty (typo!),
Electrical Items, Civil Work, Carpenter
```
**Status:** DOCUMENTED

---

## SECTION 8: Rate Library Upload Errors

### R1: Missing Item Code
**Error:** Upload fails
**Cause:** Item Code column is empty (may be required for Rate Library unlike BOQ)
**Fix:** Add HSN/SAC code as Item Code, or generate sequential codes
**Status:** NOT YET SEEN (anticipated)

### R2: Duplicate service name
**Error:** Not explicitly documented
**Cause:** Same service name appears twice
**Fix:** Deduplicate or differentiate names
**Status:** NOT YET SEEN (anticipated)

---

## SECTION 9: Edge Cases & Gotchas

### E1: Space ≠ Empty ≠ Zero
Critical distinction for numeric fields:
- `0` (zero) = VALID, means "to be quoted"
- ` ` (space) = INVALID, causes float64 error
- `` (empty) = VALID for parent/section rows, INVALID for line items
- `""` (empty string) = Same as empty

### E2: CSV quoting with commas in descriptions
Construction BOQ descriptions often contain commas:
```
"Supply, installation and commissioning of 2x1.5 sqmm copper wire"
```
Must be wrapped in double quotes. Python `csv` module handles this automatically.

### E3: Mixed issues in same file
Client BOQs from WhatsApp typically have 3-4 simultaneous issues:
1. Wrong column headers
2. Invalid serial numbers
3. Invalid units
4. Commas in numbers

Always check ALL issue types, not just the one the error message mentions.

### E4: Parent row detection ambiguity
A row with unit but NO quantity or price is ambiguous:
- Could be a parent/description row → leave serial as section number
- Could be a line item with missing data → flag for review
**Rule of thumb:** If unit exists but qty AND price are both empty, treat as parent.

### E5: Indian vs Western number formats
- Indian: `1,50,000` (lakh), `1,00,00,000` (crore)
- Western: `150,000`, `10,000,000`
- Onsite: `150000` (no commas at all)
Always strip ALL commas regardless of format.

### E6: HSN Code defaults by trade
| Trade | Default HSN |
|---|---|
| Construction services | `9954` |
| Other services | `9997` |
| Manufacturing services | `9988` |
| Electrical products | `8536`-`8544` range |
| Civil materials | `2523` (cement), `6908` (tiles) |
| Aluminium | `76042100` |
| Glass | `70051090` |

### E7: Onsite platform version changes
Current: v8.17.4. If Onsite updates their upload validation, old patterns may break.
Check for:
- New valid units added
- Changed column names
- New required fields
- Changed error messages

---

## Fix Procedure (Universal)

For ANY file that comes in:

```
1. DETECT    → What type? (BOQ/Stock/Library/Rate)
2. HEADERS   → Match to Onsite spec? If not, rename.
3. SERIALS   → Numeric hierarchical? If not, rebuild.
4. UNITS     → All valid? If not, map using MASTER UNIT MAP.
5. NUMBERS   → Commas? Spaces? Symbols? Strip everything.
6. STRUCTURE → Blank rows? Missing parents? Extra columns? Fix.
7. ENCODING  → UTF-8, no BOM, comma-delimited? Verify.
8. VALIDATE  → All checks pass? Output as <name>_FIXED.csv.
9. LOG       → Append fix to ERROR-LOG.md.
```

---

## Stats

| Metric | Value |
|---|---|
| Total scenarios documented | 45+ |
| Scenarios SEEN in real fixes | ~20 |
| Scenarios ANTICIPATED (not yet seen) | ~25 |
| Files fixed total | 9 |
| Unit mappings | 35+ |
| Header variants | 18+ |
| Patterns learned | 21 |

---

*This file is the single source of truth for BOQ upload errors. Update after EVERY fix.*

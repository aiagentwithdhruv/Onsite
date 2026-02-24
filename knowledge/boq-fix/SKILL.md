# BOQ & Data Format Fixer — Self-Learning Skill

> Fix any construction CSV/Excel file (BOQ, Rate Library, Material Stock, Material Library) into Onsite-compatible format. Learns from every fix.

**Version:** 2.0.0
**Last verified:** 2026-02-23
**Platform:** Onsite Teams v8.17.4
**Self-updates:** After every file fix, append learnings to `ERROR-LOG.md`

---

## How This Skill Works

When Dhruv gives you ANY construction data file:

1. **Detect** what type of file it is (BOQ, Rate Library, Material Stock, Material Library, Quotation)
2. **Validate** against the correct target format (see below)
3. **Fix** all issues automatically
4. **Output** a clean, Onsite-compatible CSV
5. **Log** what was wrong and how you fixed it → append to `ERROR-LOG.md`

---

## AUTHORITATIVE Onsite Upload Formats

> These formats are verified against Onsite Teams v8.17.4. Column order is CRITICAL.

### Format 1: BOQ (Bill of Quantities)

**Header (exact column names, exact order):**
```csv
Serial Number,Item Name,Item code,unit,GST Percent,Estimated Quantity,Unit Sale Price,HSN Code,Cost Code,Notes
```

**Column specs:**

| Column | Field | Required | Type | Rules |
|--------|-------|----------|------|-------|
| A | Serial Number | Yes | Text | Hierarchical: `1`, `1.1`, `1.1.1` — NUMERIC ONLY, no letters |
| B | Item Name | Yes | Text | Item/work description |
| C | Item code | No | Text | Internal item code |
| D | unit | Yes* | Text | Must be from valid units list (case-sensitive!) |
| E | GST Percent | Yes* | Number | `18`, `12`, `5`, `0` — no % symbol |
| F | Estimated Quantity | Yes* | Number | No commas: `1000` not `1,000` |
| G | Unit Sale Price | Yes* | Number | No commas: `15000` not `15,000` |
| H | HSN Code | Yes | Text | `9954` for services, product HSN for materials |
| I | Cost Code | No | Text | Cost tracking code |
| J | Notes | No | Text | Additional notes/category |

> *Required only for line items with quantities. Section headers can leave D-G blank.

**Serial Number Rules (CRITICAL — #1 cause of upload failures):**

VALID:
```
1           → Main section header
1.1         → Sub-section or sub-item
1.1.1       → Line item
2.01        → Use for non-data description rows under a section
2.10        → Valid (10th sub-item, NOT confused with 2.1)
```

INVALID (will cause `Error convert strindex_int64`):
```
a, b, c, d  → Letters NOT allowed
A, B, C     → Letters NOT allowed
1-1         → Hyphens NOT allowed
1/1         → Slashes NOT allowed
1.0.1       → Parent "1.0" must exist first
```

**Parent-child hierarchy rules:**
- Every child MUST have a valid parent row
- `2.1.1` requires parent `2.1` to exist
- `2.1` requires parent `2` to exist
- System validates parent exists before accepting child

**Actual error messages from Onsite:**
- `Error convert strindex_int64 : row not valid 3` → Letter-based serial number (a, b, c)
- `row not valid for serial_number` → Duplicate serial numbers
- `Parent Serial Number not valid` → Missing parent hierarchy
- `Error convert unitSalePrice_float64` → Comma in price
- `Error convert quantity_float64` → Comma in quantity

**Example (FINAL working format):**
```csv
Serial Number,Item Name,Item code,unit,GST Percent,Estimated Quantity,Unit Sale Price,HSN Code,Cost Code,Notes
1,DISTRIBUTION BOARDS,,,,,,9954,,
1.1,Typical Flat DB (1 BHK-12WAY SPN),,nos,18,1,4500,9954,ELECTRICAL 1 BHK FLAT,
2,POINT WIRING - TYPICAL FLATS,,,,,,9954,,
2.01,"Point wiring for Lights/Fans/Sockets description...",,,,,,9954,,
2.02,Conduits as specified above,,,,,,9954,,
2.1,One light point controlled by one gang one way 6A switch,,nos,18,8,800,9954,ELECTRICAL 1 BHK FLAT,
2.1.1,"Including supply, installation of 2 x 1.5 sq mm copper wires...",,,,,,9954,,
```

**Key pattern: Description sub-items under a section:**
When a section (e.g., `2`) has description rows before actual line items, use `2.01`, `2.02`, ... `2.06` for descriptions, then `2.1`, `2.2` etc. for actual items with quantities.

---

### Format 2: Material Library

**Header (exact):**
```csv
Material Name,Unit,Category,Description,HSN Code,GST
```

| Column | Field | Required | Rules |
|--------|-------|----------|-------|
| A | Material Name | Yes | Unique, case-sensitive, max 200 chars |
| B | Unit | Yes | Must be from valid units list |
| C | Category | No | Must match existing or create new |
| D | Description | No | Detailed description |
| E | HSN Code | No | HSN code for material |
| F | GST | Yes | Number: 18, 12, 5, 0 |

**Valid categories (case-sensitive, including typos in system):**
```
Civil, Electrical, Plumbing, HVAC, Paint & Coatings, Steel & Metal,
Concrete & Masonry, Wiring, carpentry (lowercase c!), Roofing, ceiling,
Equipment, Safety, Fuel, Site & Landscaping, Asset, Safty (typo exists),
Electrical Items, Civil Work, Carpenter
```

**Example:**
```csv
Material Name,Unit,Category,Description,HSN Code,GST
Aluminium patti,nos,Carpentry Material,Aluminium patti 15mm x 15mm x 12 feet,,18
12MM Extra Clear Glass,sqft,Glass works,12MM Extra Clear Glass,,18
PU White,litre,Paint Material,PU White Paint,,18
```

---

### Format 3: Material Stock

**Header (exact):**
```csv
Material Name,Opening Stock,Estimated Quantity,Budgeted Unit Rate
```

| Column | Field | Required | Rules |
|--------|-------|----------|-------|
| A | Material Name | Yes | **MUST EXACTLY MATCH** library name (case-sensitive, including typos!) |
| B | Opening Stock | Yes | Number >= 0 |
| C | Estimated Quantity | Yes | Number >= 0 |
| D | Budgeted Unit Rate | Yes | Number >= 0 |

**CRITICAL: Name matching is the #1 cause of upload failures.**

Known library names with intentional typos (use EXACTLY):
```
2.5 gaugrwire          (not "gauge wire")
8 "block               (with space before quote)
Brsh paint             (not "Brush paint")
Wellding Electrode 2.5 MM -   (with hyphen at end)
Concret Mixture        (not "Concrete")
Holand 6cm grey - Interlock   (not "Holland")
cement I               (lowercase, space, capital I)
hollow bloks           (not "blocks")
Fixtures (Sinks, Toilets, Fauc...   (truncated name)
```

**Error messages:**
- `Material stock already exist for material 'X'` → Skip, already has stock
- `Material 'X' does not exist in library` → Name doesn't match exactly
- `Opening Stock must be >= 0` → Don't use negative or blank

---

### Format 4: Rate Library / Service Rate

**Header (exact):**
```csv
Service Name,Item Code,Unit,GST Percent,Sales Price,HSN Code,Notes,Sub Category
```

| Column | Field | Required | Rules |
|--------|-------|----------|-------|
| A | Service Name | Yes | Service/item name |
| B | Item Code | No | Internal code or HSN |
| C | Unit | Yes | Must be from valid units list |
| D | GST Percent | Yes | Number: 18, 12, 5, 0 |
| E | Sales Price | Yes | Plain number, no commas |
| F | HSN Code | Yes | HSN/SAC code |
| G | Notes | No | Description |
| H | Sub Category | No | Category classification |

**Example:**
```csv
Service Name,Item Code,Unit,GST Percent,Sales Price,HSN Code,Notes,Sub Category
Non-jindal aluminium,,kg,18,310,76042100,ALUMINIUM MATERIAL,
Jindal aluminium,,kg,18,385,76042100,ALUMINIUM MATERIAL,
5MM CLEAR TOUGHEN GLASS,,sqft,18,52,70051090,GLASS MATERIAL,
```

---

### Format 5: Quotation CSV (Onsite Sales)

**Structure:** Company header block → Client block → Plan rows with GST
(See `Onsite/Quotation_temp/` for reference templates)

---

## Valid Units (AUTHORITATIVE — from Onsite v8.17.4)

**These are the ONLY units Onsite accepts. Case matters!**

| Category | Valid Units |
|----------|-------------|
| **Count** | `nos`, `numbers`, `pcs`, `each`, `pair`, `set`, `Item` |
| **Length** | `meter`, `ft`, `cm`, `in`, `km`, `Mm`, `yard`, `yd`, `RFT`, `RMT` |
| **Area** | `sqft`, `sqm`, `sqmm` |
| **Volume** | `cum`, `cft`, `Litre`, `KL`, `KLD`, `MLD`, `Brass` |
| **Weight** | `kg`, `tonne`, `quintal`, `bags` |
| **Time** | `hours`, `Day`, `shift`, `Monthly`, `manday` |
| **Other** | `lumpsum`, `Bundle`, `Trips`, `points`, `Stage`, `%`, `Lot`, `TR`, `KW`, `CKM` |

### Unit Conversion (INVALID → VALID)

| Invalid Input | Valid Output | Notes |
|---------------|-------------|-------|
| `Nos`, `NOS`, `Nos.`, `No`, `No.` | `nos` | Lowercase, no period |
| `Mtr`, `M`, `mtr` | `meter` | Full spelling |
| `Rm`, `RM`, `rmt`, `Rmt` | `RMT` | Uppercase |
| `Sq m`, `Sq M`, `SQM` | `sqm` | Lowercase, no space |
| `SQFT`, `Sq ft` | `sqft` | Lowercase, no space |
| `M3`, `cu.m`, `Cum` | `cum` | Lowercase |
| `M2`, `sq.m` | `sqm` | Lowercase |
| `Kg`, `KG`, `kgs` | `kg` | Lowercase, no 's' |
| `L`, `ltr`, `Ltr` | `Litre` | Capital L |
| `LS`, `L.S.`, `ls` | `lumpsum` | Full spelling |
| `Ton`, `MT` | `tonne` | Full spelling |
| `Boxes`, `Sheets` | `nos` | Use nos |
| `Pieces` | `pcs` | Use pcs |

---

## Common Issues & Auto-Fix Rules

| # | Issue | Detection | Fix |
|---|-------|-----------|-----|
| 1 | Letter serial numbers (a, b, c) | Non-numeric in Serial Number column | Convert: a→2.01, b→2.02, etc. under parent section |
| 2 | Numbers reset per section | Same numbers repeat after section break | Apply hierarchical numbering |
| 3 | Missing parent hierarchy | Child exists without parent (e.g., 2.1 without 2) | Insert parent row |
| 4 | Wrong column headers | Headers don't match spec | Map to correct Onsite headers |
| 5 | `Serial no.` instead of `Serial Number` | Old header name | Rename |
| 6 | `Type` column | Government BOQ format | Rename to `Serial Number` |
| 7 | `Description` instead of `Notes` | Column naming | Rename |
| 8 | Commas in numbers | `1,50,000` or `7,257.97` | Strip commas → `150000`, `7257.97` |
| 9 | Currency symbols | `Rs.`, `INR`, `$`, `₹` | Strip to plain number |
| 10 | GST as text | `18%` | Convert to number `18` |
| 11 | Invalid units | `Nos`, `Mtr`, `RM` | Map to valid unit (see table above) |
| 12 | Missing HSN codes | Empty HSN column | Default `9954` for services |
| 13 | Missing GST | Empty GST column | Default `18` |
| 14 | Empty rows | Blank rows between data | Remove |
| 15 | BOM characters | UTF-8 BOM at start | Strip BOM |
| 16 | Trailing spaces | Spaces in cells | Trim all cells |
| 17 | Merged cells from Excel | Multi-row cells | Unmerge, keep in parent row |
| 18 | Unicode corruption | `µ` shows as `�` | Fix encoding or replace with `u` |

---

## Fix Procedure (Step by Step)

### Step 1: Detect File Type
Read headers. Classify:
- `Serial Number` + `Item Name` + `GST Percent` → **BOQ**
- `Service Name` + `Sales Price` + `HSN Code` → **Rate Library**
- `Material Name` + `Opening Stock` → **Material Stock**
- `Material Name` + `Unit` + `Category` + `GST` → **Material Library**
- Has company header + Plan Type → **Quotation**
- Unclear → Ask Dhruv

### Step 2: Map Columns to Correct Headers
Rename any mismatched headers to exact Onsite spec.

### Step 3: Fix Data
Apply ALL relevant fixes from the issues table.
- Convert letter serials to numeric (a→2.01, b→2.02)
- Ensure parent-child hierarchy is complete
- Clean all numbers (strip commas, currency, spaces)
- Map all units to valid Onsite units
- Fill missing GST (18) and HSN (9954)
- Remove empty rows
- Fix encoding (UTF-8, no BOM)

### Step 4: Validate
- [ ] Column headers match spec exactly (including case)
- [ ] No duplicate serial numbers
- [ ] Every child has valid parent
- [ ] No letter-based serial numbers
- [ ] All units from valid list
- [ ] All numbers are plain (no commas, symbols)
- [ ] UTF-8, no BOM, no empty rows in middle

### Step 5: Output
- Write clean CSV (append `_FIXED` to filename)
- Show preview of first 10 rows
- Report: total rows, issues found, fixes applied

### Step 6: Learn (CRITICAL)
Append to `ERROR-LOG.md`:
```
## [Date] — [Original Filename]
**Type:** BOQ / Rate Library / Material Stock / Material Library
**Issues found:**
- Issue: [what was wrong] → Fix: [how fixed]
**New pattern learned:** [if any]
```
If NEW issue type found → also ADD to this SKILL.md issues table.

---

## HSN/SAC Code Reference

### Service Codes
| Code | Category |
|------|----------|
| 9954 | Construction services (default) |
| 9997 | Other services |
| 9988 | Manufacturing services |

### Electrical (JBVNL Reference)
| Code | Category |
|------|----------|
| 85011010 | Motors |
| 85044010 | Transformers |
| 85351000 | Fuses |
| 85361000 | Switchgear |
| 85371000 | Control Panels |
| 85381010 | Switchboard Parts |
| 85392910 | LED Lights |
| 85441100 | Copper Wire |
| 85441990 | Cables |
| 85446010 | Cables >1000V |
| 85469000 | Insulators |
| 90283000 | Energy Meters |

### Materials
| Code | Category |
|------|----------|
| 76042100 | Aluminium products |
| 73181110 | Iron/Steel fasteners |
| 70051090 | Glass (toughened) |
| 32091090 | Powder coating |
| 3917 | PVC pipes |
| 7411 | Copper pipes |
| 2523 | Cement |
| 6908 | Tiles (ceramic) |
| 8415 | AC units |
| 8414 | Fans/Exhaust |
| 8536 | Switches/Sockets |
| 9405 | LED Lights |

---

## JBVNL Cost Data Book Reference

**Source:** Jharkhand Bijli Vitran Nigam Limited, FY 2024-25
**Total items:** 1224 electrical distribution items

**Rate columns:**
| Column | Description | When to use |
|--------|-------------|-------------|
| Proposed SOR Rate Excl. GST | Base rate | Internal estimation |
| Proposed SOR Rate Incl. GST | Rate + GST | **Default for uploads** |
| Turnkey <5 Crore | 118% of Incl. GST | Small turnkey projects |
| Turnkey >5 Crore | 126% of Incl. GST | Large turnkey projects |

**GST Rates:** Electrical 18%, Cement/Civil 5%, Services/Labor 18%

---

## Number Formatting Rules

- No commas: `112225` not `1,12,225`
- No currency symbols: `5000` not `₹5000`
- Decimals with period: `1234.56`
- No percentage signs: `18` not `18%`
- No spaces in numbers
- UTF-8 encoding, no BOM
- Standard quotes: `"` not `" "`

---

## Self-Update Rules

| Event | Action | File to Update |
|-------|--------|---------------|
| New file type encountered | Add format spec | This SKILL.md |
| New issue pattern found | Add to issues table | This SKILL.md |
| Every file fixed | Append fix report | ERROR-LOG.md |
| Unit variant discovered | Add to unit conversion table | This SKILL.md |
| HSN code identified | Add to HSN table | This SKILL.md |
| New Onsite error message seen | Add to error messages section | This SKILL.md |
| Onsite platform version changes | Update format specs | This SKILL.md |

---

## Reference Files

| File | Location (relative to Onsite/) | Purpose |
|------|-------------------------------|---------|
| BOQ Format Guide (full) | `knowledge/boq-fix/ONSITE_BOQ_FORMAT_GUIDE.md` | Complete upload format spec with examples |
| BOQ Template (original/broken) | `knowledge/boq-fix/templates/BOQ-Upload-Template-ORIGINAL.csv` | Shows common errors (letter serials, wrong units) |
| BOQ Template (fixed) | `knowledge/boq-fix/templates/BOQ-Upload-Template-FIXED.csv` | Intermediate fix |
| BOQ Template (final/working) | `knowledge/boq-fix/templates/BOQ-Upload-Template-FINAL.csv` | Verified working upload |
| Error screenshot | `knowledge/boq-fix/screenshots/onsite-boq-upload-error-strindex.jpeg` | Actual Onsite UI error for letter serials |
| Platform knowledge base | `knowledge/onsite-platform-knowledge-base.md` | Modules, material library, JBVNL reference |
| CSV creation instructions | `knowledge/onsite-csv-instructions.md` | Rules for each upload type |
| AI system prompt | `knowledge/onsite-ai-system-prompt.md` | Compact rules for AI assistants |
| Complete upload reference | `knowledge/onsite-complete-upload-reference.md` | Full spec: all formats, validation, errors |
| Error log | `knowledge/boq-fix/ERROR-LOG.md` | Cumulative learnings from every fix |
| BOQ HVAC example | `Archived/.../BOQ_HVAC_Formatted.csv` | Correct HVAC BOQ format |
| Rate Library example | `Archived/.../say_infra_Rate_Library_FIXED.csv` | Correct Rate Library format |
| Quotation templates | `Quotation_temp/` | Reference for quotation CSV format |

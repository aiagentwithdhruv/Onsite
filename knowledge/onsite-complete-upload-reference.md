# Onsite Teams - Complete Data Upload Reference Guide

## Overview

**Platform:** Onsite Teams (https://onsiteteams.com/)  
**Version:** v8.17.4  
**Purpose:** Construction Management SaaS - Project tracking, Material management, BOQ, Procurement, Finance

This document contains all validated formats, rules, and specifications for bulk data uploads to Onsite. Use this as the definitive reference for AI assistants or team members preparing upload files.

---

## 1. MATERIAL LIBRARY UPLOAD

### File Format
```csv
Material Name,Category,Sub Category,UoM
```

### Field Specifications

| Field | Type | Required | Max Length | Rules |
|-------|------|----------|------------|-------|
| Material Name | String | Yes | 200 chars | Unique, case-sensitive |
| Category | String | Yes | 100 chars | Must match existing or create new |
| Sub Category | String | No | 100 chars | Optional grouping |
| UoM | String | Yes | 20 chars | Must be from valid UoM list |

### Valid Categories
```
Civil
Electrical
Plumbing
HVAC
Paint & Coatings
Steel & Metal
Concrete & Masonry
Wiring
carpentry (lowercase 'c')
Roofing
ceiling
Equipment
Safety
Fuel
Site & Landscaping
Asset
Safty (typo exists in system)
Electrical Items
Civil Work
Carpenter
```

### Valid Units of Measurement (UoM)
```
# Count Units
nos
numbers
nos.
Nos
Nos.
pcs
pieces
pair
Pair
set
Set
each
Each
unit

# Weight Units
kg
Kg
KG
kgs
gm
gram
grams
tonne
Tonne
MT
quintal

# Length Units
meter
Meter
mtr
Mtr
m
mm
cm
ft
feet
inch
inches

# Area Units
sqft
Sqft
sq.ft
sqm
Sqm
sq.m
sft

# Volume Units
cft
Cft
cu.ft
cum
Cum
cu.m
litre
Litre
ltr
Ltr
gallon
gallons

# Other Units
bags
Bags
roll
Roll
rolls
sheet
Sheet
sheets
bundle
Bundle
box
Box
packet
coil
Coil
drum
Drum
can
length
Length
rm
RM
rmt
RMT
lot
Lot
lump
Lumpsum
LS
ls
job
Job
trip
load
yard
Yard
```

### Sample File
```csv
Material Name,Category,Sub Category,UoM
OPC 43 Grade Cement,Civil,Binding Materials,bags
TMT Steel Bar Fe500D 10mm,Steel & Metal,Reinforcement,kg
Copper Wire 2.5 sqmm FR,Electrical,Wiring,meter
LED Panel Light 2x2,Electrical Items,Lighting,nos
```

---

## 2. MATERIAL STOCK UPLOAD

### File Format
```csv
Material Name,Opening Stock,Estimated Quantity,Budgeted Unit Rate
```

### Field Specifications

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| Material Name | String | Yes | **MUST EXACTLY MATCH** library name (case-sensitive, including typos) |
| Opening Stock | Number | Yes | Must be >= 0, no negative values |
| Estimated Quantity | Number | Yes | Must be >= 0 |
| Budgeted Unit Rate | Number | Yes | Must be >= 0 |

### CRITICAL RULES

1. **Exact Name Match Required**
   - Material name must match library EXACTLY
   - Includes typos, spaces, special characters
   - Case-sensitive matching

2. **No Duplicate Stock Entries**
   - Cannot add stock for material that already has stock
   - Error: "Material stock already exist for material 'X'"
   - Solution: Use stock update feature instead, or skip

3. **Material Must Exist in Library**
   - Cannot add stock for non-existent material
   - Error: "Material 'X' does not exist in library"
   - Solution: Add to Material Library first

### Known Library Names with Typos (Use Exactly As Shown)
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

### Sample File
```csv
Material Name,Opening Stock,Estimated Quantity,Budgeted Unit Rate
OPC 43 Grade Cement,500,5000,380
TMT Steel Bar Fe500D 10mm,200,3000,72
Copper Wire 2.5 sqmm FR,100,500,2500
```

### Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Material stock already exist" | Stock entry exists | Skip or use update feature |
| "does not exist in library" | Name mismatch | Check exact spelling in library |
| "Opening Stock must be >= 0" | Negative or blank value | Use 0 or positive number |
| "must be a number" | Text in numeric field | Remove text, use only numbers |

---

## 3. RATE LIBRARY / SERVICE LIBRARY UPLOAD

### File Format
```csv
Item Code,Item Name,Item Description,Category,Sub Category,UoM,Rate
```

### Field Specifications

| Field | Type | Required | Max Length | Rules |
|-------|------|----------|------------|-------|
| Item Code | String | Yes | 50 chars | Unique identifier (HSN/SAC code recommended) |
| Item Name | String | Yes | 200 chars | Short descriptive name |
| Item Description | String | No | 500 chars | Detailed specification |
| Category | String | Yes | 100 chars | Service/material category |
| Sub Category | String | No | 100 chars | Sub-grouping |
| UoM | String | Yes | 20 chars | From valid UoM list |
| Rate | Number | Yes | - | Unit rate (positive number) |

### Recommended Categories for Electrical (JBVNL)
```
Conductors
Poles & Supports
Insulators
Transformers - Distribution
Transformers - Power
Cables - HT
Cables - LT
Cables - Control
Switchgear
Meters & Metering
CT & PT
Lightning Arrestors
Earthing Materials
Clamps & Connectors
Jointing Kits
Structures & Hardware
Civil Works
Testing Equipment
Safety Equipment
Tools & Instruments
```

### HSN Code Reference (Electrical)
```
85011010 - Motors
85044010 - Transformers
85044090 - Transformer Parts
85351000 - Fuses
85361000 - Switchgear
85371000 - Control Panels
85381010 - Switchboard Parts
85392910 - LED Lights
85399000 - Electrical Parts
85441100 - Copper Wire
85441990 - Cables
85446010 - Cables >1000V
85469000 - Insulators
90283000 - Energy Meters
90303300 - Multimeters
```

### Sample File
```csv
Item Code,Item Name,Item Description,Category,Sub Category,UoM,Rate
85446010-001,ACSR Dog Conductor 100sqmm,ACSR Dog conductor 100 sq.mm as per IS:398,Conductors,ACSR Conductors,km,112225
85044010-001,Distribution Transformer 100kVA,100 kVA 11/0.433kV Distribution Transformer BIS-1 Star Rated,Transformers - Distribution,Oil Filled,nos,188380
85381010-001,11kV Pin Insulator Polymer,11 KV Pin Insulator 10 KN OD 40mm Polymer Type with GI PIN,Insulators,11kV Insulators,nos,334
```

---

## 4. BOQ (BILL OF QUANTITIES) UPLOAD

### File Format
```csv
Item Code,Item Name,Description,UoM,Quantity,Rate,Amount
```

### Field Specifications

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| Item Code | String | Yes | Reference to Rate Library or unique code |
| Item Name | String | Yes | Short name |
| Description | String | No | Detailed description |
| UoM | String | Yes | From valid UoM list |
| Quantity | Number | Yes | Must be > 0 |
| Rate | Number | Yes | Unit rate |
| Amount | Number | Yes | Should equal Quantity × Rate |

### BOQ Categories (Construction)
```
# Civil Works
Excavation
Concrete Works
Masonry
Plastering
Flooring
Waterproofing

# Structural
RCC Works
Steel Structure
Fabrication

# MEP
Electrical
Plumbing
HVAC
Fire Fighting

# Finishing
Painting
False Ceiling
Woodwork
Glazing

# External
Landscaping
External Development
Boundary Wall
```

### Sample File
```csv
Item Code,Item Name,Description,UoM,Quantity,Rate,Amount
CW-001,PCC 1:4:8,Plain Cement Concrete 1:4:8 mix 40mm aggregate,cum,50,5500,275000
CW-002,RCC M25,Reinforced Cement Concrete M25 grade,cum,120,7500,900000
ST-001,TMT Steel Fe500D,TMT Steel reinforcement bars Fe500D,kg,12000,72,864000
EL-001,Conduit Wiring,PVC conduit wiring with 2.5 sqmm FR copper wire,point,150,850,127500
```

---

## 5. JBVNL COST DATA BOOK REFERENCE

### Document Details
- **Title:** Cost Data Book FY 2024-25
- **Source:** Jharkhand Bijli Vitran Nigam Limited (JBVNL)
- **Total Items:** 1224 electrical distribution items
- **Coverage:** Material rates, Labor rates, Unit rate estimates

### Rate Columns Available
| Column | Description | Usage |
|--------|-------------|-------|
| Proposed SOR Rate Excl. GST | Base rate without tax | For internal estimation |
| Proposed SOR Rate Incl. GST | Rate with GST applied | **Default for uploads** |
| Turnkey Rate <5 Crore | 118% of Incl. GST | Small turnkey projects |
| Turnkey Rate >5 Crore | 126% of Incl. GST | Large turnkey projects |

### GST Rates
```
Electrical Equipment: 18%
Cement/Civil Works: 5%
Services/Labor: 18%
```

### Major Item Categories in JBVNL
```
Items 1-100: Conductors, Poles, Insulators
Items 101-200: Transformers, Switchgear
Items 201-400: Cables, Jointing Kits
Items 401-600: Meters, CT/PT, Panels
Items 601-800: Hardware, Clamps, Accessories
Items 801-1000: Structures, Civil Items
Items 1001-1224: Testing Equipment, Repair Parts, Labor Rates
```

### Labor Rate Schedules
```
Item 15: Service Connection Labor
Item 16: 33kV Line Construction Labor
Item 17: 33kV Covered Conductor Labor
Item 18: 11kV Line Construction Labor
```

---

## 6. COMMON FORMATTING RULES

### Numbers
- Use plain numbers without commas: `112225` not `1,12,225`
- Decimals use period: `1234.56`
- No currency symbols: `5000` not `₹5000`
- No percentage signs in rate fields

### Text
- UTF-8 encoding required
- Avoid special characters: `™ © ® ° ²`
- Use standard quotes: `"` not `" "`
- Escape commas in descriptions or use quotes

### Dates (where applicable)
- Format: `DD-MM-YYYY` or `YYYY-MM-DD`
- Example: `06-02-2026`

### File Specifications
- Format: CSV (Comma Separated Values)
- Encoding: UTF-8
- Line endings: Unix (LF) or Windows (CRLF)
- No BOM (Byte Order Mark)
- First row must be header row
- No empty rows in middle of data

---

## 7. VALIDATION CHECKLIST

Before uploading any file, verify:

### Material Library
- [ ] All Material Names are unique
- [ ] Categories match existing or are intentionally new
- [ ] UoM is from valid list
- [ ] No empty required fields

### Material Stock
- [ ] Material Names EXACTLY match library (check character by character)
- [ ] No materials already have stock entries
- [ ] All numbers are >= 0
- [ ] No blank numeric fields

### Rate Library
- [ ] Item Codes are unique
- [ ] HSN codes are valid (if used)
- [ ] Rates are positive numbers
- [ ] UoM is from valid list

### BOQ
- [ ] Item Codes exist in Rate Library (if referencing)
- [ ] Quantities are positive
- [ ] Amount = Quantity × Rate
- [ ] UoM is consistent with Rate Library

---

## 8. ERROR TROUBLESHOOTING

### "does not exist in library"
1. Export current library to CSV
2. Search for similar names
3. Check for typos, extra spaces, case differences
4. Copy exact name from library

### "already exist"
1. This entry already exists in system
2. Use update/edit feature instead of add
3. Or skip this row

### "must be a number"
1. Remove any text, symbols, or spaces
2. Check for invisible characters
3. Ensure decimal format is correct

### "Invalid UoM"
1. Check spelling of unit
2. Use exact format from valid UoM list
3. Case may matter

### Upload fails silently
1. Check file encoding (must be UTF-8)
2. Remove any BOM
3. Check for hidden rows/columns
4. Verify CSV delimiter is comma

---

## 9. QUICK REFERENCE TEMPLATES

### Material Library Template
```csv
Material Name,Category,Sub Category,UoM
[Unique Name],[Valid Category],[Optional Sub Cat],[Valid UoM]
```

### Material Stock Template
```csv
Material Name,Opening Stock,Estimated Quantity,Budgeted Unit Rate
[Exact Library Name],[>=0],[>=0],[>=0]
```

### Rate Library Template
```csv
Item Code,Item Name,Item Description,Category,Sub Category,UoM,Rate
[Unique Code],[Short Name],[Details],[Category],[Sub Cat],[UoM],[Number]
```

### BOQ Template
```csv
Item Code,Item Name,Description,UoM,Quantity,Rate,Amount
[Code],[Name],[Details],[UoM],[Qty],[Rate],[Qty*Rate]
```

---

## 10. AI ASSISTANT INSTRUCTIONS

When preparing files for Onsite upload:

1. **Always ask for current library export** before creating stock files
2. **Match names character-by-character** - typos in library are intentional
3. **Test with 5-10 rows first** before bulk upload
4. **Use Incl. GST rates** from JBVNL unless specified otherwise
5. **Validate all UoM** against the valid list
6. **Check for existing entries** before adding new ones
7. **Keep numeric fields clean** - no symbols, commas in Indian format
8. **Document data sources** - page numbers, version dates

### Response Format for Upload Files
When creating CSV content, always:
- Show preview of first 5-10 rows
- State total row count
- List any potential issues found
- Confirm UoM validity
- Note if any names need verification

---

*Document Version: 1.0*  
*Last Updated: 06 February 2026*  
*Platform Version: Onsite Teams v8.17.4*

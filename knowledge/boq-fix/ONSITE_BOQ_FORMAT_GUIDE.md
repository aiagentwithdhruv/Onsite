# ONSITE TEAMS - BOQ & DATA UPLOAD FORMAT GUIDE

> **Version:** 1.0  
> **Last Updated:** February 2026  
> **Purpose:** Complete reference for all CSV upload formats in Onsite Teams platform

---

## TABLE OF CONTENTS

1. [BOQ Upload Format](#1-boq-upload-format)
2. [Material Library Format](#2-material-library-format)
3. [Rate Library / Service Rate Format](#3-rate-library--service-rate-format)
4. [Valid Units Reference](#4-valid-units-reference)
5. [Common Errors & Solutions](#5-common-errors--solutions)
6. [Best Practices](#6-best-practices)

---

## 1. BOQ UPLOAD FORMAT

### 1.1 Header Structure (Column Order is CRITICAL)

```csv
Serial Number,Item Name,Item code,unit,GST Percent,Estimated Quantity,Unit Sale Price,HSN Code,Cost Code,Notes
```

| Column | Field Name | Required | Data Type | Description |
|--------|------------|----------|-----------|-------------|
| A | Serial Number | ✅ Yes | Text (Hierarchical) | `1`, `1.1`, `1.1.1`, `2`, `2.1` etc. |
| B | Item Name | ✅ Yes | Text | Item/work description |
| C | Item code | ❌ No | Text | Internal item code (optional) |
| D | unit | ✅ Yes* | Text | Must be from valid units list |
| E | GST Percent | ✅ Yes* | Number | `18`, `12`, `5`, `0` |
| F | Estimated Quantity | ✅ Yes* | Number | No commas (use `1000` not `1,000`) |
| G | Unit Sale Price | ✅ Yes* | Number | No commas (use `15000` not `15,000`) |
| H | HSN Code | ✅ Yes | Text | `9954` for services, product HSN codes |
| I | Cost Code | ❌ No | Text | Cost tracking code |
| J | Notes | ❌ No | Text | Additional notes/category |

> *Required for items with quantities. Headers/sections can leave these blank.

---

### 1.2 Serial Number Rules (CRITICAL)

#### ✅ VALID Serial Number Formats
```
1           → Main section header
1.1         → Sub-section header
1.1.1       → Item with data
1.1.2       → Item with data
2           → Main section header
2.1         → Sub-item
2.1.1       → Sub-sub-item
2.10        → Valid (10th sub-item)
2.11        → Valid (11th sub-item)
```

#### ❌ INVALID Serial Number Formats
```
a, b, c     → Letters NOT allowed (use 1.01, 1.02, 1.03)
1.0.1       → Parent "1.0" must exist
11.0.1      → Parent "11.0" must exist (use 11.1 instead)
1-1         → Hyphens NOT allowed
1/1         → Slashes NOT allowed
```

#### Parent-Child Hierarchy Rules
- Every child MUST have a valid parent
- `2.1.1` requires parent `2.1` to exist
- `2.1` requires parent `2` to exist
- System validates parent exists before accepting child

---

### 1.3 BOQ Structure Examples

#### Example 1: Electrical BOQ
```csv
Serial Number,Item Name,Item code,unit,GST Percent,Estimated Quantity,Unit Sale Price,HSN Code,Cost Code,Notes
1,DISTRIBUTION BOARDS,,,,,,9954,,
1.1,Typical Flat DB (1 BHK-12WAY SPN),,nos,18,1,4500,9954,ELECTRICAL,
1.2,Typical Flat DB (2 BHK-16WAY SPN),,nos,18,2,5500,9954,ELECTRICAL,
2,POINT WIRING,,,,,,9954,,
2.1,One light point controlled by 6A switch,,nos,18,8,800,9954,ELECTRICAL,
2.1.1,Including 2x1.5 sqmm copper wires in 20mm conduit,,,,,,9954,,
2.2,One fan point with regulator,,nos,18,3,1100,9954,ELECTRICAL,
2.2.1,Including 2x1.5 sqmm copper wires in 20mm conduit,,,,,,9954,,
```

#### Example 2: Civil BOQ
```csv
Serial Number,Item Name,Item code,unit,GST Percent,Estimated Quantity,Unit Sale Price,HSN Code,Cost Code,Notes
1,EARTH WORK,,,,,,9954,,
1.1,Earth work excavation in foundation trenches,,,,,,9954,,
1.1.1,Lift 0m to 1.50m,,cum,18,400,655,9954,a),
1.1.2,Lift 1.50m to 3m,,cum,18,10,855,9954,b),
1.2,Back filling with excavated earth,,cum,18,1890,400,9954,,
2,CONCRETING,,,,,,9954,,
2.1,PCC 1:4:8 using 40mm aggregates,,,,,,9954,,
2.1.1,Foundations,,cum,18,34.5,8000,9954,a),
2.1.2,Flooring,,cum,18,58.5,8000,9954,b),
```

#### Example 3: HVAC BOQ
```csv
Serial Number,Item Name,Item code,unit,GST Percent,Estimated Quantity,Unit Sale Price,HSN Code,Cost Code,Notes
1,CASSETTE UNITS,,,,,,9954,,
1.1,Supply and installation of Cassette type split AC,,,,,,9954,,
1.1.1,4.0 TR,,nos,18,2,85000,9954,,
1.1.2,3.0 TR,,nos,18,4,65000,9954,,
1.1.3,2.0 TR,,nos,18,6,45000,9954,,
2,REFRIGERANT PIPING,,,,,,9954,,
2.1,Copper pipe with insulation -DERA/RAJCO,,rmt,18,150,450,9954,,
```

---

## 2. MATERIAL LIBRARY FORMAT

### 2.1 Header Structure

```csv
Material Name,Unit,Category,Description,HSN Code,GST
```

| Column | Field Name | Required | Data Type | Description |
|--------|------------|----------|-----------|-------------|
| A | Material Name | ✅ Yes | Text | Material name (must be unique) |
| B | Unit | ✅ Yes | Text | Must be from valid units list |
| C | Category | ❌ No | Text | Material category |
| D | Description | ❌ No | Text | Detailed description |
| E | HSN Code | ❌ No | Text | HSN code for material |
| F | GST | ✅ Yes | Number | GST percentage (18, 12, 5, 0) |

---

### 2.2 Material Library Example

```csv
Material Name,Unit,Category,Description,HSN Code,GST
Aluminium patti,nos,Carpentry Material,Aluminium patti 15mm x 15mm x 12 feet,,18
18 MM MDF BSB 8x4,sqft,Carpentry Material,18 MM MDF BSB 8x4 BOTH SIDE LAMINATE,,18
12MM Extra Clear Glass,sqft,Glass works,12MM Extra Clear Glass,,18
LED MODULES 3Smd Samsung 1.2W,nos,Lighting Material,LED MODULES 3Smd Samsung 1.2W 4000K,,18
RCBO 63 AMP 4 Pole 30 MA Legrand,nos,Electrical,RCBO 63 AMP 4 Pole 30 MA Legrand,,18
P.T. CABLE TRAY 150*50 MM,meter,Electrical,P.T. CABLE TRAY 150*50 MM,,18
PU White,litre,Paint Material,PU White Paint,,18
Duco Paint,litre,Paint Material,Duco Paint,,18
```

### 2.3 Material Library Rules

1. **No Duplicates**: Each Material Name must be unique
2. **Valid Units Only**: Must use units from valid list
3. **GST Required**: Must have GST percentage
4. **No Special Characters**: Avoid problematic characters in names

---

## 3. RATE LIBRARY / SERVICE RATE FORMAT

### 3.1 Header Structure

```csv
Service Name,Item Code,Unit,GST Percent,Sales Price,HSN Code,Notes,Sub Category
```

| Column | Field Name | Required | Data Type | Description |
|--------|------------|----------|-----------|-------------|
| A | Service Name | ✅ Yes | Text | Service/item name |
| B | Item Code | ❌ No | Text | Internal code |
| C | Unit | ✅ Yes | Text | Must be from valid units list |
| D | GST Percent | ✅ Yes | Number | 18, 12, 5, 0 |
| E | Sales Price | ✅ Yes | Number | No commas |
| F | HSN Code | ✅ Yes | Text | HSN/SAC code |
| G | Notes | ❌ No | Text | Description |
| H | Sub Category | ❌ No | Text | Category classification |

---

### 3.2 Rate Library Example

```csv
Service Name,Item Code,Unit,GST Percent,Sales Price,HSN Code,Notes,Sub Category
Non-jindal aluminium,,kg,18,310,76042100,ALUMINIUM MATERIAL,
Jindal aluminium,,kg,18,385,76042100,ALUMINIUM MATERIAL,
M.S (38*8 CSK-PH),,pcs,18,240,73181110,FITTING MATERIAL,
5MM CLEAR TOUGHEN GLASS,,sqft,18,52,70051090,GLASS MATERIAL,
10MM CLEAR TOUGHEN GLASS,,sqft,18,102,70051090,GLASS MATERIAL,
P.P. WHITE,,kg,18,38,32091090,POWDER COATING MATERIAL,
```

---

## 4. VALID UNITS REFERENCE

### 4.1 Complete Valid Units List

| Category | Valid Units |
|----------|-------------|
| **Count** | `nos`, `numbers`, `pcs`, `each`, `pair`, `set`, `Item` |
| **Length** | `meter`, `ft`, `cm`, `in`, `km`, `Mm`, `yard`, `yd`, `RFT`, `RMT` |
| **Area** | `sqft`, `sqm`, `sqmm` |
| **Volume** | `cum`, `cft`, `Litre`, `KL`, `KLD`, `MLD`, `Brass` |
| **Weight** | `kg`, `tonne`, `quintal`, `bags` |
| **Time** | `hours`, `Day`, `shift`, `Monthly`, `manday` |
| **Other** | `lumpsum`, `Bundle`, `Trips`, `points`, `Stage`, `%`, `Lot`, `TR`, `KW`, `CKM` |

### 4.2 Unit Conversion Reference

| ❌ Invalid | ✅ Valid | Notes |
|------------|----------|-------|
| `Nos` | `nos` | Lowercase required |
| `Nos.` | `nos` | Remove period |
| `No` | `nos` | Use full form |
| `No.` | `nos` | Use full form |
| `Mtr` | `meter` | Full spelling |
| `M` | `meter` | Full spelling |
| `Rm` | `RMT` | Use RMT |
| `RM` | `RMT` | Use RMT |
| `rmt` | `RMT` | Uppercase |
| `Sq m` | `sqm` | No space, lowercase |
| `Sq M` | `sqm` | No space, lowercase |
| `SQM` | `sqm` | Lowercase |
| `SQFT` | `sqft` | Lowercase |
| `Sq ft` | `sqft` | No space |
| `M3` | `cum` | Use cum |
| `M2` | `sqm` | Use sqm |
| `Kg` | `kg` | Lowercase |
| `KG` | `kg` | Lowercase |
| `kgs` | `kg` | Remove 's' |
| `L` | `Litre` | Full spelling |
| `ltr` | `Litre` | Full spelling |
| `LS` | `lumpsum` | Full spelling |
| `L.S.` | `lumpsum` | Full spelling |
| `Ton` | `tonne` | Use tonne |
| `MT` | `tonne` | Use tonne |
| `Boxes` | `nos` | Use nos |
| `Sheets` | `nos` | Use nos |
| `Pieces` | `pcs` | Use pcs |

---

## 5. COMMON ERRORS & SOLUTIONS

### 5.1 Serial Number Errors

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `row not valid for serial_number` | Duplicate serial numbers | Ensure each serial number is unique |
| `Parent Serial Number not valid` | Missing parent hierarchy | Add parent row (e.g., add `11` before `11.1`) |
| `Error convert strindex_int64` | Letter-based serials (a,b,c) | Convert to numeric (2.01, 2.02, 2.03) |

### 5.2 Numeric Field Errors

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Error convert unitSalePrice_float64` | Comma in price (`7,257.97`) | Remove commas (`7257.97`) |
| `Error convert quantity_float64` | Comma in quantity (`1,266`) | Remove commas (`1266`) |
| `Invalid rows found in file` | Missing required fields | Add GST, HSN, Description |

### 5.3 Unit Errors

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Unit not found in onsite database` | Invalid unit format | Use exact unit from valid list |

### 5.4 Duplicate Errors

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Duplicate material name` | Same name appears twice | Remove duplicates, keep first occurrence |

---

## 6. BEST PRACTICES

### 6.1 Before Upload Checklist

- [ ] **Serial Numbers**: All numeric, hierarchical, no duplicates
- [ ] **Units**: All from valid units list (case-sensitive)
- [ ] **Numeric Fields**: No commas in Quantity or Price
- [ ] **Required Fields**: GST, HSN Code filled for all items
- [ ] **Parent-Child**: Every child has valid parent
- [ ] **No Empty Rows**: Remove blank rows at end of file
- [ ] **Encoding**: Save as UTF-8 CSV

### 6.2 File Preparation Steps

1. **Export from Excel** → Save as CSV (UTF-8)
2. **Check Units** → Replace invalid units
3. **Check Serial Numbers** → Fix letters, duplicates
4. **Remove Commas** → From all numeric fields
5. **Validate Parents** → Ensure hierarchy is complete
6. **Remove Empty Rows** → Clean file end
7. **Preview in Onsite** → Check before final upload

### 6.3 Naming Conventions

```
Project BOQ:      ProjectName_BOQ_Trade_YYYYMMDD.csv
Material Library: Company_Materials_YYYYMMDD.csv
Rate Library:     Company_RateLibrary_YYYYMMDD.csv
```

---

## QUICK REFERENCE CARD

### BOQ Header
```csv
Serial Number,Item Name,Item code,unit,GST Percent,Estimated Quantity,Unit Sale Price,HSN Code,Cost Code,Notes
```

### Material Header
```csv
Material Name,Unit,Category,Description,HSN Code,GST
```

### Rate Library Header
```csv
Service Name,Item Code,Unit,GST Percent,Sales Price,HSN Code,Notes,Sub Category
```

### Most Common Units
```
nos, meter, sqft, sqm, cum, kg, lumpsum, set, pair, RMT, pcs
```

### Standard HSN Codes
```
9954 - Construction Services
9997 - Other Services
9988 - Manufacturing Services
```

---

## SUPPORT

For upload issues:
1. Check this guide first
2. Validate file format
3. Contact Onsite Teams support with error screenshot

---

*Document maintained by AIwithDhruv for Onsite Teams*

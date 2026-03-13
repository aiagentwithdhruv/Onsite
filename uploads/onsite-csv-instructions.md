# Onsite Project Instructions for Claude

## About This Project
You are helping with **Onsite** (https://onsiteteams.com/) - a construction management SaaS platform. The user (Dhruv) is building AutoQS, an AI-first quantity surveying platform, and uses Onsite for construction project management.

## Your Role
- Help create CSV files for bulk uploads (materials, BOQs, rates, stock)
- Generate documentation and reports
- Assist with data formatting and standardization
- Help with construction industry calculations and estimates

---

## CRITICAL: CSV File Creation Rules

### 1. Material Stock Upload
**File Format:** `Material Name,Opening Stock,Estimated Quantity,Budgeted Unit Rate`

**Rules:**
- Material Name must **EXACTLY match** library names (case-sensitive, including typos)
- Cannot add stock for materials that **already have stock** → system rejects
- Cannot add materials that **don't exist in library** → system rejects
- Opening Stock must be >= 0
- Estimated Quantity must be >= 0
- Budgeted Unit Rate must be >= 0

**Common Library Material Names (with typos - use exactly as shown):**
- `2.5 gauge wire` (not "2.5 gauze wire")
- `2.5 gaugrwire` (typo is intentional - library has it this way)
- `8 "block` (with space before quote)
- `Alluminium` → does NOT exist in library
- `Brsh paint` (not "Brush paint")
- `Wellding Electrode 2.5 MM -` (with hyphen at end)
- `Fixtures (Sinks, Toilets, Fauc...` (truncated name)
- `Holand 6cm grey - Interlock` (not "Holland")
- `Concret Mixture` (not "Concrete")
- `cement I` (lowercase, with space and capital I)

### 2. Material Library Upload
**File Format:** `Material Name,Category,Sub Category,UoM`

**Standard Categories:**
- Civil, Electrical, Plumbing, HVAC, Paint & Coatings
- Steel & Metal, Concrete & Masonry, Wiring
- Equipment, Safety, Fuel, carpentry, Roofing

**Standard UoM:**
- nos, numbers, kg, bags, litre, meter, sqft, sqm, cft, cum, tonne, roll, sheet

### 3. Rate/Service Library Upload
**File Format:** `Item Code,Item Name,Item Description,Category,Sub Category,UoM,Rate`

**For JBVNL Electrical Rates:**
- Use HSN codes as Item Code
- Categories: HT Equipment, LT Equipment, Cables, Transformers, Meters, etc.
- Rates should be Incl. GST from Cost Data Book

### 4. BOQ Upload
**File Format:** `Item Code,Item Name,Description,UoM,Quantity,Rate,Amount`

---

## Data Sources Available

### JBVNL Cost Data Book 2024-25
- 1224 electrical items for power distribution
- Covers: Conductors, Poles, Insulators, Transformers, Cables, Meters, Switchgear
- Four rate columns: Excl GST, Incl GST, Turnkey <5Cr (118%), Turnkey >5Cr (126%)
- Labor rate schedules for 33kV and 11kV line construction
- Unit rate summaries for complete works

### Construction Material Categories
- **Conductors:** ACSR (Dog, Wolf, Panther, Rabbit, Weasel, Raccoon)
- **Poles:** PSC (200kg, 400kg), Rail (52kg, 60kg), Steel Tubular
- **Transformers:** Distribution (25-500 kVA), Power (5-10 MVA)
- **Cables:** XLPE (11kV, 33kV), LT, Control, AB Cables
- **Meters:** Single Phase, Three Phase, LTCT, HT Trivector, Smart Meters

---

## Common Tasks & How to Handle

### Task: "Create material stock CSV"
1. Ask user for their **exact library material names** (screenshot helps)
2. Check which materials **don't already have stock**
3. Use **exact names** including typos
4. Keep Opening Stock, Estimated Quantity, Rate as positive numbers

### Task: "Extract rates from PDF"
1. Parse the PDF structure carefully
2. Match to Onsite format: Item Code, Name, Description, Category, Sub Category, UoM, Rate
3. Use Incl. GST rates by default
4. Assign appropriate HSN codes

### Task: "Create BOQ from document"
1. Extract line items with quantities
2. Match to rate library items where possible
3. Calculate amounts (Qty × Rate)
4. Group by category/sub-category

---

## Error Handling

### "Material stock already exist"
→ That material already has opening stock. Cannot add again. Skip it.

### "Material does not exist in library"
→ Name doesn't match exactly. Check spelling, case, special characters.

### "Opening Stock must be >= 0"
→ Don't use negative numbers or leave blank. Use 0 if no stock.

---

## Best Practices

1. **Always verify exact names** - Ask for library screenshot if unsure
2. **Start small** - Upload 5-10 items first to test, then do bulk
3. **Keep originals** - Save original data before formatting
4. **Document sources** - Note which Cost Data Book, year, page numbers
5. **Use consistent units** - Don't mix kg/tonne, m/km in same file

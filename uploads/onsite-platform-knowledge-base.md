# Onsite Construction Management Platform - Knowledge Base

## Platform Overview

**Onsite** (https://onsiteteams.com/) is a construction management SaaS platform used for:
- Project management and tracking
- Material inventory and stock management
- Bill of Quantities (BOQ) creation and management
- Rate libraries and cost estimation
- Vendor and procurement management
- Daily progress reporting
- Document management

---

## Core Modules

### 1. Material Library
Central repository of all materials used across projects.

**Fields:**
| Field | Description | Example |
|-------|-------------|---------|
| Material Name | Unique identifier | OPC 43 Grade Cement |
| Category | Main grouping | Civil |
| Sub Category | Secondary grouping | Binding Materials |
| UoM | Unit of Measurement | bags |

**Standard Categories:**
- Civil, Electrical, Plumbing, HVAC, Paint & Coatings
- Steel & Metal, Concrete & Masonry, Wiring, carpentry
- Equipment, Safety, Fuel, Roofing, Site & Landscaping

### 2. Material Stock
Track opening stock, current stock, and transactions.

**Fields:**
| Field | Description |
|-------|-------------|
| Material Name | Must match library exactly |
| Opening Stock | Initial quantity |
| Estimated Quantity | Projected requirement |
| Budgeted Unit Rate | Expected cost per unit |

**Business Rules:**
- One stock entry per material per project
- Cannot duplicate - "already exists" error
- Material must exist in library first
- All numeric fields must be >= 0

### 3. Rate/Service Library
Standard rates for services, labor, and composite items.

**Fields:**
| Field | Description |
|-------|-------------|
| Item Code | Unique code (HSN/SAC) |
| Item Name | Short name |
| Item Description | Detailed description |
| Category | Service category |
| Sub Category | Sub-grouping |
| UoM | Unit of Measurement |
| Rate | Standard rate |

### 4. Bill of Quantities (BOQ)
Itemized list of materials/services for a project.

**Fields:**
| Field | Description |
|-------|-------------|
| Item Code | Reference to rate library |
| Item Name | Description |
| UoM | Unit |
| Quantity | Required amount |
| Rate | Unit rate |
| Amount | Qty × Rate |

---

## File Upload Formats

### Material Library CSV
```csv
Material Name,Category,Sub Category,UoM
OPC 43 Grade Cement,Civil,Binding Materials,bags
TMT Steel Bar Fe500D 10mm,Steel & Metal,Reinforcement,kg
```

### Material Stock CSV
```csv
Material Name,Opening Stock,Estimated Quantity,Budgeted Unit Rate
OPC 43 Grade Cement,500,5000,380
TMT Steel Bar Fe500D 10mm,200,3000,72
```

### Rate Library CSV
```csv
Item Code,Item Name,Item Description,Category,Sub Category,UoM,Rate
85381010,11kV Pin Insulator,11 KV Pin Insulator 10 KN Polymer Type with GI PIN,Insulators,11kV Insulators,Nos,334
85044010,Distribution Transformer 100kVA,100 kVA Distribution Transformer BIS-1,Transformers,Distribution,Nos,188380
```

### BOQ CSV
```csv
Item Code,Item Name,Description,UoM,Quantity,Rate,Amount
85381010,11kV Pin Insulator,Polymer Type with GI PIN,Nos,63,334,21042
85044010,DT 100kVA,BIS-1 Rated,Nos,1,188380,188380
```

---

## User's Current Library Materials

Based on uploaded screenshots, the library contains these exact names (use verbatim):

```
2.5 gauge wire
2.5 gaugrwire
8 "block
Cement
Cement sheets
cement sheets nyra
client cement
Diesel
Electrical wire
Glass
hollow bloks
Induction Motor
laptop
M-sand
nuts
Paint Brush
Petrol
plywood
red brick
Red Clay Bricks
Roofing Tiles
Royal paint
Src 30 concrete
Steel
Steel 10 mm
switch
tiles
white cement
Wire
Aluminium panel(ACP)
Blue paint
Brsh paint
camera
Concret Mixture
Conduit & Fittings
Cushions (The Comfort)
Engineered Wood
Fittings & Valves
Fixtures (Sinks, Toilets, Fauc...
GRC panel
Hand gloves
Land
LED Lights
Metal
mud
Pavers & Gravel
Pipes
RCC steel
Red paint
Royal Green paint
Sinuous Springs
Thermostats
Topsoil & Mulch
Upholstery
Vents & Grilles
Water Heaters
water proofing Focrock
Wellding Electrode 2.5 MM -
Wood
cement I
Holand 6cm grey - Interlock
Onsite Bnusiness Plus Plan Sub...
Sand
```

**Note:** Names include intentional typos (gaugrwire, Brsh, Wellding, Holand, Concret, etc.) - must match exactly!

---

## JBVNL Cost Data Book Reference

### Document: Cost_Data_Book_2024-25___.pdf
**Source:** Jharkhand Bijli Vitran Nigam Limited (JBVNL)
**Purpose:** Standard rates for electrical distribution infrastructure

### Key Sections:
1. **Material Rates (Items 1-1224)**
   - Conductors, Poles, Insulators, Transformers
   - Cables, Meters, Switchgear, Accessories
   
2. **Labor Rate Schedules**
   - Item 15: Service Connection Labor
   - Item 16: 33kV Line Construction Labor
   - Item 17: 33kV Covered Conductor Labor
   - Item 18: 11kV Line Construction Labor

3. **Unit Rate Summary (62 estimates)**
   - Service connections (₹0.05-2.58 lacs)
   - 33/11kV Substations (₹195-299 lacs)
   - Overhead lines (₹3.5-45 lacs/km)
   - Distribution substations (₹1.5-8 lacs)

### Rate Columns:
| Column | Description |
|--------|-------------|
| Proposed SOR Rate Excl. GST | Base rate without tax |
| Proposed SOR Rate Incl. GST | Rate with 18% GST |
| Turnkey <5 Crore | 118% of Incl. GST rate |
| Turnkey >5 Crore | 126% of Incl. GST rate |

### GST Rates Applied:
- Electrical equipment: 18%
- Cement/Civil works: 5%

---

## Common Electrical Material Categories

### Conductors
| Type | Size | Application |
|------|------|-------------|
| ACSR Dog | 100 sqmm | 11kV/33kV lines |
| ACSR Wolf | 150 sqmm | 33kV lines |
| ACSR Panther | 232 sqmm | 33kV heavy load |
| ACSR Rabbit | 50 sqmm | LT lines |
| ACSR Weasel | 34 sqmm | LT lines |

### Poles
| Type | Capacity | Height | Application |
|------|----------|--------|-------------|
| PSC 200kg | Light duty | 8m | LT lines |
| PSC 400kg | Medium | 9m | 11kV lines |
| Rail 52kg | Heavy | 13m | 33kV lines |
| Rail 60kg | Extra heavy | 13m | 33kV double circuit |

### Transformers
| Type | Rating | Application |
|------|--------|-------------|
| Distribution | 25-500 kVA | Local distribution |
| Power | 5-10 MVA | Substation |

---

## Onsite Teams Pricing & Plans

> Extracted from onsiteteams.com pricing page (Feb 2026 screenshots)

### Plan Tiers (3 plans — no free tier)

#### Business
- **Tagline:** Designed for small construction businesses that need more robust collaboration
- **International:** ~~$260/User/Year~~ → **$200/User/Year** (min billed $600/yr for 3 users)
- **India:** ~~₹15,000/User/Year~~ → **₹12,000/User/Year** (min billed ₹36,000/yr for 3 users)
- **Features:**
  - Payments & Expenses
  - File Management
  - Labor Attendance & Salary
  - CRM (Leads & Quotation)
  - Material Request & Inventory
  - Task & Sub Task Hierarchy
  - Issue/Snag List (To Do)
  - Subcon Work Order & RA Billing
  - Multiple Roles & Permission
- **Support:** Complimentary (min 3 users), WhatsApp & Google Meet, Onboarding Support

#### Business+ (Most Popular)
- **Tagline:** Advanced tools for mid-sized to large construction companies
- **International:** ~~$325/User/Year~~ → **$250/User/Year** (min billed $750/yr for 3 users)
- **India:** ~~₹19,500/User/Year~~ → **₹15,000/User/Year** (min billed ₹45,000/yr for 3 users)
- **Everything in Business PLUS:**
  - Design Management
  - Bill of Quantity (BOQ) & RA Bills
  - Budget Control
  - Central Warehouse
  - RFQ (Request for Quotation)
  - Purchase Orders
  - Assets & Tools
  - Equipment & Machinery
  - Staff Payroll
  - Site Inspection
  - Multi-Level Approval
- **Support:** Complimentary (min 3 users), Account Setup Support, Onboarding Support

#### Enterprise
- **Tagline:** Custom solutions for large-scale enterprises managing complex operations
- **International:** Custom Pricing, **starting from $15,000**
- **India:** Custom Pricing, **starting from ₹12L+**
- **Everything in Business+ PLUS:**
  - Unlimited Users
  - GPS Attendance
  - Custom Roles
  - Custom Dashboard
  - Accounting Integration (Zoho, Tally)
- **Premium features (paid add-ons at Enterprise level):**
  - Custom Requirements
  - Vendor Portal
  - Client Portal
  - White Labelled Solution
  - SAP Integration
- **Support:** Complimentary (min 3 users), WhatsApp & Google Meet, Onboarding Support

### Additional Add-Ons

| Add-On | International | India | Maintenance |
|--------|--------------|-------|-------------|
| GPS + Facial Recognition | $300/Year | ₹20,000/Year | Included |
| Additional Company | $300/Year | ₹20,000/Year | Included |
| Tally Integration | $300/Year | ₹20,000/Year | $100/Year (₹5,000) |
| Zoho Books Integration | $300/Year | ₹20,000/Year | $100/Year (₹5,000) |

### Key Observations (for Sales Intelligence)
- **No free tier** — minimum entry is Business at $200/user/yr (or ₹12K/user/yr in India)
- **Minimum 3 users** required for all plans (effective min: $600/yr or ₹36K/yr)
- **BOQ is Business+ only** — not available on base Business plan. This is the key upsell lever.
- **Discounted pricing shown** — strikethrough suggests ongoing promotional pricing (~23% off)
- **Enterprise starts at $15K / ₹12L+** — includes unlimited users + integrations
- **Integration add-ons** (Tally, Zoho Books) have separate yearly maintenance fees
- **GPS + Facial Recognition** is an attendance/workforce tracking upgrade
- **Multi-company support** requires paid add-on ($300/year per additional company)
- **India-specific:** Tally integration targets Indian market (Tally is dominant accounting software)
- **White-label + SAP** are Enterprise-only premium features — high-value upsell
- **Dhruv's account** appears to be on "Onsite Business Plus Plan" (from library material name entry)

---

## Tips for Better Results

### When Creating CSVs:
1. Always ask for library screenshot first
2. Match names character-by-character
3. Test with 5-10 rows before bulk upload
4. Keep rates in same unit (per piece, per kg, per meter)

### When Extracting from PDFs:
1. Note the page numbers for reference
2. Identify rate column being used (Excl/Incl GST)
3. Map to appropriate categories
4. Preserve HSN codes where available

### When Calculating Estimates:
1. Use Unit Rate Summary for quick estimates
2. Add contingency (3%), sundries (3%), overhead (10%)
3. Differentiate Normal Soil vs Hard Soil for excavation
4. Include transportation (4%) and T&P (2%) costs

# Construction & Regulatory Glossary

> Domain terminology for AI agents working on construction management and Indian regulatory compliance.
> Last verified: 2026-02-23 | Refresh: Yearly

---

## Construction Terms

### Project Management

| Term | Full Name | Definition |
|------|-----------|-----------|
| **DPR** | Daily Progress Report | Standard daily report tracking work done, labor deployed, materials used, and issues at a construction site. Core feature of any construction software. |
| **BOQ** | Bill of Quantities | Detailed document listing all materials, parts, and labor needed for a construction project, with quantities and costs. Used for bidding and cost estimation. |
| **RFQ** | Request for Quotation | Formal request sent to vendors/suppliers asking for price quotes on materials or services needed for a project. |
| **PO** | Purchase Order | Official document issued to a vendor confirming a purchase of materials/services at agreed prices and quantities. |
| **WBS** | Work Breakdown Structure | Hierarchical decomposition of a project into phases, deliverables, and work packages. |
| **BIM** | Building Information Modeling | 3D digital representation of a building with embedded data (materials, costs, timelines). Advanced feature in construction software. |
| **RFI** | Request for Information | Formal question submitted during construction to clarify design intent, specifications, or project requirements. |

### Financial

| Term | Full Name | Definition |
|------|-----------|-----------|
| **RA Bills** | Running Account Bills | Contractor payment system where bills are raised at project milestones (e.g., foundation done, structure complete). Each RA bill covers work completed since the last bill. Critical cash flow mechanism. |
| **AMC** | Annual Maintenance Contract | Ongoing support agreement (typically yearly) for software, equipment, or systems. Common in Onsite's add-on pricing. |
| **Retention Money** | — | Percentage (typically 5-10%) withheld from contractor payments until defect liability period expires. |
| **Mobilization Advance** | — | Upfront payment (10-20%) given to contractor to start work (purchase materials, setup). |
| **Escalation Clause** | — | Contract provision allowing price adjustments for material cost changes during long projects. |
| **LC/BG** | Letter of Credit / Bank Guarantee | Financial instruments required for large project bids as security. |

### Site Operations

| Term | Full Name | Definition |
|------|-----------|-----------|
| **Site Diary** | — | Daily record of all activities, visitors, weather, incidents at a construction site. Legal document. |
| **Punch List** | — | List of items that don't conform to contract specifications, identified during inspection before project handover. |
| **Change Order** | — | Formal document modifying the original contract scope, price, or timeline. Major source of disputes. |
| **QA/QC** | Quality Assurance / Quality Control | Systematic processes ensuring construction meets design specifications and building codes. |
| **Snag List** | — | Defects identified after substantial completion but before final handover. Similar to punch list. |
| **MEP** | Mechanical, Electrical, Plumbing | Major building systems that run inside the structure. Often subcontracted separately. |

---

## Indian Regulatory Terms

### Real Estate & Construction

| Term | Full Name | Definition | Relevance |
|------|-----------|-----------|-----------|
| **RERA** | Real Estate (Regulation and Development) Act, 2016 | Landmark law mandating transparency in real estate projects. Requires registration of projects, disclosure of approvals, escrow accounts for buyer money. | Software that helps RERA compliance is a strong selling point. |
| **RERA Registration** | — | All residential projects >500 sq.m or >8 apartments must register with state RERA authority before marketing. | Project tracking software proves compliance. |
| **CRZ** | Coastal Regulation Zone | Restrictions on construction near coastlines. | Relevant for coastal city projects. |
| **FSI/FAR** | Floor Space Index / Floor Area Ratio | Maximum construction area allowed relative to plot size. Varies by city/zone. | Budget and design planning. |
| **IOD** | Intimation of Disapproval | Initial construction permit from municipal authorities (name is misleading — it's actually an approval). | Project milestone tracking. |
| **CC/OC** | Commencement Certificate / Occupation Certificate | CC allows construction to start, OC certifies the building is safe to occupy. | Critical project milestones. |

### Taxation

| Term | Full Name | Definition | Relevance |
|------|-----------|-----------|-----------|
| **GST** | Goods and Services Tax | Unified indirect tax replacing multiple taxes. Construction has multiple rates. | All construction billing must be GST-compliant. Built-in GST = table stakes for construction software. |
| **Input Tax Credit** | — | GST paid on purchases can be offset against GST collected on sales. | Software that tracks ITC saves money. |
| **HSN Code** | Harmonized System of Nomenclature | Classification codes for goods and services under GST. Construction services have specific codes. | Required in invoices and quotations. |
| **TDS** | Tax Deducted at Source | Tax deducted by payer before making payment. Contractors face TDS on payments. | Payment tracking must account for TDS. |
| **GSTIN** | GST Identification Number | Unique 15-digit number for every GST-registered business. | Required on all quotations and invoices. Onsite's: 09AAVCA0250E1ZR |
| **E-Way Bill** | — | Electronic document required for movement of goods worth >₹50,000. | Material management feature. |

### Labor & Compliance

| Term | Full Name | Definition | Relevance |
|------|-----------|-----------|-----------|
| **PF** | Provident Fund | Mandatory retirement savings — employer + employee contribute 12% each of basic salary. | Labor management must track PF. |
| **ESI** | Employees' State Insurance | Health insurance for workers earning <₹21,000/month. Employer 3.25% + employee 0.75%. | Mandatory for construction workers. |
| **Minimum Wage** | — | Government-mandated minimum pay, varies by state and skill level. Revised periodically. | Wage calculation must meet minimums. |
| **BOCW** | Building and Other Construction Workers Act | Regulates employment conditions, safety, and welfare of construction workers. | Compliance tracking feature. |
| **Labor Cess** | — | 1% cess on construction cost >₹10 lakh, collected for worker welfare fund. | Project cost calculation. |

---

## Industry Associations

| Abbreviation | Full Name | Relevance |
|-------------|-----------|-----------|
| **CREDAI** | Confederation of Real Estate Developers' Associations of India | Largest real estate developer body. Membership = credibility. Lead source via events. |
| **BAI** | Builders' Association of India | Oldest construction industry body. Conferences = lead generation. |
| **CIDC** | Construction Industry Development Council | Government body promoting industry development. Standards and training. |
| **NAREDCO** | National Real Estate Development Council | Under Ministry of Housing. Policy and advocacy. |
| **ACETECH** | — | Major construction technology exhibition in India. Key sales channel. |

---

## Onsite-Specific Terms

| Term | Meaning in Onsite Context |
|------|--------------------------|
| **Business Plan** | Standard plan at ₹12,000/user/year — core PM, labor, inventory, CRM |
| **Business+ Plan** | Enhanced plan at ₹15,000/user/year — adds BOQ/RA Bills, procurement, multi-level approval |
| **Enterprise Plan** | Full-feature plan at ₹12,00,000 lump sum — unlimited users, white label, SAP add-ons |
| **White Label** | Customer-branded version of Onsite platform (Web: ₹3L, Android: ₹3.5L, iOS: ₹4L) |
| **Deal Owner** | Primary sales rep assigned to a lead/deal (NOT lead_owner). Used for all analytics. |
| **Sale Done** | Boolean flag in Zoho CRM marking a lead as successfully converted. Revenue counted only from sale_done=1. |
| **Price Pitched** | Amount quoted to the prospect (in Rs. format). May differ from final sale amount. |
| **Lead Status** | Zoho CRM status: Not Contacted → Contacted → Qualified → Proposal Sent → Won/Lost |
| **Call Disposition** | Outcome of a sales call: Interested, Not Interested, Callback, No Answer, Wrong Number |

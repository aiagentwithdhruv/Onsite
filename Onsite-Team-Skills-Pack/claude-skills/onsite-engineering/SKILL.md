---
name: onsite-engineering
description: Onsite codebase, BOQ/CSV formats, APIs, and tech stack. Use when editing Onsite repos, fixing uploads, or discussing quotation generator, sales-intelligence, frontend-next, or backend.
---

# Onsite Engineering — Codebase & Formats

## Tech Stack

- **Quotation:** `quotation-generator.html` + Google Apps Script (`QuotationGenerator.gs`). PDF to Drive, email to client.
- **Sales Intelligence:** Next.js 16 + Tailwind 4 (frontend), FastAPI (backend), Supabase (Postgres + pgvector). LangGraph agents. Path: `sales-intelligence/`.
- **Credentials:** Google Drive folder IDs, Zoho, Supabase project ref in main CLAUDE.md.

---

## BOQ & Upload Formats (Critical)

**BOQ CSV header (exact order):**
`Serial Number,Item Name,Item code,unit,GST Percent,Estimated Quantity,Unit Sale Price,HSN Code,Cost Code,Notes`

**Serial numbers:** Numeric only. Valid: `1`, `1.1`, `1.1.1`. Invalid: letters (`a`, `EX.1`), hyphens, slashes. Every child must have a parent row (e.g. `2.1.1` needs `2.1` and `2`).

**Units:** Use platform valid list (case-sensitive). No commas in numbers (use `1000` not `1,000`).

**Material Library:** Material Name, Category, Sub Category, UoM. Material Stock: Material Name, Opening Stock, Estimated Quantity, Budgeted Unit Rate. Material name must match library exactly.

**Rate Library:** Item Code, Item Name, Item Description, Category, Sub Category, UoM, Rate.

---

## User Requirements (from Demo)

1. **Weightage + engineering quantity:** Same item calculable by weight (kg/tonnes) and by engineering quantity (nos, m², m). Both measures stored and reported; conversions auditable.
2. **Financial:** (a) Per entity equity — P&L, capital, allocations per entity/SPV. (b) Per bank interest — different rates for pay vs receive, different tenures (e.g. 3y pay-out, 20y gov payback); credit/debit balanced.

---

## Where to Look

- Full BOQ/format rules: `knowledge/boq-fix/SKILL.md`, `knowledge/boq-fix/ONSITE_BOQ_FORMAT_GUIDE.md`
- Platform modules: `knowledge/onsite-platform-knowledge-base.md`
- Runbooks: `runbooks/deploy-sales-intelligence.md`, `runbooks/add-quotation-feature.md`

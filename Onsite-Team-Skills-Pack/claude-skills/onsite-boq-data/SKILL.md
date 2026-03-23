---
name: onsite-boq-data
description: BOQ and CSV upload formats for Onsite — fix and validate Material Library, Material Stock, Rate Library, BOQ. Use when fixing or validating construction CSV/Excel for upload.
---

# Onsite BOQ & Data Upload — Fix Rules

## BOQ CSV (Exact)

**Header order:** `Serial Number,Item Name,Item code,unit,GST Percent,Estimated Quantity,Unit Sale Price,HSN Code,Cost Code,Notes`

**Serial number:** Numeric only. Valid: `1`, `1.1`, `1.1.1`. Invalid: letters (a, EX.1, CON.11), hyphens, slashes. Every child needs parent (e.g. 2.1.1 → 2.1 → 2). Skip .10, .20 at each level (use .11, .21) to avoid display as .1, .2.

**Units:** From valid list, case-sensitive. Numbers: no commas (1000 not 1,000). GST: 18, 12, 5, 0 — no % symbol.

---

## Material Library

Columns: Material Name, Category, Sub Category, UoM. One row per material. Names must match exactly where used in Stock.

---

## Material Stock

Material Name (match library), Opening Stock, Estimated Quantity, Budgeted Unit Rate. One entry per material per project. All numerics ≥ 0. No duplicates.

---

## Rate Library

Item Code, Item Name, Item Description, Category, Sub Category, UoM, Rate.

---

## Fix Workflow

1. Detect type (BOQ, Rate Library, Material Stock, Material Library).
2. Validate headers and column order.
3. Fix serials (convert EX.1 → 1.1.1 style; ensure parent chain).
4. Normalize units (e.g. "Nos" not "nos" if platform expects title case).
5. Strip commas from numbers; ensure GST and HSN present where required.
6. Output clean CSV. Log fixes to ERROR-LOG or similar for learning.

Full spec: `knowledge/boq-fix/SKILL.md`, `knowledge/boq-fix/ONSITE_BOQ_FORMAT_GUIDE.md`.

# Runbook: Add Feature to Quotation Generator

> How to safely add new features, plans, add-ons, or pricing changes to the Onsite Quotation Generator.

---

## Pre-Checks

- [ ] Understand what's being added (new plan? add-on? pricing change? UI feature?)
- [ ] Read current pricing from `quotation-generator.html` → search for `PRICING` object
- [ ] Read current backend config from `QuotationGenerator.gs` → search for `CONFIG` object
- [ ] Check `UPDATES_LOG.md` for recent changes (avoid conflicts)

---

## Key Rule: Keep Both Files in Sync

The quotation system has TWO files that MUST stay synchronized:

| File | Role | Pricing Location |
|------|------|-----------------|
| `quotation-generator.html` | Frontend form + calculations | `PRICING` JavaScript object |
| `QuotationGenerator.gs` | Backend PDF generation + email | `CONFIG` + inline pricing |

**If you change pricing in one file but not the other, the form will show one price but the PDF will show a different price.**

---

## Step 1: Update Pricing (if applicable)

### In `quotation-generator.html`:
1. Find the `PRICING` object (search for `const PRICING` or `var PRICING`)
2. Add/modify the pricing for both `national` and `international` sections
3. Update the `calculateTotal()` function if the calculation logic changes

### In `QuotationGenerator.gs`:
1. Find the `CONFIG` or pricing section
2. Add/modify matching pricing values
3. Update the `generatePDF()` function to render new items

---

## Step 2: Add UI Elements (if applicable)

### New Plan Card:
1. Find the plan cards section in HTML (search for `selectPlan`)
2. Add a new card following the existing pattern
3. Add the `selectPlan('new_plan')` handler
4. Add conditional visibility logic in `selectPlan()` function

### New Add-on:
1. Find the add-ons checkbox section
2. Add a new checkbox following the existing pattern
3. If it needs a quantity input (like Additional Users), add `toggleAddon()` logic
4. Update `calculateTotal()` to include the new add-on

### New Input Field:
1. Add the HTML input/select element
2. Wire it into the `generateQuotation()` function (adds to form data)
3. Wire it into the `openPreviewWindow()` function (shows in preview)
4. Wire it into the `calculateTotal()` function (affects pricing)

---

## Step 3: Update PDF Generation

In `QuotationGenerator.gs`:
1. Find the `generatePDF()` function
2. Add the new line items to the PDF table
3. Ensure formatting matches (INR with commas for national, USD for international)
4. Test that the PDF layout doesn't break (check margins, page overflow)

---

## Step 4: Test

### Test with Preview (non-destructive):
1. Open `quotation-generator.html` in browser
2. Fill in test data for each scenario
3. Click **Preview** → verify correct calculations in the preview window
4. Check: base price, add-ons, discount, subtotal, GST, total

### Test with Send (requires Apps Script backend):
1. Use a test email address
2. Click **Send** → verify:
   - PDF generates correctly
   - PDF saves to correct Google Drive folder (National/International)
   - Email sent to both client and salesperson
   - Email contains correct PDF attachment

### Test Scenarios:
- National Business+ with add-ons + discount
- International Enterprise (no GST)
- White Label multi-platform
- Additional Users add-on with quantity

---

## Step 5: Update Documentation

After the feature is working:
1. Update `UPDATES_LOG.md` with the changes (follow existing format)
2. Update `.claude/CLAUDE.md` → Pricing section if prices changed
3. Update `tests/quotation-tests.md` with new test cases
4. Update `LOADOUT.md` changelog

---

## Common Gotchas

| Issue | Prevention |
|-------|-----------|
| Pricing mismatch between form and PDF | Always update BOTH files |
| GST applied to international quotes | Check region detection logic in `calculateTotal()` |
| White Label plans showing duration/discount | White Label has fixed pricing — no duration multiplier |
| Additional Users showing for White Label | Add-ons not available for White Label plan |
| PDF exceeds one page | Keep item descriptions short, test with many add-ons |
| CORS error on Send | Apps Script Web App must be deployed as "Anyone can access" |

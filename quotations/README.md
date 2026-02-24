# Quotation Generator

Automated quotation/proforma invoice generator for the Onsite sales team.

---

## Features

- Auto-generate professional PDF quotations
- National (INR) & International (USD) pricing
- Multiple plans: Business, Business+, Enterprise, White Label
- Add-ons: GPS, Tally, Zoho integrations
- Auto-calculated discounts & GST
- Email to client + salesperson automatically
- Save PDF to Google Drive
- Proforma Invoice option

---

## Files

| File | Purpose |
|------|---------|
| `quotation-generator.html` | Web UI (host and open in browser) |
| `QuotationGenerator.gs` | Google Apps Script backend |
| `QUOTATION-GENERATOR-SETUP.md` | Full setup instructions |
| `QUOTATION-SYSTEM-COMPLETE.md` | System documentation |
| `SPECIAL_OFFER_FEATURE.md` | Special offer pricing logic |
| `ADDITIONAL_USERS_DISCOUNT.md` | Discount calculation rules |
| `*.pdf / *.csv` | Generated quotation samples |

---

## Setup

1. Go to [script.google.com](https://script.google.com)
2. Create new project, paste `QuotationGenerator.gs`
3. Deploy as Web App
4. Update the Web App URL in `quotation-generator.html`
5. Host the HTML file (GitHub Pages, Google Sites, or company server)

See `QUOTATION-GENERATOR-SETUP.md` for detailed instructions.

# Onsite Automation Suite

**Internal automation tools for Onsite Teams** - Construction Management Software

> 🔒 Private Repository - ABEYAANTRIX TECHNOLOGY PRIVATE LIMITED

---

## 🚀 Available Tools

### 1. Quotation Generator
Automated quotation/proforma invoice generator for the sales team.

**Features:**
- ✅ Auto-generate professional PDF quotations
- ✅ National (INR) & International (USD) pricing
- ✅ Email to client & salesperson automatically
- ✅ Save PDF to Google Drive
- ✅ Multiple plans: Business, Business+, Enterprise
- ✅ Add-ons: GPS, Tally, Zoho integrations
- ✅ Auto-calculated discounts & GST
- ✅ Proforma Invoice option
- ✅ Remembers salesperson details

**Files:**
- `quotation-generator.html` - Main UI (host this)
- `QuotationGenerator.gs` - Google Apps Script backend

---

## 📦 Quick Start

### For Sales Team
1. Open the hosted quotation generator URL
2. Enter your name → email auto-fills
3. Fill client details
4. Select plan, users, duration
5. Click **Send** → Done!

### For Developers
See `QUOTATION-GENERATOR-SETUP.md` for full setup instructions.

---

## 🌐 Hosting Options

### Option 1: GitHub Pages (Recommended)
```bash
# Enable GitHub Pages in repository settings
# Set source to: main branch, / (root)
# Access at: https://aiagentwithdhruv.github.io/Onsite/quotation-generator.html
```

### Option 2: Google Sites
1. Create a new Google Site
2. Add embed block
3. Paste HTML code
4. Publish

### Option 3: Company Website
Upload `quotation-generator.html` to your server.

---

## 📁 Repository Structure

```
Onsite/
├── README.md                      # This file
├── quotation-generator.html       # Quotation Generator UI
├── QuotationGenerator.gs          # Google Apps Script backend
├── QUOTATION-GENERATOR-SETUP.md   # Setup instructions
├── SALES-TEAM-QUICK-START.md      # Quick start for sales team
├── TROUBLESHOOTING.md             # Common issues & fixes
└── Quotation_temp/                # Reference templates (not needed)
```

---

## 🔧 Configuration

### Google Apps Script
1. Go to [script.google.com](https://script.google.com)
2. Create new project
3. Paste `QuotationGenerator.gs`
4. Deploy as Web App
5. Update URL in `quotation-generator.html`

### Google Drive Folders
- National quotations: `Quotation/National`
- International quotations: `Quotation/International`

---

## 🛣️ Roadmap

Future automation tools planned:
- [ ] Invoice Generator
- [ ] Lead Tracker
- [ ] Proposal Generator
- [ ] Client Onboarding Automation
- [ ] Contract Management
- [ ] Payment Reminders

---

## 👥 Team Access

| Name | Role | Access |
|------|------|--------|
| Dhruv | Admin | Full |
| Sales Team | Users | Quotation Generator |

---

## 📞 Support

For issues or feature requests:
- Email: dhruv.tomar@onsiteteams.com
- Internal: Create GitHub Issue

---

## 📄 License

**Proprietary** - ABEYAANTRIX TECHNOLOGY PRIVATE LIMITED

All rights reserved. Internal use only.

---

*Powered by Onsite - Construction Management Software*
*https://www.onsiteteams.com*

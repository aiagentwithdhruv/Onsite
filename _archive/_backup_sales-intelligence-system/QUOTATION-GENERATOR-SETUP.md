# 🏗️ Onsite Quotation Generator - Setup Guide

> **One-time setup** to enable your sales team to generate professional quotations in seconds.

---

## 📦 What's Included

| File | Purpose |
|------|---------|
| `quotation-generator.html` | Beautiful form for sales team |
| `QuotationGenerator.gs` | Google Apps Script (backend) |
| `QUOTATION-GENERATOR-SETUP.md` | This setup guide |

---

## 🚀 Setup Instructions (15 minutes)

### Step 1: Create Google Drive Folder

1. Go to [Google Drive](https://drive.google.com)
2. Create a new folder: `Onsite Quotations`
3. Open the folder
4. Copy the **Folder ID** from the URL:
   ```
   https://drive.google.com/drive/folders/YOUR_FOLDER_ID_HERE
   ```

---

### Step 2: Set Up Google Apps Script

1. Go to [Google Apps Script](https://script.google.com)
2. Click **New Project**
3. Delete the default code
4. Copy **ALL** code from `QuotationGenerator.gs` and paste it
5. Update the `CONFIG` section at the top:

```javascript
const CONFIG = {
  FOLDER_ID: 'YOUR_GOOGLE_DRIVE_FOLDER_ID', // <-- Paste your folder ID here
  // ... other settings are already configured
};
```

6. Save the project (Ctrl+S or Cmd+S)
7. Name it: `Onsite Quotation Generator`

---

### Step 3: Deploy as Web App

1. Click **Deploy** → **New deployment**
2. Click the gear icon ⚙️ → Select **Web app**
3. Configure:
   - **Description**: `Quotation Generator v1`
   - **Execute as**: `Me`
   - **Who has access**: `Anyone`
4. Click **Deploy**
5. **Authorize** when prompted (click through the warnings - it's your own script)
6. Copy the **Web App URL** (looks like `https://script.google.com/macros/s/...`)

---

### Step 4: Connect the Form

1. Open `quotation-generator.html` in a code editor
2. Find this line (around line 410):
   ```javascript
   const SCRIPT_URL = 'YOUR_GOOGLE_APPS_SCRIPT_WEB_APP_URL';
   ```
3. Replace with your Web App URL:
   ```javascript
   const SCRIPT_URL = 'https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec';
   ```
4. Uncomment the actual fetch code (remove `/*` and `*/` around the fetch block)
5. Comment out the demo setTimeout block
6. Save the file

---

### Step 5: Host the Form

#### Option A: Google Drive Hosting (Free)
1. Upload `quotation-generator.html` to Google Drive
2. Right-click → **Open with** → **Apps Script**
3. Or use Google Sites to embed it

#### Option B: GitHub Pages (Free)
1. Create a GitHub repo
2. Upload the HTML file
3. Enable GitHub Pages in Settings
4. Access at: `https://yourusername.github.io/repo-name/quotation-generator.html`

#### Option C: Any Web Server
- Upload to your existing website
- Or use Vercel, Netlify (free hosting)

---

### Step 6: Add Salesperson Emails

In `quotation-generator.html`, update the salesperson dropdown:

```html
<select id="salesperson" required>
  <option value="">Select Salesperson</option>
  <option value="Sumit|sumit@onsiteteams.com">Sumit</option>
  <option value="Anjali|anjali@onsiteteams.com">Anjali</option>
  <option value="Rahul|rahul@onsiteteams.com">Rahul</option>
  <!-- Add more salespeople here -->
</select>
```

Format: `Name|email@domain.com`

---

## ✅ Done! Test It

1. Open the HTML form in a browser
2. Fill in test data
3. Click **Preview PDF** - should show success toast
4. Check:
   - Google Drive folder for the PDF
   - Salesperson email for notification
   - Client email for quotation

---

## 🎨 Customization

### Add More Salespeople
Edit the `<select id="salesperson">` section in the HTML

### Change Company Details
Edit the `CONFIG` object in `QuotationGenerator.gs`

### Modify Pricing
Edit the `PRICING` object in both files (keep them in sync)

### Add More Add-ons
1. Add checkbox in HTML
2. Add pricing in both `PRICING` objects
3. Add name in `addonNames` in the GS file

---

## 📧 What Emails Look Like

### To Salesperson:
```
Subject: Onsite Quotation ONS-2026-0001 - Star Electric

Hi Sumit,

A new quotation has been generated:

📋 Reference: ONS-2026-0001
👤 Client: Mr. Rahul Parekh (Star Electric)
📦 Plan: Business+ Plan - 10 Users
💰 Amount: ₹1,80,540 (incl. GST)

📎 PDF attached. Also saved to Google Drive.
```

### To Client:
```
Subject: Onsite Quotation ONS-2026-0001 - Star Electric

Dear Mr. Rahul Parekh,

Thank you for your interest in Onsite - Construction Management Software.

Please find attached your quotation (Ref: ONS-2026-0001) for the Business+ Plan - 10 Users.

💰 Total Amount: ₹1,80,540 (inclusive of 18% GST)

To proceed, simply transfer the amount to our bank account mentioned in the quotation...
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Authorization required" | Click through to authorize your own script |
| Emails not sending | Check Apps Script quota (100 emails/day free) |
| PDF not generating | Check FOLDER_ID is correct |
| Form showing error | Check Web App URL is correct |

---

## 📊 Features Summary

✅ **Auto-calculated** - Users × Rate × Duration - Discount + GST  
✅ **Region support** - National (INR) & International (USD)  
✅ **All plans** - Business, Business+, Enterprise  
✅ **Add-ons** - GPS, Tally, Zoho, Additional Company  
✅ **Multi-year discounts** - 2yr (20% off), 3yr (10% off)  
✅ **Auto reference number** - ONS-2026-XXXX format  
✅ **Professional PDF** - Branded, with features list & T&C  
✅ **Google Drive backup** - All quotations saved  
✅ **Dual emails** - Salesperson + Client  
✅ **Concise T&C** - Payment, validity, refund, jurisdiction  

---

## 🆘 Support

Need help? Contact the automation team or check the code comments.

---

**Built with ❤️ for Onsite by Agentic AI Hub**

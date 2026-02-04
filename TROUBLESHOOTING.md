# 🔧 Quotation Generator - Troubleshooting Guide

## ⚠️ If "Send" Button Does Nothing

### Step 1: Update Google Apps Script Code

1. **Open** `/Onsite/QuotationGenerator.gs` in your editor
2. **Copy ALL the code** (Cmd+A, Cmd+C)
3. **Go to** [script.google.com](https://script.google.com)
4. **Open your project** (the one with the Web App URL)
5. **Select all** in the editor (Cmd+A)
6. **Paste** the new code (Cmd+V)
7. **Save** (Cmd+S)

### Step 2: Test the Code

1. In Apps Script, click **Run** button (▶️)
2. Select **`testFolders`** from dropdown
3. Click **Run**
4. Check **Execution log** (bottom panel)
5. Should see: `✅ Both folders accessible`

### Step 3: Re-Deploy

1. Click **Deploy** → **Manage deployments**
2. Click **pencil icon** ✏️ (edit)
3. Change **Version** to **"New version"**
4. Click **Deploy**
5. **Copy the new Web App URL** (if it changed)

### Step 4: Update HTML (if URL changed)

1. Open `/Onsite/quotation-generator.html`
2. Find: `const SCRIPT_URL = '...'`
3. Replace with your **new Web App URL**
4. Save

### Step 5: Test Again

1. **Refresh** the HTML page
2. Fill form completely
3. **Select a salesperson** (important!)
4. Click **"Send to Client & Salesperson"**
5. **Open Console** (F12) to see logs

---

## 🔍 Check Execution Logs

If emails don't arrive:

1. Go to Apps Script
2. Click **View** → **Executions**
3. Click the **latest execution**
4. Check logs for:
   - `=== doPost called ===`
   - `Sending emails to:`
   - `Email sent to salesperson:`
   - `Email sent to client:`
   - Any error messages

---

## 🧪 Test Email Sending

1. In Apps Script, open `QuotationGenerator.gs`
2. Find `testGenerate()` function
3. **Change** `clientEmail: 'test@example.com'` to **YOUR EMAIL**
4. Click **Run** → Select `testGenerate` → **Run**
5. Check your email!

---

## ❌ Common Errors

| Error | Solution |
|-------|----------|
| "No data received" | Check Web App URL is correct in HTML |
| "Invalid salesperson email" | Make sure salesperson dropdown has format: `Name\|email@domain.com` |
| "Failed to send email" | Check Apps Script has permission to send emails (authorize again) |
| "Folder not found" | Check FOLDER_ID_NATIONAL and FOLDER_ID_INTERNATIONAL are correct |

---

## ✅ Quick Checklist

- [ ] Code updated in Apps Script
- [ ] Code saved in Apps Script
- [ ] Re-deployed as "New version"
- [ ] Web App URL updated in HTML (if changed)
- [ ] Salesperson selected in form
- [ ] Client email is valid
- [ ] Checked Execution logs in Apps Script

---

**Still not working?** Check the Execution logs - they'll tell you exactly what's wrong!

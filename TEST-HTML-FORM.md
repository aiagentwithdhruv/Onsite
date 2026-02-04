# 🧪 How to Test HTML Form

## Step-by-Step Testing Guide

---

## ✅ Step 1: Update Apps Script Code

1. **Open** `/Onsite/QuotationGenerator.gs` in your editor
2. **Copy ALL code** (Cmd+A, Cmd+C)
3. **Go to** [script.google.com](https://script.google.com)
4. **Open your project** (Onsite_quote)
5. **Paste** the updated code (Cmd+V)
6. **Save** (Cmd+S)
7. **Re-deploy:**
   - Click **Deploy** → **Manage deployments**
   - Click **pencil icon** ✏️
   - Change to **"New version"**
   - Click **Deploy**

---

## ✅ Step 2: Open HTML Form

1. **Open** `/Onsite/quotation-generator.html` in your browser
   - Double-click the file, OR
   - Right-click → Open with → Chrome/Safari
2. **Open Developer Console** (F12 or Cmd+Option+I)
3. **Go to Console tab**

---

## ✅ Step 3: Fill the Form

Fill in these fields:

```
Salesperson: Dhruv (or any)
Region: National (INR)
Client Name: Test Client
Company Name: Test Company
Email: YOUR_EMAIL@onsiteteams.com (use your real email!)
Phone: +91 9876543210
City/State: Bangalore
Plan: Business+
Users: 3
Duration: 1 Year
Discount: 0
```

---

## ✅ Step 4: Test Preview First

1. Click **"Preview (Opens in New Tab)"**
2. **Check:** New tab opens with quotation
3. **Check:** Quotation looks correct
4. **Check:** Logo, colors, amounts are correct

**If Preview works** → Form is working! ✅

---

## ✅ Step 5: Test Send Button

1. **Keep Console open** (F12)
2. Click **"Send to Client & Salesperson"**
3. **Watch Console** - You should see:
   ```
   === SENDING QUOTATION ===
   Salesperson: Dhruv dhruv.tomar@onsiteteams.com
   Client: Test Client test@example.com
   Full data: {...}
   ✅ Request sent to Apps Script
   ```

4. **Check for errors:**
   - ❌ Red errors in Console → Share with me
   - ✅ No errors → Good!

---

## ✅ Step 6: Verify It Worked

### Check 1: Execution Logs in Apps Script
1. Go to Apps Script
2. Click **View** → **Executions**
3. Click **latest execution**
4. **Look for:**
   ```
   === doPost called ===
   Parsed data - Ref: ONS-2026-XXXX
   ✅ Email sent to salesperson: ...
   ✅ Email sent to client: ...
   ```

### Check 2: Your Email
- Check inbox for quotation PDF
- Check spam folder too

### Check 3: Google Drive
- Go to Google Drive
- Check **Quotation → National** folder
- Should see PDF file

---

## 🔍 Debugging

### If Send Button Does Nothing

**Check Console (F12):**
- Do you see `=== SENDING QUOTATION ===`?
- Any red error messages?
- What's the last message?

**Common Errors:**

| Error | Solution |
|-------|----------|
| `Failed to fetch` | CORS issue - use form submission method (already added) |
| `Network error` | Check internet connection |
| `404 Not Found` | Web App URL is wrong - check in Apps Script |
| No error but no email | Check Execution logs in Apps Script |

---

## 🧪 Quick Test

**Test 1: Console Logs**
1. Open Console (F12)
2. Fill form
3. Click Send
4. **You MUST see:** `=== SENDING QUOTATION ===`
5. If you don't see this → Button click isn't working

**Test 2: Network Tab**
1. Open Console (F12)
2. Go to **Network** tab
3. Click Send
4. **Look for:** Request to `script.google.com`
5. **Check status:** Should be 200 or see the request

**Test 3: Apps Script Logs**
1. After clicking Send
2. Go to Apps Script → View → Executions
3. **Look for:** `=== doPost called ===`
4. If you see this → Request reached Apps Script ✅
5. If not → Request didn't reach Apps Script ❌

---

## 📋 Checklist

- [ ] Apps Script code updated
- [ ] Apps Script re-deployed
- [ ] HTML file opens in browser
- [ ] Console (F12) is open
- [ ] Preview button works
- [ ] Send button clickable
- [ ] Console shows "=== SENDING QUOTATION ==="
- [ ] Execution logs show "=== doPost called ==="
- [ ] Email received
- [ ] PDF in Google Drive

---

## 🆘 If Still Not Working

**Share with me:**
1. Screenshot of Console (F12) showing errors
2. Screenshot of Execution logs in Apps Script
3. What happens when you click Send (any message? nothing?)

---

**Follow these steps and let me know what you see in the Console!**

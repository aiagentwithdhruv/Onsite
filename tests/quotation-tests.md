# Quotation Generator — Test Cases

> Use these test cases to verify quotation calculations are correct after any pricing or feature change.

---

## Test 1: National Business+ Quote (Standard)

**Input:**
- Region: National (INR)
- Plan: Business+
- Users: 50
- Duration: 2 years
- Discount: 10%
- Add-ons: GPS Attendance
- Client: Test Corp, test@example.com

**Expected Calculation:**
```
Base Price:     50 users × ₹15,000/user/year × 2 years = ₹15,00,000
GPS Add-on:     ₹20,000
Subtotal Before Discount: ₹15,20,000
Discount (10%): -₹1,52,000
Subtotal:       ₹13,68,000
GST (18%):      ₹2,46,240
TOTAL:          ₹16,14,240
```

**Verify:**
- [ ] Summary box shows correct line items
- [ ] Preview PDF shows correct totals
- [ ] Quotation number format: ONS-2026-XXXX

---

## Test 2: International Enterprise Quote

**Input:**
- Region: International (USD)
- Plan: Enterprise
- Users: N/A (lump sum)
- Duration: 1 year
- Discount: 0%
- Add-ons: None

**Expected Calculation:**
```
Base Price:     $15,000 (lump sum)
GST:            $0 (international = no GST)
TOTAL:          $15,000
```

**Verify:**
- [ ] No GST line in summary
- [ ] Currency shows $ not ₹
- [ ] Saved to International folder (ID: 1pL0A6B-dWmLww6ClR366MD__zglR3Haa)

---

## Test 3: White Label Multi-Platform

**Input:**
- Region: National (INR)
- Plan: White Label
- Platforms: Web + Android
- Discount: N/A (no discount for White Label)
- Add-ons: N/A (no add-ons for White Label)

**Expected Calculation:**
```
Web Platform:   ₹3,00,000
Android App:    ₹3,50,000
Subtotal:       ₹6,50,000
GST (18%):      ₹1,17,000
TOTAL:          ₹7,67,000
```

**Verify:**
- [ ] Duration selector hidden for White Label
- [ ] Discount field hidden for White Label
- [ ] Add-ons hidden for White Label
- [ ] Platform checkboxes visible and working

---

## Test 4: National Business with All Add-ons

**Input:**
- Region: National (INR)
- Plan: Business
- Users: 25
- Duration: 1 year
- Discount: 5%
- Add-ons: GPS + Tally + Zoho + Additional Company + 10 Additional Users

**Expected Calculation:**
```
Base Price:     25 users × ₹12,000/user/year × 1 year = ₹3,00,000
GPS:            ₹20,000
Tally:          ₹20,000 + ₹5,000 AMC = ₹25,000
Zoho:           ₹20,000 + ₹5,000 AMC = ₹25,000
Additional Co:  ₹20,000
Additional Users: 10 × ₹5,000 = ₹50,000
Subtotal Before Discount: ₹4,40,000
Discount (5%):  -₹22,000
Subtotal:       ₹4,18,000
GST (18%):      ₹75,240
TOTAL:          ₹4,93,240
```

**Verify:**
- [ ] All add-ons appear as separate line items
- [ ] Additional Users input field shows when checkbox selected
- [ ] AMC pricing included for Tally and Zoho

---

## Test 5: International Business+ with Additional Users

**Input:**
- Region: International (USD)
- Plan: Business+
- Users: 30
- Duration: 3 years
- Discount: 15%
- Add-ons: 5 Additional Users

**Expected Calculation:**
```
Base Price:     30 users × $250/user/year × 3 years = $22,500
Additional Users: 5 × $60 = $300
Subtotal Before Discount: $22,800
Discount (15%): -$3,420
Subtotal:       $19,380
GST:            $0
TOTAL:          $19,380
```

**Verify:**
- [ ] No GST for international
- [ ] Duration multiplier applied to base only
- [ ] Discount applied to (base + add-ons)

---

## Test 6: Edge Cases

### 6a: Zero Users
- Plan: Business, Users: 0
- Expected: Validation error, form should not submit

### 6b: 100% Discount
- Plan: Business+, Discount: 100%
- Expected: Should this be allowed? If yes, total = GST on ₹0 = ₹0

### 6c: White Label All Platforms (International)
- Platforms: Web + Android + iOS, International
- Expected: $3,600 + $4,200 + $4,800 = $12,600, no GST

### 6d: Proforma Invoice Toggle
- Enable "Proforma Invoice" option
- Expected: Document title changes to "Proforma Invoice" instead of "Quotation"

---

## PDF Verification Checklist

For ANY generated quotation, verify:
- [ ] Company logo (Onsite red circle + S-arrow) appears
- [ ] Company name: ABEYAANTRIX TECHNOLOGY PRIVATE LIMITED
- [ ] GSTIN: 09AAVCA0250E1ZR (national only)
- [ ] Bank details: ICICI 401705000501, IFSC ICIC0004017 (national)
- [ ] Currency Cloud details (international)
- [ ] Client name and company correct
- [ ] All line items match form selections
- [ ] Totals match form calculations
- [ ] Quotation number is sequential
- [ ] Date is current

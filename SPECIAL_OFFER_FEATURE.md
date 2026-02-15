# Special Offer (Extra Users) Feature - Feb 13, 2026

## What Changed

The "Additional Users" add-on has been redesigned as **"Special Offer (Extra Users)"** with flexible price selection instead of fixed ₹5,000/user pricing.

---

## Key Features

### 1. **Renamed Label**
- **Old**: "Additional Users" → **New**: "Special Offer (Extra Users)"
- Makes it clear this is a flexible, customizable offering

### 2. **Price Selection (Like Plan Selection)**
When you check the "Special Offer" checkbox, you now see **3 price options**:

```
┌─────────────────────────────────────────────┐
│  Select Price per User                      │
│  ┌──────────────┬──────────────┬──────────┐ │
│  │   Business   │  Business+   │  Custom  │ │
│  │  ₹12,000/user│  ₹15,000/user│ Enter    │ │
│  └──────────────┴──────────────┴──────────┘ │
└─────────────────────────────────────────────┘
```

**How it works:**
- **Business**: ₹12,000/user
- **Business+**: ₹15,000/user
- **Custom**: Enter any custom price per user

### 3. **Custom Price Input**
If you select "Custom", an input field appears:
```
Custom Price per User: [_________]
```
- You can enter any amount you want per user
- Team decides final pricing per quotation

### 4. **Number of Additional Users**
```
Number of Additional Users: [____]
(How many extra users at the selected price)
```

### 5. **Additional Discount %**
```
Additional Discount %: [____]
(Optional: Extra discount on top of selected price)
```

---

## Examples

### Example 1: Business+ Plan, 5 Extra Users
```
Plan selected: Business+ (₹15,000/user/year)
Special Offer Price selected: Business+ (₹15,000/user)
Number of Additional Users: 5
Additional Discount: 0%

Calculation:
5 × ₹15,000 = ₹75,000 ✓
```

### Example 2: Business Plan, 10 Extra Users with 15% Discount
```
Plan selected: Business (₹12,000/user/year)
Special Offer Price selected: Business (₹12,000/user)
Number of Additional Users: 10
Additional Discount: 15%

Calculation:
10 × ₹12,000 = ₹120,000
15% off: ₹120,000 × (1 - 0.15) = ₹102,000 ✓
```

### Example 3: Custom Price (₹10,000/user)
```
Plan selected: Business+ (₹15,000/user/year)
Special Offer Price selected: Custom
Custom Price per User: ₹10,000
Number of Additional Users: 8
Additional Discount: 10%

Calculation:
8 × ₹10,000 = ₹80,000
10% off: ₹80,000 × (1 - 0.10) = ₹72,000 ✓
```

---

## How to Use

1. **Select a plan** (Business, Business+, Enterprise)
2. **Check "Special Offer (Extra Users)"** checkbox
3. **Choose a price option**:
   - Click "Business" for ₹12,000/user pricing
   - Click "Business+" for ₹15,000/user pricing
   - Click "Custom" and enter your custom price
4. **Enter number of extra users** you want to offer
5. **Optional: Add discount %** on top of that price
6. The summary box updates automatically with the calculated cost

---

## Pricing Display

### In Form (Add-Ons Section)
```
☑ Special Offer (Extra Users)    Choose price
```
When unchecked, shows "Choose price"

### In Quotation Summary
```
Special Offer - Extra Users  | 5 users | ₹15,000/user (10% off) | 1 Year | ₹67,500
```
Shows:
- Number of extra users
- Price per user (with discount if applied)
- Total amount

### In PDF Preview
Same as summary - shows exact pricing for transparency

---

## Features

✅ **Flexible Pricing**: Choose from Business (₹12K), Business+ (₹15K), or Custom
✅ **Price Options Like Plans**: Button-style selection, not a dropdown
✅ **Custom Price Support**: No limit - team can offer any price
✅ **Optional Discounts**: Apply extra discount on top of selected price
✅ **Region-Aware**: Updates prices when National/International region changes
✅ **Real-Time Calculation**: Summary updates instantly as you change values
✅ **Transparent PDF**: Quotation shows exact pricing for audit trail

---

## Files Modified

### `/Users/apple/Documents/Agentic Ai Hub/Calud_Code/n8n/Onsite/quotation-generator.html`

**HTML Changes:**
- Line 733: Renamed "Additional Users" → "Special Offer (Extra Users)"
- Line 734: Changed label from "Same as plan" → "Choose price"
- Lines 738-775: Redesigned form section with:
  - Price selection buttons (Business, Business+, Custom)
  - Custom price input field
  - Updated helper text

**CSS Changes:**
- Added `.plan-option-btn` styles for button appearance
- Hover effects, border styling, transitions

**JavaScript Changes:**
- New function: `selectSpecialOfferPrice(priceType, el)`
  - Handles price option button selection
  - Shows/hides custom price input
  - Updates selected price value
  - Applies visual styling (blue border + background)
- Updated `calculateTotal()`:
  - Uses `specialOfferPrice` instead of fixed pricing
  - Reads from Business, Business+, or Custom amount
- Updated `openPreviewWindow()`:
  - Uses selected price for PDF generation
  - Shows "Special Offer - Extra Users" in invoice
- Updated `updatePricing()`:
  - Updates special offer price buttons when region changes
- Updated `generateQuotation()`:
  - Passes `specialOfferPrice` and `specialOfferCustomAmount` to server

---

## Testing Checklist

- [x] "Special Offer (Extra Users)" displays correctly
- [x] "Choose price" label shows initially
- [x] Price selection buttons appear when checkbox is checked
- [x] Buttons become blue when selected
- [x] Business button shows ₹12,000/user
- [x] Business+ button shows ₹15,000/user
- [x] Custom option shows input field when selected
- [x] Custom input field hides when other options selected
- [x] Prices update correctly for National (₹) and International ($)
- [x] Discount % applies correctly on top of selected price
- [x] Summary box shows correct total
- [x] PDF preview shows correct pricing with discount label
- [x] Form data saves special offer price and custom amount

---

## Summary

The sales team now has full flexibility to:
1. Choose from preset pricing (Business/Business+ tiers)
2. Enter custom pricing if needed
3. Apply additional discounts on top
4. Offer different rates for extra users per quotation
5. Maintain full transparency in PDFs

This gives maximum flexibility while keeping the UI clean and intuitive. ✅

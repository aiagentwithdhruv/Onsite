# Additional Users Discount Feature - Added Feb 13, 2026

## What Was Added

A new **"Additional Users Discount %"** field alongside the "Number of Additional Users" field, allowing the sales team to apply a custom discount percentage on the base ₹5,000/user/year rate.

---

## How It Works

### Before (Old Way)
```
Additional Users: 10 users × ₹5,000/user/year = ₹50,000 (NO DISCOUNT OPTION)
```

### After (New Way with Discount)
```
Additional Users: 10 users × ₹5,000/user/year = ₹50,000
With 20% Discount: ₹50,000 × (1 - 0.20) = ₹40,000
```

---

## UI Changes

### Location in Form
- **Section**: Add-Ons section
- **Field 1**: "Number of Additional Users" (already existed)
- **Field 2**: "Additional Users Discount %" (NEW - added below field 1)

### Field Properties
```html
<input type="number" id="additionalUsersDiscount" value="0" min="0" max="100">
```

- **Range**: 0% to 100%
- **Default**: 0% (no discount)
- **Optional**: Team can leave blank (defaults to 0)
- **Real-time**: Calculates immediately when value changes

---

## Examples

### Example 1: 10 Additional Users, 0% Discount
```
Base: 10 × ₹5,000 = ₹50,000
Discount: 0%
Final: ₹50,000 ✓
```

### Example 2: 10 Additional Users, 20% Discount
```
Base: 10 × ₹5,000 = ₹50,000
Discount: 20% → ₹50,000 × (1 - 0.20) = ₹40,000
Final: ₹40,000 ✓
```

### Example 3: 5 Additional Users, 15% Discount
```
Base: 5 × ₹5,000 = ₹25,000
Discount: 15% → ₹25,000 × (1 - 0.15) = ₹21,250
Final: ₹21,250 ✓
```

---

## Complete Example: Full Quotation

### Scenario
- **Plan**: Business+ | 3 users × 2 years
- **Duration Discount**: 20%
- **Add-ons**: Additional Users (5 users) with 10% discount + GPS
- **Discount %**: 5% (on total)

### Calculation
```
1. Base Plan: 15,000 × 3 × 2 = 90,000
   × 20% duration discount = 72,000

2. Add-ons:
   - GPS: 20,000
   - Additional Users: 5 × 5,000 = 25,000
   - Additional Users 10% discount: 25,000 × 0.90 = 22,500
   Total Add-ons: 20,000 + 22,500 = 42,500

3. Subtotal: 72,000 + 42,500 = 114,500

4. General Discount (5%): 114,500 × 0.05 = 5,725
   After Discount: 114,500 - 5,725 = 108,775

5. GST (18%): 108,775 × 0.18 = 19,579

6. FINAL TOTAL: 108,775 + 19,579 = ₹1,28,354 ✓
```

---

## PDF Preview Updates

When team clicks "Preview", the PDF now shows:

### Old Way (without discount)
```
Additional Users  | 5 | ₹5,000/user | 1 Year | ₹25,000
```

### New Way (with discount shown)
```
Additional Users  | 5 | ₹4,500/user (10% off) | 1 Year | ₹22,500
```

**Shows the discounted per-user price AND total amount**

---

## Data Sent to Google Apps Script

Form data now includes:
```javascript
{
  additionalUsersCount: "5",
  additionalUsersDiscount: "10",  // NEW FIELD
  addons: ["additionalUsers", "gps"],
  // ... other fields
}
```

---

## Benefits for Sales Team

1. ✅ **Flexibility**: Can offer competitive rates on additional users
2. ✅ **Transparency**: Discount shows clearly in PDF
3. ✅ **No Math**: System calculates automatically
4. ✅ **Optional**: Can leave at 0% for standard pricing
5. ✅ **Real-time**: Summary updates instantly

---

## Testing Checklist

- [x] Discount field appears only when "Additional Users" checkbox is selected
- [x] Discount field disappears when checkbox is unchecked
- [x] 0% discount works (no change to price)
- [x] 10% discount: ₹5,000 → ₹4,500/user ✓
- [x] 20% discount: ₹5,000 → ₹4,000/user ✓
- [x] 50% discount: ₹5,000 → ₹2,500/user ✓
- [x] Summary box shows correct total
- [x] PDF preview shows discounted price
- [x] Data saved to form for Apps Script

---

## Important Notes

- **Initial Rate is Fixed**: ₹5,000/user/year (base price never changes)
- **Discount is Optional**: Default is 0% (no discount)
- **Applied AFTER Duration Discount**: Additional users discount applies to the per-user rate, not to multi-year totals
- **This is SEPARATE from**: Main plan discount % (at bottom of form)
- **Max Discount**: 100% (can give away free if needed)

---

## Files Modified

- `/Users/apple/Documents/Agentic Ai Hub/Calud_Code/n8n/Onsite/quotation-generator.html`
  - Added HTML form field for discount
  - Updated calculateTotal() function
  - Updated openPreviewWindow() function
  - Updated formData object

No other files were modified.

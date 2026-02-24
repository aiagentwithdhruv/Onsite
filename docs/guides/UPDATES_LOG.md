# Quotation Generator - Updates Log

## Date: 2026-02-13

### Updates Made to quotation-generator.html

#### 1. ✅ Added White Label Plan (4th Plan Option)

**Plan Card Added:**
- New plan option: "White Label" alongside Business, Business+, and Enterprise
- Starting price: ₹3L (Web platform)

**White Label Platform Selection:**
- Added checkbox group for selecting platforms:
  - **Web Platform**: ₹3,00,000
  - **Android App**: ₹3,50,000
  - **iOS App**: ₹4,00,000

**Features:**
- Users can select multiple platforms to create a single quotation for all platforms
- Pricing is automatically calculated based on selected platforms
- No duration/discount option for white label (fixed pricing)
- No add-ons available for white label plan

---

#### 2. ✅ Added Additional Users Add-on

**Add-on Type:**
- Name: "Additional Users"
- Base Price: ₹5,000/user/year
- Available for Business, Business+, and Enterprise plans (NOT for white label)

**Additional Users Feature:**
- Input field to specify number of additional users
- Automatically hidden until "Additional Users" checkbox is selected
- Price calculated as: `Number of Additional Users × ₹5,000/year`
- Provides discount option (10% cheaper than base plan user pricing)

---

#### 3. 💰 Pricing Updates

**National (INR) Pricing:**
```javascript
white_label: {
  web: 300000,      // ₹3 Lakhs
  android: 350000,  // ₹3.5 Lakhs
  ios: 400000       // ₹4 Lakhs
}
additionalUsers: 5000  // ₹5,000/user/year
```

**International (USD) Pricing:**
```javascript
white_label: {
  web: 3600,        // $3600
  android: 4200,    // $4200
  ios: 4800         // $4800
}
additionalUsers: 60    // $60/user/year
```

---

#### 4. 🔧 JavaScript Function Updates

**New Functions Added:**
- `toggleWhiteLabel(el)` - Handles white label platform selection
- Updated `toggleAddon(el)` - Now shows/hides additional users input field

**Updated Functions:**
- `selectPlan(plan)` - Added handling for white_label plan visibility
- `updatePricing()` - Added white label price display updates
- `calculateTotal()` - Added white label and additional users calculations
- `openPreviewWindow(data)` - Added white label items in PDF preview
- `generateQuotation(action)` - Added white label platforms and additional users to form data

---

#### 5. 📊 Summary Box Updates

The quotation summary now shows:
- White Label Plan with selected platforms
- Additional Users count and pricing
- All pricing calculations include both features

---

### How to Use

**For White Label Quotations:**
1. Select the "White Label" plan
2. Check the platforms needed (Web, Android, iOS)
3. Price automatically updates based on selection
4. Preview and send as usual

**For Additional Users:**
1. Select any of the standard plans (Business, Business+, Enterprise)
2. Check the "Additional Users" add-on
3. Enter the number of additional users
4. Price calculated as: `(numUsers × planPrice × duration) + (additionalUsers × ₹5,000)`

---

### Testing Checklist

- [ ] White Label plan card displays correctly
- [ ] White label platform checkboxes work
- [ ] Additional Users field shows/hides correctly
- [ ] Pricing updates correctly for national and international regions
- [ ] Summary box shows correct calculations
- [ ] PDF preview displays white label and additional users correctly
- [ ] Send to Gmail works with new data fields

---

### Notes

- White Label is a separate plan (not an add-on) with fixed platform-based pricing
- Additional Users is an add-on available only for standard plans
- All prices are tested for both national (INR) and international (USD) regions
- No duration discounts apply to White Label pricing

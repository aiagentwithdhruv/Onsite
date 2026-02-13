 /**
 * ONSITE QUOTATION GENERATOR - Google Apps Script
 * 
 * SETUP INSTRUCTIONS:
 * 1. Go to https://script.google.com
 * 2. Create a new project
 * 3. Copy this entire code
 * 4. Deploy as Web App (Execute as: Me, Access: Anyone)
 * 5. Copy the Web App URL and paste in quotation-generator.html
 * 6. Create a Google Drive folder for quotations and update FOLDER_ID below
 */

// ============== CONFIGURATION ==============
const CONFIG = {
  // Separate folders for easy tracking
  FOLDER_ID_NATIONAL: '19nxVxULJFIs0-gFW6J3mMWH1eWpfLveu',      // National (INR) quotations
  FOLDER_ID_INTERNATIONAL: '1pL0A6B-dWmLww6ClR366MD__zglR3Haa', // International (USD) quotations
  LOGO_URL: 'https://drive.google.com/uc?export=view&id=1GWUzCsLlwXj4jiwN3B-fZ5Ttiu7Xj9mC', // Onsite logo
  COMPANY_NAME: 'ABEYAANTRIX TECHNOLOGY PRIVATE LIMITED',
  BRAND_NAME: 'Onsite',
  ADDRESS: 'C-93, 3rd Floor, C Block, Sector 2, Noida, Uttar Pradesh 201301',
  GSTIN: '09AAVCA0250E1ZR',
  PAN: 'AAVCA0250E',
  PHONE: '+91 9560209605',
  EMAIL: 'sumit@onsiteteams.com',
  WEBSITE: 'https://www.onsiteteams.com',
  BANK_NAME: 'ICICI Bank',
  ACCOUNT_NO: '401705000501',
  IFSC: 'ICIC0004017',
  UPI: 'ABEYAANTRIXTECHNOLOGYPVTLTD@icici',
  BANK_ADDRESS: 'ICICI Bank Ltd, 30-27 East Patel Nagar, New Delhi 110008',
  // International SWIFT account (default for international quotes)
  INTERNATIONAL_PAYMENT_METHOD: 'SWIFT (International wire)',
  INTERNATIONAL_IBAN: 'GB89TCCL04140490016036',
  INTERNATIONAL_SWIFT: 'TCCLGB3L',
  INTERNATIONAL_ACCOUNT_TYPE: 'Business checking account',
  INTERNATIONAL_BANK_NAME: 'The Currency Cloud Limited',
  INTERNATIONAL_BENEFICIARY_ADDRESS: '12 Steward Street, The Steward Building, London, E1 6FQ, GB',
  INTERNATIONAL_BENEFICIARY_BANK_COUNTRY: 'United Kingdom',
  INTERNATIONAL_ACCOUNT_HOLDER: 'ABEYAANTRIX TECHNOLOGY PRIVATE LIMITED'
};

// Pricing
const PRICING = {
  national: {
    currency: '₹',
    currencyCode: 'INR',
    business: 12000,
    business_plus: 15000,
    enterprise: 1200000,
    white_label: { web: 300000, android: 350000, ios: 400000 },
    addons: { gps: 20000, company: 20000, tally: 20000, tallyAmc: 5000, zoho: 20000, zohoAmc: 5000 }
  },
  international: {
    currency: '$',
    currencyCode: 'USD',
    business: 200,
    business_plus: 250,
    enterprise: 15000,
    white_label: { web: 3600, android: 4200, ios: 4800 },
    addons: { gps: 300, company: 300, tally: 300, tallyAmc: 100, zoho: 300, zohoAmc: 100 }
  }
};

const DURATION_DISCOUNT = { 1: 0, 2: 0.20, 3: 0.30 };

// Features by Plan
const FEATURES = {
  business: [
    'Payments & Expenses',
    'File Management',
    'Labor Attendance & Salary',
    'CRM (Leads & Quotation)',
    'Material Request & Inventory',
    'Task & Sub-task Hierarchy',
    'Issue/Snag List (To-do)',
    'Subcon Work Order & RA Billing',
    'Multiple Roles & Permission'
  ],
  business_plus: [
    'Everything in Business Plan +',
    'Design Management',
    'Bill of Quantity (BOQ) & RA Bills',
    'Budget Control',
    'Central Warehouse',
    'RFQ (Request for Quotation)',
    'Purchase Orders',
    'Assets & Tools',
    'Equipment & Machinery',
    'Staff Payroll',
    'Site Inspection',
    'Multi-Level Approval'
  ],
  enterprise: [
    'Everything in Business+ Plan +',
    'Unlimited Users',
    'GPS Attendance',
    'Custom Roles',
    'Custom Dashboard',
    'Accounting Integration (Zoho, Tally)',
    'Vendor Portal',
    'Client Portal',
    'White Labelled Solution (Add-on)',
    'SAP Integration (Add-on)'
  ]
};

// ============== MAIN HANDLER ==============
function doPost(e) {
  try {
    Logger.log('=== doPost called ===');
    Logger.log('Parameter keys: ' + (e && e.parameters ? Object.keys(e.parameters).join(', ') : 'No parameters'));
    Logger.log('PostData type: ' + (e && e.postData ? e.postData.type : 'No postData'));
    Logger.log('PostData contents length: ' + (e && e.postData && e.postData.contents ? e.postData.contents.length : 0));

    // Handle case when called directly (for testing)
    if (!e) {
      Logger.log('doPost called without event object. Use testGenerate() or testEmail() for testing.');
      return ContentService.createTextOutput(JSON.stringify({
        success: false,
        error: 'doPost requires HTTP POST request. Use testGenerate() or testEmail() for testing.'
      })).setMimeType(ContentService.MimeType.JSON);
    }

    let data;
    const contents = e.postData && e.postData.contents ? e.postData.contents : '';
    const contentType = e.postData && e.postData.type ? e.postData.type : '';

    // Method 1: URL-encoded form body (data=... from form submission)
    if (contents && (contentType.indexOf('application/x-www-form-urlencoded') !== -1 || contents.indexOf('data=') === 0)) {
      Logger.log('Parsing URL-encoded form body...');
      try {
        const params = parseUrlEncodedBody(contents);
        const dataParam = params.data;
        const dataString = Array.isArray(dataParam) ? dataParam[0] : dataParam;
        data = JSON.parse(dataString);
        Logger.log('✅ Parsed JSON from URL-encoded body');
      } catch (parseError) {
        Logger.log('❌ URL-encoded parse error: ' + parseError.toString());
        throw new Error('Invalid JSON in URL-encoded body: ' + parseError.toString());
      }
    }
    // Method 2: Raw JSON body (from fetch with application/json)
    else if (contents) {
      Logger.log('Parsing JSON from raw body...');
      try {
        data = JSON.parse(contents);
        Logger.log('✅ Parsed JSON from raw body');
      } catch (parseError) {
        Logger.log('❌ JSON parse error: ' + parseError.toString());
        throw new Error('Invalid JSON: ' + parseError.toString());
      }
    }
    // Method 3: Parameters (fallback)
    else if (e.parameters && e.parameters.data) {
      Logger.log('Parsing JSON from parameters...');
      try {
        const dataParam = e.parameters.data;
        const dataString = Array.isArray(dataParam) ? dataParam[0] : dataParam;
        data = JSON.parse(dataString);
        Logger.log('✅ Parsed JSON from parameters');
      } catch (parseError) {
        Logger.log('❌ Parameter parse error: ' + parseError.toString());
        throw new Error('Invalid JSON in parameters: ' + parseError.toString());
      }
    } else {
      Logger.log('❌ No data found in request');
      return ContentService.createTextOutput(JSON.stringify({
        success: false,
        error: 'No data received. Check that data is sent as JSON in body or form parameter named "data".'
      })).setMimeType(ContentService.MimeType.JSON);
    }

    Logger.log('Parsed data - Ref: ' + (data.refNumber || 'N/A') + ', Action: ' + (data.action || 'N/A'));
    Logger.log('Client: ' + (data.clientName || 'N/A') + ' (' + (data.clientEmail || 'N/A') + ')');

    const result = generateQuotation(data);
    Logger.log('Result: ' + JSON.stringify(result));

    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    Logger.log('❌ Error in doPost: ' + error.toString());
    Logger.log('Stack: ' + error.stack);
    return ContentService.createTextOutput(JSON.stringify({
      success: false,
      error: error.message,
      stack: error.stack.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

// Parse application/x-www-form-urlencoded body (no Utilities.parseQueryString in Apps Script)
function parseUrlEncodedBody(body) {
  const params = {};
  if (!body) return params;

  const pairs = body.split('&');
  for (let i = 0; i < pairs.length; i++) {
    const pair = pairs[i];
    if (!pair) continue;
    const parts = pair.split('=');
    const rawKey = parts[0] || '';
    const rawValue = parts.slice(1).join('=') || '';
    const key = decodeURIComponent(rawKey.replace(/\+/g, ' '));
    const value = decodeURIComponent(rawValue.replace(/\+/g, ' '));

    if (params[key] === undefined) {
      params[key] = value;
    } else if (Array.isArray(params[key])) {
      params[key].push(value);
    } else {
      params[key] = [params[key], value];
    }
  }
  return params;
}

function doGet(e) {
  return ContentService.createTextOutput('Onsite Quotation Generator API is running.');
}

// ============== QUOTATION GENERATOR ==============
function generateQuotation(data) {
  try {
    Logger.log('Generating quotation for: ' + data.refNumber);
    Logger.log('Salesperson: ' + (data.salesperson || 'Not provided'));
    Logger.log('Client: ' + data.clientName + ' (' + data.clientEmail + ')');
    
    // Calculate amounts
    const calc = calculateAmounts(data);
    
    // Generate PDF
    const pdfBlob = createPDF(data, calc);
    
    // Save to Google Drive
    const file = saveToGoogleDrive(pdfBlob, data);
    Logger.log('PDF saved to Drive: ' + file.getName());
    
    // Send emails
    if (data.action === 'send') {
      Logger.log('Sending emails...');
      sendEmails(data, calc, file);
      Logger.log('Emails sent successfully');
    }
    
    return {
      success: true,
      fileUrl: file.getUrl(),
      fileName: file.getName(),
      message: 'Quotation generated and sent successfully'
    };
  } catch (error) {
    Logger.log('Error in generateQuotation: ' + error.toString());
    return {
      success: false,
      error: error.toString(),
      message: 'Failed to generate quotation: ' + error.toString()
    };
  }
}

// ============== CALCULATIONS ==============
function calculateAmounts(data) {
  const p = PRICING[data.region];
  const c = p.currency;

  let subtotal = 0;
  let addonsTotal = 0;
  let planDesc = '';
  let items = [];

  if (data.plan === 'white_label') {
    planDesc = 'White Label Plan';
    const platforms = data.whiteLabelPlatforms || [];
    platforms.forEach(platform => {
      const amt = p.white_label[platform];
      subtotal += amt;
      const platformName = platform.charAt(0).toUpperCase() + platform.slice(1);
      items.push({
        description: `White Label - ${platformName} Platform`,
        users: '1',
        rate: `${c}${amt.toLocaleString()}`,
        duration: '1 Year',
        amount: amt
      });
    });
  } else if (data.plan === 'enterprise') {
    subtotal = parseFloat(data.customAmount) || p.enterprise;
    planDesc = 'Enterprise Plan';
    items.push({
      description: 'Enterprise Plan - Unlimited Users',
      users: 'Unlimited',
      rate: `${c}${subtotal.toLocaleString()}`,
      duration: '1 Year',
      amount: subtotal
    });
  } else {
    const users = parseInt(data.numUsers) || 3;
    const pricePerUser = p[data.plan];
    const duration = parseInt(data.duration) || 1;
    const durationDiscount = DURATION_DISCOUNT[duration];

    subtotal = pricePerUser * users * duration;
    if (durationDiscount > 0) {
      subtotal = subtotal * (1 - durationDiscount);
    }

    const planName = data.plan === 'business' ? 'Business' : 'Business+';
    planDesc = `${planName} Plan - ${users} Users`;

    items.push({
      description: `${planName} Plan License`,
      users: users,
      rate: `${c}${pricePerUser.toLocaleString()}/user/year`,
      duration: `${duration} Year${duration > 1 ? 's' : ''}`,
      amount: subtotal
    });
  }

  // Calculate addons
  const addons = data.addons || [];
  const addonNames = {
    gps: 'GPS + Facial Recognition',
    company: 'Additional Company',
    tally: 'Tally Integration',
    zoho: 'Zoho Books Integration'
  };
  const duration = parseInt(data.duration) || 1;
  const addonDuration = (data.plan === 'enterprise' || data.plan === 'white_label') ? 1 : duration;

  addons.forEach(addon => {
    if (addon === 'additionalUsers') {
      const count = parseInt(data.additionalUsersCount) || 0;
      const discount = parseFloat(data.additionalUsersDiscount) || 0;
      const pricePerUser = parseFloat(data.specialOfferPerUserPrice) || 0;

      if (count > 0 && pricePerUser > 0) {
        let amt = count * pricePerUser * addonDuration;
        let discountLabel = '';
        if (discount > 0) {
          amt = amt * (1 - discount / 100);
          discountLabel = ` (${discount}% off)`;
        }
        const displayRate = discount > 0
          ? `${c}${(pricePerUser * (1 - discount / 100)).toLocaleString()}/user${discountLabel}`
          : `${c}${pricePerUser.toLocaleString()}/user`;
        addonsTotal += amt;
        items.push({
          description: 'Special Offer - Extra Users',
          users: count,
          rate: displayRate,
          duration: `${addonDuration} Year${addonDuration > 1 ? 's' : ''}`,
          amount: amt
        });
      }
      return;
    }

    let addonAmount = p.addons[addon];
    if (!addonAmount) return;
    let desc = addonNames[addon];
    if (addon === 'tally' || addon === 'zoho') {
      addonAmount += p.addons[addon + 'Amc'];
      desc += ' (incl. AMC)';
    }
    const totalAddonAmount = addonAmount * addonDuration;
    addonsTotal += totalAddonAmount;
    items.push({
      description: desc,
      users: '-',
      rate: `${c}${addonAmount.toLocaleString()}/yr`,
      duration: `${addonDuration} Year${addonDuration > 1 ? 's' : ''}`,
      amount: totalAddonAmount
    });
  });
  
  // Calculate discount
  const discountPct = parseFloat(data.discount) || 0;
  const discountAmt = (subtotal + addonsTotal) * (discountPct / 100);
  
  const afterDiscount = subtotal + addonsTotal - discountAmt;
  const gst = afterDiscount * 0.18;
  const total = afterDiscount + gst;
  
  return {
    currency: c,
    currencyCode: p.currencyCode,
    items: items,
    subtotal: subtotal,
    addonsTotal: addonsTotal,
    discountPct: discountPct,
    discountAmt: discountAmt,
    afterDiscount: afterDiscount,
    gst: gst,
    total: total,
    planDesc: planDesc
  };
}

// ============== PDF GENERATION ==============
function createPDF(data, calc) {
  Logger.log('=== Creating PDF ===');
  Logger.log('Reference: ' + data.refNumber);
  
  try {
    const html = generateHTML(data, calc);
    Logger.log('HTML generated, length: ' + html.length + ' characters');
    
    const blob = HtmlService.createHtmlOutput(html).getBlob();
    Logger.log('PDF blob created, size: ' + blob.getBytes().length + ' bytes');
    
    blob.setName(`Quotation-${data.refNumber}.pdf`);
    Logger.log('✅ PDF created successfully: ' + blob.getName());
    
    return blob;
  } catch (e) {
    Logger.log('❌ Error creating PDF: ' + e.toString());
    throw new Error('Failed to create PDF: ' + e.toString());
  }
}

function generateHTML(data, calc) {
  const c = calc.currency;
  const validDate = new Date();
  validDate.setDate(validDate.getDate() + parseInt(data.validDays));
  
  const salespersonParts = data.salesperson.split('|');
  const salespersonName = salespersonParts[0];
  
  // Payment terms text
  const paymentTermsText = {
    '100_upfront': '100% Upfront before service activation',
    '75_25': '75% Upfront, 25% within 45 days',
    '50_50': '50% Upfront, 50% on Delivery'
  };
  
  // Account selection (international default, optional Indian override)
  const paymentAccount = data.paymentAccount || (data.region === 'international' ? 'international_swift' : 'indian');
  const docTypeLabel = data.docType === 'proforma' ? 'PROFORMA INVOICE' : 'QUOTATION';

  // Items rows
  let itemsHTML = '';
  calc.items.forEach(item => {
    itemsHTML += `
      <tr>
        <td>${item.description}</td>
        <td style="text-align: center;">${item.users}</td>
        <td style="text-align: right;">${item.rate}</td>
        <td style="text-align: center;">${item.duration}</td>
        <td style="text-align: right;">${c}${item.amount.toLocaleString()}</td>
      </tr>
    `;
  });
  
  // Features list
  const features = FEATURES[data.plan] || FEATURES.business_plus;
  let featuresHTML = '';
  for (let i = 0; i < features.length; i += 2) {
    featuresHTML += `
      <tr>
        <td style="padding: 6px 10px;">✓ ${features[i]}</td>
        <td style="padding: 6px 10px;">${features[i+1] ? '✓ ' + features[i+1] : ''}</td>
      </tr>
    `;
  }
  
  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    @page { margin: 40px; }
    @media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { 
      font-family: 'Segoe UI', Arial, sans-serif; 
      font-size: 11px; 
      line-height: 1.4; 
      color: #1a1a1a;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    .header-table { 
      width: 100%;
      border-bottom: 3px solid #1a0b50; 
      margin-bottom: 20px; 
      border-collapse: collapse;
    }
    .header-table td { 
      vertical-align: top;
      padding-bottom: 15px;
    }
    .header-right {
      text-align: right;
      width: 240px;
    }
    .logo { font-size: 24px; font-weight: 700; color: #1a0b50; }
    .tagline { font-size: 12px; color: #64748b; margin-top: 2px; }
    .company-details { font-size: 10px; color: #64748b; margin-top: 8px; line-height: 1.5; }
    .doc-type { 
      display: inline-block;
      text-align: right; 
      background: #1a0b50; 
      color: white; 
      padding: 15px 20px; 
      border-radius: 8px;
    }
    .doc-type h1 { font-size: 20px; margin-bottom: 5px; }
    .doc-type p { font-size: 11px; opacity: 0.9; }
    
    .client-box { 
      background: #f8fafc; 
      border: 1px solid #e2e8f0; 
      border-radius: 8px; 
      padding: 15px; 
      margin-bottom: 20px; 
    }
    .client-box h3 { 
      font-size: 10px; 
      text-transform: uppercase; 
      color: #64748b; 
      margin-bottom: 8px; 
      letter-spacing: 0.5px;
    }
    .client-name { font-size: 14px; font-weight: 600; color: #1a0b50; }
    .client-company { font-size: 12px; color: #334155; }
    .client-location { font-size: 11px; color: #64748b; }
    
    .section-title { 
      font-size: 12px; 
      font-weight: 600; 
      color: #1a0b50; 
      margin: 20px 0 10px; 
      padding-bottom: 5px;
      border-bottom: 2px solid #e2e8f0;
    }
    
    table.items { 
      width: 100%; 
      border-collapse: collapse; 
      margin-bottom: 15px; 
      border: 1px solid #e2e8f0;
    }
    table.items th { 
      background: #1a0b50; 
      color: white; 
      padding: 10px; 
      text-align: left; 
      font-size: 10px;
      text-transform: uppercase;
    }
    table.items td { 
      padding: 10px; 
      border-bottom: 1px solid #e2e8f0; 
    }
    table.items tr:nth-child(even) { background: #f8fafc; }
    
    .totals-table { 
      width: 350px; 
      margin-left: auto; 
      margin-top: 15px;
      border-collapse: collapse;
    }
    .totals-table td {
      padding: 8px 0;
      border-bottom: 1px solid #e2e8f0;
    }
    .totals-table td.amount {
      text-align: right;
      width: 140px;
    }
    .totals-table .total-row td {
      background: #1a0b50;
      color: white;
      padding: 12px 15px;
      font-size: 14px;
      font-weight: 700;
      border-bottom: none;
    }
    
    .features-box { 
      background: #f8fafc; 
      border: 1px solid #e2e8f0; 
      border-radius: 8px; 
      padding: 15px; 
      margin: 20px 0; 
    }
    .features-box h4 { 
      font-size: 11px; 
      color: #1a0b50; 
      margin-bottom: 10px; 
    }
    table.features { width: 100%; }
    table.features td { 
      font-size: 10px; 
      color: #334155; 
      width: 50%;
    }
    
    .terms-box { 
      background: #fffbeb; 
      border: 1px solid #fcd34d; 
      border-radius: 8px; 
      padding: 15px; 
      margin: 20px 0; 
    }
    .terms-box h4 { 
      font-size: 11px; 
      color: #92400e; 
      margin-bottom: 8px; 
    }
    .terms-box ul { 
      font-size: 10px; 
      color: #78350f; 
      padding-left: 15px; 
    }
    .terms-box li { margin-bottom: 4px; }
    
    .bank-box { 
      background: #f0fdf4; 
      border: 1px solid #86efac; 
      border-radius: 8px; 
      padding: 15px; 
      margin: 20px 0; 
    }
    .bank-box h4 { 
      font-size: 11px; 
      color: #166534; 
      margin-bottom: 8px; 
    }
    .bank-details { 
      font-size: 10px; 
      color: #14532d; 
      line-height: 1.6; 
    }
    
    .footer { 
      margin-top: 30px; 
      padding-top: 15px; 
      border-top: 2px solid #e2e8f0; 
      font-size: 9px; 
      color: #64748b; 
      text-align: center; 
    }
    .footer a { color: #1a0b50; text-decoration: none; }
    
    .highlight { color: #c73e5a; font-weight: 600; }
  </style>
</head>
<body>
  <table class="header-table" style="width:100%;border-bottom:3px solid #1a0b50;margin-bottom:20px;border-collapse:collapse;">
    <tr>
      <td class="header-left">
        <div class="logo">
          <svg width="40" height="40" viewBox="0 0 100 100" style="vertical-align: middle; margin-right: 10px; display: inline-block;">
            <circle cx="50" cy="50" r="42" fill="none" stroke="#c73e5a" stroke-width="6"/>
            <path d="M60 25 L32 50 L48 50 L38 75 L68 50 L52 50 Z" fill="#c73e5a"/>
          </svg>
          ${CONFIG.BRAND_NAME}
        </div>
        <div class="tagline">Construction Management Software</div>
        <div class="company-details">
          ${CONFIG.COMPANY_NAME}<br>
          ${CONFIG.ADDRESS}<br>
          GSTIN: ${CONFIG.GSTIN} | PAN: ${CONFIG.PAN}<br>
          📞 ${CONFIG.PHONE} | ✉️ ${CONFIG.EMAIL}
        </div>
      </td>
      <td class="header-right">
        <div class="doc-type" style="background:#1a0b50;color:#ffffff;padding:15px 20px;border-radius:8px;display:inline-block;text-align:right;">
          <h1>${docTypeLabel}</h1>
          <p><strong>Ref:</strong> ${data.refNumber}</p>
          <p><strong>Date:</strong> ${new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</p>
          <p><strong>Valid Till:</strong> ${validDate.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</p>
        </div>
      </td>
    </tr>
  </table>
  
  <div class="client-box" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:15px;margin-bottom:20px;">
    <h3>Quotation For</h3>
    <div class="client-name">${data.clientName}</div>
    <div class="client-company">${data.companyName}</div>
    ${data.clientGst ? `<div class="client-location">GSTIN: ${data.clientGst}</div>` : ''}
    <div class="client-location">${data.clientLocation || ''}</div>
    ${data.clientEmail ? `<div class="client-location">✉️ ${data.clientEmail}</div>` : ''}
  </div>
  
  <div class="section-title">📦 ${calc.planDesc}</div>
  
  <table class="items" style="width:100%;border-collapse:collapse;margin-bottom:15px;border:1px solid #e2e8f0;">
    <thead>
      <tr>
          <th style="width: 40%;background:#1a0b50;color:#ffffff;padding:10px;text-align:left;font-size:10px;text-transform:uppercase;">Description</th>
          <th style="width: 12%;background:#1a0b50;color:#ffffff;padding:10px;text-align:center;font-size:10px;text-transform:uppercase;">Users</th>
          <th style="width: 18%;background:#1a0b50;color:#ffffff;padding:10px;text-align:right;font-size:10px;text-transform:uppercase;">Rate</th>
          <th style="width: 12%;background:#1a0b50;color:#ffffff;padding:10px;text-align:center;font-size:10px;text-transform:uppercase;">Duration</th>
          <th style="width: 18%;background:#1a0b50;color:#ffffff;padding:10px;text-align:right;font-size:10px;text-transform:uppercase;">Amount</th>
      </tr>
    </thead>
    <tbody>
      ${itemsHTML}
    </tbody>
  </table>
  
  <table class="totals-table" style="width:350px;margin-left:auto;margin-top:15px;border-collapse:collapse;">
    <tr>
      <td style="padding:8px 0;border-bottom:1px solid #e2e8f0;">Sub-Total</td>
      <td class="amount" style="padding:8px 0;border-bottom:1px solid #e2e8f0;text-align:right;width:140px;">${c}${(calc.subtotal + calc.addonsTotal).toLocaleString()}</td>
    </tr>
    ${calc.discountAmt > 0 ? `
    <tr>
      <td style="padding:8px 0;border-bottom:1px solid #e2e8f0;">Discount (${calc.discountPct}%)</td>
      <td class="amount highlight" style="padding:8px 0;border-bottom:1px solid #e2e8f0;text-align:right;width:140px;">-${c}${calc.discountAmt.toLocaleString()}</td>
    </tr>
    ` : ''}
    <tr>
      <td style="padding:8px 0;border-bottom:1px solid #e2e8f0;">GST (18%)</td>
      <td class="amount" style="padding:8px 0;border-bottom:1px solid #e2e8f0;text-align:right;width:140px;">${c}${Math.round(calc.gst).toLocaleString()}</td>
    </tr>
    <tr class="total-row">
      <td style="background:#1a0b50;color:#ffffff;padding:12px 15px;font-size:14px;font-weight:700;">PAYABLE AMOUNT</td>
      <td class="amount" style="background:#1a0b50;color:#ffffff;padding:12px 15px;font-size:14px;font-weight:700;text-align:right;width:140px;">${c}${Math.round(calc.total).toLocaleString()}</td>
    </tr>
  </table>
  
  <div class="features-box">
    <h4>📋 INCLUDED FEATURES (${data.plan === 'business' ? 'Business' : data.plan === 'business_plus' ? 'Business+' : 'Enterprise'} Plan)</h4>
    <table class="features">
      ${featuresHTML}
    </table>
  </div>
  
  <div class="terms-box">
    <h4>📜 TERMS & CONDITIONS</h4>
    <ul>
      <li><strong>Payment:</strong> ${paymentTermsText[data.paymentTerms] || '100% Upfront before service activation'}</li>
      <li><strong>Validity:</strong> This quotation is valid for ${data.validDays} days from the date of issue.</li>
      <li><strong>Activation:</strong> Premium services activated within 2 hours of receiving payment.</li>
      <li><strong>Support:</strong> AWS Server, Training, Setup & Onboarding Support included.</li>
      <li><strong>Renewal:</strong> Auto-renewal unless cancelled 7 days before expiry.</li>
      ${data.specialNotes ? `<li><strong>Special Notes:</strong> ${data.specialNotes}</li>` : ''}
    </ul>
    <div style="margin-top: 8px; font-size: 10px; color: #78350f;">
      Terms of Service: <a href="${CONFIG.WEBSITE}/terms/">onsiteteams.com/terms</a>
    </div>
  </div>
  
  <div class="bank-box">
    <h4>🏦 BANK DETAILS FOR PAYMENT</h4>
    <div class="bank-details">
      ${paymentAccount === 'international_swift' ? `
        <strong>International SWIFT account</strong><br>
        <strong>Payment method:</strong> ${CONFIG.INTERNATIONAL_PAYMENT_METHOD}<br>
        <strong>IBAN (Account number):</strong> ${CONFIG.INTERNATIONAL_IBAN}<br>
        <strong>BIC/SWIFT code:</strong> ${CONFIG.INTERNATIONAL_SWIFT}<br>
        <strong>Account type:</strong> ${CONFIG.INTERNATIONAL_ACCOUNT_TYPE}<br>
        <strong>Bank name:</strong> ${CONFIG.INTERNATIONAL_BANK_NAME}<br>
        <strong>Beneficiary address:</strong> ${CONFIG.INTERNATIONAL_BENEFICIARY_ADDRESS}<br>
        <strong>Beneficiary bank country:</strong> ${CONFIG.INTERNATIONAL_BENEFICIARY_BANK_COUNTRY}<br>
        <strong>Account holder name:</strong> ${CONFIG.INTERNATIONAL_ACCOUNT_HOLDER}
      ` : `
        <strong>Account Name:</strong> ${CONFIG.COMPANY_NAME}<br>
        <strong>Bank:</strong> ${CONFIG.BANK_NAME}<br>
        <strong>Account No:</strong> ${CONFIG.ACCOUNT_NO}<br>
        <strong>IFSC Code:</strong> ${CONFIG.IFSC}<br>
        <strong>UPI ID:</strong> ${CONFIG.UPI}
      `}
    </div>
  </div>
  
  <div class="footer">
    <strong>${CONFIG.BRAND_NAME}</strong> - A product of ${CONFIG.COMPANY_NAME}<br>
    🌐 <a href="${CONFIG.WEBSITE}">${CONFIG.WEBSITE}</a> | 📞 ${CONFIG.PHONE} | ✉️ ${CONFIG.EMAIL}<br><br>
    <em>Prepared by: ${salespersonName}</em>
  </div>
</body>
</html>
  `;
}

// ============== GOOGLE DRIVE ==============
function saveToGoogleDrive(pdfBlob, data) {
  Logger.log('=== Saving to Google Drive ===');
  Logger.log('Region: ' + data.region);
  
  // Select folder based on region (National or International)
  const folderId = data.region === 'international' 
    ? CONFIG.FOLDER_ID_INTERNATIONAL 
    : CONFIG.FOLDER_ID_NATIONAL;
  
  Logger.log('Folder ID: ' + folderId);
  Logger.log('Folder type: ' + (data.region === 'international' ? 'International' : 'National'));
  
  try {
    const folder = DriveApp.getFolderById(folderId);
    Logger.log('Folder found: ' + folder.getName());
    
    const fileName = `Quotation-${data.refNumber}-${data.companyName.replace(/[^a-zA-Z0-9]/g, '_')}.pdf`;
    Logger.log('Creating file: ' + fileName);
    Logger.log('PDF blob size: ' + pdfBlob.getBytes().length + ' bytes');
    
    const file = folder.createFile(pdfBlob);
    file.setName(fileName);
    
    Logger.log('✅ File created successfully!');
    Logger.log('File ID: ' + file.getId());
    Logger.log('File URL: ' + file.getUrl());
    
    return file;
  } catch (e) {
    Logger.log('❌ Error saving to Drive: ' + e.toString());
    Logger.log('Error stack: ' + e.stack);
    throw new Error('Failed to save PDF to Google Drive: ' + e.toString());
  }
}

// ============== EMAIL ==============
function sendEmails(data, calc, file) {
  // Extract salesperson info - use provided fields or parse from salesperson string
  let salespersonName, salespersonEmail;
  
  if (data.salespersonName && data.salespersonEmail) {
    // Use directly provided fields (preferred)
    salespersonName = data.salespersonName;
    salespersonEmail = data.salespersonEmail;
  } else if (data.salesperson && data.salesperson.includes('|')) {
    // Parse from "Name|email" format
    const salespersonParts = data.salesperson.split('|');
    salespersonName = salespersonParts[0];
    salespersonEmail = salespersonParts[1];
  } else {
    // Fallback to default
    salespersonName = 'Sales Team';
    salespersonEmail = CONFIG.EMAIL;
  }
  
  // Log for debugging
  Logger.log('Sending emails to:');
  Logger.log('Salesperson: ' + salespersonName + ' <' + salespersonEmail + '>');
  Logger.log('Client: ' + data.clientEmail);
  
  const c = calc.currency;
  
  // Email subject
  const docTypeLabelText = data.docType === 'proforma' ? 'Proforma Invoice' : 'Quotation';
  const subject = `Onsite ${docTypeLabelText} ${data.refNumber} - ${data.companyName}`;
  
  // Email body for salesperson (internal)
  const salesEmailBody = `
Hi ${salespersonName},

A new ${docTypeLabelText.toLowerCase()} has been generated:

Reference: ${data.refNumber}
Client: ${data.clientName} (${data.companyName})
Plan: ${calc.planDesc}
Amount: ${c}${Math.round(calc.total).toLocaleString()} (incl. GST)

PDF attached. Also saved to Google Drive.

Onsite Quotation Generator
  `;

  const salesEmailHtml = `
  <p>Hi <b>${salespersonName}</b>,</p>
  <p><b>A new ${docTypeLabelText.toLowerCase()} has been generated:</b></p>
  <ul>
    <li><b>Reference:</b> ${data.refNumber}</li>
    <li><b>Client:</b> ${data.clientName} (${data.companyName})</li>
    <li><b>Plan:</b> ${calc.planDesc}</li>
    <li><b>Amount:</b> ${c}${Math.round(calc.total).toLocaleString()} (incl. GST)</li>
  </ul>
  <p><b>PDF attached.</b> Also saved to Google Drive.</p>
  <p>—<br>Onsite Quotation Generator</p>
  `;
  
  // Email body for client (external)
  const paymentTermsText = {
    '100_upfront': '100% upfront before service activation',
    '75_25': '75% upfront and 25% within 45 days',
    '50_50': '50% upfront and 50% on delivery'
  };

  const clientEmailBody = `
Hi ${data.clientName},

Thank you for your interest in Onsite. Please find your ${docTypeLabelText.toLowerCase()} attached.

Reference: ${data.refNumber}
Plan: ${calc.planDesc}
Total: ${c}${Math.round(calc.total).toLocaleString()} (incl. GST)

Why Onsite
- 10,000+ companies use Onsite
- 50,000+ projects across 10+ countries
- 4.5/5 customer satisfaction
- 7-10% reduction in project costs
- Up to 25% faster execution
- Real-time site updates via mobile + web

What you get
- Planning & Gantt scheduling
- BOQ, budget & cost control
- RFQs, POs, GRNs & inventory
- GPS-based attendance & payroll
- DPRs, snag lists, tasks & MOM
- Subcontractor work orders & RA billing
- Vendor, client & contract management
- P&L, billing & financial tracking
- Design management & approvals

Next steps
1) Confirm the ${docTypeLabelText.toLowerCase()}
2) Share required details: founder name, company address, VAT/GST (if any), activation number
3) We schedule onboarding and training

Payment terms: ${paymentTermsText[data.paymentTerms] || '100% upfront before service activation'}
Terms of Service: ${CONFIG.WEBSITE}/terms/

If you have any questions, reply to this email and we will help immediately.

Best regards,
${salespersonName}
Product Expert
Onsite
${CONFIG.WEBSITE}
  `;

  const clientEmailHtml = `
  <p>Hi <b>${data.clientName}</b>,</p>
  <p>Thank you for your interest in <b>Onsite</b>. Please find your <b>${docTypeLabelText.toLowerCase()}</b> attached.</p>
  <p><b>Reference:</b> ${data.refNumber}<br>
  <b>Plan:</b> ${calc.planDesc}<br>
  <b>Total:</b> ${c}${Math.round(calc.total).toLocaleString()} (incl. GST)</p>

  <p><b>Why Onsite</b></p>
  <ul>
    <li>10,000+ companies use Onsite</li>
    <li>50,000+ projects across 10+ countries</li>
    <li>4.5/5 customer satisfaction</li>
    <li>7–10% reduction in project costs</li>
    <li>Up to 25% faster execution</li>
    <li>Real-time site updates via mobile + web</li>
  </ul>

  <p><b>What you get</b></p>
  <ul>
    <li>Planning & Gantt scheduling</li>
    <li>BOQ, budget & cost control</li>
    <li>RFQs, POs, GRNs & inventory</li>
    <li>GPS-based attendance & payroll</li>
    <li>DPRs, snag lists, tasks & MOM</li>
    <li>Subcontractor work orders & RA billing</li>
    <li>Vendor, client & contract management</li>
    <li>P&L, billing & financial tracking</li>
    <li>Design management & approvals</li>
  </ul>

  <p><b>Next steps</b></p>
  <ol>
    <li>Confirm the ${docTypeLabelText.toLowerCase()}</li>
    <li>Share required details: founder name, company address, VAT/GST (if any), activation number</li>
    <li>We schedule onboarding and training</li>
  </ol>

  <p><b>Payment terms:</b> ${paymentTermsText[data.paymentTerms] || '100% upfront before service activation'}<br>
  <b>Terms of Service:</b> <a href="${CONFIG.WEBSITE}/terms/">${CONFIG.WEBSITE}/terms/</a></p>

  <p>If you have any questions, reply to this email and we will help immediately.</p>

  <p>Best regards,<br>
  <b>${salespersonName}</b><br>
  Product Expert<br>
  Onsite<br>
  <a href="${CONFIG.WEBSITE}">${CONFIG.WEBSITE}</a></p>
  `;
  
  // Validate emails
  Logger.log('Validating emails...');
  Logger.log('Salesperson email: ' + salespersonEmail);
  Logger.log('Client email: ' + data.clientEmail);
  
  if (!salespersonEmail || !salespersonEmail.includes('@')) {
    Logger.log('❌ Invalid salesperson email: ' + salespersonEmail);
    throw new Error('Invalid salesperson email: ' + salespersonEmail);
  }
  if (!data.clientEmail || !data.clientEmail.includes('@')) {
    Logger.log('❌ Invalid client email: ' + data.clientEmail);
    throw new Error('Invalid client email: ' + data.clientEmail);
  }
  
  Logger.log('✅ Email validation passed');
  
  // Send to salesperson
  Logger.log('Attempting to send email to salesperson...');
  try {
    MailApp.sendEmail({
      to: salespersonEmail,
      subject: subject,
      body: salesEmailBody,
      htmlBody: salesEmailHtml,
      attachments: [file.getAs(MimeType.PDF)]
    });
    Logger.log('✅ Email sent to salesperson: ' + salespersonEmail);
  } catch (e) {
    Logger.log('❌ Error sending to salesperson: ' + e.toString());
    Logger.log('Error stack: ' + e.stack);
    throw new Error('Failed to send email to salesperson: ' + e.toString());
  }
  
  // Send to client
  Logger.log('Attempting to send email to client...');
  Logger.log('Client email address: ' + data.clientEmail);
  Logger.log('Client email type: ' + typeof data.clientEmail);
  
  try {
    MailApp.sendEmail({
      to: data.clientEmail,
      replyTo: salespersonEmail,
      subject: subject,
      body: clientEmailBody,
      htmlBody: clientEmailHtml,
      attachments: [file.getAs(MimeType.PDF)]
    });
    Logger.log('✅ Email sent to client: ' + data.clientEmail);
  } catch (e) {
    Logger.log('❌ Error sending to client: ' + e.toString());
    Logger.log('Error details: ' + JSON.stringify(e));
    Logger.log('Error stack: ' + e.stack);
    // Don't throw - log the error but continue
    Logger.log('⚠️ Continuing despite client email error...');
    // Still throw so user knows
    throw new Error('Failed to send email to client: ' + e.toString());
  }
  
  Logger.log('✅ Both emails sent successfully!');
}

// ============== TEST FUNCTION ==============
function testGenerate() {
  const testData = {
    refNumber: 'ONS-2026-TEST',
    salesperson: 'Sumit|dhruv.tomar@onsiteteams.com',
    salespersonName: 'Sumit',
    salespersonEmail: 'dhruv.tomar@onsiteteams.com', // Salesperson email
    region: 'national',
    validDays: '7',
    clientName: 'Mr. Test User',
    companyName: 'Test Company Pvt Ltd',
    clientEmail: 'aiwithdhruv@gmail.com', // Client email - CHANGE THIS TO YOUR EMAIL
    clientPhone: '+91 98765 43210',
    clientLocation: 'Bangalore, Karnataka',
    plan: 'business_plus',
    numUsers: '3',
    duration: '1',
    customAmount: '',
    addons: [],
    discount: '0',
    paymentTerms: '100_upfront',
    specialNotes: 'Test quotation',
    action: 'send' // Change to 'send' to test email sending
  };
  
  Logger.log('=== TESTING QUOTATION GENERATOR ===');
  const result = generateQuotation(testData);
  Logger.log('Test result: ' + JSON.stringify(result));
  return result;
}

// Quick test - just check if folders exist
function testFolders() {
  try {
    const natFolder = DriveApp.getFolderById(CONFIG.FOLDER_ID_NATIONAL);
    Logger.log('National folder found: ' + natFolder.getName());
    
    const intFolder = DriveApp.getFolderById(CONFIG.FOLDER_ID_INTERNATIONAL);
    Logger.log('International folder found: ' + intFolder.getName());
    
    return '✅ Both folders accessible';
  } catch (e) {
    Logger.log('❌ Error: ' + e.toString());
    return '❌ Error: ' + e.toString();
  }
}

// Simple email test - sends test email to yourself
function testEmail() {
  try {
    const testEmail = Session.getActiveUser().getEmail(); // Your email
    Logger.log('Sending test email to: ' + testEmail);
    
    MailApp.sendEmail({
      to: testEmail,
      subject: 'Onsite Quotation Generator - Test Email',
      body: 'If you receive this, email sending is working! ✅'
    });
    
    Logger.log('✅ Test email sent successfully!');
    return '✅ Test email sent to: ' + testEmail;
  } catch (e) {
    Logger.log('❌ Error sending test email: ' + e.toString());
    return '❌ Error: ' + e.toString();
  }
}

// Test International folder - saves PDF to International folder
function testInternational() {
  const testData = {
    refNumber: 'ONS-2026-INT-TEST',
    salesperson: 'Sumit|dhruv.tomar@onsiteteams.com',
    salespersonName: 'Sumit',
    salespersonEmail: 'dhruv.tomar@onsiteteams.com',
    region: 'international', // ← INTERNATIONAL!
    validDays: '7',
    clientName: 'International Test Client',
    companyName: 'Test Company International',
    clientEmail: 'aiwithdhruv@gmail.com',
    clientPhone: '+1 555-1234',
    clientLocation: 'New York, USA',
    plan: 'business_plus',
    numUsers: '5',
    duration: '1',
    customAmount: '',
    addons: [],
    discount: '0',
    paymentTerms: '100_upfront',
    specialNotes: 'International test quotation',
    action: 'send'
  };
  
  Logger.log('=== TESTING INTERNATIONAL QUOTATION ===');
  const result = generateQuotation(testData);
  Logger.log('Test result: ' + JSON.stringify(result));
  Logger.log('Check International folder for PDF: ' + result.fileUrl);
  return result;
}

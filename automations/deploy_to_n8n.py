#!/usr/bin/env python3
"""
Deploy all 6 Onsite Phase 1 automations to n8n as scheduled workflows.

Each workflow = Schedule Trigger → Code Node (JavaScript with all logic).
Creates workflows as INACTIVE so you can review before activating.

Usage:
  python3 deploy_to_n8n.py          # Deploy all 6
  python3 deploy_to_n8n.py 1        # Deploy specific one
  python3 deploy_to_n8n.py --list   # List existing Onsite workflows
"""

import json
import os
import sys
import urllib.request

# Load .env file (same directory as this script)
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

N8N_HOST = os.environ.get("N8N_HOST", "https://n8n.srv1184808.hstgr.cloud")
N8N_API_KEY = os.environ["N8N_API_KEY"]

# === SHARED JAVASCRIPT HELPERS ===
# This gets prepended to every Code node
SHARED_JS = r"""
// === ONSITE CONFIG ===
const Z = {
  cid: '%ZOHO_CID%',
  cs: '%ZOHO_CS%',
  rt: '%ZOHO_RT%'
};
const G = {
  k: '%GALLABOX_KEY%',
  s: '%GALLABOX_SECRET%',
  ch: '%GALLABOX_CHANNEL%'
};
const MGR = {Sumit:'918291400026',Akshansh:'919654225317',Dhruv:'918770101822'};
const REPS = {Sunil:'919289602555',Anjali:'917020774603',Bhavya:'919900425676',Mohan:'918220494443',Gayatri:'919993786319',Shailendra:'919589613771','Amit U':'918762879435',Hitangi:'919082286699','Amit Kumar':'916263582436'};
const PRE_SALES = {Jyoti:'918528001207',Shruti:'919084525155'};
const ALL_TEAM = {...REPS, ...PRE_SALES};

// CRM "Deal Owner" field → API name is Leads_Owner (Zoho naming quirk) → short name mapping
const CRM_OWNER_MAP = {
  'Sunil Demo':'Sunil', 'Sunil':'Sunil',
  'Anjali Bajaj':'Anjali', 'Anjali':'Anjali',
  'Bhavya Pattegudde Janappa':'Bhavya', 'Bhavya P Janappa':'Bhavya', 'Pattegudde Janappa':'Bhavya', 'Bhavya':'Bhavya',
  'Mohan C':'Mohan', 'Mohan':'Mohan',
  'Gayatri Surlkar':'Gayatri', 'Gayatri':'Gayatri',
  'Shailendra Gour':'Shailendra', 'Shailendra':'Shailendra',
  'Amit B Udagatti':'Amit U', 'Amit Udagatti':'Amit U', 'Amit Balasaheb Udagatti':'Amit U',
  'Hitangi Arora':'Hitangi', 'Hitangi':'Hitangi',
  'Amit Kumar':'Amit Kumar',
  'Desi Yulia':'Desi', 'Desi':'Desi',
  'Jyoti':'Jyoti', 'Shruti':'Shruti', 'Chadni':'Chadni',
  'Sumit':'Sumit', 'Akshansh':'Akshansh', 'Dhruv':'Dhruv',
  'Team':'Team'
};

// TEST MODE: set true to send all messages to Dhruv only
const TEST_MODE = false;
const TEST_PHONE = '918770101822';

// MONITOR MODE: CC all messages to Dhruv so he can verify delivery
// Set false once everything is confirmed working
const MONITOR_MODE = true;
const MONITOR_PHONE = '918770101822';

// Date helpers
const pad = n => String(n).padStart(2, '0');
const now = new Date();
const TODAY = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}`;
let MONTH_START = `${now.getFullYear()}-${pad(now.getMonth()+1)}-01`;
let MONTH_NAME = now.toLocaleString('en-US', {month:'long', year:'numeric'});
let MONTH_END = TODAY;
const DAY_NUM = now.getDate();

// Month parser — detects "feb", "january", "last month" etc. in message text
function parseMonth(text) {
  if (!text) return null;
  const t = text.toLowerCase();
  const months = {jan:0,january:0,feb:1,february:1,mar:2,march:2,apr:3,april:3,may:4,jun:5,june:5,jul:6,july:6,aug:7,august:7,sep:8,september:8,oct:9,october:9,nov:10,november:10,dec:11,december:11};
  // Check "last month"
  if (/\blast\s*month\b/.test(t)) {
    const d = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const lastDay = new Date(d.getFullYear(), d.getMonth() + 1, 0);
    return {start:`${d.getFullYear()}-${pad(d.getMonth()+1)}-01`, end:`${lastDay.getFullYear()}-${pad(lastDay.getMonth()+1)}-${pad(lastDay.getDate())}`, name:d.toLocaleString('en-US',{month:'long',year:'numeric'})};
  }
  for (const [key, mo] of Object.entries(months)) {
    if (new RegExp('\\b' + key + '\\b').test(t)) {
      const yr = mo > now.getMonth() ? now.getFullYear() - 1 : now.getFullYear();
      const d = new Date(yr, mo, 1);
      const lastDay = new Date(yr, mo + 1, 0);
      const isCurrentMonth = (mo === now.getMonth() && yr === now.getFullYear());
      return {start:`${yr}-${pad(mo+1)}-01`, end: isCurrentMonth ? TODAY : `${lastDay.getFullYear()}-${pad(lastDay.getMonth()+1)}-${pad(lastDay.getDate())}`, name:d.toLocaleString('en-US',{month:'long',year:'numeric'})};
    }
  }
  return null;
}

function daysAgo(n) {
  const d = new Date(now - n * 86400000);
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
}

// Format INR number: 1234567 → "12,34,567"
function fmtINR(n) {
  const s = String(Math.round(n));
  if (s.length <= 3) return s;
  const last3 = s.slice(-3);
  const rest = s.slice(0, -3);
  return rest.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + ',' + last3;
}

// HTTP helper
const http = this.helpers.httpRequest.bind(this.helpers);

// Get Zoho token (lazy — only fail if actually needed)
let token = null;
async function getToken() {
  if (token) return token;
  const _tb = `grant_type=refresh_token&client_id=${Z.cid}&client_secret=${Z.cs}&refresh_token=${Z.rt}`;
  const _tr = await http({method:'POST', url:'https://accounts.zoho.in/oauth/v2/token', body:_tb, headers:{'Content-Type':'application/x-www-form-urlencoded'}});
  token = (typeof _tr === 'string' ? JSON.parse(_tr) : _tr).access_token;
  return token;
}

// COQL query
async function q(query) {
  try {
    const t = await getToken();
    const r = await http({method:'POST', url:'https://www.zohoapis.in/crm/v7/coql',
      headers:{Authorization:`Zoho-oauthtoken ${t}`, 'Content-Type':'application/json'},
      body: JSON.stringify({select_query: query})});
    return typeof r === 'string' ? JSON.parse(r) : r;
  } catch(e) { return {error: e.message}; }
}

async function qCount(query) {
  const d = await q(query);
  return d?.data?.[0]?.total || d?.data?.[0]?.c || 0;
}

async function qPage(query, max=2000) {
  const all = [];
  for (let off = 0; off < max; off += 200) {
    const d = await q(`${query} LIMIT ${off}, 200`);
    if (d?.data) { all.push(...d.data); if (!d?.info?.more_records) break; }
    else break;
  }
  return all;
}

// Send WhatsApp template (opens 24h session window — needed for first msg of day)
async function waTemplate(phone, name) {
  if (TEST_MODE) { phone = TEST_PHONE; name = 'Dhruv [TEST]'; }
  try {
    return await http({method:'POST', url:'https://server.gallabox.com/devapi/messages/whatsapp',
      headers:{apiKey:G.k, apiSecret:G.s, 'Content-Type':'application/json'},
      body: JSON.stringify({channelId:G.ch, channelType:'whatsapp', recipient:{name, phone},
        whatsapp:{type:'template', template:{templateName:'onsite_morning_kickoff', bodyValues:{'1':name}}}})});
  } catch(e) { return {status:'FAILED', error:e.message}; }
}

// WhatsApp sender (respects TEST_MODE + MONITOR_MODE)
async function wa(phone, msg, name='Team') {
  if (TEST_MODE) { phone = TEST_PHONE; name = 'Dhruv [TEST]'; }
  if (msg.length > 4096) msg = msg.slice(0, 4090) + '\n...';
  try {
    const r = await http({method:'POST', url:'https://server.gallabox.com/devapi/messages/whatsapp',
      headers:{apiKey:G.k, apiSecret:G.s, 'Content-Type':'application/json'},
      body: JSON.stringify({channelId:G.ch, channelType:'whatsapp', recipient:{name, phone},
        whatsapp:{type:'text', text:{body:msg}}})});
    // CC to monitor (skip if already sending to monitor, or in TEST_MODE)
    if (MONITOR_MODE && !TEST_MODE && phone !== MONITOR_PHONE) {
      const monMsg = `[TO: ${name}]\n${msg}`;
      await http({method:'POST', url:'https://server.gallabox.com/devapi/messages/whatsapp',
        headers:{apiKey:G.k, apiSecret:G.s, 'Content-Type':'application/json'},
        body: JSON.stringify({channelId:G.ch, channelType:'whatsapp',
          recipient:{name:'Dhruv [MONITOR]', phone:MONITOR_PHONE},
          whatsapp:{type:'text', text:{body:monMsg.slice(0,4096)}}})});
    }
    return r;
  } catch(e) { return {status:'FAILED', error:e.message}; }
}

async function waAll(team, msg) {
  if (TEST_MODE) { await wa(TEST_PHONE, msg, 'Dhruv [TEST]'); return; }
  for (const [name, phone] of Object.entries(team)) await wa(phone, msg, name);
}
"""

# === AUTOMATION-SPECIFIC JAVASCRIPT ===

AUTO_1_JS = r"""
// === AUTOMATION 1: Hourly Follow-Up Alerts ===
// Runs every hour 8 AM - 8 PM IST Mon-Sat
// PERSONALIZED — each rep gets ONLY their own leads with exact follow-up time
// Managers get full team view grouped by rep

const THREE_DAYS_AGO = daysAgo(3);
const istNow = new Date(now.getTime() + 5.5 * 3600000); // UTC → IST
const currentHour = istNow.getHours();
const nextHourIST = currentHour + 1;

// --- Helper: format Lead_Task datetime → "2:30 PM" ---
function fmtTime(dt) {
  if (!dt) return '';
  const m = String(dt).match(/T(\d{2}):(\d{2})/);
  if (!m) return '';
  let h = parseInt(m[1]), mn = m[2];
  const ap = h >= 12 ? 'PM' : 'AM';
  if (h > 12) h -= 12;
  if (h === 0) h = 12;
  return `${h}:${mn} ${ap}`;
}

// --- Helper: get Deal Owner from Leads_Owner field → short name ---
function getDealOwner(l) {
  const raw = String(l.Leads_Owner || '').trim();
  return CRM_OWNER_MAP[raw] || raw || 'Unassigned';
}

// --- Helper: find rep phone from short name ---
const ALL_PHONES = {...REPS, ...PRE_SALES};
function findRep(shortName) {
  if (!shortName || shortName === 'Team' || shortName === 'Unassigned') return null;
  if (TEST_MODE) return {phone: TEST_PHONE, name: shortName + ' [TEST→Dhruv]'};
  if (ALL_PHONES[shortName]) return {phone: ALL_PHONES[shortName], name: shortName};
  return null;
}

// --- Helper: group leads by Owner short name ---
function groupByOwner(leads) {
  const g = {};
  leads.forEach(l => {
    const o = getDealOwner(l);
    if (!g[o]) g[o] = [];
    g[o].push(l);
  });
  return g;
}

// --- Zoho Queries ---
const hourStart = `${TODAY}T${pad(currentHour)}:00:00+05:30`;
const hourEnd = `${TODAY}T${pad(nextHourIST > 23 ? 23 : nextHourIST)}:00:00+05:30`;

const nextHourLeads = await qPage(
  `SELECT Company, Full_Name, Phone, Email, Lead_Task, Sales_Stage, Lead_Status, Leads_Owner FROM Leads WHERE Lead_Task between '${hourStart}' and '${hourEnd}'`
);

const todayLeads = await qPage(
  `SELECT Company, Full_Name, Phone, Email, Lead_Task, Sales_Stage, Lead_Status, Leads_Owner FROM Leads WHERE Lead_Task between '${TODAY}T00:00:00+05:30' and '${TODAY}T23:59:59+05:30'`
);

let overdueLeads = [];
let urgent = [];
if (currentHour <= 8) {
  overdueLeads = await qPage(
    `SELECT Company, Full_Name, Phone, Email, Lead_Task, Sales_Stage, Lead_Status, Leads_Owner FROM Leads WHERE Lead_Task < '${TODAY}T00:00:00+05:30' and Lead_Task > '2026-01-01T00:00:00+05:30' and Lead_Status not in ('12. Subscribed', '11. Rejected', '10. Not Interested (Not Potential)', 'Junk Lead')`
  );
  urgent = overdueLeads.filter(l => {
    const fu = String(l.Lead_Task || '').slice(0, 10);
    return fu && fu < THREE_DAYS_AGO;
  });
}

// Skip if nothing due in next hour (except 8 AM morning briefing)
if (nextHourLeads.length === 0 && currentHour > 8) {
  return [{ json: { nextHour: 0, skipped: true, hour: currentHour } }];
}

const timeLabel = `${pad(currentHour)}:00 - ${pad(nextHourIST)}:00`;
let sentToReps = 0;

if (currentHour <= 8) {
  // ============ 8 AM MORNING BRIEFING ============

  // --- MANAGER MESSAGE: full team view grouped by rep ---
  const todayByOwner = groupByOwner(todayLeads);
  const overdueByOwner = groupByOwner(overdueLeads);

  let mm = `*MORNING BRIEFING — ${TODAY}*\n\n`;
  mm += `Due Today: *${todayLeads.length}*\n`;
  if (overdueLeads.length) mm += `Overdue: *${overdueLeads.length}*\n`;
  if (urgent.length) mm += `Urgent (>3 days): *${urgent.length}*\n`;
  mm += '\n';

  // Per-rep breakdown
  for (const [owner, leads] of Object.entries(todayByOwner).sort((a,b) => b[1].length - a[1].length)) {
    mm += `*${owner}* — ${leads.length} follow-ups\n`;
    leads.slice(0, 5).forEach(l => {
      const co = l.Company || l.Full_Name || '?';
      const time = fmtTime(l.Lead_Task);
      mm += `  - ${co}${time ? ` @ ${time}` : ''}\n`;
    });
    if (leads.length > 5) mm += `  ...+${leads.length - 5} more\n`;
    mm += '\n';
  }

  if (urgent.length) {
    mm += `*URGENT — Overdue >3 Days:*\n`;
    urgent.slice(0, 8).forEach((l, i) => {
      const co = l.Company || l.Full_Name || '?';
      const owner = getDealOwner(l);
      mm += `${i+1}. ${co} (${owner}) — was due: ${String(l.Lead_Task || '').slice(0, 10)}\n`;
    });
    if (urgent.length > 8) mm += `...+${urgent.length - 8} more\n`;
  }
  mm += `\n_Onsite Pulse_`;
  await waAll(MGR, mm);

  // --- REP MESSAGES: each rep gets ONLY their own leads ---
  for (const [owner, leads] of Object.entries(todayByOwner)) {
    const rep = findRep(owner);
    if (!rep) continue;

    const myOverdue = (overdueByOwner[owner] || []).length;
    let rm = `*Good Morning, ${rep.name}!*\n\n`;
    rm += `You have *${leads.length}* follow-ups today`;
    if (myOverdue) rm += ` + *${myOverdue}* overdue`;
    rm += `:\n\n`;

    leads.slice(0, 12).forEach((l, i) => {
      const co = l.Company || l.Full_Name || '?';
      const time = fmtTime(l.Lead_Task);
      const st = l.Sales_Stage || l.Lead_Status || '';
      const contact = l.Phone || l.Email || '';
      rm += `${i+1}. *${co}*`;
      if (time) rm += ` — *${time}*`;
      if (st) rm += ` (${st})`;
      if (contact) rm += `\n   ${contact}`;
      rm += '\n';
    });
    if (leads.length > 12) rm += `\n...+${leads.length - 12} more in CRM\n`;
    if (myOverdue) rm += `\n${myOverdue} overdue — update these in CRM today!\n`;
    rm += `\n_Onsite Pulse — ${TODAY}_`;
    await wa(rep.phone, rm, rep.name);
    sentToReps++;
  }

} else if (currentHour >= 20) {
  // ============ 8 PM EVENING WRAP-UP (Managers only) ============

  const todayByOwner = groupByOwner(todayLeads);
  const totalReps = Object.keys(todayByOwner).length;

  let mm = `*EVENING WRAP-UP — ${TODAY}*\n\n`;
  mm += `Total follow-ups scheduled today: *${todayLeads.length}*\n`;
  mm += `Across *${totalReps}* deal owners\n\n`;

  mm += `*Per Rep Summary:*\n`;
  for (const [owner, leads] of Object.entries(todayByOwner).sort((a,b) => b[1].length - a[1].length)) {
    mm += `  ${owner}: ${leads.length} follow-ups\n`;
  }

  mm += `\nMake sure all reps updated their remarks in CRM.`;
  mm += `\nTomorrow's follow-ups will be sent at 8 AM.`;
  mm += `\n\n_Onsite Pulse_`;
  await waAll(MGR, mm);

} else {
  // ============ HOURLY NUDGE (9 AM - 7 PM) — Reps only ============

  const nextByOwner = groupByOwner(nextHourLeads);
  const todayByOwner = groupByOwner(todayLeads);

  // --- REP MESSAGES: only reps who have follow-ups in next hour ---
  for (const [owner, leads] of Object.entries(nextByOwner)) {
    const rep = findRep(owner);
    if (!rep) continue;

    const myTodayTotal = (todayByOwner[owner] || []).length;
    let rm = `*${rep.name}, ${leads.length} follow-up${leads.length > 1 ? 's' : ''} due NOW (${timeLabel}):*\n\n`;
    leads.forEach((l, i) => {
      const co = l.Company || l.Full_Name || '?';
      const time = fmtTime(l.Lead_Task);
      const st = l.Sales_Stage || l.Lead_Status || '';
      const contact = l.Phone || l.Email || '';
      rm += `${i+1}. *${co}*`;
      if (time) rm += ` — *${time}*`;
      if (st) rm += ` (${st})`;
      if (contact) rm += `\n   ${contact}`;
      rm += '\n';
    });
    rm += `\n_${myTodayTotal} total follow-ups remaining for you today_`;
    rm += `\n_Onsite Pulse_`;
    await wa(rep.phone, rm, rep.name);
    sentToReps++;
  }
}

return [{ json: { nextHour: nextHourLeads.length, today: todayLeads.length, overdue: overdueLeads.length, hour: currentHour, repsNotified: sentToReps } }];
"""

AUTO_2_JS = r"""
// === AUTOMATION 2: Demo Booked → No Demo Done Alert ===
// Shows Deal Owner on each stuck lead so managers know who to push

const SEVEN_DAYS_AGO = daysAgo(7);
const THREE_DAYS_AGO = daysAgo(3);

const total = await qCount("SELECT COUNT(id) as total FROM Leads WHERE Lead_Status = '6. Demo booked' and Demo_Done_Date is null");

const urgentLeads = await qPage(
  `SELECT Company, Full_Name, Phone, Email, Lead_Assigned_Time, Lead_Source, Leads_Owner FROM Leads WHERE Lead_Status = '6. Demo booked' and Demo_Done_Date is null and Lead_Assigned_Time < '${SEVEN_DAYS_AGO}T00:00:00+05:30'`
);

const warningLeads = await qPage(
  `SELECT Company, Full_Name, Phone, Email, Lead_Assigned_Time, Lead_Source, Leads_Owner FROM Leads WHERE Lead_Status = '6. Demo booked' and Demo_Done_Date is null and Lead_Assigned_Time between '${SEVEN_DAYS_AGO}T00:00:00+05:30' and '${THREE_DAYS_AGO}T23:59:59+05:30'`
);

function dealOwner(l) {
  const raw = String(l.Leads_Owner || '').trim();
  return CRM_OWNER_MAP[raw] || raw || '?';
}

const recent = total - urgentLeads.length - warningLeads.length;

let msg = `*DEMO STUCK ALERT — ${TODAY}*\n\n*${total}* leads in 'Demo Booked' but demo NOT done.\n\nURGENT (>7 days): *${urgentLeads.length}*\nWarning (3-7 days): *${warningLeads.length}*\nRecent (<3 days): *${recent}*\n`;

if (urgentLeads.length) {
  msg += `\n*URGENT — Book or Remove:*\n`;
  urgentLeads.slice(0, 12).forEach((l, i) => {
    const co = l.Company || l.Full_Name || '?';
    const owner = dealOwner(l);
    msg += `${i+1}. *${co}* — _${owner}_`;
    const contact = l.Phone || l.Email || '';
    if (contact) msg += `\n   ${contact}`;
    msg += '\n';
  });
  if (urgentLeads.length > 12) msg += `\n...and ${urgentLeads.length - 12} more urgent\n`;
}

if (warningLeads.length) {
  msg += `\n*WARNING — Follow Up This Week:*\n`;
  warningLeads.slice(0, 8).forEach((l, i) => {
    const co = l.Company || l.Full_Name || '?';
    const owner = dealOwner(l);
    msg += `${i+1}. ${co} — _${owner}_\n`;
  });
  if (warningLeads.length > 8) msg += `\n...and ${warningLeads.length - 8} more\n`;
}

msg += `\nEach demo = Rs.8,305 avg revenue. Don't waste booked demos!`;
msg += `\n\n_Onsite Pulse — ${TODAY}_`;
await waAll(MGR, msg);

return [{ json: { total, urgent: urgentLeads.length, warning: warningLeads.length } }];
"""

AUTO_3_JS = r"""
// === AUTOMATION 3: Daily Rep Scorecard ===
// Demos broken down by Deal Owner (Leads_Owner)

const totalDemos = await qCount(`SELECT COUNT(id) as total FROM Leads WHERE Demo_Done_Date between '${MONTH_START}' and '${TODAY}'`);
const totalSales = await qCount(`SELECT COUNT(id) as total FROM Leads WHERE Sale_Done_Date between '${MONTH_START}' and '${TODAY}'`);
const vh = await qCount("SELECT COUNT(id) as total FROM Leads WHERE Sales_Stage = 'Very High Prospect'");
const hp = await qCount("SELECT COUNT(id) as total FROM Leads WHERE Sales_Stage = 'High Prospect'");
const demoBooked = await qCount("SELECT COUNT(id) as total FROM Leads WHERE Lead_Status = '6. Demo booked'");
const followupsToday = await qCount(`SELECT COUNT(id) as total FROM Leads WHERE Lead_Task between '${TODAY}T00:00:00+05:30' and '${TODAY}T23:59:59+05:30'`);

// Per Deal Owner demos
const demoLeads = await qPage(`SELECT Leads_Owner, Demo_Done_Date FROM Leads WHERE Demo_Done_Date between '${MONTH_START}' and '${TODAY}'`);
const demoByOwner = {};
demoLeads.forEach(l => {
  const raw = String(l.Leads_Owner || '').trim();
  const owner = CRM_OWNER_MAP[raw] || raw || 'Unknown';
  demoByOwner[owner] = (demoByOwner[owner] || 0) + 1;
});
const sortedOwners = Object.entries(demoByOwner).sort((a, b) => b[1] - a[1]);

// Per Deal Owner sales
const saleLeads = await qPage(`SELECT Leads_Owner, Sale_Done_Date FROM Leads WHERE Sale_Done_Date between '${MONTH_START}' and '${TODAY}'`);
const salesByOwner = {};
saleLeads.forEach(l => {
  const raw = String(l.Leads_Owner || '').trim();
  const owner = CRM_OWNER_MAP[raw] || raw || 'Unknown';
  salesByOwner[owner] = (salesByOwner[owner] || 0) + 1;
});

// Manager message
let mm = `*DAILY SCORECARD — ${TODAY}*\nDay ${DAY_NUM} of ${MONTH_NAME}\n\n`;
mm += `*Team MTD:*\nDemos: *${totalDemos}*\nSales: *${totalSales}*\n\n`;
mm += `*Pipeline:*\nVH Prospects: ${vh}\nHigh Prospects: ${hp}\nDemo Booked: ${demoBooked}\nFollow-ups Today: ${followupsToday}\n\n`;
if (sortedOwners.length) {
  mm += `*MTD by Deal Owner:*\n`;
  sortedOwners.slice(0, 15).forEach(([owner, demoCount]) => {
    const saleCount = salesByOwner[owner] || 0;
    mm += `  ${owner}: ${demoCount} demos`;
    if (saleCount) mm += ` | ${saleCount} sales`;
    mm += '\n';
  });
}
mm += `\n_Onsite Pulse_`;
await waAll(MGR, mm);

// Rep message — no change, generic team motivation
const rm = `*Good Morning! Day ${DAY_NUM} of ${MONTH_NAME}*\n\n*Team so far:* ${totalDemos} demos | ${totalSales} sales\n\n*Today's Focus:*\n- ${followupsToday} follow-ups due today\n- ${demoBooked} demos pending in pipeline\n- ${vh + hp} hot prospects waiting\n\nCheck your CRM follow-up dates. Update remarks after every demo.\n\n_Onsite Pulse — ${TODAY}_`;
await waAll(ALL_TEAM, rm);

return [{ json: { demos: totalDemos, sales: totalSales, vh, hp, demoBooked, followups: followupsToday } }];
"""

AUTO_4_JS = r"""
// === AUTOMATION 4: CRM Hygiene Report ===
// Per Deal Owner hygiene breakdown

const demos = await qPage(
  `SELECT Company, Leads_Owner, Business_Type, Price_PItched, Lead_Task, Demo_Done_Date FROM Leads WHERE Demo_Done_Date between '${MONTH_START}' and '${TODAY}'`
);

if (!demos.length) return [{ json: { status: 'no_demos' } }];

const total = demos.length;
let remarksFilled = 0, priceFilled = 0, followupSet = 0;

// Per-rep hygiene tracking
const repHygiene = {};

demos.forEach(d => {
  const raw = String(d.Leads_Owner || '').trim();
  const owner = CRM_OWNER_MAP[raw] || raw || 'Unknown';
  if (!repHygiene[owner]) repHygiene[owner] = {total: 0, remarks: 0, price: 0, followup: 0};
  repHygiene[owner].total++;

  const remark = d.Business_Type;
  const hasRemark = remark && String(remark).trim() && !['null','None'].includes(String(remark).trim());
  const hasPrice = d.Price_PItched != null;
  const hasFollowup = d.Lead_Task != null;

  if (hasRemark) { remarksFilled++; repHygiene[owner].remarks++; }
  if (hasPrice) { priceFilled++; repHygiene[owner].price++; }
  if (hasFollowup) { followupSet++; repHygiene[owner].followup++; }
});

const rPct = total ? Math.floor(remarksFilled * 100 / total) : 0;
const pPct = total ? Math.floor(priceFilled * 100 / total) : 0;
const fPct = total ? Math.floor(followupSet * 100 / total) : 0;

let msg = `*CRM HYGIENE REPORT — ${MONTH_NAME}*\n\nTotal Demos: *${total}*\n\n`;
msg += `*Team Data Completeness:*\n`;
msg += `Remarks: ${remarksFilled}/${total} (${rPct}%) ${rPct >= 80 ? 'OK' : 'NEEDS WORK'}\n`;
msg += `Price Pitched: ${priceFilled}/${total} (${pPct}%) ${pPct >= 80 ? 'OK' : 'NEEDS WORK'}\n`;
msg += `Follow-up Set: ${followupSet}/${total} (${fPct}%) ${fPct >= 80 ? 'OK' : 'NEEDS WORK'}\n`;

// Per-rep hygiene leaderboard
msg += `\n*Per Rep Hygiene:*\n`;
const sorted = Object.entries(repHygiene).sort((a, b) => {
  const aScore = a[1].total ? (a[1].remarks + a[1].price + a[1].followup) / (a[1].total * 3) : 0;
  const bScore = b[1].total ? (b[1].remarks + b[1].price + b[1].followup) / (b[1].total * 3) : 0;
  return bScore - aScore;
});
sorted.slice(0, 12).forEach(([owner, h]) => {
  const score = h.total ? Math.floor((h.remarks + h.price + h.followup) * 100 / (h.total * 3)) : 0;
  msg += `  ${owner}: ${score}% (${h.total} demos)\n`;
});

msg += `\n*Target:* 80%+ on all three fields.\n\n_Onsite Pulse — ${TODAY}_`;
await waAll(MGR, msg);

return [{ json: { total, remarksPct: rPct, pricePct: pPct, followupPct: fPct } }];
"""

AUTO_5_JS = r"""
// === AUTOMATION 5: Website + WhatsApp Hot Lead Alert ===
// Shows Deal Owner on each lead. Managers get full list, reps get only their own.

const THREE_DAYS_AGO = daysAgo(3);
const allHot = [];

for (const source of ['2.Website', '4.Customer Support WA']) {
  const leads = await qPage(
    `SELECT Company, Full_Name, Phone, Email, Lead_Source, Lead_Status, Leads_Owner, Created_Time FROM Leads WHERE Lead_Source = '${source}' and Created_Time > '${THREE_DAYS_AGO}T00:00:00+05:30' and Demo_Done_Date is null and Lead_Status not in ('12. Subscribed', '11. Rejected', '10. Not Interested (Not Potential)', 'Junk Lead')`
  );
  leads.forEach(l => { l._src = source.includes('Website') ? 'Website' : 'WhatsApp'; });
  allHot.push(...leads);
}

for (const source of ['8. Client Referral', '3. Inbound Demo Req.']) {
  const leads = await qPage(
    `SELECT Company, Full_Name, Phone, Email, Lead_Source, Lead_Status, Leads_Owner, Created_Time FROM Leads WHERE Lead_Source = '${source}' and Created_Time > '${THREE_DAYS_AGO}T00:00:00+05:30' and Demo_Done_Date is null and Lead_Status not in ('12. Subscribed', '11. Rejected', '10. Not Interested (Not Potential)', 'Junk Lead')`
  );
  if (leads.length) {
    leads.forEach(l => { l._src = source.split('.').pop().trim(); });
    allHot.push(...leads);
  }
}

if (!allHot.length) return [{ json: { status: 'no_hot_leads' } }];

function dealOwner(l) {
  const raw = String(l.Leads_Owner || '').trim();
  return CRM_OWNER_MAP[raw] || raw || 'Unassigned';
}

// Count by source
const bySource = {};
allHot.forEach(l => { bySource[l._src] = (bySource[l._src] || 0) + 1; });

// Manager message — full list with Deal Owner
let msg = `*HOT LEAD ALERT — ${TODAY}*\n\n*${allHot.length}* high-converting leads NOT YET contacted:\n\n`;
Object.entries(bySource).sort((a,b) => b[1]-a[1]).forEach(([src, cnt]) => { msg += `*${src}:* ${cnt} leads\n`; });
msg += `\nThese convert *2-3x better* than paid ads.\n\n`;
msg += `*Top Leads:*\n`;
allHot.slice(0, 12).forEach((l, i) => {
  const co = l.Company || l.Full_Name || '?';
  const owner = dealOwner(l);
  msg += `${i+1}. *${co}* (${l._src}) — _${owner}_`;
  const contact = l.Phone || l.Email || '';
  if (contact) msg += `\n   ${contact}`;
  msg += '\n';
});
if (allHot.length > 12) msg += `\n...and ${allHot.length - 12} more in CRM\n`;
msg += `\n_Onsite Pulse_`;
await waAll(MGR, msg);

// Per-rep: each rep gets only their own hot leads
const ALL_PHONES = {...REPS, ...PRE_SALES};
const byOwner = {};
allHot.forEach(l => {
  const o = dealOwner(l);
  if (!byOwner[o]) byOwner[o] = [];
  byOwner[o].push(l);
});

for (const [owner, leads] of Object.entries(byOwner)) {
  if (!owner || owner === 'Team' || owner === 'Unassigned') continue;
  const phone = ALL_PHONES[owner];
  if (!phone) continue;
  if (TEST_MODE) continue; // skip per-rep in test mode

  let rm = `*${owner}, ${leads.length} hot lead${leads.length > 1 ? 's' : ''} waiting!*\n\n`;
  rm += `These are Website/WhatsApp/Referral leads — they convert 2-3x better.\n\n`;
  leads.slice(0, 8).forEach((l, i) => {
    const co = l.Company || l.Full_Name || '?';
    const contact = l.Phone || l.Email || '';
    rm += `${i+1}. *${co}* (${l._src})`;
    if (contact) rm += `\n   ${contact}`;
    rm += '\n';
  });
  if (leads.length > 8) rm += `\n...+${leads.length - 8} more\n`;
  rm += `\nCall them TODAY!\n_Onsite Pulse_`;
  await wa(phone, rm, owner);
}

return [{ json: { hotLeads: allHot.length, bySource } }];
"""

AUTO_7_JS = r"""
// === AUTOMATION 7: Daily Session Opener ===
// Runs at 7:50 AM IST Mon-Sat (10 min before 8 AM briefing)
// Sends sample_template to open the 24h WhatsApp session window for each rep
// WITHOUT this, text-only messages are blocked by WhatsApp (no active session)
// Excludes: Sumit, Akshansh (managers who don't need this ping)

const SESSION_PHONES = {
  ...REPS,
  ...PRE_SALES,
  Dhruv: MGR.Dhruv  // include Dhruv from managers
};

const results = [];
for (const [name, phone] of Object.entries(SESSION_PHONES)) {
  const r = await waTemplate(phone, name);
  const raw = typeof r === 'string' ? JSON.parse(r) : r;
  results.push({name, status: raw?.status || 'SENT'});
}

const sent = results.filter(r => r.status === 'ACCEPTED').length;
const failed = results.filter(r => r.status !== 'ACCEPTED').length;

return [{ json: { sent, failed, total: results.length, results } }];
"""

AUTO_6_JS = r"""
// === AUTOMATION 6: Ad Fatigue & Dying Campaign Alert ===
// FB Ads config
const FB_TOKEN = '%FB_TOKEN%';
const FB_ACCOUNT = 'act_3176065209371338';
const FB_BASE = 'https://graph.facebook.com/v21.0';
const LAST_7 = daysAgo(7);
const LAST_14 = daysAgo(14);

if (!FB_TOKEN || FB_TOKEN === '%FB_TOKEN%') return [{ json: { error: 'No FB token' } }];

async function fbApi(endpoint, params = {}) {
  params.access_token = FB_TOKEN;
  const qs = Object.entries(params).map(([k,v]) => `${k}=${encodeURIComponent(v)}`).join('&');
  try {
    const r = await http({method:'GET', url:`${FB_BASE}/${endpoint}?${qs}`});
    return typeof r === 'string' ? JSON.parse(r) : r;
  } catch(e) { return {error: e.message}; }
}

// Get active campaigns
const campaigns = await fbApi(`${FB_ACCOUNT}/campaigns`, {
  fields: 'name,status,objective',
  filtering: JSON.stringify([{field:'effective_status',operator:'IN',value:['ACTIVE']}]),
  limit: 50
});

const campList = campaigns?.data || [];
const alerts = [];
const campData = [];

for (const camp of campList) {
  const recent = await fbApi(`${camp.id}/insights`, {
    fields: 'spend,impressions,clicks,actions,cost_per_action_type,frequency',
    time_range: JSON.stringify({since: LAST_7, until: TODAY})
  });
  const previous = await fbApi(`${camp.id}/insights`, {
    fields: 'spend,impressions,clicks,actions,cost_per_action_type,frequency',
    time_range: JSON.stringify({since: LAST_14, until: LAST_7})
  });

  const r = recent?.data?.[0] || {};
  const p = previous?.data?.[0] || {};
  const spendR = parseFloat(r.spend || 0);
  const freqR = parseFloat(r.frequency || 0);

  let leadsR = 0, leadsP = 0, cplR = 0, cplP = 0;
  (r.actions || []).forEach(a => { if (a.action_type === 'lead') leadsR = parseInt(a.value); });
  (r.cost_per_action_type || []).forEach(a => { if (a.action_type === 'lead') cplR = parseFloat(a.value); });
  (p.actions || []).forEach(a => { if (a.action_type === 'lead') leadsP = parseInt(a.value); });
  (p.cost_per_action_type || []).forEach(a => { if (a.action_type === 'lead') cplP = parseFloat(a.value); });

  campData.push({name: camp.name, spend7d: spendR, leads7d: leadsR, cpl7d: cplR, leadsP, cplP, freq: freqR});

  if (cplP > 0 && cplR > 0 && cplR > cplP * 1.3) {
    const pct = Math.floor((cplR - cplP) / cplP * 100);
    alerts.push(`*CPL UP ${pct}%* — ${camp.name}\n  Rs.${cplP.toFixed(0)} → Rs.${cplR.toFixed(0)}`);
  }
  if (freqR > 3.0) alerts.push(`*AUDIENCE FATIGUE* — ${camp.name}\n  Frequency: ${freqR.toFixed(1)} (>3.0 = burnt out)`);
  if (spendR > 1000 && leadsR === 0) alerts.push(`*ZERO LEADS* — ${camp.name}\n  Spent Rs.${spendR.toFixed(0)} in 7 days, 0 leads`);
  if (leadsP > 5 && leadsR < leadsP * 0.5) {
    const pct = Math.floor((leadsP - leadsR) / leadsP * 100);
    alerts.push(`*LEADS DOWN ${pct}%* — ${camp.name}\n  ${leadsP} → ${leadsR} (7-day)`);
  }
}

let msg = `*AD PERFORMANCE ALERT — ${TODAY}*\n\n`;
if (alerts.length) {
  msg += `*${alerts.length} Issues Detected:*\n\n`;
  alerts.forEach((a, i) => { msg += `${i+1}. ${a}\n\n`; });
} else {
  msg += 'No critical issues. All campaigns performing within normal range.\n\n';
}
msg += `*Active Campaigns (7-day):*\n`;
campData.sort((a, b) => b.spend7d - a.spend7d).slice(0, 8).forEach(c => {
  if (c.spend7d > 0) {
    msg += `- ${c.name.slice(0, 30)}: Rs.${c.spend7d.toFixed(0)} spend`;
    msg += c.leads7d > 0 ? ` | ${c.leads7d} leads | Rs.${c.cpl7d.toFixed(0)} CPL` : ' | 0 leads';
    msg += '\n';
  }
});
msg += `\n_Onsite Pulse_`;

// Send to Dhruv + Akshansh only
const adRecipients = {Dhruv: MGR.Dhruv, Akshansh: MGR.Akshansh};
for (const [name, phone] of Object.entries(adRecipients)) await wa(phone, msg, name);

return [{ json: { campaigns: campData.length, alerts: alerts.length } }];
"""



AUTO_8_JS = r"""
// === AUTO 8: INTERACTIVE WHATSAPP BOT ===
// Webhook-triggered — responds when team members reply

const body = $input.first().json.body || $input.first().json;
const msg = (body?.message?.text || body?.text || body?.whatsapp?.text?.body || body?.payload?.text || '').trim();
const senderPhone = (body?.message?.from || body?.from || body?.recipient?.phone || body?.sender?.phone || body?.payload?.source || '').replace(/\+/g, '');
const senderName = body?.message?.name || body?.sender?.name || body?.recipient?.name || '';

// === PHONE WHITELIST — only respond to registered team ===
const ALLOWED = {
  ...REPS, ...PRE_SALES,
  Sumit: MGR.Sumit, Akshansh: MGR.Akshansh, Dhruv: MGR.Dhruv
};
const PHONE_TO_NAME = {};
for (const [name, phone] of Object.entries(ALLOWED)) PHONE_TO_NAME[phone] = name;

const repName = PHONE_TO_NAME[senderPhone];
if (!repName) {
  return [{ json: { status: 'ignored', reason: 'not_authorized', phone: senderPhone } }];
}

if (!msg || msg.length < 1) {
  return [{ json: { status: 'ignored', reason: 'empty_message' } }];
}

const msgLower = msg.toLowerCase();

// === INTENT DETECTION ===
let intent = 'chat';
const wantsNotes = /\b(note|notes|remark|remarks|description|detail|details)\b/.test(msgLower);
if (/\b(demo|demos)\b/.test(msgLower)) intent = 'demos';
else if (/\b(sale|sales|closed|won|conversion|revenue|paisa|kitna kamaya)\b/.test(msgLower)) intent = 'sales';
else if (/\b(pipeline|prospect|hp|vhp|high prospect)\b/.test(msgLower)) intent = 'pipeline';
else if (/\b(follow.?up|pending|overdue|task)\b/.test(msgLower)) intent = 'followups';
else if (/\b(help|kya kar|what can|commands?)\b/.test(msgLower)) intent = 'help';
else if (/\b(hi|hello|hey|good morning|gm|namaste)\b/.test(msgLower)) intent = 'greeting';
else if (/\b(score|rank|leaderboard|position|kahan|standing)\b/.test(msgLower)) intent = 'rank';
else if (/\b(target|goal|kitna|how much)\b/.test(msgLower)) intent = 'target';
else if (wantsNotes) intent = 'notes';

// === MONTH PARSING — override date range if user mentions a specific month ===
const parsedMonth = parseMonth(msg);
if (parsedMonth) {
  MONTH_START = parsedMonth.start;
  MONTH_END = parsedMonth.end;
  MONTH_NAME = parsedMonth.name;
}

// === CRM OWNER NAME for queries ===
const crmNames = Object.entries(CRM_OWNER_MAP).filter(([k, v]) => v === repName).map(([k]) => k);
const ownerFilter = crmNames.length > 0
  ? crmNames.map(n => `Leads_Owner = '${n}'`).join(' OR ')
  : `Leads_Owner = '${repName}'`;

let reply = '';

// === GREETING ===
if (intent === 'greeting') {
  const greetings = [
    `Hey ${repName}! 🙌 Ready to crush some deals today? Just ask me anything — demos, pipeline, sales. I'm here!`,
    `Good morning ${repName}! ☀️ Your friendly Onsite Pulse bot reporting for duty. Kya chahiye?`,
    `Hello ${repName}! 👋 Pipeline check? Demo count? Sales update? Bas bol do!`,
    `Hey hey ${repName}! 🚀 Aaj ka plan kya hai? Main ready hoon data ke saath!`,
  ];
  reply = greetings[Math.floor(Math.random() * greetings.length)];
}

// === HELP ===
else if (intent === 'help') {
  reply = `*Hey ${repName}! Here's what I can do:* 🤖\n\n` +
    `📊 *"my demos"* — Your demo count this month\n` +
    `💰 *"my sales"* — Your closed deals\n` +
    `🔥 *"my pipeline"* — Your hot prospects\n` +
    `📋 *"my follow-ups"* — Pending follow-ups\n` +
    `🏆 *"my rank"* — Where you stand in the team\n` +
    `🎯 *"my target"* — Monthly target vs actual\n\n` +
    `Just type naturally — Hinglish bhi chalega! 😄\n` +
    `_— Onsite Pulse_`;
}

// === DEMOS ===
else if (intent === 'demos') {
  const demoCount = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Demo_Done_Date between '${MONTH_START}' and '${MONTH_END}'`);
  const bookedCount = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Lead_Status = '6. Demo booked'`);

  const demoLeads = await qPage(`SELECT Full_Name, Company, Demo_Done_Date FROM Leads WHERE (${ownerFilter}) AND Demo_Done_Date between '${MONTH_START}' and '${MONTH_END}' ORDER BY Demo_Done_Date DESC`);

  reply = `*${repName}'s Demos — ${MONTH_NAME}* 📊\n\n`;
  reply += `✅ Demos Done: *${demoCount}*\n`;
  reply += `📅 Demos Booked (pending): *${bookedCount}*\n\n`;

  if (demoLeads.length > 0) {
    reply += `*Recent demos:*\n`;
    demoLeads.slice(0, 5).forEach((l, i) => {
      const name = l.Company || l.Full_Name || '?';
      const date = (l.Demo_Done_Date || '').slice(0, 10);
      reply += `${i+1}. ${name} — ${date}\n`;
    });
    if (demoLeads.length > 5) reply += `...+${demoLeads.length - 5} more\n`;
  }
  reply += `\nKeep going ${repName}! 💪\n_— Onsite Pulse_`;
}

// === SALES ===
else if (intent === 'sales') {
  const salesLeads = await qPage(`SELECT Full_Name, Company, Annual_Revenue, Sale_Done_Date FROM Leads WHERE (${ownerFilter}) AND Sale_Done_Date between '${MONTH_START}' and '${MONTH_END}' ORDER BY Sale_Done_Date DESC`);
  const salesCount = salesLeads.length;
  let totalRevenue = 0;
  salesLeads.forEach(l => { totalRevenue += Number(l.Annual_Revenue) || 0; });

  reply = `*${repName}'s Sales — ${MONTH_NAME}* 💰\n\n`;
  reply += `🏆 Sales Closed: *${salesCount}*\n`;
  reply += `💰 Total Revenue: *Rs. ${fmtINR(totalRevenue)}*\n\n`;

  if (salesLeads.length > 0) {
    reply += `*Closures:*\n`;
    salesLeads.slice(0, 8).forEach((l, i) => {
      const name = l.Company || l.Full_Name || '?';
      const rev = Number(l.Annual_Revenue) || 0;
      reply += `${i+1}. ${name}${rev ? ` — Rs. ${fmtINR(rev)}` : ''}\n`;
    });
    if (salesLeads.length > 8) reply += `...+${salesLeads.length - 8} more\n`;
  }
  reply += salesCount > 0 ? `\nGreat work! Keep the momentum! 🔥` : `\nMonth abhi baaki hai — let's close some! 💪`;
  reply += `\n_— Onsite Pulse_`;
}

// === PIPELINE ===
else if (intent === 'pipeline') {
  const vhp = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Sales_Stage = 'Very High Prospect'`);
  const hp = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Sales_Stage = 'High Prospect'`);
  const prospect = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Sales_Stage = '1. Prospect'`);

  reply = `*${repName}'s Pipeline* 🔥\n\n`;
  reply += `🔴 Very High Prospect: *${vhp}*\n`;
  reply += `🟠 High Prospect: *${hp}*\n`;
  reply += `🟡 Prospect: *${prospect}*\n`;
  reply += `\nTotal hot leads: *${vhp + hp + prospect}*\n`;
  reply += vhp > 0 ? `\n${vhp} VHP leads — follow up TODAY! 🎯` : `\nFocus on converting prospects to HP! 📈`;
  reply += `\n_— Onsite Pulse_`;
}

// === FOLLOW-UPS ===
else if (intent === 'followups') {
  const overdue = await qPage(`SELECT Full_Name, Company, Lead_Task FROM Leads WHERE (${ownerFilter}) AND Lead_Task is not null AND Lead_Task < '${TODAY}T00:00:00+05:30'`);
  const todayTasks = await qPage(`SELECT Full_Name, Company, Lead_Task FROM Leads WHERE (${ownerFilter}) AND Lead_Task >= '${TODAY}T00:00:00+05:30' AND Lead_Task <= '${TODAY}T23:59:59+05:30'`);

  reply = `*${repName}'s Follow-Ups* 📋\n\n`;
  reply += `📅 Due Today: *${todayTasks.length}*\n`;
  reply += `⚠️ Overdue: *${overdue.length}*\n\n`;

  if (todayTasks.length > 0) {
    reply += `*Today's calls:*\n`;
    todayTasks.slice(0, 5).forEach((l, i) => {
      reply += `${i+1}. ${l.Company || l.Full_Name || '?'}\n`;
    });
  }
  if (overdue.length > 0) {
    reply += `\n*Overdue (needs attention):*\n`;
    overdue.slice(0, 3).forEach((l, i) => {
      reply += `${i+1}. ${l.Company || l.Full_Name || '?'} — was due ${(l.Lead_Task || '').slice(0, 10)}\n`;
    });
  }
  reply += `\n_— Onsite Pulse_`;
}

// === RANK ===
else if (intent === 'rank') {
  const allReps = await qPage(`SELECT Leads_Owner, Sale_Done_Date FROM Leads WHERE Sale_Done_Date between '${MONTH_START}' and '${MONTH_END}'`);

  const ranks = {};
  (allReps || []).forEach(r => {
    const owner = CRM_OWNER_MAP[r.Leads_Owner] || r.Leads_Owner;
    ranks[owner] = (ranks[owner] || 0) + 1;
  });

  const sorted = Object.entries(ranks).sort((a, b) => b[1] - a[1]);
  const myRank = sorted.findIndex(([n]) => n === repName) + 1;
  const myCount = ranks[repName] || 0;

  reply = `*Team Leaderboard — ${MONTH_NAME}* 🏆\n\n`;
  sorted.slice(0, 5).forEach(([name, count], i) => {
    const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i+1}.`;
    const marker = name === repName ? ' ← YOU' : '';
    reply += `${medal} ${name}: ${count} sales${marker}\n`;
  });

  if (myRank > 5) reply += `\n...you're at #${myRank} with ${myCount} sales`;
  reply += myRank <= 3 ? `\n\nTop 3! Amazing work ${repName}! 🔥` : `\n\nLet's climb up! Every demo counts 💪`;
  reply += `\n_— Onsite Pulse_`;
}

// === TARGET ===
else if (intent === 'target') {
  const mySales = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Sale_Done_Date between '${MONTH_START}' and '${MONTH_END}'`);
  const myDemos = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Demo_Done_Date between '${MONTH_START}' and '${MONTH_END}'`);
  const daysLeft = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate() - DAY_NUM;

  reply = `*${repName}'s Progress — ${MONTH_NAME}* 🎯\n\n`;
  reply += `📊 Demos Done: *${myDemos}*\n`;
  reply += `💰 Sales Closed: *${mySales}*\n`;
  reply += `📅 Days Left: *${daysLeft}*\n\n`;
  reply += `Conversion Rate: ${myDemos > 0 ? Math.round(mySales / myDemos * 100) : 0}%\n`;
  reply += daysLeft > 15 ? `\nStill plenty of time — keep pushing! 🚀` : `\nFinal stretch! Close those hot leads NOW! 🔥`;
  reply += `\n_— Onsite Pulse_`;
}

// === GENERAL CHAT ===
else {
  const funReplies = [
    `Hey ${repName}! Samajh nahi aaya 😅 Try "my demos", "my sales", "my pipeline", or just say "help"!`,
    `${repName}, main data bot hoon yaar — sales aur demos ke baare mein pooch! Type "help" for options 😄`,
    `Hmm interesting ${repName}... but mujhe sirf sales ki baat samajh aati hai 😂 Try "help"!`,
    `${repName}, mere paas jokes nahi hai but numbers zaroor hai! 📊 Type "my pipeline" or "help"`,
  ];
  reply = funReplies[Math.floor(Math.random() * funReplies.length)];
}

// === SEND REPLY ===
await wa(senderPhone, reply, repName);

return [{ json: { status: 'replied', to: repName, intent, msgLength: msg.length } }];
"""

# === AUTO 9: PULSE CHAT (WEB UI) ===
# Same bot logic as AUTO_8 but for web chat — accepts {name, message}, returns {reply}
# No WhatsApp sending — response goes directly to the chat UI
AUTO_9_JS = r"""
// === AUTO 9: PULSE CHAT — WEB INTERFACE ===
const body = $input.first().json.body || $input.first().json;
const repName = (body?.name || '').trim();
const msg = (body?.message || '').trim();
const pin = (body?.pin || '').trim();

// === PIN AUTH ===
const PINS = {
  Sunil:'2824', Anjali:'1409', Bhavya:'5506', Mohan:'5012',
  Gayatri:'4657', Shailendra:'3286', 'Amit U':'2679', Hitangi:'9935',
  'Amit Kumar':'2424', Jyoti:'7912', Shruti:'1520',
  Sumit:'1488', Akshansh:'2535', Dhruv:'4582'
};

// === ROLES ===
// admin: can see ALL reps' data
// team_lead: can see own + assigned team
// rep: own data only
const ROLES = {
  Dhruv:'admin', Sumit:'admin', Akshansh:'admin',
  Anjali:'team_lead',
  Sunil:'rep', Bhavya:'rep', Mohan:'rep', Gayatri:'rep',
  Shailendra:'rep', 'Amit U':'rep', Hitangi:'rep', 'Amit Kumar':'rep',
  Jyoti:'rep', Shruti:'rep'
};

// team_lead can also see these reps' data
const LEAD_ACCESS = {
  Anjali: ['Jyoti', 'Shruti', 'Chadni']
};

if (!repName || !PINS[repName]) {
  return [{ json: { reply: 'Access denied. Name not recognized.', status: 'auth_failed' } }];
}

// === LOGIN FLOW ===
if (msg === '__login__') {
  if (pin !== PINS[repName]) {
    return [{ json: { reply: 'Wrong PIN. Please try again.', status: 'auth_failed' } }];
  }
  const role = ROLES[repName] || 'rep';
  let welcome = `Hey ${repName}! Welcome to Onsite Pulse.\n\n`;
  welcome += `Ask me about your demos, sales, pipeline, follow-ups, or rank.\n`;
  if (role === 'admin') welcome += `\nAdmin access: You can check any rep's data. Try "Anjali demos" or "team overview".\n`;
  else if (role === 'team_lead') welcome += `\nTeam Lead access: You can also check Jyoti, Shruti, Chadni's data.\n`;
  welcome += `\nOr just tap a quick action below!\n— Onsite Pulse`;
  return [{ json: { reply: welcome, status: 'ok', role } }];
}

if (!msg || msg.length < 1) {
  return [{ json: { reply: `Hey ${repName}! Type something — "my demos", "my sales", "my pipeline", or "help"`, status: 'empty' } }];
}

const myRole = ROLES[repName] || 'rep';
const msgLower = msg.toLowerCase();

// === SUPABASE CONVERSATION MEMORY ===
const SB_URL = '%SUPABASE_URL%';
const SB_KEY = '%SUPABASE_KEY%';
const SB_HEADERS = {'apikey':SB_KEY,'Authorization':`Bearer ${SB_KEY}`,'Content-Type':'application/json','Prefer':'return=minimal'};

// Fetch recent conversation history for this user
async function sbGetHistory(userName, limit=5) {
  try {
    const resp = await http({method:'GET',
      url:`${SB_URL}/rest/v1/pulse_chat_history?user_name=eq.${encodeURIComponent(userName)}&order=created_at.desc&limit=${limit}&select=message,reply,intent,lead_context,created_at`,
      headers:{...SB_HEADERS, 'Prefer':''}});
    const data = typeof resp === 'string' ? JSON.parse(resp) : resp;
    return Array.isArray(data) ? data.reverse() : []; // oldest first
  } catch(e) { return []; }
}

// Store a message + reply
async function sbStore(userName, message, replyText, intent, leadContext) {
  try {
    await http({method:'POST', url:`${SB_URL}/rest/v1/pulse_chat_history`,
      headers:SB_HEADERS,
      body:JSON.stringify({user_name:userName, message, reply:(replyText||'').slice(0,2000), intent, lead_context:leadContext||{}})});
  } catch(e) { /* non-critical — don't break chat if store fails */ }
}

// Fetch conversation history (non-blocking — don't fail if Supabase is down)
let chatHistory = [];
try {
  chatHistory = await sbGetHistory(repName, 5);
} catch(e) { /* Supabase unavailable — continue without memory */ }

// Build conversation context string for AI
let conversationContext = '';
if (chatHistory.length > 0) {
  conversationContext = '\n\nRecent conversation history (oldest to newest):\n';
  chatHistory.forEach(h => {
    conversationContext += `User: ${h.message}\nBot: ${(h.reply||'').slice(0,200)}\nIntent: ${h.intent || '?'}`;
    if (h.lead_context?.lead_name) conversationContext += ` | Lead discussed: ${h.lead_context.lead_name}`;
    if (h.lead_context?.lead_phone) conversationContext += ` (${h.lead_context.lead_phone})`;
    conversationContext += '\n';
  });
}

// === DETECT TARGET REP ===
// Admins can say "Anjali demos", "Bhavya sales", etc.
// Team leads can query their team members
// Reps can only query themselves
const ALL_NAMES = Object.keys(PINS);
let targetRep = repName; // default: self
let queryingOther = false;
let queryingAll = false;

if (/\b(team|all|everyone|sab|sabke|overview)\b/.test(msgLower)) {
  if (myRole === 'admin') { queryingAll = true; }
  else if (myRole === 'team_lead') { queryingAll = true; } // will be scoped to their team
}

if (!queryingAll) {
  for (const name of ALL_NAMES) {
    if (name === repName) continue;
    if (new RegExp('\\b' + name.toLowerCase() + '\\b').test(msgLower)) {
      // Check permission
      if (myRole === 'admin') { targetRep = name; queryingOther = true; break; }
      else if (myRole === 'team_lead' && (LEAD_ACCESS[repName] || []).includes(name)) { targetRep = name; queryingOther = true; break; }
      // Reps trying to see others → deny
      else {
        return [{ json: { reply: `Sorry ${repName}, you can only see your own data. Try "my demos" or "my sales".`, status: 'ok', intent: 'denied' } }];
      }
    }
  }
}

// === AI INTENT DETECTION (Grok 4.1 Fast via OpenRouter) ===
const OR_KEY = '%OPENROUTER_KEY%';

// Fast-path: obvious intents (no AI call needed)
let intent = null;
let wantsNotes = false;
let searchPhone = null;
let searchName = null;
let searchCompany = null;
let aiReply = null;

if (/^\s*(hi|hello|hey|good morning|gm|namaste|yo)\s*[!.]?\s*$/i.test(msg)) intent = 'greeting';
else if (/^\s*(help|kya kar|what can|commands?)\s*[?]?\s*$/i.test(msg)) intent = 'help';

// For everything else → ask AI
if (!intent) {
  try {
    const aiResp = await http({
      method: 'POST',
      url: 'https://openrouter.ai/api/v1/chat/completions',
      headers: { 'Authorization': `Bearer ${OR_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'x-ai/grok-4.1-fast',
        max_tokens: 300,
        temperature: 0,
        messages: [
          { role: 'system', content: `You are an intent classifier for a sales CRM chatbot. The user is "${repName}", a sales rep at Onsite Teams (construction SaaS).

Given the user's message, respond with ONLY a JSON object (no markdown, no explanation):
{
  "intent": one of: "demos", "sales", "pipeline", "followups", "rank", "target", "notes", "lead_search", "assistant", "greeting", "help", "chat",
  "month": null or month name if user mentions a specific month (e.g. "feb", "january", "last month"),
  "wants_notes": true/false - whether user wants remarks/notes/details,
  "search_phone": null or phone number if user wants to find a lead by phone,
  "search_name": null or lead/company name if user wants to find a specific lead,
  "search_company": null or company name if searching by company,
  "ai_reply": null or a short friendly reply if intent is "chat" (general conversation not about CRM data)
}

Intent definitions:
- demos: anything about demos done, demo count, demo list, presentations given
- sales: anything about sales closed, deals won, revenue, money earned, conversions
- pipeline: prospects, hot leads, VHP/HP, pipeline status, potential deals
- followups: follow-ups, pending tasks, overdue calls, scheduled callbacks
- rank: leaderboard, ranking, position in team, comparison with others
- target: goals, targets, progress, how much more needed, days left
- notes: remarks, notes, lead details, what was discussed
- lead_search: finding a specific lead by phone number, name, or company name
- assistant: ANY question about product knowledge, pricing, how to approach/pitch a client, write an email/message, handle objections, competitor comparison, sales strategy, what features Onsite has, how to close a deal, follow-up email templates, demo prep. This includes: "write a mail", "how to pitch", "what's our pricing", "how to handle objection", "compare with Procore", "help me close this deal", "draft a message", "what modules do we have"
- greeting: hi, hello, good morning
- help: asking what bot can do
- chat: general conversation, jokes, completely unrelated questions (weather, cricket, food — NOT business/sales related)

The user may write in English, Hindi, or Hinglish. Understand all three.

IMPORTANT: If the user says "same lead", "that one", "this lead", "uska", "iska", etc. — refer to the conversation history to identify which lead they're talking about. Use the lead_context from previous messages.${conversationContext}` },
          { role: 'user', content: msg }
        ]
      })
    });
    const parsed = typeof aiResp === 'string' ? JSON.parse(aiResp) : aiResp;
    const aiText = (parsed?.choices?.[0]?.message?.content || '').trim();
    // Parse JSON from AI response (handle markdown code blocks)
    const jsonStr = aiText.replace(/```json?\n?/g, '').replace(/```/g, '').trim();
    const ai = JSON.parse(jsonStr);
    intent = ai.intent || 'chat';
    wantsNotes = ai.wants_notes || false;
    searchPhone = ai.search_phone || null;
    searchName = ai.search_name || null;
    searchCompany = ai.search_company || null;
    aiReply = ai.ai_reply || null;

    // AI-detected month override
    if (ai.month) {
      const pm = parseMonth(ai.month);
      if (pm) { MONTH_START = pm.start; MONTH_END = pm.end; MONTH_NAME = pm.name; }
    }
  } catch(e) {
    // AI failed — fallback to basic regex
    intent = 'chat';
    const ml = msgLower;
    if (/\b(demo|demos)\b/.test(ml)) intent = 'demos';
    else if (/\b(sale|sales|closed|won|revenue)\b/.test(ml)) intent = 'sales';
    else if (/\b(pipeline|prospect|hp|vhp)\b/.test(ml)) intent = 'pipeline';
    else if (/\b(follow.?up|pending|overdue)\b/.test(ml)) intent = 'followups';
    else if (/\b(rank|leaderboard|position)\b/.test(ml)) intent = 'rank';
    else if (/\b(target|goal)\b/.test(ml)) intent = 'target';
    else if (/\b(price|pricing|cost|plan|feature|module|write|email|mail|draft|pitch|approach|objection|competitor|compare|close|strategy|help me)\b/.test(ml)) intent = 'assistant';
    wantsNotes = /\b(note|notes|remark|remarks)\b/.test(ml);
  }
}

if (queryingAll && intent === 'chat') intent = 'demos';

// === MONTH PARSING (fallback — AI may have already set it) ===
const parsedMonth = parseMonth(msg);
if (parsedMonth) {
  MONTH_START = parsedMonth.start;
  MONTH_END = parsedMonth.end;
  MONTH_NAME = parsedMonth.name;
}

// === BUILD OWNER FILTER ===
function buildOwnerFilter(name) {
  const crmN = Object.entries(CRM_OWNER_MAP).filter(([k, v]) => v === name).map(([k]) => k);
  return crmN.length > 0 ? crmN.map(n => `Leads_Owner = '${n}'`).join(' OR ') : `Leads_Owner = '${name}'`;
}

let ownerFilter;
let displayName = targetRep;

if (queryingAll) {
  if (myRole === 'admin') {
    // All reps
    const allRepNames = [...Object.keys(REPS), ...Object.keys(PRE_SALES)];
    const filters = allRepNames.map(n => buildOwnerFilter(n));
    ownerFilter = filters.join(' OR ');
    displayName = 'Team';
  } else if (myRole === 'team_lead') {
    // Own + team
    const teamNames = [repName, ...(LEAD_ACCESS[repName] || [])];
    const filters = teamNames.map(n => buildOwnerFilter(n));
    ownerFilter = filters.join(' OR ');
    displayName = `${repName}'s Team`;
  }
} else {
  ownerFilter = buildOwnerFilter(targetRep);
  displayName = targetRep;
}

let reply = '';

// === GREETING ===
if (intent === 'greeting') {
  const greetings = [
    `Hey ${repName}! Ready to crush some deals today? Just ask me anything — demos, pipeline, sales. I'm here!`,
    `Good morning ${repName}! Your friendly Pulse bot reporting for duty. Kya chahiye?`,
    `Hello ${repName}! Pipeline check? Demo count? Sales update? Bas bol do!`,
    `Hey hey ${repName}! Aaj ka plan kya hai? Main ready hoon data ke saath!`,
  ];
  reply = greetings[Math.floor(Math.random() * greetings.length)];
}

// === HELP ===
else if (intent === 'help') {
  reply = `Hey ${repName}! Here's everything I can do:\n\n` +
    `CRM DATA:\n` +
    `"my demos" — Demo count this month\n` +
    `"my sales" — Closed deals & revenue\n` +
    `"my pipeline" — Hot prospects (VHP/HP)\n` +
    `"my follow-ups" — Pending follow-ups\n` +
    `"my rank" — Team leaderboard\n` +
    `"my target" — Monthly progress\n` +
    `"my notes" — Recent leads with remarks\n` +
    `"find lead <name/phone>" — Search CRM\n\n` +
    `SALES ASSISTANT:\n` +
    `"our pricing" — Full pricing breakdown\n` +
    `"write a follow-up email" — Draft emails\n` +
    `"how to pitch this client" — Approach strategy\n` +
    `"handle objection: too expensive" — Rebuttals\n` +
    `"compare with Procore" — Competitor info\n` +
    `"what features in Business+" — Product info\n\n` +
    `Add month: "feb demos", "last month sales"\n` +
    (myRole === 'admin' ? `\nAdmin: "Anjali demos", "team overview", "all sales"\n` : '') +
    (myRole === 'team_lead' ? `\nTeam Lead: "Jyoti demos", "all demos"\n` : '') +
    `Hinglish bhi chalega!\n— Onsite Pulse`;
}

// === DEMOS ===
else if (intent === 'demos') {
  const fields = wantsNotes ? 'Full_Name, Company, Demo_Done_Date, Business_Type, Description' : 'Full_Name, Company, Demo_Done_Date';
  const demoCount = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Demo_Done_Date between '${MONTH_START}' and '${MONTH_END}'`);
  const bookedCount = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Lead_Status = '6. Demo booked'`);
  const demoLeads = await qPage(`SELECT ${fields} FROM Leads WHERE (${ownerFilter}) AND Demo_Done_Date between '${MONTH_START}' and '${MONTH_END}' ORDER BY Demo_Done_Date DESC`);

  reply = `${displayName}'s Demos — ${MONTH_NAME}\n\n`;
  reply += `Demos Done: ${demoCount}\n`;
  reply += `Demos Booked (pending): ${bookedCount}\n\n`;

  if (demoLeads.length > 0) {
    const limit = wantsNotes ? 8 : 5;
    reply += wantsNotes ? `Demos with notes:\n` : `Recent demos:\n`;
    demoLeads.slice(0, limit).forEach((l, i) => {
      const name = l.Company || l.Full_Name || '?';
      const date = (l.Demo_Done_Date || '').slice(0, 10);
      reply += `${i+1}. ${name} — ${date}\n`;
      if (wantsNotes) {
        const remark = (l.Business_Type || '').trim();
        const desc = (l.Description || '').trim();
        if (remark) reply += `   Remarks: ${remark.slice(0, 120)}\n`;
        if (desc) reply += `   Notes: ${desc.slice(0, 120)}\n`;
        if (!remark && !desc) reply += `   (no notes)\n`;
      }
    });
    if (demoLeads.length > limit) reply += `...+${demoLeads.length - limit} more\n`;
  }
  reply += `\nKeep going ${displayName}!\n— Onsite Pulse`;
}

// === SALES ===
else if (intent === 'sales') {
  const salesFields = wantsNotes ? 'Full_Name, Company, Annual_Revenue, Sale_Done_Date, Business_Type, Description' : 'Full_Name, Company, Annual_Revenue, Sale_Done_Date';
  const salesLeads = await qPage(`SELECT ${salesFields} FROM Leads WHERE (${ownerFilter}) AND Sale_Done_Date between '${MONTH_START}' and '${MONTH_END}' ORDER BY Sale_Done_Date DESC`);
  const salesCount = salesLeads.length;
  let totalRevenue = 0;
  salesLeads.forEach(l => { totalRevenue += Number(l.Annual_Revenue) || 0; });

  reply = `${displayName}'s Sales — ${MONTH_NAME}\n\n`;
  reply += `Sales Closed: ${salesCount}\n`;
  reply += `Total Revenue: Rs. ${fmtINR(totalRevenue)}\n\n`;

  if (salesLeads.length > 0) {
    reply += `Closures:\n`;
    salesLeads.slice(0, 8).forEach((l, i) => {
      const name = l.Company || l.Full_Name || '?';
      const rev = Number(l.Annual_Revenue) || 0;
      reply += `${i+1}. ${name}${rev ? ` — Rs. ${fmtINR(rev)}` : ''}\n`;
      if (wantsNotes) {
        const remark = (l.Business_Type || '').trim();
        const desc = (l.Description || '').trim();
        if (remark) reply += `   Remarks: ${remark.slice(0, 120)}\n`;
        if (desc) reply += `   Notes: ${desc.slice(0, 120)}\n`;
        if (!remark && !desc) reply += `   (no notes)\n`;
      }
    });
    if (salesLeads.length > 8) reply += `...+${salesLeads.length - 8} more\n`;
  }
  reply += salesCount > 0 ? `\nGreat work! Keep the momentum!` : `\nMonth abhi baaki hai — let's close some!`;
  reply += `\n— Onsite Pulse`;
}

// === PIPELINE ===
else if (intent === 'pipeline') {
  const vhp = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Sales_Stage = 'Very High Prospect'`);
  const hp = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Sales_Stage = 'High Prospect'`);
  const prospect = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Sales_Stage = '1. Prospect'`);

  reply = `${displayName}'s Pipeline\n\n`;
  reply += `Very High Prospect: ${vhp}\n`;
  reply += `High Prospect: ${hp}\n`;
  reply += `Prospect: ${prospect}\n`;
  reply += `\nTotal hot leads: ${vhp + hp + prospect}\n`;
  reply += vhp > 0 ? `\n${vhp} VHP leads — follow up TODAY!` : `\nFocus on converting prospects to HP!`;
  reply += `\n— Onsite Pulse`;
}

// === FOLLOW-UPS ===
else if (intent === 'followups') {
  const overdue = await qPage(`SELECT Full_Name, Company, Lead_Task FROM Leads WHERE (${ownerFilter}) AND Lead_Task is not null AND Lead_Task < '${TODAY}T00:00:00+05:30'`);
  const todayTasks = await qPage(`SELECT Full_Name, Company, Lead_Task FROM Leads WHERE (${ownerFilter}) AND Lead_Task >= '${TODAY}T00:00:00+05:30' AND Lead_Task <= '${TODAY}T23:59:59+05:30'`);

  reply = `${displayName}'s Follow-Ups\n\n`;
  reply += `Due Today: ${todayTasks.length}\n`;
  reply += `Overdue: ${overdue.length}\n\n`;

  if (todayTasks.length > 0) {
    reply += `Today's calls:\n`;
    todayTasks.slice(0, 5).forEach((l, i) => {
      reply += `${i+1}. ${l.Company || l.Full_Name || '?'}\n`;
    });
  }
  if (overdue.length > 0) {
    reply += `\nOverdue (needs attention):\n`;
    overdue.slice(0, 3).forEach((l, i) => {
      reply += `${i+1}. ${l.Company || l.Full_Name || '?'} — was due ${(l.Lead_Task || '').slice(0, 10)}\n`;
    });
  }
  reply += `\n— Onsite Pulse`;
}

// === RANK ===
else if (intent === 'rank') {
  const allReps = await qPage(`SELECT Leads_Owner, Sale_Done_Date FROM Leads WHERE Sale_Done_Date between '${MONTH_START}' and '${MONTH_END}'`);

  const ranks = {};
  (allReps || []).forEach(r => {
    const owner = CRM_OWNER_MAP[r.Leads_Owner] || r.Leads_Owner;
    ranks[owner] = (ranks[owner] || 0) + 1;
  });

  const sorted = Object.entries(ranks).sort((a, b) => b[1] - a[1]);
  const myRank = sorted.findIndex(([n]) => n === repName) + 1;
  const myCount = ranks[repName] || 0;

  reply = `Team Leaderboard — ${MONTH_NAME}\n\n`;
  sorted.slice(0, 5).forEach(([name, count], i) => {
    const medal = i === 0 ? '#1' : i === 1 ? '#2' : i === 2 ? '#3' : `#${i+1}`;
    const marker = name === repName ? ' <-- YOU' : '';
    reply += `${medal} ${name}: ${count} sales${marker}\n`;
  });

  if (myRank > 5) reply += `\n...you're at #${myRank} with ${myCount} sales`;
  reply += myRank <= 3 ? `\n\nTop 3! Amazing work ${repName}!` : `\n\nLet's climb up! Every demo counts`;
  reply += `\n— Onsite Pulse`;
}

// === TARGET ===
else if (intent === 'target') {
  const mySales = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Sale_Done_Date between '${MONTH_START}' and '${MONTH_END}'`);
  const myDemos = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Demo_Done_Date between '${MONTH_START}' and '${MONTH_END}'`);
  const daysLeft = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate() - DAY_NUM;

  reply = `${displayName}'s Progress — ${MONTH_NAME}\n\n`;
  reply += `Demos Done: ${myDemos}\n`;
  reply += `Sales Closed: ${mySales}\n`;
  reply += `Days Left: ${daysLeft}\n\n`;
  reply += `Conversion Rate: ${myDemos > 0 ? Math.round(mySales / myDemos * 100) : 0}%\n`;
  reply += daysLeft > 15 ? `\nStill plenty of time — keep pushing!` : `\nFinal stretch! Close those hot leads NOW!`;
  reply += `\n— Onsite Pulse`;
}

// === NOTES (standalone — recent leads with remarks/notes) ===
else if (intent === 'notes') {
  const notesLeads = await qPage(`SELECT Full_Name, Company, Business_Type, Description, Modified_Time FROM Leads WHERE (${ownerFilter}) ORDER BY Modified_Time DESC`);

  reply = `${displayName}'s Recent Notes\n\n`;
  if (notesLeads.length > 0) {
    let shown = 0;
    for (const l of notesLeads) {
      if (shown >= 10) break;
      const remark = (l.Business_Type || '').trim();
      const desc = (l.Description || '').trim();
      if (!remark && !desc) continue;
      const name = l.Company || l.Full_Name || '?';
      const date = (l.Modified_Time || '').slice(0, 10);
      reply += `${shown+1}. ${name} (${date})\n`;
      if (remark) reply += `   Remarks: ${remark.slice(0, 150)}\n`;
      if (desc) reply += `   Notes: ${desc.slice(0, 150)}\n`;
      reply += `\n`;
      shown++;
    }
    if (shown === 0) reply += `No notes found for your leads.\n`;
    else if (notesLeads.length > 10) reply += `...+${notesLeads.length - 10} more leads with notes\n`;
  } else {
    reply += `No notes found. Add remarks in CRM for better tracking!\n`;
  }
  reply += `Tip: "demos with notes" or "sales with notes" for specific views\n— Onsite Pulse`;
}

// === LEAD SEARCH (by phone, name, or company) ===
else if (intent === 'lead_search') {
  let searchFilter = '';
  let searchLabel = '';
  if (searchPhone) {
    const ph = searchPhone.replace(/[^0-9]/g, '');
    // Try partial match — last 10 digits
    const ph10 = ph.slice(-10);
    searchFilter = `Phone like '%${ph10}%' OR Mobile like '%${ph10}%'`;
    searchLabel = `phone ${ph10}`;
  } else if (searchCompany || searchName) {
    // Use the first significant keyword (2+ words → first 2, else first word)
    const raw = (searchCompany || searchName || '').replace(/'/g, "\\'");
    const words = raw.split(/\s+/).filter(w => w.length > 1);
    // Search both Company AND Full_Name with first keyword for broader match
    const kw = words[0] || raw;
    searchFilter = `Company like '%${kw}%' OR Full_Name like '%${kw}%'`;
    searchLabel = searchCompany ? `company "${searchCompany}"` : `name "${searchName}"`;
  } else {
    reply = `Please provide a phone number, lead name, or company name to search.\n\nExamples:\n"find lead 9876543210"\n"search company ABC Builders"\n"lead named Rahul"\n— Onsite Pulse`;
  }

  if (searchFilter && !reply) {
    // Search without scope in COQL (like + complex OR breaks Zoho), filter by role in JS
    const rawResults = await qPage(`SELECT id, Full_Name, Company, Phone, Mobile, Leads_Owner, Sales_Stage, Lead_Status, Annual_Revenue, Business_Type, Description, Demo_Done_Date, Sale_Done_Date FROM Leads WHERE (${searchFilter}) ORDER BY Modified_Time DESC`);

    // Build allowed owner names for this user's role
    let results = rawResults;
    if (myRole !== 'admin') {
      const allowed = new Set();
      const names = myRole === 'team_lead' ? [repName, ...(LEAD_ACCESS[repName] || [])] : [repName];
      names.forEach(n => {
        allowed.add(n);
        Object.entries(CRM_OWNER_MAP).forEach(([k, v]) => { if (v === n) allowed.add(k); });
      });
      results = rawResults.filter(l => allowed.has(l.Leads_Owner));
    }

    reply = `Search: ${searchLabel}\n\n`;
    if (results.length === 0) {
      reply += `No leads found. Try a different search term.`;
    } else {
      reply += `Found ${results.length} lead${results.length > 1 ? 's' : ''}:\n\n`;
      // For top 3 results, also fetch Zoho Notes (related list)
      const topResults = results.slice(0, 5);
      for (let i = 0; i < topResults.length; i++) {
        const l = topResults[i];
        const name = l.Full_Name || '?';
        const comp = l.Company ? ` (${l.Company})` : '';
        const phone = l.Phone || l.Mobile || '';
        const owner = CRM_OWNER_MAP[l.Leads_Owner] || l.Leads_Owner || '';
        const stage = l.Sales_Stage || l.Lead_Status || '';
        const rev = Number(l.Annual_Revenue) || 0;
        reply += `${i+1}. ${name}${comp}\n`;
        if (phone) reply += `   Phone: ${phone}\n`;
        if (owner) reply += `   Owner: ${owner}\n`;
        if (stage) reply += `   Stage: ${stage}\n`;
        if (rev) reply += `   Revenue: Rs. ${fmtINR(rev)}\n`;
        if (l.Demo_Done_Date) reply += `   Demo: ${(l.Demo_Done_Date || '').slice(0, 10)}\n`;
        if (l.Sale_Done_Date) reply += `   Sale: ${(l.Sale_Done_Date || '').slice(0, 10)}\n`;
        const remark = (l.Business_Type || '').trim();
        const desc = (l.Description || '').trim();
        if (remark) reply += `   Remarks: ${remark.slice(0, 150)}\n`;
        if (desc) reply += `   Description: ${desc.slice(0, 150)}\n`;
        // Fetch Zoho Notes (related list) for this lead
        if (l.id && i < 3) {
          try {
            const t = await getToken();
            const notesResp = await http({method:'GET',
              url:`https://www.zohoapis.in/crm/v7/Leads/${l.id}/Notes?fields=Note_Content,Note_Title,Created_Time,Modified_Time`,
              headers:{Authorization:`Zoho-oauthtoken ${t}`}});
            const notesData = typeof notesResp === 'string' ? JSON.parse(notesResp) : notesResp;
            if (notesData?.data?.length > 0) {
              reply += `   CRM Notes:\n`;
              notesData.data.slice(0, 3).forEach(n => {
                // Strip HTML tags from Note_Content
                let noteText = (n.Note_Content || n.Note_Title || '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
                const noteDate = (n.Modified_Time || n.Created_Time || '').slice(0, 10);
                if (noteText) reply += `   - ${noteDate}: ${noteText.slice(0, 250)}\n`;
              });
            }
          } catch(e) { /* notes API failed, skip */ }
        }
        reply += `\n`;
      }
      if (results.length > 5) reply += `...+${results.length - 5} more\n`;
    }
    reply += `\n— Onsite Pulse`;
  }
}

// === SALES ASSISTANT (AI-powered with full Onsite knowledge) ===
else if (intent === 'assistant') {
  // Build lead context from memory for personalized answers
  let leadInfo = '';
  const lastCtx = chatHistory.length > 0 ? chatHistory[chatHistory.length - 1]?.lead_context : null;
  if (lastCtx?.lead_name) leadInfo = `\nThe rep was recently discussing lead: ${lastCtx.lead_name}${lastCtx.lead_phone ? ` (${lastCtx.lead_phone})` : ''}. Use this context if relevant.`;

  const ONSITE_KNOWLEDGE = `You are the Onsite Pulse Sales Assistant for Onsite Teams — a construction management SaaS.

ABOUT ONSITE:
- Construction Management Software & ERP (SaaS) — Project, Material, Labor, Finance, Procurement, Quality, Design modules
- 10,000+ companies, ISO certified, mobile-first, implementation in 1-2 weeks
- Website: onsiteteams.com | Founded 2021 | Office: Noida, UP

PRICING (National — INR, +18% GST):
- Business: Rs.12,000/user/year — Payments, Files, Attendance, Salary, CRM, Inventory, Tasks, Issues, Subcon
- Business+: Rs.15,000/user/year — All Business + Design Mgmt, BOQ/RA Bills, Budget Control, Warehouse, RFQ, POs, Assets, Payroll, Inspection, Multi-Level Approval
- Enterprise: Rs.12,00,000 lump sum — Unlimited Users, GPS, Custom Dashboards, Tally/Zoho Integration, Vendor/Client Portals, White Label
- Add-ons: GPS Attendance 20K, Additional Company 20K, Tally Integration 20K+5K AMC, Additional Users 5K/user/year

PRICING (International — USD, no GST):
- Business: $200/user/year | Business+: $250/user/year | Enterprise: $15,000 lump sum
- White Label: Web $3,600, Android $4,200, iOS $4,800
- Add-ons: GPS $300, Additional Company $300, Additional Users $60/user/year

KEY USPs:
- 10-20x cheaper than Procore ($200/user/year vs $2,388-4,500)
- Mobile-first (site workers use phones, Hindi support)
- 1-2 week implementation (vs months for traditional ERP)
- Up to 7% cost savings on projects
- ISO certified, RERA & GST compliant

COMPETITORS:
India: Powerplay (700K users, budget), NYGGS (AI/IoT, infra), StrategicERP (flexible), RDash (9K projects)
Global: Procore ($199-375/user/mo), Buildertrend ($299-499/mo), PlanGrid ($39-199/user/mo), Fieldwire, Oracle Aconex

OBJECTION HANDLING:
- "Too expensive" → ROI: 7% savings on 10Cr project = 70L saved. One material theft > annual subscription
- "My team can't use it" → Mobile-first, Hindi, on-site training. Simpler than WhatsApp groups
- "We use Excel" → Show time saved, error reduction, real-time visibility across sites
- "Data security" → ISO certified, enterprise cloud, data ownership guarantee
- "Not the right time" → Cost overruns happening NOW. Every month without tracking = money lost
- "Already using competitor" → Integration possible, feature comparison, lower cost

SALES APPROACH:
- Builders are phone-first, relationship-driven — calls > emails
- Lead with ROI numbers, not features: "save 2 hours daily" beats "AI-powered"
- Short 15-20 min demos beat hour-long presentations
- Free trial / pilot on one site reduces risk
- Construction buyers are first-time software buyers — educate WHY before WHICH
- WhatsApp follow-ups work better than email in construction

BUYER PAIN POINTS:
1. Manual processes (57%) — paper DPRs, Excel, WhatsApp chaos
2. Cost overruns (10-30%) — no budget visibility, material wastage
3. Multi-site chaos — no single source of truth
4. Cash flow blindness — manual RA billing
5. Compliance headaches — GST, RERA, labor laws

EMAIL/MESSAGE TEMPLATES STYLE:
- Keep it short (3-4 lines max for WhatsApp, 5-6 for email)
- Start with pain point or value, not features
- Use INR for Indian clients, USD for international
- Include specific ROI numbers
- End with clear CTA (call/demo/trial)
- Tone: professional but practical, not salesy

CONSTRUCTION TERMS:
DPR = Daily Progress Report, RA Bills = Running Account Bills, BOQ = Bill of Quantities, RFQ = Request for Quotation, PO = Purchase Order, AMC = Annual Maintenance Contract
${leadInfo}
${conversationContext}`;

  try {
    const assistResp = await http({
      method: 'POST',
      url: 'https://openrouter.ai/api/v1/chat/completions',
      headers: { 'Authorization': `Bearer ${OR_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'x-ai/grok-4.1-fast',
        max_tokens: 800,
        temperature: 0.3,
        messages: [
          { role: 'system', content: ONSITE_KNOWLEDGE },
          { role: 'user', content: `I am ${repName}, a sales rep at Onsite Teams. ${msg}` }
        ]
      })
    });
    const aParsed = typeof assistResp === 'string' ? JSON.parse(assistResp) : assistResp;
    reply = (aParsed?.choices?.[0]?.message?.content || '').trim();
    if (!reply) reply = 'Sorry, could not generate a response. Try rephrasing your question.';
    reply += `\n\n— Onsite Pulse Assistant`;
  } catch(e) {
    reply = `Sorry ${repName}, assistant is temporarily unavailable. Try again in a moment.\n— Onsite Pulse`;
  }
}

// === GENERAL CHAT (AI-powered reply) ===
else {
  if (aiReply) {
    reply = aiReply + `\n\nNeed help? Try "write a follow-up email", "our pricing", "how to handle objection", or say "help".\n— Onsite Pulse`;
  } else {
    const funReplies = [
      `Hey ${repName}! Samajh nahi aaya — Try "my demos", "our pricing", "write a follow-up email", or "help"!`,
      `${repName}, I can help with sales data AND sales coaching! Type "help" for everything I can do`,
      `Hmm interesting ${repName}... try asking about pricing, pipeline, or "help me close this deal"!`,
      `${repName}, mere paas data bhi hai aur sales tips bhi! Type "help" for options`,
    ];
    reply = funReplies[Math.floor(Math.random() * funReplies.length)];
  }
}

// === SEND TO WHATSAPP (auto for useful intents) ===
// Look up rep's phone number
const ALL_PHONES = {...MGR, ...REPS, ...PRE_SALES};
const repPhone = ALL_PHONES[repName];
let sentToWA = false;

// Auto-send to WhatsApp for: assistant, followups, lead_search, demos/sales with notes, or any long reply
const waIntents = ['assistant', 'followups', 'lead_search'];
const shouldSendWA = repPhone && reply && intent !== 'greeting' && intent !== 'help' && intent !== 'chat' && (
  waIntents.includes(intent) ||
  (wantsNotes && ['demos', 'sales', 'notes'].includes(intent)) ||
  reply.length > 500
);

if (shouldSendWA) {
  try {
    // Clean markdown bold/italic for WhatsApp (** → *, keep single *)
    const waMsg = `Pulse Chat — ${repName}\nQ: ${msg}\n\n${reply.replace(/\*\*/g, '*')}`;
    await wa(repPhone, waMsg.slice(0, 4096), repName);
    sentToWA = true;
    reply += `\n\nSent to your WhatsApp`;
  } catch(e) { /* WA send failed — non-critical */ }
}

// === STORE TO MEMORY ===
// Build lead context from search results if applicable
let leadCtx = {};
if (intent === 'lead_search' && searchPhone) leadCtx.lead_phone = searchPhone;
if (intent === 'lead_search' && (searchName || searchCompany)) leadCtx.lead_name = searchName || searchCompany;
// Carry forward lead context from last message if user is referencing "same lead"
if (chatHistory.length > 0 && !leadCtx.lead_name && !leadCtx.lead_phone) {
  const lastCtx = chatHistory[chatHistory.length - 1]?.lead_context;
  if (lastCtx?.lead_name || lastCtx?.lead_phone) {
    if (/\b(same|that|this|uska|iska|wahi|us|is)\b/i.test(msg)) leadCtx = lastCtx;
  }
}
// Store conversation (non-blocking)
sbStore(repName, msg, reply, intent, leadCtx).catch(() => {});

return [{ json: { reply, status: 'ok', intent, repName, sentToWA } }];
"""

# === WORKFLOW DEFINITIONS ===

WORKFLOWS = {
    "1": {
        "name": "Onsite: Follow-Up Alerts",
        "cron": "0 8-20 * * 1-6",  # Hourly 8 AM - 8 PM IST, Mon-Sat
        "js": AUTO_1_JS,
        "description": "Hourly 8 AM-8 PM Mon-Sat — Follow-up alerts (full briefing at 8 AM, hourly nudges after)",
    },
    "2": {
        "name": "Onsite: Demo Stuck Alert",
        "cron": "0 9 * * *",  # Daily 9 AM IST
        "js": AUTO_2_JS,
        "description": "Daily 9 AM — Leads stuck in 'Demo Booked' status",
    },
    "3": {
        "name": "Onsite: Daily Scorecard",
        "cron": "15 9 * * *",  # Daily 9:15 AM IST
        "js": AUTO_3_JS,
        "description": "Daily 9:15 AM — MTD demos, sales, pipeline summary",
    },
    "4": {
        "name": "Onsite: CRM Hygiene Report",
        "cron": "0 17 * * 5",  # Friday 5 PM IST
        "js": AUTO_4_JS,
        "description": "Friday 5 PM — CRM data quality report",
    },
    "5": {
        "name": "Onsite: Hot Source Alert",
        "cron": "0 8,14 * * 1-6",  # 8 AM + 2 PM IST, Mon-Sat
        "js": AUTO_5_JS,
        "description": "8 AM + 2 PM Mon-Sat — Website & WhatsApp lead priority alerts",
    },
    "6": {
        "name": "Onsite: Ad Fatigue Alert",
        "cron": "0 9 * * 1",  # Monday 9 AM IST
        "js": AUTO_6_JS,
        "description": "Monday 9 AM — Facebook ad fatigue & dying campaign alerts",
    },
    "7": {
        "name": "Onsite: Daily Session Opener",
        "cron": "30 9 * * 1-6",  # 9:30 AM IST Mon-Sat
        "js": AUTO_7_JS,
        "description": "9:30 AM Mon-Sat — Sends personalized morning kickoff template to team",
    },
    "8": {
        "name": "Onsite: Pulse Bot",
        "webhook": True,
        "webhook_path": "onsite-pulse-bot",
        "js": AUTO_8_JS,
        "description": "Webhook — Interactive WhatsApp bot (responds to team messages)",
    },
    "9": {
        "name": "Onsite: Pulse Chat",
        "webhook": True,
        "webhook_path": "pulse-chat",
        "js": AUTO_9_JS,
        "description": "Webhook — Web chat interface for team to query their CRM data",
    },
}


def get_fb_token():
    """Try to read FB token from various sources."""
    import os
    # Try .env
    env_path = "/Volumes/Dhruv_SSD/AIwithDhruv/Claude/Onsite/sales-intelligence/backend/.env"
    try:
        with open(env_path) as f:
            for line in f:
                if line.startswith("FB_ACCESS_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"')
    except FileNotFoundError:
        pass

    # Try MCP settings
    settings_path = os.path.expanduser("~/.claude/projects/-Volumes-Dhruv-SSD-AIwithDhruv-Claude/settings.json")
    try:
        import json as j
        with open(settings_path) as f:
            settings = j.load(f)
            for server in settings.get("mcpServers", {}).values():
                env = server.get("env", {})
                if "FB_ACCESS_TOKEN" in env:
                    return env["FB_ACCESS_TOKEN"]
    except (FileNotFoundError, Exception):
        pass

    return ""


def build_workflow_json(num: str) -> dict:
    """Build n8n workflow JSON for a given automation number."""
    import uuid
    wf = WORKFLOWS[num]
    js_code = SHARED_JS + wf["js"]

    # Inject credentials from environment
    _env_replacements = {
        "%ZOHO_CID%": os.environ.get("ZOHO_CID", ""),
        "%ZOHO_CS%": os.environ.get("ZOHO_CS", ""),
        "%ZOHO_RT%": os.environ.get("ZOHO_RT", ""),
        "%GALLABOX_KEY%": os.environ.get("GALLABOX_KEY", ""),
        "%GALLABOX_SECRET%": os.environ.get("GALLABOX_SECRET", ""),
        "%GALLABOX_CHANNEL%": os.environ.get("GALLABOX_CHANNEL", ""),
        "%SUPABASE_URL%": os.environ.get("SUPABASE_URL", ""),
        "%SUPABASE_KEY%": os.environ.get("SUPABASE_KEY", ""),
        "%OPENROUTER_KEY%": os.environ.get("OPENROUTER_KEY", ""),
    }
    for placeholder, value in _env_replacements.items():
        js_code = js_code.replace(placeholder, value)

    # Inject FB token for automation 6
    if num == "6":
        fb_token = get_fb_token()
        js_code = js_code.replace("%FB_TOKEN%", fb_token)

    # Webhook-triggered workflow (e.g., interactive bot)
    if wf.get("webhook"):
        return {
            "name": wf["name"],
            "nodes": [
                {
                    "parameters": {
                        "httpMethod": "POST",
                        "path": wf["webhook_path"],
                        "responseMode": "responseNode",
                    },
                    "name": "Webhook",
                    "type": "n8n-nodes-base.webhook",
                    "typeVersion": 2,
                    "position": [0, 0],
                    "id": str(uuid.uuid4()),
                    "webhookId": str(uuid.uuid4()),
                },
                {
                    "parameters": {
                        "mode": "runOnceForAllItems",
                        "jsCode": js_code,
                    },
                    "name": "Run Automation",
                    "type": "n8n-nodes-base.code",
                    "typeVersion": 2,
                    "position": [300, 0],
                    "id": str(uuid.uuid4()),
                },
                {
                    "parameters": {
                        "respondWith": "json",
                        "responseBody": "={{ $json }}",
                    },
                    "name": "Respond",
                    "type": "n8n-nodes-base.respondToWebhook",
                    "typeVersion": 1.1,
                    "position": [600, 0],
                    "id": str(uuid.uuid4()),
                },
            ],
            "connections": {
                "Webhook": {
                    "main": [
                        [{"node": "Run Automation", "type": "main", "index": 0}]
                    ]
                },
                "Run Automation": {
                    "main": [
                        [{"node": "Respond", "type": "main", "index": 0}]
                    ]
                },
            },
            "settings": {
                "executionOrder": "v1",
                "timezone": "Asia/Kolkata",
                "availableInMCP": True,
            },
        }

    # Schedule-triggered workflow (default)
    return {
        "name": wf["name"],
        "nodes": [
            {
                "parameters": {
                    "rule": {
                        "interval": [
                            {"field": "cronExpression", "expression": wf["cron"]}
                        ]
                    }
                },
                "name": "Schedule",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.3,
                "position": [0, 0],
                "id": str(uuid.uuid4()),
            },
            {
                "parameters": {
                    "mode": "runOnceForAllItems",
                    "jsCode": js_code,
                },
                "name": "Run Automation",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [300, 0],
                "id": str(uuid.uuid4()),
            },
        ],
        "connections": {
            "Schedule": {
                "main": [
                    [{"node": "Run Automation", "type": "main", "index": 0}]
                ]
            }
        },
        "settings": {
            "executionOrder": "v1",
            "timezone": "Asia/Kolkata",
            "availableInMCP": True,
        },
    }


def deploy_workflow(num: str) -> dict:
    """Deploy a workflow to n8n via REST API."""
    wf_json = build_workflow_json(num)
    wf = WORKFLOWS[num]

    data = json.dumps(wf_json).encode()
    headers = {
        "Content-Type": "application/json",
        "X-N8N-API-KEY": N8N_API_KEY,
    }
    req = urllib.request.Request(
        f"{N8N_HOST}/api/v1/workflows",
        data=data,
        headers=headers,
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        wf_id = result.get("id", "?")
        print(f"  OK — {wf['name']} → ID: {wf_id}")
        return result
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"  FAILED — {wf['name']}: {e} | {body[:200]}")
        return {"error": str(e), "body": body}


def activate_workflow(wf_id: str) -> dict:
    """Activate a workflow by ID."""
    headers = {
        "Content-Type": "application/json",
        "X-N8N-API-KEY": N8N_API_KEY,
    }
    req = urllib.request.Request(
        f"{N8N_HOST}/api/v1/workflows/{wf_id}/activate",
        headers=headers,
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": str(e)}


def list_onsite_workflows():
    """List existing Onsite workflows on n8n."""
    headers = {"X-N8N-API-KEY": N8N_API_KEY}
    req = urllib.request.Request(f"{N8N_HOST}/api/v1/workflows?limit=100", headers=headers)
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        workflows = result.get("data", [])
        onsite = [w for w in workflows if w.get("name", "").startswith("Onsite:")]
        if onsite:
            print(f"\n=== ONSITE WORKFLOWS ON N8N ({len(onsite)}) ===\n")
            for w in onsite:
                status = "ACTIVE" if w.get("active") else "INACTIVE"
                print(f"  [{status}] {w['name']} (ID: {w['id']})")
        else:
            print("\nNo Onsite workflows found on n8n.")
        return onsite
    except urllib.error.HTTPError as e:
        print(f"Error: {e}")
        return []


def main():
    args = sys.argv[1:]

    if "--list" in args:
        list_onsite_workflows()
        return

    # Which to deploy
    nums = [a for a in args if a.isdigit() and a in WORKFLOWS]
    if not nums:
        nums = list(WORKFLOWS.keys())

    print(f"=== DEPLOYING {len(nums)} ONSITE WORKFLOWS TO N8N ===\n")
    print(f"Target: {N8N_HOST}\n")

    results = {}
    for num in nums:
        wf = WORKFLOWS[num]
        print(f"[{num}] {wf['name']} — {wf['description']}")
        print(f"    Schedule: {wf.get('cron', 'webhook')}")
        result = deploy_workflow(num)
        results[num] = result

    print(f"\n{'='*60}")
    print(f"Deployed {len(nums)} workflows (all INACTIVE)")
    print(f"Go to {N8N_HOST} to review and activate them.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

/**
 * Smart Data Management Layer v2
 *
 * - IndexedDB persistence via Dexie (survives refresh)
 * - Smart merge on re-upload (dedup by zoho_lead_id)
 * - Phone merge: same phone + different lead IDs → merge into best record
 *   - Keep older user_date (first contact)
 *   - Keep newer lead_source_date
 *   - Combine notes
 *   - Keep higher-priority status
 *   - Merge all enrichment fields
 * - Upload history tracking
 * - Designed for future API/webhook integration
 */

import Dexie, { type Table } from 'dexie'

// ─── Types ───────────────────────────────────────────────────────────────────

export interface LeadRecord {
  _id?: number
  zoho_lead_id: string
  _phone_norm?: string
  _merged_from?: string    // comma-separated zoho_lead_ids merged into this record
  _source: string
  _updated_at: string
  [key: string]: unknown
}

export interface UploadRecord {
  id?: number
  timestamp: string
  fileName: string
  totalRows: number
  newLeads: number
  updatedLeads: number
  unchangedLeads: number
  phoneMerged: number
  duration_ms: number
  changesSummary: FieldChangeSummary[]
}

export interface FieldChangeSummary {
  field: string
  count: number
}

export interface MergeResult {
  newLeads: number
  updatedLeads: number
  unchangedLeads: number
  phoneMerged: number
  totalProcessed: number
  totalAfterMerge: number
  duration_ms: number
  changesByField: FieldChangeSummary[]
  phoneMergeDetails: PhoneMergeDetail[]
}

export interface PhoneMergeDetail {
  phone: string
  keptLeadId: string
  keptName: string
  mergedCount: number
  mergedIds: string[]
}

// ─── Status priority (higher number = more advanced / keep this one) ─────────

const STATUS_PRIORITY: Record<string, number> = {
  'Purchased': 100,
  'Paid User': 95,
  'Sale Done': 90,
  'Renewed': 85,
  'Upgraded': 80,
  'Demo Done': 70,
  'Session Completed': 68,
  'Demo Booked': 65,
  'Session scheduled': 63,
  'Priority': 60,
  'High Prospect': 58,
  'Very High Prospect': 57,
  'Qualified': 55,
  'Follow Up': 50,
  'Trial Activated': 45,
  'User not attend session': 30,
  'Contacted': 25,
  'Not Interested': 20,
  'DTA': 15,
  'Rejected': 10,
  '': 0,
}

function getStatusPriority(status: string): number {
  return STATUS_PRIORITY[status] ?? 35
}

const STAGE_PRIORITY: Record<string, number> = {
  '3. Sale Done': 100,
  '4. Secondary Sales': 95,
  'Very High Prospect': 80,
  'High Prospect': 70,
  '1. Prospect': 60,
  'Not Able to Connect after Prospect': 40,
  '2. Not Interested After Demo': 30,
  '': 0,
}

function getStagePriority(stage: string): number {
  return STAGE_PRIORITY[stage] ?? 20
}

// ─── Tracked fields for change detection ─────────────────────────────────────

const TRACKED_FIELDS = [
  'lead_status', 'sales_stage', 'lead_notes', 'last_touched_date_new',
  'last_touched_date', 'deal_owner', 'demo_done', 'sale_done',
  'demo_booked', 'trial_activated', 'lead_source', 'call_disposition',
  'lead_category', 'lead_category_1', 'pre_qualification', 'is_prospect',
  'is_high_prospect', 'lead_priority', 'price_pitched', 'lead_assigned',
  'upgrade_done', 'renewal_done', 'onboarding_session_stage', 'remark',
  'annual_revenue', 'sale_done_date', 'lead_source_date',
]

// ─── Database ────────────────────────────────────────────────────────────────

class OnsiteDB extends Dexie {
  leads!: Table<LeadRecord>
  uploads!: Table<UploadRecord>

  constructor() {
    super('onsite-intelligence')
    this.version(2).stores({
      leads: '++_id, zoho_lead_id, _phone_norm, _source',
      uploads: '++id, timestamp',
    })
  }
}

const db = new OnsiteDB()

// ─── Phone normalization ─────────────────────────────────────────────────────

function normalizePhone(phone: string | undefined): string {
  if (!phone) return ''
  const digits = phone.replace(/[^0-9]/g, '')
  return digits.length >= 10 ? digits.slice(-10) : digits
}

// ─── Date comparison helpers ─────────────────────────────────────────────────

function parseLooseDate(str: string | undefined): Date | null {
  if (!str || !str.trim()) return null
  const d = new Date(str)
  return isNaN(d.getTime()) ? null : d
}

function keepOlderDate(a: string | undefined, b: string | undefined): string {
  const da = parseLooseDate(String(a ?? ''))
  const db2 = parseLooseDate(String(b ?? ''))
  if (!da && !db2) return ''
  if (!da) return String(b ?? '')
  if (!db2) return String(a ?? '')
  return da <= db2 ? String(a ?? '') : String(b ?? '')
}

function keepNewerDate(a: string | undefined, b: string | undefined): string {
  const da = parseLooseDate(String(a ?? ''))
  const db2 = parseLooseDate(String(b ?? ''))
  if (!da && !db2) return ''
  if (!da) return String(b ?? '')
  if (!db2) return String(a ?? '')
  return da >= db2 ? String(a ?? '') : String(b ?? '')
}

// ─── Notes merge (combine unique notes) ──────────────────────────────────────

function mergeNotes(a: string | undefined, b: string | undefined): string {
  const na = String(a ?? '').trim()
  const nb = String(b ?? '').trim()
  if (!na) return nb
  if (!nb) return na
  if (na === nb) return na
  if (na.includes(nb)) return na
  if (nb.includes(na)) return nb
  return `${na}\n---\n${nb}`
}

// ─── Merge two lead records (phone dedup) ────────────────────────────────────

function mergeLeadRecords(primary: LeadRecord, secondary: LeadRecord): Partial<LeadRecord> {
  const changes: Partial<LeadRecord> = {}

  // user_date: keep the OLDER one (first contact)
  const olderUserDate = keepOlderDate(
    String(primary.user_date ?? ''),
    String(secondary.user_date ?? '')
  )
  if (olderUserDate && olderUserDate !== String(primary.user_date ?? '')) {
    changes.user_date = olderUserDate
  }

  // lead_source_date: keep the NEWER one
  const newerSourceDate = keepNewerDate(
    String(primary.lead_source_date ?? ''),
    String(secondary.lead_source_date ?? '')
  )
  if (newerSourceDate && newerSourceDate !== String(primary.lead_source_date ?? '')) {
    changes.lead_source_date = newerSourceDate
  }

  // last_touched_date_new: keep NEWER
  const newerTouch = keepNewerDate(
    String(primary.last_touched_date_new ?? ''),
    String(secondary.last_touched_date_new ?? '')
  )
  if (newerTouch && newerTouch !== String(primary.last_touched_date_new ?? '')) {
    changes.last_touched_date_new = newerTouch
  }

  // lead_status: keep higher priority
  const pStatus = String(primary.lead_status ?? '')
  const sStatus = String(secondary.lead_status ?? '')
  if (getStatusPriority(sStatus) > getStatusPriority(pStatus)) {
    changes.lead_status = sStatus
  }

  // sales_stage: keep higher priority
  const pStage = String(primary.sales_stage ?? '')
  const sStage = String(secondary.sales_stage ?? '')
  if (getStagePriority(sStage) > getStagePriority(pStage)) {
    changes.sales_stage = sStage
  }

  // lead_notes: combine
  const merged = mergeNotes(String(primary.lead_notes ?? ''), String(secondary.lead_notes ?? ''))
  if (merged !== String(primary.lead_notes ?? '')) {
    changes.lead_notes = merged
  }

  // Boolean fields: keep '1' if either has it
  for (const boolField of ['demo_done', 'demo_booked', 'sale_done', 'trial_activated', 'is_prospect', 'is_high_prospect', 'upgrade_done', 'renewal_done']) {
    if (String(secondary[boolField] ?? '') === '1' && String(primary[boolField] ?? '') !== '1') {
      changes[boolField] = '1'
    }
  }

  // Enrichment: fill empty fields from secondary
  for (const field of ['deal_owner', 'company_name', 'Lead_email', 'lead_source', 'lead_city', 'state_mobile', 'region', 'user_profession', 'Team_size', 'project_type', 'price_pitched', 'annual_revenue', 'sale_done_date', 'demo_date', 'campaign_name', 'Adset_name', 'total_activity', 'pre_qualification', 'lead_priority', 'Construction_type']) {
    const pVal = String(primary[field] ?? '').trim()
    const sVal = String(secondary[field] ?? '').trim()
    if (!pVal && sVal) {
      changes[field] = sVal
    }
  }

  // price_pitched: keep higher value
  const pPrice = parseFloat(String(primary.price_pitched ?? '').replace(/,/g, '')) || 0
  const sPrice = parseFloat(String(secondary.price_pitched ?? '').replace(/,/g, '')) || 0
  if (sPrice > pPrice) {
    changes.price_pitched = String(secondary.price_pitched ?? '')
  }

  // annual_revenue: keep higher value
  const pRev = parseFloat(String(primary.annual_revenue ?? '').replace(/,/g, '')) || 0
  const sRev = parseFloat(String(secondary.annual_revenue ?? '').replace(/,/g, '')) || 0
  if (sRev > pRev) {
    changes.annual_revenue = String(secondary.annual_revenue ?? '')
  }

  // sale_done_date: keep newer
  const newerSaleDate = keepNewerDate(
    String(primary.sale_done_date ?? ''),
    String(secondary.sale_done_date ?? '')
  )
  if (newerSaleDate && newerSaleDate !== String(primary.sale_done_date ?? '')) {
    changes.sale_done_date = newerSaleDate
  }

  // Track merged IDs
  const existingMerged = String(primary._merged_from ?? '')
  const secId = secondary.zoho_lead_id
  if (!existingMerged.includes(secId)) {
    changes._merged_from = existingMerged ? `${existingMerged},${secId}` : secId
  }

  return changes
}

// ─── Smart Merge Engine ──────────────────────────────────────────────────────

export async function smartMerge(
  rows: Record<string, string>[],
  fileName: string,
  source: string = 'csv',
): Promise<MergeResult> {
  const start = performance.now()

  const existingLeads = await db.leads.toArray()
  const existingByZohoId = new Map<string, LeadRecord>()
  existingLeads.forEach(l => {
    if (l.zoho_lead_id) existingByZohoId.set(l.zoho_lead_id, l)
  })

  let newCount = 0
  let updatedCount = 0
  let unchangedCount = 0
  const fieldChanges: Record<string, number> = {}
  const now = new Date().toISOString()

  const toInsert: LeadRecord[] = []
  const toUpdate: { key: number; changes: Partial<LeadRecord> }[] = []

  for (const row of rows) {
    const zohoId = (row.zoho_lead_id || row.lead_id || '').trim()
    if (!zohoId) continue

    const phoneNorm = normalizePhone(row.lead_phone)

    if (existingByZohoId.has(zohoId)) {
      const existing = existingByZohoId.get(zohoId)!
      const changes: Partial<LeadRecord> = {}
      let hasChanges = false

      for (const field of TRACKED_FIELDS) {
        const oldVal = String(existing[field] ?? '').trim()
        const newVal = String(row[field] ?? '').trim()
        if (newVal && newVal !== oldVal) {
          changes[field] = newVal
          hasChanges = true
          fieldChanges[field] = (fieldChanges[field] || 0) + 1
        }
      }

      // user_date: always keep the older one
      const olderDate = keepOlderDate(String(existing.user_date ?? ''), row.user_date)
      if (olderDate && olderDate !== String(existing.user_date ?? '')) {
        changes.user_date = olderDate
        hasChanges = true
      }

      // lead_source_date: keep newer
      const newerSrcDate = keepNewerDate(String(existing.lead_source_date ?? ''), row.lead_source_date)
      if (newerSrcDate && newerSrcDate !== String(existing.lead_source_date ?? '')) {
        changes.lead_source_date = newerSrcDate
        hasChanges = true
      }

      // Notes: merge
      const mergedNotes = mergeNotes(String(existing.lead_notes ?? ''), row.lead_notes)
      if (mergedNotes !== String(existing.lead_notes ?? '')) {
        changes.lead_notes = mergedNotes
        hasChanges = true
        fieldChanges['lead_notes'] = (fieldChanges['lead_notes'] || 0) + 1
      }

      // Status: keep higher priority
      const existStatus = String(existing.lead_status ?? '')
      const newStatus = String(row.lead_status ?? '')
      if (newStatus && getStatusPriority(newStatus) > getStatusPriority(existStatus)) {
        changes.lead_status = newStatus
        hasChanges = true
        fieldChanges['lead_status'] = (fieldChanges['lead_status'] || 0) + 1
      }

      if (hasChanges) {
        changes._updated_at = now
        changes._phone_norm = phoneNorm
        toUpdate.push({ key: existing._id!, changes })
        updatedCount++
      } else {
        unchangedCount++
      }
    } else {
      const record: LeadRecord = {
        ...row,
        zoho_lead_id: zohoId,
        _phone_norm: phoneNorm,
        _source: source,
        _updated_at: now,
      } as LeadRecord
      toInsert.push(record)
      newCount++
    }
  }

  if (toInsert.length > 0) {
    await db.leads.bulkAdd(toInsert)
  }

  for (const { key, changes } of toUpdate) {
    await db.leads.update(key, changes)
  }

  // ─── Phone merge: same phone, different lead IDs → merge into best ─────
  const allLeads = await db.leads.toArray()
  const phoneMap = new Map<string, LeadRecord[]>()
  for (const lead of allLeads) {
    const p = lead._phone_norm
    if (!p || p.length < 10) continue
    if (!phoneMap.has(p)) phoneMap.set(p, [])
    phoneMap.get(p)!.push(lead)
  }

  const phoneMergeDetails: PhoneMergeDetail[] = []
  let phoneMergedCount = 0
  const idsToDelete: number[] = []

  for (const [phone, leads] of phoneMap) {
    if (leads.length <= 1) continue
    const uniqueZohoIds = new Set(leads.map(l => l.zoho_lead_id))
    if (uniqueZohoIds.size <= 1) continue

    // Pick the "best" lead as primary (highest status priority)
    const sorted = [...leads].sort((a, b) => {
      const sa = getStatusPriority(String(a.lead_status ?? ''))
      const sb = getStatusPriority(String(b.lead_status ?? ''))
      if (sb !== sa) return sb - sa
      // Tie-break: more activity = better
      const actA = parseInt(String(a.total_activity ?? '0')) || 0
      const actB = parseInt(String(b.total_activity ?? '0')) || 0
      return actB - actA
    })

    const primary = sorted[0]
    const secondaries = sorted.slice(1)
    let mergeChanges: Partial<LeadRecord> = {}

    for (const sec of secondaries) {
      const secChanges = mergeLeadRecords(
        { ...primary, ...mergeChanges } as LeadRecord,
        sec
      )
      mergeChanges = { ...mergeChanges, ...secChanges }
      idsToDelete.push(sec._id!)
    }

    if (Object.keys(mergeChanges).length > 0) {
      mergeChanges._updated_at = now
      await db.leads.update(primary._id!, mergeChanges)
    }

    phoneMergedCount += secondaries.length
    phoneMergeDetails.push({
      phone,
      keptLeadId: primary.zoho_lead_id,
      keptName: String(primary.lead_name ?? ''),
      mergedCount: secondaries.length,
      mergedIds: secondaries.map(s => s.zoho_lead_id),
    })
  }

  // Delete merged-away leads
  if (idsToDelete.length > 0) {
    await db.leads.bulkDelete(idsToDelete)
  }

  const totalAfterMerge = await db.leads.count()
  const duration = Math.round(performance.now() - start)

  const changesByField = Object.entries(fieldChanges)
    .map(([field, count]) => ({ field, count }))
    .sort((a, b) => b.count - a.count)

  await db.uploads.add({
    timestamp: now,
    fileName,
    totalRows: rows.length,
    newLeads: newCount,
    updatedLeads: updatedCount,
    unchangedLeads: unchangedCount,
    phoneMerged: phoneMergedCount,
    duration_ms: duration,
    changesSummary: changesByField.slice(0, 20),
  })

  return {
    newLeads: newCount,
    updatedLeads: updatedCount,
    unchangedLeads: unchangedCount,
    phoneMerged: phoneMergedCount,
    totalProcessed: rows.length,
    totalAfterMerge,
    duration_ms: duration,
    changesByField,
    phoneMergeDetails: phoneMergeDetails.slice(0, 100),
  }
}

// ─── Data Access ─────────────────────────────────────────────────────────────

export async function getAllLeads(): Promise<Record<string, string>[]> {
  const leads = await db.leads.toArray()
  return leads.map(l => {
    const row: Record<string, string> = {}
    for (const [k, v] of Object.entries(l)) {
      if (k.startsWith('_')) continue
      row[k] = String(v ?? '')
    }
    return row
  })
}

export async function getLeadCount(): Promise<number> {
  return db.leads.count()
}

export async function getUploadHistory(): Promise<UploadRecord[]> {
  return db.uploads.orderBy('timestamp').reverse().toArray()
}

export async function getPhoneMergeHistory(): Promise<PhoneMergeDetail[]> {
  const leads = await db.leads.toArray()
  return leads
    .filter(l => l._merged_from)
    .map(l => ({
      phone: l._phone_norm || '',
      keptLeadId: l.zoho_lead_id,
      keptName: String(l.lead_name ?? ''),
      mergedCount: String(l._merged_from ?? '').split(',').length,
      mergedIds: String(l._merged_from ?? '').split(',').filter(Boolean),
    }))
    .sort((a, b) => b.mergedCount - a.mergedCount)
}

export async function clearAllData(): Promise<void> {
  await db.leads.clear()
  await db.uploads.clear()
}

export async function getLastUpload(): Promise<UploadRecord | undefined> {
  return db.uploads.orderBy('timestamp').reverse().first()
}

export { db }

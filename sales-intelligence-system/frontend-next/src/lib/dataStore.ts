/**
 * Smart Data Management Layer
 *
 * - IndexedDB persistence via Dexie (survives refresh)
 * - Smart merge on re-upload (dedup by zoho_lead_id)
 * - Phone number duplicate detection (same phone, different lead IDs)
 * - Upload history tracking with change summaries
 * - Designed for future API/webhook integration (not just CSV)
 */

import Dexie, { type Table } from 'dexie'

// ─── Types ───────────────────────────────────────────────────────────────────

export interface LeadRecord {
  /** Internal auto-increment ID (IndexedDB) */
  _id?: number
  /** Primary business key — Zoho CRM lead ID */
  zoho_lead_id: string
  /** Normalized phone for dedup (digits only) */
  _phone_norm?: string
  /** Duplicate group ID — leads sharing a phone number */
  _dup_group?: string
  /** Source of this record: csv, api, manual */
  _source: string
  /** ISO timestamp of last update to this record */
  _updated_at: string
  /** All raw CSV fields */
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
  phoneDuplicates: number
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
  phoneDuplicates: number
  totalProcessed: number
  duration_ms: number
  changesByField: FieldChangeSummary[]
  duplicateGroups: DuplicateGroup[]
}

export interface DuplicateGroup {
  phone: string
  leads: { zoho_lead_id: string; lead_name: string; lead_status: string }[]
}

// ─── Fields to track for change detection ────────────────────────────────────

const TRACKED_FIELDS = [
  'lead_status', 'sales_stage', 'lead_notes', 'last_touched_date_new',
  'last_touched_date', 'deal_owner', 'lead_owner', 'demo_done', 'sale_done',
  'demo_booked', 'trial_activated', 'lead_source', 'call_disposition',
  'lead_category', 'lead_category_1', 'pre_qualification', 'is_prospect',
  'is_high_prospect', 'lead_priority', 'price_pitched', 'lead_assigned',
  'upgrade_done', 'renewal_done', 'onboarding_session_stage', 'remark',
]

// ─── Database ────────────────────────────────────────────────────────────────

class OnsiteDB extends Dexie {
  leads!: Table<LeadRecord>
  uploads!: Table<UploadRecord>

  constructor() {
    super('onsite-intelligence')
    this.version(1).stores({
      leads: '++_id, zoho_lead_id, _phone_norm, _dup_group, _source',
      uploads: '++id, timestamp',
    })
  }
}

const db = new OnsiteDB()

// ─── Phone normalization ─────────────────────────────────────────────────────

function normalizePhone(phone: string | undefined): string {
  if (!phone) return ''
  const digits = phone.replace(/[^0-9]/g, '')
  if (digits.length >= 10) {
    return digits.slice(-10)
  }
  return digits
}

// ─── Smart Merge Engine ──────────────────────────────────────────────────────

export async function smartMerge(
  rows: Record<string, string>[],
  fileName: string,
  source: string = 'csv',
): Promise<MergeResult> {
  const start = performance.now()

  // Build lookup of existing leads by zoho_lead_id
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
      // Existing lead — check for changes
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

      if (hasChanges) {
        changes._updated_at = now
        changes._phone_norm = phoneNorm
        toUpdate.push({ key: existing._id!, changes })
        updatedCount++
      } else {
        unchangedCount++
      }
    } else {
      // New lead
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

  // Batch insert new leads
  if (toInsert.length > 0) {
    await db.leads.bulkAdd(toInsert)
  }

  // Batch update changed leads
  for (const { key, changes } of toUpdate) {
    await db.leads.update(key, changes)
  }

  // ─── Phone duplicate detection ───────────────────────────────────────────
  const allLeads = await db.leads.toArray()
  const phoneMap = new Map<string, LeadRecord[]>()
  for (const lead of allLeads) {
    const p = lead._phone_norm
    if (!p || p.length < 10) continue
    if (!phoneMap.has(p)) phoneMap.set(p, [])
    phoneMap.get(p)!.push(lead)
  }

  const duplicateGroups: DuplicateGroup[] = []
  let phoneDupCount = 0

  for (const [phone, leads] of phoneMap) {
    if (leads.length <= 1) continue
    const uniqueZohoIds = new Set(leads.map(l => l.zoho_lead_id))
    if (uniqueZohoIds.size <= 1) continue

    phoneDupCount += leads.length
    const dupGroupId = `dup_${phone}`

    // Tag leads with dup group
    for (const lead of leads) {
      if (lead._dup_group !== dupGroupId) {
        await db.leads.update(lead._id!, { _dup_group: dupGroupId })
      }
    }

    duplicateGroups.push({
      phone,
      leads: leads.map(l => ({
        zoho_lead_id: l.zoho_lead_id,
        lead_name: String(l.lead_name ?? ''),
        lead_status: String(l.lead_status ?? ''),
      })),
    })
  }

  const duration = Math.round(performance.now() - start)

  const changesByField = Object.entries(fieldChanges)
    .map(([field, count]) => ({ field, count }))
    .sort((a, b) => b.count - a.count)

  // Save upload history
  await db.uploads.add({
    timestamp: now,
    fileName,
    totalRows: rows.length,
    newLeads: newCount,
    updatedLeads: updatedCount,
    unchangedLeads: unchangedCount,
    phoneDuplicates: phoneDupCount,
    duration_ms: duration,
    changesSummary: changesByField.slice(0, 20),
  })

  return {
    newLeads: newCount,
    updatedLeads: updatedCount,
    unchangedLeads: unchangedCount,
    phoneDuplicates: phoneDupCount,
    totalProcessed: rows.length,
    duration_ms: duration,
    changesByField,
    duplicateGroups: duplicateGroups.slice(0, 100),
  }
}

// ─── Data Access ─────────────────────────────────────────────────────────────

export async function getAllLeads(): Promise<Record<string, string>[]> {
  const leads = await db.leads.toArray()
  return leads.map(l => {
    const row: Record<string, string> = {}
    for (const [k, v] of Object.entries(l)) {
      if (k.startsWith('_') && k !== '_dup_group') continue
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

export async function getPhoneDuplicates(): Promise<DuplicateGroup[]> {
  const allLeads = await db.leads.toArray()
  const phoneMap = new Map<string, LeadRecord[]>()
  for (const lead of allLeads) {
    const p = lead._phone_norm
    if (!p || p.length < 10) continue
    if (!phoneMap.has(p)) phoneMap.set(p, [])
    phoneMap.get(p)!.push(lead)
  }

  const groups: DuplicateGroup[] = []
  for (const [phone, leads] of phoneMap) {
    if (leads.length <= 1) continue
    const uniqueZohoIds = new Set(leads.map(l => l.zoho_lead_id))
    if (uniqueZohoIds.size <= 1) continue
    groups.push({
      phone,
      leads: leads.map(l => ({
        zoho_lead_id: l.zoho_lead_id,
        lead_name: String(l.lead_name ?? ''),
        lead_status: String(l.lead_status ?? ''),
      })),
    })
  }
  return groups.sort((a, b) => b.leads.length - a.leads.length)
}

export async function clearAllData(): Promise<void> {
  await db.leads.clear()
  await db.uploads.clear()
}

export async function getLastUpload(): Promise<UploadRecord | undefined> {
  return db.uploads.orderBy('timestamp').reverse().first()
}

export { db }

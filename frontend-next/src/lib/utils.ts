import { clsx, type ClassValue } from 'clsx'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function formatCurrency(amount: number): string {
  if (amount >= 10000000) return `₹${(amount / 10000000).toFixed(1)}Cr`
  if (amount >= 100000) return `₹${(amount / 100000).toFixed(1)}L`
  if (amount >= 1000) return `₹${(amount / 1000).toFixed(0)}K`
  return `₹${amount.toLocaleString('en-IN')}`
}

export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function formatRelative(date: string): string {
  const now = new Date()
  const d = new Date(date)
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`
  return formatDate(date)
}

export function getStageColor(stage: string): string {
  const colors: Record<string, string> = {
    new: 'bg-sky-500/10 text-sky-600 dark:text-sky-400',
    contacted: 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400',
    qualified: 'bg-violet-500/10 text-violet-600 dark:text-violet-400',
    demo: 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400',
    proposal: 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
    negotiation: 'bg-orange-500/10 text-orange-600 dark:text-orange-400',
    won: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
    lost: 'bg-red-500/10 text-red-600 dark:text-red-400',
    not_reachable: 'bg-zinc-500/10 text-zinc-600 dark:text-zinc-400',
    meeting_scheduled: 'bg-violet-500/10 text-violet-600 dark:text-violet-400',
  }
  return colors[stage] || 'bg-zinc-500/10 text-zinc-600 dark:text-zinc-400'
}

export function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    low: 'bg-sky-500/10 text-sky-600',
    medium: 'bg-amber-500/10 text-amber-600',
    high: 'bg-orange-500/10 text-orange-600',
    critical: 'bg-red-500/10 text-red-600',
  }
  return colors[severity] || 'bg-zinc-500/10 text-zinc-600'
}

export function truncate(str: string, len: number): string {
  if (str.length <= len) return str
  return str.slice(0, len) + '...'
}

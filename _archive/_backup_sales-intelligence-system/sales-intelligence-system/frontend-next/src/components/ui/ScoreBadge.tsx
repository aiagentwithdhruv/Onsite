'use client'

import { cn } from '@/lib/utils'

interface ScoreBadgeProps {
  score: number | string | null | undefined
  size?: 'sm' | 'md' | 'lg'
}

function getLabel(score: number | string | null | undefined): { text: string; color: string } {
  if (score === null || score === undefined) {
    return { text: '--', color: 'bg-zinc-500/10 text-zinc-500 ring-zinc-500/20' }
  }
  if (typeof score === 'string') {
    switch (score.toLowerCase()) {
      case 'hot':
        return { text: 'HOT', color: 'bg-rose-500/15 text-rose-600 dark:text-rose-400 ring-rose-500/30' }
      case 'warm':
        return { text: 'WARM', color: 'bg-amber-500/15 text-amber-600 dark:text-amber-400 ring-amber-500/30' }
      case 'cold':
        return { text: 'COLD', color: 'bg-sky-500/15 text-sky-600 dark:text-sky-400 ring-sky-500/30' }
      default:
        return { text: score, color: 'bg-zinc-500/10 text-zinc-600 ring-zinc-500/20' }
    }
  }
  if (score >= 80) return { text: String(score), color: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 ring-emerald-500/30' }
  if (score >= 60) return { text: String(score), color: 'bg-amber-500/15 text-amber-600 dark:text-amber-400 ring-amber-500/30' }
  if (score >= 40) return { text: String(score), color: 'bg-orange-500/15 text-orange-600 dark:text-orange-400 ring-orange-500/30' }
  return { text: String(score), color: 'bg-rose-500/15 text-rose-600 dark:text-rose-400 ring-rose-500/30' }
}

const sizeClasses: Record<string, string> = {
  sm: 'min-w-8 h-6 px-2 text-[11px] font-semibold rounded-md',
  md: 'min-w-10 h-8 px-2.5 text-xs font-bold rounded-lg',
  lg: 'min-w-14 h-10 px-3 text-sm font-bold rounded-lg',
}

export default function ScoreBadge({ score, size = 'md' }: ScoreBadgeProps) {
  const { text, color } = getLabel(score)
  return (
    <span
      className={cn(
        'inline-flex items-center justify-center ring-1 ring-inset',
        color,
        sizeClasses[size]
      )}
    >
      {text}
    </span>
  )
}

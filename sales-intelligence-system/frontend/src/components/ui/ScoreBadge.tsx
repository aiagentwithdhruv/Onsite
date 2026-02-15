import { cn } from '../../lib/utils'

interface ScoreBadgeProps {
  score: number | string | null | undefined
  size?: 'sm' | 'md' | 'lg'
}

function getLabel(score: number | string | null | undefined): { text: string; color: string } {
  if (score === null || score === undefined) {
    return { text: '--', color: 'bg-slate-100 text-slate-400 ring-slate-200' }
  }
  if (typeof score === 'string') {
    switch (score.toLowerCase()) {
      case 'hot':
        return { text: 'HOT', color: 'bg-red-100 text-red-700 ring-red-200' }
      case 'warm':
        return { text: 'WARM', color: 'bg-amber-100 text-amber-700 ring-amber-200' }
      case 'cold':
        return { text: 'COLD', color: 'bg-blue-100 text-blue-700 ring-blue-200' }
      default:
        return { text: score, color: 'bg-slate-100 text-slate-500 ring-slate-200' }
    }
  }
  if (score >= 80) return { text: String(score), color: 'bg-green-100 text-green-700 ring-green-200' }
  if (score >= 60) return { text: String(score), color: 'bg-amber-100 text-amber-700 ring-amber-200' }
  if (score >= 40) return { text: String(score), color: 'bg-orange-100 text-orange-700 ring-orange-200' }
  return { text: String(score), color: 'bg-red-100 text-red-700 ring-red-200' }
}

const sizeClasses: Record<string, string> = {
  sm: 'min-w-8 h-7 px-2 text-[11px] font-semibold',
  md: 'min-w-10 h-9 px-2.5 text-xs font-bold',
  lg: 'min-w-14 h-12 px-3 text-sm font-bold',
}

export default function ScoreBadge({ score, size = 'md' }: ScoreBadgeProps) {
  const { text, color } = getLabel(score)
  return (
    <div
      className={cn(
        'inline-flex items-center justify-center rounded-full ring-1 ring-inset',
        color,
        sizeClasses[size]
      )}
    >
      {text}
    </div>
  )
}

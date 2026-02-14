import { cn } from '../../lib/utils'

interface ScoreBadgeProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
}

function getScoreBg(score: number): string {
  if (score >= 80) return 'bg-green-100 text-green-700 ring-green-600/20'
  if (score >= 60) return 'bg-yellow-100 text-yellow-700 ring-yellow-600/20'
  if (score >= 40) return 'bg-orange-100 text-orange-700 ring-orange-600/20'
  return 'bg-red-100 text-red-700 ring-red-600/20'
}

const sizeClasses: Record<string, string> = {
  sm: 'w-8 h-8 text-xs font-semibold',
  md: 'w-10 h-10 text-sm font-bold',
  lg: 'w-14 h-14 text-lg font-bold',
}

export default function ScoreBadge({ score, size = 'md' }: ScoreBadgeProps) {
  return (
    <div
      className={cn(
        'inline-flex items-center justify-center rounded-full ring-1 ring-inset',
        getScoreBg(score),
        sizeClasses[size]
      )}
    >
      {score}
    </div>
  )
}

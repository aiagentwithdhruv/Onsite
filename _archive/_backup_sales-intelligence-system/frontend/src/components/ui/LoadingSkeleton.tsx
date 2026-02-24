import { cn } from '../../lib/utils'

function Shimmer({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'animate-pulse rounded bg-gray-200',
        className
      )}
    />
  )
}

export function CardSkeleton({ count = 1 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="rounded-xl border border-gray-200 bg-white p-5 space-y-3"
        >
          <Shimmer className="h-4 w-20" />
          <Shimmer className="h-8 w-28" />
          <Shimmer className="h-3 w-16" />
        </div>
      ))}
    </div>
  )
}

export function TableSkeleton({ rows = 5, cols = 6 }: { rows?: number; cols?: number }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
      {/* Header */}
      <div className="border-b border-gray-200 bg-gray-50 px-4 py-3 flex gap-4">
        {Array.from({ length: cols }).map((_, i) => (
          <Shimmer key={i} className="h-4 flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIdx) => (
        <div
          key={rowIdx}
          className="border-b border-gray-100 px-4 py-4 flex gap-4 items-center"
        >
          {Array.from({ length: cols }).map((_, colIdx) => (
            <Shimmer
              key={colIdx}
              className={cn(
                'h-4 flex-1',
                colIdx === 0 ? 'max-w-[140px]' : 'max-w-[100px]'
              )}
            />
          ))}
        </div>
      ))}
    </div>
  )
}

export function TextSkeleton({ lines = 3 }: { lines?: number }) {
  const widths = ['w-full', 'w-5/6', 'w-4/6', 'w-3/4', 'w-2/3']
  return (
    <div className="space-y-2.5">
      {Array.from({ length: lines }).map((_, i) => (
        <Shimmer
          key={i}
          className={cn('h-4', widths[i % widths.length])}
        />
      ))}
    </div>
  )
}

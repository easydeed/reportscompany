export default function ReportsLoading() {
  return (
    <div className="space-y-5">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div>
          <div className="h-6 w-40 bg-muted rounded-md animate-pulse" />
          <div className="h-3.5 w-64 bg-muted rounded-md animate-pulse mt-1.5" />
        </div>
        <div className="h-9 w-28 bg-muted rounded-lg animate-pulse" />
      </div>

      {/* Table skeleton */}
      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-[var(--shadow-card)]">
        <div className="px-4 py-2.5 border-b border-border bg-muted/30">
          <div className="flex gap-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-3 w-20 bg-muted rounded animate-pulse" />
            ))}
          </div>
        </div>
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="px-4 py-3.5 border-b border-border/50 flex gap-4">
            {Array.from({ length: 5 }).map((_, j) => (
              <div key={j} className="h-4 w-24 bg-muted rounded animate-pulse" />
            ))}
          </div>
        ))}
        <div className="px-4 py-2.5 border-t border-border bg-muted/20">
          <div className="h-3 w-32 bg-muted rounded animate-pulse" />
        </div>
      </div>
    </div>
  )
}

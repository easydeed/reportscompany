export default function DashboardLoading() {
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

      {/* Metric cards skeleton */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-card border border-border rounded-xl p-4 shadow-[var(--shadow-card)]">
            <div className="h-3 w-16 bg-muted rounded animate-pulse mb-3" />
            <div className="h-7 w-12 bg-muted rounded animate-pulse" />
          </div>
        ))}
      </div>

      {/* Two-column content area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Activity table skeleton */}
        <div className="lg:col-span-2 bg-card border border-border rounded-xl overflow-hidden shadow-[var(--shadow-card)]">
          <div className="px-4 py-3 border-b border-border">
            <div className="h-4 w-32 bg-muted rounded animate-pulse" />
          </div>
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="px-4 py-3.5 border-b border-border/50 last:border-0 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-muted rounded-lg animate-pulse" />
                <div>
                  <div className="h-4 w-32 bg-muted rounded animate-pulse mb-1" />
                  <div className="h-3 w-20 bg-muted rounded animate-pulse" />
                </div>
              </div>
              <div className="h-5 w-16 bg-muted rounded-full animate-pulse" />
            </div>
          ))}
        </div>

        {/* Sidebar skeleton */}
        <div className="lg:col-span-1 bg-card border border-border rounded-xl p-4 shadow-[var(--shadow-card)]">
          <div className="h-4 w-24 bg-muted rounded animate-pulse mb-4" />
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 mb-3">
              <div className="w-5 h-5 bg-muted rounded animate-pulse" />
              <div className="h-4 w-32 bg-muted rounded animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

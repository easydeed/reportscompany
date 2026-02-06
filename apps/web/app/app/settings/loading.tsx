export default function SettingsLoading() {
  return (
    <div className="max-w-3xl">
      {/* Header skeleton */}
      <div className="mb-6">
        <div className="h-6 w-32 bg-muted rounded-md animate-pulse" />
        <div className="h-4 w-56 bg-muted rounded-md animate-pulse mt-1.5" />
      </div>

      {/* Main card skeleton */}
      <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
        {/* Avatar section */}
        <div className="p-6 border-b border-border">
          <div className="flex items-center gap-5">
            <div className="w-20 h-20 rounded-full bg-muted animate-pulse" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-28 bg-muted rounded animate-pulse" />
              <div className="h-3 w-48 bg-muted rounded animate-pulse" />
              <div className="h-8 w-20 bg-muted rounded animate-pulse mt-2" />
            </div>
          </div>
        </div>

        {/* Form sections */}
        <div className="divide-y divide-border">
          {/* Section 1 */}
          <div className="p-6">
            <div className="h-4 w-36 bg-muted rounded animate-pulse mb-4" />
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <div className="h-3 w-20 bg-muted rounded animate-pulse" />
                <div className="h-9 bg-muted rounded-md animate-pulse" />
              </div>
              <div className="space-y-1.5">
                <div className="h-3 w-20 bg-muted rounded animate-pulse" />
                <div className="h-9 bg-muted rounded-md animate-pulse" />
              </div>
              <div className="space-y-1.5">
                <div className="h-3 w-20 bg-muted rounded animate-pulse" />
                <div className="h-9 bg-muted rounded-md animate-pulse" />
              </div>
              <div className="space-y-1.5">
                <div className="h-3 w-20 bg-muted rounded animate-pulse" />
                <div className="h-9 bg-muted rounded-md animate-pulse" />
              </div>
            </div>
          </div>

          {/* Section 2 */}
          <div className="p-6">
            <div className="h-4 w-40 bg-muted rounded animate-pulse mb-4" />
            <div className="grid gap-4">
              <div className="space-y-1.5">
                <div className="h-3 w-24 bg-muted rounded animate-pulse" />
                <div className="h-9 bg-muted rounded-md animate-pulse" />
              </div>
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <div className="h-3 w-24 bg-muted rounded animate-pulse" />
                  <div className="h-9 bg-muted rounded-md animate-pulse" />
                </div>
                <div className="space-y-1.5">
                  <div className="h-3 w-16 bg-muted rounded animate-pulse" />
                  <div className="h-9 bg-muted rounded-md animate-pulse" />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-muted/30 border-t border-border flex justify-end">
          <div className="h-8 w-28 bg-muted rounded animate-pulse" />
        </div>
      </div>
    </div>
  )
}

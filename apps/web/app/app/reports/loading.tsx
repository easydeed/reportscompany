import { Skeleton } from "@/components/ui/skeleton"

export default function ReportsLoading() {
  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-8 w-44" />
          <Skeleton className="h-4 w-64 mt-2" />
        </div>
        <Skeleton className="h-9 w-32 rounded-md" />
      </div>

      {/* Table */}
      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
        {/* Search bar */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <Skeleton className="h-8 w-64 rounded-md" />
          <Skeleton className="h-8 w-20 rounded-md" />
        </div>

        {/* Table header */}
        <div className="px-4 py-3 border-b border-border bg-muted/30">
          <div className="flex items-center gap-4">
            <Skeleton className="h-3 w-32" />
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-3 w-16 ml-auto" />
          </div>
        </div>

        {/* Table rows */}
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="px-4 py-4 border-b border-border last:border-0 flex items-center gap-4">
            <Skeleton className="h-4 w-36" />
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-5 w-16 rounded-full ml-auto" />
          </div>
        ))}

        {/* Pagination */}
        <div className="px-4 py-3 border-t border-border flex items-center justify-between">
          <Skeleton className="h-3 w-32" />
          <Skeleton className="h-8 w-48" />
        </div>
      </div>
    </div>
  )
}

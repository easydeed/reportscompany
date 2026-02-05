import { Skeleton } from "@/components/ui/skeleton"

export default function SettingsLoading() {
  return (
    <div className="space-y-8 max-w-2xl">
      <div>
        <Skeleton className="h-7 w-32" />
        <Skeleton className="h-4 w-64 mt-2" />
      </div>

      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="bg-card border border-border rounded-xl p-6 shadow-sm">
          <Skeleton className="h-3 w-28 mb-6" />
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-9 w-full rounded-md" />
            </div>
            <div className="space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-9 w-full rounded-md" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

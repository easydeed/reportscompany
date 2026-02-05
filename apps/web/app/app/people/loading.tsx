import { Skeleton } from "@/components/ui/skeleton"

export default function ContactsLoading() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-8 w-36" />
          <Skeleton className="h-4 w-56 mt-2" />
        </div>
        <Skeleton className="h-9 w-32 rounded-md" />
      </div>

      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="px-4 py-4 border-b border-border last:border-0 flex items-center gap-4">
            <Skeleton className="h-8 w-8 rounded-full" />
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-5 w-16 rounded-full ml-auto" />
          </div>
        ))}
      </div>
    </div>
  )
}

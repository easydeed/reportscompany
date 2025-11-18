"use client"

import { cn } from "@/lib/utils"

interface SkeletonCardProps {
  className?: string
}

export function SkeletonCard({ className }: SkeletonCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl bg-card border border-border/50 p-5 animate-pulse",
        "shadow-[0_1px_3px_0_rgba(0,0,0,0.1),0_1px_2px_-1px_rgba(0,0,0,0.1)]",
        "dark:shadow-[0_1px_3px_0_rgba(0,0,0,0.3),0_1px_2px_-1px_rgba(0,0,0,0.2)]",
        className,
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 space-y-2">
          <div className="h-4 w-24 bg-muted rounded shimmer" />
          <div className="h-7 w-32 bg-muted rounded shimmer" />
        </div>
        <div className="w-9 h-9 bg-muted rounded-lg shimmer" />
      </div>
      <div className="h-4 w-20 bg-muted rounded shimmer" />
    </div>
  )
}

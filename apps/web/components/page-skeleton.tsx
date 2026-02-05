"use client"

import { Skeleton } from "@/components/ui/skeleton"

/**
 * Page skeleton for loading states
 */
export function PageSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-4 w-72 mt-2" />
        </div>
        <Skeleton className="h-9 w-32" />
      </div>

      {/* Metric cards skeleton */}
      <div className="grid grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-card border border-border rounded-xl p-5 shadow-sm">
            <Skeleton className="h-4 w-24 mb-3" />
            <Skeleton className="h-7 w-16" />
          </div>
        ))}
      </div>

      {/* Table skeleton */}
      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
        <div className="px-4 py-3 border-b border-border">
          <Skeleton className="h-8 w-64" />
        </div>
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="px-4 py-3 border-b border-border last:border-0">
            <Skeleton className="h-4 w-full" />
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * Table skeleton for loading states
 */
export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
      <div className="px-4 py-3 border-b border-border">
        <Skeleton className="h-8 w-64" />
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="px-4 py-3 border-b border-border last:border-0">
          <Skeleton className="h-4 w-full" />
        </div>
      ))}
    </div>
  )
}

/**
 * Card skeleton for loading states
 */
export function CardSkeleton() {
  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
      <Skeleton className="h-5 w-32 mb-4" />
      <Skeleton className="h-4 w-full mb-2" />
      <Skeleton className="h-4 w-3/4" />
    </div>
  )
}

/**
 * Metric card skeleton
 */
export function MetricSkeleton() {
  return (
    <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
      <Skeleton className="h-4 w-24 mb-3" />
      <Skeleton className="h-7 w-16" />
    </div>
  )
}

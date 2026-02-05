"use client"

import { cn } from "@/lib/utils"

type Status = 
  | "completed" 
  | "processing" 
  | "pending" 
  | "failed" 
  | "active" 
  | "inactive"
  | "sent"
  | "delivered"
  | "opened"
  | "new"
  | "contacted"
  | "converted"

const STATUS_STYLES: Record<Status, string> = {
  // Report/Job statuses
  completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  processing: "bg-blue-50 text-blue-700 border-blue-200",
  pending: "bg-amber-50 text-amber-700 border-amber-200",
  failed: "bg-red-50 text-red-700 border-red-200",
  
  // Active/Inactive
  active: "bg-emerald-50 text-emerald-700 border-emerald-200",
  inactive: "bg-gray-50 text-gray-500 border-gray-200",
  
  // Email statuses
  sent: "bg-blue-50 text-blue-700 border-blue-200",
  delivered: "bg-emerald-50 text-emerald-700 border-emerald-200",
  opened: "bg-violet-50 text-violet-700 border-violet-200",
  
  // Lead statuses
  new: "bg-blue-50 text-blue-700 border-blue-200",
  contacted: "bg-amber-50 text-amber-700 border-amber-200",
  converted: "bg-emerald-50 text-emerald-700 border-emerald-200",
}

const STATUS_LABELS: Record<Status, string> = {
  completed: "Completed",
  processing: "Processing",
  pending: "Pending",
  failed: "Failed",
  active: "Active",
  inactive: "Inactive",
  sent: "Sent",
  delivered: "Delivered",
  opened: "Opened",
  new: "New",
  contacted: "Contacted",
  converted: "Converted",
}

interface StatusBadgeProps {
  status: Status | string
  label?: string
  className?: string
}

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  const normalizedStatus = status.toLowerCase() as Status
  const styles = STATUS_STYLES[normalizedStatus] || "bg-gray-50 text-gray-500 border-gray-200"
  const displayLabel = label || STATUS_LABELS[normalizedStatus] || status

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border",
        styles,
        className
      )}
    >
      {displayLabel}
    </span>
  )
}

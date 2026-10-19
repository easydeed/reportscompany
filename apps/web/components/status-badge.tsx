"use client"

import { cn } from "@/lib/utils"

type Status = 
  | "completed" 
  | "complete"
  | "processing" 
  | "pending" 
  | "failed" 
  | "active" 
  | "inactive"
  | "draft"
  | "sent"
  | "delivered"
  | "opened"
  | "new"
  | "contacted"
  | "converted"

const STATUS_STYLES: Record<Status, string> = {
  // Report/Job statuses
  completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  complete: "bg-emerald-50 text-emerald-700 border-emerald-200",
  processing: "bg-amber-50 text-amber-700 border-amber-200",
  pending: "bg-slate-50 text-slate-600 border-slate-200",
  failed: "bg-red-50 text-red-700 border-red-200",
  draft: "bg-slate-50 text-slate-500 border-slate-200",
  
  // Active/Inactive
  active: "bg-emerald-50 text-emerald-700 border-emerald-200",
  inactive: "bg-slate-50 text-slate-500 border-slate-200",
  
  // Email statuses
  // Design's semantic pairs are the only tinted fills allowed on chrome.
  sent: "bg-[var(--neutral-muted)] text-muted-foreground border-border",
  delivered: "bg-emerald-50 text-emerald-700 border-emerald-200",
  opened: "bg-[var(--success-muted)] text-[var(--success-foreground)] border-transparent",
  
  // Lead statuses
  new: "bg-primary text-primary-foreground border-transparent",
  contacted: "bg-amber-50 text-amber-700 border-amber-200",
  converted: "bg-emerald-50 text-emerald-700 border-emerald-200",
}

const STATUS_LABELS: Record<Status, string> = {
  completed: "Completed",
  complete: "Complete",
  processing: "Processing",
  pending: "Pending",
  failed: "Failed",
  draft: "Draft",
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
  const styles = STATUS_STYLES[normalizedStatus] || "bg-slate-50 text-slate-500 border-slate-200"
  const displayLabel = label || STATUS_LABELS[normalizedStatus] || status

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium border",
        styles,
        className
      )}
    >
      {displayLabel}
    </span>
  )
}

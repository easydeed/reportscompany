"use client"

import { cn } from "@/lib/utils"

// App v3 status pill: 12px / 700, 4px 10px, 999px. Semantic pairs only —
// never derived from brand. `clicked` is the one exception (agent accent),
// pass it via `accent`.
type Tone = "success" | "neutral" | "danger" | "info" | "warning" | "ink" | "clicked"

const TONE: Record<Tone, string> = {
  success: "bg-[var(--success-muted)] text-[var(--success-foreground)]",
  neutral: "bg-[var(--neutral-muted)] text-muted-foreground",
  danger: "bg-[var(--destructive-muted)] text-[var(--destructive-foreground)]",
  info: "bg-[var(--info-muted)] text-[var(--info-foreground)]",
  warning: "bg-[var(--warning-muted)] text-[var(--warning-foreground)]",
  ink: "bg-primary text-primary-foreground",
  clicked: "text-white",
}

const STATUS: Record<string, [Tone, string]> = {
  completed: ["success", "Done"], complete: ["success", "Done"], done: ["success", "Done"],
  delivered: ["success", "Delivered"], opened: ["success", "Opened"], called: ["success", "Called"],
  converted: ["success", "Converted"], active: ["success", "Active"],
  processing: ["info", "Running"], running: ["info", "Running"], queued: ["info", "Queued"],
  pending: ["neutral", "Pending"], sent: ["neutral", "Sent"], draft: ["neutral", "Draft"], inactive: ["neutral", "Paused"], paused: ["neutral", "Paused"],
  failed: ["danger", "Failed"], bounced: ["danger", "Bounced"],
  hot: ["warning", "Hot"], contacted: ["warning", "Contacted"],
  new: ["ink", "New"], lead: ["ink", "New lead"],
  clicked: ["clicked", "Clicked"],
}

interface StatusBadgeProps { status: string; label?: string; className?: string; accent?: string }

export function StatusBadge({ status, label, className, accent }: StatusBadgeProps) {
  const key = status.toLowerCase()
  const [tone, text] = STATUS[key] ?? ["neutral", status]
  return (
    <span
      className={cn("inline-flex items-center whitespace-nowrap rounded-full px-[10px] py-1 text-[12px] font-bold", TONE[tone], className)}
      style={tone === "clicked" ? { background: accent ?? "var(--agent-accent)" } : undefined}
    >
      {label ?? text}
    </span>
  )
}

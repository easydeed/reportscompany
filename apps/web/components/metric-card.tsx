"use client"

import { cn } from "@/lib/utils"
import type { ReactNode } from "react"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"

interface MetricCardProps {
  label: string
  value: string | number
  change?: number
  trend?: "up" | "down" | "neutral"
  icon?: ReactNode
  className?: string
  index?: number
}

export function MetricCard({ label, value, change, trend = "neutral", icon, className, index = 0 }: MetricCardProps) {
  return (
    <div
      className={cn(
        "bg-card border border-border rounded-xl p-4 shadow-[var(--shadow-card)] hover:shadow-[var(--shadow-elevated)] transition-shadow duration-200",
        className,
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.06em]">
          {label}
        </span>
        {icon && (
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
            {icon}
          </div>
        )}
      </div>
      <div className="text-2xl font-bold text-foreground tracking-tight">{value}</div>
      {change !== undefined && (
        <div className="flex items-center gap-1.5 mt-1.5">
          <div className={cn(
            "flex items-center gap-0.5 text-xs font-medium",
            trend === "up" ? "text-emerald-600" : trend === "down" ? "text-red-600" : "text-muted-foreground"
          )}>
            {trend === "up" ? <TrendingUp className="w-3 h-3" /> : trend === "down" ? <TrendingDown className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
            <span>{Math.abs(change)}%</span>
          </div>
          <span className="text-[11px] text-muted-foreground">vs last period</span>
        </div>
      )}
    </div>
  )
}

"use client"

import { cn } from "@/lib/utils"
import type { ReactNode } from "react"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"
import { motion } from "framer-motion"

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
  const getTrendIcon = () => {
    switch (trend) {
      case "up":
        return <TrendingUp className="w-3 h-3" />
      case "down":
        return <TrendingDown className="w-3 h-3" />
      default:
        return <Minus className="w-3 h-3" />
    }
  }

  const getTrendColor = () => {
    switch (trend) {
      case "up":
        return "text-emerald-600"
      case "down":
        return "text-red-600"
      default:
        return "text-muted-foreground"
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.2, delay: index * 0.05 }}
      className={cn(
        "bg-card border border-border rounded-xl p-5 shadow-sm",
        className,
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          {label}
        </span>
        {icon && (
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
            {icon}
          </div>
        )}
      </div>
      <div className="text-2xl font-bold text-foreground">{value}</div>
      {change !== undefined && (
        <div className="flex items-center gap-1 mt-1">
          <div className={cn("flex items-center gap-1", getTrendColor())}>
            {getTrendIcon()}
            <span className="text-xs font-medium">{Math.abs(change)}%</span>
          </div>
          <span className="text-xs text-muted-foreground">vs last period</span>
        </div>
      )}
    </motion.div>
  )
}

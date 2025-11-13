"use client"

import { cn } from "../lib/utils"
import type { ReactNode } from "react"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"
import { motion } from "framer-motion"

interface MetricCardProps {
  title?: string
  label?: string
  value: string | number
  change?: number
  trend?: "up" | "down" | "neutral"
  icon?: ReactNode
  className?: string
  index?: number
}

export function MetricCard({
  title,
  label,
  value,
  change,
  trend = "neutral",
  icon,
  className,
  index = 0,
}: MetricCardProps) {
  const displayLabel = title || label

  const getTrendIcon = () => {
    switch (trend) {
      case "up":
        return <TrendingUp className="w-4 h-4" />
      case "down":
        return <TrendingDown className="w-4 h-4" />
      default:
        return <Minus className="w-4 h-4" />
    }
  }

  const getTrendColor = () => {
    switch (trend) {
      case "up":
        return "text-green-600 dark:text-green-400"
      case "down":
        return "text-red-600 dark:text-red-400"
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
        "glass rounded-xl p-6 border border-border hover:border-primary/30 transition-all duration-200 group",
        className,
      )}
    >
      <div className="flex items-start justify-between mb-4">
        <p className="text-sm font-medium text-muted-foreground">{displayLabel}</p>
        {icon && (
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
            {icon}
          </div>
        )}
      </div>
      <div className="space-y-2">
        <p className="font-display text-3xl font-bold text-foreground">{value}</p>
        {change !== undefined && (
          <div className={cn("flex items-center gap-1 text-sm font-medium", getTrendColor())}>
            {getTrendIcon()}
            <span>{Math.abs(change)}%</span>
          </div>
        )}
      </div>
    </motion.div>
  )
}

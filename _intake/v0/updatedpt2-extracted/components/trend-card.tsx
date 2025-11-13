"use client"

import { cn } from "@/lib/utils"
import type { ReactNode } from "react"
import { TrendingUp, TrendingDown } from "lucide-react"
import { motion } from "framer-motion"
import { LineChart, Line, ResponsiveContainer } from "recharts"

interface TrendCardProps {
  title: string
  value: string | number
  change?: number
  trend?: "up" | "down"
  sparklineData?: number[]
  icon?: ReactNode
  className?: string
  index?: number
}

export function TrendCard({
  title,
  value,
  change,
  trend,
  sparklineData = [4, 3, 5, 6, 4, 7, 8, 6, 9, 8, 10, 9],
  icon,
  className,
  index = 0,
}: TrendCardProps) {
  const chartData = sparklineData.map((value, index) => ({ value, index }))

  const trendColor = trend === "up" ? "text-success" : trend === "down" ? "text-danger" : "text-muted-foreground"
  const sparklineColor = trend === "up" ? "#10B981" : trend === "down" ? "#EF4444" : "#22D3EE"

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.18, delay: index * 0.04 }}
      className={cn(
        "relative overflow-hidden rounded-xl bg-card border border-border/50 p-5 hover:border-primary/30 transition-all duration-180 group",
        "shadow-[0_1px_3px_0_rgba(0,0,0,0.1),0_1px_2px_-1px_rgba(0,0,0,0.1)]",
        "dark:shadow-[0_1px_3px_0_rgba(0,0,0,0.3),0_1px_2px_-1px_rgba(0,0,0,0.2)]",
        className,
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <p className="text-sm font-medium text-muted-foreground mb-1">{title}</p>
          <p className="font-display text-2xl font-bold text-foreground tracking-tight">{value}</p>
        </div>
        {icon && (
          <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center text-primary transition-all duration-180 group-hover:bg-primary group-hover:text-primary-foreground">
            {icon}
          </div>
        )}
      </div>

      <div className="flex items-center justify-between">
        {change !== undefined && trend && (
          <div className={cn("flex items-center gap-1 text-sm font-medium", trendColor)}>
            {trend === "up" ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            <span>{Math.abs(change)}%</span>
          </div>
        )}

        <div className="ml-auto h-10 w-24 -mr-1">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <Line
                type="monotone"
                dataKey="value"
                stroke={sparklineColor}
                strokeWidth={2}
                dot={false}
                animationDuration={800}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </motion.div>
  )
}

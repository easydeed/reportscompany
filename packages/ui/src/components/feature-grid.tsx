"use client"

import { cn } from "../lib/utils"
import type { ReactNode } from "react"
import { motion } from "framer-motion"

interface FeatureGridProps {
  children: ReactNode
  columns?: 2 | 3 | 4
  className?: string
}

export function FeatureGrid({ children, columns = 3, className }: FeatureGridProps) {
  return (
    <div
      className={cn(
        "grid gap-6",
        columns === 2 && "md:grid-cols-2",
        columns === 3 && "md:grid-cols-2 lg:grid-cols-3",
        columns === 4 && "md:grid-cols-2 lg:grid-cols-4",
        className,
      )}
    >
      {children}
    </div>
  )
}

interface FeatureCardProps {
  icon: ReactNode
  title: string
  description: string
  index?: number
}

export function FeatureCard({ icon, title, description, index = 0 }: FeatureCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.2, delay: index * 0.05 }}
      className="glass rounded-xl p-6 border border-border hover:border-primary/50 transition-all duration-200 hover:shadow-lg group"
    >
      <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-200">
        {icon}
      </div>
      <h3 className="font-display font-semibold text-lg mb-2 text-balance">{title}</h3>
      <p className="text-sm text-muted-foreground leading-relaxed text-pretty">{description}</p>
    </motion.div>
  )
}

"use client"

import { cn } from "../../lib/utils"
import { motion } from "framer-motion"

interface SegmentedControlProps<T extends string> {
  options: { label: string; value: T }[]
  value: T
  onChange: (value: T) => void
  className?: string
}

export function SegmentedControl<T extends string>({ options, value, onChange, className }: SegmentedControlProps<T>) {
  return (
    <div
      className={cn("inline-flex items-center gap-1 p-1 bg-muted rounded-lg border border-border", className)}
      role="tablist"
    >
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          role="tab"
          aria-selected={value === option.value}
          onClick={() => onChange(option.value)}
          className={cn(
            "relative px-4 py-1.5 text-sm font-medium rounded-md transition-colors duration-180",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60",
            value === option.value ? "text-foreground" : "text-muted-foreground hover:text-foreground",
          )}
        >
          {value === option.value && (
            <motion.div
              layoutId="segmented-control-active"
              className="absolute inset-0 bg-background border border-border rounded-md shadow-sm"
              transition={{ type: "spring", bounce: 0.2, duration: 0.4 }}
            />
          )}
          <span className="relative z-10">{option.label}</span>
        </button>
      ))}
    </div>
  )
}

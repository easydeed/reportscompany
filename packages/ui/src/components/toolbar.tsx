"use client"

import { cn } from "../lib/utils"
import type { ReactNode } from "react"

interface ToolbarProps {
  children: ReactNode
  className?: string
}

export function Toolbar({ children, className }: ToolbarProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 p-3 rounded-lg border border-border bg-card/50 backdrop-blur-sm",
        className,
      )}
    >
      {children}
    </div>
  )
}

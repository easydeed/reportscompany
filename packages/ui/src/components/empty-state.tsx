"use client"

import type { ReactNode } from "react"
import { Button } from "./ui/button"
import { cn } from "../lib/utils"

interface EmptyStateProps {
  icon: ReactNode
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
  }
  className?: string
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn("glass rounded-xl border border-border p-12 text-center", className)}>
      <div className="w-16 h-16 rounded-full bg-secondary mx-auto mb-4 flex items-center justify-center text-muted-foreground">
        {icon}
      </div>
      <h3 className="font-display font-semibold text-lg mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground mb-6 max-w-md mx-auto text-pretty">{description}</p>
      {action && (
        <Button onClick={action.onClick} className="bg-primary hover:bg-primary/90">
          {action.label}
        </Button>
      )}
    </div>
  )
}

"use client"

import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

interface PageHeaderProps {
  title: ReactNode
  /** One sentence. Numbers in it must be derived from state; pass undefined while loading, never a placeholder. */
  description?: ReactNode
  action?: ReactNode
  className?: string
}

// App v3: title 34 / 800 / -0.03em; sub 16px muted; action bottom-aligned on the right.
export function PageHeader({ title, description, action, className }: PageHeaderProps) {
  return (
    <div className={cn("flex flex-wrap items-end justify-between gap-6", className)}>
      <div className="flex flex-col gap-1.5">
        <h1 className="text-[34px] font-extrabold leading-[1.1] tracking-[-0.03em] text-foreground [text-wrap:balance]">{title}</h1>
        {description && <p className="text-[16px] text-muted-foreground [text-wrap:pretty]">{description}</p>}
      </div>
      {action && <div className="flex items-center gap-2">{action}</div>}
    </div>
  )
}

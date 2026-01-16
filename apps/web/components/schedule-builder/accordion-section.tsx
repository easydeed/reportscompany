"use client"

import type React from "react"
import { ChevronDown, ChevronUp, Check, AlertCircle, Circle } from "lucide-react"
import { cn } from "@/lib/utils"
import type { SectionStatus } from "./types"

interface AccordionSectionProps {
  title: string
  summary?: string
  status: SectionStatus
  isExpanded: boolean
  onToggle: () => void
  children: React.ReactNode
}

export function AccordionSection({ title, summary, status, isExpanded, onToggle, children }: AccordionSectionProps) {
  return (
    <div className="overflow-hidden rounded-xl border bg-background shadow-sm transition-all duration-200">
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-muted/30"
      >
        <div className="flex items-center gap-3">
          <StatusIcon status={status} />
          <div>
            <span className="font-medium">{title}</span>
            {!isExpanded && summary && <div className="text-sm text-muted-foreground">{summary}</div>}
          </div>
        </div>
        {isExpanded ? (
          <ChevronUp className="h-5 w-5 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-5 w-5 text-muted-foreground" />
        )}
      </button>

      <div
        className={cn("grid transition-all duration-200 ease-out", isExpanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]")}
      >
        <div className="overflow-hidden">
          <div className="border-t px-4 py-4">{children}</div>
        </div>
      </div>
    </div>
  )
}

function StatusIcon({ status }: { status: SectionStatus }) {
  switch (status) {
    case "complete":
      return (
        <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500 text-white">
          <Check className="h-3 w-3" />
        </div>
      )
    case "warning":
      return (
        <div className="flex h-5 w-5 items-center justify-center rounded-full bg-amber-500 text-white">
          <AlertCircle className="h-3 w-3" />
        </div>
      )
    case "optional":
      return <Circle className="h-5 w-5 text-muted-foreground" />
  }
}


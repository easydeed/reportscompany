"use client"

import type React from "react"
import { useRef, useState, useEffect } from "react"
import { ChevronDown, Check, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import type { SectionStatus } from "./types"

interface AccordionSectionProps {
  stepNumber?: number
  title: string
  subtitle?: string
  summary?: string | React.ReactNode
  status: SectionStatus
  isExpanded: boolean
  onToggle: () => void
  children: React.ReactNode
}

export function AccordionSection({ 
  stepNumber, 
  title, 
  subtitle,
  summary, 
  status, 
  isExpanded, 
  onToggle, 
  children 
}: AccordionSectionProps) {
  const contentRef = useRef<HTMLDivElement>(null)
  const [contentHeight, setContentHeight] = useState(0)

  useEffect(() => {
    if (contentRef.current) {
      setContentHeight(contentRef.current.scrollHeight)
    }
  }, [children, isExpanded])

  return (
    <div 
      className={cn(
        "rounded-2xl border-2 bg-card shadow-sm transition-all duration-300",
        isExpanded ? "border-violet-200 shadow-md" : "border-border hover:border-violet-100",
        status === "complete" && !isExpanded && "border-emerald-100 bg-emerald-50/30 dark:bg-emerald-950/20"
      )}
    >
      {/* Header */}
      <button
        onClick={onToggle}
        className="flex w-full items-center gap-4 p-5 text-left"
      >
        {/* Step Number / Status */}
        <div className="relative">
          <StepIndicator stepNumber={stepNumber} status={status} isExpanded={isExpanded} />
        </div>

        {/* Title & Summary */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold tracking-tight">{title}</h3>
            {!isExpanded && status === "complete" && summary && (
              <div className="flex items-center gap-2 text-sm text-emerald-700 dark:text-emerald-400 font-medium animate-in fade-in slide-in-from-left-2 duration-300">
                {typeof summary === 'string' ? <span>{summary}</span> : summary}
              </div>
            )}
          </div>
          {isExpanded && subtitle && (
            <p className="mt-0.5 text-sm text-muted-foreground animate-in fade-in duration-200">
              {subtitle}
            </p>
          )}
        </div>

        {/* Chevron */}
        <ChevronDown 
          className={cn(
            "h-5 w-5 text-muted-foreground transition-transform duration-300",
            isExpanded && "rotate-180"
          )} 
        />
      </button>

      {/* Content */}
      <div 
        className="overflow-hidden transition-all duration-300 ease-out"
        style={{ height: isExpanded ? contentHeight : 0 }}
      >
        <div ref={contentRef} className="px-5 pb-6 pt-2">
          <div className={stepNumber ? "ml-12" : ""}>
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}

function StepIndicator({
  stepNumber,
  status,
  isExpanded,
}: {
  stepNumber?: number
  status: SectionStatus
  isExpanded: boolean
}) {
  if (status === "complete" && !isExpanded) {
    return (
      <div className="relative flex h-8 w-8 items-center justify-center">
        {/* Animated ring */}
        <div className="absolute inset-0 rounded-full bg-emerald-500/20 animate-ping" style={{ animationDuration: '1.5s', animationIterationCount: '1' }} />
        {/* Check circle */}
        <div className="relative flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500 text-white shadow-lg shadow-emerald-500/30 animate-in zoom-in duration-300">
          <Check className="h-4 w-4" strokeWidth={3} />
        </div>
      </div>
    )
  }

  if (status === "warning") {
    return (
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-500 text-white shadow-lg shadow-amber-500/30">
        <AlertCircle className="h-4 w-4" />
      </div>
    )
  }

  // Default: Show step number or empty circle
  return (
    <div 
      className={cn(
        "flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold transition-all duration-300",
        isExpanded 
          ? "bg-violet-600 text-white shadow-lg shadow-violet-600/30" 
          : "bg-muted text-muted-foreground"
      )}
    >
      {stepNumber || <div className="h-2 w-2 rounded-full bg-current" />}
    </div>
  )
}

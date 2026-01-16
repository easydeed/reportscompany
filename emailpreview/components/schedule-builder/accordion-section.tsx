"use client"

import type { ReactNode } from "react"
import { Check, AlertCircle, Circle } from "lucide-react"
import { AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"

interface AccordionSectionProps {
  id: string
  title: string
  status: "complete" | "warning" | "optional" | "incomplete"
  summary?: string
  summaryIcon?: ReactNode
  children: ReactNode
}

export function AccordionSection({ id, title, status, summary, summaryIcon, children }: AccordionSectionProps) {
  const StatusIcon = () => {
    switch (status) {
      case "complete":
        return (
          <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
            <Check className="h-3 w-3" />
          </div>
        )
      case "warning":
        return (
          <div className="flex h-5 w-5 items-center justify-center rounded-full bg-amber-100 text-amber-600">
            <AlertCircle className="h-3 w-3" />
          </div>
        )
      case "optional":
        return (
          <div className="flex h-5 w-5 items-center justify-center rounded-full bg-muted text-muted-foreground">
            <Circle className="h-3 w-3" />
          </div>
        )
      default:
        return (
          <div className="flex h-5 w-5 items-center justify-center rounded-full bg-muted text-muted-foreground">
            <Circle className="h-3 w-3" />
          </div>
        )
    }
  }

  return (
    <AccordionItem value={id} className="rounded-lg border bg-card overflow-hidden">
      <AccordionTrigger className="px-4 py-3 hover:no-underline hover:bg-muted/50 [&[data-state=open]>div>.summary]:hidden">
        <div className="flex items-center gap-3 flex-1">
          <StatusIcon />
          <div className="flex flex-col items-start gap-0.5">
            <span className="font-medium">{title}</span>
            {summary && (
              <span className="summary flex items-center gap-1.5 text-sm text-muted-foreground font-normal">
                {summaryIcon}
                {summary}
              </span>
            )}
          </div>
        </div>
      </AccordionTrigger>
      <AccordionContent className="px-4 pb-4 pt-2">{children}</AccordionContent>
    </AccordionItem>
  )
}

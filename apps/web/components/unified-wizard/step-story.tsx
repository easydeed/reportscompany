"use client"

import { cn } from "@/lib/utils"
import {
  Check,
  Image,
  BadgeDollarSign,
  TrendingUp,
  Building2,
  Award,
  CalendarClock,
  BarChart3,
  ListOrdered,
} from "lucide-react"
import type { LucideIcon } from "lucide-react"
import { REPORT_TYPES } from "./types"

const iconMap: Record<string, LucideIcon> = {
  image: Image,
  "badge-dollar-sign": BadgeDollarSign,
  "trending-up": TrendingUp,
  "building-2": Building2,
  award: Award,
  "calendar-clock": CalendarClock,
  "bar-chart-3": BarChart3,
  "list-ordered": ListOrdered,
}

const CATEGORIES = [
  { key: "gallery" as const, label: "Gallery Reports" },
  { key: "data" as const, label: "Data Reports" },
  { key: "analytics" as const, label: "Analytics Reports" },
]

interface StepStoryProps {
  selected: string | null
  onSelect: (reportType: string) => void
}

export function StepStory({ selected, onSelect }: StepStoryProps) {
  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">What report do you want to create?</h2>
        <p className="text-sm text-gray-500 mt-1">Choose from 8 report types across gallery, data, and analytics formats.</p>
      </div>

      {CATEGORIES.map((cat) => {
        const items = REPORT_TYPES.filter((r) => r.category === cat.key)
        return (
          <div key={cat.key}>
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
              {cat.label}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {items.map((rt) => {
                const active = selected === rt.id
                const Icon = iconMap[rt.icon]
                return (
                  <button
                    key={rt.id}
                    onClick={() => onSelect(rt.id)}
                    className={cn(
                      "group relative flex flex-col items-start gap-2 rounded-xl border-2 p-4 text-left transition-all",
                      active
                        ? "border-primary bg-primary/5 shadow-sm"
                        : "border-gray-200 hover:border-primary/40 hover:bg-gray-50/50"
                    )}
                  >
                    <div className="flex items-center gap-2 w-full">
                      {Icon && (
                        <Icon
                          className={cn(
                            "w-5 h-5 flex-shrink-0",
                            active ? "text-primary" : "text-muted-foreground"
                          )}
                        />
                      )}
                      <span className="text-sm font-semibold text-gray-900 flex-1">{rt.title}</span>
                      {active && (
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary flex-shrink-0">
                          <Check className="h-3 w-3 text-white" />
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 leading-relaxed">{rt.description}</p>
                  </button>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}

"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  Check,
  Circle,
  User,
  Palette,
  FileText,
  Calendar,
  UserPlus,
  ChevronRight,
  X,
  Loader2,
  Sparkles,
} from "lucide-react"
import { cn } from "@/lib/utils"

type OnboardingStep = {
  key: string
  title: string
  description: string
  href: string
  icon: string
  required: boolean
  completed: boolean
  skipped: boolean
  completed_at: string | null
}

type OnboardingStatus = {
  user_id: string
  is_complete: boolean
  is_dismissed: boolean
  current_step: string | null
  progress_percent: number
  steps: OnboardingStep[]
  completed_count: number
  total_count: number
}

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  user: User,
  palette: Palette,
  "file-text": FileText,
  calendar: Calendar,
  "user-plus": UserPlus,
}

interface OnboardingChecklistProps {
  className?: string
  variant?: "card" | "inline" | "minimal"
  onComplete?: () => void
}

export function OnboardingChecklist({
  className,
  variant = "card",
  onComplete,
}: OnboardingChecklistProps) {
  const [status, setStatus] = useState<OnboardingStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [dismissing, setDismissing] = useState(false)

  useEffect(() => {
    loadOnboardingStatus()
  }, [])

  async function loadOnboardingStatus() {
    try {
      const res = await fetch("/api/proxy/v1/onboarding", { cache: "no-store" })
      if (res.ok) {
        const data = await res.json()
        setStatus(data)

        // Call onComplete if fully completed
        if (data.is_complete && onComplete) {
          onComplete()
        }
      }
    } catch (error) {
      console.error("Failed to load onboarding status:", error)
    } finally {
      setLoading(false)
    }
  }

  async function dismissOnboarding() {
    setDismissing(true)
    try {
      const res = await fetch("/api/proxy/v1/onboarding/dismiss", {
        method: "POST",
      })
      if (res.ok) {
        setStatus((prev) => prev ? { ...prev, is_dismissed: true } : null)
      }
    } catch (error) {
      console.error("Failed to dismiss onboarding:", error)
    } finally {
      setDismissing(false)
    }
  }

  // Don't show if loading, dismissed, or complete
  if (loading) {
    return (
      <Card className={cn("animate-pulse", className)}>
        <CardContent className="p-6">
          <div className="h-4 bg-muted rounded w-1/2 mb-4" />
          <div className="space-y-3">
            <div className="h-3 bg-muted rounded w-full" />
            <div className="h-3 bg-muted rounded w-3/4" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!status || status.is_dismissed || status.is_complete) {
    return null
  }

  if (variant === "minimal") {
    return (
      <div className={cn("flex items-center gap-3 text-sm", className)}>
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-primary" />
          <span className="font-medium">Setup Progress</span>
        </div>
        <Progress value={status.progress_percent} className="w-24 h-2" />
        <span className="text-muted-foreground">
          {status.completed_count}/{status.total_count}
        </span>
      </div>
    )
  }

  if (variant === "inline") {
    return (
      <div
        className={cn(
          "flex items-center justify-between p-4 rounded-lg border bg-gradient-to-r from-primary/5 to-primary/10",
          className
        )}
      >
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            <span className="font-medium">Complete your setup</span>
          </div>
          <Progress value={status.progress_percent} className="w-32 h-2" />
          <span className="text-sm text-muted-foreground">
            {status.completed_count} of {status.total_count} complete
          </span>
        </div>
        {status.current_step && (
          <Link href={status.steps.find((s) => s.key === status.current_step)?.href || "/app"}>
            <Button size="sm" className="gap-1">
              Continue
              <ChevronRight className="w-4 h-4" />
            </Button>
          </Link>
        )}
      </div>
    )
  }

  // Default card variant
  return (
    <Card className={cn("relative overflow-hidden", className)}>
      {/* Gradient accent */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary via-primary/80 to-primary/60" />

      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            <CardTitle className="text-lg">Welcome! Let's get you set up</CardTitle>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            onClick={dismissOnboarding}
            disabled={dismissing}
          >
            {dismissing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <X className="w-4 h-4" />
            )}
          </Button>
        </div>
        <div className="flex items-center gap-3 mt-2">
          <Progress value={status.progress_percent} className="flex-1 h-2" />
          <span className="text-sm text-muted-foreground whitespace-nowrap">
            {status.completed_count} of {status.total_count}
          </span>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <ul className="space-y-2">
          {status.steps.map((step, index) => {
            const Icon = iconMap[step.icon] || Circle
            const isNext = step.key === status.current_step

            return (
              <li key={step.key}>
                <Link
                  href={step.href}
                  className={cn(
                    "flex items-center gap-3 p-3 rounded-lg transition-all",
                    step.completed
                      ? "bg-green-50 dark:bg-green-950/20"
                      : step.skipped
                      ? "bg-muted/50 opacity-60"
                      : isNext
                      ? "bg-primary/5 ring-1 ring-primary/20 hover:bg-primary/10"
                      : "hover:bg-muted/50"
                  )}
                >
                  {/* Status Icon */}
                  <div
                    className={cn(
                      "flex items-center justify-center w-8 h-8 rounded-full flex-shrink-0",
                      step.completed
                        ? "bg-green-500 text-white"
                        : step.skipped
                        ? "bg-muted text-muted-foreground"
                        : isNext
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground"
                    )}
                  >
                    {step.completed ? (
                      <Check className="w-4 h-4" />
                    ) : (
                      <Icon className="w-4 h-4" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          "font-medium text-sm",
                          step.completed && "text-green-700 dark:text-green-400",
                          step.skipped && "line-through"
                        )}
                      >
                        {step.title}
                      </span>
                      {step.required && !step.completed && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                          Required
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground truncate">
                      {step.description}
                    </p>
                  </div>

                  {/* Arrow */}
                  {!step.completed && !step.skipped && (
                    <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  )}
                </Link>
              </li>
            )
          })}
        </ul>
      </CardContent>
    </Card>
  )
}

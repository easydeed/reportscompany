"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Check,
  Circle,
  User,
  Palette,
  UserPlus,
  ChevronRight,
  X,
  Loader2,
  Building2,
  Users,
  Mail,
  ArrowRight,
  Sparkles,
  Info,
  Zap,
} from "lucide-react"
import { cn } from "@/lib/utils"

export type OnboardingStep = {
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

export type OnboardingStatus = {
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
  "user-plus": UserPlus,
}

interface AffiliateOnboardingProps {
  className?: string
  sponsoredCount?: number
  /** Server-fetched onboarding status to avoid client-side loading flash */
  initialStatus?: OnboardingStatus | null
}

export function AffiliateOnboarding({
  className,
  sponsoredCount = 0,
  initialStatus,
}: AffiliateOnboardingProps) {
  const [status, setStatus] = useState<OnboardingStatus | null>(initialStatus ?? null)
  // If we have initial status, no loading needed
  const [loading, setLoading] = useState(!initialStatus)
  const [dismissing, setDismissing] = useState(false)

  useEffect(() => {
    // Skip fetch if we already have initial status
    if (initialStatus) return
    loadOnboardingStatus()
  }, [initialStatus])

  async function loadOnboardingStatus() {
    try {
      const res = await fetch("/api/proxy/v1/onboarding", { cache: "no-store" })
      if (res.ok) {
        const data = await res.json()
        setStatus(data)
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

  if (!status || status.is_dismissed) {
    return null
  }

  // If complete, show success state
  if (status.is_complete) {
    return (
      <div className={cn("flex items-center gap-3 p-4 rounded-xl border border-green-200 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20", className)}>
        <div className="w-8 h-8 rounded-lg bg-green-500 flex items-center justify-center flex-shrink-0 shadow-sm shadow-green-500/30">
          <Check className="h-4 w-4 text-white" />
        </div>
        <div>
          <p className="text-sm font-semibold text-green-800 dark:text-green-200">
            Setup complete!
          </p>
          <p className="text-xs text-green-600 dark:text-green-400">
            You&apos;re ready to manage your sponsored agents and track their activity.
          </p>
        </div>
      </div>
    )
  }

  return (
    <Card className={cn("relative overflow-hidden", className)}>
      {/* Gradient accent */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary via-primary/80 to-primary/60" />

      <CardHeader className="pb-3 pt-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center shadow-md shadow-primary/20">
              <Building2 className="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <CardTitle className="text-base font-bold">Welcome to your Affiliate Dashboard</CardTitle>
              <CardDescription className="text-xs mt-0.5">
                Let&apos;s set up your account to start sponsoring agents
              </CardDescription>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-muted-foreground hover:text-foreground"
            onClick={dismissOnboarding}
            disabled={dismissing}
          >
            {dismissing ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <X className="w-3.5 h-3.5" />
            )}
          </Button>
        </div>

        {/* Progress bar with percentage */}
        <div className="flex items-center gap-3 mt-3">
          <div className="flex-1 relative">
            <Progress value={status.progress_percent} className="h-2" />
          </div>
          <span className="text-xs font-semibold text-primary tabular-nums min-w-[2.5rem] text-right">
            {Math.round(status.progress_percent)}%
          </span>
        </div>
      </CardHeader>

      <CardContent className="pt-0 space-y-3 pb-4">
        {/* Steps list */}
        <ul className="space-y-1.5">
          {status.steps.map((step) => {
            const Icon = iconMap[step.icon] || Circle
            const isNext = step.key === status.current_step

            return (
              <li key={step.key}>
                <Link
                  href={step.href}
                  prefetch={false}
                  className={cn(
                    "flex items-center gap-3 p-3 rounded-xl transition-all duration-200 group",
                    step.completed
                      ? "bg-green-50/80 dark:bg-green-950/20"
                      : step.skipped
                      ? "bg-muted/30 opacity-50"
                      : isNext
                      ? "bg-primary/5 ring-1 ring-primary/20 hover:bg-primary/10 shadow-sm"
                      : "hover:bg-muted/50"
                  )}
                >
                  {/* Status Icon */}
                  <div
                    className={cn(
                      "flex items-center justify-center w-8 h-8 rounded-lg flex-shrink-0 transition-all duration-200",
                      step.completed
                        ? "bg-green-500 text-white shadow-sm shadow-green-500/30"
                        : step.skipped
                        ? "bg-muted text-muted-foreground"
                        : isNext
                        ? "bg-primary text-primary-foreground shadow-sm shadow-primary/30"
                        : "bg-muted/80 text-muted-foreground group-hover:bg-muted"
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
                          step.skipped && "line-through text-muted-foreground"
                        )}
                      >
                        {step.title}
                      </span>
                      {step.required && !step.completed && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 font-medium">
                          Required
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground truncate mt-0.5">
                      {step.description}
                    </p>
                  </div>

                  {/* Arrow */}
                  {!step.completed && !step.skipped && (
                    <ChevronRight className={cn(
                      "w-4 h-4 flex-shrink-0 transition-transform duration-200",
                      isNext ? "text-primary group-hover:translate-x-0.5" : "text-muted-foreground group-hover:translate-x-0.5"
                    )} />
                  )}
                </Link>
              </li>
            )
          })}
        </ul>

        {/* Helpful tip based on current step */}
        {status.current_step === "branding_setup" && (
          <div className="flex items-start gap-3 p-3 rounded-xl bg-blue-50/80 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900/30">
            <div className="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
              <Info className="h-3.5 w-3.5 text-blue-600" />
            </div>
            <div>
              <p className="text-xs font-semibold text-blue-800 dark:text-blue-200">Pro Tip</p>
              <p className="text-xs text-blue-700 dark:text-blue-300 mt-0.5">
                Your branding (logo, colors) will appear on all reports generated by your sponsored agents.
              </p>
            </div>
          </div>
        )}

        {status.current_step === "first_agent_invited" && (
          <div className="flex items-start gap-3 p-3 rounded-xl bg-blue-50/80 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900/30">
            <div className="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
              <Mail className="h-3.5 w-3.5 text-blue-600" />
            </div>
            <div>
              <p className="text-xs font-semibold text-blue-800 dark:text-blue-200">Pro Tip</p>
              <p className="text-xs text-blue-700 dark:text-blue-300 mt-0.5">
                When you invite an agent, they&apos;ll receive an email with a link to set up their account. They&apos;ll automatically see your branding on their reports.
              </p>
            </div>
          </div>
        )}

        {/* Quick stats for context */}
        {sponsoredCount > 0 && (
          <div className="flex items-center gap-3 p-3 bg-muted/30 rounded-xl border border-border/50">
            <div className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
              <Users className="w-3.5 h-3.5 text-primary" />
            </div>
            <span className="text-xs text-muted-foreground">
              You have <strong className="text-foreground font-semibold">{sponsoredCount}</strong> sponsored agent{sponsoredCount !== 1 ? 's' : ''}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

/**
 * Inline variant for showing in the header area
 */
export function AffiliateOnboardingBanner({ className }: { className?: string }) {
  const [status, setStatus] = useState<OnboardingStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch("/api/proxy/v1/onboarding", { cache: "no-store" })
        if (res.ok) {
          setStatus(await res.json())
        }
      } catch (error) {
        console.error("Failed to load onboarding:", error)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading || !status || status.is_dismissed || status.is_complete) {
    return null
  }

  const nextStep = status.steps.find(s => s.key === status.current_step)

  return (
    <div
      className={cn(
        "flex items-center justify-between p-4 rounded-xl border bg-gradient-to-r from-primary/5 to-primary/10",
        className
      )}
    >
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-primary" />
          </div>
          <span className="font-semibold text-sm">Complete your affiliate setup</span>
        </div>
        <Progress value={status.progress_percent} className="w-32 h-2" />
        <span className="text-xs font-medium text-muted-foreground">
          {status.completed_count} of {status.total_count} complete
        </span>
      </div>
      {nextStep && (
        <Link href={nextStep.href} prefetch={false}>
          <Button size="sm" className="gap-1.5 shadow-sm">
            {nextStep.title}
            <ArrowRight className="w-3.5 h-3.5" />
          </Button>
        </Link>
      )}
    </div>
  )
}

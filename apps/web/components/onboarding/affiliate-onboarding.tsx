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
      <Alert className={cn("border-green-200 bg-green-50 dark:bg-green-950/20", className)}>
        <Check className="h-4 w-4 text-green-600" />
        <AlertDescription className="text-green-800 dark:text-green-200">
          <strong>Setup complete!</strong> You&apos;re ready to manage your sponsored agents and track their activity.
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <Card className={cn("relative overflow-hidden", className)}>
      {/* Gradient accent */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary via-primary/80 to-primary/60" />

      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Building2 className="w-5 h-5 text-primary" />
            <div>
              <CardTitle className="text-lg">Welcome to your Affiliate Dashboard</CardTitle>
              <CardDescription>
                Let&apos;s set up your account to start sponsoring agents
              </CardDescription>
            </div>
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
        <div className="flex items-center gap-3 mt-3">
          <Progress value={status.progress_percent} className="flex-1 h-2" />
          <span className="text-sm text-muted-foreground whitespace-nowrap">
            {status.completed_count} of {status.total_count} complete
          </span>
        </div>
      </CardHeader>

      <CardContent className="pt-0 space-y-4">
        {/* Steps list */}
        <ul className="space-y-2">
          {status.steps.map((step) => {
            const Icon = iconMap[step.icon] || Circle
            const isNext = step.key === status.current_step

            return (
              <li key={step.key}>
                <Link
                  href={step.href}
                  prefetch={false}
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

        {/* Helpful tip based on current step */}
        {status.current_step === "branding_setup" && (
          <Alert className="bg-blue-50 dark:bg-blue-950/20 border-blue-200">
            <Info className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800 dark:text-blue-200 text-sm">
              <strong>Tip:</strong> Your branding (logo, colors) will appear on all reports generated by your sponsored agents.
            </AlertDescription>
          </Alert>
        )}

        {status.current_step === "first_agent_invited" && (
          <Alert className="bg-blue-50 dark:bg-blue-950/20 border-blue-200">
            <Mail className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800 dark:text-blue-200 text-sm">
              <strong>Tip:</strong> When you invite an agent, they&apos;ll receive an email with a link to set up their account. They&apos;ll automatically see your branding on their reports.
            </AlertDescription>
          </Alert>
        )}

        {/* Quick stats for context */}
        {sponsoredCount > 0 && (
          <div className="flex items-center gap-2 p-3 bg-muted/30 rounded-lg">
            <Users className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              You have <strong className="text-foreground">{sponsoredCount}</strong> sponsored agent{sponsoredCount !== 1 ? 's' : ''}
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
        "flex items-center justify-between p-4 rounded-lg border bg-gradient-to-r from-primary/5 to-primary/10",
        className
      )}
    >
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-primary" />
          <span className="font-medium">Complete your affiliate setup</span>
        </div>
        <Progress value={status.progress_percent} className="w-32 h-2" />
        <span className="text-sm text-muted-foreground">
          {status.completed_count} of {status.total_count} complete
        </span>
      </div>
      {nextStep && (
        <Link href={nextStep.href} prefetch={false}>
          <Button size="sm" className="gap-1">
            {nextStep.title}
            <ArrowRight className="w-4 h-4" />
          </Button>
        </Link>
      )}
    </div>
  )
}

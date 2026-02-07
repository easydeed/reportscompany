"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import {
  FileText,
  Calendar,
  Users,
  Palette,
  Plus,
  ArrowRight,
  PlayCircle,
  Sparkles,
} from "lucide-react"
import { cn } from "@/lib/utils"

type EmptyStateVariant = "reports" | "schedules" | "contacts" | "branding" | "generic"

interface EmptyStateProps {
  variant?: EmptyStateVariant
  title?: string
  description?: string
  actionLabel?: string
  actionHref?: string
  secondaryLabel?: string
  secondaryHref?: string
  className?: string
}

const variants: Record<EmptyStateVariant, {
  icon: React.ComponentType<{ className?: string }>
  title: string
  description: string
  actionLabel: string
  actionHref: string
  secondaryLabel?: string
  secondaryHref?: string
  gradient: string
  iconColor: string
  accentColor: string
}> = {
  reports: {
    icon: FileText,
    title: "No reports yet",
    description: "Create your first market report to share insights with your clients. It only takes a few seconds.",
    actionLabel: "Create Report",
    actionHref: "/app/reports/new",
    secondaryLabel: "Watch Tutorial",
    secondaryHref: "#",
    gradient: "from-indigo-500/10 via-indigo-500/5 to-transparent",
    iconColor: "bg-indigo-500/10 text-indigo-600",
    accentColor: "bg-indigo-500",
  },
  schedules: {
    icon: Calendar,
    title: "No scheduled reports",
    description: "Set up automated reports to keep your clients informed with regular market updates.",
    actionLabel: "Create Schedule",
    actionHref: "/app/schedules/new",
    gradient: "from-blue-500/10 via-blue-500/5 to-transparent",
    iconColor: "bg-blue-500/10 text-blue-600",
    accentColor: "bg-blue-500",
  },
  contacts: {
    icon: Users,
    title: "No contacts yet",
    description: "Add contacts to easily send reports and manage your client relationships.",
    actionLabel: "Add Contact",
    actionHref: "/app/people",
    gradient: "from-emerald-500/10 via-emerald-500/5 to-transparent",
    iconColor: "bg-emerald-500/10 text-emerald-600",
    accentColor: "bg-emerald-500",
  },
  branding: {
    icon: Palette,
    title: "Branding not configured",
    description: "Add your logo and brand colors to personalize your reports.",
    actionLabel: "Set Up Branding",
    actionHref: "/app/branding",
    gradient: "from-orange-500/10 via-orange-500/5 to-transparent",
    iconColor: "bg-orange-500/10 text-orange-600",
    accentColor: "bg-orange-500",
  },
  generic: {
    icon: Plus,
    title: "Nothing here yet",
    description: "Get started by creating your first item.",
    actionLabel: "Get Started",
    actionHref: "/app",
    gradient: "from-slate-500/10 via-slate-500/5 to-transparent",
    iconColor: "bg-slate-500/10 text-slate-600",
    accentColor: "bg-slate-500",
  },
}

export function EmptyState({
  variant = "generic",
  title,
  description,
  actionLabel,
  actionHref,
  secondaryLabel,
  secondaryHref,
  className,
}: EmptyStateProps) {
  const config = variants[variant]
  const Icon = config.icon

  const finalTitle = title || config.title
  const finalDescription = description || config.description
  const finalActionLabel = actionLabel || config.actionLabel
  const finalActionHref = actionHref || config.actionHref
  const finalSecondaryLabel = secondaryLabel || config.secondaryLabel
  const finalSecondaryHref = secondaryHref || config.secondaryHref

  return (
    <div
      className={cn(
        "relative flex flex-col items-center justify-center text-center p-10 rounded-2xl border-2 border-dashed overflow-hidden",
        `bg-gradient-to-br ${config.gradient}`,
        className
      )}
    >
      {/* Decorative background elements */}
      <div className="absolute top-4 right-4 opacity-[0.04]">
        <Icon className="w-32 h-32" />
      </div>

      <div className={cn(
        "w-16 h-16 rounded-2xl flex items-center justify-center mb-5 shadow-lg",
        config.iconColor
      )}>
        <Icon className="w-8 h-8" />
      </div>

      <h3 className="text-lg font-bold mb-2">{finalTitle}</h3>
      <p className="text-sm text-muted-foreground max-w-sm mb-6 leading-relaxed">
        {finalDescription}
      </p>

      <div className="flex flex-col sm:flex-row items-center gap-3">
        <Link href={finalActionHref} prefetch={false}>
          <Button className="gap-2 shadow-md hover:shadow-lg transition-shadow">
            <Plus className="w-4 h-4" />
            {finalActionLabel}
          </Button>
        </Link>

        {finalSecondaryLabel && finalSecondaryHref && (
          <Link href={finalSecondaryHref} prefetch={false}>
            <Button variant="outline" className="gap-2">
              <PlayCircle className="w-4 h-4" />
              {finalSecondaryLabel}
            </Button>
          </Link>
        )}
      </div>
    </div>
  )
}

/**
 * Inline empty state for smaller contexts (tables, lists)
 */
export function EmptyStateInline({
  title,
  description,
  actionLabel,
  actionHref,
  className,
}: {
  title: string
  description?: string
  actionLabel?: string
  actionHref?: string
  className?: string
}) {
  return (
    <div className={cn("flex items-center justify-between p-4 rounded-xl bg-muted/30 border border-border/50", className)}>
      <div>
        <p className="font-semibold text-sm">{title}</p>
        {description && (
          <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
        )}
      </div>
      {actionLabel && actionHref && (
        <Link href={actionHref} prefetch={false}>
          <Button size="sm" variant="outline" className="gap-1.5">
            {actionLabel}
            <ArrowRight className="w-3 h-3" />
          </Button>
        </Link>
      )}
    </div>
  )
}

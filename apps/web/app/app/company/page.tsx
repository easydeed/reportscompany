"use client"

import { useState } from "react"
import Link from "next/link"
import {
  Users,
  FileText,
  TrendingUp,
  Activity,
  MoreHorizontal,
  Plus,
  Settings,
  Download,
  Eye,
  Mail,
  UserX,
  Building2,
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { useCompanyOverview } from "@/hooks/use-api"
import { useToast } from "@/components/ui/use-toast"

interface TitleRep {
  id: string
  name: string
  email: string
  office: string
  agent_count: number
  reports_this_month: number
  last_active: string | null
  status: "active" | "pending" | "deactivated"
}

interface ActivityEvent {
  id: string
  description: string
  timestamp: string
}

interface CompanyOverview {
  company: {
    name: string
    plan: string
    usage: number
    limit: number
    initials: string
  }
  metrics: {
    total_reps: number
    total_agents: number
    reports_this_month: number
    active_agents_30d: number
    total_agent_seats: number
    reps_change: number
    agents_change: number
    reports_change_pct: number
    engagement_pct: number
  }
  reps: TitleRep[]
  activity: ActivityEvent[]
}

function getStatusBadge(status: TitleRep["status"]) {
  switch (status) {
    case "active":
      return (
        <Badge className="bg-[#DCFCE7] text-[#166534] hover:bg-[#DCFCE7]">
          <CheckCircle2 className="mr-1 h-3 w-3" />
          Active
        </Badge>
      )
    case "pending":
      return (
        <Badge className="bg-[#FEF9C3] text-[#854D0E] hover:bg-[#FEF9C3]">
          <Clock className="mr-1 h-3 w-3" />
          Pending
        </Badge>
      )
    case "deactivated":
      return (
        <Badge className="bg-[#F1F5F9] text-[#64748B] hover:bg-[#F1F5F9]">
          <AlertCircle className="mr-1 h-3 w-3" />
          Deactivated
        </Badge>
      )
  }
}

function formatRelativeTime(dateStr: string | null) {
  if (!dateStr) return "Never"
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return "Just now"
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days < 30) return `${days}d ago`
  return `${Math.floor(days / 30)}mo ago`
}

function getInitials(name: string) {
  return name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)
}

const AVATAR_COLORS = [
  "bg-[#6366F1]",
  "bg-[#4338CA]",
  "bg-[#818CF8]",
  "bg-[#312E81]",
  "bg-[#94A3B8]",
  "bg-[#7C3AED]",
]

export default function CompanyDashboard() {
  const { data, isLoading, error } = useCompanyOverview()
  const { toast } = useToast()
  const [resendModal, setResendModal] = useState<{ open: boolean; rep: TitleRep | null }>({
    open: false,
    rep: null,
  })
  const [resending, setResending] = useState(false)

  async function handleResendInvite(rep: TitleRep) {
    setResending(true)
    try {
      const res = await fetch("/api/proxy/v1/company/resend-invite", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: rep.email }),
      })
      const result = await res.json()
      if (res.ok) {
        toast({ title: "Invitation sent", description: `New invitation sent to ${rep.email}` })
        setResendModal({ open: false, rep: null })
      } else {
        toast({
          title: "Error",
          description: typeof result.detail === "string" ? result.detail : "Failed to resend invitation",
          variant: "destructive",
        })
      }
    } catch {
      toast({ title: "Error", description: "Network error — please try again", variant: "destructive" })
    } finally {
      setResending(false)
    }
  }

  if (isLoading) return <DashboardSkeleton />

  if (error || !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <Building2 className="h-16 w-16 text-muted-foreground mb-4" />
        <h1 className="text-2xl font-bold mb-2">Unable to Load Dashboard</h1>
        <p className="text-muted-foreground max-w-md mb-6">
          {error?.message?.includes("403")
            ? "This account is not a title company admin."
            : "Failed to load company data. Please try again."}
        </p>
        <Button asChild>
          <Link href="/app">Back to Dashboard</Link>
        </Button>
      </div>
    )
  }

  const overview = data as CompanyOverview
  const { company, metrics, reps, activity } = overview
  const usagePercent = company.limit > 0 ? (company.usage / company.limit) * 100 : 0

  const metricCards = [
    {
      label: "TITLE REPS",
      value: String(metrics.total_reps),
      change: metrics.reps_change,
      changeLabel: "this month",
      icon: Users,
    },
    {
      label: "TOTAL AGENTS",
      value: String(metrics.total_agents),
      change: metrics.agents_change,
      changeLabel: "this month",
      icon: Users,
    },
    {
      label: "REPORTS THIS MONTH",
      value: String(metrics.reports_this_month),
      change: metrics.reports_change_pct,
      changeLabel: "vs last month",
      icon: FileText,
      isPercent: true,
    },
    {
      label: "ACTIVE AGENTS (30D)",
      value: `${metrics.active_agents_30d} / ${metrics.total_agents}`,
      change: metrics.engagement_pct,
      changeLabel: "engagement",
      icon: Activity,
      isPercent: true,
    },
  ]

  const quickActions = [
    { label: "Invite New Rep", href: "/app/company/reps", icon: Plus },
    { label: "Edit Company Branding", href: "/app/company/branding", icon: Settings },
    { label: "View All Agents", href: "/app/company/agents", icon: Users },
    { label: "Download Activity Report", href: "#", icon: Download, isDownload: true },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      {/* Company Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-[#6366F1] text-xl font-bold text-white">
            {company.initials || getInitials(company.name)}
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">{company.name}</h1>
            <div className="mt-1 flex items-center gap-3">
              <Badge className="bg-[#EEF2FF] text-[#4338CA] hover:bg-[#EEF2FF]">
                {company.plan} Plan
              </Badge>
              <span className="text-sm text-muted-foreground">
                {company.usage.toLocaleString()} / {company.limit.toLocaleString()} reports
              </span>
            </div>
          </div>
        </div>
        <Button variant="outline" asChild>
          <Link href="/app/company/branding">
            <Settings className="mr-2 h-4 w-4" />
            Edit Branding
          </Link>
        </Button>
      </div>

      {/* Usage Bar */}
      <div className="mt-4">
        <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-[#6366F1] transition-all"
            style={{ width: `${Math.min(usagePercent, 100)}%` }}
          />
        </div>
      </div>

      {/* Metrics Row */}
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metricCards.map((metric) => (
          <div
            key={metric.label}
            className="rounded-xl border border-border bg-card p-5"
          >
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                {metric.label}
              </span>
              <metric.icon className="h-4 w-4 text-muted-foreground/60" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-bold text-foreground">
                {metric.value}
              </span>
              {metric.change > 0 && (
                <span className="flex items-center text-sm font-medium text-[#16A34A]">
                  <TrendingUp className="mr-0.5 h-3 w-3" />
                  {metric.isPercent ? `${metric.change}%` : `+${metric.change}`}
                </span>
              )}
            </div>
            <p className="mt-1 text-xs text-muted-foreground/70">{metric.changeLabel}</p>
          </div>
        ))}
      </div>

      {/* Title Reps Table */}
      <div className="mt-8">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">Title Reps</h2>
          <Button asChild>
            <Link href="/app/company/reps">
              <Plus className="mr-2 h-4 w-4" />
              Invite Rep
            </Link>
          </Button>
        </div>

        <div className="mt-4 overflow-hidden rounded-xl border border-border bg-card">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/40">
                  <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                    Rep Name
                  </th>
                  <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                    Office / Area
                  </th>
                  <th className="px-4 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                    Agents
                  </th>
                  <th className="px-4 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                    Reports (30d)
                  </th>
                  <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                    Last Active
                  </th>
                  <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                    Status
                  </th>
                  <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {reps.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-12 text-center">
                      <Users className="mx-auto h-10 w-10 text-muted-foreground/40 mb-3" />
                      <p className="text-sm font-medium text-muted-foreground">No reps yet</p>
                      <p className="text-xs text-muted-foreground/70 mt-1">Invite your first title rep to get started</p>
                      <Button size="sm" className="mt-3" asChild>
                        <Link href="/app/company/reps">
                          <Plus className="mr-1 h-3.5 w-3.5" />
                          Invite Rep
                        </Link>
                      </Button>
                    </td>
                  </tr>
                ) : (
                  reps.slice(0, 5).map((rep, idx) => (
                    <tr key={rep.id} className="transition-colors hover:bg-muted/30">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div
                            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white ${AVATAR_COLORS[idx % AVATAR_COLORS.length]}`}
                          >
                            {getInitials(rep.name)}
                          </div>
                          <div>
                            <p className="text-sm font-medium text-foreground">{rep.name}</p>
                            <p className="text-xs text-muted-foreground">{rep.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-muted-foreground">
                        {rep.office || "—"}
                      </td>
                      <td className="px-4 py-3 text-center text-sm font-medium text-foreground tabular-nums">
                        {rep.agent_count}
                      </td>
                      <td className="px-4 py-3 text-center text-sm font-medium text-foreground tabular-nums">
                        {rep.reports_this_month}
                      </td>
                      <td className="px-4 py-3 text-sm text-muted-foreground">
                        {formatRelativeTime(rep.last_active)}
                      </td>
                      <td className="px-4 py-3">{getStatusBadge(rep.status)}</td>
                      <td className="px-4 py-3 text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem asChild>
                              <Link href={`/app/company/agents?rep=${rep.id}`}>
                                <Eye className="mr-2 h-4 w-4" />
                                View Agents
                              </Link>
                            </DropdownMenuItem>
                            {rep.status === "pending" && (
                              <DropdownMenuItem onClick={() => setResendModal({ open: true, rep })}>
                                <Mail className="mr-2 h-4 w-4" />
                                Resend Invite
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-red-600">
                              <UserX className="mr-2 h-4 w-4" />
                              {rep.status === "active" ? "Deactivate" : "Remove"}
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {reps.length > 5 && (
          <div className="mt-2 text-right">
            <Link
              href="/app/company/reps"
              className="text-sm font-medium text-[#6366F1] hover:underline"
            >
              View all reps →
            </Link>
          </div>
        )}
      </div>

      {/* Two Column Layout */}
      <div className="mt-8 grid gap-6 lg:grid-cols-5">
        {/* Recent Activity */}
        <div className="lg:col-span-3">
          <div className="rounded-xl border border-border bg-card">
            <div className="border-b border-border px-5 py-4">
              <h3 className="font-semibold text-foreground">Recent Activity</h3>
            </div>
            <div className="divide-y divide-border">
              {activity.length === 0 ? (
                <div className="px-5 py-8 text-center">
                  <Activity className="mx-auto h-8 w-8 text-muted-foreground/40 mb-2" />
                  <p className="text-sm text-muted-foreground">No recent activity</p>
                </div>
              ) : (
                activity.map((event) => (
                  <div
                    key={event.id}
                    className="flex items-center justify-between px-5 py-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#EEF2FF]">
                        <Building2 className="h-4 w-4 text-[#6366F1]" />
                      </div>
                      <p className="text-sm text-muted-foreground">{event.description}</p>
                    </div>
                    <span className="shrink-0 text-xs text-muted-foreground/60">
                      {event.timestamp}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="lg:col-span-2">
          <div className="rounded-xl border border-border bg-card">
            <div className="border-b border-border px-5 py-4">
              <h3 className="font-semibold text-foreground">Quick Actions</h3>
            </div>
            <div className="p-4">
              <div className="grid gap-2">
                {quickActions.map((action) => (
                  <Button
                    key={action.label}
                    variant="outline"
                    className="justify-start"
                    asChild={!action.isDownload}
                  >
                    {action.isDownload ? (
                      <>
                        <action.icon className="mr-2 h-4 w-4" />
                        {action.label}
                      </>
                    ) : (
                      <Link href={action.href}>
                        <action.icon className="mr-2 h-4 w-4" />
                        {action.label}
                      </Link>
                    )}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Resend Invite Modal */}
      <Dialog open={resendModal.open} onOpenChange={(o) => !o && setResendModal({ open: false, rep: null })}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Resend Invitation</DialogTitle>
            <DialogDescription>Send a new invitation email to this title rep.</DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                <span className="text-sm font-semibold text-primary">
                  {resendModal.rep?.name?.[0]?.toUpperCase()}
                </span>
              </div>
              <div>
                <p className="text-sm font-medium">{resendModal.rep?.name}</p>
                <p className="text-sm text-muted-foreground">{resendModal.rep?.email}</p>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setResendModal({ open: false, rep: null })}>
              Cancel
            </Button>
            <Button
              onClick={() => resendModal.rep && handleResendInvite(resendModal.rep)}
              disabled={resending}
            >
              {resending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Send Invitation
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function DashboardSkeleton() {
  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <div className="flex items-center gap-4">
        <Skeleton className="h-14 w-14 rounded-xl" />
        <div>
          <Skeleton className="h-7 w-48 mb-2" />
          <Skeleton className="h-5 w-64" />
        </div>
      </div>
      <Skeleton className="h-2 w-full rounded-full" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="rounded-xl border border-border bg-card p-5">
            <Skeleton className="h-4 w-24 mb-3" />
            <Skeleton className="h-9 w-16" />
          </div>
        ))}
      </div>
      <div className="rounded-xl border border-border bg-card">
        <div className="p-4">
          <Skeleton className="h-6 w-32 mb-4" />
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-4 py-3">
              <Skeleton className="h-9 w-9 rounded-full" />
              <Skeleton className="h-4 w-40 flex-1" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-5 w-16 rounded-full" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

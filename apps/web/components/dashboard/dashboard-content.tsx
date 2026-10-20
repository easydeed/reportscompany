'use client'

import Link from 'next/link'
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle, AlertTriangle, FileText, Mail, Calendar, Clock, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardTitle } from "@/components/ui/card"
import { DashboardOnboarding } from "@/components/onboarding"
import { PageHeader } from "@/components/page-header"
import { MetricCard } from "@/components/metric-card"
import { StatusBadge } from "@/components/status-badge"
import { useUsage, usePlanUsage, useOnboarding, useSchedules, useAllLeads,
         useBranding, useMe } from "@/hooks/use-api"
import { SharedPDFPreview } from "@/components/shared/pdf-preview"
import type { PreviewReportType } from "@/components/shared/email-preview/sample-data"

interface UsageData {
  summary?: {
    total_reports?: number
    avg_ms?: number
  }
  limits?: {
    active_schedules?: number
  }
  recent_reports?: Array<{
    id: string
    type: string
    city: string
    status: string
    created_at: string
    pdf_url?: string
  }>
  recent_emails?: Array<{
    id: string
    subject: string
    to: string
    status: string
    created_at: string
  }>
}

// Format relative time
function formatRelativeTime(timestamp: string): string {
  const now = new Date()
  const then = new Date(timestamp)
  const diffMs = now.getTime() - then.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return "Just now"
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return then.toLocaleDateString()
}

export function DashboardContent() {
  const { data: usageData, isLoading: usageLoading } = useUsage()
  const { data: planUsageData, isLoading: planLoading } = usePlanUsage()
  const { data: onboardingData, isLoading: onboardingLoading } = useOnboarding()
  const { data: schedulesData } = useSchedules()
  const { data: leadsData } = useAllLeads()
  const { data: brandingData } = useBranding()
  const { data: meData } = useMe()

  const loading = usageLoading || planLoading || onboardingLoading
  const usage: UsageData | null = usageData || null
  const planUsage = planUsageData || null
  const onboarding = onboardingData || null

  // Build recent activity from fetched data
  const recentReports = (usage?.recent_reports ?? []).map((r) => ({
    id: r.id,
    type: 'report' as const,
    // The API's own kind string, kept alongside the humanised title so the
    // embedded preview can be asked for the right layout. `title` has already
    // had its underscores replaced and been title-cased, which no longer
    // matches any PreviewReportType.
    rawType: r.type,
    title: `${r.type?.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}`,
    area: r.city || 'Unknown',
    status: r.status,
    timestamp: r.created_at,
    url: r.pdf_url,
  }))
  
  const recentEmails = (usage?.recent_emails ?? []).map((e) => ({
    id: e.id,
    type: 'email' as const,
    title: e.subject || 'Email sent',
    area: e.to || '',
    status: e.status,
    timestamp: e.created_at,
  }))
  
  const recentActivity = [...recentReports, ...recentEmails]
    .sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''))
    .slice(0, 8)

  // ───────────────────────────────────────────────────────────────────────
  // B4. Design's four pieces, each derived from state that already exists.
  //
  // Two of their constraints shape every line below:
  //
  //   #4  "every number in a title or lead sentence is computed from plan
  //        limits, usage and schedule state. No sentence should ship with a
  //        literal number in it. Show '—' or 'Nothing scheduled', never 0 as
  //        a fake value."
  //   #6  "Sentence titles replace page names WHERE STATE EXISTS. If the
  //        state can't be computed, fall back to the page name — don't ship a
  //        sentence with blanks."
  //
  // So every derivation below returns `null` when it cannot be computed, and
  // the render shows the fallback rather than a sentence with a hole in it.
  // ───────────────────────────────────────────────────────────────────────

  const mkt = planUsage?.plan?.market_reports_limit
  const used = planUsage?.usage?.market_reports_used
  const remaining =
    typeof mkt === 'number' && typeof used === 'number' && mkt < 99999
      ? Math.max(mkt - used, 0)
      : null
  const planName = planUsage?.plan?.plan_name ?? null

  //: The sentence title. Null whenever either half is missing — a plan with
  //: no finite limit has no "left this month" to state, and an unlimited plan
  //: is not "0 left" (D-195's mistake, in prose).
  const sentenceTitle =
    remaining !== null && planName
      ? `${remaining} report${remaining === 1 ? '' : 's'} left on ${planName}`
      : null

  const latest = recentReports[0] ?? null

  const schedules: any[] = Array.isArray(schedulesData)
    ? schedulesData
    : (schedulesData as any)?.schedules ?? []
  //: The soonest future send among ACTIVE schedules. A paused schedule has no
  //: next send, and a past next_run_at is a worker that has not caught up —
  //: neither is "next".
  const nextSend = schedules
    .filter((x) => x?.active && x?.next_run_at && new Date(x.next_run_at) > new Date())
    .sort((a, b) => a.next_run_at.localeCompare(b.next_run_at))[0] ?? null

  const leads: any[] = Array.isArray(leadsData)
    ? leadsData
    : (leadsData as any)?.leads ?? []
  //: "Call these first" — new leads, newest first. `new` is one of exactly
  //: three states the database permits (leads_status_check), so this is the
  //: whole of the un-actioned set rather than a guess at one.
  const callFirst = leads
    .filter((l) => (l?.status ?? 'new') === 'new')
    .sort((a, b) => (b.created_at ?? '').localeCompare(a.created_at ?? ''))
    .slice(0, 5)

  const branding: any = brandingData ?? {}
  const me: any = meData ?? {}

  return (
    <div className="space-y-5">
      {/* Header — renders instantly */}
      <PageHeader
        title={sentenceTitle ?? "Overview"}
        description={sentenceTitle ? "Your account at a glance" : "Your account activity and key metrics"}
        action={
          <Button asChild size="sm">
            <Link href="/app/reports/new" prefetch={false}>
              <Plus className="w-4 h-4 mr-1.5" />
              New Report
            </Link>
          </Button>
        }
      />

      {/* Per-product limit alerts — only show after data loads */}
      {!loading && planUsage?.limits && (
        <>
          {planUsage.limits.market_reports?.status === 'at_limit' || planUsage.limits.market_reports?.status === 'exceeded' ? (
            <Alert className="border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertTitle className="text-red-800">Market Report Limit Reached</AlertTitle>
              <AlertDescription className="flex items-center justify-between text-red-700">
                <span>
                  You've used all {planUsage.limits.market_reports.limit} market reports this month.
                </span>
                <Button asChild variant="outline" size="sm" className="ml-4 border-red-600 text-red-700 hover:bg-red-100">
                  <Link href="/app/settings/billing" prefetch={false}>Upgrade</Link>
                </Button>
              </AlertDescription>
            </Alert>
          ) : planUsage.limits.market_reports?.status === 'warning' ? (
            <Alert className="border-amber-200 bg-amber-50">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              <AlertTitle className="text-amber-800">Approaching Market Report Limit</AlertTitle>
              <AlertDescription className="flex items-center justify-between text-amber-700">
                <span>
                  You've used {planUsage.limits.market_reports.used} of {planUsage.limits.market_reports.limit} market reports this month.
                </span>
                <Button asChild variant="outline" size="sm" className="ml-4 border-amber-600 text-amber-700 hover:bg-amber-100">
                  <Link href="/app/settings/billing" prefetch={false}>View Plan</Link>
                </Button>
              </AlertDescription>
            </Alert>
          ) : null}

          {planUsage.limits.schedules?.status === 'at_limit' || planUsage.limits.schedules?.status === 'exceeded' ? (
            <Alert className="border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertTitle className="text-red-800">Schedule Limit Reached</AlertTitle>
              <AlertDescription className="flex items-center justify-between text-red-700">
                <span>
                  You've used all {planUsage.limits.schedules.limit} active schedules on your plan.
                </span>
                <Button asChild variant="outline" size="sm" className="ml-4 border-red-600 text-red-700 hover:bg-red-100">
                  <Link href="/app/settings/billing" prefetch={false}>Upgrade</Link>
                </Button>
              </AlertDescription>
            </Alert>
          ) : null}

          {planUsage.limits.property_reports?.status === 'at_limit' || planUsage.limits.property_reports?.status === 'exceeded' ? (
            <Alert className="border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertTitle className="text-red-800">Property Report Limit Reached</AlertTitle>
              <AlertDescription className="flex items-center justify-between text-red-700">
                <span>
                  You've used all {planUsage.limits.property_reports.limit} property reports this month.
                </span>
                <Button asChild variant="outline" size="sm" className="ml-4 border-red-600 text-red-700 hover:bg-red-100">
                  <Link href="/app/settings/billing" prefetch={false}>Upgrade</Link>
                </Button>
              </AlertDescription>
            </Alert>
          ) : null}
        </>
      )}

      {/* ── Latest report · Next send · Call these first ─────────────────
          Design replaces the four stat tiles with these. The tiles counted
          things ("Reports 14", "Avg. Render 312ms"); these say what to do
          next, which is what a dashboard opened every morning is for. Every
          number here is computed, and every absence says so in words rather
          than rendering a zero. */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* Latest report — the artifact, not a count of artifacts. */}
        {/* ui/Card, not a hand-rolled div. Three of twenty-two routes used
            the primitive before this batch; adding three more hand-rolled
            ones would widen exactly the gap just reported to Design. */}
        <Card className="lg:col-span-1 gap-3">
          <CardTitle className="text-[11px] font-bold uppercase tracking-[0.08em] text-muted-foreground">
            Latest report
          </CardTitle>
          {loading ? (
            <Skeleton className="aspect-[8.5/11] w-full mt-3 rounded-xl" />
          ) : latest ? (
            <>
              <p className="text-[15px] font-semibold text-foreground mt-1">
                {latest.title} — {latest.area}
              </p>
              <p className="text-[13px] text-muted-foreground">
                {formatRelativeTime(latest.timestamp)}
              </p>
              {/* Design constraint #2: the embedded report is a fixed
                  816x1056 page, SCALED — never reflowed. A responsive
                  re-layout is a different document from the PDF the client
                  receives. */}
              {/* IT WAS A SCALE ARTEFACT, NOT A LAYOUT ONE.
                  SharedPDFPreview is `maxWidth: 480` with its own 8.5/11
                  aspect, and `scale` is a CSS transform applied ON TOP of
                  that — so scale={0.27} rendered the page at 84.6px inside a
                  315px box and the rest was air. Measured, not eyeballed.
                  At its natural size it fills the column and keeps the fixed
                  page proportion, which is constraint #2: scaled, never
                  reflowed. */}
              <div className="mt-3 overflow-hidden rounded-xl">
                <SharedPDFPreview
                  primaryColor={branding.primary_color ?? '#4F46E5'}
                  accentColor={branding.accent_color ?? '#818CF8'}
                  headerLogoUrl={branding.logo_url ?? null}
                  displayName={branding.display_name ?? null}
                  agentName={me.first_name ? `${me.first_name} ${me.last_name ?? ''}`.trim() : (me.email ?? '')}
                  agentTitle={me.title ?? null}
                  agentPhone={me.phone ?? null}
                  agentEmail={me.email ?? ''}
                  agentPhotoUrl={me.avatar_url ?? null}
                  reportType={(latest.rawType ?? 'market_snapshot') as PreviewReportType}
                  audienceLabel={null}
                  areaName={latest.area}
                  lookbackDays={180}
                />
              </div>
              <Link href="/app/reports" prefetch={false}
                    className="text-[13px] font-semibold text-[var(--link)] hover:text-[var(--link-hover)] mt-3 inline-block">
                All reports →
              </Link>
            </>
          ) : (
            <>
              <p className="text-[15px] text-muted-foreground mt-1">Nothing sent yet</p>
              <Button asChild className="mt-3">
                <Link href="/app/reports/new" prefetch={false}>
                  <Plus className="w-4 h-4 mr-1.5" />
                  Your first report
                </Link>
              </Button>
            </>
          )}
        </Card>

        {/* Next send + Call these first */}
        <div className="lg:col-span-2 space-y-5">

          <Card className="gap-2">
            <CardTitle className="text-[11px] font-bold uppercase tracking-[0.08em] text-muted-foreground">
              Next send
            </CardTitle>
            {loading ? (
              <Skeleton className="h-6 w-2/3 mt-2" />
            ) : nextSend ? (
              <p className="text-[15px] text-foreground mt-1">
                <span className="font-semibold">{nextSend.name}</span>
                {' goes out '}
                {new Date(nextSend.next_run_at).toLocaleDateString(undefined,
                  { month: 'long', day: 'numeric' })}
                {Array.isArray(nextSend.recipients) && nextSend.recipients.length > 0
                  ? ` to ${nextSend.recipients.length} recipient${nextSend.recipients.length === 1 ? '' : 's'}`
                  : ''}
              </p>
            ) : (
              /* Design #4: "Nothing scheduled", never 0 as a fake value. */
              <p className="text-[15px] text-muted-foreground mt-1">Nothing scheduled</p>
            )}
            <Link href="/app/schedules" prefetch={false}
                  className="text-[13px] font-semibold text-[var(--link)] hover:text-[var(--link-hover)] mt-2 inline-block">
              Schedules →
            </Link>
          </Card>

          <Card className="gap-2">
            <CardTitle className="text-[11px] font-bold uppercase tracking-[0.08em] text-muted-foreground">
              Call these first
            </CardTitle>
            {loading ? (
              <ActivityListSkeleton />
            ) : callFirst.length === 0 ? (
              <p className="text-[15px] text-muted-foreground mt-1">No new leads</p>
            ) : (
              <ul className="mt-2 divide-y divide-[var(--border-subtle)]">
                {callFirst.map((l) => (
                  <li key={l.id} className="py-3 flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-[15px] font-semibold text-foreground truncate">
                        {l.name || l.email || 'Unnamed lead'}
                      </p>
                      <p className="text-[13px] text-muted-foreground truncate">
                        {l.phone || l.email || '—'}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <StatusBadge status={l.status ?? 'new'} />
                      <span className="text-[13px] text-muted-foreground">
                        {formatRelativeTime(l.created_at)}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
            <Link href="/app/leads" prefetch={false}
                  className="text-[13px] font-semibold text-[var(--link)] hover:text-[var(--link-hover)] mt-2 inline-block">
              All leads →
            </Link>
          </Card>
        </div>
      </div>

      {/* Onboarding keeps its column below, unchanged. */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-3">
          {loading ? (
            <OnboardingSkeleton />
          ) : (
            <DashboardOnboarding initialStatus={onboarding} />
          )}
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Skeleton Components
// ─────────────────────────────────────────────────────────────────────────────

function MetricCardSkeleton() {
  return (
    <div className="bg-card border border-border rounded-xl p-4 shadow-[var(--shadow-card)]">
      <div className="flex items-center justify-between mb-3">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-8 w-8 rounded-lg" />
      </div>
      <Skeleton className="h-7 w-16 mb-1" />
    </div>
  )
}

function ActivityListSkeleton() {
  return (
    <div className="divide-y divide-border">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Skeleton className="w-8 h-8 rounded-lg" />
            <div>
              <Skeleton className="h-4 w-32 mb-1.5" />
              <Skeleton className="h-3 w-20" />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Skeleton className="h-5 w-16 rounded-full" />
            <Skeleton className="h-3 w-12" />
          </div>
        </div>
      ))}
    </div>
  )
}

function OnboardingSkeleton() {
  return (
    <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
      <div className="px-4 py-3 border-b border-border">
        <Skeleton className="h-4 w-32 mb-2" />
        <Skeleton className="h-2 w-full rounded-full" />
      </div>
      <div className="p-4 space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex items-center gap-3 p-2">
            <Skeleton className="h-5 w-5 rounded-full" />
            <Skeleton className="h-4 flex-1" />
          </div>
        ))}
      </div>
    </div>
  )
}

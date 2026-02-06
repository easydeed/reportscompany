'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle, AlertTriangle, FileText, Mail, Calendar, Clock, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { DashboardOnboarding } from "@/components/onboarding"
import { PageHeader } from "@/components/page-header"
import { MetricCard } from "@/components/metric-card"
import { StatusBadge } from "@/components/status-badge"

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

interface PlanUsageData {
  decision?: 'ALLOW' | 'ALLOW_WITH_WARNING' | 'BLOCK'
  plan?: {
    plan_name?: string
  }
  info?: {
    message?: string
  }
}

interface OnboardingData {
  is_dismissed?: boolean
  completed_steps?: string[]
  profile_completed?: boolean
  branding_completed?: boolean
  first_report_completed?: boolean
}

interface DashboardData {
  usage: UsageData | null
  planUsage: PlanUsageData | null
  onboarding: OnboardingData | null
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
  const [data, setData] = useState<DashboardData>({
    usage: null,
    planUsage: null,
    onboarding: null,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchDashboard() {
      const fetchStart = Date.now()
      console.log('[PERF] Dashboard client fetch starting...')
      
      try {
        const [usageRes, planRes, onboardingRes] = await Promise.all([
          (async () => {
            const start = Date.now()
            const res = await fetch('/api/proxy/v1/usage', { credentials: 'include' })
            console.log(`[PERF] /v1/usage: ${Date.now() - start}ms`)
            return res.ok ? res.json() : null
          })(),
          (async () => {
            const start = Date.now()
            const res = await fetch('/api/proxy/v1/account/plan-usage', { credentials: 'include' })
            console.log(`[PERF] /v1/account/plan-usage: ${Date.now() - start}ms`)
            return res.ok ? res.json() : null
          })(),
          (async () => {
            const start = Date.now()
            const res = await fetch('/api/proxy/v1/onboarding', { credentials: 'include' })
            console.log(`[PERF] /v1/onboarding: ${Date.now() - start}ms`)
            return res.ok ? res.json() : null
          })(),
        ])
        
        console.log(`[PERF] Dashboard client fetch TOTAL: ${Date.now() - fetchStart}ms`)
        
        setData({
          usage: usageRes,
          planUsage: planRes,
          onboarding: onboardingRes,
        })
      } catch (err) {
        console.error('Dashboard fetch failed:', err)
      } finally {
        setLoading(false)
      }
    }
    
    fetchDashboard()
  }, [])

  // Build recent activity from fetched data
  const recentReports = (data.usage?.recent_reports ?? []).map((r) => ({
    id: r.id,
    type: 'report' as const,
    title: `${r.type?.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}`,
    area: r.city || 'Unknown',
    status: r.status,
    timestamp: r.created_at,
    url: r.pdf_url,
  }))
  
  const recentEmails = (data.usage?.recent_emails ?? []).map((e) => ({
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

  return (
    <div className="space-y-5">
      {/* Header — renders instantly */}
      <PageHeader
        title="Overview"
        description="Your account activity and key metrics"
        action={
          <Button asChild size="sm">
            <Link href="/app/reports/new">
              <Plus className="w-4 h-4 mr-1.5" />
              New Report
            </Link>
          </Button>
        }
      />

      {/* Usage Warning Banners — only show after data loads */}
      {!loading && data.planUsage?.decision === 'ALLOW_WITH_WARNING' && (
        <Alert className="border-amber-200 bg-amber-50">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertTitle className="text-amber-800">Approaching Limit</AlertTitle>
          <AlertDescription className="flex items-center justify-between text-amber-700">
            <span>
              You're approaching your monthly report limit for the <strong>{data.planUsage.plan?.plan_name}</strong> plan. {data.planUsage.info?.message}
            </span>
            <Button asChild variant="outline" size="sm" className="ml-4 border-amber-600 text-amber-700 hover:bg-amber-100">
              <Link href="/app/settings/billing">View Plan</Link>
            </Button>
          </AlertDescription>
        </Alert>
      )}
      
      {!loading && data.planUsage?.decision === 'BLOCK' && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertTitle className="text-red-800">Monthly Limit Reached</AlertTitle>
          <AlertDescription className="flex items-center justify-between text-red-700">
            <span>
              You've reached your monthly report limit. New reports are blocked until the period resets.
            </span>
            <Button asChild variant="outline" size="sm" className="ml-4 border-red-600 text-red-700 hover:bg-red-100">
              <Link href="/app/settings/billing">Upgrade Plan</Link>
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Metric Cards — show skeletons while loading */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {loading ? (
          <>
            <MetricCardSkeleton />
            <MetricCardSkeleton />
            <MetricCardSkeleton />
            <MetricCardSkeleton />
          </>
        ) : (
          <>
            <MetricCard 
              label="Reports" 
              value={data.usage?.summary?.total_reports ?? 0} 
              icon={<FileText className="w-4 h-4" />} 
              index={0} 
            />
            <MetricCard 
              label="Emails Sent" 
              value={data.usage?.recent_emails?.length ?? 0} 
              icon={<Mail className="w-4 h-4" />} 
              index={1} 
            />
            <MetricCard 
              label="Active Schedules" 
              value={data.usage?.limits?.active_schedules ?? 0} 
              icon={<Calendar className="w-4 h-4" />} 
              index={2} 
            />
            <MetricCard 
              label="Avg. Render" 
              value={data.usage?.summary?.avg_ms ? `${Math.round(data.usage.summary.avg_ms)}ms` : '—'} 
              icon={<Clock className="w-4 h-4" />} 
              index={3} 
            />
          </>
        )}
      </div>

      {/* Two-column layout: Recent Activity + Onboarding */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Recent Activity - takes 2 cols */}
        <div className="lg:col-span-2 bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
          <div className="px-4 py-3 border-b border-border flex items-center justify-between">
            <h3 className="text-[13px] font-semibold text-foreground">Recent Activity</h3>
            <Link href="/app/reports" className="text-xs text-primary hover:text-primary/80 font-medium">
              View all →
            </Link>
          </div>
          
          {loading ? (
            <ActivityListSkeleton />
          ) : recentActivity.length === 0 ? (
            <div className="p-8 text-center">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                <FileText className="w-6 h-6 text-primary" />
              </div>
              <h4 className="text-sm font-medium text-foreground mb-1">No recent activity</h4>
              <p className="text-xs text-muted-foreground mb-4">
                Create your first report to get started
              </p>
              <Button size="sm" asChild>
                <Link href="/app/reports/new">
                  <Plus className="w-3.5 h-3.5 mr-1.5" />
                  Create Report
                </Link>
              </Button>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {recentActivity.map((item) => (
                <div 
                  key={`${item.type}-${item.id}`}
                  className="px-4 py-3 hover:bg-muted/30 transition-colors flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      item.type === 'report' ? 'bg-primary/10 text-primary' : 'bg-blue-50 text-blue-600'
                    }`}>
                      {item.type === 'report' ? (
                        <FileText className="w-4 h-4" />
                      ) : (
                        <Mail className="w-4 h-4" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-foreground">{item.title}</p>
                      <p className="text-xs text-muted-foreground">{item.area}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge status={item.status} />
                    <span className="text-xs text-muted-foreground">
                      {formatRelativeTime(item.timestamp)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Onboarding Checklist - takes 1 col */}
        <div className="lg:col-span-1">
          {loading ? (
            <OnboardingSkeleton />
          ) : (
            <DashboardOnboarding initialStatus={data.onboarding} />
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

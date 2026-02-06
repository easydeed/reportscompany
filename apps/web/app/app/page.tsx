import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle, AlertTriangle, FileText, Mail, Calendar, Clock, Plus } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { redirect } from 'next/navigation'
import { DashboardOnboarding } from "@/components/onboarding"
import { createServerApi } from "@/lib/api-server"
import { PageHeader } from "@/components/page-header"
import { MetricCard } from "@/components/metric-card"
import { StatusBadge } from "@/components/status-badge"

export const dynamic = 'force-dynamic'

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

export default async function Overview() {
  const api = await createServerApi()
  
  if (!api.isAuthenticated()) {
    redirect('/login')
  }

  // Fetch ALL data in parallel using the shared API utility
  const [meRes, dataRes, planUsageRes, onboardingRes] = await Promise.all([
    api.get<any>("/v1/me"),
    api.get<any>("/v1/usage"),
    api.get<any>("/v1/account/plan-usage"),
    api.get<any>("/v1/onboarding"),
  ])

  const me = meRes.data
  const data = dataRes.data
  const planUsage = planUsageRes.data
  const onboardingStatus = onboardingRes.data
  
  // Check if affiliate and redirect
  if (me?.account_type === "INDUSTRY_AFFILIATE") {
    redirect("/app/affiliate")
  }

  // Combine recent reports and emails into a single feed
  const recentReports = (data?.recent_reports ?? []).map((r: any) => ({
    id: r.id,
    type: 'report' as const,
    title: `${r.type?.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}`,
    area: r.city || 'Unknown',
    status: r.status,
    timestamp: r.created_at,
    url: r.pdf_url,
  }))
  
  const recentEmails = (data?.recent_emails ?? []).map((e: any) => ({
    id: e.id,
    type: 'email' as const,
    title: e.subject || 'Email sent',
    area: e.to || '',
    status: e.status,
    timestamp: e.created_at,
  }))
  
  // Merge and sort by timestamp
  const recentActivity = [...recentReports, ...recentEmails]
    .sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''))
    .slice(0, 8)

  return (
    <div className="space-y-6">
      {/* Header */}
      <PageHeader
        title="Overview"
        description="Your account activity and key metrics"
        action={
          <Button asChild>
            <Link href="/app/reports/new">
              <Plus className="w-4 h-4 mr-2" />
              New Report
            </Link>
          </Button>
        }
      />

      {/* Usage Warning Banners */}
      {planUsage && planUsage.decision === 'ALLOW_WITH_WARNING' && (
        <Alert className="border-amber-200 bg-amber-50">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertTitle className="text-amber-800">Approaching Limit</AlertTitle>
          <AlertDescription className="flex items-center justify-between text-amber-700">
            <span>
              You're approaching your monthly report limit for the <strong>{planUsage.plan.plan_name}</strong> plan. {planUsage.info.message}
            </span>
            <Button asChild variant="outline" size="sm" className="ml-4 border-amber-600 text-amber-700 hover:bg-amber-100">
              <Link href="/app/settings/billing">View Plan</Link>
            </Button>
          </AlertDescription>
        </Alert>
      )}
      
      {planUsage && planUsage.decision === 'BLOCK' && (
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

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Reports"
          value={data?.summary?.total_reports ?? 0}
          icon={<FileText className="w-4 h-4" />}
          index={0}
        />
        <MetricCard
          label="Emails Sent"
          value={data?.recent_emails?.length ?? 0}
          icon={<Mail className="w-4 h-4" />}
          index={1}
        />
        <MetricCard
          label="Active Schedules"
          value={data?.limits?.active_schedules ?? 0}
          icon={<Calendar className="w-4 h-4" />}
          index={2}
        />
        <MetricCard
          label="Avg. Render Time"
          value={data?.summary?.avg_ms ? `${Math.round(data.summary.avg_ms)}ms` : '0ms'}
          icon={<Clock className="w-4 h-4" />}
          index={3}
        />
      </div>

      {/* Two-column layout: Recent Activity + Onboarding */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity - takes 2 cols */}
        <div className="lg:col-span-2 bg-card border border-border rounded-xl shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-border flex items-center justify-between">
            <h3 className="text-sm font-medium text-foreground">Recent Activity</h3>
            <Link href="/app/reports" className="text-xs text-primary hover:underline">
              View all
            </Link>
          </div>
          {recentActivity.length === 0 ? (
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
          <DashboardOnboarding initialStatus={onboardingStatus} />
        </div>
      </div>
    </div>
  )
}

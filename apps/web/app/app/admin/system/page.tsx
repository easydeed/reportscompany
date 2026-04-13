"use client"

import { useState, useEffect, useCallback } from "react"
import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  ArrowLeft,
  Database,
  Server,
  Mail,
  ExternalLink,
  Activity,
  HardDrive,
  RefreshCw,
  Loader2,
  AlertTriangle,
  CheckCircle,
  Clock,
  CreditCard,
  Cloud,
  FileText,
  Phone,
  Globe,
  XCircle,
} from "lucide-react"

interface SystemHealth {
  timestamp: string
  database: {
    status: string
    size_mb?: number
    users?: number
    accounts?: number
    reports_24h?: number
    active_schedules?: number
    recent_failures?: number
    error?: string
  }
  redis: {
    status: string
    queue_depth?: number
    error?: string
    message?: string
  }
  worker: {
    status: string
    recent_completed_10m?: number
    currently_processing?: number
    pending?: number
    error?: string
  }
  system: {
    environment?: string
    api_base?: string
  }
}

const INTEGRATIONS = [
  { name: "PostgreSQL", provider: "Render", icon: Database, color: "text-blue-500", bg: "bg-blue-600", abbr: "PG", live: "database" as const, url: "https://dashboard.render.com" },
  { name: "Redis", provider: "Upstash", icon: HardDrive, color: "text-red-500", bg: "bg-red-600", abbr: "RD", live: "redis" as const, url: "https://console.upstash.com" },
  { name: "SendGrid", provider: "Twilio SendGrid", icon: Mail, color: "text-emerald-500", bg: "bg-emerald-600", abbr: "SG", configured: true, url: "https://app.sendgrid.com" },
  { name: "Cloudflare R2", provider: "PDF & Asset Storage", icon: Cloud, color: "text-orange-500", bg: "bg-orange-600", abbr: "R2", configured: true, url: "https://dash.cloudflare.com" },
  { name: "Stripe", provider: "Payment Processing", icon: CreditCard, color: "text-indigo-500", bg: "bg-indigo-600", abbr: "ST", configured: true, url: "https://dashboard.stripe.com" },
  { name: "PDFShift", provider: "HTML → PDF Conversion", icon: FileText, color: "text-violet-500", bg: "bg-violet-600", abbr: "PS", configured: true, url: "https://pdfshift.io/dashboard" },
  { name: "SimplyRETS", provider: "MLS Data Provider", icon: Globe, color: "text-cyan-500", bg: "bg-cyan-600", abbr: "SR", configured: true, url: "https://simplyrets.com" },
  { name: "SiteX", provider: "IDX / Website Hosting", icon: Globe, color: "text-pink-500", bg: "bg-pink-600", abbr: "SX", configured: true, url: null },
  { name: "Twilio", provider: "SMS (Optional)", icon: Phone, color: "text-red-500", bg: "bg-red-500", abbr: "TW", configured: false, url: "https://console.twilio.com" },
]

const QUICK_LINKS = [
  { name: "Vercel Dashboard", description: "Frontend hosting", url: "https://vercel.com" },
  { name: "Render Dashboard", description: "API + Worker hosting", url: "https://dashboard.render.com" },
  { name: "SendGrid Dashboard", description: "Email delivery", url: "https://app.sendgrid.com" },
  { name: "Stripe Dashboard", description: "Payments & billing", url: "https://dashboard.stripe.com" },
  { name: "Cloudflare R2 Console", description: "Object storage", url: "https://dash.cloudflare.com" },
]

function StatusBadge({ status }: { status: string }) {
  switch (status) {
    case "healthy":
    case "active":
      return (
        <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50">
          <CheckCircle className="h-3 w-3 mr-1" />Healthy
        </Badge>
      )
    case "idle":
      return (
        <Badge variant="outline" className="text-blue-600 border-blue-200 bg-blue-50">
          <Clock className="h-3 w-3 mr-1" />Idle
        </Badge>
      )
    case "idle_with_pending":
      return (
        <Badge variant="outline" className="text-amber-600 border-amber-200 bg-amber-50">
          <AlertTriangle className="h-3 w-3 mr-1" />Pending
        </Badge>
      )
    case "unhealthy":
      return (
        <Badge variant="outline" className="text-red-600 border-red-200 bg-red-50">
          <XCircle className="h-3 w-3 mr-1" />Unhealthy
        </Badge>
      )
    default:
      return <Badge variant="secondary">Unknown</Badge>
  }
}

export default function AdminSystemPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const fetchHealth = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    try {
      const res = await fetch("/api/proxy/v1/admin/system/health", { credentials: "include" })
      if (res.ok) {
        const data = await res.json()
        setHealth(data)
      }
    } catch (err) {
      console.error("Failed to fetch health:", err)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    fetchHealth()
    const interval = setInterval(() => fetchHealth(), 30_000)
    return () => clearInterval(interval)
  }, [fetchHealth])

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded" />
          <div>
            <Skeleton className="h-9 w-48 mb-2" />
            <Skeleton className="h-5 w-72" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}><CardContent className="pt-6"><Skeleton className="h-24 w-full" /></CardContent></Card>
          ))}
        </div>
        <Card>
          <CardContent className="pt-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="py-3 flex gap-4">
                <Skeleton className="h-10 w-10 rounded-lg" />
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-5 w-20 rounded-full ml-auto" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/app/admin">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-display font-bold text-foreground">System Health</h1>
            <p className="text-muted-foreground mt-1">
              Live service status, integrations, and infrastructure
            </p>
          </div>
        </div>
        <Button variant="outline" onClick={() => fetchHealth(true)} disabled={refreshing}>
          {refreshing ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4 mr-2" />
          )}
          Refresh
        </Button>
      </div>

      {/* Live Health Cards */}
      {health && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-indigo-500" />
                Live System Health
              </CardTitle>
              <span className="text-xs text-muted-foreground">
                Last checked: {new Date(health.timestamp).toLocaleString()}
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Database */}
              <Card className="bg-muted/40">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Database className="h-5 w-5 text-blue-500" />
                      <span className="font-medium text-foreground">Database</span>
                    </div>
                    <StatusBadge status={health.database.status} />
                  </div>
                  <div className="space-y-2 text-sm">
                    {health.database.size_mb != null && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Size</span>
                        <span className="text-foreground">{health.database.size_mb} MB</span>
                      </div>
                    )}
                    {health.database.users != null && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Users</span>
                        <span className="text-foreground">{health.database.users}</span>
                      </div>
                    )}
                    {health.database.accounts != null && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Accounts</span>
                        <span className="text-foreground">{health.database.accounts}</span>
                      </div>
                    )}
                    {health.database.reports_24h != null && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Reports (24h)</span>
                        <span className="text-foreground">{health.database.reports_24h}</span>
                      </div>
                    )}
                    {health.database.active_schedules != null && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Active Schedules</span>
                        <span className="text-foreground">{health.database.active_schedules}</span>
                      </div>
                    )}
                    {(health.database.recent_failures ?? 0) > 0 && (
                      <div className="flex justify-between">
                        <span className="text-red-500">Failures (1h)</span>
                        <span className="text-red-600 font-medium">{health.database.recent_failures}</span>
                      </div>
                    )}
                    {health.database.error && (
                      <p className="text-red-500 text-xs mt-1">{health.database.error}</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Redis */}
              <Card className="bg-muted/40">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <HardDrive className="h-5 w-5 text-red-500" />
                      <span className="font-medium text-foreground">Redis Queue</span>
                    </div>
                    <StatusBadge status={health.redis.status} />
                  </div>
                  <div className="space-y-2 text-sm">
                    {health.redis.queue_depth != null && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Queue Depth</span>
                        <span className={`font-medium ${health.redis.queue_depth > 10 ? "text-amber-600" : "text-foreground"}`}>
                          {health.redis.queue_depth}
                        </span>
                      </div>
                    )}
                    {health.redis.message && (
                      <p className="text-xs text-muted-foreground">{health.redis.message}</p>
                    )}
                    {health.redis.error && (
                      <p className="text-red-500 text-xs">{health.redis.error}</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Worker */}
              <Card className="bg-muted/40">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Server className="h-5 w-5 text-emerald-500" />
                      <span className="font-medium text-foreground">Worker</span>
                    </div>
                    <StatusBadge status={health.worker.status} />
                  </div>
                  <div className="space-y-2 text-sm">
                    {health.worker.currently_processing != null && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Processing</span>
                        <span className="text-blue-600 font-medium">{health.worker.currently_processing}</span>
                      </div>
                    )}
                    {health.worker.pending != null && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Pending</span>
                        <span className={`font-medium ${health.worker.pending > 5 ? "text-amber-600" : "text-foreground"}`}>
                          {health.worker.pending}
                        </span>
                      </div>
                    )}
                    {health.worker.recent_completed_10m != null && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Completed (10m)</span>
                        <span className="text-emerald-600 font-medium">{health.worker.recent_completed_10m}</span>
                      </div>
                    )}
                    {health.worker.error && (
                      <p className="text-red-500 text-xs mt-1">{health.worker.error}</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Integration Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            Integrations
          </CardTitle>
          <CardDescription>Connected services and their current status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {INTEGRATIONS.map((svc) => {
              const isLive = "live" in svc && svc.live
              let liveStatus: string | undefined
              if (isLive && health) {
                liveStatus = health[svc.live as keyof Pick<SystemHealth, "database" | "redis">]?.status
              }
              const isHealthy = isLive
                ? liveStatus === "healthy" || liveStatus === "active"
                : svc.configured

              return (
                <div
                  key={svc.name}
                  className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-muted/40 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-9 h-9 ${svc.bg} rounded-lg flex items-center justify-center`}>
                      <span className="text-white font-bold text-xs">{svc.abbr}</span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-foreground">{svc.name}</p>
                      <p className="text-xs text-muted-foreground">{svc.provider}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {isHealthy ? (
                      <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50">
                        {isLive ? "Connected" : "Configured"}
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-amber-600 border-amber-200 bg-amber-50">
                        {isLive ? "Down" : "Not Configured"}
                      </Badge>
                    )}
                    {svc.url && (
                      <a href={svc.url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
                        <ExternalLink className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground transition-colors" />
                      </a>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Quick Links */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Links</CardTitle>
          <CardDescription>External dashboards and management consoles</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {QUICK_LINKS.map((link) => (
              <a
                key={link.name}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-muted/40 transition-colors group"
              >
                <div>
                  <p className="text-sm font-medium text-foreground">{link.name}</p>
                  <p className="text-xs text-muted-foreground">{link.description}</p>
                </div>
                <ExternalLink className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors shrink-0 ml-2" />
              </a>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Environment Info */}
      {health?.system && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Environment</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4 text-sm">
              {health.system.environment && (
                <div>
                  <span className="text-muted-foreground mr-2">Environment:</span>
                  <Badge variant="outline">{health.system.environment}</Badge>
                </div>
              )}
              {health.system.api_base && (
                <div>
                  <span className="text-muted-foreground mr-2">API Base:</span>
                  <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">{health.system.api_base}</code>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

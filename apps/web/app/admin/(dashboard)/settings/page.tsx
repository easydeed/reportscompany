"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
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

export default function SettingsPage() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<any>(null)
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [healthLoading, setHealthLoading] = useState(false)

  useEffect(() => {
    fetchStats()
    fetchHealth()
  }, [])

  async function fetchStats() {
    try {
      const res = await fetch("/api/v1/admin/stats/revenue", { credentials: "include" })
      if (res.ok) {
        const data = await res.json()
        setStats(data)
      }
    } catch (error) {
      console.error("Failed to fetch stats:", error)
    } finally {
      setLoading(false)
    }
  }

  async function fetchHealth() {
    setHealthLoading(true)
    try {
      const res = await fetch("/api/v1/admin/system/health", { credentials: "include" })
      if (res.ok) {
        const data = await res.json()
        setHealth(data)
      }
    } catch (error) {
      console.error("Failed to fetch health:", error)
    } finally {
      setHealthLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "healthy":
      case "active":
        return <Badge className="bg-emerald-100 text-emerald-700"><CheckCircle className="h-3 w-3 mr-1" />Healthy</Badge>
      case "idle":
        return <Badge className="bg-blue-100 text-blue-700"><Clock className="h-3 w-3 mr-1" />Idle</Badge>
      case "idle_with_pending":
        return <Badge className="bg-amber-100 text-amber-700"><AlertTriangle className="h-3 w-3 mr-1" />Pending</Badge>
      case "unhealthy":
        return <Badge className="bg-red-100 text-red-700"><AlertTriangle className="h-3 w-3 mr-1" />Unhealthy</Badge>
      default:
        return <Badge className="bg-slate-100 text-slate-600">Unknown</Badge>
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Settings</h1>
          <p className="text-slate-500 mt-1">System configuration and integrations</p>
        </div>
        <Button
          variant="outline"
          onClick={fetchHealth}
          disabled={healthLoading}
          className="border-slate-300 text-slate-600 hover:bg-slate-50"
        >
          {healthLoading ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4 mr-2" />
          )}
          Refresh Health
        </Button>
      </div>

      {/* Live System Health */}
      {health && (
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="text-slate-900 flex items-center gap-2">
              <Activity className="h-5 w-5 text-violet-500" />
              Live System Health
            </CardTitle>
            <CardDescription className="text-slate-500">
              Last checked: {new Date(health.timestamp).toLocaleString()}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Database */}
              <Card className="bg-slate-50 border-slate-200">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Database className="h-5 w-5 text-blue-500" />
                      <span className="font-medium text-slate-900">Database</span>
                    </div>
                    {getStatusBadge(health.database.status)}
                  </div>
                  <div className="space-y-2 text-sm">
                    {health.database.size_mb && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Size</span>
                        <span className="text-slate-700">{health.database.size_mb} MB</span>
                      </div>
                    )}
                    {health.database.users !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Users</span>
                        <span className="text-slate-700">{health.database.users}</span>
                      </div>
                    )}
                    {health.database.accounts !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Accounts</span>
                        <span className="text-slate-700">{health.database.accounts}</span>
                      </div>
                    )}
                    {health.database.recent_failures !== undefined && health.database.recent_failures > 0 && (
                      <div className="flex justify-between">
                        <span className="text-red-500">Failures (1h)</span>
                        <span className="text-red-600 font-medium">{health.database.recent_failures}</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Redis / Queue */}
              <Card className="bg-slate-50 border-slate-200">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <HardDrive className="h-5 w-5 text-red-500" />
                      <span className="font-medium text-slate-900">Redis Queue</span>
                    </div>
                    {getStatusBadge(health.redis.status)}
                  </div>
                  <div className="space-y-2 text-sm">
                    {health.redis.queue_depth !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Queue Depth</span>
                        <span className={`font-medium ${health.redis.queue_depth > 10 ? 'text-amber-600' : 'text-slate-700'}`}>
                          {health.redis.queue_depth}
                        </span>
                      </div>
                    )}
                    {health.redis.message && (
                      <p className="text-slate-400 text-xs">{health.redis.message}</p>
                    )}
                    {health.redis.error && (
                      <p className="text-red-500 text-xs">{health.redis.error}</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Worker */}
              <Card className="bg-slate-50 border-slate-200">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Server className="h-5 w-5 text-emerald-500" />
                      <span className="font-medium text-slate-900">Worker</span>
                    </div>
                    {getStatusBadge(health.worker.status)}
                  </div>
                  <div className="space-y-2 text-sm">
                    {health.worker.currently_processing !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Processing</span>
                        <span className="text-blue-600 font-medium">{health.worker.currently_processing}</span>
                      </div>
                    )}
                    {health.worker.pending !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Pending</span>
                        <span className={`font-medium ${health.worker.pending > 5 ? 'text-amber-600' : 'text-slate-700'}`}>
                          {health.worker.pending}
                        </span>
                      </div>
                    )}
                    {health.worker.recent_completed_10m !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Completed (10m)</span>
                        <span className="text-emerald-600 font-medium">{health.worker.recent_completed_10m}</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Static System Status */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-slate-900 flex items-center gap-2">
            <Server className="h-5 w-5 text-slate-500" />
            Infrastructure
          </CardTitle>
          <CardDescription className="text-slate-500">Connected services and providers</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center gap-3">
                <Database className="h-5 w-5 text-emerald-500" />
                <div>
                  <p className="text-slate-900 font-medium">Database</p>
                  <p className="text-xs text-slate-400">PostgreSQL on Render</p>
                </div>
              </div>
              <Badge className="bg-emerald-100 text-emerald-700">Connected</Badge>
            </div>
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center gap-3">
                <Server className="h-5 w-5 text-emerald-500" />
                <div>
                  <p className="text-slate-900 font-medium">API Server</p>
                  <p className="text-xs text-slate-400">FastAPI on Render</p>
                </div>
              </div>
              <Badge className="bg-emerald-100 text-emerald-700">Online</Badge>
            </div>
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center gap-3">
                <Mail className="h-5 w-5 text-emerald-500" />
                <div>
                  <p className="text-slate-900 font-medium">Email Service</p>
                  <p className="text-xs text-slate-400">SendGrid</p>
                </div>
              </div>
              <Badge className="bg-emerald-100 text-emerald-700">Active</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Platform Stats */}
      {stats && (
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="text-slate-900">Platform Statistics</CardTitle>
            <CardDescription className="text-slate-500">Account distribution and growth metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Accounts by Plan */}
              <div>
                <h4 className="text-sm font-medium text-slate-500 mb-3">Accounts by Plan</h4>
                <div className="space-y-2">
                  {stats.accounts_by_plan?.map((item: any) => (
                    <div key={item.plan} className="flex items-center justify-between p-2 bg-slate-50 rounded border border-slate-200">
                      <span className="text-slate-700 capitalize">{item.plan || "None"}</span>
                      <Badge variant="outline" className="border-slate-300 text-slate-600">{item.count}</Badge>
                    </div>
                  ))}
                </div>
              </div>

              {/* Growth */}
              <div>
                <h4 className="text-sm font-medium text-slate-500 mb-3">Monthly Growth (Last 6 months)</h4>
                <div className="space-y-2">
                  {stats.growth?.map((item: any) => (
                    <div key={item.month} className="flex items-center justify-between p-2 bg-slate-50 rounded border border-slate-200">
                      <span className="text-slate-700">{item.month}</span>
                      <Badge className="bg-violet-100 text-violet-700">+{item.new_accounts} accounts</Badge>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Integrations */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-slate-900">Integrations</CardTitle>
          <CardDescription className="text-slate-500">Connected services and API keys</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-violet-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">SR</span>
                </div>
                <div>
                  <p className="text-slate-900 font-medium">SimplyRETS</p>
                  <p className="text-xs text-slate-400">MLS Data Provider</p>
                </div>
              </div>
              <Badge className="bg-emerald-100 text-emerald-700">Connected</Badge>
            </div>

            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">R2</span>
                </div>
                <div>
                  <p className="text-slate-900 font-medium">Cloudflare R2</p>
                  <p className="text-xs text-slate-400">PDF & Asset Storage</p>
                </div>
              </div>
              <Badge className="bg-emerald-100 text-emerald-700">Connected</Badge>
            </div>

            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-emerald-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">SG</span>
                </div>
                <div>
                  <p className="text-slate-900 font-medium">SendGrid</p>
                  <p className="text-xs text-slate-400">Transactional Email</p>
                </div>
              </div>
              <Badge className="bg-emerald-100 text-emerald-700">Connected</Badge>
            </div>

            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">ST</span>
                </div>
                <div>
                  <p className="text-slate-900 font-medium">Stripe</p>
                  <p className="text-xs text-slate-400">Payment Processing</p>
                </div>
              </div>
              <Badge variant="outline" className="border-amber-300 text-amber-700 bg-amber-50">Configure</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Links */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-slate-900">Quick Links</CardTitle>
          <CardDescription className="text-slate-500">External dashboards and tools</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <a
              href="https://vercel.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200 hover:bg-slate-100 transition-colors"
            >
              <span className="text-slate-700">Vercel Dashboard</span>
              <ExternalLink className="h-4 w-4 text-slate-400" />
            </a>
            <a
              href="https://render.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200 hover:bg-slate-100 transition-colors"
            >
              <span className="text-slate-700">Render Dashboard</span>
              <ExternalLink className="h-4 w-4 text-slate-400" />
            </a>
            <a
              href="https://app.sendgrid.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200 hover:bg-slate-100 transition-colors"
            >
              <span className="text-slate-700">SendGrid Dashboard</span>
              <ExternalLink className="h-4 w-4 text-slate-400" />
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

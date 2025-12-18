"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Database,
  Server,
  Mail,
  ExternalLink,
} from "lucide-react"

export default function SettingsPage() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<any>(null)

  useEffect(() => {
    fetchStats()
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

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Settings</h1>
        <p className="text-slate-500 mt-1">System configuration and integrations</p>
      </div>

      {/* System Status */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-slate-900 flex items-center gap-2">
            <Server className="h-5 w-5 text-slate-500" />
            System Status
          </CardTitle>
          <CardDescription className="text-slate-500">Current system health and connectivity</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center gap-3">
                <Database className="h-5 w-5 text-emerald-500" />
                <div>
                  <p className="text-slate-900 font-medium">Database</p>
                  <p className="text-xs text-slate-400">PostgreSQL</p>
                </div>
              </div>
              <Badge className="bg-emerald-100 text-emerald-700">Connected</Badge>
            </div>
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center gap-3">
                <Server className="h-5 w-5 text-emerald-500" />
                <div>
                  <p className="text-slate-900 font-medium">API Server</p>
                  <p className="text-xs text-slate-400">FastAPI</p>
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

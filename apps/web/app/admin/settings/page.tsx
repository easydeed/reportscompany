"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import {
  Settings,
  Database,
  Server,
  Mail,
  Shield,
  Save,
  Loader2,
  CheckCircle,
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
        <h1 className="text-3xl font-bold text-white">Settings</h1>
        <p className="text-gray-400 mt-1">System configuration and integrations</p>
      </div>

      {/* System Status */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Server className="h-5 w-5" />
            System Status
          </CardTitle>
          <CardDescription className="text-gray-400">Current system health and connectivity</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
              <div className="flex items-center gap-3">
                <Database className="h-5 w-5 text-green-400" />
                <div>
                  <p className="text-white font-medium">Database</p>
                  <p className="text-xs text-gray-500">PostgreSQL</p>
                </div>
              </div>
              <Badge className="bg-green-500/20 text-green-400">Connected</Badge>
            </div>
            <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
              <div className="flex items-center gap-3">
                <Server className="h-5 w-5 text-green-400" />
                <div>
                  <p className="text-white font-medium">API Server</p>
                  <p className="text-xs text-gray-500">FastAPI</p>
                </div>
              </div>
              <Badge className="bg-green-500/20 text-green-400">Online</Badge>
            </div>
            <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
              <div className="flex items-center gap-3">
                <Mail className="h-5 w-5 text-green-400" />
                <div>
                  <p className="text-white font-medium">Email Service</p>
                  <p className="text-xs text-gray-500">Resend</p>
                </div>
              </div>
              <Badge className="bg-green-500/20 text-green-400">Active</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Platform Stats */}
      {stats && (
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-white">Platform Statistics</CardTitle>
            <CardDescription className="text-gray-400">Account distribution and growth metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Accounts by Plan */}
              <div>
                <h4 className="text-sm font-medium text-gray-400 mb-3">Accounts by Plan</h4>
                <div className="space-y-2">
                  {stats.accounts_by_plan?.map((item: any) => (
                    <div key={item.plan} className="flex items-center justify-between p-2 bg-gray-800/50 rounded">
                      <span className="text-gray-300 capitalize">{item.plan || "None"}</span>
                      <Badge variant="outline" className="border-gray-700 text-gray-400">{item.count}</Badge>
                    </div>
                  ))}
                </div>
              </div>

              {/* Growth */}
              <div>
                <h4 className="text-sm font-medium text-gray-400 mb-3">Monthly Growth (Last 6 months)</h4>
                <div className="space-y-2">
                  {stats.growth?.map((item: any) => (
                    <div key={item.month} className="flex items-center justify-between p-2 bg-gray-800/50 rounded">
                      <span className="text-gray-300">{item.month}</span>
                      <Badge className="bg-violet-500/20 text-violet-400">+{item.new_accounts} accounts</Badge>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Integrations */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white">Integrations</CardTitle>
          <CardDescription className="text-gray-400">Connected services and API keys</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-violet-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">SR</span>
                </div>
                <div>
                  <p className="text-white font-medium">SimplyRETS</p>
                  <p className="text-xs text-gray-500">MLS Data Provider</p>
                </div>
              </div>
              <Badge className="bg-green-500/20 text-green-400">Connected</Badge>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">R2</span>
                </div>
                <div>
                  <p className="text-white font-medium">Cloudflare R2</p>
                  <p className="text-xs text-gray-500">PDF & Asset Storage</p>
                </div>
              </div>
              <Badge className="bg-green-500/20 text-green-400">Connected</Badge>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">RS</span>
                </div>
                <div>
                  <p className="text-white font-medium">Resend</p>
                  <p className="text-xs text-gray-500">Transactional Email</p>
                </div>
              </div>
              <Badge className="bg-green-500/20 text-green-400">Connected</Badge>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">ST</span>
                </div>
                <div>
                  <p className="text-white font-medium">Stripe</p>
                  <p className="text-xs text-gray-500">Payment Processing</p>
                </div>
              </div>
              <Badge variant="outline" className="border-yellow-500/50 text-yellow-400">Configure</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Links */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white">Quick Links</CardTitle>
          <CardDescription className="text-gray-400">External dashboards and tools</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <a
              href="https://vercel.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg hover:bg-gray-800 transition-colors"
            >
              <span className="text-gray-300">Vercel Dashboard</span>
              <ExternalLink className="h-4 w-4 text-gray-500" />
            </a>
            <a
              href="https://render.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg hover:bg-gray-800 transition-colors"
            >
              <span className="text-gray-300">Render Dashboard</span>
              <ExternalLink className="h-4 w-4 text-gray-500" />
            </a>
            <a
              href="https://resend.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg hover:bg-gray-800 transition-colors"
            >
              <span className="text-gray-300">Resend Dashboard</span>
              <ExternalLink className="h-4 w-4 text-gray-500" />
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

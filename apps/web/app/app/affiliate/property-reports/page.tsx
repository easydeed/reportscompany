'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Home,
  Users,
  Eye,
  UserPlus,
  TrendingUp,
  Trophy,
  AlertCircle,
  RefreshCw,
  Target,
  BarChart3,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'

interface AffiliateStats {
  period: { from: string; to: string }
  summary: {
    total_agents: number
    active_agents: number
    inactive_agents: number
  }
  aggregate: {
    total_reports: number
    completed: number
    failed: number
    total_views: number
    unique_visitors: number
    total_leads: number
    leads_from_qr: number
    leads_from_direct: number
    leads_converted: number
    conversion_rate: number
  }
  themes: {
    classic: number
    modern: number
    elegant: number
    teal: number
    bold: number
  }
  leaderboard: {
    account_id: string
    name: string
    email: string
    avatar: string | null
    reports: number
    views: number
    leads: number
    last_activity: string | null
  }[]
  inactive_agents: {
    account_id: string
    name: string
    email: string
    last_report: string
  }[]
}

// Theme colors for badges
const THEME_COLORS: Record<string, string> = {
  classic: 'bg-slate-100 text-slate-700 border-slate-300',
  modern: 'bg-blue-100 text-blue-700 border-blue-300',
  elegant: 'bg-indigo-100 text-indigo-700 border-indigo-300',
  teal: 'bg-teal-100 text-teal-700 border-teal-300',
  bold: 'bg-amber-100 text-amber-700 border-amber-300',
}

export default function AffiliatePropertyReportsPage() {
  const [stats, setStats] = useState<AffiliateStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function fetchStats() {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/proxy/v1/property/stats/affiliate')
      if (!response.ok) {
        if (response.status === 403) {
          setError('This page is only available to affiliate accounts.')
        } else {
          setError('Failed to load property report statistics.')
        }
        return
      }
      const data = await response.json()
      setStats(data)
    } catch (err) {
      setError('Failed to connect to the server.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Property Reports Analytics</h1>
          <p className="text-muted-foreground">Loading statistics...</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-center px-4">
        <AlertCircle className="h-16 w-16 text-muted-foreground mb-4" />
        <h1 className="text-2xl font-bold mb-2">Unable to Load Data</h1>
        <p className="text-muted-foreground max-w-md mb-6">{error}</p>
        <Button onClick={fetchStats}>
          <RefreshCw className="h-4 w-4 mr-2" /> Try Again
        </Button>
      </div>
    )
  }

  if (!stats) return null

  const { summary, aggregate, themes, leaderboard, inactive_agents } = stats

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Property Reports Analytics</h1>
          <p className="text-muted-foreground">
            Performance metrics for your sponsored agents • Last 30 days
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchStats}>
          <RefreshCw className="h-4 w-4 mr-2" /> Refresh
        </Button>
      </div>

      {/* Agent Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Agents</CardTitle>
            <Users className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{summary.total_agents}</div>
            <p className="text-xs text-muted-foreground mt-1">sponsored agents</p>
          </CardContent>
        </Card>

        <Card className="bg-emerald-50 border-emerald-200">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-emerald-700">Active Agents</CardTitle>
            <TrendingUp className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-emerald-700">{summary.active_agents}</div>
            <p className="text-xs text-emerald-600 mt-1">created reports this month</p>
          </CardContent>
        </Card>

        <Card className="bg-amber-50 border-amber-200">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-amber-700">Inactive Agents</CardTitle>
            <AlertCircle className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-amber-700">{summary.inactive_agents}</div>
            <p className="text-xs text-amber-600 mt-1">no reports in 30 days</p>
          </CardContent>
        </Card>
      </div>

      {/* Aggregate Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Reports</CardTitle>
            <Home className="h-4 w-4 text-teal-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{aggregate.total_reports}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {aggregate.completed} completed • {aggregate.failed} failed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Views</CardTitle>
            <Eye className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{aggregate.total_views}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {aggregate.unique_visitors} unique visitors
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Leads Captured</CardTitle>
            <UserPlus className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{aggregate.total_leads}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {aggregate.leads_converted} converted
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Conversion Rate</CardTitle>
            <Target className="h-4 w-4 text-indigo-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{aggregate.conversion_rate}%</div>
            <p className="text-xs text-muted-foreground mt-1">
              visitors → leads
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Lead Sources */}
      <div className="grid grid-cols-2 gap-4">
        <Card className="bg-teal-50 border-teal-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-teal-600">From QR Scans</p>
                <p className="text-xl font-bold text-teal-700">{aggregate.leads_from_qr}</p>
              </div>
              <BarChart3 className="h-6 w-6 text-teal-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-blue-600">From Direct Links</p>
                <p className="text-xl font-bold text-blue-700">{aggregate.leads_from_direct}</p>
              </div>
              <TrendingUp className="h-6 w-6 text-blue-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Theme Distribution */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Theme Popularity
          </CardTitle>
          <CardDescription>How your agents&apos; reports are distributed across themes</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            {Object.entries(themes).map(([theme, count]) => {
              const total = aggregate.total_reports || 1
              const percentage = Math.round((count / total) * 100)
              return (
                <div key={theme} className="flex-1 min-w-[100px]">
                  <div className="flex items-center justify-between mb-2">
                    <Badge className={THEME_COLORS[theme]}>
                      {theme.charAt(0).toUpperCase() + theme.slice(1)}
                    </Badge>
                    <span className="text-sm font-medium">{count}</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-teal-400 to-teal-600 rounded-full"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{percentage}%</p>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Leaderboard */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trophy className="h-5 w-5 text-amber-500" />
            Agent Leaderboard
          </CardTitle>
          <CardDescription>Top performing agents by property report activity</CardDescription>
        </CardHeader>
        <CardContent>
          {leaderboard.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No agent activity yet. Invite agents to get started!
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Rank</TableHead>
                  <TableHead>Agent</TableHead>
                  <TableHead className="text-right">Reports</TableHead>
                  <TableHead className="text-right">Views</TableHead>
                  <TableHead className="text-right">Leads</TableHead>
                  <TableHead className="text-right">Last Active</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {leaderboard.map((agent, idx) => (
                  <TableRow key={agent.account_id}>
                    <TableCell>
                      <Badge
                        variant={idx < 3 ? 'default' : 'outline'}
                        className={
                          idx === 0 ? 'bg-amber-500' :
                          idx === 1 ? 'bg-slate-400' :
                          idx === 2 ? 'bg-amber-700' : ''
                        }
                      >
                        #{idx + 1}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{agent.name}</p>
                        <p className="text-xs text-muted-foreground">{agent.email}</p>
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-semibold text-teal-600">
                      {agent.reports}
                    </TableCell>
                    <TableCell className="text-right">{agent.views}</TableCell>
                    <TableCell className="text-right font-semibold text-emerald-600">
                      {agent.leads}
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground text-sm">
                      {agent.last_activity
                        ? new Date(agent.last_activity).toLocaleDateString()
                        : 'Never'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Inactive Agents */}
      {inactive_agents.length > 0 && (
        <Card className="border-amber-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-amber-700">
              <AlertCircle className="h-5 w-5" />
              Inactive Agents
            </CardTitle>
            <CardDescription>
              Agents who haven&apos;t created a property report in the last 30 days
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Agent</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead className="text-right">Last Report</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {inactive_agents.map((agent) => (
                  <TableRow key={agent.account_id}>
                    <TableCell className="font-medium">{agent.name}</TableCell>
                    <TableCell className="text-muted-foreground">{agent.email}</TableCell>
                    <TableCell className="text-right text-muted-foreground">
                      {agent.last_report}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}


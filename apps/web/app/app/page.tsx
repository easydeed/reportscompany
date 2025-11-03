"use client"

import { useEffect, useState } from "react"
import { MetricCard } from "@/components/metric-card"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts"
import { FileText, TrendingUp, CheckCircle, Zap } from "lucide-react"
import { API_BASE, DEMO_ACC } from "@/lib/api"

type UsageData = {
  summary?: { total_reports: number; billable_reports: number }
  by_type?: Array<{ report_type: string; c: number }>
  timeline?: Array<{ date: string; reports: number }>
  limits?: { monthly_report_limit?: number; api_rate_limit?: number }
}

async function fetchUsage(): Promise<UsageData | null> {
  try {
    const res = await fetch(`${API_BASE}/v1/usage`, {
      headers: { "X-Demo-Account": DEMO_ACC },
      cache: "no-store"
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export default function Overview() {
  const [data, setData] = useState<UsageData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchUsage().then((d) => {
      setData(d)
      setLoading(false)
    })
  }, [])

  const summary = data?.summary ?? { total_reports: 0, billable_reports: 0 }
  const byType = data?.by_type ?? []
  const timeline = data?.timeline ?? []
  const limits = data?.limits ?? {}

  // Format timeline data for recharts
  const chartData = timeline.map((d) => ({
    date: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    reports: d.reports,
  }))

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="font-bold text-3xl">Overview</h1>
        <p className="text-muted-foreground">Loading...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-bold text-3xl mb-2">Overview</h1>
        <p className="text-muted-foreground">Welcome back! Here's your report activity.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Total Reports"
          value={summary.total_reports}
          icon={<FileText className="w-4 h-4" />}
          index={0}
        />
        <MetricCard
          label="Billable Reports"
          value={summary.billable_reports}
          icon={<CheckCircle className="w-4 h-4" />}
          index={1}
        />
        <MetricCard
          label="Monthly Limit"
          value={limits.monthly_report_limit ?? "—"}
          icon={<TrendingUp className="w-4 h-4" />}
          index={2}
        />
        <MetricCard
          label="API Rate (rpm)"
          value={limits.api_rate_limit ?? "—"}
          icon={<Zap className="w-4 h-4" />}
          index={3}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Daily Activity</CardTitle>
            <CardDescription>Report generation over time</CardDescription>
          </CardHeader>
          <CardContent>
            {chartData.length === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center">No activity data yet</p>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="date" className="text-xs" />
                  <YAxis className="text-xs" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "var(--radius)",
                    }}
                  />
                  <Bar dataKey="reports" fill="hsl(var(--primary))" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Reports by Type</CardTitle>
            <CardDescription>Distribution across report templates</CardDescription>
          </CardHeader>
          <CardContent>
            {byType.length === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center">No reports generated yet</p>
            ) : (
              <div className="space-y-4">
                {byType.map((r) => {
                  const maxCount = byType[0]?.c || 1
                  const percentage = (r.c / maxCount) * 100
                  return (
                    <div key={r.report_type} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium capitalize">{r.report_type.replace(/_/g, " ")}</span>
                        <span className="text-muted-foreground">{r.c}</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-muted">
                        <div
                          className="h-2 rounded-full bg-primary transition-all"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

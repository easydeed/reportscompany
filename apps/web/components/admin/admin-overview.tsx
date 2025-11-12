"use client"

import { MetricCard } from "@/components/metric-card"
import { BarChart3, Calendar, Mail, Zap } from "lucide-react"
import { Line, LineChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip } from "recharts"
import { Card } from "@/components/ui/card"
import type { AdminKPIData, ChartDataPoint } from "./types"

interface AdminOverviewProps {
  kpis: AdminKPIData
  reportsChartData: ChartDataPoint[]
  emailsChartData: ChartDataPoint[]
}

export function AdminOverview({ kpis, reportsChartData, emailsChartData }: AdminOverviewProps) {
  return (
    <div className="space-y-8">
      {/* KPI Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Active Schedules"
          value={kpis.activeSchedules}
          icon={<Calendar className="w-4 h-4" />}
          index={0}
        />
        <MetricCard label="Reports/Day" value={kpis.reportsPerDay} icon={<BarChart3 className="w-4 h-4" />} index={1} />
        <MetricCard label="Emails/Day" value={kpis.emailsPerDay} icon={<Mail className="w-4 h-4" />} index={2} />
        <MetricCard label="Avg Render (ms)" value={kpis.avgRenderMs} icon={<Zap className="w-4 h-4" />} index={3} />
      </div>

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Reports Chart */}
        <Card className="glass p-6 border-border">
          <div className="mb-4">
            <h3 className="text-lg font-display font-semibold text-foreground">Reports (Last 30d)</h3>
            <p className="text-sm text-muted-foreground">Daily report generation volume</p>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={reportsChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis
                dataKey="date"
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                }}
              />
              <Line type="monotone" dataKey="reports" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        {/* Emails Chart */}
        <Card className="glass p-6 border-border">
          <div className="mb-4">
            <h3 className="text-lg font-display font-semibold text-foreground">Emails (Last 30d)</h3>
            <p className="text-sm text-muted-foreground">Daily email delivery volume</p>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={emailsChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis
                dataKey="date"
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                }}
              />
              <Line type="monotone" dataKey="emails" stroke="hsl(var(--accent))" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  )
}

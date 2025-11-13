"use client"

import { Card } from "./ui/card"
import { BarChart3, Calendar, Mail, Zap, AlertTriangle, Server } from "lucide-react"
import { Line, LineChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip, Area, AreaChart } from "recharts"
import type { AdminKPIData, ChartDataPoint, QueueStatus } from "./types"
import { cn } from "../lib/utils"

interface AdminOverviewProps {
  kpis: AdminKPIData
  reportsChartData: ChartDataPoint[]
  emailsChartData: ChartDataPoint[]
  queue?: QueueStatus
}

export function AdminOverview({ kpis, reportsChartData, emailsChartData, queue }: AdminOverviewProps) {
  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat("en-US", {
      hour: "numeric",
      minute: "2-digit",
      second: "2-digit",
    }).format(date)
  }

  return (
    <div className="space-y-8">
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-5">
        <Card className="glass border-border/50 backdrop-blur-sm p-6">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-medium text-slate-400">Active Schedules</div>
            <Calendar className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-display font-bold text-white">{kpis.activeSchedules}</div>
        </Card>

        <Card className="glass border-border/50 backdrop-blur-sm p-6">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-medium text-slate-400">Reports/Day</div>
            <BarChart3 className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-display font-bold text-white">{kpis.reportsPerDay.toLocaleString()}</div>
        </Card>

        <Card className="glass border-border/50 backdrop-blur-sm p-6">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-medium text-slate-400">Emails/Day</div>
            <Mail className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-display font-bold text-white">{kpis.emailsPerDay.toLocaleString()}</div>
        </Card>

        <Card className="glass border-border/50 backdrop-blur-sm p-6">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-medium text-slate-400">Avg Render</div>
            <Zap className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-display font-bold text-white font-mono">{kpis.avgRenderMs}ms</div>
        </Card>

        <Card className="glass border-border/50 backdrop-blur-sm p-6">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-medium text-slate-400">Error Rate</div>
            <AlertTriangle className={cn("w-4 h-4", kpis.errorRate < 1 ? "text-cyan-400" : "text-red-400")} />
          </div>
          <div
            className={cn(
              "text-3xl font-display font-bold font-mono",
              kpis.errorRate < 1 ? "text-cyan-400" : "text-red-400",
            )}
          >
            {kpis.errorRate.toFixed(2)}%
          </div>
        </Card>
      </div>

      {queue && (
        <Card className="glass border-cyan-500/20 backdrop-blur-sm p-6 bg-gradient-to-br from-slate-900/50 to-slate-800/30">
          <div className="flex items-center gap-3 mb-4">
            <Server className="w-5 h-5 text-cyan-400" />
            <h3 className="text-lg font-display font-semibold text-white">Queue Status</h3>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-slate-400 mb-1">Queue Depth</div>
              <div className="text-2xl font-display font-bold text-white font-mono">{queue.depth}</div>
            </div>
            {queue.lastTask && (
              <div className="text-right">
                <div className="text-sm text-slate-400 mb-1">Last Task</div>
                <div className="flex items-center gap-2">
                  <div
                    className={cn(
                      "w-2 h-2 rounded-full",
                      queue.lastTask.status === "completed"
                        ? "bg-green-400"
                        : queue.lastTask.status === "processing"
                          ? "bg-cyan-400 animate-pulse"
                          : "bg-red-400",
                    )}
                  />
                  <span className="text-white font-medium">{queue.lastTask.type}</span>
                  <span className="text-slate-400 text-sm font-mono">{formatDate(queue.lastTask.startedAt)}</span>
                </div>
              </div>
            )}
          </div>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="glass border-border/50 backdrop-blur-sm p-6">
          <div className="mb-4">
            <h3 className="text-lg font-display font-semibold text-white">Reports (Last 30d)</h3>
            <p className="text-sm text-slate-400">Daily report generation volume</p>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={reportsChartData}>
              <defs>
                <linearGradient id="colorReports" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22D3EE" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#22D3EE" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
              <XAxis dataKey="date" stroke="#64748B" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="#64748B" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0F172A",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                  color: "#fff",
                }}
              />
              <Area
                type="monotone"
                dataKey="reports"
                stroke="#22D3EE"
                strokeWidth={2}
                fill="url(#colorReports)"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        <Card className="glass border-border/50 backdrop-blur-sm p-6">
          <div className="mb-4">
            <h3 className="text-lg font-display font-semibold text-white">Emails (Last 30d)</h3>
            <p className="text-sm text-slate-400">Daily email delivery volume</p>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={emailsChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
              <XAxis dataKey="date" stroke="#64748B" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="#64748B" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0F172A",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                  color: "#fff",
                }}
              />
              <Line type="monotone" dataKey="emails" stroke="#7C3AED" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  )
}

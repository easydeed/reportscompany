"use client"

import type React from "react"

import { motion } from "framer-motion"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { FileText, Calendar, Zap, ExternalLink, FileCheck, TrendingUp } from "lucide-react"
import { cn } from "@/lib/utils"
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import Link from "next/link"

interface KPIData {
  reports: number
  billable: number
  schedules: number
  avgRenderMs: number
}

interface ChartDataPoint {
  date: string
  value: number
}

interface ActivityItem {
  id: string
  date: string
  event: string
  type: string
  status: "success" | "pending" | "failed"
  link: string
  linkType: "report" | "email"
}

interface DashboardOverviewProps {
  kpis: KPIData
  reports30d: ChartDataPoint[]
  emails30d: ChartDataPoint[]
  recent: ActivityItem[]
}

function KPICard({
  label,
  value,
  icon,
  index,
}: {
  label: string
  value: string | number
  icon: React.ReactNode
  index: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18, delay: index * 0.04 }}
    >
      <Card className="relative overflow-hidden border-slate-200 bg-white shadow-sm hover:shadow-md transition-shadow">
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-3">
            <p className="text-sm font-medium text-slate-600">{label}</p>
            <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center text-purple-600">
              {icon}
            </div>
          </div>
          <p className="font-display text-4xl font-bold text-slate-900 tracking-tight">{value}</p>
        </CardContent>
      </Card>
    </motion.div>
  )
}

function StatusDot({ status }: { status: "success" | "pending" | "failed" }) {
  const colors = {
    success: "bg-green-500",
    pending: "bg-blue-500",
    failed: "bg-red-500",
  }

  return (
    <span className={cn("inline-block w-1.5 h-1.5 rounded-full", colors[status])} aria-label={status}>
      <span className="sr-only">{status}</span>
    </span>
  )
}

export function DashboardOverview({ kpis, reports30d, emails30d, recent }: DashboardOverviewProps) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50/30 via-white to-white">
      <div className="border-b border-slate-200 bg-white/80 backdrop-blur-sm mb-6">
        <div className="px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-purple-700 flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-display text-2xl font-bold text-slate-900">Overview</h1>
              <p className="text-sm text-slate-600">Track your market report trends</p>
            </div>
          </div>
        </div>
      </div>

      <div className="px-6 space-y-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <KPICard label="Reports (Period)" value={kpis.reports} icon={<FileText className="w-5 h-5" />} index={0} />
          <KPICard label="Billable Reports" value={kpis.billable} icon={<FileCheck className="w-5 h-5" />} index={1} />
          <KPICard label="Active Schedules" value={kpis.schedules} icon={<Calendar className="w-5 h-5" />} index={2} />
          <KPICard label="Avg Render (ms)" value={kpis.avgRenderMs} icon={<Zap className="w-5 h-5" />} index={3} />
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="text-slate-900 font-display">Reports (30 days)</CardTitle>
              <CardDescription className="text-slate-600">Daily generation volume</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={reports30d}>
                  <defs>
                    <linearGradient id="colorReportsTrendy" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#7C3AED" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#7C3AED" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                  <XAxis
                    dataKey="date"
                    stroke="#94a3b8"
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value) => value.slice(0, 5)}
                  />
                  <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} width={40} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#ffffff",
                      border: "1px solid #e2e8f0",
                      borderRadius: "8px",
                      color: "#0f172a",
                      boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                    }}
                    labelStyle={{ color: "#475569" }}
                  />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#7C3AED"
                    strokeWidth={3}
                    fill="url(#colorReportsTrendy)"
                    animationDuration={600}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="text-slate-900 font-display">Emails Sent (30 days)</CardTitle>
              <CardDescription className="text-slate-600">Delivery volume</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={emails30d}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                  <XAxis
                    dataKey="date"
                    stroke="#94a3b8"
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value) => value.slice(0, 5)}
                  />
                  <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} width={40} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#ffffff",
                      border: "1px solid #e2e8f0",
                      borderRadius: "8px",
                      color: "#0f172a",
                      boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                    }}
                    labelStyle={{ color: "#475569" }}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#F26B2B"
                    strokeWidth={3}
                    dot={{ fill: "#F26B2B", r: 4 }}
                    activeDot={{ r: 6 }}
                    animationDuration={600}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        <Card className="border-slate-200 bg-white shadow-sm">
          <CardHeader>
            <CardTitle className="text-slate-900 font-display">Recent Activity</CardTitle>
            <CardDescription className="text-slate-600">Latest reports and deliveries</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-3 px-4 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                      Event
                    </th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                      Link
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {recent.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3 px-4 text-sm text-slate-600 whitespace-nowrap">{item.date}</td>
                      <td className="py-3 px-4 text-sm text-slate-900 font-medium">{item.event}</td>
                      <td className="py-3 px-4">
                        <Badge variant="secondary" className="text-xs bg-purple-100 text-purple-700 border-purple-200">
                          {item.type}
                        </Badge>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <StatusDot status={item.status} />
                          <span className="text-sm text-slate-700 capitalize">{item.status}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <Link href={item.link}>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 text-xs text-purple-600 hover:text-purple-700 hover:bg-purple-50"
                          >
                            {item.linkType === "report" ? "View Report" : "View Email"}
                            <ExternalLink className="w-3 h-3 ml-1" />
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export function DashboardOverviewEmpty() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50/30 via-white to-white">
      <div className="border-b border-slate-200 bg-white/80 backdrop-blur-sm mb-6">
        <div className="px-6 py-4">
          <h1 className="font-display text-2xl font-bold text-slate-900">Market Control Center</h1>
          <p className="text-sm text-slate-600 mt-0.5">Real-time insights and operational metrics</p>
        </div>
      </div>

      <div className="px-6">
        <Card className="border-slate-200 bg-white shadow-sm">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="w-16 h-16 rounded-full bg-slate-800/50 flex items-center justify-center mb-4">
              <FileText className="w-8 h-8 text-slate-500" />
            </div>
            <h3 className="font-display text-xl font-semibold text-slate-200 mb-2">No Data Available</h3>
            <p className="text-sm text-slate-400 text-center max-w-md mb-6">
              Start generating reports to see your dashboard metrics and activity.
            </p>
            <Link href="/dashboard/reports/new">
              <Button className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white">
                Create Your First Report
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

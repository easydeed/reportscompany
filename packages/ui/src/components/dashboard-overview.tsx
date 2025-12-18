"use client"

import type React from "react"

import { motion } from "framer-motion"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Button } from "./ui/button"
import { FileText, Calendar } from "lucide-react"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
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

export function DashboardOverview({ kpis, reports30d, emails30d, recent }: DashboardOverviewProps) {
  return (
    <div className="space-y-6">
      {/* Simplified KPIs - 2 cards instead of 4 */}
      <div className="grid gap-4 md:grid-cols-2">
        <KPICard label="Reports This Month" value={kpis.reports} icon={<FileText className="w-5 h-5" />} index={0} />
        <KPICard label="Active Schedules" value={kpis.schedules} icon={<Calendar className="w-5 h-5" />} index={1} />
      </div>

      {/* Single full-width chart */}
      <Card className="border-slate-200 bg-white shadow-sm">
        <CardHeader>
          <CardTitle className="text-slate-900 font-display">Reports (30 days)</CardTitle>
          <CardDescription className="text-slate-600">Your report generation activity</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={240}>
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

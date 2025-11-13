"use client"

import { MetricCard } from "@/components/metric-card"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid, Area, AreaChart } from "recharts"
import { FileText, TrendingUp, Users, Eye, Plus, ArrowRight, Calendar } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { Badge } from "@/components/ui/badge"

const reportsData = [
  { month: "Jan", reports: 45 },
  { month: "Feb", reports: 52 },
  { month: "Mar", reports: 61 },
  { month: "Apr", reports: 58 },
  { month: "May", reports: 72 },
  { month: "Jun", reports: 68 },
]

const engagementData = [
  { day: "Mon", views: 120 },
  { day: "Tue", views: 145 },
  { day: "Wed", views: 132 },
  { day: "Thu", views: 168 },
  { day: "Fri", views: 195 },
  { day: "Sat", views: 88 },
  { day: "Sun", views: 76 },
]

const reportTypeData = [
  { type: "Market Analysis", count: 45, color: "hsl(var(--chart-1))" },
  { type: "CMA Report", count: 38, color: "hsl(var(--chart-2))" },
  { type: "Investment", count: 32, color: "hsl(var(--chart-3))" },
  { type: "Neighborhood", count: 27, color: "hsl(var(--chart-4))" },
]

const recentActivity = [
  {
    id: "rpt_001",
    title: "Market Analysis - Downtown SF",
    time: "2 hours ago",
    status: "Completed",
    type: "Market Analysis",
    views: 12,
  },
  {
    id: "rpt_002",
    title: "Neighborhood Comparison - Mission District",
    time: "5 hours ago",
    status: "Completed",
    type: "Neighborhood",
    views: 8,
  },
  {
    id: "rpt_003",
    title: "Investment Analysis - Oakland",
    time: "1 day ago",
    status: "Completed",
    type: "Investment",
    views: 15,
  },
  {
    id: "rpt_004",
    title: "CMA Report - Berkeley Hills",
    time: "2 days ago",
    status: "Completed",
    type: "CMA Report",
    views: 23,
  },
]

export default function DashboardOverview() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display font-bold text-3xl mb-2 text-balance">Overview</h1>
          <p className="text-muted-foreground">Welcome back! Here's what's happening with your reports.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="gap-2 bg-transparent">
            <Calendar className="w-4 h-4" />
            Last 30 days
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Total Reports"
          value="142"
          change={12.5}
          trend="up"
          icon={<FileText className="w-4 h-4" />}
          index={0}
        />
        <MetricCard
          label="This Month"
          value="68"
          change={8.2}
          trend="up"
          icon={<TrendingUp className="w-4 h-4" />}
          index={1}
        />
        <MetricCard
          label="Total Views"
          value="3,247"
          change={23.1}
          trend="up"
          icon={<Eye className="w-4 h-4" />}
          index={2}
        />
        <MetricCard
          label="Avg. per Report"
          value="22.8"
          change={2.4}
          trend="down"
          icon={<Users className="w-4 h-4" />}
          index={3}
        />
      </div>

      <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-accent/5">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-display font-semibold text-lg mb-1">Ready to create a new report?</h3>
              <p className="text-sm text-muted-foreground">Generate professional market reports in seconds</p>
            </div>
            <Link href="/dashboard/reports/new">
              <Button size="lg" className="gap-2">
                <Plus className="w-4 h-4" />
                New Report
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="font-display">Reports Generated</CardTitle>
            <CardDescription>Monthly report generation over the last 6 months</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={reportsData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" vertical={false} />
                <XAxis dataKey="month" className="text-xs" axisLine={false} tickLine={false} />
                <YAxis className="text-xs" axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "var(--radius)",
                  }}
                  cursor={{ fill: "hsl(var(--muted))" }}
                />
                <Bar dataKey="reports" fill="hsl(var(--primary))" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="font-display">Report Types</CardTitle>
            <CardDescription>Distribution by type</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {reportTypeData.map((item, index) => (
                <div key={item.type} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{item.type}</span>
                    <span className="text-muted-foreground">{item.count}</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                    <div
                      className="h-2 rounded-full transition-all duration-500"
                      style={{
                        width: `${(item.count / 142) * 100}%`,
                        backgroundColor: item.color,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="font-display">Report Engagement</CardTitle>
          <CardDescription>Views per day over the last week</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={engagementData}>
              <defs>
                <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" vertical={false} />
              <XAxis dataKey="day" className="text-xs" axisLine={false} tickLine={false} />
              <YAxis className="text-xs" axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "var(--radius)",
                }}
              />
              <Area
                type="monotone"
                dataKey="views"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                fill="url(#colorViews)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="font-display">Recent Activity</CardTitle>
              <CardDescription>Your latest report generations and updates</CardDescription>
            </div>
            <Link href="/dashboard/reports">
              <Button variant="ghost" size="sm" className="gap-2">
                View All
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recentActivity.map((activity) => (
              <div
                key={activity.id}
                className="flex items-center justify-between p-4 rounded-lg border border-border hover:border-primary/30 hover:bg-secondary/30 transition-all cursor-pointer group"
              >
                <div className="flex items-center gap-4 flex-1">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-sm mb-1">{activity.title}</p>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-xs">
                        {activity.type}
                      </Badge>
                      <span className="text-xs text-muted-foreground">{activity.time}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-sm font-medium">{activity.views} views</p>
                    <Badge className="text-xs bg-primary/10 text-primary hover:bg-primary/20">{activity.status}</Badge>
                  </div>
                  <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

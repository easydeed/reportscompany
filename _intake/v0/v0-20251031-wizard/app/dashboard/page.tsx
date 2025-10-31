"use client"

import { MetricCard } from "@/components/metric-card"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Bar, BarChart, Line, LineChart, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts"
import { FileText, TrendingUp, Users, DollarSign } from "lucide-react"

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

export default function DashboardOverview() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display font-bold text-3xl mb-2">Overview</h1>
        <p className="text-muted-foreground">Welcome back! Here's what's happening with your reports.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Reports"
          value="142"
          change="+12.5%"
          trend="up"
          icon={<FileText className="w-4 h-4" />}
        />
        <MetricCard title="This Month" value="68" change="+8.2%" trend="up" icon={<TrendingUp className="w-4 h-4" />} />
        <MetricCard title="Total Views" value="3,247" change="+23.1%" trend="up" icon={<Users className="w-4 h-4" />} />
        <MetricCard
          title="Avg. per Report"
          value="22.8"
          change="-2.4%"
          trend="down"
          icon={<DollarSign className="w-4 h-4" />}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="font-display">Reports Generated</CardTitle>
            <CardDescription>Monthly report generation over the last 6 months</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={reportsData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="month" className="text-xs" />
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
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="font-display">Report Engagement</CardTitle>
            <CardDescription>Views per day over the last week</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={engagementData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="day" className="text-xs" />
                <YAxis className="text-xs" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "var(--radius)",
                  }}
                />
                <Line type="monotone" dataKey="views" stroke="hsl(var(--primary))" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="font-display">Recent Activity</CardTitle>
          <CardDescription>Your latest report generations and updates</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { title: "Market Analysis - Downtown SF", time: "2 hours ago", status: "Completed" },
              { title: "Neighborhood Comparison - Mission District", time: "5 hours ago", status: "Completed" },
              { title: "Investment Analysis - Oakland", time: "1 day ago", status: "Completed" },
              { title: "CMA Report - Berkeley Hills", time: "2 days ago", status: "Completed" },
            ].map((activity, i) => (
              <div key={i} className="flex items-center justify-between py-3 border-b border-border last:border-0">
                <div>
                  <p className="font-medium text-sm">{activity.title}</p>
                  <p className="text-xs text-muted-foreground">{activity.time}</p>
                </div>
                <span className="text-xs px-2 py-1 rounded-full bg-primary/10 text-primary font-medium">
                  {activity.status}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

"use client"

import {
  AdminOverview,
  AdminReportsTable,
  AdminSchedulesTable,
  AdminEmailsTable,
  type AdminKPIData,
  type RecentReport,
  type AdminSchedule,
  type EmailLog,
  type ChartDataPoint,
  type QueueStatus,
} from "@/components/admin"

// Mock data - parent pages will wire real fetch/submit
const mockKPIs: AdminKPIData = {
  activeSchedules: 142,
  reportsPerDay: 3247,
  emailsPerDay: 8921,
  avgRenderMs: 847,
  errorRate: 0.34, // Added error rate KPI
}

const mockQueue: QueueStatus = {
  depth: 23,
  lastTask: {
    id: "task-1234",
    type: "Market Snapshot",
    status: "completed",
    startedAt: new Date(Date.now() - 2 * 60 * 1000),
  },
}

const mockReportsChartData: ChartDataPoint[] = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  }),
  reports: Math.floor(Math.random() * 1000) + 2500,
}))

const mockEmailsChartData: ChartDataPoint[] = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  }),
  emails: Math.floor(Math.random() * 2000) + 7000,
}))

const mockRecentReports: RecentReport[] = [
  {
    id: "1",
    type: "Market Snapshot",
    org: "Coldwell Banker",
    status: "completed",
    duration: 1247,
    finished: new Date(Date.now() - 5 * 60 * 1000),
  },
  {
    id: "2",
    type: "Neighborhood Report",
    org: "RE/MAX Elite",
    status: "processing",
    duration: 0,
    finished: new Date(),
  },
  {
    id: "3",
    type: "Price Analysis",
    org: "Keller Williams",
    status: "completed",
    duration: 892,
    finished: new Date(Date.now() - 12 * 60 * 1000),
  },
  {
    id: "4",
    type: "Listing Flyer",
    org: "Compass Realty",
    status: "failed",
    duration: 234,
    finished: new Date(Date.now() - 18 * 60 * 1000),
  },
  {
    id: "5",
    type: "Market Trends",
    org: "Sotheby's International",
    status: "completed",
    duration: 1534,
    finished: new Date(Date.now() - 25 * 60 * 1000),
  },
]

const mockSchedules: AdminSchedule[] = [
  {
    id: "1",
    org: "Coldwell Banker",
    name: "Weekly Market Update",
    cadence: "Weekly - Monday 9:00 AM",
    nextRun: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000),
    active: true,
  },
  {
    id: "2",
    org: "RE/MAX Elite",
    name: "Monthly Report",
    cadence: "Monthly - 1st at 8:00 AM",
    nextRun: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000),
    active: true,
  },
  {
    id: "3",
    org: "Keller Williams",
    name: "Neighborhood Digest",
    cadence: "Weekly - Friday 5:00 PM",
    nextRun: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000),
    active: false,
  },
  {
    id: "4",
    org: "Compass Realty",
    name: "Price Updates",
    cadence: "Weekly - Wednesday 10:00 AM",
    nextRun: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000),
    active: true,
  },
]

const mockEmailLogs: EmailLog[] = [
  {
    id: "1",
    date: new Date(Date.now() - 5 * 60 * 1000),
    to: 15,
    subject: "Your Weekly Market Snapshot - Downtown Seattle",
    code: 200,
  },
  {
    id: "2",
    date: new Date(Date.now() - 12 * 60 * 1000),
    to: 8,
    subject: "Monthly Market Report - Eastside Neighborhoods",
    code: 200,
  },
  {
    id: "3",
    date: new Date(Date.now() - 18 * 60 * 1000),
    to: 23,
    subject: "Price Analysis Report - Capitol Hill",
    code: 422,
  },
  {
    id: "4",
    date: new Date(Date.now() - 25 * 60 * 1000),
    to: 1,
    subject: "Custom Neighborhood Report - Queen Anne",
    code: 200,
  },
  {
    id: "5",
    date: new Date(Date.now() - 35 * 60 * 1000),
    to: 12,
    subject: "Market Trends - Greater Seattle Area",
    code: 200,
  },
]

export default function AdminPage() {
  const handleToggleSchedule = (id: string, active: boolean) => {
    console.log("[v0] Toggle schedule", { id, active })
    // Parent will wire API call
  }

  const handlePauseResume = (id: string, action: "pause" | "resume") => {
    console.log("[v0] Pause/Resume schedule", { id, action })
    // Parent will wire API call
  }

  const handleRetryReport = (id: string) => {
    console.log("[v0] Retry report", { id })
    // Parent will wire API call
  }

  const handleImpersonate = (org: string) => {
    console.log("[v0] Impersonate org", { org })
    // Parent will wire navigation/auth switch
  }

  return (
    <div className="space-y-8 min-h-screen bg-gradient-to-b from-slate-900 to-slate-950 p-8">
      <div>
        <h1 className="text-3xl font-display font-bold text-white">Market Control Center</h1>
        <p className="text-slate-400 mt-2">Monitor system performance and manage all organizations</p>
      </div>

      <AdminOverview
        kpis={mockKPIs}
        reportsChartData={mockReportsChartData}
        emailsChartData={mockEmailsChartData}
        queue={mockQueue}
      />

      <div className="space-y-6">
        <AdminReportsTable reports={mockRecentReports} onRetry={handleRetryReport} onImpersonate={handleImpersonate} />
        <AdminSchedulesTable
          schedules={mockSchedules}
          onToggleActive={handleToggleSchedule}
          onPauseResume={handlePauseResume}
          onImpersonate={handleImpersonate}
        />
        <AdminEmailsTable logs={mockEmailLogs} />
      </div>
    </div>
  )
}

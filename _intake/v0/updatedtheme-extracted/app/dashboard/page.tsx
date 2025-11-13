"use client"

import { DashboardOverview } from "@/components/dashboard-overview"

// Mock data - parent pages will wire actual API calls
const mockKPIs = {
  reports: 342,
  billable: 298,
  schedules: 12,
  avgRenderMs: 847,
}

const mockReports30d = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  }),
  value: Math.floor(Math.random() * 30) + 10,
}))

const mockEmails30d = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  }),
  value: Math.floor(Math.random() * 50) + 20,
}))

const mockRecent = [
  {
    id: "1",
    date: "Jan 15, 10:23 AM",
    event: "Market Report Generated",
    type: "Report",
    status: "success" as const,
    link: "/dashboard/reports/123",
    linkType: "report" as const,
  },
  {
    id: "2",
    date: "Jan 15, 09:45 AM",
    event: "Scheduled Email Sent",
    type: "Email",
    status: "success" as const,
    link: "/dashboard/emails/456",
    linkType: "email" as const,
  },
  {
    id: "3",
    date: "Jan 15, 08:12 AM",
    event: "CMA Report Processing",
    type: "Report",
    status: "pending" as const,
    link: "/dashboard/reports/124",
    linkType: "report" as const,
  },
  {
    id: "4",
    date: "Jan 14, 11:30 PM",
    event: "Bulk Email Delivery",
    type: "Email",
    status: "success" as const,
    link: "/dashboard/emails/457",
    linkType: "email" as const,
  },
  {
    id: "5",
    date: "Jan 14, 10:15 PM",
    event: "Report Generation Failed",
    type: "Report",
    status: "failed" as const,
    link: "/dashboard/reports/125",
    linkType: "report" as const,
  },
]

export default function DashboardPage() {
  return <DashboardOverview kpis={mockKPIs} reports30d={mockReports30d} emails30d={mockEmails30d} recent={mockRecent} />
}

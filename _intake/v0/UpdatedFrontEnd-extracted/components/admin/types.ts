export interface AdminKPIData {
  activeSchedules: number
  reportsPerDay: number
  emailsPerDay: number
  avgRenderMs: number
  errorRate: number // percentage
}

export interface RecentReport {
  id: string
  type: string
  org: string
  status: "completed" | "processing" | "failed"
  duration: number
  finished: Date
}

export interface AdminSchedule {
  id: string
  org: string
  name: string
  cadence: string
  nextRun: Date
  active: boolean
}

export interface EmailLog {
  id: string
  date: Date
  to: number
  subject: string
  code: number
}

export interface ChartDataPoint {
  date: string
  reports?: number
  emails?: number
}

export interface QueueStatus {
  depth: number
  lastTask?: {
    id: string
    type: string
    status: "processing" | "completed" | "failed"
    startedAt: Date
  }
}

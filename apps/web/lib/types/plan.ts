export interface ProductLimit {
  used: number
  limit: number
  status: 'ok' | 'warning' | 'at_limit' | 'exceeded'
  can_proceed: boolean
}

export interface PlanUsage {
  plan: {
    plan_slug: string
    plan_name: string
    market_reports_limit: number
    schedules_limit: number
    property_reports_limit: number
  }
  usage: {
    market_reports_used: number
    schedules_active: number
    property_reports_used: number
  }
  limits: {
    market_reports: ProductLimit
    schedules: ProductLimit
    property_reports: ProductLimit
  }
}

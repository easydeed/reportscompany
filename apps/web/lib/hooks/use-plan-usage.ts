'use client'

import { useQuery } from '@tanstack/react-query'

export type PlanUsage = {
  plan: {
    plan_name: string
    plan_slug: string
    monthly_report_limit: number
    allow_overage: boolean
    overage_price_cents: number
    has_override: boolean
  }
  usage: {
    report_count: number
    schedule_run_count: number
    period_start: string
    period_end: string
  }
  decision: string
  account: Record<string, unknown>
  info: Record<string, unknown>
  stripe_billing: Record<string, unknown> | null
}

async function fetchPlanUsage(): Promise<PlanUsage> {
  const res = await fetch('/api/proxy/v1/account/plan-usage', {
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Failed to fetch plan usage')
  return res.json()
}

export function usePlanUsage() {
  return useQuery({
    queryKey: ['plan-usage'],
    queryFn: fetchPlanUsage,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

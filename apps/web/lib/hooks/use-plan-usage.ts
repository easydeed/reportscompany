'use client'

import { useQuery } from '@tanstack/react-query'

export type PlanUsage = {
  plan: {
    plan_name: string
    plan_slug: string
    monthly_reports_limit: number
  }
  info: {
    reports_this_period: number
    active_schedules: number
  }
  limits: {
    reports_used: number
    reports_limit: number
    schedules_used: number
    schedules_limit: number
  }
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

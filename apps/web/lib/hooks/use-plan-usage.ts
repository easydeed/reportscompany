'use client'

import { useQuery } from '@tanstack/react-query'
import type { PlanUsage } from '@/lib/types/plan'

export type { PlanUsage }

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

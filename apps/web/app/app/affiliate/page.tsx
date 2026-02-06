'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Building2, Loader2 } from 'lucide-react'
import { AffiliateDashboardShell, type AffiliateDashboardShellProps } from '@/components/v0-styling/AffiliateDashboardShell'
import { AffiliateOnboarding, type OnboardingStatus } from '@/components/onboarding/affiliate-onboarding'
import { Skeleton } from '@/components/ui/skeleton'

interface AffiliateData {
  account: {
    account_id: string
    name: string
    account_type: string
    plan_slug: string
  }
  overview: {
    sponsored_count: number
    total_reports_this_month: number
  }
  sponsored_accounts: Array<{
    account_id: string
    name: string
    plan_slug: string
    account_type: string
    created_at: string
    reports_this_month: number
    last_report_at: string | null
  }>
}

export default function AffiliateDashboardPage() {
  const [loading, setLoading] = useState(true)
  const [affiliateData, setAffiliateData] = useState<AffiliateData | null>(null)
  const [planUsage, setPlanUsage] = useState<any>(null)
  const [onboardingData, setOnboardingData] = useState<OnboardingStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchAll() {
      try {
        const [affiliateRes, planRes, onboardingRes] = await Promise.all([
          fetch('/api/proxy/v1/affiliate/overview', { credentials: 'include' }),
          fetch('/api/proxy/v1/account/plan-usage', { credentials: 'include' }),
          fetch('/api/proxy/v1/onboarding', { credentials: 'include' }),
        ])

        if (affiliateRes.status === 403) {
          setError('not_affiliate')
          return
        }
        if (!affiliateRes.ok) {
          setError('load_failed')
          return
        }

        const affiliateJson = await affiliateRes.json()
        setAffiliateData(affiliateJson)

        if (planRes.ok) {
          setPlanUsage(await planRes.json())
        }
        if (onboardingRes.ok) {
          setOnboardingData(await onboardingRes.json())
        }
      } catch (err) {
        console.error('Failed to fetch affiliate data:', err)
        setError('load_failed')
      } finally {
        setLoading(false)
      }
    }
    fetchAll()
  }, [])

  if (loading) {
    return <AffiliateSkeleton />
  }

  if (error === 'not_affiliate') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <Building2 className="h-16 w-16 text-muted-foreground mb-4" />
        <h1 className="text-2xl font-bold mb-2">Not an Affiliate Account</h1>
        <p className="text-muted-foreground max-w-md mb-6">
          This account is not an industry affiliate. Affiliate features are only available
          to accounts with Industry Affiliate status.
        </p>
        <Button asChild>
          <a href="/app">Back to Dashboard</a>
        </Button>
      </div>
    )
  }

  if (error || !affiliateData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <h1 className="text-2xl font-bold mb-2">Error Loading Affiliate Data</h1>
        <p className="text-muted-foreground max-w-md mb-6">Failed to load affiliate data</p>
        <Button asChild>
          <a href="/app">Back to Dashboard</a>
        </Button>
      </div>
    )
  }

  const shellProps: AffiliateDashboardShellProps = {
    overview: affiliateData.overview,
    planSummary: planUsage ? {
      plan_name: planUsage.plan?.plan_name,
      report_count: planUsage.usage?.report_count,
      limit: planUsage.account?.monthly_report_limit_override ?? planUsage.plan?.monthly_report_limit,
    } : undefined,
    sponsoredAccounts: affiliateData.sponsored_accounts,
  }

  return (
    <div className="space-y-6">
      <AffiliateOnboarding
        sponsoredCount={affiliateData.overview.sponsored_count}
        initialStatus={onboardingData}
      />
      <AffiliateDashboardShell {...shellProps} />
    </div>
  )
}

function AffiliateSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-8 w-60 mb-2" />
          <Skeleton className="h-4 w-80" />
        </div>
        <Skeleton className="h-10 w-36 rounded-md" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-card border border-border rounded-xl p-6">
            <Skeleton className="h-4 w-24 mb-3" />
            <Skeleton className="h-8 w-16" />
          </div>
        ))}
      </div>
      <div className="bg-card border border-border rounded-xl p-6">
        <Skeleton className="h-5 w-40 mb-4" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="py-3 flex items-center gap-4">
            <Skeleton className="h-4 w-40 flex-1" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
        ))}
      </div>
    </div>
  )
}

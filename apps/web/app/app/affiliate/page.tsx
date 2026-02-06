'use client'

import { Button } from '@/components/ui/button'
import { Building2 } from 'lucide-react'
import { AffiliateDashboardShell, type AffiliateDashboardShellProps } from '@/components/v0-styling/AffiliateDashboardShell'
import { AffiliateOnboarding } from '@/components/onboarding/affiliate-onboarding'
import { Skeleton } from '@/components/ui/skeleton'
import { useAffiliateOverview, usePlanUsage, useOnboarding } from '@/hooks/use-api'

export default function AffiliateDashboardPage() {
  const { data: affiliateData, isLoading: affLoading, error: affError } = useAffiliateOverview()
  const { data: planUsage } = usePlanUsage()
  const { data: onboardingData } = useOnboarding()

  const loading = affLoading

  if (loading) {
    return <AffiliateSkeleton />
  }

  // Check for 403 (not affiliate)
  if (affError && String(affError).includes('403')) {
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

  if (affError || !affiliateData) {
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

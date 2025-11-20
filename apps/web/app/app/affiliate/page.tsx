import { cookies } from 'next/headers';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Building2 } from 'lucide-react';
import { AffiliateDashboardShell, type AffiliateDashboardShellProps } from '@/components/v0-styling/AffiliateDashboardShell';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

interface SponsoredAccount {
  account_id: string;
  name: string;
  plan_slug: string;
  account_type: string;
  created_at: string;
  reports_this_month: number;
  last_report_at: string | null;
}

interface AffiliateOverview {
  sponsored_count: number;
  total_reports_this_month: number;
}

interface AffiliateData {
  account: {
    account_id: string;
    name: string;
    account_type: string;
    plan_slug: string;
  };
  overview: AffiliateOverview;
  sponsored_accounts: SponsoredAccount[];
}

async function getAffiliateData(): Promise<AffiliateData | { error: string }> {
  const cookieStore = await cookies();
  const token = cookieStore.get('mr_token')?.value;

  if (!token) {
    return { error: 'Not authenticated' };
  }

  try {
    const response = await fetch(`${API_BASE}/v1/affiliate/overview`, {
      headers: {
        'Cookie': `mr_token=${token}`,
      },
      cache: 'no-store',
    });

    if (response.status === 403) {
      return { error: 'not_affiliate' };
    }

    if (!response.ok) {
      return { error: 'Failed to load affiliate data' };
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Failed to fetch affiliate data:', error);
    return { error: 'Failed to load affiliate data' };
  }
}

// Phase 29E: Fetch plan usage for affiliate's own account
async function getPlanUsage() {
  const cookieStore = await cookies();
  const token = cookieStore.get('mr_token')?.value;

  if (!token) return null;

  try {
    const response = await fetch(`${API_BASE}/v1/account/plan-usage`, {
      headers: {
        'Cookie': `mr_token=${token}`,
      },
      cache: 'no-store',
    });

    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch plan usage:', error);
    return null;
  }
}

export default async function AffiliateDashboardPage() {
  const data = await getAffiliateData();
  const planUsage = await getPlanUsage(); // Phase 29E

  // Handle errors
  if ('error' in data) {
    if (data.error === 'not_affiliate') {
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
      );
    }

    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <h1 className="text-2xl font-bold mb-2">Error Loading Affiliate Data</h1>
        <p className="text-muted-foreground max-w-md mb-6">{data.error}</p>
        <Button asChild>
          <a href="/app">Back to Dashboard</a>
        </Button>
      </div>
    );
  }

  // Map fetched data to shell props
  const shellProps: AffiliateDashboardShellProps = {
    overview: data.overview,
    planSummary: planUsage ? {
      plan_name: planUsage.plan.plan_name,
      report_count: planUsage.usage.report_count,
      limit: planUsage.account.monthly_report_limit_override ?? planUsage.plan.monthly_report_limit,
    } : undefined,
    sponsoredAccounts: data.sponsored_accounts,
  };

  return <AffiliateDashboardShell {...shellProps} />;
}


import { cookies } from 'next/headers';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Building2, TrendingUp, Users2, Calendar } from 'lucide-react';
import { InviteAgentModal } from '@/components/invite-agent-modal';

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
        'Authorization': `Bearer ${token}`,
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

function formatDate(dateString: string | null): string {
  if (!dateString) return '—';
  
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now.getTime() - date.getTime());
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export default async function AffiliateDashboardPage() {
  const data = await getAffiliateData();

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Affiliate Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Manage your sponsored agents and track their activity
          </p>
        </div>
        <InviteAgentModal />
      </div>

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sponsored Accounts</CardTitle>
            <Users2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.overview.sponsored_count}</div>
            <p className="text-xs text-muted-foreground">
              Total agents under your sponsorship
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reports This Month</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.overview.total_reports_this_month}</div>
            <p className="text-xs text-muted-foreground">
              Combined reports from all sponsored accounts
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Sponsored Accounts Table */}
      <Card>
        <CardHeader>
          <CardTitle>Sponsored Accounts</CardTitle>
          <CardDescription>
            View and manage your sponsored agent accounts
          </CardDescription>
        </CardHeader>
        <CardContent>
          {data.sponsored_accounts.length === 0 ? (
            <div className="text-center py-12">
              <Users2 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Sponsored Accounts Yet</h3>
              <p className="text-muted-foreground mb-4">
                Start by inviting your first agent
              </p>
              <InviteAgentModal />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-medium text-sm text-muted-foreground">
                      Account Name
                    </th>
                    <th className="text-left py-3 px-4 font-medium text-sm text-muted-foreground">
                      Plan
                    </th>
                    <th className="text-right py-3 px-4 font-medium text-sm text-muted-foreground">
                      Reports This Month
                    </th>
                    <th className="text-left py-3 px-4 font-medium text-sm text-muted-foreground">
                      Last Activity
                    </th>
                    <th className="text-left py-3 px-4 font-medium text-sm text-muted-foreground">
                      Created
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.sponsored_accounts.map((account) => (
                    <tr key={account.account_id} className="border-b hover:bg-muted/50">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <Building2 className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{account.name}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                          {account.plan_slug}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right font-mono">
                        {account.reports_this_month}
                      </td>
                      <td className="py-3 px-4 text-sm text-muted-foreground">
                        {formatDate(account.last_report_at)}
                      </td>
                      <td className="py-3 px-4 text-sm text-muted-foreground">
                        {formatDate(account.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}


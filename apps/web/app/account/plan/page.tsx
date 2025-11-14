import { cookies } from 'next/headers';
import { Suspense } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { AlertCircle, CheckCircle2, TrendingUp, Building2, Calendar } from 'lucide-react';
import { StripeBillingActions } from '@/components/stripe-billing-actions';
import { CheckoutStatusBanner } from '@/components/checkout-status-banner';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://reportscompany.onrender.com';

interface PlanUsageData {
  account: {
    id: string;
    name: string;
    account_type: string;
    plan_slug: string;
    monthly_report_limit_override: number | null;
    sponsor_account_id: string | null;
  };
  plan: {
    plan_slug: string;
    plan_name: string;
    monthly_report_limit: number;
    allow_overage: boolean;
    overage_price_cents: number | null;
  };
  usage: {
    report_count: number;
    period_start: string;
    period_end: string;
  };
  decision: 'ALLOW' | 'ALLOW_WITH_WARNING' | 'BLOCK';
  info: {
    ratio: number;
    message: string;
    can_proceed: boolean;
  };
}

async function getPlanUsage(): Promise<PlanUsageData | { error: string }> {
  const cookieStore = await cookies();
  const token = cookieStore.get('mr_token')?.value;

  if (!token) {
    return { error: 'Not authenticated' };
  }

  try {
    // Use the proxy route which handles authentication cookies properly
    const baseUrl = process.env.NEXT_PUBLIC_WEB_BASE || 'https://reportscompany-web.vercel.app';
    const response = await fetch(`${baseUrl}/api/proxy/v1/account/plan-usage`, {
      headers: {
        'Cookie': `mr_token=${token}`,
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      console.error(`Plan usage fetch failed: ${response.status} ${response.statusText}`);
      return { error: 'Failed to load plan information' };
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Failed to fetch plan usage:', error);
    return { error: 'Failed to load plan information' };
  }
}

function getProgressColor(decision: string): string {
  switch (decision) {
    case 'ALLOW':
      return 'bg-green-500';
    case 'ALLOW_WITH_WARNING':
      return 'bg-yellow-500';
    case 'BLOCK':
      return 'bg-red-500';
    default:
      return 'bg-gray-500';
  }
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export default async function PlanPage() {
  const data = await getPlanUsage();

  // Handle errors
  if ('error' in data) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold tracking-tight">Plan & Usage</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">{data.error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const limit = data.account.monthly_report_limit_override ?? data.plan.monthly_report_limit;
  const progressPercent = Math.min((data.usage.report_count / limit) * 100, 100);
  const isSponsored = data.account.sponsor_account_id !== null && data.plan.plan_slug === 'sponsored_free';

  return (
    <div className="space-y-6">
      {/* Checkout Status Banner */}
      <Suspense fallback={null}>
        <CheckoutStatusBanner />
      </Suspense>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Plan & Usage</h1>
          <p className="text-muted-foreground mt-1">
            Manage your subscription and track your usage
          </p>
        </div>
      </div>

      {/* Plan Summary Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{data.plan.plan_name} Plan</CardTitle>
              <CardDescription>
                {isSponsored ? (
                  <span className="flex items-center gap-2 mt-2">
                    <Badge variant="secondary" className="bg-primary/10 text-primary">
                      Sponsored
                    </Badge>
                    <span className="text-sm">Sponsored by your industry affiliate</span>
                  </span>
                ) : (
                  <span className="text-sm">Current plan: {data.plan.plan_slug}</span>
                )}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Stripe Billing Actions */}
          <StripeBillingActions
            accountType={data.account.account_type}
            planSlug={data.plan.plan_slug}
            isSponsored={isSponsored}
          />
          <div className="grid gap-4 md:grid-cols-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <TrendingUp className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">Monthly Limit</p>
                <p className="text-2xl font-bold">{limit}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Building2 className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">Account Type</p>
                <p className="text-sm font-semibold capitalize">
                  {data.account.account_type.replace('_', ' ').toLowerCase()}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Calendar className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">Billing Period</p>
                <p className="text-sm font-semibold">Monthly</p>
              </div>
            </div>
          </div>

          {data.plan.allow_overage && (
            <div className="p-3 rounded-lg bg-muted/50 border border-border">
              <p className="text-sm text-muted-foreground">
                <strong>Overage allowed:</strong> Additional reports beyond your limit
                {data.plan.overage_price_cents && (
                  <span> at ${(data.plan.overage_price_cents / 100).toFixed(2)} per report</span>
                )}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Usage Meter Card */}
      <Card>
        <CardHeader>
          <CardTitle>Current Usage</CardTitle>
          <CardDescription>
            Period: {formatDate(data.usage.period_start)} – {formatDate(data.usage.period_end)}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Reports Generated</span>
                {data.decision === 'ALLOW' && (
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                )}
                {data.decision === 'ALLOW_WITH_WARNING' && (
                  <AlertCircle className="h-4 w-4 text-yellow-500" />
                )}
                {data.decision === 'BLOCK' && (
                  <AlertCircle className="h-4 w-4 text-red-500" />
                )}
              </div>
              <span className="text-2xl font-bold">
                {data.usage.report_count} / {limit}
              </span>
            </div>

            <div className="space-y-1">
              <div className="h-3 w-full bg-muted rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all ${getProgressColor(data.decision)}`}
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground text-right">
                {progressPercent.toFixed(1)}% of monthly limit
              </p>
            </div>
          </div>

          {data.info.message && (
            <div className={`p-3 rounded-lg border ${
              data.decision === 'ALLOW' 
                ? 'bg-green-500/10 border-green-500/20 text-green-700 dark:text-green-400'
                : data.decision === 'ALLOW_WITH_WARNING'
                ? 'bg-yellow-500/10 border-yellow-500/20 text-yellow-700 dark:text-yellow-400'
                : 'bg-red-500/10 border-red-500/20 text-red-700 dark:text-red-400'
            }`}>
              <p className="text-sm font-medium flex items-center gap-2">
                {data.decision === 'ALLOW_WITH_WARNING' && <AlertCircle className="h-4 w-4" />}
                {data.decision === 'BLOCK' && <AlertCircle className="h-4 w-4" />}
                {data.info.message}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Account Details Card */}
      <Card>
        <CardHeader>
          <CardTitle>Account Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 text-sm">
            <div className="flex items-center justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Account Name</span>
              <span className="font-medium">{data.account.name}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Account ID</span>
              <span className="font-mono text-xs">{data.account.id}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Plan</span>
              <span className="font-medium capitalize">{data.plan.plan_name}</span>
            </div>
            {data.account.monthly_report_limit_override && (
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">Custom Limit Override</span>
                <Badge variant="secondary">{data.account.monthly_report_limit_override} reports/month</Badge>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}


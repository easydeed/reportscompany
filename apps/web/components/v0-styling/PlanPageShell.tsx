import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, CheckCircle2, TrendingUp, Building2, Calendar } from 'lucide-react';
import { StripeBillingActions } from '@/components/stripe-billing-actions';
import { CheckoutStatusBanner } from '@/components/checkout-status-banner';

export type PlanPageShellProps = {
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
};

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

export function PlanPageShell(props: PlanPageShellProps) {
  const { account, plan, usage, decision, info } = props;

  const limit = account.monthly_report_limit_override ?? plan.monthly_report_limit;
  const progressPercent = Math.min((usage.report_count / limit) * 100, 100);
  const isSponsored = account.sponsor_account_id !== null && plan.plan_slug === 'sponsored_free';

  return (
    <div className="space-y-6">
      {/* Checkout Status Banner */}
      <CheckoutStatusBanner />

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
              <CardTitle>{plan.plan_name} Plan</CardTitle>
              <CardDescription>
                {isSponsored ? (
                  <span className="flex items-center gap-2 mt-2">
                    <Badge variant="secondary" className="bg-primary/10 text-primary">
                      Sponsored
                    </Badge>
                    <span className="text-sm">Sponsored by your industry affiliate</span>
                  </span>
                ) : (
                  <span className="text-sm">Current plan: {plan.plan_slug}</span>
                )}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Stripe Billing Actions */}
          <StripeBillingActions
            accountType={account.account_type}
            planSlug={plan.plan_slug}
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
                  {account.account_type.replace('_', ' ').toLowerCase()}
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

          {plan.allow_overage && (
            <div className="p-3 rounded-lg bg-muted/50 border border-border">
              <p className="text-sm text-muted-foreground">
                <strong>Overage allowed:</strong> Additional reports beyond your limit
                {plan.overage_price_cents && (
                  <span> at ${(plan.overage_price_cents / 100).toFixed(2)} per report</span>
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
            Period: {formatDate(usage.period_start)} – {formatDate(usage.period_end)}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Reports Generated</span>
                {decision === 'ALLOW' && (
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                )}
                {decision === 'ALLOW_WITH_WARNING' && (
                  <AlertCircle className="h-4 w-4 text-yellow-500" />
                )}
                {decision === 'BLOCK' && (
                  <AlertCircle className="h-4 w-4 text-red-500" />
                )}
              </div>
              <span className="text-2xl font-bold">
                {usage.report_count} / {limit}
              </span>
            </div>

            <div className="space-y-1">
              <div className="h-3 w-full bg-muted rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all ${getProgressColor(decision)}`}
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground text-right">
                {progressPercent.toFixed(1)}% of monthly limit
              </p>
            </div>
          </div>

          {info.message && (
            <div className={`p-3 rounded-lg border ${
              decision === 'ALLOW' 
                ? 'bg-green-500/10 border-green-500/20 text-green-700 dark:text-green-400'
                : decision === 'ALLOW_WITH_WARNING'
                ? 'bg-yellow-500/10 border-yellow-500/20 text-yellow-700 dark:text-yellow-400'
                : 'bg-red-500/10 border-red-500/20 text-red-700 dark:text-red-400'
            }`}>
              <p className="text-sm font-medium flex items-center gap-2">
                {decision === 'ALLOW_WITH_WARNING' && <AlertCircle className="h-4 w-4" />}
                {decision === 'BLOCK' && <AlertCircle className="h-4 w-4" />}
                {info.message}
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
              <span className="font-medium">{account.name}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Account ID</span>
              <span className="font-mono text-xs">{account.id}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Plan</span>
              <span className="font-medium capitalize">{plan.plan_name}</span>
            </div>
            {account.monthly_report_limit_override && (
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">Custom Limit Override</span>
                <Badge variant="secondary">{account.monthly_report_limit_override} reports/month</Badge>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}


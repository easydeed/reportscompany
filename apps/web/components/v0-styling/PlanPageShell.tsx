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
      return 'bg-emerald-500';
    case 'ALLOW_WITH_WARNING':
      return 'bg-amber-500';
    case 'BLOCK':
      return 'bg-rose-500';
    default:
      return 'bg-muted';
  }
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function PlanPageShell(props: PlanPageShellProps) {
  const { account, plan, usage, decision, info } = props;

  const limit = account.monthly_report_limit_override ?? plan.monthly_report_limit ?? 1;
  const reportCount = usage?.report_count ?? 0;
  const progressPercent = limit > 0 ? Math.min((reportCount / limit) * 100, 100) : 0;
  const isSponsored = account.sponsor_account_id !== null && plan.plan_slug === 'sponsored_free';

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Checkout Status Banner */}
        <CheckoutStatusBanner />

        <div className="space-y-1">
          <h1 className="text-3xl font-display font-bold tracking-tight text-slate-900">Plan & Usage</h1>
          <p className="text-slate-600">
            Track your subscription and monitor report generation
          </p>
        </div>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="space-y-4 pb-4">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <CardTitle className="text-2xl font-display text-slate-900">
                    {plan.plan_name}
                  </CardTitle>
                  {isSponsored && (
                    <Badge className="bg-primary/10 text-primary border-primary/20 font-medium">
                      Sponsored
                    </Badge>
                  )}
                </div>
                <CardDescription className="text-slate-600">
                  {isSponsored 
                    ? 'Sponsored by your industry affiliate partner'
                    : `${formatDate(usage.period_start)} – ${formatDate(usage.period_end)}`
                  }
                </CardDescription>
              </div>
              
              <div className="text-right">
                <div className="text-3xl font-display font-bold text-slate-900">
                  {usage.report_count}
                  <span className="text-lg text-slate-400 font-normal"> / {limit}</span>
                </div>
                <p className="text-xs text-slate-500 mt-1">Reports this month</p>
              </div>
            </div>

            <div className="space-y-2">
              <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${getProgressColor(decision)}`}
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500">{progressPercent.toFixed(0)}% used</span>
                {decision === 'ALLOW' && (
                  <span className="flex items-center gap-1 text-emerald-600 font-medium">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Available
                  </span>
                )}
                {decision === 'ALLOW_WITH_WARNING' && (
                  <span className="flex items-center gap-1 text-amber-600 font-medium">
                    <AlertCircle className="h-3.5 w-3.5" />
                    Approaching Limit
                  </span>
                )}
                {decision === 'BLOCK' && (
                  <span className="flex items-center gap-1 text-rose-600 font-medium">
                    <AlertCircle className="h-3.5 w-3.5" />
                    Limit Reached
                  </span>
                )}
              </div>
            </div>

            {info.message && (
              <div className={`px-4 py-3 rounded-lg border text-sm font-medium ${
                decision === 'ALLOW' 
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : decision === 'ALLOW_WITH_WARNING'
                  ? 'bg-amber-50 border-amber-200 text-amber-800'
                  : 'bg-rose-50 border-rose-200 text-rose-800'
              }`}>
                {info.message}
              </div>
            )}
          </CardHeader>

          <CardContent className="space-y-6 pt-4 border-t border-slate-100">
            <StripeBillingActions
              accountType={account.account_type}
              planSlug={plan.plan_slug}
              isSponsored={isSponsored}
            />

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-primary/10">
                  <TrendingUp className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wide font-medium">Monthly Limit</p>
                  <p className="text-xl font-display font-bold text-slate-900 mt-1">{limit}</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-primary/10">
                  <Building2 className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wide font-medium">Account Type</p>
                  <p className="text-sm font-semibold text-slate-900 capitalize mt-1">
                    {account.account_type.replace('_', ' ')}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-primary/10">
                  <Calendar className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wide font-medium">Billing Cycle</p>
                  <p className="text-sm font-semibold text-slate-900 mt-1">Monthly</p>
                </div>
              </div>
            </div>

            {plan.allow_overage && (
              <div className="px-4 py-3 rounded-lg bg-slate-50 border border-slate-200">
                <p className="text-sm text-slate-700">
                  <span className="font-semibold">Overage billing enabled:</span> Additional reports beyond your limit
                  {plan.overage_price_cents && (
                    <span> are billed at <span className="font-semibold text-slate-900">${(plan.overage_price_cents / 100).toFixed(2)}</span> per report</span>
                  )}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg font-display text-slate-900">Account Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between py-3 border-b border-slate-100">
                <span className="text-sm text-slate-600">Account Name</span>
                <span className="font-medium text-slate-900">{account.name}</span>
              </div>
              <div className="flex items-center justify-between py-3 border-b border-slate-100">
                <span className="text-sm text-slate-600">Account ID</span>
                <span className="font-mono text-xs text-slate-500">{account.id}</span>
              </div>
              <div className="flex items-center justify-between py-3 border-b border-slate-100">
                <span className="text-sm text-slate-600">Plan Type</span>
                <span className="font-medium text-slate-900 capitalize">{plan.plan_name}</span>
              </div>
              {account.monthly_report_limit_override && (
                <div className="flex items-center justify-between py-3">
                  <span className="text-sm text-slate-600">Custom Limit</span>
                  <Badge variant="secondary" className="bg-slate-100 text-slate-900 border-slate-200">
                    {account.monthly_report_limit_override} reports/month
                  </Badge>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

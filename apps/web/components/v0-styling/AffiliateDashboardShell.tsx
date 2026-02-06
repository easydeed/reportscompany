import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Building2, TrendingUp, Users2 } from 'lucide-react';
import { InviteAgentModal } from '@/components/invite-agent-modal';

export type SponsoredAccount = {
  account_id: string;
  name: string;
  plan_slug: string;
  reports_this_month: number;
  last_report_at: string | null;
  created_at: string;
};

export type Overview = {
  sponsored_count: number;
  total_reports_this_month: number;
};

export type AffiliateDashboardShellProps = {
  overview: Overview;
  planSummary?: {
    plan_name: string;
    report_count: number;
    limit: number;
  };
  sponsoredAccounts: SponsoredAccount[];
};

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

export function AffiliateDashboardShell(props: AffiliateDashboardShellProps) {
  const { overview, planSummary, sponsoredAccounts } = props;

  return (
    <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">
              Affiliate Dashboard
            </h1>
            <p className="text-slate-600 mt-1.5 text-[15px]">
              Manage your sponsored agents and track their activity
            </p>
          </div>
          <InviteAgentModal />
        </div>

        {planSummary && (
          <Card className="border-indigo-200/60 bg-gradient-to-br from-indigo-50/50 to-white shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
              <div>
                <CardTitle className="text-base font-semibold text-slate-900">
                  Your Affiliate Plan
                </CardTitle>
                <div className="mt-3">
                  <div className="text-2xl font-display font-bold text-indigo-600">
                    {planSummary.plan_name}
                  </div>
                  <p className="text-sm text-slate-600 mt-1">
                    {planSummary.report_count} of {planSummary.limit} reports used this month
                  </p>
                </div>
              </div>
              <div className="rounded-xl bg-indigo-100 p-2.5">
                <TrendingUp className="h-5 w-5 text-indigo-600" />
              </div>
            </CardHeader>
          </Card>
        )}

        <div className="grid gap-6 md:grid-cols-2">
          <Card className="border-slate-200/60 bg-white shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
              <div>
                <CardTitle className="text-sm font-medium text-slate-600">
                  Sponsored Accounts
                </CardTitle>
                <div className="mt-2">
                  <div className="text-3xl font-display font-bold text-slate-900">
                    {overview.sponsored_count}
                  </div>
                </div>
              </div>
              <div className="rounded-xl bg-slate-100 p-2.5">
                <Users2 className="h-5 w-5 text-slate-600" />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-600">
                Total agents under your sponsorship
              </p>
            </CardContent>
          </Card>

          <Card className="border-slate-200/60 bg-white shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
              <div>
                <CardTitle className="text-sm font-medium text-slate-600">
                  Reports This Month
                </CardTitle>
                <div className="mt-2">
                  <div className="text-3xl font-display font-bold text-slate-900">
                    {overview.total_reports_this_month}
                  </div>
                </div>
              </div>
              <div className="rounded-xl bg-orange-100 p-2.5">
                <TrendingUp className="h-5 w-5 text-orange-600" />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-600">
                Combined reports from all sponsored accounts
              </p>
            </CardContent>
          </Card>
        </div>

        <Card className="border-slate-200/60 bg-white shadow-sm">
          <CardHeader className="border-b border-slate-100">
            <CardTitle className="text-lg font-semibold text-slate-900">
              Sponsored Accounts
            </CardTitle>
            <CardDescription className="text-slate-600">
              View and manage your sponsored agent accounts
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {sponsoredAccounts.length === 0 ? (
              <div className="text-center py-16 px-4">
                <div className="rounded-2xl bg-slate-100 w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <Users2 className="h-8 w-8 text-slate-400" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">
                  No Sponsored Accounts Yet
                </h3>
                <p className="text-slate-600 mb-6 max-w-sm mx-auto">
                  Start by inviting your first agent to begin tracking their activity
                </p>
                <InviteAgentModal />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-100 bg-slate-50/50">
                      <th className="text-left py-3.5 px-6 font-medium text-xs uppercase tracking-wider text-slate-600">
                        Account Name
                      </th>
                      <th className="text-left py-3.5 px-6 font-medium text-xs uppercase tracking-wider text-slate-600">
                        Plan
                      </th>
                      <th className="text-right py-3.5 px-6 font-medium text-xs uppercase tracking-wider text-slate-600">
                        Reports
                      </th>
                      <th className="text-left py-3.5 px-6 font-medium text-xs uppercase tracking-wider text-slate-600">
                        Last Activity
                      </th>
                      <th className="text-left py-3.5 px-6 font-medium text-xs uppercase tracking-wider text-slate-600">
                        Created
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {sponsoredAccounts.map((account) => (
                      <tr key={account.account_id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="py-4 px-6">
                          <div className="flex items-center gap-3">
                            <div className="rounded-lg bg-indigo-100 p-2">
                              <Building2 className="h-4 w-4 text-indigo-600" />
                            </div>
                            <span className="font-medium text-slate-900">{account.name}</span>
                          </div>
                        </td>
                        <td className="py-4 px-6">
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-700 border border-indigo-200/50">
                            {account.plan_slug}
                          </span>
                        </td>
                        <td className="py-4 px-6 text-right">
                          <span className="font-mono font-semibold text-slate-900">
                            {account.reports_this_month}
                          </span>
                        </td>
                        <td className="py-4 px-6 text-sm text-slate-600">
                          {formatDate(account.last_report_at)}
                        </td>
                        <td className="py-4 px-6 text-sm text-slate-600">
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

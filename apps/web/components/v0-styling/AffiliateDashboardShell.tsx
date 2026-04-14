import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Building2, TrendingUp, Users2, RotateCcw, Loader2 } from 'lucide-react';
import { InviteAgentModal } from '@/components/invite-agent-modal';
import { BulkInviteModal } from '@/components/affiliate/bulk-invite-modal';
import { PageHeader } from '@/components/page-header';
import { MetricCard } from '@/components/metric-card';
import { useToast } from '@/components/ui/use-toast';

export type SponsoredAccount = {
  account_id: string;
  name: string;
  plan_slug: string;
  reports_this_month: number;
  last_report_at: string | null;
  created_at: string;
  status?: 'pending' | 'active' | 'deactivated';
  email?: string;
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

function StatusBadge({ status }: { status: string }) {
  switch (status) {
    case 'active':
      return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 text-[11px]">Active</Badge>;
    case 'deactivated':
      return <Badge variant="outline" className="bg-gray-100 text-gray-600 border-gray-200 text-[11px]">Deactivated</Badge>;
    case 'pending':
    default:
      return <Badge variant="outline" className="bg-yellow-50 text-yellow-800 border-yellow-200 text-[11px]">Pending</Badge>;
  }
}

function ResendButton({ email }: { email: string }) {
  const [sending, setSending] = useState(false);
  const { toast } = useToast();

  async function resend() {
    setSending(true);
    try {
      const res = await fetch('/api/proxy/v1/affiliate/invite-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ name: '', email }),
      });
      if (res.ok) {
        toast({ title: 'Invite resent', description: `A new invitation was sent to ${email}` });
      } else {
        const data = await res.json().catch(() => ({}));
        toast({ title: 'Failed to resend', description: data.detail || 'Could not resend invite', variant: 'destructive' });
      }
    } catch {
      toast({ title: 'Error', description: 'Failed to resend invitation', variant: 'destructive' });
    } finally {
      setSending(false);
    }
  }

  return (
    <Button variant="ghost" size="sm" onClick={resend} disabled={sending} className="h-7 px-2 text-xs text-muted-foreground hover:text-foreground">
      {sending ? <Loader2 className="h-3 w-3 animate-spin" /> : <RotateCcw className="h-3 w-3 mr-1" />}
      Resend
    </Button>
  );
}

export function AffiliateDashboardShell(props: AffiliateDashboardShellProps) {
  const { overview, planSummary, sponsoredAccounts } = props;

  return (
    <div className="space-y-5">
        <PageHeader
          title="Affiliate Dashboard"
          description="Manage your sponsored agents and track their activity"
          action={
            <div className="flex items-center gap-2">
              <BulkInviteModal />
              <InviteAgentModal />
            </div>
          }
        />

        {planSummary && (
          <Card className="border-indigo-200/60 bg-gradient-to-br from-indigo-50/50 to-white shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
              <div>
                <CardTitle className="text-base font-semibold text-foreground">
                  Your Affiliate Plan
                </CardTitle>
                <div className="mt-3">
                  <div className="text-2xl font-display font-bold text-indigo-600">
                    {planSummary.plan_name}
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
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

        <div className="grid gap-3 md:grid-cols-2">
          <MetricCard label="Sponsored Accounts" value={overview.sponsored_count} icon={<Users2 className="w-4 h-4" />} index={0} />
          <MetricCard label="Reports This Month" value={overview.total_reports_this_month} icon={<TrendingUp className="w-4 h-4" />} index={1} />
        </div>

        <Card className="border-border bg-card shadow-sm">
          <CardHeader className="border-b border-border">
            <CardTitle className="text-lg font-semibold text-foreground">
              Sponsored Accounts
            </CardTitle>
            <CardDescription className="text-muted-foreground">
              View and manage your sponsored agent accounts
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {sponsoredAccounts.length === 0 ? (
              <div className="text-center py-16 px-4">
                <div className="rounded-2xl bg-muted w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <Users2 className="h-8 w-8 text-muted-foreground/60" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  No Sponsored Accounts Yet
                </h3>
                <p className="text-muted-foreground mb-6 max-w-sm mx-auto">
                  Start by inviting your first agent to begin tracking their activity
                </p>
                <InviteAgentModal />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border bg-muted/40">
                      <th className="text-left py-2.5 px-6 text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em]">
                        Account Name
                      </th>
                      <th className="text-left py-2.5 px-6 text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em]">
                        Plan
                      </th>
                      <th className="text-right py-2.5 px-6 text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em]">
                        Reports
                      </th>
                      <th className="text-left py-2.5 px-6 text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em]">
                        Status
                      </th>
                      <th className="text-left py-2.5 px-6 text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em]">
                        Last Activity
                      </th>
                      <th className="text-left py-2.5 px-6 text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em]">
                        Created
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {sponsoredAccounts.map((account) => (
                      <tr key={account.account_id} className="hover:bg-muted/30 transition-colors">
                        <td className="py-4 px-6">
                          <div className="flex items-center gap-3">
                            <div className="rounded-lg bg-primary/10 p-2">
                              <Building2 className="h-4 w-4 text-primary" />
                            </div>
                            <span className="font-medium text-foreground">{account.name}</span>
                          </div>
                        </td>
                        <td className="py-4 px-6">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
                            {account.plan_slug}
                          </span>
                        </td>
                        <td className="py-4 px-6 text-right">
                          <span className="font-semibold text-foreground">
                            {account.reports_this_month}
                          </span>
                        </td>
                        <td className="py-4 px-6">
                          <div className="flex items-center gap-2">
                            <StatusBadge status={account.status || 'pending'} />
                            {account.status === 'pending' && account.email && (
                              <ResendButton email={account.email} />
                            )}
                          </div>
                        </td>
                        <td className="py-4 px-6 text-sm text-muted-foreground">
                          {formatDate(account.last_report_at)}
                        </td>
                        <td className="py-4 px-6 text-sm text-muted-foreground">
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

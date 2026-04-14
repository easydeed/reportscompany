import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Building2, TrendingUp, Users2, RotateCcw, Loader2,
  MoreHorizontal, Eye, UserX, UserCheck, Trash2, Send,
} from 'lucide-react';
import { InviteAgentModal } from '@/components/invite-agent-modal';
import { BulkInviteModal } from '@/components/affiliate/bulk-invite-modal';
import { PageHeader } from '@/components/page-header';
import { MetricCard } from '@/components/metric-card';
import { useToast } from '@/components/ui/use-toast';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export type SponsoredAccount = {
  account_id: string;
  name: string;
  plan_slug: string;
  reports_this_month: number;
  last_report_at: string | null;
  created_at: string;
  status?: 'pending' | 'active' | 'deactivated';
  email?: string;
  last_invite_sent?: string | null;
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
  onRefresh?: () => void;
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

function formatRelativeTime(dateString: string | null): string {
  if (!dateString) return 'Never';
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60_000);
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
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

export function AffiliateDashboardShell(props: AffiliateDashboardShellProps) {
  const { overview, planSummary, sponsoredAccounts, onRefresh } = props;
  const { toast } = useToast();

  const [resendModal, setResendModal] = useState<{ open: boolean; agent: SponsoredAccount | null }>({ open: false, agent: null });
  const [resending, setResending] = useState(false);

  const [confirmModal, setConfirmModal] = useState<{
    open: boolean;
    agent: SponsoredAccount | null;
    action: 'deactivate' | 'reactivate' | 'unsponsor' | null;
  }>({ open: false, agent: null, action: null });
  const [actionLoading, setActionLoading] = useState(false);

  async function handleResendInvite(agent: SponsoredAccount) {
    setResending(true);
    try {
      const res = await fetch('/api/proxy/v1/affiliate/resend-invite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email: agent.email }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        toast({ title: 'Invitation sent', description: `New invitation sent to ${agent.email}` });
        setResendModal({ open: false, agent: null });
        onRefresh?.();
      } else {
        const detail = typeof data.detail === 'string' ? data.detail : data.detail?.message || 'Failed to resend invitation';
        toast({ title: 'Error', description: detail, variant: 'destructive' });
      }
    } catch {
      toast({ title: 'Error', description: 'Network error — please try again', variant: 'destructive' });
    } finally {
      setResending(false);
    }
  }

  async function handleAccountAction() {
    if (!confirmModal.agent || !confirmModal.action) return;
    setActionLoading(true);
    const { agent, action } = confirmModal;
    const endpoint = `/api/proxy/v1/affiliate/accounts/${agent.account_id}/${action}`;
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        const labels: Record<string, string> = {
          deactivate: 'Account deactivated',
          reactivate: 'Account reactivated',
          unsponsor: 'Sponsorship removed',
        };
        toast({ title: labels[action] || 'Done', description: `${agent.name} updated successfully` });
        setConfirmModal({ open: false, agent: null, action: null });
        onRefresh?.();
      } else {
        const detail = typeof data.detail === 'string' ? data.detail : data.detail?.message || 'Action failed';
        toast({ title: 'Error', description: detail, variant: 'destructive' });
      }
    } catch {
      toast({ title: 'Error', description: 'Network error — please try again', variant: 'destructive' });
    } finally {
      setActionLoading(false);
    }
  }

  const actionLabels: Record<string, { title: string; description: string; confirm: string; variant: 'default' | 'destructive' }> = {
    deactivate: {
      title: 'Deactivate Account',
      description: 'This will suspend the agent\'s account. They will lose access until reactivated.',
      confirm: 'Deactivate',
      variant: 'destructive',
    },
    reactivate: {
      title: 'Reactivate Account',
      description: 'This will restore the agent\'s account access.',
      confirm: 'Reactivate',
      variant: 'default',
    },
    unsponsor: {
      title: 'Remove Sponsorship',
      description: 'This will remove your sponsorship and downgrade the agent to the free plan. This cannot be undone.',
      confirm: 'Remove',
      variant: 'destructive',
    },
  };

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
                        Last Invited
                      </th>
                      <th className="text-left py-2.5 px-6 text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em]">
                        Last Activity
                      </th>
                      <th className="text-left py-2.5 px-6 text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em]">
                        Created
                      </th>
                      <th className="text-right py-2.5 px-6 text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em]">
                        Actions
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
                            <div>
                              <span className="font-medium text-foreground">{account.name}</span>
                              {account.email && (
                                <p className="text-xs text-muted-foreground">{account.email}</p>
                              )}
                            </div>
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
                          <StatusBadge status={account.status || 'pending'} />
                        </td>
                        <td className="py-4 px-6 text-sm text-muted-foreground">
                          {account.status === 'pending' && account.last_invite_sent
                            ? formatRelativeTime(account.last_invite_sent)
                            : '—'
                          }
                        </td>
                        <td className="py-4 px-6 text-sm text-muted-foreground">
                          {formatDate(account.last_report_at)}
                        </td>
                        <td className="py-4 px-6 text-sm text-muted-foreground">
                          {formatDate(account.created_at)}
                        </td>
                        <td className="py-4 px-6 text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              {account.status === 'pending' && (
                                <>
                                  <DropdownMenuItem onClick={() => setResendModal({ open: true, agent: account })}>
                                    <Send className="h-4 w-4 mr-2" />
                                    Resend Invite
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem
                                    className="text-destructive focus:text-destructive"
                                    onClick={() => setConfirmModal({ open: true, agent: account, action: 'deactivate' })}
                                  >
                                    <UserX className="h-4 w-4 mr-2" />
                                    Cancel Invitation
                                  </DropdownMenuItem>
                                </>
                              )}
                              {account.status === 'active' && (
                                <>
                                  <DropdownMenuItem onClick={() => window.open(`/app/admin/accounts/${account.account_id}`, '_blank')}>
                                    <Eye className="h-4 w-4 mr-2" />
                                    View Details
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem
                                    className="text-destructive focus:text-destructive"
                                    onClick={() => setConfirmModal({ open: true, agent: account, action: 'deactivate' })}
                                  >
                                    <UserX className="h-4 w-4 mr-2" />
                                    Deactivate
                                  </DropdownMenuItem>
                                </>
                              )}
                              {account.status === 'deactivated' && (
                                <>
                                  <DropdownMenuItem onClick={() => setConfirmModal({ open: true, agent: account, action: 'reactivate' })}>
                                    <UserCheck className="h-4 w-4 mr-2" />
                                    Reactivate
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem
                                    className="text-destructive focus:text-destructive"
                                    onClick={() => setConfirmModal({ open: true, agent: account, action: 'unsponsor' })}
                                  >
                                    <Trash2 className="h-4 w-4 mr-2" />
                                    Remove
                                  </DropdownMenuItem>
                                </>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Resend Invitation Modal */}
        <Dialog open={resendModal.open} onOpenChange={(o) => { if (!o) setResendModal({ open: false, agent: null }); }}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Resend Invitation</DialogTitle>
              <DialogDescription>
                Send a new invitation email to this agent.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3 py-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                  <span className="text-sm font-semibold text-primary">
                    {resendModal.agent?.name?.[0]?.toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-sm font-medium">{resendModal.agent?.name}</p>
                  <p className="text-sm text-muted-foreground">{resendModal.agent?.email}</p>
                </div>
              </div>

              {resendModal.agent?.last_invite_sent && (
                <p className="text-xs text-muted-foreground">
                  Last sent: {new Date(resendModal.agent.last_invite_sent).toLocaleDateString()} at {new Date(resendModal.agent.last_invite_sent).toLocaleTimeString()}
                </p>
              )}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setResendModal({ open: false, agent: null })} disabled={resending}>
                Cancel
              </Button>
              <Button onClick={() => resendModal.agent && handleResendInvite(resendModal.agent)} disabled={resending}>
                {resending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Send className="h-4 w-4 mr-2" />}
                Send Invitation
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Confirm Action Modal (deactivate / reactivate / unsponsor) */}
        <Dialog open={confirmModal.open} onOpenChange={(o) => { if (!o) setConfirmModal({ open: false, agent: null, action: null }); }}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>{confirmModal.action ? actionLabels[confirmModal.action]?.title : ''}</DialogTitle>
              <DialogDescription>
                {confirmModal.action ? actionLabels[confirmModal.action]?.description : ''}
              </DialogDescription>
            </DialogHeader>

            <div className="flex items-center gap-3 py-4">
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                <span className="text-sm font-semibold text-primary">
                  {confirmModal.agent?.name?.charAt(0)}
                </span>
              </div>
              <div>
                <p className="text-sm font-medium">{confirmModal.agent?.name}</p>
                {confirmModal.agent?.email && (
                  <p className="text-sm text-muted-foreground">{confirmModal.agent.email}</p>
                )}
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setConfirmModal({ open: false, agent: null, action: null })} disabled={actionLoading}>
                Cancel
              </Button>
              <Button
                variant={confirmModal.action ? actionLabels[confirmModal.action]?.variant : 'default'}
                onClick={handleAccountAction}
                disabled={actionLoading}
              >
                {actionLoading && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                {confirmModal.action ? actionLabels[confirmModal.action]?.confirm : ''}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
    </div>
  );
}

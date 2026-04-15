'use client'

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Building2, TrendingUp, Users2, Loader2,
  MoreHorizontal, UserX, UserCheck, Trash2, Send, Eye,
} from 'lucide-react';
import { InviteAgentModal } from '@/components/invite-agent-modal';
import { BulkInviteModal } from '@/components/affiliate/bulk-invite-modal';
import { PageHeader } from '@/components/page-header';
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

export type AgentMetrics = {
  total_agents: number;
  total_agent_reports: number;
  active_agents: number;
  active_agents_total: number;
  agents_at_limit: number;
};

export type AffiliateDashboardShellProps = {
  overview: Overview;
  metrics?: AgentMetrics;
  sponsoredAccounts: SponsoredAccount[];
  onRefresh?: () => void;
  isCompanyRep?: boolean;
  companyName?: string;
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
  const { overview, metrics: rawMetrics, sponsoredAccounts, onRefresh, isCompanyRep = false, companyName = '' } = props;
  const router = useRouter();
  const metrics: AgentMetrics = rawMetrics || {
    total_agents: overview.sponsored_count,
    total_agent_reports: overview.total_reports_this_month,
    active_agents: 0,
    active_agents_total: overview.sponsored_count,
    agents_at_limit: 0,
  };
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
      title: isCompanyRep ? 'Remove from Book' : 'Remove Sponsorship',
      description: isCompanyRep
        ? 'This will remove the agent from your book and downgrade them to the free plan. This cannot be undone.'
        : 'This will remove your sponsorship and downgrade the agent to the free plan. This cannot be undone.',
      confirm: isCompanyRep ? 'Remove from Book' : 'Remove',
      variant: 'destructive',
    },
  };

  return (
    <div className="space-y-5">
        <PageHeader
          title={isCompanyRep ? "My Agents" : "Affiliate Dashboard"}
          description={isCompanyRep
            ? `${companyName}${companyName ? ' • ' : ''}Manage your agents and track their activity`
            : "Manage your trial agents and track their activity"}
          action={
            <div className="flex items-center gap-2">
              <BulkInviteModal />
              <InviteAgentModal isCompanyRep={isCompanyRep} />
            </div>
          }
        />

        <Card className="border-indigo-200/60 bg-gradient-to-br from-indigo-50/50 to-white shadow-sm">
          <div className="p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold">{companyName || 'My Agents'}</p>
                <p className="text-xs text-muted-foreground">
                  {isCompanyRep ? 'Title Rep Dashboard' : 'Affiliate Dashboard'}
                </p>
              </div>
              <div className="rounded-xl bg-indigo-100 p-2.5">
                <TrendingUp className="h-5 w-5 text-indigo-600" />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="text-center p-2 bg-muted/30 rounded-lg">
                <p className="text-xl font-bold">{metrics.total_agents}</p>
                <p className="text-[10px] text-muted-foreground uppercase">Agents</p>
              </div>
              <div className="text-center p-2 bg-muted/30 rounded-lg">
                <p className="text-xl font-bold">{metrics.total_agent_reports}</p>
                <p className="text-[10px] text-muted-foreground uppercase">Reports</p>
              </div>
              <div className="text-center p-2 bg-muted/30 rounded-lg">
                <p className="text-xl font-bold">{metrics.active_agents}/{metrics.active_agents_total}</p>
                <p className="text-[10px] text-muted-foreground uppercase">Active (30d)</p>
              </div>
            </div>

            {metrics.agents_at_limit > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-center dark:bg-amber-950/30 dark:border-amber-800">
                <p className="text-sm text-amber-800 dark:text-amber-300 font-medium">
                  {metrics.agents_at_limit} agent{metrics.agents_at_limit > 1 ? 's' : ''} at their report limit
                </p>
              </div>
            )}
          </div>
        </Card>

        <Card className="border-border bg-card shadow-sm">
          <CardHeader className="border-b border-border">
            <CardTitle className="text-lg font-semibold text-foreground">
              {isCompanyRep ? 'My Agents' : 'Trial Agents'}
            </CardTitle>
            <CardDescription className="text-muted-foreground">
              {isCompanyRep ? 'View and manage the agents in your book' : 'View and manage your trial agent accounts'}
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {sponsoredAccounts.length === 0 ? (
              <div className="text-center py-16 px-4">
                <div className="rounded-2xl bg-muted w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <Users2 className="h-8 w-8 text-muted-foreground/60" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  {isCompanyRep ? 'No Agents Yet' : 'No Trial Agents Yet'}
                </h3>
                <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                  {isCompanyRep
                    ? <>Use the <strong>Invite Agent</strong> button above to add your first agent.</>
                    : <>Use the <strong>Invite Agent</strong> button above to start tracking agent activity.</>
                  }
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border bg-muted/40">
                      <th className="text-left py-2.5 px-6 text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em]">
                        Agent
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
                              {account.status === 'active' ? (
                                <Link
                                  href={`/app/affiliate/agents/${account.account_id}`}
                                  className="font-medium text-foreground hover:text-primary hover:underline transition-colors"
                                >
                                  {account.name}
                                </Link>
                              ) : (
                                <span className="font-medium text-foreground">{account.name}</span>
                              )}
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
                                  <DropdownMenuItem
                                    onClick={() => router.push(`/app/affiliate/agents/${account.account_id}`)}
                                  >
                                    <Eye className="h-4 w-4 mr-2" />
                                    View Reports &amp; Schedules
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
                                    {isCompanyRep ? 'Remove from Book' : 'Remove'}
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
                  {confirmModal.agent?.name?.[0]?.toUpperCase()}
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

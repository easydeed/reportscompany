'use client'

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Building2,
  Users,
  FileText,
  ArrowLeft,
  Mail,
  Globe,
  Calendar,
  UserPlus,
  ExternalLink,
  CheckCircle,
  XCircle,
  FileUp,
  User,
  AlertTriangle,
  Send,
  Loader2,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { InviteAgentForm } from "./invite-agent-form"
import { AffiliateActions } from "./affiliate-actions"
import { BulkImportForm } from "./bulk-import-form"
import { AgentHeadshotUpload } from "./agent-headshot-upload"
import { EditBrandingModal } from "./edit-branding-modal"

interface Agent {
  account_id: string
  name: string
  slug: string
  plan_slug: string
  is_active: boolean
  created_at: string
  email: string
  first_name: string | null
  last_name: string | null
  avatar_url: string | null
  reports_this_month: number
  last_report_at: string | null
}

interface AffiliateDetail {
  account_id: string
  name: string
  slug: string
  account_type: string
  plan_slug: string
  is_active: boolean
  created_at: string
  branding: {
    brand_display_name: string | null
    logo_url: string | null
    primary_color: string | null
    accent_color: string | null
    rep_photo_url: string | null
    contact_line1: string | null
    contact_line2: string | null
    website_url: string | null
  }
  admin_user?: {
    user_id: string
    email: string
    first_name: string | null
    last_name: string | null
    is_active: boolean
    created_at: string
    status: 'pending' | 'active' | 'deactivated'
    last_invite_sent: string | null
  }
  agents: Agent[]
  agent_count: number
  reports_this_month: number
}

function formatRelativeTime(dateString: string | null): string {
  if (!dateString) return 'Never'
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60_000)
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function AdminStatusBadge({ status }: { status: string }) {
  switch (status) {
    case 'active':
      return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 text-[11px]"><CheckCircle className="h-3 w-3 mr-1" />Active</Badge>
    case 'deactivated':
      return <Badge variant="outline" className="bg-gray-100 text-gray-600 border-gray-200 text-[11px]"><XCircle className="h-3 w-3 mr-1" />Deactivated</Badge>
    case 'pending':
    default:
      return <Badge variant="outline" className="bg-yellow-50 text-yellow-800 border-yellow-200 text-[11px]">Pending</Badge>
  }
}

export default function AffiliateDetailPage() {
  const params = useParams()
  const id = params.id as string
  const [affiliate, setAffiliate] = useState<AffiliateDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const { toast } = useToast()

  // Invite admin modal
  const [inviteAdminOpen, setInviteAdminOpen] = useState(false)
  const [inviteForm, setInviteForm] = useState({ email: '', first_name: '', last_name: '' })
  const [inviteSubmitting, setInviteSubmitting] = useState(false)

  // Resend invite loading
  const [resending, setResending] = useState(false)

  async function fetchData() {
    try {
      const res = await fetch(`/api/proxy/v1/admin/affiliates/${id}`, {
        credentials: 'include',
      })
      if (!res.ok) {
        setError(true)
        return
      }
      setAffiliate(await res.json())
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [id])

  async function handleInviteAdmin(e: React.FormEvent) {
    e.preventDefault()
    if (!inviteForm.email || !inviteForm.first_name || !inviteForm.last_name) return
    setInviteSubmitting(true)
    try {
      const res = await fetch(`/api/proxy/v1/admin/affiliates/${id}/invite-admin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(inviteForm),
      })
      const data = await res.json()
      if (res.ok) {
        toast({ title: 'Admin invited', description: `Invitation sent to ${inviteForm.email}` })
        setInviteAdminOpen(false)
        setInviteForm({ email: '', first_name: '', last_name: '' })
        fetchData()
      } else {
        const detail = typeof data.detail === 'string' ? data.detail : data.detail?.message || 'Failed to invite admin'
        toast({ title: 'Error', description: detail, variant: 'destructive' })
      }
    } catch {
      toast({ title: 'Error', description: 'Network error — please try again', variant: 'destructive' })
    } finally {
      setInviteSubmitting(false)
    }
  }

  async function handleResendAdminInvite() {
    if (!affiliate?.admin_user) return
    setResending(true)
    try {
      const res = await fetch(`/api/proxy/v1/admin/affiliates/${id}/invite-admin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          email: affiliate.admin_user.email,
          first_name: affiliate.admin_user.first_name || '',
          last_name: affiliate.admin_user.last_name || '',
        }),
      })
      const data = await res.json()
      if (res.ok) {
        toast({ title: 'Invitation resent', description: `New invitation sent to ${affiliate.admin_user.email}` })
        fetchData()
      } else {
        const detail = typeof data.detail === 'string' ? data.detail : data.detail?.message || 'Failed to resend invitation'
        toast({ title: 'Error', description: detail, variant: 'destructive' })
      }
    } catch {
      toast({ title: 'Error', description: 'Network error — please try again', variant: 'destructive' })
    } finally {
      setResending(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded" />
          <Skeleton className="h-12 w-12 rounded" />
          <div>
            <Skeleton className="h-9 w-48 mb-2" />
            <Skeleton className="h-5 w-32" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <Card key={i}><CardContent className="pt-6"><Skeleton className="h-8 w-16" /></CardContent></Card>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card><CardContent className="pt-6"><Skeleton className="h-24 w-full" /></CardContent></Card>
          <Card className="lg:col-span-2"><CardContent className="pt-6"><Skeleton className="h-24 w-full" /></CardContent></Card>
        </div>
        <Card><CardContent className="pt-6"><Skeleton className="h-48 w-full" /></CardContent></Card>
      </div>
    )
  }

  if (error || !affiliate) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 mx-auto text-red-500 mb-4" />
        <h3 className="text-lg font-semibold mb-2">Affiliate not found</h3>
        <Link href="/app/admin/affiliates">
          <Button variant="outline">Back to Affiliates</Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/app/admin/affiliates">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div className="flex items-center gap-4">
            {affiliate.branding.logo_url ? (
              <img
                src={affiliate.branding.logo_url}
                alt={affiliate.name}
                className="h-12 w-12 rounded object-contain bg-muted"
              />
            ) : (
              <div
                className="h-12 w-12 rounded flex items-center justify-center text-white text-lg font-bold"
                style={{ backgroundColor: affiliate.branding.primary_color || '#7C3AED' }}
              >
                {affiliate.name.charAt(0)}
              </div>
            )}
            <div>
              <h1 className="text-3xl font-display font-bold text-foreground">{affiliate.name}</h1>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant={affiliate.is_active ? "default" : "secondary"}>
                  {affiliate.is_active ? "Active" : "Inactive"}
                </Badge>
                <Badge variant="outline">{affiliate.plan_slug}</Badge>
              </div>
            </div>
          </div>
        </div>
        <AffiliateActions affiliate={affiliate} />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Agents</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{affiliate.agent_count}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reports/Month</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{affiliate.reports_this_month}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Created</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {affiliate.created_at
                ? new Date(affiliate.created_at).toLocaleDateString()
                : '-'}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Website</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {affiliate.branding.website_url ? (
              <a
                href={affiliate.branding.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-primary hover:underline flex items-center gap-1"
              >
                Visit
                <ExternalLink className="h-3 w-3" />
              </a>
            ) : (
              <span className="text-muted-foreground">Not set</span>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Admin User */}
        <Card className="bg-card border border-border rounded-xl shadow-sm">
          <div className="px-5 py-3 border-b border-border bg-muted/30">
            <h3 className="text-sm font-semibold">Company Admin</h3>
          </div>
          <div className="p-5">
            {affiliate.admin_user ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                      <span className="text-sm font-semibold text-primary">
                        {(affiliate.admin_user.first_name?.[0] || affiliate.admin_user.email[0])?.toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm font-medium">
                        {affiliate.admin_user.first_name || affiliate.admin_user.last_name
                          ? `${affiliate.admin_user.first_name || ''} ${affiliate.admin_user.last_name || ''}`.trim()
                          : affiliate.admin_user.email}
                      </p>
                      <p className="text-sm text-muted-foreground">{affiliate.admin_user.email}</p>
                    </div>
                  </div>
                  <AdminStatusBadge status={affiliate.admin_user.status} />
                </div>
                {affiliate.admin_user.status === 'pending' && (
                  <div className="flex items-center justify-between pt-2 border-t border-border">
                    <p className="text-xs text-muted-foreground">
                      {affiliate.admin_user.last_invite_sent
                        ? `Last sent: ${formatRelativeTime(affiliate.admin_user.last_invite_sent)}`
                        : 'No invitation sent yet'}
                    </p>
                    <Button variant="outline" size="sm" onClick={handleResendAdminInvite} disabled={resending}>
                      {resending ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" /> : <Send className="h-3.5 w-3.5 mr-1" />}
                      Resend Invite
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-sm text-muted-foreground mb-3">No admin has been invited yet.</p>
                <Button size="sm" onClick={() => setInviteAdminOpen(true)}>
                  <UserPlus className="h-4 w-4 mr-1" />
                  Invite Company Admin
                </Button>
              </div>
            )}
          </div>
        </Card>

        {/* Branding */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-start justify-between space-y-0">
            <div>
              <CardTitle className="text-lg">Branding</CardTitle>
              <CardDescription>White-label configuration</CardDescription>
            </div>
            <EditBrandingModal
              affiliateId={affiliate.account_id}
              branding={affiliate.branding}
              onSaved={(updated) =>
                setAffiliate((prev) =>
                  prev ? { ...prev, branding: { ...prev.branding, ...updated } } : prev
                )
              }
            />
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-muted-foreground mb-1">Display Name</div>
                <div>{affiliate.branding.brand_display_name || affiliate.name}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground mb-1">Colors</div>
                <div className="flex items-center gap-2">
                  {affiliate.branding.primary_color && (
                    <div
                      className="w-6 h-6 rounded border"
                      style={{ backgroundColor: affiliate.branding.primary_color }}
                      title={`Primary: ${affiliate.branding.primary_color}`}
                    />
                  )}
                  {affiliate.branding.accent_color && (
                    <div
                      className="w-6 h-6 rounded border"
                      style={{ backgroundColor: affiliate.branding.accent_color }}
                      title={`Accent: ${affiliate.branding.accent_color}`}
                    />
                  )}
                  {!affiliate.branding.primary_color && !affiliate.branding.accent_color && (
                    <span className="text-muted-foreground">Not set</span>
                  )}
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground mb-1">Contact Line 1</div>
                <div>{affiliate.branding.contact_line1 || <span className="text-muted-foreground">Not set</span>}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground mb-1">Contact Line 2</div>
                <div>{affiliate.branding.contact_line2 || <span className="text-muted-foreground">Not set</span>}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Invite Agent Form */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <UserPlus className="h-5 w-5" />
            Invite New Agent
          </CardTitle>
          <CardDescription>
            Add a new trial agent under {affiliate.name}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <InviteAgentForm affiliateId={affiliate.account_id} affiliateName={affiliate.name} />
        </CardContent>
      </Card>

      {/* Bulk Import */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <FileUp className="h-5 w-5" />
            Bulk Import Agents
          </CardTitle>
          <CardDescription>
            Import multiple agents at once from a CSV file. Great for full-service onboarding.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <BulkImportForm affiliateId={affiliate.account_id} affiliateName={affiliate.name} />
        </CardContent>
      </Card>

      {/* Agents Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Users className="h-5 w-5" />
            Trial Agents ({affiliate.agent_count})
          </CardTitle>
          <CardDescription>
            Agents using {affiliate.name}&apos;s branding
          </CardDescription>
        </CardHeader>
        <CardContent>
          {affiliate.agents.length === 0 ? (
            <div className="text-center py-12">
              <Users className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No agents yet</h3>
              <p className="text-muted-foreground">
                Use the form above to invite agents to this affiliate
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Agent</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Reports/Month</TableHead>
                  <TableHead>Last Report</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Joined</TableHead>
                  <TableHead className="w-[50px]">Headshot</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {affiliate.agents.map((agent) => (
                  <TableRow key={agent.account_id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        {agent.avatar_url ? (
                          <img
                            src={agent.avatar_url}
                            alt={agent.name}
                            className="h-8 w-8 rounded-full object-cover"
                          />
                        ) : (
                          <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center">
                            <User className="h-4 w-4 text-muted-foreground" />
                          </div>
                        )}
                        <div>
                          <div className="font-medium">{agent.name}</div>
                          {(agent.first_name || agent.last_name) && (
                            <div className="text-sm text-muted-foreground">
                              {agent.first_name} {agent.last_name}
                            </div>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>{agent.email}</TableCell>
                    <TableCell>{agent.reports_this_month}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {agent.last_report_at
                        ? new Date(agent.last_report_at).toLocaleDateString()
                        : 'Never'}
                    </TableCell>
                    <TableCell>
                      <Badge variant={agent.is_active ? "default" : "secondary"}>
                        {agent.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {agent.created_at
                        ? new Date(agent.created_at).toLocaleDateString()
                        : '-'}
                    </TableCell>
                    <TableCell>
                      <AgentHeadshotUpload
                        accountId={agent.account_id}
                        agentName={agent.name}
                        currentHeadshot={agent.avatar_url}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Invite Admin Dialog */}
      <Dialog open={inviteAdminOpen} onOpenChange={setInviteAdminOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Invite Company Admin</DialogTitle>
            <DialogDescription>
              Create an admin user for {affiliate.name}. They&apos;ll receive an invitation email to set up their account.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleInviteAdmin}>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="admin_first_name">First Name</Label>
                  <Input
                    id="admin_first_name"
                    required
                    value={inviteForm.first_name}
                    onChange={(e) => setInviteForm(prev => ({ ...prev, first_name: e.target.value }))}
                    disabled={inviteSubmitting}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="admin_last_name">Last Name</Label>
                  <Input
                    id="admin_last_name"
                    required
                    value={inviteForm.last_name}
                    onChange={(e) => setInviteForm(prev => ({ ...prev, last_name: e.target.value }))}
                    disabled={inviteSubmitting}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="admin_email">Email Address</Label>
                <Input
                  id="admin_email"
                  type="email"
                  required
                  value={inviteForm.email}
                  onChange={(e) => setInviteForm(prev => ({ ...prev, email: e.target.value }))}
                  disabled={inviteSubmitting}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setInviteAdminOpen(false)} disabled={inviteSubmitting}>
                Cancel
              </Button>
              <Button type="submit" disabled={inviteSubmitting}>
                {inviteSubmitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Send className="h-4 w-4 mr-2" />}
                Send Invitation
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

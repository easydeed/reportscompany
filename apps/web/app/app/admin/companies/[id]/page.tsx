'use client'

import { useEffect, useState, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  ArrowLeft, Building, Users, UserCheck, FileText, TrendingUp,
  TrendingDown, Minus, Loader2, UserPlus, Send, Power, PowerOff,
} from "lucide-react"

interface CompanyBranding {
  brand_display_name: string | null
  logo_url: string | null
  email_logo_url: string | null
  footer_logo_url: string | null
  email_footer_logo_url: string | null
  primary_color: string | null
  accent_color: string | null
  website_url: string | null
}

interface CompanyAdmin {
  user_id: string
  email: string
  first_name: string | null
  last_name: string | null
  status: string
  last_invite_sent: string | null
}

interface Rep {
  account_id: string
  name: string
  is_active: boolean
  created_at: string | null
  email: string | null
  first_name: string | null
  last_name: string | null
  status: string
  agent_count: number
  reports_30d: number
}

interface Agent {
  account_id: string
  name: string
  is_active: boolean
  created_at: string | null
  plan_slug: string | null
  sponsor_account_id: string
  email: string | null
  first_name: string | null
  last_name: string | null
  reports_30d: number
  rep_name: string | null
}

interface CompanyMetrics {
  total_reps: number
  total_agents: number
  reports_30d: number
  reports_prev_30d: number
  trend_pct: number
}

interface CompanyDetail {
  account_id: string
  name: string
  slug: string
  is_active: boolean
  created_at: string | null
  plan_slug: string | null
  branding: CompanyBranding
  admin: CompanyAdmin | null
  reps: Rep[]
  agents: Agent[]
  metrics: CompanyMetrics
}

export default function CompanyDetailPage() {
  const params = useParams()
  const router = useRouter()
  const companyId = params.id as string

  const [company, setCompany] = useState<CompanyDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [inviteOpen, setInviteOpen] = useState(false)
  const [inviteLoading, setInviteLoading] = useState(false)
  const [inviteError, setInviteError] = useState<string | null>(null)
  const [inviteSuccess, setInviteSuccess] = useState<string | null>(null)

  const [statusLoading, setStatusLoading] = useState(false)
  const [repFilter, setRepFilter] = useState<string>("all")

  const fetchCompany = useCallback(async () => {
    try {
      const res = await fetch(`/api/proxy/v1/admin/companies/${companyId}`, { credentials: 'include' })
      if (!res.ok) throw new Error("Company not found")
      const data = await res.json()
      setCompany(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load company")
    } finally {
      setLoading(false)
    }
  }, [companyId])

  useEffect(() => { fetchCompany() }, [fetchCompany])

  async function handleInviteAdmin(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setInviteLoading(true)
    setInviteError(null)
    const fd = new FormData(e.currentTarget)
    try {
      const res = await fetch(`/api/proxy/v1/admin/companies/${companyId}/invite-admin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: fd.get('email'),
          first_name: fd.get('first_name'),
          last_name: fd.get('last_name'),
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || "Failed to invite admin")
      setInviteSuccess(data.action === 'resent' ? "Invite resent successfully" : "Admin invited successfully")
      setInviteOpen(false)
      fetchCompany()
    } catch (err) {
      setInviteError(err instanceof Error ? err.message : "Failed to invite admin")
    } finally {
      setInviteLoading(false)
    }
  }

  async function toggleStatus() {
    if (!company) return
    setStatusLoading(true)
    try {
      const res = await fetch(`/api/proxy/v1/admin/companies/${companyId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !company.is_active }),
      })
      if (!res.ok) throw new Error("Failed to update status")
      fetchCompany()
    } catch (err) {
      console.error(err)
    } finally {
      setStatusLoading(false)
    }
  }

  const filteredAgents = company?.agents.filter(a =>
    repFilter === "all" ? true : a.sponsor_account_id === repFilter
  ) ?? []

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded" />
          <div>
            <Skeleton className="h-9 w-64 mb-2" />
            <Skeleton className="h-5 w-40" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <Card key={i}><CardContent className="pt-6"><Skeleton className="h-8 w-16" /></CardContent></Card>
          ))}
        </div>
        <Card><CardContent className="pt-6"><Skeleton className="h-32 w-full" /></CardContent></Card>
      </div>
    )
  }

  if (error || !company) {
    return (
      <div className="space-y-6">
        <Link href="/app/admin/companies">
          <Button variant="ghost"><ArrowLeft className="h-4 w-4 mr-2" />Back to Companies</Button>
        </Link>
        <Alert variant="destructive"><AlertDescription>{error || "Company not found"}</AlertDescription></Alert>
      </div>
    )
  }

  const b = company.branding
  const m = company.metrics
  const TrendIcon = m.trend_pct > 0 ? TrendingUp : m.trend_pct < 0 ? TrendingDown : Minus

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/app/admin/companies">
            <Button variant="ghost" size="icon"><ArrowLeft className="h-4 w-4" /></Button>
          </Link>
          <div className="flex items-center gap-3">
            {b.logo_url ? (
              <img src={b.logo_url} alt={company.name} className="h-10 w-10 rounded object-contain bg-muted" />
            ) : (
              <div
                className="h-10 w-10 rounded flex items-center justify-center text-white text-sm font-bold"
                style={{ backgroundColor: b.primary_color || '#4F46E5' }}
              >
                {company.name.charAt(0)}
              </div>
            )}
            <div>
              <h1 className="text-2xl font-display font-bold text-foreground">{company.name}</h1>
              <p className="text-muted-foreground text-sm">{company.slug}</p>
            </div>
          </div>
          <Badge variant={company.is_active ? "default" : "secondary"} className="ml-2">
            {company.is_active ? "Active" : "Inactive"}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          {(!company.admin || company.admin.status === "pending") && (
            <Button variant="outline" onClick={() => setInviteOpen(true)}>
              <UserPlus className="h-4 w-4 mr-2" />
              {company.admin ? "Resend Invite" : "Invite Admin"}
            </Button>
          )}
          <Button
            variant={company.is_active ? "destructive" : "default"}
            size="sm"
            onClick={toggleStatus}
            disabled={statusLoading}
          >
            {statusLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : company.is_active ? (
              <><PowerOff className="h-4 w-4 mr-1" />Deactivate</>
            ) : (
              <><Power className="h-4 w-4 mr-1" />Activate</>
            )}
          </Button>
        </div>
      </div>

      {inviteSuccess && (
        <Alert><AlertDescription>{inviteSuccess}</AlertDescription></Alert>
      )}

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reps</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent><div className="text-2xl font-bold">{m.total_reps}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Agents</CardTitle>
            <UserCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent><div className="text-2xl font-bold">{m.total_agents}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reports (30d)</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent><div className="text-2xl font-bold">{m.reports_30d}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Trend</CardTitle>
            <TrendIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${m.trend_pct > 0 ? 'text-green-600' : m.trend_pct < 0 ? 'text-red-600' : ''}`}>
              {m.trend_pct > 0 ? '+' : ''}{m.trend_pct}%
            </div>
            <p className="text-xs text-muted-foreground">vs. previous 30 days</p>
          </CardContent>
        </Card>
      </div>

      {/* Company Info + Branding + Admin */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Building className="h-5 w-5" />Company Info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-y-2 text-sm">
              <span className="text-muted-foreground">Display Name</span>
              <span className="font-medium">{b.brand_display_name || company.name}</span>
              <span className="text-muted-foreground">Plan</span>
              <span className="font-medium capitalize">{company.plan_slug || 'affiliate'}</span>
              <span className="text-muted-foreground">Created</span>
              <span className="font-medium">{company.created_at ? new Date(company.created_at).toLocaleDateString() : '-'}</span>
              <span className="text-muted-foreground">Website</span>
              <span className="font-medium">
                {b.website_url ? (
                  <a href={b.website_url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 underline">
                    {b.website_url.replace(/^https?:\/\//, '')}
                  </a>
                ) : '-'}
              </span>
            </div>
            {(b.primary_color || b.accent_color) && (
              <div className="flex items-center gap-3 pt-2">
                <span className="text-sm text-muted-foreground">Colors:</span>
                {b.primary_color && (
                  <div className="flex items-center gap-1.5">
                    <div className="h-5 w-5 rounded border" style={{ backgroundColor: b.primary_color }} />
                    <span className="text-xs text-muted-foreground">{b.primary_color}</span>
                  </div>
                )}
                {b.accent_color && (
                  <div className="flex items-center gap-1.5">
                    <div className="h-5 w-5 rounded border" style={{ backgroundColor: b.accent_color }} />
                    <span className="text-xs text-muted-foreground">{b.accent_color}</span>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><UserPlus className="h-5 w-5" />Company Admin</CardTitle>
          </CardHeader>
          <CardContent>
            {company.admin ? (
              <div className="space-y-2 text-sm">
                <div className="grid grid-cols-2 gap-y-2">
                  <span className="text-muted-foreground">Name</span>
                  <span className="font-medium">
                    {[company.admin.first_name, company.admin.last_name].filter(Boolean).join(' ') || '-'}
                  </span>
                  <span className="text-muted-foreground">Email</span>
                  <span className="font-medium">{company.admin.email}</span>
                  <span className="text-muted-foreground">Status</span>
                  <span>
                    <Badge variant={company.admin.status === 'active' ? 'default' : company.admin.status === 'pending' ? 'outline' : 'secondary'}>
                      {company.admin.status}
                    </Badge>
                  </span>
                  {company.admin.status === 'pending' && company.admin.last_invite_sent && (
                    <>
                      <span className="text-muted-foreground">Last Invite</span>
                      <span className="font-medium">{new Date(company.admin.last_invite_sent).toLocaleDateString()}</span>
                    </>
                  )}
                </div>
                {company.admin.status === 'pending' && (
                  <Button variant="outline" size="sm" className="mt-3" onClick={() => setInviteOpen(true)}>
                    <Send className="h-3.5 w-3.5 mr-1.5" />Resend Invite
                  </Button>
                )}
              </div>
            ) : (
              <div className="text-center py-6">
                <UserPlus className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground mb-3">No admin assigned yet</p>
                <Button variant="outline" size="sm" onClick={() => setInviteOpen(true)}>
                  <UserPlus className="h-3.5 w-3.5 mr-1.5" />Invite Admin
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Reps Table */}
      <Card>
        <CardHeader>
          <CardTitle>Title Reps</CardTitle>
          <CardDescription>{company.reps.length} rep{company.reps.length !== 1 ? 's' : ''} under this company</CardDescription>
        </CardHeader>
        <CardContent>
          {company.reps.length === 0 ? (
            <p className="text-center py-8 text-muted-foreground">No reps have been invited yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Rep</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-center">Agents</TableHead>
                  <TableHead className="text-center">Reports (30d)</TableHead>
                  <TableHead>Joined</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {company.reps.map((rep) => (
                  <TableRow key={rep.account_id}>
                    <TableCell className="font-medium">
                      {[rep.first_name, rep.last_name].filter(Boolean).join(' ') || rep.name}
                    </TableCell>
                    <TableCell className="text-muted-foreground">{rep.email || '-'}</TableCell>
                    <TableCell>
                      <Badge variant={rep.status === 'active' ? 'default' : rep.status === 'pending' ? 'outline' : 'secondary'}>
                        {rep.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">{rep.agent_count}</TableCell>
                    <TableCell className="text-center">{rep.reports_30d}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {rep.created_at ? new Date(rep.created_at).toLocaleDateString() : '-'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Agents Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Agents</CardTitle>
              <CardDescription>
                {filteredAgents.length} agent{filteredAgents.length !== 1 ? 's' : ''} across all reps
              </CardDescription>
            </div>
            {company.reps.length > 1 && (
              <Select value={repFilter} onValueChange={setRepFilter}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Filter by rep" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Reps</SelectItem>
                  {company.reps.map(r => (
                    <SelectItem key={r.account_id} value={r.account_id}>
                      {[r.first_name, r.last_name].filter(Boolean).join(' ') || r.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {filteredAgents.length === 0 ? (
            <p className="text-center py-8 text-muted-foreground">No agents found.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Agent</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Rep</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-center">Reports (30d)</TableHead>
                  <TableHead>Plan</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAgents.map((agent) => (
                  <TableRow key={agent.account_id}>
                    <TableCell className="font-medium">
                      {[agent.first_name, agent.last_name].filter(Boolean).join(' ') || agent.name}
                    </TableCell>
                    <TableCell className="text-muted-foreground">{agent.email || '-'}</TableCell>
                    <TableCell className="text-muted-foreground">{agent.rep_name || '-'}</TableCell>
                    <TableCell>
                      <Badge variant={agent.is_active ? 'default' : 'secondary'}>
                        {agent.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">{agent.reports_30d}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="capitalize">{agent.plan_slug || 'trial'}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Invite Admin Dialog */}
      <Dialog open={inviteOpen} onOpenChange={(open) => { setInviteOpen(open); setInviteError(null) }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{company.admin ? "Resend Admin Invite" : "Invite Company Admin"}</DialogTitle>
            <DialogDescription>
              {company.admin
                ? `Resend the invitation to ${company.admin.email}`
                : `Invite an admin to manage ${company.name}`}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleInviteAdmin}>
            <div className="space-y-4 py-4">
              <div>
                <Label htmlFor="invite_email">Email Address *</Label>
                <Input
                  id="invite_email"
                  name="email"
                  type="email"
                  defaultValue={company.admin?.email || ''}
                  required
                  disabled={inviteLoading || !!company.admin}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="invite_first">First Name *</Label>
                  <Input
                    id="invite_first"
                    name="first_name"
                    defaultValue={company.admin?.first_name || ''}
                    required
                    disabled={inviteLoading}
                  />
                </div>
                <div>
                  <Label htmlFor="invite_last">Last Name *</Label>
                  <Input
                    id="invite_last"
                    name="last_name"
                    defaultValue={company.admin?.last_name || ''}
                    required
                    disabled={inviteLoading}
                  />
                </div>
              </div>
              {inviteError && (
                <Alert variant="destructive"><AlertDescription>{inviteError}</AlertDescription></Alert>
              )}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setInviteOpen(false)} disabled={inviteLoading}>
                Cancel
              </Button>
              <Button type="submit" disabled={inviteLoading}>
                {inviteLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                {company.admin ? "Resend Invite" : "Send Invite"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

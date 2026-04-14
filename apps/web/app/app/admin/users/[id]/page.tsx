"use client"

import { useState, useEffect, useCallback } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  ArrowLeft,
  User as UserIcon,
  Shield,
  KeyRound,
  ToggleLeft,
  ToggleRight,
  MailCheck,
  Send,
  CheckCircle,
  XCircle,
  Loader2,
  AlertTriangle,
  Building,
  FileText,
  Calendar,
  Users,
  Phone,
  Mail,
  Clock,
  ExternalLink,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"

interface UserDetail {
  user_id: string
  email: string
  first_name: string | null
  last_name: string | null
  phone: string | null
  title: string | null
  company: string | null
  license_number: string | null
  headshot_url: string | null
  is_active: boolean
  email_verified: boolean
  role: string
  created_at: string
  last_login_at: string | null
  account_id: string
  account_name: string
  account_type: string
  sponsor_account_id: string | null
  sponsor_name: string | null
  reports?: ReportRow[]
  schedules?: ScheduleRow[]
  leads?: LeadRow[]
}

interface ReportRow {
  id: string
  report_type: string
  city: string | null
  status: string
  created_at: string
  pdf_url: string | null
}

interface ScheduleRow {
  id: string
  name: string
  report_type: string
  active: boolean
  cadence: string
  next_run_at: string | null
}

interface LeadRow {
  id: string
  email: string | null
  name: string | null
  status: string
  created_at: string
}

function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return "Just now"
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 30) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

function getInitials(first: string | null, last: string | null, email: string): string {
  if (first && last) return `${first[0]}${last[0]}`.toUpperCase()
  if (first) return first[0].toUpperCase()
  return email[0].toUpperCase()
}

function statusBadge(status: string) {
  const map: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; className?: string }> = {
    completed: { variant: "outline", className: "text-green-600 border-green-200 bg-green-50" },
    success: { variant: "outline", className: "text-green-600 border-green-200 bg-green-50" },
    running: { variant: "outline", className: "text-blue-600 border-blue-200 bg-blue-50" },
    pending: { variant: "outline", className: "text-yellow-600 border-yellow-200 bg-yellow-50" },
    queued: { variant: "outline", className: "text-yellow-600 border-yellow-200 bg-yellow-50" },
    failed: { variant: "outline", className: "text-red-600 border-red-200 bg-red-50" },
    error: { variant: "outline", className: "text-red-600 border-red-200 bg-red-50" },
  }
  const s = map[status.toLowerCase()] || { variant: "secondary" as const }
  return <Badge variant={s.variant} className={s.className}>{status}</Badge>
}

export default function AdminUserDetailPage() {
  const params = useParams()
  const userId = params.id as string
  const { toast } = useToast()

  const [user, setUser] = useState<UserDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  const fetchUser = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await fetch(`/api/proxy/v1/admin/users/${userId}`, {
        credentials: "include",
      })
      if (!res.ok) throw new Error("Failed to fetch user")
      const data = await res.json()
      setUser(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load user")
    } finally {
      setLoading(false)
    }
  }, [userId])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  async function handleAction(action: string, label: string) {
    setActionLoading(action)
    try {
      let res: Response

      switch (action) {
        case "force-password-reset":
          res = await fetch(`/api/proxy/v1/admin/users/${userId}/force-password-reset`, {
            method: "POST",
            credentials: "include",
          })
          break
        case "toggle-active":
          res = await fetch(`/api/proxy/v1/admin/users/${userId}`, {
            method: "PATCH",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_active: !user?.is_active }),
          })
          break
        case "verify-email":
          res = await fetch(`/api/proxy/v1/admin/users/${userId}`, {
            method: "PATCH",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email_verified: true }),
          })
          break
        case "resend-invite":
          res = await fetch(`/api/proxy/v1/admin/users/${userId}/resend-invite`, {
            method: "POST",
            credentials: "include",
          })
          break
        default:
          return
      }

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || data.error || `Failed to ${label.toLowerCase()}`)
      }

      toast({ title: `${label} successful` })
      fetchUser()
    } catch (err) {
      toast({
        title: `Failed to ${label.toLowerCase()}`,
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      })
    } finally {
      setActionLoading(null)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded" />
          <div>
            <Skeleton className="h-9 w-48 mb-2" />
            <Skeleton className="h-5 w-64" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <Card key={i}><CardContent className="pt-6"><Skeleton className="h-8 w-16" /></CardContent></Card>
          ))}
        </div>
        <Card><CardContent className="pt-6 space-y-4">
          {[1, 2, 3, 4, 5].map(i => (
            <Skeleton key={i} className="h-5 w-full" />
          ))}
        </CardContent></Card>
      </div>
    )
  }

  if (error || !user) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 mx-auto text-red-500 mb-4" />
        <h3 className="text-lg font-semibold mb-2">{error || "User not found"}</h3>
        <Link href="/app/admin/users">
          <Button variant="outline">Back to Users</Button>
        </Link>
      </div>
    )
  }

  const fullName = [user.first_name, user.last_name].filter(Boolean).join(" ") || "Unnamed User"
  const initials = getInitials(user.first_name, user.last_name, user.email)
  const isSponsored = user.account_type === "SPONSORED" || !!user.sponsor_account_id
  const isAffiliate = user.account_type === "INDUSTRY_AFFILIATE"
  const accountLabel = isAffiliate ? "Affiliate" : isSponsored ? "Trial" : "Regular"

  const reports = user.reports || []
  const schedules = user.schedules || []
  const leads = user.leads || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <Link href="/app/admin/users">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div className="flex items-center gap-4">
            {user.headshot_url ? (
              <img
                src={user.headshot_url}
                alt={fullName}
                className="h-12 w-12 rounded-full object-cover"
              />
            ) : (
              <div className="h-12 w-12 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-lg font-bold">
                {initials}
              </div>
            )}
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-3xl font-display font-bold text-foreground">{fullName}</h1>
                {user.is_active ? (
                  <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50">Active</Badge>
                ) : (
                  <Badge variant="outline" className="text-red-600 border-red-200 bg-red-50">Inactive</Badge>
                )}
                {!user.email_verified && (
                  <Badge variant="outline" className="text-yellow-600 border-yellow-200 bg-yellow-50">Unverified</Badge>
                )}
                <Badge variant={user.role === "ADMIN" ? "default" : "secondary"}>
                  {user.role || "Member"}
                </Badge>
              </div>
              <p className="text-muted-foreground mt-0.5">{user.email}</p>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-2 sm:ml-auto">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleAction("force-password-reset", "Force password reset")}
            disabled={!!actionLoading}
          >
            {actionLoading === "force-password-reset" ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <KeyRound className="h-4 w-4 mr-2" />
            )}
            Force Password Reset
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleAction("toggle-active", user.is_active ? "Deactivate user" : "Activate user")}
            disabled={!!actionLoading}
          >
            {actionLoading === "toggle-active" ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : user.is_active ? (
              <ToggleRight className="h-4 w-4 mr-2" />
            ) : (
              <ToggleLeft className="h-4 w-4 mr-2" />
            )}
            {user.is_active ? "Deactivate" : "Activate"}
          </Button>

          {!user.email_verified && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAction("verify-email", "Verify email")}
                disabled={!!actionLoading}
              >
                {actionLoading === "verify-email" ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <MailCheck className="h-4 w-4 mr-2" />
                )}
                Verify Email
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAction("resend-invite", "Resend invite")}
                disabled={!!actionLoading}
              >
                {actionLoading === "resend-invite" ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Send className="h-4 w-4 mr-2" />
                )}
                Resend Invite
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Profile Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserIcon className="h-5 w-5" />
            Profile
          </CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-4 text-sm">
            <div>
              <dt className="text-muted-foreground mb-0.5">Full Name</dt>
              <dd className="font-medium">{fullName}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground mb-0.5">Email</dt>
              <dd className="font-medium flex items-center gap-1.5">
                <Mail className="h-3.5 w-3.5 text-muted-foreground" />
                {user.email}
                {user.email_verified ? (
                  <CheckCircle className="h-3.5 w-3.5 text-green-500" />
                ) : (
                  <XCircle className="h-3.5 w-3.5 text-red-400" />
                )}
              </dd>
            </div>
            {user.phone && (
              <div>
                <dt className="text-muted-foreground mb-0.5">Phone</dt>
                <dd className="font-medium flex items-center gap-1.5">
                  <Phone className="h-3.5 w-3.5 text-muted-foreground" />
                  {user.phone}
                </dd>
              </div>
            )}
            {user.title && (
              <div>
                <dt className="text-muted-foreground mb-0.5">Title</dt>
                <dd className="font-medium">{user.title}</dd>
              </div>
            )}
            {user.company && (
              <div>
                <dt className="text-muted-foreground mb-0.5">Company</dt>
                <dd className="font-medium">{user.company}</dd>
              </div>
            )}
            {user.license_number && (
              <div>
                <dt className="text-muted-foreground mb-0.5">License #</dt>
                <dd className="font-medium font-mono text-xs">{user.license_number}</dd>
              </div>
            )}
            <div>
              <dt className="text-muted-foreground mb-0.5">Account Type</dt>
              <dd className="font-medium">
                <Badge variant="outline">{accountLabel}</Badge>
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground mb-0.5">Account</dt>
              <dd className="font-medium">
                <Link
                  href={`/app/admin/accounts/${user.account_id}`}
                  className="text-indigo-600 hover:underline inline-flex items-center gap-1"
                >
                  {user.account_name}
                  <ExternalLink className="h-3 w-3" />
                </Link>
              </dd>
            </div>
            {isSponsored && user.sponsor_name && (
              <div>
                <dt className="text-muted-foreground mb-0.5">Sponsor</dt>
                <dd className="font-medium">
                  {user.sponsor_account_id ? (
                    <Link
                      href={`/app/admin/accounts/${user.sponsor_account_id}`}
                      className="text-indigo-600 hover:underline inline-flex items-center gap-1"
                    >
                      {user.sponsor_name}
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  ) : (
                    user.sponsor_name
                  )}
                </dd>
              </div>
            )}
            <div>
              <dt className="text-muted-foreground mb-0.5">Joined</dt>
              <dd className="font-medium flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                {new Date(user.created_at).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground mb-0.5">Last Login</dt>
              <dd className="font-medium">
                {user.last_login_at ? formatTimeAgo(user.last_login_at) : "Never"}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground mb-0.5">User ID</dt>
              <dd className="font-mono text-xs text-muted-foreground">{user.user_id}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      {/* Associated Data */}
      <Tabs defaultValue="reports" className="space-y-4">
        <TabsList>
          <TabsTrigger value="reports" className="gap-1.5">
            <FileText className="h-3.5 w-3.5" />
            Reports {reports.length > 0 && <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-xs">{reports.length}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="schedules" className="gap-1.5">
            <Calendar className="h-3.5 w-3.5" />
            Schedules {schedules.length > 0 && <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-xs">{schedules.length}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="leads" className="gap-1.5">
            <Users className="h-3.5 w-3.5" />
            Leads {leads.length > 0 && <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-xs">{leads.length}</Badge>}
          </TabsTrigger>
        </TabsList>

        {/* Reports Tab */}
        <TabsContent value="reports">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recent Reports</CardTitle>
            </CardHeader>
            <CardContent>
              {reports.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No reports generated yet</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type</TableHead>
                      <TableHead>City</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Generated</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {reports.slice(0, 10).map((r) => (
                      <TableRow key={r.id}>
                        <TableCell className="font-medium">{r.report_type?.replace(/_/g, " ")}</TableCell>
                        <TableCell className="text-muted-foreground">{r.city || "-"}</TableCell>
                        <TableCell>{statusBadge(r.status)}</TableCell>
                        <TableCell className="text-muted-foreground">{formatTimeAgo(r.created_at)}</TableCell>
                        <TableCell>
                          {r.pdf_url && (
                            <a href={r.pdf_url} target="_blank" rel="noopener noreferrer">
                              <Button variant="ghost" size="sm">
                                <ExternalLink className="h-3.5 w-3.5" />
                              </Button>
                            </a>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Schedules Tab */}
        <TabsContent value="schedules">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Active Schedules</CardTitle>
            </CardHeader>
            <CardContent>
              {schedules.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Calendar className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No schedules configured</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Cadence</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Next Run</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {schedules.map((s) => (
                      <TableRow key={s.id}>
                        <TableCell className="font-medium">{s.name}</TableCell>
                        <TableCell className="text-muted-foreground">{s.report_type?.replace(/_/g, " ")}</TableCell>
                        <TableCell className="text-muted-foreground capitalize">{s.cadence}</TableCell>
                        <TableCell>
                          {s.active ? (
                            <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50">Active</Badge>
                          ) : (
                            <Badge variant="outline" className="text-yellow-600 border-yellow-200 bg-yellow-50">Paused</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {s.next_run_at ? formatTimeAgo(s.next_run_at) : "-"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Leads Tab */}
        <TabsContent value="leads">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Leads</CardTitle>
            </CardHeader>
            <CardContent>
              {leads.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Users className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No leads captured yet</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Captured</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {leads.map((l) => (
                      <TableRow key={l.id}>
                        <TableCell className="font-medium">{l.name || "-"}</TableCell>
                        <TableCell className="text-muted-foreground">{l.email || "-"}</TableCell>
                        <TableCell>{statusBadge(l.status)}</TableCell>
                        <TableCell className="text-muted-foreground">{formatTimeAgo(l.created_at)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

"use client"

import { useState, useMemo } from "react"
import Link from "next/link"
import {
  Search,
  Plus,
  MoreHorizontal,
  Eye,
  Mail,
  UserX,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  Clock,
  AlertCircle,
  ArrowLeft,
  Download,
  Loader2,
  Users,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { useCompanyReps } from "@/hooks/use-api"
import { useToast } from "@/components/ui/use-toast"
import { useQueryClient } from "@tanstack/react-query"
import { queryKeys } from "@/hooks/use-api"

interface TitleRep {
  id: string
  name: string
  email: string
  office: string
  agent_count: number
  reports_this_month: number
  total_reports: number
  last_active: string | null
  joined_date: string | null
  status: "active" | "pending" | "deactivated"
}

const PER_PAGE = 10

const AVATAR_COLORS = [
  "bg-[#6366F1]",
  "bg-[#4338CA]",
  "bg-[#818CF8]",
  "bg-[#312E81]",
  "bg-[#94A3B8]",
  "bg-[#7C3AED]",
]

function getInitials(name: string) {
  return name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)
}

function getStatusBadge(status: TitleRep["status"]) {
  switch (status) {
    case "active":
      return (
        <Badge className="bg-[#DCFCE7] text-[#166534] hover:bg-[#DCFCE7]">
          <CheckCircle2 className="mr-1 h-3 w-3" />
          Active
        </Badge>
      )
    case "pending":
      return (
        <Badge className="bg-[#FEF9C3] text-[#854D0E] hover:bg-[#FEF9C3]">
          <Clock className="mr-1 h-3 w-3" />
          Pending
        </Badge>
      )
    case "deactivated":
      return (
        <Badge className="bg-[#F1F5F9] text-[#64748B] hover:bg-[#F1F5F9]">
          <AlertCircle className="mr-1 h-3 w-3" />
          Deactivated
        </Badge>
      )
  }
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return "—"
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

function formatRelativeTime(dateStr: string | null) {
  if (!dateStr) return "Never"
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return "Just now"
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days < 30) return `${days}d ago`
  return `${Math.floor(days / 30)}mo ago`
}

export default function RepsListPage() {
  const { data, isLoading, error, refetch } = useCompanyReps()
  const queryClient = useQueryClient()
  const { toast } = useToast()

  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [officeFilter, setOfficeFilter] = useState("all")
  const [currentPage, setCurrentPage] = useState(1)

  // Invite modal
  const [inviteOpen, setInviteOpen] = useState(false)
  const [inviteForm, setInviteForm] = useState({ email: "", first_name: "", last_name: "" })
  const [inviteSubmitting, setInviteSubmitting] = useState(false)

  // Resend modal
  const [resendModal, setResendModal] = useState<{ open: boolean; rep: TitleRep | null }>({
    open: false,
    rep: null,
  })
  const [resending, setResending] = useState(false)

  const reps: TitleRep[] = data?.reps ?? []

  const offices = useMemo(() => {
    const set = new Set(reps.map((r) => r.office).filter(Boolean))
    return Array.from(set).sort()
  }, [reps])

  const filteredReps = useMemo(() => {
    return reps.filter((rep) => {
      const matchesSearch =
        !search ||
        rep.name.toLowerCase().includes(search.toLowerCase()) ||
        rep.email.toLowerCase().includes(search.toLowerCase()) ||
        (rep.office && rep.office.toLowerCase().includes(search.toLowerCase()))
      const matchesStatus = statusFilter === "all" || rep.status === statusFilter
      const matchesOffice = officeFilter === "all" || rep.office === officeFilter
      return matchesSearch && matchesStatus && matchesOffice
    })
  }, [reps, search, statusFilter, officeFilter])

  const totalPages = Math.ceil(filteredReps.length / PER_PAGE)
  const paginatedReps = filteredReps.slice(
    (currentPage - 1) * PER_PAGE,
    currentPage * PER_PAGE
  )

  const activeCount = reps.filter((r) => r.status === "active").length
  const pendingCount = reps.filter((r) => r.status === "pending").length
  const deactivatedCount = reps.filter((r) => r.status === "deactivated").length
  const totalAgents = reps.reduce((sum, r) => sum + r.agent_count, 0)

  async function handleInviteRep() {
    if (!inviteForm.email || !inviteForm.first_name || !inviteForm.last_name) {
      toast({ title: "Error", description: "All fields are required", variant: "destructive" })
      return
    }
    setInviteSubmitting(true)
    try {
      const res = await fetch("/api/proxy/v1/company/invite-rep", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(inviteForm),
      })
      const result = await res.json()
      if (res.ok) {
        toast({ title: "Rep invited", description: `Invitation sent to ${inviteForm.email}` })
        setInviteOpen(false)
        setInviteForm({ email: "", first_name: "", last_name: "" })
        queryClient.invalidateQueries({ queryKey: queryKeys.company.reps() })
        refetch()
      } else {
        toast({
          title: "Error",
          description: typeof result.detail === "string" ? result.detail : "Failed to invite rep",
          variant: "destructive",
        })
      }
    } catch {
      toast({ title: "Error", description: "Network error — please try again", variant: "destructive" })
    } finally {
      setInviteSubmitting(false)
    }
  }

  async function handleResendInvite(rep: TitleRep) {
    setResending(true)
    try {
      const res = await fetch("/api/proxy/v1/company/resend-invite", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: rep.email }),
      })
      const result = await res.json()
      if (res.ok) {
        toast({ title: "Invitation sent", description: `New invitation sent to ${rep.email}` })
        setResendModal({ open: false, rep: null })
        refetch()
      } else {
        toast({
          title: "Error",
          description: typeof result.detail === "string" ? result.detail : "Failed to resend",
          variant: "destructive",
        })
      }
    } catch {
      toast({ title: "Error", description: "Network error — please try again", variant: "destructive" })
    } finally {
      setResending(false)
    }
  }

  if (isLoading) return <RepsSkeleton />

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <Users className="h-16 w-16 text-muted-foreground mb-4" />
        <h1 className="text-2xl font-bold mb-2">Unable to Load Reps</h1>
        <p className="text-muted-foreground max-w-md mb-6">Failed to load rep data. Please try again.</p>
        <Button asChild>
          <Link href="/app/company">Back to Dashboard</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/app/company"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="mr-1 h-4 w-4" />
          Back to Dashboard
        </Link>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Title Reps</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage your title representatives and their agent networks
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Button onClick={() => setInviteOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Invite Rep
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="mt-6 grid gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Active Reps
          </p>
          <p className="mt-1 text-2xl font-bold text-foreground">{activeCount}</p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Pending Invites
          </p>
          <p className="mt-1 text-2xl font-bold text-[#F59E0B]">{pendingCount}</p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Deactivated
          </p>
          <p className="mt-1 text-2xl font-bold text-muted-foreground">{deactivatedCount}</p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Total Agents
          </p>
          <p className="mt-1 text-2xl font-bold text-foreground">{totalAgents}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground/60" />
          <Input
            placeholder="Search by name, email, or office..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setCurrentPage(1)
            }}
            className="pl-9"
          />
        </div>
        <Select
          value={statusFilter}
          onValueChange={(v) => {
            setStatusFilter(v)
            setCurrentPage(1)
          }}
        >
          <SelectTrigger className="w-full sm:w-40">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="deactivated">Deactivated</SelectItem>
          </SelectContent>
        </Select>
        {offices.length > 0 && (
          <Select
            value={officeFilter}
            onValueChange={(v) => {
              setOfficeFilter(v)
              setCurrentPage(1)
            }}
          >
            <SelectTrigger className="w-full sm:w-48">
              <SelectValue placeholder="Office" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Offices</SelectItem>
              {offices.map((office) => (
                <SelectItem key={office} value={office}>
                  {office}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {/* Table */}
      <div className="mt-6 overflow-hidden rounded-xl border border-border bg-card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                  Rep Name
                </th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                  Office
                </th>
                <th className="px-4 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                  Agents
                </th>
                <th className="px-4 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                  Reports (30d)
                </th>
                <th className="px-4 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                  Total Reports
                </th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                  Joined
                </th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                  Last Active
                </th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                  Status
                </th>
                <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {paginatedReps.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-12 text-center">
                    <Users className="mx-auto h-10 w-10 text-muted-foreground/40 mb-3" />
                    <p className="text-sm font-medium text-muted-foreground">
                      {search || statusFilter !== "all" || officeFilter !== "all"
                        ? "No reps match your filters"
                        : "No reps yet"}
                    </p>
                    {!search && statusFilter === "all" && officeFilter === "all" && (
                      <Button size="sm" className="mt-3" onClick={() => setInviteOpen(true)}>
                        <Plus className="mr-1 h-3.5 w-3.5" />
                        Invite Rep
                      </Button>
                    )}
                  </td>
                </tr>
              ) : (
                paginatedReps.map((rep, idx) => (
                  <tr key={rep.id} className="transition-colors hover:bg-muted/30">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div
                          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white ${AVATAR_COLORS[idx % AVATAR_COLORS.length]}`}
                        >
                          {getInitials(rep.name)}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-foreground">{rep.name}</p>
                          <p className="text-xs text-muted-foreground">{rep.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {rep.office || "—"}
                    </td>
                    <td className="px-4 py-3 text-center text-sm font-medium text-foreground tabular-nums">
                      {rep.agent_count}
                    </td>
                    <td className="px-4 py-3 text-center text-sm font-medium text-foreground tabular-nums">
                      {rep.reports_this_month}
                    </td>
                    <td className="px-4 py-3 text-center text-sm text-muted-foreground tabular-nums">
                      {rep.total_reports.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {formatDate(rep.joined_date)}
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {formatRelativeTime(rep.last_active)}
                    </td>
                    <td className="px-4 py-3">{getStatusBadge(rep.status)}</td>
                    <td className="px-4 py-3 text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem asChild>
                            <Link href={`/app/company/agents?rep=${rep.id}`}>
                              <Eye className="mr-2 h-4 w-4" />
                              View Agents
                            </Link>
                          </DropdownMenuItem>
                          {rep.status === "pending" && (
                            <DropdownMenuItem onClick={() => setResendModal({ open: true, rep })}>
                              <Mail className="mr-2 h-4 w-4" />
                              Resend Invite
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          <DropdownMenuItem className="text-red-600">
                            <UserX className="mr-2 h-4 w-4" />
                            {rep.status === "active" ? "Deactivate" : "Remove"}
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {filteredReps.length > 0 && (
          <div className="flex items-center justify-between border-t border-border px-4 py-3">
            <p className="text-sm text-muted-foreground">
              Showing {(currentPage - 1) * PER_PAGE + 1} –{" "}
              {Math.min(currentPage * PER_PAGE, filteredReps.length)} of{" "}
              {filteredReps.length} reps
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => p - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {currentPage}{totalPages > 1 ? ` of ${totalPages}` : ""}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={currentPage >= totalPages}
                onClick={() => setCurrentPage((p) => p + 1)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Invite Rep Modal */}
      <Dialog open={inviteOpen} onOpenChange={setInviteOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Invite Title Rep</DialogTitle>
            <DialogDescription>
              Send an invitation to a new title representative to join your company.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-1.5">
              <Label className="text-xs font-medium">Email</Label>
              <Input
                type="email"
                placeholder="rep@company.com"
                value={inviteForm.email}
                onChange={(e) => setInviteForm((f) => ({ ...f, email: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs font-medium">First Name</Label>
                <Input
                  placeholder="Sarah"
                  value={inviteForm.first_name}
                  onChange={(e) => setInviteForm((f) => ({ ...f, first_name: e.target.value }))}
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs font-medium">Last Name</Label>
                <Input
                  placeholder="Martinez"
                  value={inviteForm.last_name}
                  onChange={(e) => setInviteForm((f) => ({ ...f, last_name: e.target.value }))}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setInviteOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleInviteRep} disabled={inviteSubmitting}>
              {inviteSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Send Invitation
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Resend Invite Modal */}
      <Dialog open={resendModal.open} onOpenChange={(o) => !o && setResendModal({ open: false, rep: null })}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Resend Invitation</DialogTitle>
            <DialogDescription>Send a new invitation email to this title rep.</DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                <span className="text-sm font-semibold text-primary">
                  {resendModal.rep?.name?.[0]?.toUpperCase()}
                </span>
              </div>
              <div>
                <p className="text-sm font-medium">{resendModal.rep?.name}</p>
                <p className="text-sm text-muted-foreground">{resendModal.rep?.email}</p>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setResendModal({ open: false, rep: null })}>
              Cancel
            </Button>
            <Button
              onClick={() => resendModal.rep && handleResendInvite(resendModal.rep)}
              disabled={resending}
            >
              {resending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Send Invitation
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function RepsSkeleton() {
  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <Skeleton className="h-4 w-32" />
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-7 w-32 mb-2" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-10 w-24 rounded-md" />
          <Skeleton className="h-10 w-32 rounded-md" />
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="rounded-xl border border-border bg-card p-4">
            <Skeleton className="h-3 w-20 mb-2" />
            <Skeleton className="h-7 w-12" />
          </div>
        ))}
      </div>
      <div className="flex gap-3">
        <Skeleton className="h-10 flex-1 rounded-md" />
        <Skeleton className="h-10 w-40 rounded-md" />
      </div>
      <div className="rounded-xl border border-border bg-card p-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex items-center gap-4 py-3">
            <Skeleton className="h-9 w-9 rounded-full" />
            <Skeleton className="h-4 w-32 flex-1" />
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
        ))}
      </div>
    </div>
  )
}

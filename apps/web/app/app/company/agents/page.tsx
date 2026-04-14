"use client"

import { useState, useMemo } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import {
  Search,
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
  ExternalLink,
  Users,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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
import { useCompanyAgents } from "@/hooks/use-api"

interface Agent {
  id: string
  name: string
  email: string
  brokerage: string
  rep_name: string
  rep_id: string
  reports_this_month: number
  total_reports: number
  last_active: string | null
  joined_date: string | null
  status: "active" | "pending" | "inactive"
  plan: "free" | "pro"
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

function getStatusBadge(status: Agent["status"]) {
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
    case "inactive":
      return (
        <Badge className="bg-[#F1F5F9] text-[#64748B] hover:bg-[#F1F5F9]">
          <AlertCircle className="mr-1 h-3 w-3" />
          Inactive
        </Badge>
      )
  }
}

function getPlanBadge(plan: Agent["plan"]) {
  if (plan === "pro") {
    return (
      <Badge className="bg-[#EEF2FF] text-[#4338CA] hover:bg-[#EEF2FF]">Pro</Badge>
    )
  }
  return (
    <Badge variant="outline" className="text-muted-foreground">Free</Badge>
  )
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

export default function AgentsListPage() {
  const searchParams = useSearchParams()
  const initialRepFilter = searchParams.get("rep") || "all"

  const { data, isLoading, error } = useCompanyAgents()

  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [repFilter, setRepFilter] = useState(initialRepFilter)
  const [planFilter, setPlanFilter] = useState("all")
  const [currentPage, setCurrentPage] = useState(1)

  const agents: Agent[] = data?.agents ?? []
  const repsForFilter: { id: string; name: string }[] = data?.reps ?? []

  const filteredAgents = useMemo(() => {
    return agents.filter((agent) => {
      const matchesSearch =
        !search ||
        agent.name.toLowerCase().includes(search.toLowerCase()) ||
        agent.email.toLowerCase().includes(search.toLowerCase()) ||
        agent.brokerage.toLowerCase().includes(search.toLowerCase())
      const matchesStatus = statusFilter === "all" || agent.status === statusFilter
      const matchesRep = repFilter === "all" || agent.rep_id === repFilter
      const matchesPlan = planFilter === "all" || agent.plan === planFilter
      return matchesSearch && matchesStatus && matchesRep && matchesPlan
    })
  }, [agents, search, statusFilter, repFilter, planFilter])

  const totalPages = Math.ceil(filteredAgents.length / PER_PAGE)
  const paginatedAgents = filteredAgents.slice(
    (currentPage - 1) * PER_PAGE,
    currentPage * PER_PAGE
  )

  const activeCount = agents.filter((a) => a.status === "active").length
  const pendingCount = agents.filter((a) => a.status === "pending").length
  const proCount = agents.filter((a) => a.plan === "pro").length
  const totalReports = agents.reduce((sum, a) => sum + a.reports_this_month, 0)

  if (isLoading) return <AgentsSkeleton />

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <Users className="h-16 w-16 text-muted-foreground mb-4" />
        <h1 className="text-2xl font-bold mb-2">Unable to Load Agents</h1>
        <p className="text-muted-foreground max-w-md mb-6">Failed to load agent data. Please try again.</p>
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
          <h1 className="text-2xl font-bold text-foreground">All Agents</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            View all agents across your title reps
          </p>
        </div>
        <Button variant="outline">
          <Download className="mr-2 h-4 w-4" />
          Export CSV
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="mt-6 grid gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Total Agents
          </p>
          <p className="mt-1 text-2xl font-bold text-foreground">{agents.length}</p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Active
          </p>
          <p className="mt-1 text-2xl font-bold text-[#16A34A]">{activeCount}</p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Pro Plans
          </p>
          <p className="mt-1 text-2xl font-bold text-[#6366F1]">{proCount}</p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Reports (30d)
          </p>
          <p className="mt-1 text-2xl font-bold text-foreground">{totalReports}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground/60" />
          <Input
            placeholder="Search by name, email, or brokerage..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setCurrentPage(1)
            }}
            className="pl-9"
          />
        </div>
        <Select
          value={repFilter}
          onValueChange={(v) => {
            setRepFilter(v)
            setCurrentPage(1)
          }}
        >
          <SelectTrigger className="w-full sm:w-44">
            <SelectValue placeholder="Rep" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Reps</SelectItem>
            {repsForFilter.map((rep) => (
              <SelectItem key={rep.id} value={rep.id}>
                {rep.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          value={statusFilter}
          onValueChange={(v) => {
            setStatusFilter(v)
            setCurrentPage(1)
          }}
        >
          <SelectTrigger className="w-full sm:w-36">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={planFilter}
          onValueChange={(v) => {
            setPlanFilter(v)
            setCurrentPage(1)
          }}
        >
          <SelectTrigger className="w-full sm:w-32">
            <SelectValue placeholder="Plan" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Plans</SelectItem>
            <SelectItem value="pro">Pro</SelectItem>
            <SelectItem value="free">Free</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="mt-6 overflow-hidden rounded-xl border border-border bg-card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                  Agent
                </th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                  Brokerage
                </th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                  Rep
                </th>
                <th className="px-4 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                  Reports (30d)
                </th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                  Last Active
                </th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                  Plan
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
              {paginatedAgents.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center">
                    <Users className="mx-auto h-10 w-10 text-muted-foreground/40 mb-3" />
                    <p className="text-sm font-medium text-muted-foreground">
                      {search || statusFilter !== "all" || repFilter !== "all" || planFilter !== "all"
                        ? "No agents match your filters"
                        : "No agents yet"}
                    </p>
                  </td>
                </tr>
              ) : (
                paginatedAgents.map((agent, idx) => (
                  <tr key={agent.id} className="transition-colors hover:bg-muted/30">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div
                          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white ${AVATAR_COLORS[idx % AVATAR_COLORS.length]}`}
                        >
                          {getInitials(agent.name)}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-foreground">{agent.name}</p>
                          <p className="text-xs text-muted-foreground">{agent.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {agent.brokerage || "—"}
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/app/company/agents?rep=${agent.rep_id}`}
                        className="text-sm text-[#6366F1] hover:underline"
                      >
                        {agent.rep_name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-center text-sm font-medium text-foreground tabular-nums">
                      {agent.reports_this_month}
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {formatRelativeTime(agent.last_active)}
                    </td>
                    <td className="px-4 py-3">{getPlanBadge(agent.plan)}</td>
                    <td className="px-4 py-3">{getStatusBadge(agent.status)}</td>
                    <td className="px-4 py-3 text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem asChild>
                            <Link href={`/app/company/agents?rep=${agent.rep_id}`}>
                              <Eye className="mr-2 h-4 w-4" />
                              View Rep&apos;s Agents
                            </Link>
                          </DropdownMenuItem>
                          {agent.status === "pending" && (
                            <DropdownMenuItem>
                              <Mail className="mr-2 h-4 w-4" />
                              Resend Invite
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          <DropdownMenuItem className="text-red-600">
                            <UserX className="mr-2 h-4 w-4" />
                            Remove from Company
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
        {filteredAgents.length > 0 && (
          <div className="flex items-center justify-between border-t border-border px-4 py-3">
            <p className="text-sm text-muted-foreground">
              Showing {(currentPage - 1) * PER_PAGE + 1} –{" "}
              {Math.min(currentPage * PER_PAGE, filteredAgents.length)} of{" "}
              {filteredAgents.length} agents
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
    </div>
  )
}

function AgentsSkeleton() {
  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <Skeleton className="h-4 w-32" />
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-7 w-28 mb-2" />
          <Skeleton className="h-4 w-56" />
        </div>
        <Skeleton className="h-10 w-28 rounded-md" />
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
        <Skeleton className="h-10 w-36 rounded-md" />
        <Skeleton className="h-10 w-32 rounded-md" />
        <Skeleton className="h-10 w-28 rounded-md" />
      </div>
      <div className="rounded-xl border border-border bg-card p-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex items-center gap-4 py-3">
            <Skeleton className="h-9 w-9 rounded-full" />
            <Skeleton className="h-4 w-32 flex-1" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-5 w-14 rounded-full" />
            <Skeleton className="h-5 w-14 rounded-full" />
          </div>
        ))}
      </div>
    </div>
  )
}

'use client'

import { useEffect, useState, useMemo } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Mail,
  AlertTriangle,
  CheckCircle,
  Send,
  Search,
  X,
  ChevronDown,
  ChevronUp,
  Percent,
} from "lucide-react"

interface EmailLog {
  id: string
  account_name: string
  account_id: string
  subject: string
  to_email: string | null
  to_count: number
  report_type: string | null
  sender: string | null
  status: string
  error: string | null
  created_at: string
}

const STATUS_STYLES: Record<string, string> = {
  delivered: "bg-green-100 text-green-800",
  sent: "bg-green-100 text-green-800",
  success: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  bounced: "bg-red-100 text-red-800",
  pending: "bg-yellow-100 text-yellow-800",
  queued: "bg-gray-100 text-gray-700",
}

const REPORT_TYPE_LABELS: Record<string, string> = {
  new_listings_gallery: "New Listings Gallery",
  closed: "Closed Sales",
  market_snapshot: "Market Snapshot",
  inventory: "Active Inventory",
  featured_listings: "Featured Listings",
  open_houses: "Open Houses",
  price_bands: "Price Bands",
  new_listings: "New Listings Analytics",
}

function formatTimeAgo(dateString: string | null): string {
  if (!dateString) return "—"
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return "Just now"
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 30) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

export default function AdminEmailsPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [emails, setEmails] = useState<EmailLog[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const filterStatus = searchParams.get("status") || "all"
  const [recipientSearch, setRecipientSearch] = useState(searchParams.get("q") || "")

  useEffect(() => {
    async function fetchEmails() {
      setLoading(true)
      try {
        const params = new URLSearchParams()
        if (filterStatus !== "all") params.set("status", filterStatus)
        const q = searchParams.get("q")
        if (q) params.set("q", q)
        params.set("limit", "200")

        const res = await fetch(`/api/proxy/v1/admin/emails?${params.toString()}`, { credentials: "include" })
        if (res.ok) {
          const data = await res.json()
          setEmails(data?.emails || data || [])
        }
      } catch (err) {
        console.error("Failed to fetch emails:", err)
      } finally {
        setLoading(false)
      }
    }
    fetchEmails()
  }, [searchParams, filterStatus])

  const stats = useMemo(() => {
    const now = new Date()
    const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
    const recent = emails.filter(e => new Date(e.created_at) >= thirtyDaysAgo)
    const total = recent.length
    const failed = recent.filter(e => e.status === "failed" || e.status === "bounced").length
    const delivered = recent.filter(e => e.status === "delivered" || e.status === "sent" || e.status === "success").length
    const deliveryRate = total > 0 ? Math.round((delivered / total) * 100) : 0

    return { total, failed, deliveryRate }
  }, [emails])

  function updateFilter(key: string, value: string) {
    const params = new URLSearchParams(searchParams.toString())
    if (value && value !== "all") {
      params.set(key, value)
    } else {
      params.delete(key)
    }
    router.push(`/app/admin/emails?${params.toString()}`)
  }

  function clearFilters() {
    setRecipientSearch("")
    router.push("/app/admin/emails")
  }

  const hasFilters = filterStatus !== "all" || searchParams.get("q")

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-9 w-48 mb-2" />
          <Skeleton className="h-5 w-72" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <Card key={i}><CardContent className="pt-6"><Skeleton className="h-8 w-16" /></CardContent></Card>
          ))}
        </div>
        <Card><CardContent className="pt-6">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="py-3 flex gap-4">
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-5 w-16 rounded-full" />
            </div>
          ))}
        </CardContent></Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-display font-bold">Email Delivery</h1>
        <p className="text-muted-foreground mt-2">Email delivery logs across all accounts</p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sent (30d)</CardTitle>
            <Send className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent><div className="text-2xl font-bold">{stats.total}</div></CardContent>
        </Card>
        <Card className={stats.failed > 0 ? "bg-red-50 border-red-200" : ""}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed (30d)</CardTitle>
            <AlertTriangle className={`h-4 w-4 ${stats.failed > 0 ? "text-red-500" : "text-muted-foreground"}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stats.failed > 0 ? "text-red-600" : ""}`}>{stats.failed}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Delivery Rate</CardTitle>
            <Percent className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stats.deliveryRate < 90 ? "text-yellow-600" : stats.deliveryRate >= 95 ? "text-green-600" : ""}`}>
              {stats.deliveryRate}%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by recipient or account..."
            value={recipientSearch}
            onChange={(e) => setRecipientSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && updateFilter("q", recipientSearch)}
            className="pl-9"
          />
        </div>

        <Select value={filterStatus} onValueChange={(v) => updateFilter("status", v)}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="delivered">Delivered</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
            <SelectItem value="bounced">Bounced</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
          </SelectContent>
        </Select>

        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            <X className="w-4 h-4 mr-1" />
            Clear
          </Button>
        )}
      </div>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Email Logs ({emails.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {emails.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No email logs found</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-[11px] uppercase tracking-wider w-8" />
                  <TableHead className="text-[11px] uppercase tracking-wider">Recipient</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Subject</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Account</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Status</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Sent</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {emails.map((email) => {
                  const isExpanded = expandedId === email.id
                  const isFailed = email.status === "failed" || email.status === "bounced"
                  return (
                    <>
                      <TableRow
                        key={email.id}
                        className="cursor-pointer hover:bg-muted/50"
                        onClick={() => setExpandedId(isExpanded ? null : email.id)}
                      >
                        <TableCell className="w-8 pr-0">
                          {isExpanded ? (
                            <ChevronUp className="w-4 h-4 text-muted-foreground" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-muted-foreground" />
                          )}
                        </TableCell>
                        <TableCell>
                          <p className="text-sm font-medium truncate max-w-[180px]">
                            {email.to_email || `${email.to_count} recipient${email.to_count !== 1 ? "s" : ""}`}
                          </p>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground truncate max-w-[220px]">
                          {email.subject}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">{email.account_name}</TableCell>
                        <TableCell>
                          <Badge className={STATUS_STYLES[email.status] || "bg-gray-100"}>
                            {email.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {formatTimeAgo(email.created_at)}
                        </TableCell>
                      </TableRow>
                      {isExpanded && (
                        <TableRow key={`${email.id}-detail`}>
                          <TableCell colSpan={6} className="bg-muted/30 py-3 px-6">
                            <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
                              <div>
                                <span className="text-muted-foreground">Subject:</span>
                                <p className="font-medium">{email.subject}</p>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Recipients:</span>
                                <p className="font-medium">
                                  {email.to_email || `${email.to_count} recipient${email.to_count !== 1 ? "s" : ""}`}
                                </p>
                              </div>
                              {email.sender && (
                                <div>
                                  <span className="text-muted-foreground">Sender:</span>
                                  <p className="font-medium">{email.sender}</p>
                                </div>
                              )}
                              {email.report_type && (
                                <div>
                                  <span className="text-muted-foreground">Report Type:</span>
                                  <p className="font-medium">{REPORT_TYPE_LABELS[email.report_type] || email.report_type}</p>
                                </div>
                              )}
                              {isFailed && email.error && (
                                <div className="col-span-2">
                                  <span className="text-red-600 font-medium">Error:</span>
                                  <p className="text-red-600 text-xs mt-0.5 font-mono bg-red-50 p-2 rounded">{email.error}</p>
                                </div>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      )}
                    </>
                  )
                })}
              </TableBody>
            </Table>
          )}
          {emails.length > 0 && (
            <p className="text-xs text-muted-foreground text-center mt-4">
              Showing {emails.length} email{emails.length !== 1 ? "s" : ""}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

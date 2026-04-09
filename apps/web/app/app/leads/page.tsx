"use client"

import { useState, useMemo } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Skeleton } from "@/components/ui/skeleton"
import { PageHeader } from "@/components/page-header"
import { MetricCard } from "@/components/metric-card"
import { StatusBadge } from "@/components/status-badge"
import { EmptyState } from "@/components/empty-state"
import {
  Download,
  Search,
  Mail,
  Phone,
  MessageSquare,
  MoreVertical,
  ExternalLink,
  Check,
  Clock,
  UserCheck,
  Loader2,
  Filter,
  X,
  Users,
  Sparkles,
  PhoneCall,
  Trophy,
} from "lucide-react"
import { apiFetch } from "@/lib/api"
import { useAllLeads, usePropertyReports, useInvalidate } from "@/hooks/use-api"

type Lead = {
  id: string
  name: string
  email: string
  phone?: string
  message?: string
  source: "qr_scan" | "direct_link"
  consent_given: boolean
  status: "new" | "contacted" | "converted"
  property_report_id?: string
  property_address?: string
  sms_sent_at?: string
  email_sent_at?: string
  created_at: string
}

type PropertyReport = {
  id: string
  property_address: string
}

type LeadStats = {
  total: number
  newThisWeek: number
  contacted: number
  converted: number
}

export default function LeadsPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const invalidate = useInvalidate()
  
  // React Query hooks
  const { data: allLeadsData, isLoading: loading, error: queryError } = useAllLeads()
  const { data: propertyData } = usePropertyReports()
  
  const allLeads: Lead[] = allLeadsData?.leads || []
  const properties: PropertyReport[] = propertyData?.reports || []
  const error = queryError ? String(queryError) : null
  
  // Filters
  const [statusFilter, setStatusFilter] = useState<string>(searchParams.get("status") || "all")
  const [propertyFilter, setPropertyFilter] = useState<string>(searchParams.get("property_report_id") || "all")
  const [searchQuery, setSearchQuery] = useState("")
  
  // Lead detail modal
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null)
  
  // Export loading
  const [exporting, setExporting] = useState(false)
  
  // Compute leads based on filters (client-side)
  const leads = useMemo(() => {
    let filtered = allLeads
    if (statusFilter && statusFilter !== "all") {
      filtered = filtered.filter((l) => l.status === statusFilter)
    }
    if (propertyFilter && propertyFilter !== "all") {
      filtered = filtered.filter((l) => l.property_report_id === propertyFilter)
    }
    return filtered
  }, [allLeads, statusFilter, propertyFilter])
  
  const total = leads.length
  
  // Compute stats from all leads (cached data, no extra API call)
  const stats = useMemo<LeadStats>(() => {
    const now = new Date()
    const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
    return {
      total: allLeads.length,
      newThisWeek: allLeads.filter((l) => 
        l.status === "new" && new Date(l.created_at) >= oneWeekAgo
      ).length,
      contacted: allLeads.filter((l) => l.status === "contacted").length,
      converted: allLeads.filter((l) => l.status === "converted").length,
    }
  }, [allLeads])

  async function updateLeadStatus(leadId: string, status: string) {
    try {
      await apiFetch(`/v1/leads/${leadId}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      })
      // Invalidate leads cache to refresh data
      invalidate.leads()
      if (selectedLead?.id === leadId) {
        setSelectedLead({ ...selectedLead, status: status as Lead["status"] })
      }
    } catch (e: any) {
      // Show error inline if needed
      console.error("Failed to update lead:", e)
    }
  }

  async function exportCSV() {
    try {
      setExporting(true)
      const response = await fetch("/api/proxy/v1/leads/export/csv", {
        credentials: "include",
      })
      
      if (!response.ok) throw new Error("Export failed")
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `leads-${new Date().toISOString().split("T")[0]}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (e: any) {
      console.error("Export failed:", e)
    } finally {
      setExporting(false)
    }
  }


  const getSourceBadge = (source: string) => {
    return source === "qr_scan" 
      ? <Badge variant="outline" className="border-indigo-300 text-indigo-700">QR Scan</Badge>
      : <Badge variant="outline" className="border-blue-300 text-blue-700">Direct Link</Badge>
  }

  const filteredLeads = leads.filter((lead) => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      lead.name.toLowerCase().includes(query) ||
      lead.email.toLowerCase().includes(query) ||
      lead.phone?.toLowerCase().includes(query) ||
      lead.property_address?.toLowerCase().includes(query)
    )
  })

  if (loading && leads.length === 0) {
    return (
      <div className="space-y-5">
        <PageHeader title="Leads" description="Lead capture from property reports" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-card border border-border rounded-xl p-4">
              <Skeleton className="h-3 w-20 mb-3" />
              <Skeleton className="h-7 w-12" />
            </div>
          ))}
        </div>
        <LeadsTableSkeleton />
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Leads"
        description={`${total} lead${total !== 1 ? "s" : ""} captured from property reports`}
        action={
          <Button size="sm" onClick={exportCSV} disabled={exporting}>
            {exporting ? (
              <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
            ) : (
              <Download className="w-4 h-4 mr-1.5" />
            )}
            Export CSV
          </Button>
        }
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard label="Total Leads" value={stats.total} icon={<Users className="w-4 h-4" />} index={0} />
        <MetricCard label="New This Week" value={stats.newThisWeek} icon={<Sparkles className="w-4 h-4" />} index={1} />
        <MetricCard label="Contacted" value={stats.contacted} icon={<PhoneCall className="w-4 h-4" />} index={2} />
        <MetricCard label="Converted" value={stats.converted} icon={<Trophy className="w-4 h-4" />} index={3} />
      </div>

      {error && (
        <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search leads..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[150px]">
            <Filter className="w-4 h-4 mr-2" />
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="new">New</SelectItem>
            <SelectItem value="contacted">Contacted</SelectItem>
            <SelectItem value="converted">Converted</SelectItem>
          </SelectContent>
        </Select>

        <Select value={propertyFilter} onValueChange={setPropertyFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All Properties" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Properties</SelectItem>
            {properties.map((p) => (
              <SelectItem key={p.id} value={p.id}>
                {p.property_address.slice(0, 30)}...
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {(statusFilter !== "all" || propertyFilter !== "all" || searchQuery) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setStatusFilter("all")
              setPropertyFilter("all")
              setSearchQuery("")
            }}
          >
            <X className="w-4 h-4 mr-1" />
            Clear
          </Button>
        )}
      </div>

      {/* Table */}
      {filteredLeads.length === 0 && !searchQuery && statusFilter === "all" && propertyFilter === "all" ? (
        <EmptyState
          icon={<Users className="w-6 h-6" />}
          title="No leads captured yet"
          description="Leads will appear here once visitors interact with your property reports."
        />
      ) : (
        <div className="bg-card border border-border rounded-xl overflow-hidden shadow-[var(--shadow-card)]">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/40 hover:bg-muted/40 border-b border-border">
                <TableHead className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] py-2.5">Lead</TableHead>
                <TableHead className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] py-2.5">Property</TableHead>
                <TableHead className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] py-2.5">Source</TableHead>
                <TableHead className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] py-2.5">Status</TableHead>
                <TableHead className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] py-2.5">Date</TableHead>
                <TableHead className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] py-2.5 w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredLeads.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-32 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <Users className="w-8 h-8 text-muted-foreground" />
                      <p className="text-sm text-muted-foreground">No leads match your filters</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                filteredLeads.map((lead) => (
                  <TableRow
                    key={lead.id}
                    className="cursor-pointer hover:bg-muted/30 transition-colors"
                    onClick={() => setSelectedLead(lead)}
                  >
                    <TableCell>
                      <div>
                        <p className="font-medium text-sm">{lead.name}</p>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <Mail className="w-3 h-3" />
                          {lead.email}
                        </div>
                        {lead.phone && (
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Phone className="w-3 h-3" />
                            {lead.phone}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {lead.property_address ? (
                        <span className="text-sm">{lead.property_address}</span>
                      ) : (
                        <span className="text-sm text-muted-foreground">N/A</span>
                      )}
                    </TableCell>
                    <TableCell>{getSourceBadge(lead.source)}</TableCell>
                    <TableCell><StatusBadge status={lead.status} /></TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">{new Date(lead.created_at).toLocaleDateString()}</span>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreVertical className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => setSelectedLead(lead)}>
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => updateLeadStatus(lead.id, "new")}>
                            <Clock className="w-4 h-4 mr-2" />
                            Mark as New
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => updateLeadStatus(lead.id, "contacted")}>
                            <Phone className="w-4 h-4 mr-2" />
                            Mark as Contacted
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => updateLeadStatus(lead.id, "converted")}>
                            <UserCheck className="w-4 h-4 mr-2" />
                            Mark as Converted
                          </DropdownMenuItem>
                          {lead.property_report_id && (
                            <>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={() => router.push(`/app/property/${lead.property_report_id}`)}
                              >
                                <ExternalLink className="w-4 h-4 mr-2" />
                                View Property Report
                              </DropdownMenuItem>
                            </>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>

          {/* Footer */}
          <div className="flex items-center justify-between px-4 py-2.5 border-t border-border bg-muted/20">
            <p className="text-[11px] text-muted-foreground">
              Showing {filteredLeads.length} lead{filteredLeads.length !== 1 ? "s" : ""}
            </p>
          </div>
        </div>
      )}

      {/* Lead Detail Modal */}
      <Dialog open={!!selectedLead} onOpenChange={() => setSelectedLead(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Lead Details</DialogTitle>
            <DialogDescription>
              Captured on {selectedLead && new Date(selectedLead.created_at).toLocaleString()}
            </DialogDescription>
          </DialogHeader>
          
          {selectedLead && (
            <div className="space-y-6">
              {/* Contact Info */}
              <div className="space-y-3">
                <h4 className="font-medium text-sm text-muted-foreground">Contact Information</h4>
                <div className="space-y-2">
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                      <span className="text-primary font-semibold">
                        {selectedLead.name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium">{selectedLead.name}</p>
                      <div className="flex items-center gap-1 text-sm text-muted-foreground">
                        {getSourceBadge(selectedLead.source)}
                        <StatusBadge status={selectedLead.status} />
                      </div>
                    </div>
                  </div>
                  
                  <a
                    href={`mailto:${selectedLead.email}`}
                    className="flex items-center gap-3 p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                  >
                    <Mail className="w-5 h-5 text-muted-foreground" />
                    <span className="text-sm">{selectedLead.email}</span>
                  </a>
                  
                  {selectedLead.phone && (
                    <a
                      href={`tel:${selectedLead.phone}`}
                      className="flex items-center gap-3 p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                    >
                      <Phone className="w-5 h-5 text-muted-foreground" />
                      <span className="text-sm">{selectedLead.phone}</span>
                    </a>
                  )}
                </div>
              </div>

              {/* Message */}
              {selectedLead.message && (
                <div className="space-y-2">
                  <h4 className="font-medium text-sm text-muted-foreground">Message</h4>
                  <div className="p-3 rounded-lg bg-muted/50">
                    <MessageSquare className="w-4 h-4 text-muted-foreground mb-2" />
                    <p className="text-sm">{selectedLead.message}</p>
                  </div>
                </div>
              )}

              {/* Property */}
              {selectedLead.property_address && (
                <div className="space-y-2">
                  <h4 className="font-medium text-sm text-muted-foreground">Property</h4>
                  <div
                    className="p-3 rounded-lg border hover:bg-muted/50 transition-colors cursor-pointer"
                    onClick={() => {
                      setSelectedLead(null)
                      router.push(`/app/property/${selectedLead.property_report_id}`)
                    }}
                  >
                    <p className="font-medium text-sm">{selectedLead.property_address}</p>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                      <ExternalLink className="w-3 h-3" />
                      View property report
                    </div>
                  </div>
                </div>
              )}

              {/* Notifications Sent */}
              <div className="space-y-2">
                <h4 className="font-medium text-sm text-muted-foreground">Notifications</h4>
                <div className="flex gap-3">
                  <div className="flex items-center gap-2 text-sm">
                    {selectedLead.sms_sent_at ? (
                      <>
                        <Check className="w-4 h-4 text-green-500" />
                        <span>SMS sent</span>
                      </>
                    ) : (
                      <>
                        <X className="w-4 h-4 text-muted-foreground" />
                        <span className="text-muted-foreground">No SMS</span>
                      </>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    {selectedLead.email_sent_at ? (
                      <>
                        <Check className="w-4 h-4 text-green-500" />
                        <span>Email sent</span>
                      </>
                    ) : (
                      <>
                        <X className="w-4 h-4 text-muted-foreground" />
                        <span className="text-muted-foreground">No email</span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="flex gap-2 pt-4 border-t">
                <Button
                  variant={selectedLead.status === "new" ? "default" : "outline"}
                  size="sm"
                  className="flex-1"
                  onClick={() => updateLeadStatus(selectedLead.id, "new")}
                >
                  <Clock className="w-4 h-4 mr-1" />
                  New
                </Button>
                <Button
                  variant={selectedLead.status === "contacted" ? "default" : "outline"}
                  size="sm"
                  className="flex-1"
                  onClick={() => updateLeadStatus(selectedLead.id, "contacted")}
                >
                  <Phone className="w-4 h-4 mr-1" />
                  Contacted
                </Button>
                <Button
                  variant={selectedLead.status === "converted" ? "default" : "outline"}
                  size="sm"
                  className="flex-1"
                  onClick={() => updateLeadStatus(selectedLead.id, "converted")}
                >
                  <UserCheck className="w-4 h-4 mr-1" />
                  Converted
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

function LeadsTableSkeleton() {
  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden shadow-[var(--shadow-card)]">
      <div className="px-4 py-3 border-b border-border bg-muted/40">
        <div className="grid grid-cols-6 gap-4">
          {["Lead", "Property", "Source", "Status", "Date", ""].map((h) => (
            <Skeleton key={h || "actions"} className="h-3 w-16" />
          ))}
        </div>
      </div>
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="px-4 py-3 border-b border-border/50 flex items-center gap-4">
          <Skeleton className="h-4 w-28 flex-1" />
          <Skeleton className="h-4 w-24 flex-1" />
          <Skeleton className="h-5 w-16 rounded-full flex-1" />
          <Skeleton className="h-5 w-16 rounded-full flex-1" />
          <Skeleton className="h-4 w-20 flex-1" />
          <Skeleton className="h-8 w-8 rounded flex-shrink-0" />
        </div>
      ))}
    </div>
  )
}

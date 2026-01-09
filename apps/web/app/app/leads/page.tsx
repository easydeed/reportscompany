"use client"

import { useEffect, useState } from "react"
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
} from "lucide-react"
import { apiFetch } from "@/lib/api"

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

export default function LeadsPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  
  // Filters
  const [statusFilter, setStatusFilter] = useState<string>(searchParams.get("status") || "all")
  const [propertyFilter, setPropertyFilter] = useState<string>(searchParams.get("property_report_id") || "all")
  const [searchQuery, setSearchQuery] = useState("")
  
  // Properties for filter dropdown
  const [properties, setProperties] = useState<PropertyReport[]>([])
  
  // Lead detail modal
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null)
  
  // Export loading
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    loadLeads()
    loadProperties()
  }, [statusFilter, propertyFilter])

  async function loadLeads() {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (statusFilter && statusFilter !== "all") params.set("status", statusFilter)
      if (propertyFilter && propertyFilter !== "all") params.set("property_report_id", propertyFilter)
      
      const data = await apiFetch(`/v1/leads?${params.toString()}`)
      setLeads(data.leads || [])
      setTotal(data.total || 0)
      setError(null)
    } catch (e: any) {
      setError(e.message || "Failed to load leads")
    } finally {
      setLoading(false)
    }
  }

  async function loadProperties() {
    try {
      const data = await apiFetch("/v1/property/reports?limit=100")
      setProperties(data.reports || [])
    } catch {
      // Ignore error
    }
  }

  async function updateLeadStatus(leadId: string, status: string) {
    try {
      await apiFetch(`/v1/leads/${leadId}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      })
      setLeads((prev) =>
        prev.map((l) => (l.id === leadId ? { ...l, status: status as Lead["status"] } : l))
      )
      if (selectedLead?.id === leadId) {
        setSelectedLead({ ...selectedLead, status: status as Lead["status"] })
      }
    } catch (e: any) {
      setError(e.message || "Failed to update lead")
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
      setError(e.message || "Failed to export")
    } finally {
      setExporting(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "new":
        return <Badge className="bg-blue-500/10 text-blue-700 hover:bg-blue-500/20">New</Badge>
      case "contacted":
        return <Badge className="bg-yellow-500/10 text-yellow-700 hover:bg-yellow-500/20">Contacted</Badge>
      case "converted":
        return <Badge className="bg-green-500/10 text-green-700 hover:bg-green-500/20">Converted</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const getSourceBadge = (source: string) => {
    return source === "qr_scan" 
      ? <Badge variant="outline" className="border-purple-300 text-purple-700">QR Scan</Badge>
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
      <div className="space-y-6">
        <h1 className="font-bold text-3xl">Leads</h1>
        <p className="text-muted-foreground">Loading...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-bold text-3xl mb-2">Leads</h1>
          <p className="text-muted-foreground">
            {total} lead{total !== 1 ? "s" : ""} captured from property reports
          </p>
        </div>
        <Button onClick={exportCSV} disabled={exporting} variant="outline">
          {exporting ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Download className="w-4 h-4 mr-2" />
          )}
          Export CSV
        </Button>
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
      <div className="rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Lead</TableHead>
              <TableHead>Property</TableHead>
              <TableHead>Source</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Date</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredLeads.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="h-32 text-center">
                  <div className="flex flex-col items-center gap-2">
                    <p className="text-sm text-muted-foreground">
                      {searchQuery || statusFilter !== "all" || propertyFilter !== "all"
                        ? "No leads match your filters"
                        : "No leads captured yet"}
                    </p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              filteredLeads.map((lead) => (
                <TableRow
                  key={lead.id}
                  className="cursor-pointer"
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
                  <TableCell>{getStatusBadge(lead.status)}</TableCell>
                  <TableCell>
                    <span className="text-sm">{new Date(lead.created_at).toLocaleDateString()}</span>
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
      </div>

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
                        {getStatusBadge(selectedLead.status)}
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


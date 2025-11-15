"use client"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Plus, Download, Eye, MoreHorizontal, Search, Filter, FileText, Clock, TrendingUp } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import Link from "next/link"
import { useState } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

const reports = [
  {
    id: "rpt_001",
    title: "Market Analysis - Downtown SF",
    type: "Market Analysis",
    location: "San Francisco, CA",
    created: "2024-01-15",
    views: 45,
    status: "Published",
  },
  {
    id: "rpt_002",
    title: "Neighborhood Comparison - Mission",
    type: "Neighborhood Comparison",
    location: "San Francisco, CA",
    created: "2024-01-14",
    views: 32,
    status: "Published",
  },
  {
    id: "rpt_003",
    title: "Investment Analysis - Oakland",
    type: "Investment Analysis",
    location: "Oakland, CA",
    created: "2024-01-13",
    views: 28,
    status: "Draft",
  },
  {
    id: "rpt_004",
    title: "CMA Report - Berkeley Hills",
    type: "CMA Report",
    location: "Berkeley, CA",
    created: "2024-01-12",
    views: 56,
    status: "Published",
  },
  {
    id: "rpt_005",
    title: "Market Trends - Palo Alto",
    type: "Market Analysis",
    location: "Palo Alto, CA",
    created: "2024-01-11",
    views: 41,
    status: "Published",
  },
  {
    id: "rpt_006",
    title: "Investment Opportunity - San Jose",
    type: "Investment Analysis",
    location: "San Jose, CA",
    created: "2024-01-10",
    views: 19,
    status: "Processing",
  },
]

export default function ReportsPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")

  const filteredReports = reports.filter((report) => {
    const matchesSearch =
      report.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      report.location.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === "all" || report.status.toLowerCase() === statusFilter.toLowerCase()
    return matchesSearch && matchesStatus
  })

  const getStatusBadge = (status: string) => {
    const styles = {
      Published: "bg-green-500/10 text-green-700 hover:bg-green-500/20 border border-green-500/20",
      Draft: "bg-slate-500/10 text-slate-700 hover:bg-slate-500/20 border border-slate-500/20",
      Processing: "bg-primary/10 text-primary hover:bg-primary/20 border border-primary/20",
      Failed: "bg-red-500/10 text-red-700 hover:bg-red-500/20 border border-red-500/20",
    }
    return styles[status as keyof typeof styles] || styles.Draft
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="font-display font-bold text-3xl mb-2 text-balance">Reports</h1>
          <p className="text-muted-foreground text-pretty">Manage and generate your market reports</p>
        </div>
        <Link href="/dashboard/reports/new">
          <Button size="lg" className="gap-2 bg-gradient-to-r from-primary to-primary/80 hover:opacity-90">
            <Plus className="w-4 h-4" />
            New Report
          </Button>
        </Link>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="p-4 border-border/50 bg-card hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Total Reports</p>
              <p className="text-2xl font-display font-bold text-foreground">{reports.length}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4 border-border/50 bg-card hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center text-green-600">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Published</p>
              <p className="text-2xl font-display font-bold text-foreground">
                {reports.filter((r) => r.status === "Published").length}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4 border-border/50 bg-card hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Processing</p>
              <p className="text-2xl font-display font-bold text-foreground">
                {reports.filter((r) => r.status === "Processing").length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      <Card className="p-4 border-border/50 bg-card">
        <div className="flex flex-col gap-4 md:flex-row md:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search reports by title or location..."
              className="pl-9"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <Filter className="w-4 h-4 mr-2" />
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="published">Published</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="processing">Processing</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="icon">
              <Download className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </Card>

      <Card className="border-border/50 bg-card">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50 hover:bg-muted/50">
                <TableHead className="font-display font-semibold">Report</TableHead>
                <TableHead className="font-display font-semibold">Location</TableHead>
                <TableHead className="font-display font-semibold">Created</TableHead>
                <TableHead className="font-display font-semibold">Views</TableHead>
                <TableHead className="font-display font-semibold">Status</TableHead>
                <TableHead className="font-display font-semibold w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredReports.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-12">
                    <div className="flex flex-col items-center gap-2">
                      <FileText className="w-12 h-12 text-muted-foreground/50" />
                      <p className="text-muted-foreground font-medium">No reports found</p>
                      <p className="text-sm text-muted-foreground">Try adjusting your search or filters</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                filteredReports.map((report) => (
                  <TableRow key={report.id} className="hover:bg-muted/50 cursor-pointer group transition-colors">
                    <TableCell>
                      <div>
                        <p className="font-medium text-sm group-hover:text-primary transition-colors">{report.title}</p>
                        <p className="text-xs text-muted-foreground">{report.type}</p>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">{report.location}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{report.created}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-sm">
                        <Eye className="w-3 h-3 text-muted-foreground" />
                        <span>{report.views}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={getStatusBadge(report.status)}>{report.status}</Badge>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>
                            <Eye className="w-4 h-4 mr-2" />
                            View Report
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Download className="w-4 h-4 mr-2" />
                            Download PDF
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem className="text-destructive">Delete</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </Card>
    </div>
  )
}

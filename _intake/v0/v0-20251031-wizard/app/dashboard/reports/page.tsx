"use client"

import { Button } from "@/components/ui/button"
import { DataTable } from "@/components/data-table"
import { Plus, Download, Eye, MoreHorizontal } from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import Link from "next/link"

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
]

const columns = [
  {
    header: "Report",
    accessorKey: "title",
    cell: (row: any) => (
      <div>
        <p className="font-medium text-sm">{row.title}</p>
        <p className="text-xs text-muted-foreground">{row.type}</p>
      </div>
    ),
  },
  {
    header: "Location",
    accessorKey: "location",
  },
  {
    header: "Created",
    accessorKey: "created",
  },
  {
    header: "Views",
    accessorKey: "views",
  },
  {
    header: "Status",
    accessorKey: "status",
    cell: (row: any) => (
      <span
        className={`text-xs px-2 py-1 rounded-full font-medium ${
          row.status === "Published" ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
        }`}
      >
        {row.status}
      </span>
    ),
  },
  {
    header: "",
    accessorKey: "actions",
    cell: (row: any) => (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <MoreHorizontal className="w-4 h-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem>
            <Eye className="w-4 h-4 mr-2" />
            View
          </DropdownMenuItem>
          <DropdownMenuItem>
            <Download className="w-4 h-4 mr-2" />
            Download
          </DropdownMenuItem>
          <DropdownMenuItem className="text-destructive">Delete</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
]

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display font-bold text-3xl mb-2">Reports</h1>
          <p className="text-muted-foreground">Manage and generate your market reports</p>
        </div>
        <Link href="/dashboard/reports/new">
          <Button className="gap-2">
            <Plus className="w-4 h-4" />
            New Report
          </Button>
        </Link>
      </div>

      <DataTable columns={columns} data={reports} />
    </div>
  )
}

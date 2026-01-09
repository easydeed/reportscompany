"use client"

import { useRouter, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Search, X, Download, Loader2 } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"

export function LeadsFilters() {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  const [account, setAccount] = useState(searchParams.get("account") || "")
  const [exporting, setExporting] = useState(false)
  const status = searchParams.get("status") || "all"

  function updateFilters(key: string, value: string) {
    const params = new URLSearchParams(searchParams.toString())
    if (value && value !== "all") {
      params.set(key, value)
    } else {
      params.delete(key)
    }
    router.push(`/app/admin/leads?${params.toString()}`)
  }

  function clearFilters() {
    setAccount("")
    router.push("/app/admin/leads")
  }

  function handleAccountSearch() {
    updateFilters("account", account)
  }

  async function exportCSV() {
    setExporting(true)
    try {
      const response = await fetch("/api/proxy/v1/admin/leads/export", {
        credentials: "include",
      })
      
      if (!response.ok) throw new Error("Export failed")
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `all-leads-${new Date().toISOString().split("T")[0]}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success("CSV exported successfully")
    } catch {
      toast.error("Failed to export CSV")
    } finally {
      setExporting(false)
    }
  }

  const hasFilters = status !== "all" || account

  return (
    <div className="flex flex-wrap gap-3 items-center justify-between">
      <div className="flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by account..."
            value={account}
            onChange={(e) => setAccount(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAccountSearch()}
            className="pl-9"
          />
        </div>

        <Select value={status} onValueChange={(v) => updateFilters("status", v)}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="new">New</SelectItem>
            <SelectItem value="contacted">Contacted</SelectItem>
            <SelectItem value="converted">Converted</SelectItem>
          </SelectContent>
        </Select>

        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            <X className="w-4 h-4 mr-1" />
            Clear
          </Button>
        )}
      </div>

      <Button variant="outline" onClick={exportCSV} disabled={exporting}>
        {exporting ? (
          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
        ) : (
          <Download className="w-4 h-4 mr-2" />
        )}
        Export All
      </Button>
    </div>
  )
}


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
import { Search, X } from "lucide-react"
import { useState } from "react"

export function PropertyReportsFilters() {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  const [account, setAccount] = useState(searchParams.get("account") || "")
  const status = searchParams.get("status") || "all"

  function updateFilters(key: string, value: string) {
    const params = new URLSearchParams(searchParams.toString())
    if (value && value !== "all") {
      params.set(key, value)
    } else {
      params.delete(key)
    }
    router.push(`/app/admin/property-reports?${params.toString()}`)
  }

  function clearFilters() {
    setAccount("")
    router.push("/app/admin/property-reports")
  }

  function handleAccountSearch() {
    updateFilters("account", account)
  }

  const hasFilters = status !== "all" || account

  return (
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
          <SelectItem value="complete">Complete</SelectItem>
          <SelectItem value="processing">Processing</SelectItem>
          <SelectItem value="draft">Draft</SelectItem>
          <SelectItem value="failed">Failed</SelectItem>
        </SelectContent>
      </Select>

      {hasFilters && (
        <Button variant="ghost" size="sm" onClick={clearFilters}>
          <X className="w-4 h-4 mr-1" />
          Clear
        </Button>
      )}
    </div>
  )
}


"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Building,
  Search,
  Settings,
  Loader2,
  RefreshCw,
  FileText,
  Users,
  TrendingUp,
} from "lucide-react"

interface Account {
  account_id: string
  name: string
  slug: string
  account_type: string
  plan_slug: string
  is_active: boolean
  sponsor_name: string | null
  created_at: string
  user_count: number
  reports_this_month: number
}

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [typeFilter, setTypeFilter] = useState<string>("all")
  const [planFilter, setPlanFilter] = useState<string>("all")
  const [total, setTotal] = useState(0)

  useEffect(() => {
    fetchAccounts()
  }, [search, typeFilter, planFilter])

  async function fetchAccounts() {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (search) params.set("search", search)
      if (typeFilter !== "all") params.set("account_type", typeFilter)
      if (planFilter !== "all") params.set("plan_slug", planFilter)

      const res = await fetch(`/api/v1/admin/accounts?${params.toString()}`, {
        credentials: "include",
      })
      if (res.ok) {
        const data = await res.json()
        setAccounts(data.accounts || [])
        setTotal(data.total || 0)
      }
    } catch (error) {
      console.error("Failed to fetch accounts:", error)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString()
  }

  // Calculate totals
  const totalUsers = accounts.reduce((sum, a) => sum + a.user_count, 0)
  const totalReports = accounts.reduce((sum, a) => sum + a.reports_this_month, 0)

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Accounts</h1>
          <p className="text-slate-500 mt-1">Manage all accounts and their settings</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Accounts</p>
                <p className="text-2xl font-bold text-slate-900">{total}</p>
              </div>
              <Building className="h-8 w-8 text-indigo-200" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Users</p>
                <p className="text-2xl font-bold text-slate-900">{totalUsers}</p>
              </div>
              <Users className="h-8 w-8 text-blue-200" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Reports This Month</p>
                <p className="text-2xl font-bold text-slate-900">{totalReports}</p>
              </div>
              <FileText className="h-8 w-8 text-emerald-200" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Avg Reports/Account</p>
                <p className="text-2xl font-bold text-slate-900">
                  {accounts.length > 0 ? (totalReports / accounts.length).toFixed(1) : 0}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-orange-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <div className="relative flex-1 min-w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by name or slug..."
                className="pl-10 bg-white border-slate-300 text-slate-900"
              />
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-40 bg-white border-slate-300 text-slate-900">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent className="bg-white border-slate-200">
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="REGULAR">Regular</SelectItem>
                <SelectItem value="INDUSTRY_AFFILIATE">Affiliate</SelectItem>
              </SelectContent>
            </Select>
            <Select value={planFilter} onValueChange={setPlanFilter}>
              <SelectTrigger className="w-40 bg-white border-slate-300 text-slate-900">
                <SelectValue placeholder="Plan" />
              </SelectTrigger>
              <SelectContent className="bg-white border-slate-200">
                <SelectItem value="all">All Plans</SelectItem>
                <SelectItem value="free">Free</SelectItem>
                <SelectItem value="pro">Pro</SelectItem>
                <SelectItem value="team">Team</SelectItem>
                <SelectItem value="affiliate">Affiliate</SelectItem>
                <SelectItem value="sponsored_free">Sponsored Free</SelectItem>
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              onClick={fetchAccounts}
              className="border-slate-300 text-slate-600 hover:bg-slate-50"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Accounts Table */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardContent className="pt-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
            </div>
          ) : accounts.length === 0 ? (
            <div className="text-center py-12">
              <Building className="h-12 w-12 mx-auto text-slate-300 mb-4" />
              <p className="text-slate-500">No accounts found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-slate-200 hover:bg-transparent">
                  <TableHead className="text-slate-500">Account</TableHead>
                  <TableHead className="text-slate-500">Type</TableHead>
                  <TableHead className="text-slate-500">Plan</TableHead>
                  <TableHead className="text-slate-500">Sponsor</TableHead>
                  <TableHead className="text-slate-500">Users</TableHead>
                  <TableHead className="text-slate-500">Reports/Mo</TableHead>
                  <TableHead className="text-slate-500">Status</TableHead>
                  <TableHead className="text-slate-500">Created</TableHead>
                  <TableHead className="text-slate-500 w-16"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {accounts.map((account) => (
                  <TableRow key={account.account_id} className="border-slate-100">
                    <TableCell>
                      <div>
                        <p className="text-slate-900 font-medium">{account.name}</p>
                        <p className="text-xs text-slate-400">{account.slug}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          account.account_type === "INDUSTRY_AFFILIATE"
                            ? "border-indigo-300 text-indigo-700 bg-indigo-50"
                            : "border-slate-300 text-slate-600"
                        }
                      >
                        {account.account_type === "INDUSTRY_AFFILIATE" ? "Affiliate" : "Regular"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          account.plan_slug === "free" ? "border-slate-300 text-slate-600" :
                          account.plan_slug === "pro" ? "border-blue-300 text-blue-700 bg-blue-50" :
                          account.plan_slug === "team" ? "border-emerald-300 text-emerald-700 bg-emerald-50" :
                          account.plan_slug === "affiliate" ? "border-indigo-300 text-indigo-700 bg-indigo-50" :
                          "border-amber-300 text-amber-700 bg-amber-50"
                        }
                      >
                        {account.plan_slug}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-500">
                      {account.sponsor_name || "-"}
                    </TableCell>
                    <TableCell className="text-slate-700">{account.user_count}</TableCell>
                    <TableCell className="text-slate-700">{account.reports_this_month}</TableCell>
                    <TableCell>
                      <Badge className={account.is_active ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}>
                        {account.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-400 text-sm">
                      {formatDate(account.created_at)}
                    </TableCell>
                    <TableCell>
                      <Link href={`/admin/accounts/${account.account_id}`}>
                        <Button variant="ghost" size="sm" className="text-slate-500 hover:text-slate-900 hover:bg-slate-100">
                          <Settings className="h-4 w-4" />
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

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
          <h1 className="text-3xl font-bold text-white">Accounts</h1>
          <p className="text-gray-400 mt-1">Manage all accounts and their settings</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Accounts</p>
                <p className="text-2xl font-bold text-white">{total}</p>
              </div>
              <Building className="h-8 w-8 text-violet-400/30" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Users</p>
                <p className="text-2xl font-bold text-white">{totalUsers}</p>
              </div>
              <Users className="h-8 w-8 text-blue-400/30" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Reports This Month</p>
                <p className="text-2xl font-bold text-white">{totalReports}</p>
              </div>
              <FileText className="h-8 w-8 text-green-400/30" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Avg Reports/Account</p>
                <p className="text-2xl font-bold text-white">
                  {accounts.length > 0 ? (totalReports / accounts.length).toFixed(1) : 0}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-orange-400/30" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <div className="relative flex-1 min-w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by name or slug..."
                className="pl-10 bg-gray-800 border-gray-700 text-white"
              />
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-40 bg-gray-800 border-gray-700 text-white">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="REGULAR">Regular</SelectItem>
                <SelectItem value="INDUSTRY_AFFILIATE">Affiliate</SelectItem>
              </SelectContent>
            </Select>
            <Select value={planFilter} onValueChange={setPlanFilter}>
              <SelectTrigger className="w-40 bg-gray-800 border-gray-700 text-white">
                <SelectValue placeholder="Plan" />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
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
              className="border-gray-700 text-gray-300 hover:bg-gray-800"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Accounts Table */}
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="pt-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : accounts.length === 0 ? (
            <div className="text-center py-12">
              <Building className="h-12 w-12 mx-auto text-gray-600 mb-4" />
              <p className="text-gray-400">No accounts found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-gray-800 hover:bg-transparent">
                  <TableHead className="text-gray-400">Account</TableHead>
                  <TableHead className="text-gray-400">Type</TableHead>
                  <TableHead className="text-gray-400">Plan</TableHead>
                  <TableHead className="text-gray-400">Sponsor</TableHead>
                  <TableHead className="text-gray-400">Users</TableHead>
                  <TableHead className="text-gray-400">Reports/Mo</TableHead>
                  <TableHead className="text-gray-400">Status</TableHead>
                  <TableHead className="text-gray-400">Created</TableHead>
                  <TableHead className="text-gray-400 w-16"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {accounts.map((account) => (
                  <TableRow key={account.account_id} className="border-gray-800">
                    <TableCell>
                      <div>
                        <p className="text-white font-medium">{account.name}</p>
                        <p className="text-xs text-gray-500">{account.slug}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          account.account_type === "INDUSTRY_AFFILIATE"
                            ? "border-violet-500/50 text-violet-400"
                            : "border-gray-700 text-gray-400"
                        }
                      >
                        {account.account_type === "INDUSTRY_AFFILIATE" ? "Affiliate" : "Regular"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          account.plan_slug === "free" ? "border-gray-600 text-gray-400" :
                          account.plan_slug === "pro" ? "border-blue-500/50 text-blue-400" :
                          account.plan_slug === "team" ? "border-green-500/50 text-green-400" :
                          account.plan_slug === "affiliate" ? "border-violet-500/50 text-violet-400" :
                          "border-yellow-500/50 text-yellow-400"
                        }
                      >
                        {account.plan_slug}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-gray-400">
                      {account.sponsor_name || "-"}
                    </TableCell>
                    <TableCell className="text-gray-300">{account.user_count}</TableCell>
                    <TableCell className="text-gray-300">{account.reports_this_month}</TableCell>
                    <TableCell>
                      <Badge className={account.is_active ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"}>
                        {account.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-gray-500 text-sm">
                      {formatDate(account.created_at)}
                    </TableCell>
                    <TableCell>
                      <Link href={`/admin/accounts/${account.account_id}`}>
                        <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white">
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

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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import {
  Building2,
  Search,
  Plus,
  Users,
  FileText,
  Loader2,
  RefreshCw,
  Settings,
} from "lucide-react"

interface Affiliate {
  account_id: string
  name: string
  slug: string
  plan_slug: string
  is_active: boolean
  created_at: string
  logo_url: string | null
  primary_color: string | null
  brand_display_name: string | null
  agent_count: number
  reports_this_month: number
}

export default function AffiliatesPage() {
  const [affiliates, setAffiliates] = useState<Affiliate[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newAffiliate, setNewAffiliate] = useState({
    company_name: "",
    admin_email: "",
    admin_first_name: "",
    admin_last_name: "",
    primary_color: "#7C3AED",
  })

  useEffect(() => {
    fetchAffiliates()
  }, [search])

  async function fetchAffiliates() {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (search) params.set("search", search)

      const res = await fetch(`/api/v1/admin/affiliates?${params.toString()}`, {
        credentials: "include",
      })
      if (res.ok) {
        const data = await res.json()
        setAffiliates(data.affiliates || [])
      }
    } catch (error) {
      console.error("Failed to fetch affiliates:", error)
    } finally {
      setLoading(false)
    }
  }

  async function createAffiliate() {
    setCreating(true)
    try {
      const res = await fetch("/api/v1/admin/affiliates", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(newAffiliate),
      })
      if (res.ok) {
        fetchAffiliates()
        setShowCreateDialog(false)
        setNewAffiliate({
          company_name: "",
          admin_email: "",
          admin_first_name: "",
          admin_last_name: "",
          primary_color: "#7C3AED",
        })
      }
    } catch (error) {
      console.error("Failed to create affiliate:", error)
    } finally {
      setCreating(false)
    }
  }

  const formatDate = (date: string) => new Date(date).toLocaleDateString()

  // Calculate totals
  const totalAgents = affiliates.reduce((sum, a) => sum + a.agent_count, 0)
  const totalReports = affiliates.reduce((sum, a) => sum + a.reports_this_month, 0)

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Title Companies</h1>
          <p className="text-slate-500 mt-1">Manage affiliate title companies and their agents</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-violet-600 hover:bg-violet-700 text-white">
              <Plus className="h-4 w-4 mr-2" />
              Add Title Company
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-white border-slate-200">
            <DialogHeader>
              <DialogTitle className="text-slate-900">Create Title Company</DialogTitle>
              <DialogDescription className="text-slate-500">
                Add a new affiliate title company to the platform
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <Label className="text-slate-700">Company Name</Label>
                <Input
                  value={newAffiliate.company_name}
                  onChange={(e) => setNewAffiliate({ ...newAffiliate, company_name: e.target.value })}
                  placeholder="e.g., Premier Title Services"
                  className="bg-white border-slate-300 text-slate-900"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-700">Admin First Name</Label>
                  <Input
                    value={newAffiliate.admin_first_name}
                    onChange={(e) => setNewAffiliate({ ...newAffiliate, admin_first_name: e.target.value })}
                    className="bg-white border-slate-300 text-slate-900"
                  />
                </div>
                <div>
                  <Label className="text-slate-700">Admin Last Name</Label>
                  <Input
                    value={newAffiliate.admin_last_name}
                    onChange={(e) => setNewAffiliate({ ...newAffiliate, admin_last_name: e.target.value })}
                    className="bg-white border-slate-300 text-slate-900"
                  />
                </div>
              </div>
              <div>
                <Label className="text-slate-700">Admin Email</Label>
                <Input
                  type="email"
                  value={newAffiliate.admin_email}
                  onChange={(e) => setNewAffiliate({ ...newAffiliate, admin_email: e.target.value })}
                  placeholder="admin@company.com"
                  className="bg-white border-slate-300 text-slate-900"
                />
              </div>
              <div>
                <Label className="text-slate-700">Brand Color</Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="color"
                    value={newAffiliate.primary_color}
                    onChange={(e) => setNewAffiliate({ ...newAffiliate, primary_color: e.target.value })}
                    className="w-16 h-10 p-1 bg-white border-slate-300"
                  />
                  <Input
                    value={newAffiliate.primary_color}
                    onChange={(e) => setNewAffiliate({ ...newAffiliate, primary_color: e.target.value })}
                    className="flex-1 bg-white border-slate-300 text-slate-900"
                  />
                </div>
              </div>
              <Button
                onClick={createAffiliate}
                disabled={creating || !newAffiliate.company_name || !newAffiliate.admin_email}
                className="w-full bg-violet-600 hover:bg-violet-700 text-white"
              >
                {creating ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <Plus className="h-4 w-4 mr-2" />
                )}
                Create Title Company
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Title Companies</p>
                <p className="text-2xl font-bold text-slate-900">{affiliates.length}</p>
              </div>
              <Building2 className="h-8 w-8 text-violet-200" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Agents</p>
                <p className="text-2xl font-bold text-slate-900">{totalAgents}</p>
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
                <p className="text-sm text-slate-500">Avg Agents/Company</p>
                <p className="text-2xl font-bold text-slate-900">
                  {affiliates.length > 0 ? (totalAgents / affiliates.length).toFixed(1) : 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by company name..."
                className="pl-10 bg-white border-slate-300 text-slate-900"
              />
            </div>
            <Button
              variant="outline"
              onClick={fetchAffiliates}
              className="border-slate-300 text-slate-600 hover:bg-slate-50"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Affiliates Table */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardContent className="pt-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
            </div>
          ) : affiliates.length === 0 ? (
            <div className="text-center py-12">
              <Building2 className="h-12 w-12 mx-auto text-slate-300 mb-4" />
              <p className="text-slate-500">No title companies found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-slate-200 hover:bg-transparent">
                  <TableHead className="text-slate-500">Company</TableHead>
                  <TableHead className="text-slate-500">Brand</TableHead>
                  <TableHead className="text-slate-500">Plan</TableHead>
                  <TableHead className="text-slate-500">Agents</TableHead>
                  <TableHead className="text-slate-500">Reports/Mo</TableHead>
                  <TableHead className="text-slate-500">Status</TableHead>
                  <TableHead className="text-slate-500">Created</TableHead>
                  <TableHead className="text-slate-500 w-16"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {affiliates.map((affiliate) => (
                  <TableRow key={affiliate.account_id} className="border-slate-100">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        {affiliate.logo_url ? (
                          <img
                            src={affiliate.logo_url}
                            alt={affiliate.name}
                            className="w-8 h-8 rounded object-cover"
                          />
                        ) : (
                          <div
                            className="w-8 h-8 rounded flex items-center justify-center text-white font-bold"
                            style={{ backgroundColor: affiliate.primary_color || "#7C3AED" }}
                          >
                            {affiliate.name[0]}
                          </div>
                        )}
                        <div>
                          <p className="text-slate-900 font-medium">{affiliate.name}</p>
                          <p className="text-xs text-slate-400">{affiliate.slug}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div
                          className="w-4 h-4 rounded-full border border-slate-200"
                          style={{ backgroundColor: affiliate.primary_color || "#7C3AED" }}
                        />
                        <span className="text-xs text-slate-400">{affiliate.primary_color}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="border-violet-300 text-violet-700 bg-violet-50">
                        {affiliate.plan_slug}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-700">{affiliate.agent_count}</TableCell>
                    <TableCell className="text-slate-700">{affiliate.reports_this_month}</TableCell>
                    <TableCell>
                      <Badge className={affiliate.is_active ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}>
                        {affiliate.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-400 text-sm">
                      {formatDate(affiliate.created_at)}
                    </TableCell>
                    <TableCell>
                      <Link href={`/admin/affiliates/${affiliate.account_id}`}>
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

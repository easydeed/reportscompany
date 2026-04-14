'use client'

import { useEffect, useState } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
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
import { Building, Users, UserCheck, FileText, Plus, ArrowLeft, Eye } from "lucide-react"

interface Company {
  account_id: string
  name: string
  slug: string
  is_active: boolean
  created_at: string
  logo_url: string | null
  primary_color: string | null
  brand_display_name: string | null
  plan_slug: string | null
  rep_count: number
  agent_count: number
  reports_30d: number
  has_admin: boolean
}

export default function AdminCompaniesPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [companies, setCompanies] = useState<Company[]>([])
  const [count, setCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') || 'all')

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      try {
        const params = new URLSearchParams()
        const s = searchParams.get('search')
        if (s) params.set('search', s)
        const st = searchParams.get('status')
        if (st && st !== 'all') params.set('status', st)

        const res = await fetch(`/api/proxy/v1/admin/companies?${params.toString()}`, {
          credentials: 'include',
        })
        if (res.ok) {
          const data = await res.json()
          setCompanies(data?.companies || [])
          setCount(data?.count || 0)
        }
      } catch (err) {
        console.error('Failed to fetch companies:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [searchParams])

  function applyFilters(newSearch?: string, newStatus?: string) {
    const params = new URLSearchParams()
    const s = newSearch !== undefined ? newSearch : search
    const st = newStatus !== undefined ? newStatus : statusFilter
    if (s) params.set('search', s)
    if (st && st !== 'all') params.set('status', st)
    router.push(`/app/admin/companies?${params.toString()}`)
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    applyFilters()
  }

  const totalReps = companies.reduce((sum, c) => sum + c.rep_count, 0)
  const totalAgents = companies.reduce((sum, c) => sum + c.agent_count, 0)
  const totalReports = companies.reduce((sum, c) => sum + c.reports_30d, 0)

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Skeleton className="h-10 w-10 rounded" />
            <div>
              <Skeleton className="h-9 w-48 mb-2" />
              <Skeleton className="h-5 w-72" />
            </div>
          </div>
          <Skeleton className="h-10 w-40" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <Card key={i}><CardContent className="pt-6"><Skeleton className="h-8 w-16" /></CardContent></Card>
          ))}
        </div>
        <Card><CardContent className="pt-6">
          {[1, 2, 3].map(i => (
            <div key={i} className="py-3 flex gap-4">
              <Skeleton className="h-8 w-8 rounded" />
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-5 w-16 rounded-full" />
            </div>
          ))}
        </CardContent></Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/app/admin">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-display font-bold text-foreground">Title Companies</h1>
            <p className="text-muted-foreground mt-1">Manage title companies and their rep hierarchies</p>
          </div>
        </div>
        <Link href="/app/admin/companies/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Company
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Companies</CardTitle>
            <Building className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{count}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Reps</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalReps}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
            <UserCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalAgents}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reports (30d)</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalReports}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSearch} className="flex gap-4 items-end">
            <Input
              placeholder="Search by company name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="max-w-sm"
            />
            <Select
              value={statusFilter}
              onValueChange={(v) => { setStatusFilter(v); applyFilters(undefined, v) }}
            >
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
                <SelectItem value="no_admin">No Admin</SelectItem>
              </SelectContent>
            </Select>
            <Button type="submit" variant="secondary">Search</Button>
            {(searchParams.get('search') || searchParams.get('status')) && (
              <Link href="/app/admin/companies">
                <Button variant="ghost" type="button" onClick={() => { setSearch(''); setStatusFilter('all') }}>
                  Clear
                </Button>
              </Link>
            )}
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          {companies.length === 0 ? (
            <div className="text-center py-12">
              <Building className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No companies found</h3>
              <p className="text-muted-foreground mb-4">
                {searchParams.get('search') || searchParams.get('status')
                  ? "No companies match your filters"
                  : "Get started by adding your first title company"}
              </p>
              <Link href="/app/admin/companies/new">
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Company
                </Button>
              </Link>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Company</TableHead>
                  <TableHead className="text-center">Reps</TableHead>
                  <TableHead className="text-center">Agents</TableHead>
                  <TableHead className="text-center">Reports (30d)</TableHead>
                  <TableHead>Plan</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {companies.map((company) => (
                  <TableRow key={company.account_id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        {company.logo_url ? (
                          <img
                            src={company.logo_url}
                            alt={company.name}
                            className="h-8 w-8 rounded object-contain bg-muted"
                          />
                        ) : (
                          <div
                            className="h-8 w-8 rounded flex items-center justify-center text-white text-xs font-bold"
                            style={{ backgroundColor: company.primary_color || '#4F46E5' }}
                          >
                            {company.name.charAt(0)}
                          </div>
                        )}
                        <div>
                          <div className="font-medium">{company.name}</div>
                          <div className="text-sm text-muted-foreground">{company.slug}</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-center">{company.rep_count}</TableCell>
                    <TableCell className="text-center">{company.agent_count}</TableCell>
                    <TableCell className="text-center">{company.reports_30d}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="capitalize">
                        {company.plan_slug || 'affiliate'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <Badge variant={company.is_active ? "default" : "secondary"}>
                          {company.is_active ? "Active" : "Inactive"}
                        </Badge>
                        {!company.has_admin && (
                          <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50">
                            No Admin
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Link href={`/app/admin/companies/${company.account_id}`}>
                        <Button variant="ghost" size="sm">
                          <Eye className="h-3.5 w-3.5 mr-1" />
                          View
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

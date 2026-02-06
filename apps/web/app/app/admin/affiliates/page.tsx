import { apiFetch } from "@/lib/api"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Building2, Users, FileText, Plus, ArrowLeft, ExternalLink } from "lucide-react"

export const dynamic = 'force-dynamic'

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

async function getAffiliates(search?: string): Promise<{ affiliates: Affiliate[], count: number }> {
  try {
    const url = search
      ? `/v1/admin/affiliates?search=${encodeURIComponent(search)}`
      : '/v1/admin/affiliates'
    const data = await apiFetch(url)
    return data || { affiliates: [], count: 0 }
  } catch (error) {
    console.error("Failed to fetch affiliates:", error)
    return { affiliates: [], count: 0 }
  }
}

export default async function AdminAffiliatesPage({
  searchParams,
}: {
  searchParams: Promise<{ search?: string }>
}) {
  const params = await searchParams
  const { affiliates, count } = await getAffiliates(params.search)

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
            <p className="text-muted-foreground mt-1">Manage affiliate accounts and their agents</p>
          </div>
        </div>
        <Link href="/app/admin/affiliates/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Title Company
          </Button>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Affiliates</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{count}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {affiliates.reduce((sum, a) => sum + a.agent_count, 0)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reports This Month</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {affiliates.reduce((sum, a) => sum + a.reports_this_month, 0)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <form method="GET" className="flex gap-4">
            <Input
              name="search"
              placeholder="Search by company name..."
              defaultValue={params.search}
              className="max-w-sm"
            />
            <Button type="submit" variant="secondary">Search</Button>
            {params.search && (
              <Link href="/app/admin/affiliates">
                <Button variant="ghost">Clear</Button>
              </Link>
            )}
          </form>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="pt-6">
          {affiliates.length === 0 ? (
            <div className="text-center py-12">
              <Building2 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No affiliates found</h3>
              <p className="text-muted-foreground mb-4">
                {params.search
                  ? "No affiliates match your search criteria"
                  : "Get started by adding your first title company"}
              </p>
              <Link href="/app/admin/affiliates/new">
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Title Company
                </Button>
              </Link>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Company</TableHead>
                  <TableHead>Plan</TableHead>
                  <TableHead>Agents</TableHead>
                  <TableHead>Reports/Month</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {affiliates.map((affiliate) => (
                  <TableRow key={affiliate.account_id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        {affiliate.logo_url ? (
                          <img
                            src={affiliate.logo_url}
                            alt={affiliate.name}
                            className="h-8 w-8 rounded object-contain bg-muted"
                          />
                        ) : (
                          <div
                            className="h-8 w-8 rounded flex items-center justify-center text-white text-xs font-bold"
                            style={{ backgroundColor: affiliate.primary_color || '#4F46E5' }}
                          >
                            {affiliate.name.charAt(0)}
                          </div>
                        )}
                        <div>
                          <div className="font-medium">{affiliate.name}</div>
                          <div className="text-sm text-muted-foreground">{affiliate.slug}</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{affiliate.plan_slug}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        {affiliate.agent_count}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        {affiliate.reports_this_month}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={affiliate.is_active ? "default" : "secondary"}>
                        {affiliate.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {affiliate.created_at
                        ? new Date(affiliate.created_at).toLocaleDateString()
                        : '-'}
                    </TableCell>
                    <TableCell>
                      <Link href={`/app/admin/affiliates/${affiliate.account_id}`}>
                        <Button variant="ghost" size="sm">
                          View
                          <ExternalLink className="h-3 w-3 ml-1" />
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

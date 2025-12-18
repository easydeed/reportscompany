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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Building, Users, FileText, ArrowLeft, Settings } from "lucide-react"

export const dynamic = 'force-dynamic'

interface Account {
  account_id: string
  name: string
  slug: string
  account_type: string
  plan_slug: string
  is_active: boolean
  sponsor_account_id: string | null
  sponsor_name: string | null
  created_at: string
  user_count: number
  reports_this_month: number
}

interface AccountsResponse {
  accounts: Account[]
  count: number
  total: number
}

async function getAccounts(params: {
  search?: string
  account_type?: string
  plan_slug?: string
}): Promise<AccountsResponse> {
  try {
    const searchParams = new URLSearchParams()
    if (params.search) searchParams.set("search", params.search)
    if (params.account_type && params.account_type !== "all") searchParams.set("account_type", params.account_type)
    if (params.plan_slug && params.plan_slug !== "all") searchParams.set("plan_slug", params.plan_slug)

    const url = `/v1/admin/accounts?${searchParams.toString()}`
    const data = await apiFetch(url)
    return data || { accounts: [], count: 0, total: 0 }
  } catch (error) {
    console.error("Failed to fetch accounts:", error)
    return { accounts: [], count: 0, total: 0 }
  }
}

export default async function AdminAccountsPage({
  searchParams,
}: {
  searchParams: Promise<{ search?: string; account_type?: string; plan_slug?: string }>
}) {
  const params = await searchParams
  const { accounts, count, total } = await getAccounts(params)

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/app/admin">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-display font-bold text-foreground">All Accounts</h1>
          <p className="text-muted-foreground mt-1">View and manage all accounts in the system</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Accounts</CardTitle>
            <Building className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Showing</CardTitle>
            <Building className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{count}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {accounts.reduce((sum, a) => sum + a.user_count, 0)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reports/Month</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {accounts.reduce((sum, a) => sum + a.reports_this_month, 0)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <form method="GET" className="flex flex-wrap gap-4">
            <Input
              name="search"
              placeholder="Search by name..."
              defaultValue={params.search}
              className="w-64"
            />
            <Select name="account_type" defaultValue={params.account_type || "all"}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="All Types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="REGULAR">Regular</SelectItem>
                <SelectItem value="INDUSTRY_AFFILIATE">Affiliate</SelectItem>
              </SelectContent>
            </Select>
            <Select name="plan_slug" defaultValue={params.plan_slug || "all"}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="All Plans" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Plans</SelectItem>
                <SelectItem value="free">Free</SelectItem>
                <SelectItem value="pro">Pro</SelectItem>
                <SelectItem value="team">Team</SelectItem>
                <SelectItem value="affiliate">Affiliate</SelectItem>
                <SelectItem value="sponsored_free">Sponsored Free</SelectItem>
              </SelectContent>
            </Select>
            <Button type="submit" variant="secondary">Filter</Button>
            {(params.search || params.account_type || params.plan_slug) && (
              <Link href="/app/admin/accounts">
                <Button variant="ghost">Clear</Button>
              </Link>
            )}
          </form>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="pt-6">
          {accounts.length === 0 ? (
            <div className="text-center py-12">
              <Building className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No accounts found</h3>
              <p className="text-muted-foreground">
                {params.search || params.account_type || params.plan_slug
                  ? "No accounts match your filters"
                  : "No accounts in the system yet"}
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Account</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Plan</TableHead>
                  <TableHead>Sponsor</TableHead>
                  <TableHead>Users</TableHead>
                  <TableHead>Reports/Month</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="w-16"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {accounts.map((account) => (
                  <TableRow key={account.account_id}>
                    <TableCell>
                      <Link href={`/app/admin/accounts/${account.account_id}`} className="hover:underline">
                        <div className="font-medium text-primary">{account.name}</div>
                        <div className="text-sm text-muted-foreground">{account.slug}</div>
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge variant={account.account_type === "INDUSTRY_AFFILIATE" ? "default" : "secondary"}>
                        {account.account_type === "INDUSTRY_AFFILIATE" ? "Affiliate" : "Regular"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{account.plan_slug}</Badge>
                    </TableCell>
                    <TableCell>
                      {account.sponsor_name ? (
                        <span className="text-sm">{account.sponsor_name}</span>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>{account.user_count}</TableCell>
                    <TableCell>{account.reports_this_month}</TableCell>
                    <TableCell>
                      <Badge variant={account.is_active ? "default" : "secondary"}>
                        {account.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {account.created_at
                        ? new Date(account.created_at).toLocaleDateString()
                        : '-'}
                    </TableCell>
                    <TableCell>
                      <Link href={`/app/admin/accounts/${account.account_id}`}>
                        <Button variant="ghost" size="icon">
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

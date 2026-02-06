import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
  Users,
  TrendingUp,
  UserPlus,
  Mail,
  Phone,
  ExternalLink,
} from "lucide-react"
import { LeadsFilters } from "./filters"
import { LeadsActions } from "./actions"

export const dynamic = 'force-dynamic'

interface Lead {
  id: string
  account_id: string
  account_name: string
  property_report_id: string | null
  property_address: string | null
  name: string
  email: string
  phone: string | null
  message: string | null
  source: string
  status: string
  consent_given: boolean
  sms_sent_at: string | null
  email_sent_at: string | null
  created_at: string
}

interface Stats {
  total: number
  new_this_week: number
  contacted: number
  converted: number
  conversion_rate: number
}

async function fetchWithAuth(path: string, token: string) {
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://reportscompany.onrender.com'

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: { 'Cookie': `mr_token=${token}` },
      cache: 'no-store',
    })
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

function formatTimeAgo(dateString: string | null): string {
  if (!dateString) return "Never"
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return "Just now"
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  return `${diffDays}d ago`
}

export default async function AdminLeadsPage({
  searchParams,
}: {
  searchParams: { status?: string; account?: string; from?: string; to?: string }
}) {
  const cookieStore = await cookies()
  const token = cookieStore.get('mr_token')?.value

  if (!token) {
    redirect('/login')
  }

  // Build query params
  const params = new URLSearchParams()
  if (searchParams.status && searchParams.status !== 'all') params.set('status', searchParams.status)
  if (searchParams.account) params.set('account', searchParams.account)
  if (searchParams.from) params.set('from_date', searchParams.from)
  if (searchParams.to) params.set('to_date', searchParams.to)
  params.set('limit', '100')

  const [leadsRes, statsRes] = await Promise.all([
    fetchWithAuth(`/v1/admin/leads?${params.toString()}`, token),
    fetchWithAuth('/v1/admin/stats/leads', token),
  ])

  const leads: Lead[] = leadsRes?.leads || []
  const stats: Stats = statsRes || { total: 0, new_this_week: 0, contacted: 0, converted: 0, conversion_rate: 0 }

  const statusColors: Record<string, string> = {
    new: "bg-blue-100 text-blue-800",
    contacted: "bg-yellow-100 text-yellow-800",
    converted: "bg-green-100 text-green-800",
  }

  const sourceColors: Record<string, string> = {
    qr_scan: "border-indigo-300 text-indigo-700",
    direct_link: "border-blue-300 text-blue-700",
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-display font-bold">Leads</h1>
        <p className="text-muted-foreground mt-2">Manage leads captured from property reports</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Leads</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">New This Week</CardTitle>
            <UserPlus className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.new_this_week}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Converted</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.converted}</div>
          </CardContent>
        </Card>

        <Card className={(stats.conversion_rate ?? 0) > 0 ? "bg-green-50 border-green-200" : ""}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {(stats.conversion_rate ?? 0).toFixed(1)}%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <LeadsFilters />

      {/* Leads Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Leads ({leads.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {leads.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No leads found</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Lead</TableHead>
                  <TableHead>Account</TableHead>
                  <TableHead>Property</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {leads.map((lead) => (
                  <TableRow key={lead.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium text-sm">{lead.name}</p>
                        <a href={`mailto:${lead.email}`} className="flex items-center gap-1 text-xs text-muted-foreground hover:underline">
                          <Mail className="w-3 h-3" />
                          {lead.email}
                        </a>
                        {lead.phone && (
                          <a href={`tel:${lead.phone}`} className="flex items-center gap-1 text-xs text-muted-foreground hover:underline">
                            <Phone className="w-3 h-3" />
                            {lead.phone}
                          </a>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Link 
                        href={`/app/admin/accounts/${lead.account_id}`}
                        className="text-sm hover:underline"
                      >
                        {lead.account_name}
                      </Link>
                    </TableCell>
                    <TableCell>
                      {lead.property_address ? (
                        <Link 
                          href={`/app/admin/property-reports/${lead.property_report_id}`}
                          className="text-sm hover:underline flex items-center gap-1"
                        >
                          {lead.property_address.slice(0, 25)}...
                          <ExternalLink className="w-3 h-3" />
                        </Link>
                      ) : (
                        <span className="text-sm text-muted-foreground">N/A</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={sourceColors[lead.source] || ""}>
                        {lead.source.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={statusColors[lead.status] || "bg-gray-100"}>
                        {lead.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {formatTimeAgo(lead.created_at)}
                    </TableCell>
                    <TableCell>
                      <LeadsActions leadId={lead.id} />
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


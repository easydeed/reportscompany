import { redirect } from "next/navigation"
import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
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
  Home,
  Users,
  Eye,
  UserPlus,
  TrendingUp,
  Building2,
  BarChart3,
  Target,
  CheckCircle,
  AlertTriangle,
  Palette,
} from "lucide-react"
import { createServerApi } from "@/lib/api-server"

export const dynamic = 'force-dynamic'

// Theme names mapping
const THEME_NAMES: Record<number, string> = {
  1: 'Classic',
  2: 'Modern',
  3: 'Elegant',
  4: 'Teal',
  5: 'Bold',
}

// Theme colors for badges
const THEME_COLORS: Record<number, string> = {
  1: 'bg-slate-100 text-slate-700 border-slate-300',
  2: 'bg-blue-100 text-blue-700 border-blue-300',
  3: 'bg-purple-100 text-purple-700 border-purple-300',
  4: 'bg-teal-100 text-teal-700 border-teal-300',
  5: 'bg-amber-100 text-amber-700 border-amber-300',
}

export default async function PropertyReportsAdminPage() {
  const api = await createServerApi()

  if (!api.isAuthenticated()) {
    redirect('/login?next=/admin/property-reports')
  }

  // Fetch all property report data in parallel
  const [statsRes, reportsRes, topAffiliatesRes, topAgentsRes] = await Promise.all([
    api.get<any>("/v1/admin/property-reports/stats"),
    api.get<any>("/v1/admin/property-reports?limit=10"),
    api.get<any>("/v1/admin/property-reports/top-affiliates?limit=5"),
    api.get<any>("/v1/admin/property-reports/top-agents?limit=5"),
  ])

  const stats = statsRes.data || {}
  const reports = reportsRes.data?.reports || []
  const topAffiliates = topAffiliatesRes.data?.affiliates || []
  const topAgents = topAgentsRes.data?.agents || []

  const summary = stats.summary || {}
  const engagement = stats.engagement || {}
  const leads = stats.leads || {}
  const themes = stats.themes || {}
  const byType = stats.by_account_type || {}
  const allTime = stats.all_time || {}

  // Find most popular theme
  const popularTheme = Object.entries(themes)
    .sort(([,a], [,b]) => (b as number) - (a as number))[0]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Property Reports</h1>
        <p className="text-slate-500 mt-1">
          Platform-wide property report analytics • Last 30 days
        </p>
      </div>

      {/* Primary KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Total Reports</CardTitle>
            <Home className="h-4 w-4 text-teal-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">{summary.total_reports || 0}</div>
            <p className="text-xs text-slate-500 mt-1">
              <span className="text-emerald-600 font-medium">{summary.completed || 0}</span> completed
              {summary.failed > 0 && (
                <span className="text-red-500 ml-2">• {summary.failed} failed</span>
              )}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Total Views</CardTitle>
            <Eye className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">{engagement.total_views || 0}</div>
            <p className="text-xs text-slate-500 mt-1">
              <span className="text-violet-600 font-medium">{engagement.unique_visitors || 0}</span> unique visitors
            </p>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Leads Captured</CardTitle>
            <UserPlus className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">{leads.total || 0}</div>
            <p className="text-xs text-slate-500 mt-1">
              <span className="text-emerald-600 font-medium">{leads.conversion_rate || 0}%</span> conversion rate
            </p>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Active Accounts</CardTitle>
            <Users className="h-4 w-4 text-violet-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">{summary.accounts_with_reports || 0}</div>
            <p className="text-xs text-slate-500 mt-1">
              <span className="text-violet-600 font-medium">{summary.active_landing_pages || 0}</span> active landing pages
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Secondary KPIs - Account Types & Themes */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <Card className="bg-emerald-50 border-emerald-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-emerald-600">Regular Agents</p>
                <p className="text-xl font-bold text-emerald-700">{byType.regular || 0}</p>
              </div>
              <Users className="h-5 w-5 text-emerald-300" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-blue-600">Sponsored Agents</p>
                <p className="text-xl font-bold text-blue-700">{byType.sponsored || 0}</p>
              </div>
              <Building2 className="h-5 w-5 text-blue-300" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-violet-50 border-violet-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-violet-600">Affiliates</p>
                <p className="text-xl font-bold text-violet-700">{byType.affiliate || 0}</p>
              </div>
              <Building2 className="h-5 w-5 text-violet-300" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-teal-50 border-teal-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-teal-600">From QR Scans</p>
                <p className="text-xl font-bold text-teal-700">{leads.from_qr || 0}</p>
              </div>
              <Target className="h-5 w-5 text-teal-300" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-amber-50 border-amber-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-amber-600">Direct Links</p>
                <p className="text-xl font-bold text-amber-700">{leads.from_direct || 0}</p>
              </div>
              <TrendingUp className="h-5 w-5 text-amber-300" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-purple-50 border-purple-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-purple-600">Converted</p>
                <p className="text-xl font-bold text-purple-700">{leads.converted || 0}</p>
              </div>
              <CheckCircle className="h-5 w-5 text-purple-300" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Theme Distribution */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-slate-900 flex items-center gap-2">
            <Palette className="h-5 w-5" />
            Theme Popularity
          </CardTitle>
          <CardDescription>Distribution of reports across themes</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            {Object.entries(THEME_NAMES).map(([id, name]) => {
              const count = themes[name.toLowerCase()] || 0
              const total = summary.total_reports || 1
              const percentage = Math.round((count / total) * 100)
              return (
                <div key={id} className="flex-1 min-w-[120px]">
                  <div className="flex items-center justify-between mb-2">
                    <Badge className={THEME_COLORS[parseInt(id)]}>{name}</Badge>
                    <span className="text-sm font-medium text-slate-600">{count}</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-teal-400 to-teal-600 rounded-full transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{percentage}%</p>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Tables Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Affiliates */}
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-slate-900">Top Affiliates</CardTitle>
              <Link href="/admin/affiliates" className="text-sm text-violet-600 hover:text-violet-700 font-medium">
                View all →
              </Link>
            </div>
            <CardDescription>By property report volume (30d)</CardDescription>
          </CardHeader>
          <CardContent>
            {topAffiliates.length === 0 ? (
              <p className="text-slate-400 text-center py-8">No affiliate activity yet</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-200 hover:bg-transparent">
                    <TableHead className="text-slate-500">Affiliate</TableHead>
                    <TableHead className="text-slate-500 text-right">Agents</TableHead>
                    <TableHead className="text-slate-500 text-right">Reports</TableHead>
                    <TableHead className="text-slate-500 text-right">Leads</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {topAffiliates.map((aff: any, idx: number) => (
                    <TableRow key={aff.id} className="border-slate-100">
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-400">#{idx + 1}</span>
                          <span className="text-slate-700 font-medium">{aff.name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right text-slate-600">{aff.agents}</TableCell>
                      <TableCell className="text-right">
                        <span className="font-semibold text-teal-600">{aff.reports}</span>
                      </TableCell>
                      <TableCell className="text-right">
                        <span className="font-semibold text-emerald-600">{aff.leads}</span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Top Agents */}
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-slate-900">Top Agents</CardTitle>
              <Link href="/admin/users" className="text-sm text-violet-600 hover:text-violet-700 font-medium">
                View all →
              </Link>
            </div>
            <CardDescription>By property report volume (30d)</CardDescription>
          </CardHeader>
          <CardContent>
            {topAgents.length === 0 ? (
              <p className="text-slate-400 text-center py-8">No agent activity yet</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-200 hover:bg-transparent">
                    <TableHead className="text-slate-500">Agent</TableHead>
                    <TableHead className="text-slate-500">Type</TableHead>
                    <TableHead className="text-slate-500 text-right">Reports</TableHead>
                    <TableHead className="text-slate-500 text-right">Conv.</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {topAgents.map((agent: any, idx: number) => (
                    <TableRow key={agent.id} className="border-slate-100">
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-400">#{idx + 1}</span>
                          <div>
                            <p className="text-slate-700 font-medium">{agent.name}</p>
                            <p className="text-xs text-slate-400">{agent.email}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={
                          agent.type === 'sponsored' 
                            ? 'border-blue-300 text-blue-600' 
                            : 'border-slate-300 text-slate-600'
                        }>
                          {agent.type}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <span className="font-semibold text-teal-600">{agent.reports}</span>
                      </TableCell>
                      <TableCell className="text-right">
                        <span className="font-semibold text-emerald-600">{agent.conversion_rate}%</span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Property Reports */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-slate-900">Recent Property Reports</CardTitle>
          <CardDescription>Latest property reports across the platform</CardDescription>
        </CardHeader>
        <CardContent>
          {reports.length === 0 ? (
            <p className="text-slate-400 text-center py-8">No property reports yet</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-slate-200 hover:bg-transparent">
                  <TableHead className="text-slate-500">Property</TableHead>
                  <TableHead className="text-slate-500">Account</TableHead>
                  <TableHead className="text-slate-500">Theme</TableHead>
                  <TableHead className="text-slate-500">Status</TableHead>
                  <TableHead className="text-slate-500 text-right">Views</TableHead>
                  <TableHead className="text-slate-500 text-right">Leads</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reports.map((report: any) => (
                  <TableRow key={report.id} className="border-slate-100">
                    <TableCell>
                      <div>
                        <p className="text-slate-700 font-medium">{report.address}</p>
                        <p className="text-xs text-slate-400">{report.city}, {report.state}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="text-slate-600">{report.account_name}</p>
                        <Badge variant="outline" className={
                          report.account_type === 'sponsored' 
                            ? 'border-blue-200 text-blue-600 text-xs' 
                            : report.account_type === 'affiliate'
                            ? 'border-violet-200 text-violet-600 text-xs'
                            : 'border-slate-200 text-slate-500 text-xs'
                        }>
                          {report.account_type}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={THEME_COLORS[report.theme] || THEME_COLORS[1]}>
                        {THEME_NAMES[report.theme] || 'Classic'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={
                        report.status === 'complete' ? 'bg-emerald-100 text-emerald-700 border-emerald-200' :
                        report.status === 'failed' ? 'bg-red-100 text-red-700 border-red-200' :
                        report.status === 'processing' ? 'bg-blue-100 text-blue-700 border-blue-200' :
                        'bg-amber-100 text-amber-700 border-amber-200'
                      }>
                        {report.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right text-slate-600">{report.views}</TableCell>
                    <TableCell className="text-right">
                      <span className={report.leads > 0 ? 'font-semibold text-emerald-600' : 'text-slate-400'}>
                        {report.leads}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* All-Time Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-teal-500 to-cyan-600 border-0 shadow-lg">
          <CardContent className="pt-6">
            <p className="text-sm text-teal-100">All-Time Reports</p>
            <p className="text-2xl font-bold text-white mt-1">{allTime.total_reports || 0}</p>
            <p className="text-xs text-teal-200 mt-1">total generated</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-500 to-indigo-600 border-0 shadow-lg">
          <CardContent className="pt-6">
            <p className="text-sm text-blue-100">All-Time Views</p>
            <p className="text-2xl font-bold text-white mt-1">{allTime.total_views || 0}</p>
            <p className="text-xs text-blue-200 mt-1">landing page views</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-emerald-500 to-green-600 border-0 shadow-lg">
          <CardContent className="pt-6">
            <p className="text-sm text-emerald-100">All-Time Leads</p>
            <p className="text-2xl font-bold text-white mt-1">{allTime.total_leads || 0}</p>
            <p className="text-xs text-emerald-200 mt-1">leads captured</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-violet-500 to-purple-600 border-0 shadow-lg">
          <CardContent className="pt-6">
            <p className="text-sm text-violet-100">Active Accounts</p>
            <p className="text-2xl font-bold text-white mt-1">{allTime.accounts_with_reports || 0}</p>
            <p className="text-xs text-violet-200 mt-1">using property reports</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}


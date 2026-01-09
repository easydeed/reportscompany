import { cookies } from "next/headers"
import { redirect, notFound } from "next/navigation"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  ArrowLeft,
  FileText,
  Home,
  Users,
  Eye,
  Download,
  QrCode,
  ExternalLink,
  Mail,
  Phone,
  Shield,
  Clock,
  Lock,
  Unlock,
  CheckCircle,
  XCircle,
} from "lucide-react"
import { PropertyReportActions } from "../actions"
import { RawDataViewer } from "./raw-data-viewer"

export const dynamic = 'force-dynamic'

interface Lead {
  id: string
  name: string
  email: string
  phone: string | null
  status: string
  source: string
  created_at: string
}

interface PropertyReport {
  id: string
  account_id: string
  account_name: string
  user_id: string
  user_email: string
  user_name: string
  report_type: string
  status: string
  theme: number
  accent_color: string
  language: string
  property_address: string
  property_city: string
  property_state: string
  property_zip: string
  property_county: string
  apn: string
  owner_name: string
  legal_description: string
  property_type: string
  sitex_data: Record<string, any> | null
  comparables: any[] | null
  short_code: string
  qr_code_url: string | null
  pdf_url: string | null
  view_count: number
  unique_visitors: number
  last_viewed_at: string | null
  is_active: boolean
  expires_at: string | null
  max_leads: number | null
  access_code: string | null
  created_at: string
  updated_at: string
  leads: Lead[]
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

export default async function AdminPropertyReportDetailPage({
  params,
}: {
  params: { id: string }
}) {
  const cookieStore = await cookies()
  const token = cookieStore.get('mr_token')?.value

  if (!token) {
    redirect('/login')
  }

  const report: PropertyReport | null = await fetchWithAuth(
    `/v1/admin/property-reports/${params.id}`,
    token
  )

  if (!report) {
    notFound()
  }

  const statusColors: Record<string, string> = {
    complete: "bg-green-100 text-green-800",
    processing: "bg-blue-100 text-blue-800",
    draft: "bg-yellow-100 text-yellow-800",
    failed: "bg-red-100 text-red-800",
  }

  const leadStatusColors: Record<string, string> = {
    new: "bg-blue-100 text-blue-800",
    contacted: "bg-yellow-100 text-yellow-800",
    converted: "bg-green-100 text-green-800",
  }

  const publicUrl = report.short_code ? `/p/${report.short_code}` : null

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Link href="/app/admin/property-reports">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="w-4 h-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-bold">{report.property_address}</h1>
              <Badge className={statusColors[report.status] || "bg-gray-100"}>
                {report.status}
              </Badge>
            </div>
            <p className="text-muted-foreground">
              {report.property_city}, {report.property_state} {report.property_zip}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          {report.pdf_url && (
            <Button variant="outline" asChild>
              <a href={report.pdf_url} target="_blank" rel="noopener noreferrer">
                <Download className="w-4 h-4 mr-2" />
                Download PDF
              </a>
            </Button>
          )}
          {publicUrl && (
            <Button variant="outline" asChild>
              <a href={publicUrl} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="w-4 h-4 mr-2" />
                Public Page
              </a>
            </Button>
          )}
          <PropertyReportActions reportId={report.id} status={report.status} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Account Info */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                Account Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Account</p>
                  <Link 
                    href={`/app/admin/accounts/${report.account_id}`}
                    className="font-medium hover:underline"
                  >
                    {report.account_name}
                  </Link>
                </div>
                <div>
                  <p className="text-muted-foreground">User</p>
                  <p className="font-medium">{report.user_name || report.user_email}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Report Type</p>
                  <p className="font-medium capitalize">{report.report_type}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Language</p>
                  <p className="font-medium">{report.language === 'en' ? 'English' : 'Spanish'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Created</p>
                  <p className="font-medium">{new Date(report.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Updated</p>
                  <p className="font-medium">{new Date(report.updated_at).toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Property Info */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Home className="w-5 h-5" />
                Property Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Address</p>
                  <p className="font-medium">{report.property_address}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">City, State ZIP</p>
                  <p className="font-medium">
                    {report.property_city}, {report.property_state} {report.property_zip}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">County</p>
                  <p className="font-medium">{report.property_county || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">APN</p>
                  <p className="font-medium font-mono">{report.apn || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Owner</p>
                  <p className="font-medium">{report.owner_name || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Property Type</p>
                  <p className="font-medium">{report.property_type || 'N/A'}</p>
                </div>
                {report.sitex_data && (
                  <>
                    <div>
                      <p className="text-muted-foreground">Beds / Baths</p>
                      <p className="font-medium">
                        {report.sitex_data.bedrooms || 'N/A'} / {report.sitex_data.bathrooms || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Sq Ft</p>
                      <p className="font-medium">
                        {report.sitex_data.sqft?.toLocaleString() || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Year Built</p>
                      <p className="font-medium">{report.sitex_data.year_built || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Assessed Value</p>
                      <p className="font-medium">
                        {report.sitex_data.assessed_value 
                          ? `$${report.sitex_data.assessed_value.toLocaleString()}` 
                          : 'N/A'}
                      </p>
                    </div>
                  </>
                )}
              </div>
              {report.legal_description && (
                <div className="mt-4 pt-4 border-t">
                  <p className="text-muted-foreground text-sm mb-1">Legal Description</p>
                  <p className="text-sm">{report.legal_description}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Leads */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                Associated Leads ({report.leads?.length || 0})
              </CardTitle>
              <CardDescription>Leads captured from this property report</CardDescription>
            </CardHeader>
            <CardContent>
              {(!report.leads || report.leads.length === 0) ? (
                <p className="text-muted-foreground text-center py-4">No leads captured yet</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Contact</TableHead>
                      <TableHead>Source</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {report.leads.map((lead) => (
                      <TableRow key={lead.id}>
                        <TableCell className="font-medium">{lead.name}</TableCell>
                        <TableCell>
                          <div className="flex flex-col gap-1">
                            <a href={`mailto:${lead.email}`} className="flex items-center gap-1 text-sm hover:underline">
                              <Mail className="w-3 h-3" />
                              {lead.email}
                            </a>
                            {lead.phone && (
                              <a href={`tel:${lead.phone}`} className="flex items-center gap-1 text-sm text-muted-foreground hover:underline">
                                <Phone className="w-3 h-3" />
                                {lead.phone}
                              </a>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="capitalize">
                            {lead.source.replace('_', ' ')}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={leadStatusColors[lead.status] || "bg-gray-100"}>
                            {lead.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {new Date(lead.created_at).toLocaleDateString()}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          {/* Raw SiteX Data */}
          {report.sitex_data && (
            <RawDataViewer 
              title="SiteX Raw Data" 
              data={report.sitex_data} 
            />
          )}

          {/* Comparables */}
          {report.comparables && report.comparables.length > 0 && (
            <RawDataViewer 
              title={`Comparables (${report.comparables.length})`}
              data={report.comparables} 
            />
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* QR Code */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <QrCode className="w-5 h-5" />
                QR Code
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {report.qr_code_url ? (
                <div className="flex justify-center">
                  <img
                    src={report.qr_code_url}
                    alt="QR Code"
                    className="w-40 h-40 rounded-lg border"
                  />
                </div>
              ) : (
                <div className="w-40 h-40 mx-auto rounded-lg border-2 border-dashed flex items-center justify-center">
                  <p className="text-sm text-muted-foreground">No QR code</p>
                </div>
              )}
              
              {report.short_code && (
                <div className="text-center">
                  <p className="text-xs text-muted-foreground mb-1">Short Code</p>
                  <code className="bg-muted px-2 py-1 rounded text-sm">{report.short_code}</code>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Stats */}
          <Card>
            <CardHeader>
              <CardTitle>Statistics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                <div className="flex items-center gap-2">
                  <Eye className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">Page Views</span>
                </div>
                <span className="font-semibold">{report.view_count}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">Unique Visitors</span>
                </div>
                <span className="font-semibold">{report.unique_visitors}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">Leads</span>
                </div>
                <span className="font-semibold">{report.leads?.length || 0}</span>
              </div>
              {report.last_viewed_at && (
                <div className="text-xs text-muted-foreground text-center pt-2 border-t">
                  Last viewed: {new Date(report.last_viewed_at).toLocaleString()}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Landing Page Controls */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Landing Page
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Active Status */}
              <div className="flex items-center justify-between">
                <span className="text-sm">Status</span>
                {report.is_active ? (
                  <Badge className="bg-green-100 text-green-800 flex items-center gap-1">
                    <CheckCircle className="w-3 h-3" />
                    Active
                  </Badge>
                ) : (
                  <Badge className="bg-red-100 text-red-800 flex items-center gap-1">
                    <XCircle className="w-3 h-3" />
                    Inactive
                  </Badge>
                )}
              </div>

              {/* Expiration */}
              <div className="flex items-center justify-between">
                <span className="text-sm flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Expires
                </span>
                <span className="text-sm font-medium">
                  {report.expires_at 
                    ? new Date(report.expires_at).toLocaleDateString()
                    : 'Never'
                  }
                </span>
              </div>

              {/* Max Leads */}
              <div className="flex items-center justify-between">
                <span className="text-sm">Max Leads</span>
                <span className="text-sm font-medium">
                  {report.max_leads 
                    ? `${report.leads?.length || 0} / ${report.max_leads}`
                    : 'Unlimited'
                  }
                </span>
              </div>

              {/* Access Code */}
              <div className="flex items-center justify-between">
                <span className="text-sm flex items-center gap-1">
                  {report.access_code ? <Lock className="w-3 h-3" /> : <Unlock className="w-3 h-3" />}
                  Password
                </span>
                <span className="text-sm font-medium">
                  {report.access_code ? 'Protected' : 'None'}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Theme */}
          <Card>
            <CardHeader>
              <CardTitle>Theme</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-lg border"
                  style={{ backgroundColor: report.accent_color }}
                />
                <div>
                  <p className="font-medium text-sm">Accent Color</p>
                  <p className="text-xs text-muted-foreground font-mono">{report.accent_color}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* IDs */}
          <Card>
            <CardHeader>
              <CardTitle>Identifiers</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              <div>
                <p className="text-muted-foreground">Report ID</p>
                <code className="text-xs">{report.id}</code>
              </div>
              <div>
                <p className="text-muted-foreground">Account ID</p>
                <code className="text-xs">{report.account_id}</code>
              </div>
              <div>
                <p className="text-muted-foreground">User ID</p>
                <code className="text-xs">{report.user_id}</code>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}


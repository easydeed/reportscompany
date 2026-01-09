"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  ArrowLeft,
  Download,
  ExternalLink,
  QrCode,
  Users,
  Eye,
  Copy,
  Check,
  Home,
  FileText,
  Loader2,
} from "lucide-react"
import { apiFetch } from "@/lib/api"

type PropertyReport = {
  id: string
  report_type: "seller" | "buyer"
  status: "draft" | "processing" | "complete" | "failed"
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
  sitex_data?: Record<string, any>
  comparables?: any[]
  short_code: string
  qr_code_url?: string
  pdf_url?: string
  view_count: number
  created_at: string
  updated_at: string
}

export default function PropertyReportDetailPage() {
  const params = useParams()
  const router = useRouter()
  const reportId = params.id as string

  const [report, setReport] = useState<PropertyReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [leadsCount, setLeadsCount] = useState(0)

  useEffect(() => {
    loadReport()
  }, [reportId])

  async function loadReport() {
    try {
      setLoading(true)
      const data = await apiFetch(`/v1/property/reports/${reportId}`)
      setReport(data)
      
      // Load leads count for this report
      try {
        const leadsData = await apiFetch(`/v1/leads?property_report_id=${reportId}&limit=1`)
        setLeadsCount(leadsData.total || 0)
      } catch {
        // Ignore leads error
      }
      
      setError(null)
    } catch (e: any) {
      setError(e.message || "Failed to load report")
    } finally {
      setLoading(false)
    }
  }

  async function copyShareLink() {
    if (!report?.short_code) return
    const url = `${window.location.origin}/p/${report.short_code}`
    await navigator.clipboard.writeText(url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "complete":
        return <Badge className="bg-green-500/10 text-green-700 hover:bg-green-500/20">Complete</Badge>
      case "processing":
        return <Badge className="bg-blue-500/10 text-blue-700 hover:bg-blue-500/20">Processing</Badge>
      case "failed":
        return <Badge className="bg-red-500/10 text-red-700 hover:bg-red-500/20">Failed</Badge>
      case "draft":
        return <Badge className="bg-yellow-500/10 text-yellow-700 hover:bg-yellow-500/20">Draft</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div className="rounded-lg border border-red-300 bg-red-50 p-6 text-center">
          <p className="text-red-800">{error || "Report not found"}</p>
        </div>
      </div>
    )
  }

  const publicUrl = report.short_code ? `${typeof window !== 'undefined' ? window.location.origin : ''}/p/${report.short_code}` : null

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push("/app/property")}>
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="font-bold text-2xl">{report.property_address}</h1>
              {getStatusBadge(report.status)}
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
                View Public Page
              </a>
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
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
                  <p className="font-medium">{report.property_county || "N/A"}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">APN</p>
                  <p className="font-medium">{report.apn || "N/A"}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Owner</p>
                  <p className="font-medium">{report.owner_name || "N/A"}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Property Type</p>
                  <p className="font-medium">{report.property_type || "N/A"}</p>
                </div>
                {report.sitex_data && (
                  <>
                    <div>
                      <p className="text-muted-foreground">Bedrooms / Bathrooms</p>
                      <p className="font-medium">
                        {report.sitex_data.bedrooms || "N/A"} bed / {report.sitex_data.bathrooms || "N/A"} bath
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Square Feet</p>
                      <p className="font-medium">
                        {report.sitex_data.sqft ? report.sitex_data.sqft.toLocaleString() : "N/A"} sqft
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Year Built</p>
                      <p className="font-medium">{report.sitex_data.year_built || "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Assessed Value</p>
                      <p className="font-medium">
                        {report.sitex_data.assessed_value
                          ? `$${report.sitex_data.assessed_value.toLocaleString()}`
                          : "N/A"}
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

          {/* Report Details */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Report Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Report Type</p>
                  <p className="font-medium capitalize">{report.report_type}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Language</p>
                  <p className="font-medium">{report.language === "en" ? "English" : "Spanish"}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Created</p>
                  <p className="font-medium">{new Date(report.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Last Updated</p>
                  <p className="font-medium">{new Date(report.updated_at).toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Comparables */}
          {report.comparables && report.comparables.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Comparable Properties ({report.comparables.length})</CardTitle>
                <CardDescription>Recent similar sales used in this report</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {report.comparables.slice(0, 5).map((comp, i) => (
                    <div key={i} className="flex justify-between items-center p-3 rounded-lg bg-muted/50">
                      <div>
                        <p className="font-medium text-sm">{comp.address}</p>
                        <p className="text-xs text-muted-foreground">
                          {comp.bedrooms} bed / {comp.bathrooms} bath · {comp.sqft?.toLocaleString()} sqft
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">${comp.close_price?.toLocaleString()}</p>
                        <p className="text-xs text-muted-foreground">
                          {comp.close_date ? new Date(comp.close_date).toLocaleDateString() : "N/A"}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
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
              <CardDescription>
                Share this code to capture leads
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {report.qr_code_url ? (
                <div className="flex justify-center">
                  <img
                    src={report.qr_code_url}
                    alt="QR Code"
                    className="w-48 h-48 rounded-lg border"
                  />
                </div>
              ) : (
                <div className="w-48 h-48 mx-auto rounded-lg border-2 border-dashed flex items-center justify-center">
                  <p className="text-sm text-muted-foreground">QR code pending</p>
                </div>
              )}
              
              {publicUrl && (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground text-center">Public Link</p>
                  <div className="flex gap-2">
                    <Input
                      value={publicUrl}
                      readOnly
                      className="text-xs h-9"
                    />
                    <Button
                      variant="outline"
                      size="icon"
                      className="h-9 w-9 shrink-0"
                      onClick={copyShareLink}
                    >
                      {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Stats */}
          <Card>
            <CardHeader>
              <CardTitle>Statistics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
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
                  <span className="text-sm">Leads Captured</span>
                </div>
                <span className="font-semibold">{leadsCount}</span>
              </div>
              {leadsCount > 0 && (
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => router.push(`/app/leads?property_report_id=${reportId}`)}
                >
                  View Leads
                  <ExternalLink className="w-4 h-4 ml-2" />
                </Button>
              )}
            </CardContent>
          </Card>

          {/* Accent Color Preview */}
          <Card>
            <CardHeader>
              <CardTitle>Theme</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-lg"
                  style={{ backgroundColor: report.accent_color }}
                />
                <div>
                  <p className="font-medium text-sm">Accent Color</p>
                  <p className="text-xs text-muted-foreground">{report.accent_color}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

// Simple Input for the share link
function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={`flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
      {...props}
    />
  )
}


"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowLeft,
  Download,
  ExternalLink,
  QrCode,
  Settings,
  Trash2,
  Copy,
  Check,
  Users,
  Eye,
  RefreshCw,
  Loader2,
  Home,
  Calendar,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { apiFetch } from "@/lib/api";

interface PropertyReport {
  id: string;
  account_id: string;
  user_id: string;
  report_type: "seller" | "buyer";
  theme: number;
  accent_color: string;
  language: string;
  property_address: string;
  property_city: string;
  property_state: string;
  property_zip: string;
  property_county: string;
  apn: string;
  owner_name: string;
  legal_description: string;
  property_type: string;
  sitex_data: any;
  comparables: any[];
  pdf_url: string | null;
  status: "draft" | "processing" | "complete" | "failed";
  error_message: string | null;
  short_code: string;
  qr_code_url: string | null;
  view_count: number;
  unique_visitors: number;
  last_viewed_at: string | null;
  is_active: boolean;
  expires_at: string | null;
  max_leads: number | null;
  created_at: string;
  updated_at: string;
}

interface Lead {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  status: string;
  created_at: string;
}

export default function PropertyReportDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const reportId = params.id as string;
  const justCreated = searchParams.get("created") === "true";

  const [report, setReport] = useState<PropertyReport | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    loadReport();
    loadLeads();
  }, [reportId]);

  // Poll for status updates if processing
  useEffect(() => {
    if (report?.status === "processing" || (justCreated && !report)) {
      setPolling(true);
      const interval = setInterval(async () => {
        try {
          const data = await apiFetch(`/v1/property/reports/${reportId}`);
          setReport(data);
          if (data.status !== "processing") {
            clearInterval(interval);
            setPolling(false);
          }
        } catch (e) {
          // Ignore polling errors
        }
      }, 3000);

      return () => {
        clearInterval(interval);
        setPolling(false);
      };
    }
  }, [report?.status, reportId, justCreated]);

  async function loadReport() {
    try {
      setLoading(true);
      const data = await apiFetch(`/v1/property/reports/${reportId}`);
      setReport(data);
      setError(null);
    } catch (e: any) {
      setError(e.message || "Failed to load report");
    } finally {
      setLoading(false);
    }
  }

  async function loadLeads() {
    try {
      const data = await apiFetch(`/v1/leads?property_report_id=${reportId}&limit=5`);
      setLeads(data.leads || []);
    } catch (e) {
      // Ignore lead errors
    }
  }

  async function handleDelete() {
    try {
      setDeleting(true);
      await apiFetch(`/v1/property/reports/${reportId}`, { method: "DELETE" });
      router.push("/app/property");
    } catch (e: any) {
      setError(e.message || "Failed to delete report");
      setDeleting(false);
    }
  }

  const copyLink = () => {
    if (report?.short_code) {
      const url = `${window.location.origin}/p/${report.short_code}`;
      navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "complete":
        return (
          <Badge className="bg-green-500/10 text-green-700 hover:bg-green-500/20">
            Complete
          </Badge>
        );
      case "processing":
        return (
          <Badge className="bg-blue-500/10 text-blue-700 hover:bg-blue-500/20">
            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            Processing
          </Badge>
        );
      case "failed":
        return (
          <Badge className="bg-red-500/10 text-red-700 hover:bg-red-500/20">
            Failed
          </Badge>
        );
      case "draft":
        return (
          <Badge className="bg-yellow-500/10 text-yellow-700 hover:bg-yellow-500/20">
            Draft
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href="/app/property">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="w-5 h-5" />
            </Button>
          </Link>
          <h1 className="font-bold text-2xl">Loading...</h1>
        </div>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href="/app/property">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="w-5 h-5" />
            </Button>
          </Link>
          <h1 className="font-bold text-2xl">Report Not Found</h1>
        </div>
        <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-800">
          {error || "This report could not be found"}
        </div>
      </div>
    );
  }

  const landingPageUrl = `${typeof window !== "undefined" ? window.location.origin : ""}/p/${report.short_code}`;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/app/property">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="w-5 h-5" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="font-bold text-2xl">{report.property_address}</h1>
              {getStatusBadge(report.status)}
            </div>
            <p className="text-muted-foreground">
              {report.property_city}, {report.property_state} {report.property_zip}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link href={`/app/property/${reportId}/settings`}>
            <Button variant="outline" size="sm">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Button>
          </Link>

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700">
                <Trash2 className="w-4 h-4 mr-2" />
                Delete
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete Property Report</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to delete this report? This will also remove the
                  landing page and QR code. This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleDelete}
                  disabled={deleting}
                  className="bg-red-600 hover:bg-red-700"
                >
                  {deleting ? "Deleting..." : "Delete"}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>

      {/* Processing Message */}
      {report.status === "processing" && (
        <div className="rounded-lg border border-blue-300 bg-blue-50 p-4 flex items-center gap-3">
          <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
          <div>
            <p className="font-medium text-blue-900">Generating your report...</p>
            <p className="text-sm text-blue-700">
              This usually takes 15-30 seconds. The page will update automatically.
            </p>
          </div>
        </div>
      )}

      {/* Failed Message */}
      {report.status === "failed" && (
        <div className="rounded-lg border border-red-300 bg-red-50 p-4">
          <p className="font-medium text-red-900">Report generation failed</p>
          <p className="text-sm text-red-700">{report.error_message || "An error occurred"}</p>
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - Property Info & PDF */}
        <div className="lg:col-span-2 space-y-6">
          {/* Property Details */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Home className="w-5 h-5" />
                Property Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Owner</p>
                  <p className="font-medium">{report.owner_name || "N/A"}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">APN</p>
                  <p className="font-medium">{report.apn || "N/A"}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">County</p>
                  <p className="font-medium">{report.property_county || "N/A"}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Property Type</p>
                  <p className="font-medium">{report.property_type || "N/A"}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Report Type</p>
                  <p className="font-medium capitalize">{report.report_type}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Created</p>
                  <p className="font-medium">
                    {new Date(report.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* PDF Preview/Download */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Report PDF
              </CardTitle>
            </CardHeader>
            <CardContent>
              {report.status === "complete" && report.pdf_url ? (
                <div className="space-y-4">
                  <div className="aspect-[8.5/11] bg-muted rounded-lg overflow-hidden border">
                    <iframe
                      src={`${report.pdf_url}#toolbar=0`}
                      className="w-full h-full"
                      title="PDF Preview"
                    />
                  </div>
                  <div className="flex gap-2">
                    <a href={report.pdf_url} target="_blank" rel="noopener noreferrer" className="flex-1">
                      <Button className="w-full">
                        <Download className="w-4 h-4 mr-2" />
                        Download PDF
                      </Button>
                    </a>
                    <a href={report.pdf_url} target="_blank" rel="noopener noreferrer">
                      <Button variant="outline">
                        <ExternalLink className="w-4 h-4" />
                      </Button>
                    </a>
                  </div>
                </div>
              ) : report.status === "processing" ? (
                <div className="aspect-[8.5/11] bg-muted rounded-lg flex items-center justify-center">
                  <div className="text-center">
                    <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3 text-muted-foreground" />
                    <p className="text-muted-foreground">Generating PDF...</p>
                  </div>
                </div>
              ) : (
                <div className="aspect-[8.5/11] bg-muted rounded-lg flex items-center justify-center">
                  <p className="text-muted-foreground">PDF not available</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column - QR, Landing Page, Leads */}
        <div className="space-y-6">
          {/* QR Code & Landing Page */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <QrCode className="w-5 h-5" />
                QR Code & Landing Page
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* QR Code */}
              <div className="flex justify-center">
                {report.qr_code_url ? (
                  <div className="bg-white p-4 rounded-lg border">
                    <Image
                      src={report.qr_code_url}
                      alt="QR Code"
                      width={160}
                      height={160}
                      className="w-40 h-40"
                    />
                  </div>
                ) : (
                  <div className="w-40 h-40 bg-muted rounded-lg flex items-center justify-center">
                    <QrCode className="w-12 h-12 text-muted-foreground" />
                  </div>
                )}
              </div>

              {/* Landing Page URL */}
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Landing Page URL</p>
                <div className="flex gap-2">
                  <code className="flex-1 text-sm bg-muted px-3 py-2 rounded truncate">
                    {landingPageUrl}
                  </code>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="outline" size="icon" onClick={copyLink}>
                          {copied ? (
                            <Check className="w-4 h-4 text-green-600" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        {copied ? "Copied!" : "Copy link"}
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                  <a href={landingPageUrl} target="_blank" rel="noopener noreferrer">
                    <Button variant="outline" size="icon">
                      <ExternalLink className="w-4 h-4" />
                    </Button>
                  </a>
                </div>
              </div>

              {/* Status */}
              <div className="flex items-center justify-between text-sm pt-2 border-t">
                <span className="text-muted-foreground">Status</span>
                <Badge variant={report.is_active ? "default" : "secondary"}>
                  {report.is_active ? "Active" : "Inactive"}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Eye className="w-5 h-5" />
                Analytics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <p className="text-3xl font-bold">{report.view_count}</p>
                  <p className="text-sm text-muted-foreground">Total Views</p>
                </div>
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <p className="text-3xl font-bold">{report.unique_visitors}</p>
                  <p className="text-sm text-muted-foreground">Unique Visitors</p>
                </div>
              </div>
              {report.last_viewed_at && (
                <p className="text-xs text-muted-foreground mt-3 text-center">
                  Last viewed: {new Date(report.last_viewed_at).toLocaleString()}
                </p>
              )}
            </CardContent>
          </Card>

          {/* Leads */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                Recent Leads
              </CardTitle>
              <Link href={`/app/leads?property_report_id=${reportId}`}>
                <Button variant="ghost" size="sm">
                  View All
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {leads.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No leads captured yet
                </p>
              ) : (
                <div className="space-y-3">
                  {leads.map((lead) => (
                    <div
                      key={lead.id}
                      className="flex items-center justify-between text-sm border-b pb-2 last:border-0"
                    >
                      <div>
                        <p className="font-medium">{lead.name}</p>
                        <p className="text-xs text-muted-foreground">{lead.email}</p>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {lead.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

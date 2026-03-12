"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Download,
  Eye,
  FileJson,
  Share2,
  Loader2,
  MapPin,
  FileText,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

interface MarketReport {
  id: string;
  report_type: string;
  status: "completed" | "complete" | "processing" | "pending" | "failed";
  city?: string;
  html_url?: string;
  json_url?: string;
  csv_url?: string;
  pdf_url?: string;
  theme_id?: string;
  generated_at?: string;
}

const STATUS_BADGE: Record<string, { className: string; label: string }> = {
  completed: {
    className: "bg-green-500/10 text-green-700 hover:bg-green-500/20",
    label: "Completed",
  },
  complete: {
    className: "bg-green-500/10 text-green-700 hover:bg-green-500/20",
    label: "Completed",
  },
  processing: {
    className: "bg-blue-500/10 text-blue-700 hover:bg-blue-500/20",
    label: "Processing",
  },
  pending: {
    className: "bg-yellow-500/10 text-yellow-700 hover:bg-yellow-500/20",
    label: "Pending",
  },
  failed: {
    className: "bg-red-500/10 text-red-700 hover:bg-red-500/20",
    label: "Failed",
  },
};

export default function MarketReportDetailPage() {
  const params = useParams();
  const router = useRouter();
  const reportId = params.id as string;

  const [report, setReport] = useState<MarketReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadReport();
  }, [reportId]);

  useEffect(() => {
    if (
      report?.status === "processing" ||
      report?.status === "pending"
    ) {
      const interval = setInterval(async () => {
        try {
          const data = await apiFetch(`/v1/reports/${reportId}`);
          setReport(data);
          if (data.status !== "processing" && data.status !== "pending") {
            clearInterval(interval);
          }
        } catch {
          // ignore polling errors
        }
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [report?.status, reportId]);

  async function loadReport() {
    try {
      setLoading(true);
      const data = await apiFetch(`/v1/reports/${reportId}`);
      setReport(data);
      setError(null);
    } catch (e: any) {
      setError(e.message || "Failed to load report");
    } finally {
      setLoading(false);
    }
  }

  const badge = STATUS_BADGE[report?.status ?? ""] ?? {
    className: "",
    label: report?.status ?? "",
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href="/app/reports">
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
          <Link href="/app/reports">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="w-5 h-5" />
            </Button>
          </Link>
          <h1 className="font-bold text-2xl">Report Not Found</h1>
        </div>
        <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-800">
          {error || "This report could not be found."}
        </div>
      </div>
    );
  }

  const title = report.city
    ? `${report.report_type.replace(/_/g, " ")} — ${report.city}`
    : report.report_type.replace(/_/g, " ");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/app/reports">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="w-5 h-5" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="font-bold text-2xl capitalize">{title}</h1>
              <Badge className={badge.className}>
                {report.status === "processing" && (
                  <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                )}
                {badge.label}
              </Badge>
            </div>
            {report.generated_at && (
              <p className="text-muted-foreground text-sm">
                Generated{" "}
                {new Date(report.generated_at).toLocaleDateString(undefined, {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </p>
            )}
          </div>
        </div>

        {(report.status === "completed" || report.status === "complete") && (
          <Button variant="outline" size="sm" onClick={loadReport}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        )}
      </div>

      {/* Processing banner */}
      {(report.status === "processing" || report.status === "pending") && (
        <div className="rounded-lg border border-blue-300 bg-blue-50 p-4 flex items-center gap-3">
          <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
          <div>
            <p className="font-medium text-blue-900">
              Generating your report...
            </p>
            <p className="text-sm text-blue-700">
              This usually takes 30–90 seconds. The page will update
              automatically.
            </p>
          </div>
        </div>
      )}

      {/* Failed banner */}
      {report.status === "failed" && (
        <div className="rounded-lg border border-red-300 bg-red-50 p-4">
          <p className="font-medium text-red-900">
            Report generation failed
          </p>
          <p className="text-sm text-red-700">
            Please try generating a new report. If the issue persists, contact
            support.
          </p>
        </div>
      )}

      {/* Details card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="w-5 h-5" />
            Report Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Type</p>
              <p className="font-medium capitalize">
                {report.report_type.replace(/_/g, " ")}
              </p>
            </div>
            {report.city && (
              <div>
                <p className="text-muted-foreground">City</p>
                <p className="font-medium">{report.city}</p>
              </div>
            )}
            <div>
              <p className="text-muted-foreground">Created</p>
              <p className="font-medium">
                {report.generated_at
                  ? new Date(report.generated_at).toLocaleDateString()
                  : "—"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actions / Downloads */}
      {(report.status === "completed" || report.status === "complete") && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Downloads
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              {report.pdf_url && (
                <a
                  href={report.pdf_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button>
                    <Eye className="w-4 h-4 mr-2" />
                    View in Browser
                  </Button>
                </a>
              )}
              {report.pdf_url && (
                <a
                  href={report.pdf_url}
                  download
                >
                  <Button variant="outline">
                    <Download className="w-4 h-4 mr-2" />
                    Download PDF
                  </Button>
                </a>
              )}
              {report.html_url && (
                <a
                  href={report.html_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button variant="outline">
                    <Eye className="w-4 h-4 mr-2" />
                    Preview HTML
                  </Button>
                </a>
              )}
              {report.json_url && (
                <a
                  href={report.json_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button variant="outline">
                    <FileJson className="w-4 h-4 mr-2" />
                    View JSON
                  </Button>
                </a>
              )}
              {report.csv_url && (
                <a
                  href={report.csv_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button variant="outline">
                    <Download className="w-4 h-4 mr-2" />
                    Download CSV
                  </Button>
                </a>
              )}
            </div>

            {/* PDF inline preview */}
            {report.pdf_url && (
              <div className="mt-6 aspect-[8.5/11] bg-muted rounded-lg overflow-hidden border">
                <iframe
                  src={`${report.pdf_url}#toolbar=0`}
                  className="w-full h-full"
                  title="PDF Preview"
                />
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

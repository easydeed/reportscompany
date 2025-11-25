"use client";

import { useState } from "react";
import { Download, FileText, Mail, Loader2, Check, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { REPORT_TYPE_OPTIONS, ReportType } from "@/lib/sample-report-data";
import { cn } from "@/lib/utils";

interface DownloadToolsProps {
  brandName: string;
}

/**
 * DownloadTools Component
 * 
 * Provides sample PDF download and test email functionality.
 * 
 * Pass B4.3: Download Tools UI
 */
export function DownloadTools({ brandName }: DownloadToolsProps) {
  const [reportType, setReportType] = useState<ReportType>("market_snapshot");
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const [testEmail, setTestEmail] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [sendSuccess, setSendSuccess] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);

  const handleDownloadPdf = async () => {
    setIsDownloading(true);
    setDownloadSuccess(false);
    setDownloadError(null);

    try {
      const response = await fetch("/api/proxy/v1/branding/sample-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_type: reportType }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || data.detail || "Failed to generate PDF");
      }

      // Get the blob and trigger download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${brandName.replace(/\s+/g, "-").toLowerCase()}-sample-${reportType.replace(/_/g, "-")}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setDownloadSuccess(true);
      setTimeout(() => setDownloadSuccess(false), 3000);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Download failed";
      setDownloadError(message);
      setTimeout(() => setDownloadError(null), 5000);
    } finally {
      setIsDownloading(false);
    }
  };

  const handleSendTestEmail = async () => {
    if (!testEmail || !testEmail.includes("@")) {
      setSendError("Please enter a valid email address");
      return;
    }

    setIsSending(true);
    setSendSuccess(false);
    setSendError(null);

    try {
      const response = await fetch("/api/proxy/v1/branding/test-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: testEmail, report_type: reportType }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || data.detail || "Failed to send email");
      }

      setSendSuccess(true);
      setTimeout(() => setSendSuccess(false), 5000);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Send failed";
      setSendError(message);
      setTimeout(() => setSendError(null), 5000);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Report Type Selector */}
      <div className="space-y-2">
        <Label>Report Type</Label>
        <Select value={reportType} onValueChange={(v) => setReportType(v as ReportType)}>
          <SelectTrigger className="w-full max-w-sm">
            <SelectValue placeholder="Select report type" />
          </SelectTrigger>
          <SelectContent>
            {REPORT_TYPE_OPTIONS.map((type) => (
              <SelectItem key={type.value} value={type.value}>
                <div className="flex flex-col">
                  <span>{type.label}</span>
                  <span className="text-xs text-muted-foreground">{type.description}</span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground">
          Select a report type to download or send as a test
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Download PDF Card */}
        <div className="border rounded-lg p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <FileText className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold">Download Sample PDF</h3>
              <p className="text-sm text-muted-foreground">
                Get a branded PDF with sample data
              </p>
            </div>
          </div>

          <div className="bg-muted/50 rounded-lg p-4 text-sm text-muted-foreground">
            <p>
              Download a sample <strong>{REPORT_TYPE_OPTIONS.find(t => t.value === reportType)?.label}</strong> report
              branded with your logo and colors. Uses Beverly Hills demo data.
            </p>
          </div>

          <Button
            onClick={handleDownloadPdf}
            disabled={isDownloading}
            className={cn(
              "w-full gap-2",
              downloadSuccess && "bg-green-600 hover:bg-green-600"
            )}
          >
            {isDownloading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Generating PDF...
              </>
            ) : downloadSuccess ? (
              <>
                <Check className="w-4 h-4" />
                Downloaded!
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                Download Sample PDF
              </>
            )}
          </Button>

          {downloadError && (
            <div className="flex items-center gap-2 text-sm text-destructive">
              <AlertCircle className="w-4 h-4" />
              {downloadError}
            </div>
          )}
        </div>

        {/* Test Email Card */}
        <div className="border rounded-lg p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center">
              <Mail className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <h3 className="font-semibold">Send Test Email</h3>
              <p className="text-sm text-muted-foreground">
                Preview how branded emails look
              </p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="test-email">Email Address</Label>
              <Input
                id="test-email"
                type="email"
                placeholder="you@example.com"
                value={testEmail}
                onChange={(e) => setTestEmail(e.target.value)}
              />
            </div>
          </div>

          <Button
            onClick={handleSendTestEmail}
            disabled={isSending || !testEmail}
            variant="outline"
            className={cn(
              "w-full gap-2",
              sendSuccess && "border-green-600 text-green-600"
            )}
          >
            {isSending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Sending...
              </>
            ) : sendSuccess ? (
              <>
                <Check className="w-4 h-4" />
                Email Sent!
              </>
            ) : (
              <>
                <Mail className="w-4 h-4" />
                Send Test Email
              </>
            )}
          </Button>

          {sendError && (
            <div className="flex items-center gap-2 text-sm text-destructive">
              <AlertCircle className="w-4 h-4" />
              {sendError}
            </div>
          )}

          <p className="text-xs text-muted-foreground">
            Coming soon: Receive a branded email with the sample report attached.
          </p>
        </div>
      </div>

      {/* Tips */}
      <div className="bg-muted/30 rounded-lg p-4 space-y-2">
        <h4 className="font-medium text-sm">Tips for Best Results</h4>
        <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
          <li>Use a high-resolution logo (at least 400px wide)</li>
          <li>PNG with transparent background works best</li>
          <li>Choose colors that have good contrast</li>
          <li>Test on both light and dark backgrounds</li>
        </ul>
      </div>
    </div>
  );
}


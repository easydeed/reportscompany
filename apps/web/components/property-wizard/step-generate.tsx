"use client";

import { useRef, useState, useCallback, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Check,
  Copy,
  Download,
  ExternalLink,
  Loader2,
  MapPin,
  RotateCcw,
  Sparkles,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import type { PropertyData, Theme, Comparable, PropertyReportResponse } from "./types";

interface StepGenerateProps {
  property: PropertyData;
  selectedComps: Comparable[];
  selectedTheme: Theme;
  accentColor: string;
  selectedPageIds: string[];
  generationPhase: "idle" | "generating" | "success" | "error";
  onGenerate: () => void;
  onReset: () => void;
  goToStep: (step: number) => void;
  generationProgress: number;
  currentStage: number;
  onSetPhase: (phase: "idle" | "generating" | "success" | "error") => void;
  onSetProgress: (progress: number) => void;
  onSetStage: (stage: number) => void;
}

export function StepGenerate({
  property,
  selectedComps,
  selectedTheme,
  accentColor,
  selectedPageIds,
  generationPhase,
  onGenerate,
  onReset,
  goToStep,
  generationProgress,
  currentStage,
  onSetPhase,
  onSetProgress,
  onSetStage,
}: StepGenerateProps) {
  const [copied, setCopied] = useState(false);
  const [reportResult, setReportResult] = useState<PropertyReportResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const generatingRef = useRef(false);

  const avgPrice =
    selectedComps.length > 0
      ? Math.round(
          selectedComps.reduce((a, c) => a + c.sale_price, 0) /
            selectedComps.length
        )
      : 0;
  const minPrice = Math.min(...selectedComps.map((c) => c.sale_price));
  const maxPrice = Math.max(...selectedComps.map((c) => c.sale_price));

  // Dynamic stage labels
  const dynamicStages = useMemo(
    () => [
      { label: "Fetching property data" },
      { label: `Analyzing ${selectedComps.length} comparables` },
      { label: `Rendering ${selectedPageIds.length} report pages` },
      { label: "Generating PDF" },
      { label: "Finalizing QR code & share link" },
    ],
    [selectedComps.length, selectedPageIds.length]
  );

  const startGeneration = useCallback(async () => {
    if (generatingRef.current) return;
    generatingRef.current = true;
    setErrorMessage(null);
    onGenerate(); // Sets phase to "generating"

    try {
      // Stage 1: Create report
      onSetStage(0);
      onSetProgress(10);

      const createRes = await fetch("/api/proxy/v1/property/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          address: property.full_address,
          property_address: property.street_address,
          property_city: property.city,
          property_state: property.state,
          property_zip: property.zip_code,
          theme: selectedTheme.id,
          accent_color: accentColor,
          comparables: selectedComps.map((c) => ({
            id: c.id,
            address: c.address,
            sale_price: c.sale_price,
            sold_date: c.sold_date,
            sqft: c.sqft,
            bedrooms: c.bedrooms,
            bathrooms: c.bathrooms,
            year_built: c.year_built,
            distance_miles: c.distance_miles,
            price_per_sqft: c.price_per_sqft,
            photo_url: c.photo_url,
          })),
          selected_pages: selectedPageIds,
        }),
      });

      if (!createRes.ok) {
        const errData = await createRes.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to create report");
      }

      const { id: reportId } = await createRes.json();

      // Stage 2: Poll for completion
      onSetStage(1);
      onSetProgress(25);

      let attempts = 0;
      const maxAttempts = 120; // 2 minutes max

      const poll = async (): Promise<PropertyReportResponse> => {
        const statusRes = await fetch(
          `/api/proxy/v1/property/reports/${reportId}`
        );
        if (!statusRes.ok) throw new Error("Failed to check report status");

        const report: PropertyReportResponse = await statusRes.json();

        if (report.status === "completed" || report.status === "complete") {
          return report;
        }

        if (report.status === "failed") {
          throw new Error(
            report.error_message || "Report generation failed"
          );
        }

        attempts++;
        if (attempts >= maxAttempts) {
          throw new Error("Report generation timed out");
        }

        // Update progress based on attempts
        const progressPercent = Math.min(
          25 + (attempts / maxAttempts) * 70,
          95
        );
        onSetProgress(Math.round(progressPercent));

        // Update stage indicator based on progress
        if (progressPercent < 40) onSetStage(1);
        else if (progressPercent < 60) onSetStage(2);
        else if (progressPercent < 85) onSetStage(3);
        else onSetStage(4);

        await new Promise((resolve) => setTimeout(resolve, 1000));
        return poll();
      };

      const completedReport = await poll();

      // Done!
      onSetProgress(100);
      onSetStage(4);
      setReportResult(completedReport);

      setTimeout(() => {
        onSetPhase("success");
        generatingRef.current = false;
      }, 500);
    } catch (err: any) {
      console.error("Report generation failed:", err);
      setErrorMessage(err.message || "Report generation failed");
      onSetPhase("error");
      generatingRef.current = false;
    }
  }, [
    property,
    selectedComps,
    selectedTheme,
    accentColor,
    selectedPageIds,
    onGenerate,
    onSetPhase,
    onSetProgress,
    onSetStage,
  ]);

  function handleCopy() {
    const shareUrl = reportResult?.short_code
      ? `${window.location.origin}/p/${reportResult.short_code}`
      : "Link not available";
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  // Idle / Review
  if (generationPhase === "idle") {
    return (
      <div className="space-y-6 max-w-2xl">
        <div className="flex items-center gap-3 mb-2">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-[#EEF2FF]">
            <Sparkles className="h-5 w-5 text-[#6366F1]" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">
              Review & Generate
            </h2>
            <p className="text-sm text-muted-foreground">
              Everything looks good? Let&apos;s create your report.
            </p>
          </div>
        </div>

        {/* Summary Card */}
        <div className="rounded-2xl border border-border bg-card overflow-hidden divide-y divide-border">
          {/* Property */}
          <div className="p-5 flex items-start justify-between">
            <div className="flex items-start gap-3">
              <MapPin className="h-4 w-4 text-[#6366F1] mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-semibold text-foreground">
                  Property
                </p>
                <p className="text-sm text-muted-foreground mt-0.5">
                  {property.full_address}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {property.bedrooms} bed {"·"} {property.bathrooms} bath {"·"}{" "}
                  {property.sqft.toLocaleString()} sqft {"·"} Built{" "}
                  {property.year_built}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-[#6366F1] shrink-0"
              onClick={() => goToStep(0)}
            >
              Edit
            </Button>
          </div>

          {/* Comparables */}
          <div className="p-5 flex items-start justify-between">
            <div className="flex items-start gap-3">
              <svg
                className="h-4 w-4 text-[#6366F1] mt-0.5 shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              <div>
                <p className="text-sm font-semibold text-foreground">
                  Comparables
                </p>
                <p className="text-sm text-muted-foreground mt-0.5">
                  {selectedComps.length} comparable sales selected
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Avg price: ${avgPrice.toLocaleString()} {"·"} Range: $
                  {Math.round(minPrice / 1000)}K–$
                  {Math.round(maxPrice / 1000)}K
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-[#6366F1] shrink-0"
              onClick={() => goToStep(1)}
            >
              Edit
            </Button>
          </div>

          {/* Theme */}
          <div className="p-5 flex items-start justify-between">
            <div className="flex items-start gap-3">
              <svg
                className="h-4 w-4 text-[#6366F1] mt-0.5 shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
                />
              </svg>
              <div>
                <p className="text-sm font-semibold text-foreground">
                  Theme & Pages
                </p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-sm text-muted-foreground">
                    {selectedTheme.name}
                  </span>
                  <div
                    className="w-3 h-3 rounded-full border border-border"
                    style={{ backgroundColor: accentColor }}
                  />
                  <span className="text-sm text-muted-foreground">
                    {"·"} {selectedPageIds.length} pages
                  </span>
                </div>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-[#6366F1] shrink-0"
              onClick={() => goToStep(2)}
            >
              Edit
            </Button>
          </div>
        </div>

        {/* Generate CTA */}
        <div className="rounded-2xl border border-border bg-card p-6 text-center">
          <p className="text-sm text-muted-foreground mb-4">
            This will create a branded PDF report with QR code and shareable
            link.
          </p>
          <Button
            className="bg-[#6366F1] text-white text-base font-semibold py-6 w-full rounded-xl hover:bg-[#4F46E5] shadow-lg shadow-[#6366F1]/25"
            onClick={startGeneration}
          >
            <Sparkles className="h-5 w-5 mr-2" />
            Generate Report
          </Button>
        </div>
      </div>
    );
  }

  // Generating
  if (generationPhase === "generating") {
    return (
      <div className="flex flex-col items-center justify-center py-12 max-w-lg mx-auto">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="mb-6"
        >
          <Loader2 className="h-12 w-12 text-[#6366F1] animate-spin" />
        </motion.div>

        <h2 className="text-xl font-bold text-foreground mb-6">
          Creating Your Property Report
        </h2>

        <div className="w-full mb-6">
          <Progress value={generationProgress} className="h-2" />
          <p className="text-right text-xs text-muted-foreground mt-1">
            {generationProgress}%
          </p>
        </div>

        <div className="w-full space-y-3">
          {dynamicStages.map((stage, i) => {
            const status =
              i < currentStage
                ? "done"
                : i === currentStage
                ? "active"
                : "waiting";
            return (
              <motion.div
                key={stage.label}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  {status === "done" && (
                    <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center">
                      <Check className="h-3 w-3 text-emerald-600" />
                    </div>
                  )}
                  {status === "active" && (
                    <div className="w-5 h-5 flex items-center justify-center">
                      <Loader2 className="h-4 w-4 text-[#6366F1] animate-spin" />
                    </div>
                  )}
                  {status === "waiting" && (
                    <div className="w-5 h-5 rounded-full border-2 border-border" />
                  )}
                  <span
                    className={`text-sm ${
                      status === "done"
                        ? "text-foreground"
                        : status === "active"
                        ? "text-foreground font-medium"
                        : "text-muted-foreground"
                    }`}
                  >
                    {stage.label}
                  </span>
                </div>
                <span
                  className={`text-xs ${
                    status === "done"
                      ? "text-emerald-600"
                      : status === "active"
                      ? "text-[#6366F1]"
                      : "text-muted-foreground"
                  }`}
                >
                  {status === "done"
                    ? "Done"
                    : status === "active"
                    ? "In progress..."
                    : "Waiting"}
                </span>
              </motion.div>
            );
          })}
        </div>

        <p className="text-xs text-muted-foreground mt-6">
          Usually takes 30-60 seconds
        </p>
      </div>
    );
  }

  // Success
  if (generationPhase === "success") {
    const shareUrl = reportResult?.short_code
      ? `${typeof window !== "undefined" ? window.location.origin : ""}/p/${reportResult.short_code}`
      : null;

    return (
      <div className="flex flex-col items-center justify-center py-12 max-w-lg mx-auto">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{
            type: "spring",
            stiffness: 260,
            damping: 20,
          }}
          className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mb-4"
        >
          <Check className="h-8 w-8 text-emerald-600" />
        </motion.div>

        <motion.h2
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-xl font-bold text-foreground"
        >
          Report Generated Successfully!
        </motion.h2>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-sm text-muted-foreground mt-1"
        >
          {property.street_address}, {property.city}
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-8 w-full rounded-2xl border border-border bg-card p-6"
        >
          <div className="flex flex-col sm:flex-row gap-6 items-center">
            {/* QR Code */}
            <div className="w-32 h-32 rounded-xl bg-muted border border-border shrink-0 relative overflow-hidden">
              {reportResult?.qr_code_url ? (
                <img
                  src={reportResult.qr_code_url}
                  alt="QR Code"
                  className="w-full h-full object-contain p-1"
                />
              ) : (
                <>
                  <div
                    className="absolute inset-2"
                    style={{
                      backgroundImage:
                        "repeating-conic-gradient(hsl(var(--foreground)) 0% 25%, transparent 0% 50%) 0 0 / 8px 8px",
                      opacity: 0.15,
                    }}
                  />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-[8px] font-bold text-muted-foreground bg-card px-1.5 py-0.5 rounded">
                      QR CODE
                    </div>
                  </div>
                </>
              )}
            </div>

            <div className="flex-1 space-y-3 w-full">
              <Button
                className="w-full bg-[#6366F1] text-white hover:bg-[#4F46E5] gap-2"
                onClick={() => {
                  if (reportResult?.pdf_url) {
                    window.open(reportResult.pdf_url, "_blank");
                  }
                }}
              >
                <Download className="h-4 w-4" />
                Download PDF
              </Button>
              <Button
                variant="outline"
                className="w-full gap-2 bg-transparent"
                onClick={handleCopy}
              >
                {copied ? (
                  <>
                    <Check className="h-4 w-4" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4" />
                    Copy Share Link
                  </>
                )}
              </Button>
              {shareUrl && (
                <p className="text-xs text-muted-foreground text-center">
                  {shareUrl}
                </p>
              )}
              <Button
                variant="ghost"
                className="w-full gap-2 text-muted-foreground"
                onClick={() => {
                  window.location.href = "/app/property";
                }}
              >
                <ExternalLink className="h-4 w-4" />
                View All Reports
              </Button>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-6"
        >
          <Button
            variant="ghost"
            className="text-muted-foreground gap-2"
            onClick={onReset}
          >
            <RotateCcw className="h-4 w-4" />
            Create Another Report
          </Button>
        </motion.div>
      </div>
    );
  }

  // Error
  return (
    <div className="flex flex-col items-center justify-center py-12 max-w-lg mx-auto">
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", stiffness: 260, damping: 20 }}
        className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mb-4"
      >
        <X className="h-8 w-8 text-red-600" />
      </motion.div>

      <h2 className="text-xl font-bold text-foreground">
        Report Generation Failed
      </h2>
      <p className="text-sm text-muted-foreground mt-1">
        {errorMessage || "Something went wrong. Please try again."}
      </p>

      <div className="flex gap-3 mt-6">
        <Button
          className="bg-[#6366F1] text-white hover:bg-[#4F46E5] gap-2"
          onClick={() => {
            generatingRef.current = false;
            startGeneration();
          }}
        >
          <RotateCcw className="h-4 w-4" />
          Retry
        </Button>
        <Button
          variant="outline"
          onClick={() => {
            onSetPhase("idle");
            onSetProgress(0);
            onSetStage(0);
            generatingRef.current = false;
          }}
        >
          Back to Review
        </Button>
      </div>
    </div>
  );
}

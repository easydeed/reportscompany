"use client";

import { useRef, useState, useCallback, useMemo } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Check, Download, ExternalLink, RotateCcw, X } from "lucide-react";
import { StepHeader } from "@/components/unified-wizard/wizard-ui";
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
      { label: "Finalizing report" },
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
          apn: property.apn || undefined,
          owner_name: property.owner_name || undefined,
          theme: selectedTheme.id,
          accent_color: accentColor,
          // Send full property data so worker doesn't need a second SiteX call
          sitex_data: {
            street: property.street_address,
            full_address: property.full_address,
            city: property.city,
            state: property.state,
            zip_code: property.zip_code,
            county: property.county || "",
            apn: property.apn || "",
            owner_name: property.owner_name || "",
            legal_description: property.legal_description || "",
            bedrooms: property.bedrooms,
            bathrooms: property.bathrooms,
            sqft: property.sqft,
            lot_size: property.lot_size,
            year_built: property.year_built,
            assessed_value: property.assessed_value,
            tax_amount: property.tax_amount,
            latitude: property.latitude,
            longitude: property.longitude,
            property_type: property.property_type || "",
            unit_number: property.unit_number || "",
            unit_type: property.unit_type || "",
            // D-118. Without these three the worker's sitex_data has no sale
            // and the subject's price row falls back to N/A — the wizard path
            // and the lookup path would disagree, which is D-135's
            // land_value/$0 split all over again.
            last_sale_price: property.last_sale_price,
            last_sale_date: property.last_sale_date,
            last_sale_price_per_sqft: property.last_sale_price_per_sqft,
          },
          comparables: selectedComps.map((c) => ({
            id: c.id,
            address: c.address,
            city: c.city,
            state: c.state,
            zip_code: c.zip,
            sale_price: c.sale_price,
            list_price: c.list_price,
            sold_date: c.sold_date,
            list_date: c.list_date,
            sqft: c.sqft,
            bedrooms: c.bedrooms,
            bathrooms: c.bathrooms,
            year_built: c.year_built,
            distance_miles: c.distance_miles,
            price_per_sqft: c.price_per_sqft,
            photo_url: c.photo_url,
            status: c.status,
            dom: c.dom,
            // Coordinates — needed by the worker to generate Google Static Maps
            // thumbnails for comps that have no photo_url
            lat: c.lat,
            lng: c.lng,
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

  // Idle / Review — Design's Wizards v3: one heading, the choices as rows that
  // jump back to their step, then the one action. Design's "Who's reading
  // it?" (seller / buyer) and "Public page + QR code" switch are not here:
  // both are product decisions, not styling.
  if (generationPhase === "idle") {
    const rows: { label: string; value: string; sub: string; step: number }[] = [
      {
        label: "Home",
        value: property.full_address,
        sub: `${property.bedrooms} bed · ${property.bathrooms} bath · ${property.sqft.toLocaleString()} sqft · Built ${property.year_built}`,
        step: 0,
      },
      {
        label: "Comparables",
        value: `${selectedComps.length} comparable sales`,
        sub: `Avg $${avgPrice.toLocaleString()} · $${Math.round(minPrice / 1000)}K–$${Math.round(maxPrice / 1000)}K`,
        step: 1,
      },
      {
        label: "Look",
        value: `${selectedTheme.name} · ${selectedPageIds.length} pages`,
        sub: `Accent ${accentColor.toUpperCase()}`,
        step: 2,
      },
    ];
    return (
      <div className="flex flex-col gap-6">
        <StepHeader title="Ready to build it?" sub="Check what goes in. Change anything by tapping it." />

        <div className="flex flex-col border-t-[1.5px] border-[#0F172A]">
          {rows.map((r) => (
            <button
              key={r.label}
              type="button"
              onClick={() => goToStep(r.step)}
              className="grid items-start gap-3.5 border-b border-[#ECEAE3] py-3.5 text-left"
              style={{ gridTemplateColumns: "112px minmax(0,1fr) auto" }}
            >
              <span className="pt-0.5 text-xs font-bold uppercase tracking-[0.1em] text-[#64748B]">{r.label}</span>
              <span className="flex min-w-0 flex-col">
                <span className="flex items-center gap-2 text-[15px] font-semibold text-[#0F172A]">
                  {r.step === 2 && (
                    <span className="h-3 w-3 shrink-0 rounded-full border border-[#E4E2DA]" style={{ backgroundColor: accentColor }} />
                  )}
                  <span className="truncate">{r.value}</span>
                </span>
                <span className="text-[13px] text-[#64748B]">{r.sub}</span>
              </span>
              <span className="pt-0.5 text-[13px] font-semibold text-[#4F46E5]">Edit</span>
            </button>
          ))}
        </div>

        <p className="m-0 text-[13px] text-[#64748B]">
          This will create a branded PDF report with QR code and shareable link.
        </p>
        <button
          type="button"
          onClick={startGeneration}
          className="inline-flex h-12 items-center justify-center gap-2 self-end rounded-[10px] bg-[#0F172A] px-[22px] text-[15px] font-semibold text-white"
        >
          Generate Report
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    );
  }

  // Generating
  if (generationPhase === "generating") {
    return (
      <div className="flex flex-col gap-7">
        <StepHeader title="Building the report…" sub="Usually takes 30–60 seconds." />
        <div>
          <div className="h-1.5 overflow-hidden rounded-full bg-[#ECEAE3]">
            <div className="h-full bg-[#0F172A] transition-all" style={{ width: `${generationProgress}%` }} />
          </div>
          <p className="mt-1 text-right text-xs text-[#64748B]">{generationProgress}%</p>
        </div>
        <ol className="m-0 flex list-none flex-col border-t-[1.5px] border-[#0F172A] p-0">
          {dynamicStages.map((stage, i) => {
            const status = i < currentStage ? "done" : i === currentStage ? "active" : "waiting";
            return (
              <li
                key={stage.label}
                className={`flex items-center gap-3.5 border-b border-[#ECEAE3] py-3.5 text-[15px] ${
                  status === "waiting" ? "font-medium text-[#94A3B8]" : status === "active" ? "font-semibold text-[#0F172A]" : "font-medium text-[#0F172A]"
                }`}
              >
                <span
                  className={`flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-full ${
                    status === "done"
                      ? "bg-[#047857]"
                      : status === "active"
                      ? "animate-[spin_1.4s_linear_infinite] border-2 border-dashed border-[#0F172A]"
                      : "border-[1.5px] border-[#CBD5E1]"
                  }`}
                >
                  {status === "done" && <Check className="h-3 w-3 text-white" />}
                </span>
                {stage.label}
              </li>
            );
          })}
        </ol>
      </div>
    );
  }

  // Success
  if (generationPhase === "success") {
    return (
      <div className="flex flex-col gap-7">
        <div className="flex flex-col gap-3">
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 260, damping: 20 }}
            className="flex h-12 w-12 items-center justify-center rounded-full bg-[#D1FAE5]"
          >
            <Check className="h-[22px] w-[22px] text-[#047857]" />
          </motion.span>
          <h2 className="m-0 text-[30px] font-extrabold leading-[1.08] tracking-[-0.03em] text-[#0F172A]">
            Your report is ready.
          </h2>
          <p className="m-0 text-base text-[#475569]">
            {property.street_address}, {property.city}
          </p>
        </div>
        <div className="flex flex-col border-t-[1.5px] border-[#0F172A]">
          <button
            type="button"
            onClick={() => {
              if (reportResult?.pdf_url) {
                window.open(reportResult.pdf_url, "_blank");
              }
            }}
            className="grid items-center gap-3.5 border-b border-[#ECEAE3] py-3.5 text-left text-[#0F172A] hover:text-[#4F46E5]"
            style={{ gridTemplateColumns: "auto minmax(0,1fr) auto" }}
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-[9px] border border-[#ECEAE3] bg-[#FAFAF7]">
              <Download className="h-4 w-4" />
            </span>
            <span className="flex flex-col">
              <span className="text-[15px] font-semibold">Download PDF</span>
              <span className="text-[13px] text-[#64748B]">Opens in a new tab</span>
            </span>
            <ArrowRight className="h-4 w-4 text-[#94A3B8]" />
          </button>
          <button
            type="button"
            onClick={() => {
              window.location.href = "/app/property";
            }}
            className="grid items-center gap-3.5 border-b border-[#ECEAE3] py-3.5 text-left text-[#0F172A] hover:text-[#4F46E5]"
            style={{ gridTemplateColumns: "auto minmax(0,1fr) auto" }}
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-[9px] border border-[#ECEAE3] bg-[#FAFAF7]">
              <ExternalLink className="h-4 w-4" />
            </span>
            <span className="flex flex-col">
              <span className="text-[15px] font-semibold">View all reports</span>
              <span className="text-[13px] text-[#64748B]">Your property reports</span>
            </span>
            <ArrowRight className="h-4 w-4 text-[#94A3B8]" />
          </button>
        </div>
        <button
          type="button"
          onClick={onReset}
          className="inline-flex h-[46px] items-center gap-2 self-start rounded-[9px] border border-[#D6D3CB] px-[18px] text-sm font-semibold text-[#0F172A]"
        >
          <RotateCcw className="h-4 w-4" />
          Create another report
        </button>
      </div>
    );
  }

  // Error
  return (
    <div className="flex flex-col gap-6">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-[#FEE2E2]">
        <X className="h-[22px] w-[22px] text-[#B91C1C]" />
      </span>
      <StepHeader title="Report generation failed" sub={errorMessage || "Something went wrong. Please try again."} />
      <div className="flex gap-2.5">
        <button
          type="button"
          onClick={() => {
            onSetPhase("idle");
            onSetProgress(0);
            onSetStage(0);
            generatingRef.current = false;
          }}
          className="h-[46px] rounded-[9px] border border-[#D6D3CB] px-[18px] text-sm font-semibold text-[#0F172A]"
        >
          Back to review
        </button>
        <button
          type="button"
          onClick={() => {
            generatingRef.current = false;
            startGeneration();
          }}
          className="inline-flex h-[46px] items-center gap-2 rounded-[9px] bg-[#0F172A] px-5 text-sm font-semibold text-white"
        >
          <RotateCcw className="h-4 w-4" />
          Retry
        </button>
      </div>
    </div>
  );
}

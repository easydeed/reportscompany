"use client";

import { Info } from "lucide-react";
import type { ReportBuilderState } from "./types";

interface StepTimeframeProps {
  state: ReportBuilderState;
  onChange: (patch: Partial<ReportBuilderState>) => void;
}

const OPTIONS: { value: 7 | 14 | 30 | 60 | 90; label: string }[] = [
  { value: 7, label: "7 days" },
  { value: 14, label: "14 days" },
  { value: 30, label: "30 days" },
  { value: 60, label: "60 days" },
  { value: 90, label: "90 days" },
];

function getHint(reportType: string | null, days: number | null): string {
  if (
    reportType === "new_listings_gallery" ||
    reportType === "new_listings" ||
    reportType === "open_houses"
  ) {
    return "Shorter periods like 7-14 days work best for this report type.";
  }
  if (reportType === "market_snapshot" || reportType === "closed") {
    return "30 days is recommended for a comprehensive market overview.";
  }
  return "30 days is recommended for most reports. Shorter periods work best for New Listings and Open Houses.";
}

export function StepTimeframe({ state, onChange }: StepTimeframeProps) {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-foreground">
          How far back should we look?
        </h2>
        <p className="mt-1 text-muted-foreground">
          Choose the lookback period for your report data.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        {OPTIONS.map((opt) => {
          const selected = state.lookbackDays === opt.value;
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => onChange({ lookbackDays: opt.value })}
              className={`flex flex-col items-center justify-center rounded-xl border-2 px-6 py-5 transition-all ${
                selected
                  ? "border-[#6366F1] bg-[#6366F1] text-white"
                  : "border-border bg-card text-foreground hover:border-[#C7D2FE]"
              }`}
            >
              <span className="text-2xl font-bold">{opt.value}</span>
              <span
                className={`text-sm ${selected ? "text-white/80" : "text-muted-foreground"}`}
              >
                days
              </span>
            </button>
          );
        })}
      </div>

      <div className="flex items-start gap-2 rounded-lg bg-muted px-4 py-3">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-[#6366F1]" />
        <p className="text-sm leading-relaxed text-muted-foreground">
          {getHint(state.reportType, state.lookbackDays)}
        </p>
      </div>
    </div>
  );
}

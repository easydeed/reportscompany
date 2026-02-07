"use client";

import React from "react"

import { useState } from "react";
import {
  BarChart3,
  Images,
  DollarSign,
  Layers,
  BarChart,
  Calendar,
  Star,
  Table,
  Check,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import type { ReportBuilderState, ReportType, AudienceFilter, ReportTypeInfo } from "./types";
import {
  PRIMARY_REPORT_TYPES,
  SECONDARY_REPORT_TYPES,
  AUDIENCE_PRESETS,
} from "./types";

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  BarChart3,
  Images,
  DollarSign,
  Layers,
  BarChart,
  Calendar,
  Star,
  Table,
};

interface StepReportTypeProps {
  state: ReportBuilderState;
  onChange: (patch: Partial<ReportBuilderState>) => void;
}

function ReportCard({
  info,
  selected,
  onClick,
}: {
  info: ReportTypeInfo;
  selected: boolean;
  onClick: () => void;
}) {
  const Icon = ICON_MAP[info.icon] || BarChart3;

  return (
    <button
      type="button"
      onClick={onClick}
      className={`relative flex flex-col items-start gap-3 rounded-xl border-2 p-5 text-left transition-all ${
        selected
          ? "border-[#6366F1] bg-[#EEF2FF]"
          : "border-border bg-card hover:border-[#C7D2FE]"
      }`}
    >
      {selected && (
        <div className="absolute right-3 top-3 flex h-5 w-5 items-center justify-center rounded-full bg-[#6366F1]">
          <Check className="h-3 w-3 text-white" />
        </div>
      )}
      <Icon
        className={`h-6 w-6 ${selected ? "text-[#6366F1]" : "text-muted-foreground"}`}
      />
      <div className="space-y-1">
        <p className="font-semibold text-foreground">{info.name}</p>
        <p className="text-sm leading-relaxed text-muted-foreground">
          {info.description}
        </p>
      </div>
      <span className="mt-auto inline-flex rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium text-muted-foreground">
        {info.tag}
      </span>
    </button>
  );
}

export function StepReportType({ state, onChange }: StepReportTypeProps) {
  const [showMore, setShowMore] = useState(false);

  function selectReport(id: ReportType) {
    const needsAudience = id === "new_listings_gallery" || id === "new_listings";
    onChange({
      reportType: id,
      audienceFilter: needsAudience ? (state.audienceFilter || "all") : null,
      audienceFilterName: needsAudience
        ? (state.audienceFilterName || "All Listings")
        : null,
    });
  }

  function selectAudience(preset: (typeof AUDIENCE_PRESETS)[number]) {
    onChange({
      audienceFilter: preset.id,
      audienceFilterName: preset.name,
    });
  }

  const showAudience =
    state.reportType === "new_listings_gallery" ||
    state.reportType === "new_listings";

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-foreground">
          What report do you want to create?
        </h2>
        <p className="mt-1 text-muted-foreground">
          Select the type of report that best fits your needs.
        </p>
      </div>

      {/* Primary 2x2 grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {PRIMARY_REPORT_TYPES.map((rt) => (
          <ReportCard
            key={rt.id}
            info={rt}
            selected={state.reportType === rt.id}
            onClick={() => selectReport(rt.id)}
          />
        ))}
      </div>

      {/* Show more */}
      {!showMore && (
        <button
          type="button"
          onClick={() => setShowMore(true)}
          className="flex items-center gap-1.5 text-sm font-medium text-[#6366F1] hover:text-[#4338CA]"
        >
          Show more report types
          <ChevronDown className="h-4 w-4" />
        </button>
      )}
      {showMore && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {SECONDARY_REPORT_TYPES.map((rt) => (
              <ReportCard
                key={rt.id}
                info={rt}
                selected={state.reportType === rt.id}
                onClick={() => selectReport(rt.id)}
              />
            ))}
          </div>
          <button
            type="button"
            onClick={() => setShowMore(false)}
            className="flex items-center gap-1.5 text-sm font-medium text-[#6366F1] hover:text-[#4338CA]"
          >
            Show fewer
            <ChevronUp className="h-4 w-4" />
          </button>
        </>
      )}

      {/* Audience presets */}
      {showAudience && (
        <div className="space-y-3">
          <p className="text-sm font-semibold text-foreground">
            Target Audience
          </p>
          <div className="flex flex-wrap gap-2">
            {AUDIENCE_PRESETS.map((preset) => (
              <button
                key={preset.id}
                type="button"
                onClick={() => selectAudience(preset)}
                className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition-all ${
                  state.audienceFilter === preset.id
                    ? "border-[#6366F1] bg-[#6366F1] text-white"
                    : "border-border bg-card text-foreground hover:bg-muted"
                }`}
              >
                {preset.name}
              </button>
            ))}
          </div>
          {state.audienceFilter && (
            <p className="text-sm text-muted-foreground">
              {AUDIENCE_PRESETS.find((p) => p.id === state.audienceFilter)
                ?.description}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Check,
  Loader2,
  Sparkles,
  ExternalLink,
  Download,
  RotateCcw,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import type { ReportBuilderState } from "./types";
import { getReportTypeInfo } from "./types";

interface StepReviewProps {
  state: ReportBuilderState;
  onChange: (patch: Partial<ReportBuilderState>) => void;
  onReset: () => void;
}

type GenPhase = "idle" | "generating" | "done";

export function StepReview({ state, onChange, onReset }: StepReviewProps) {
  const [phase, setPhase] = useState<GenPhase>("idle");
  const [progress, setProgress] = useState(0);
  const [emailInput, setEmailInput] = useState("");

  const reportInfo = state.reportType
    ? getReportTypeInfo(state.reportType)
    : null;
  const areaLabel =
    state.areaType === "city"
      ? state.city
      : state.zipCodes.join(", ");

  const simulate = useCallback(() => {
    setPhase("generating");
    setProgress(0);
    let p = 0;
    const iv = setInterval(() => {
      p += Math.random() * 15 + 5;
      if (p >= 100) {
        p = 100;
        clearInterval(iv);
        setTimeout(() => setPhase("done"), 400);
      }
      setProgress(Math.min(p, 100));
    }, 300);
  }, []);

  function addEmail() {
    const trimmed = emailInput.trim();
    if (
      trimmed &&
      trimmed.includes("@") &&
      !state.recipientEmails.includes(trimmed)
    ) {
      onChange({ recipientEmails: [...state.recipientEmails, trimmed] });
      setEmailInput("");
    }
  }

  function removeEmail(email: string) {
    onChange({
      recipientEmails: state.recipientEmails.filter((e) => e !== email),
    });
  }

  // Done state
  if (phase === "done") {
    return (
      <div className="flex flex-col items-center justify-center gap-6 py-12 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[#EEF2FF]">
          <Check className="h-8 w-8 text-[#6366F1]" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-foreground">
            Report Ready!
          </h2>
          <p className="mt-1 text-muted-foreground">
            Your {reportInfo?.name} for {areaLabel} has been generated.
          </p>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-3">
          {state.viewInBrowser && (
            <Button className="bg-[#6366F1] text-white hover:bg-[#4338CA]">
              <ExternalLink className="mr-2 h-4 w-4" />
              Open Report
            </Button>
          )}
          {state.downloadPdf && (
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Download PDF
            </Button>
          )}
        </div>
        <button
          type="button"
          onClick={onReset}
          className="mt-2 flex items-center gap-1.5 text-sm font-medium text-[#6366F1] hover:text-[#4338CA]"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          Create Another Report
        </button>
      </div>
    );
  }

  // Generating state
  if (phase === "generating") {
    return (
      <div className="flex flex-col items-center justify-center gap-6 py-12 text-center">
        <Loader2 className="h-10 w-10 animate-spin text-[#6366F1]" />
        <div>
          <h2 className="text-xl font-bold text-foreground">
            Generating Report...
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            This usually takes 10-30 seconds
          </p>
        </div>
        <div className="w-full max-w-xs">
          <Progress value={progress} className="h-2" />
          <p className="mt-2 text-xs text-muted-foreground">
            {progress < 30
              ? "Fetching MLS data..."
              : progress < 70
                ? "Processing..."
                : "Finalizing report..."}
          </p>
        </div>
      </div>
    );
  }

  // Idle / form state
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-foreground">
          Review & Generate
        </h2>
        <p className="mt-1 text-muted-foreground">
          Confirm your selections and choose delivery options.
        </p>
      </div>

      {/* Summary card */}
      <div className="flex items-center gap-4 rounded-xl border border-border bg-muted/50 p-5">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-[#EEF2FF]">
          <Sparkles className="h-5 w-5 text-[#6366F1]" />
        </div>
        <div>
          <p className="font-semibold text-foreground">
            {reportInfo?.name || "Report"}
          </p>
          <p className="text-sm text-muted-foreground">
            {areaLabel} &middot; Last {state.lookbackDays} days
            {state.audienceFilterName && state.audienceFilterName !== "All Listings"
              ? ` \u00b7 ${state.audienceFilterName}`
              : ""}
          </p>
        </div>
      </div>

      {/* Delivery options */}
      <div className="space-y-4">
        <p className="text-sm font-semibold text-foreground">
          Delivery Options
        </p>
        <div className="space-y-3">
          {[
            {
              key: "viewInBrowser" as const,
              label: "View in Browser",
            },
            {
              key: "downloadPdf" as const,
              label: "Download PDF",
            },
            {
              key: "downloadSocialImage" as const,
              label: "Download Social Image (1080\u00d71920)",
            },
            {
              key: "sendViaEmail" as const,
              label: "Send via Email",
            },
          ].map((opt) => (
            <label
              key={opt.key}
              className="flex items-center gap-3 cursor-pointer"
            >
              <Checkbox
                checked={state[opt.key]}
                onCheckedChange={(v) => onChange({ [opt.key]: !!v })}
              />
              <span className="text-sm text-foreground">{opt.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Recipient emails */}
      {state.sendViaEmail && (
        <div className="space-y-3">
          <p className="text-sm font-semibold text-foreground">Recipients</p>
          <div className="flex items-center gap-2">
            <Input
              placeholder="Search contacts or enter email..."
              value={emailInput}
              onChange={(e) => setEmailInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addEmail();
                }
              }}
            />
          </div>
          {state.recipientEmails.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {state.recipientEmails.map((email) => (
                <span
                  key={email}
                  className="inline-flex items-center gap-1.5 rounded-full bg-[#EEF2FF] px-3 py-1 text-sm font-medium text-[#4338CA]"
                >
                  {email}
                  <button
                    type="button"
                    onClick={() => removeEmail(email)}
                    className="rounded-full p-0.5 hover:bg-[#C7D2FE]"
                    aria-label={`Remove ${email}`}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Generate button */}
      <Button
        onClick={simulate}
        size="lg"
        className="w-full bg-[#6366F1] py-6 text-base font-semibold text-white hover:bg-[#4338CA]"
      >
        <Sparkles className="mr-2 h-5 w-5" />
        Generate Report
      </Button>
    </div>
  );
}

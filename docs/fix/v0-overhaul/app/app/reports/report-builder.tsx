"use client";

import React from "react"

import { useState, useCallback, useMemo } from "react";
import {
  Check,
  MapPin,
  BarChart3,
  CalendarDays,
  Send,
  ChevronLeft,
  ChevronRight,
  Clock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { AnimatePresence, motion } from "framer-motion";
import type { ReportBuilderState } from "./types";
import { INITIAL_STATE, getReportTypeInfo } from "./types";
import { StepArea } from "./step-area";
import { StepReportType } from "./step-report-type";
import { StepTimeframe } from "./step-timeframe";
import { StepReview } from "./step-review";

const STEPS = [
  { label: "Area", icon: MapPin },
  { label: "Report Type", icon: BarChart3 },
  { label: "Timeframe", icon: CalendarDays },
  { label: "Review & Generate", icon: Send },
] as const;

export function ReportBuilder() {
  const [step, setStep] = useState(0);
  const [state, setState] = useState<ReportBuilderState>(INITIAL_STATE);
  const [direction, setDirection] = useState(1); // 1 = forward, -1 = back

  const update = useCallback((patch: Partial<ReportBuilderState>) => {
    setState((prev) => ({ ...prev, ...patch }));
  }, []);

  const canContinue = useMemo(() => {
    switch (step) {
      case 0:
        return state.areaType === "city"
          ? !!state.city
          : state.zipCodes.length > 0;
      case 1:
        return !!state.reportType;
      case 2:
        return !!state.lookbackDays;
      case 3:
        return true;
      default:
        return false;
    }
  }, [step, state]);

  const maxCompleted = useMemo(() => {
    let max = -1;
    if (
      state.areaType === "city" ? !!state.city : state.zipCodes.length > 0
    )
      max = 0;
    if (max >= 0 && state.reportType) max = 1;
    if (max >= 1 && state.lookbackDays) max = 2;
    return max;
  }, [state]);

  function goTo(target: number) {
    if (target === step) return;
    setDirection(target > step ? 1 : -1);
    setStep(target);
  }

  function next() {
    if (step < 3 && canContinue) goTo(step + 1);
  }
  function back() {
    if (step > 0) goTo(step - 1);
  }

  function reset() {
    setState(INITIAL_STATE);
    setDirection(-1);
    setStep(0);
  }

  // Sidebar data
  const reportInfo = state.reportType
    ? getReportTypeInfo(state.reportType)
    : null;
  const areaLabel =
    state.areaType === "city"
      ? state.city
      : state.zipCodes.length > 0
        ? state.zipCodes.join(", ")
        : null;

  const slideVariants = {
    enter: (d: number) => ({
      x: d > 0 ? 60 : -60,
      opacity: 0,
    }),
    center: { x: 0, opacity: 1 },
    exit: (d: number) => ({
      x: d > 0 ? -60 : 60,
      opacity: 0,
    }),
  };

  return (
    <div className="mx-auto max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-foreground">Create Report</h1>
        <span className="text-sm text-muted-foreground">
          Step {step + 1} of {STEPS.length}
        </span>
      </div>

      {/* Step indicator */}
      <div className="mt-8 hidden md:block">
        <div className="flex items-center">
          {STEPS.map((s, i) => {
            const completed = i <= maxCompleted && i < step;
            const active = i === step;
            const clickable = i <= maxCompleted + 1 && i <= step;

            return (
              <div key={s.label} className="flex flex-1 items-center">
                <button
                  type="button"
                  disabled={!clickable}
                  onClick={() => clickable && goTo(i)}
                  className={`flex items-center gap-2 ${clickable ? "cursor-pointer" : "cursor-default"}`}
                >
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold transition-colors ${
                      active
                        ? "bg-[#6366F1] text-white"
                        : completed
                          ? "bg-[#6366F1] text-white"
                          : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {completed ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      i + 1
                    )}
                  </div>
                  <span
                    className={`text-sm font-medium ${
                      active
                        ? "text-foreground"
                        : completed
                          ? "text-foreground"
                          : "text-muted-foreground"
                    }`}
                  >
                    {s.label}
                  </span>
                </button>
                {i < STEPS.length - 1 && (
                  <div
                    className={`mx-4 h-px flex-1 ${
                      i <= maxCompleted && i < step
                        ? "bg-[#6366F1]"
                        : "bg-border"
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Mobile step pills */}
      <div className="mt-6 flex gap-1.5 md:hidden">
        {STEPS.map((_, i) => (
          <div
            key={i}
            className={`h-1.5 flex-1 rounded-full ${
              i <= step ? "bg-[#6366F1]" : "bg-border"
            }`}
          />
        ))}
      </div>

      {/* Main content + sidebar */}
      <div className="mt-8 flex gap-8">
        {/* Content area */}
        <div className="min-w-0 flex-1">
          <div className="rounded-2xl border border-border bg-card p-6 md:p-8">
            <AnimatePresence mode="wait" custom={direction}>
              <motion.div
                key={step}
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.25, ease: "easeInOut" }}
              >
                {step === 0 && (
                  <StepArea state={state} onChange={update} />
                )}
                {step === 1 && (
                  <StepReportType state={state} onChange={update} />
                )}
                {step === 2 && (
                  <StepTimeframe state={state} onChange={update} />
                )}
                {step === 3 && (
                  <StepReview
                    state={state}
                    onChange={update}
                    onReset={reset}
                  />
                )}
              </motion.div>
            </AnimatePresence>

            {/* Navigation buttons */}
            {step < 3 && (
              <div className="mt-8 flex items-center justify-between border-t border-border pt-6">
                <Button
                  variant="ghost"
                  onClick={back}
                  disabled={step === 0}
                  className="gap-1.5"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Back
                </Button>
                <Button
                  onClick={next}
                  disabled={!canContinue}
                  className="gap-1.5 bg-[#6366F1] text-white hover:bg-[#4338CA]"
                >
                  Continue
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <aside className="hidden w-72 shrink-0 lg:block">
          <div className="sticky top-24 rounded-2xl border border-border bg-card p-6">
            <h3 className="text-sm font-semibold text-foreground">
              Report Summary
            </h3>

            <div className="mt-6 space-y-5">
              {/* Area */}
              <SidebarItem
                label="Area"
                value={areaLabel}
                completed={!!areaLabel}
                onClick={areaLabel ? () => goTo(0) : undefined}
                icon={<MapPin className="h-4 w-4" />}
              />

              {/* Report type */}
              <SidebarItem
                label="Report Type"
                value={reportInfo?.name ?? null}
                completed={!!reportInfo}
                onClick={reportInfo ? () => goTo(1) : undefined}
                icon={<BarChart3 className="h-4 w-4" />}
              />

              {/* Timeframe */}
              <SidebarItem
                label="Timeframe"
                value={
                  state.lookbackDays
                    ? `Last ${state.lookbackDays} days`
                    : null
                }
                completed={!!state.lookbackDays}
                onClick={
                  state.lookbackDays ? () => goTo(2) : undefined
                }
                icon={<CalendarDays className="h-4 w-4" />}
              />

              {/* Delivery */}
              <SidebarItem
                label="Delivery"
                value={
                  step >= 3
                    ? [
                        state.viewInBrowser && "Browser",
                        state.downloadPdf && "PDF",
                        state.downloadSocialImage && "Social",
                        state.sendViaEmail && "Email",
                      ]
                        .filter(Boolean)
                        .join(", ") || null
                    : null
                }
                completed={step >= 3}
                icon={<Send className="h-4 w-4" />}
              />
            </div>

            <div className="mt-6 border-t border-border pt-4">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Clock className="h-3.5 w-3.5" />
                <span className="text-xs">Est. processing: ~15 seconds</span>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

function SidebarItem({
  label,
  value,
  completed,
  onClick,
  icon,
}: {
  label: string;
  value: string | null;
  completed: boolean;
  onClick?: () => void;
  icon: React.ReactNode;
}) {
  const Wrapper = onClick ? "button" : "div";
  return (
    <Wrapper
      {...(onClick ? { type: "button" as const, onClick } : {})}
      className={`flex items-start gap-3 text-left ${onClick ? "cursor-pointer rounded-lg transition-colors hover:bg-muted -mx-2 px-2 py-1" : ""}`}
    >
      <div
        className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full ${
          completed
            ? "bg-[#6366F1] text-white"
            : "bg-muted text-muted-foreground"
        }`}
      >
        {completed ? <Check className="h-3 w-3" /> : icon}
      </div>
      <div>
        <p
          className={`text-xs font-medium ${completed ? "text-foreground" : "text-muted-foreground"}`}
        >
          {label}
        </p>
        {value ? (
          <p className="text-sm font-medium text-foreground">{value}</p>
        ) : (
          <p className="text-xs text-muted-foreground/60">Not selected</p>
        )}
      </div>
    </Wrapper>
  );
}

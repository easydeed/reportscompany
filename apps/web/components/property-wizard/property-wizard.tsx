"use client";

import React from "react";
import { useState, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Home,
  BarChart3,
  Palette,
  Sparkles,
  Check,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { StepProperty } from "./step-property";
import { StepComparables } from "./step-comparables";
import { StepTheme } from "./step-theme";
import { StepGenerate } from "./step-generate";
import type { PropertyData, Comparable } from "./types";
import { THEMES, COMPACT_PAGES, FULL_PAGES } from "./types";

const STEP_ICONS = [Home, BarChart3, Palette, Sparkles];
const STEP_LABELS = ["Property", "Comparables", "Theme & Pages", "Generate"];

const slideVariants = {
  enter: (d: number) => ({ x: d > 0 ? 60 : -60, opacity: 0 }),
  center: { x: 0, opacity: 1 },
  exit: (d: number) => ({ x: d > 0 ? -60 : 60, opacity: 0 }),
};

export function PropertyWizard() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [direction, setDirection] = useState(1);

  // Step 1
  const [streetAddress, setStreetAddress] = useState("");
  const [cityStateZip, setCityStateZip] = useState("");
  const [property, setProperty] = useState<PropertyData | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Step 2
  const [availableComps, setAvailableComps] = useState<Comparable[]>([]);
  const [selectedCompIds, setSelectedCompIds] = useState<string[]>([]);
  const [compsLoading, setCompsLoading] = useState(false);
  const [compsLoaded, setCompsLoaded] = useState(false);
  const [compsError, setCompsError] = useState<string | null>(null);
  const [compsStatus, setCompsStatus] = useState<"Active" | "Closed">("Active");

  // Step 3
  const [selectedThemeId, setSelectedThemeId] = useState(4);
  const [accentColor, setAccentColor] = useState("#34d1c3");
  const [selectedPageIds, setSelectedPageIds] = useState<string[]>(
    COMPACT_PAGES.map((p) => p.id)
  );

  // Step 4
  const [generationPhase, setGenerationPhase] = useState<
    "idle" | "generating" | "success" | "error"
  >("idle");
  const [generationProgress, setGenerationProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState(0);

  const selectedTheme = useMemo(
    () => THEMES.find((t) => t.id === selectedThemeId) || THEMES[3],
    [selectedThemeId]
  );

  const pages = useMemo(
    () => (selectedTheme.compact ? COMPACT_PAGES : FULL_PAGES),
    [selectedTheme]
  );

  const selectedComps = useMemo(
    () => availableComps.filter((c) => selectedCompIds.includes(c.id)),
    [availableComps, selectedCompIds]
  );

  const canProceed = useCallback(
    (s: number) => {
      switch (s) {
        case 0:
          return !!property;
        case 1:
          return selectedCompIds.length >= 4 && selectedCompIds.length <= 8;
        case 2:
          return selectedThemeId >= 1 && selectedThemeId <= 5;
        case 3:
          return true;
        default:
          return false;
      }
    },
    [property, selectedCompIds.length, selectedThemeId]
  );

  // Fetch real comparables from API
  const loadComparables = useCallback(async (status: "Active" | "Closed" = "Active") => {
    if (!property) return;
    setCompsLoading(true);
    setCompsError(null);
    setSelectedCompIds([]);

    try {
      // Build city_state_zip for the backend to parse into SimplyRETS location filters
      const cityStateZipStr = [property.city, property.state, property.zip_code]
        .filter(Boolean)
        .join(", ");

      const res = await fetch("/api/proxy/v1/property/comparables", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          address: property.full_address,
          city_state_zip: cityStateZipStr,
          latitude: property.latitude,
          longitude: property.longitude,
          beds: property.bedrooms,
          baths: property.bathrooms,
          sqft: property.sqft,
          property_type: property.property_type || undefined,
          radius_miles: 1.0,
          status,
        }),
      });

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.detail || "Failed to fetch comparables");
      }

      const data = await res.json();

      // Backend returns { success, comparables, total_found, subject_property, search_params, error }
      if (!data.success) {
        throw new Error(data.error || "Failed to fetch comparables");
      }

      // Map backend comparable fields to our Comparable interface
      const isActive = status === "Active";
      const comps: Comparable[] = (data.comparables || []).map(
        (c: any, i: number) => {
          const price = isActive
            ? (c.list_price || c.price || c.close_price || 0)
            : (c.close_price || c.price || c.list_price || 0);
          const compSqft = c.sqft || c.square_feet || 0;
          return {
            id: c.mls_id || c.id || `comp-${i}`,
            address: c.address || "",
            city: c.city || "",
            state: c.state || "",
            zip: c.zip_code || c.zip || "",
            sale_price: price,
            sold_date: c.close_date || c.sold_date || "",
            list_price: c.list_price || c.price || 0,
            list_date: c.list_date || "",
            sqft: compSqft,
            bedrooms: c.bedrooms || 0,
            bathrooms: c.bathrooms || 0,
            year_built: c.year_built || 0,
            distance_miles: c.distance_miles ?? 0,
            price_per_sqft:
              c.price_per_sqft ||
              (price && compSqft ? Math.round(price / compSqft) : 0),
            status: c.status || status,
            dom: c.dom || c.days_on_market || 0,
            photo_url: c.photo_url || (c.photos && c.photos[0]) || null,
            lat: c.lat || c.latitude,
            lng: c.lng || c.longitude,
          };
        }
      );

      setAvailableComps(comps);
      setCompsLoaded(true);
    } catch (err: any) {
      console.error("Failed to load comparables:", err);
      setCompsError(err.message || "Failed to load comparables");
    } finally {
      setCompsLoading(false);
    }
  }, [property]);

  function goToStep(s: number) {
    setDirection(s > step ? 1 : -1);
    setStep(s);
  }

  function next() {
    if (!canProceed(step)) return;
    // When leaving step 1, load real comps
    if (step === 0 && !compsLoaded) {
      loadComparables(compsStatus);
    }
    setDirection(1);
    setStep((s) => Math.min(s + 1, 3));
  }

  function handleCompsStatusChange(newStatus: "Active" | "Closed") {
    setCompsStatus(newStatus);
    loadComparables(newStatus);
  }

  function back() {
    setDirection(-1);
    setStep((s) => Math.max(s - 1, 0));
  }

  function handleThemeChange(id: number) {
    setSelectedThemeId(id);
    const theme = THEMES.find((t) => t.id === id);
    if (theme) {
      setAccentColor(theme.accentDefault);
      const newPages = theme.compact ? COMPACT_PAGES : FULL_PAGES;
      setSelectedPageIds(newPages.map((p) => p.id));
    }
  }

  function handleReset() {
    setStep(0);
    setDirection(-1);
    setStreetAddress("");
    setCityStateZip("");
    setProperty(null);
    setSearchLoading(false);
    setSearchError(null);
    setAvailableComps([]);
    setSelectedCompIds([]);
    setCompsLoading(false);
    setCompsLoaded(false);
    setCompsError(null);
    setCompsStatus("Active");
    setSelectedThemeId(4);
    setAccentColor("#34d1c3");
    setSelectedPageIds(COMPACT_PAGES.map((p) => p.id));
    setGenerationPhase("idle");
    setGenerationProgress(0);
    setCurrentStage(0);
  }

  function handleClear() {
    setProperty(null);
    setStreetAddress("");
    setCityStateZip("");
    setSearchError(null);
    // Reset comps since they depend on the property
    setAvailableComps([]);
    setSelectedCompIds([]);
    setCompsLoaded(false);
    setCompsError(null);
    setCompsStatus("Active");
  }

  const stepsCompleted = [
    !!property,
    selectedCompIds.length >= 4 && selectedCompIds.length <= 8,
    selectedThemeId >= 1,
    generationPhase === "success",
  ];

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Sticky Header */}
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/app/property"
              className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
              <span className="hidden sm:inline">Property Reports</span>
            </Link>
            <div className="h-4 w-px bg-border" />
            <h1 className="text-sm font-semibold text-foreground">
              New Property Report
            </h1>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push("/app/property")}
            >
              Cancel
            </Button>
            {step === 3 && generationPhase === "idle" && (
              <Button
                size="sm"
                className="bg-[#6366F1] text-white hover:bg-[#4F46E5]"
                onClick={() => setGenerationPhase("generating")}
              >
                <Sparkles className="h-4 w-4 mr-1.5" />
                <span className="hidden sm:inline">Generate Report</span>
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Step Indicator */}
      <div className="border-b border-border bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          {/* Desktop stepper */}
          <div className="hidden sm:flex items-center justify-center">
            {STEP_LABELS.map((label, i) => {
              const Icon = STEP_ICONS[i];
              const isActive = step === i;
              const isComplete = i < step || stepsCompleted[i];
              const isClickable = i <= step;

              return (
                <div key={label} className="flex items-center">
                  {i > 0 && (
                    <div
                      className={`w-12 lg:w-20 h-0.5 mx-1 rounded-full transition-colors ${
                        i <= step ? "bg-[#6366F1]" : "bg-border"
                      }`}
                    />
                  )}
                  <button
                    type="button"
                    onClick={() => {
                      if (isClickable) goToStep(i);
                    }}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-full transition-all ${
                      isActive
                        ? "bg-[#6366F1] text-white shadow-md"
                        : isComplete && i < step
                        ? "bg-[#6366F1] text-white"
                        : "bg-muted text-muted-foreground"
                    } ${isClickable ? "cursor-pointer" : "cursor-default"}`}
                  >
                    <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold">
                      {isComplete && i < step ? (
                        <Check className="h-3.5 w-3.5" />
                      ) : (
                        <Icon className="h-3.5 w-3.5" />
                      )}
                    </div>
                    <span className="text-xs font-medium hidden lg:inline">
                      {label}
                    </span>
                  </button>
                </div>
              );
            })}
          </div>

          {/* Mobile progress dots */}
          <div className="flex sm:hidden items-center justify-center gap-2">
            {STEP_LABELS.map((label, i) => (
              <div
                key={label}
                className={`h-2 rounded-full transition-all ${
                  step === i
                    ? "w-8 bg-[#6366F1]"
                    : i < step
                    ? "w-2 bg-[#6366F1]"
                    : "w-2 bg-border"
                }`}
              />
            ))}
          </div>
          <p className="sm:hidden text-center text-xs font-medium text-muted-foreground mt-2">
            Step {step + 1}: {STEP_LABELS[step]}
          </p>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 max-w-7xl mx-auto w-full flex">
        {/* Step Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-4 sm:px-6 py-6">
            <AnimatePresence mode="wait" custom={direction}>
              <motion.div
                key={step}
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3, ease: "easeInOut" }}
              >
                {step === 0 && (
                  <StepProperty
                    property={property}
                    streetAddress={streetAddress}
                    cityStateZip={cityStateZip}
                    searchLoading={searchLoading}
                    searchError={searchError}
                    onStreetAddressChange={setStreetAddress}
                    onCityStateZipChange={setCityStateZip}
                    onSearchLoading={setSearchLoading}
                    onPropertyFound={setProperty}
                    onSearchError={setSearchError}
                    onClear={handleClear}
                  />
                )}

                {step === 1 && property && (
                  <StepComparables
                    comps={availableComps}
                    selectedCompIds={selectedCompIds}
                    compsLoading={compsLoading}
                    compsLoaded={compsLoaded}
                    compsError={compsError}
                    property={property}
                    onSelectedChange={setSelectedCompIds}
                    compsStatus={compsStatus}
                    onStatusChange={handleCompsStatusChange}
                    onReload={() => loadComparables(compsStatus)}
                  />
                )}

                {step === 2 && (
                  <StepTheme
                    selectedThemeId={selectedThemeId}
                    accentColor={accentColor}
                    selectedPageIds={selectedPageIds}
                    pages={pages}
                    onThemeChange={handleThemeChange}
                    onAccentChange={setAccentColor}
                    onPagesChange={setSelectedPageIds}
                    propertyData={property}
                    comparables={selectedComps}
                  />
                )}

                {step === 3 && property && (
                  <StepGenerate
                    property={property}
                    selectedComps={selectedComps}
                    selectedTheme={selectedTheme}
                    accentColor={accentColor}
                    selectedPageIds={selectedPageIds}
                    generationPhase={generationPhase}
                    onGenerate={() => setGenerationPhase("generating")}
                    onReset={handleReset}
                    goToStep={goToStep}
                    generationProgress={generationProgress}
                    currentStage={currentStage}
                    onSetPhase={setGenerationPhase}
                    onSetProgress={setGenerationProgress}
                    onSetStage={setCurrentStage}
                  />
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>

        {/* Live Preview Sidebar - Desktop */}
        <aside className="hidden lg:block w-72 xl:w-80 border-l border-border">
          <div className="sticky top-[57px] p-5">
            <div className="rounded-2xl border border-border bg-card p-5">
              <h3 className="text-sm font-semibold text-foreground">
                Report Preview
              </h3>

              {/* Mini cover */}
              <div
                className="mt-4 aspect-[8.5/11] rounded-xl overflow-hidden shadow-lg"
                style={{
                  background:
                    selectedTheme?.gradient ||
                    "linear-gradient(135deg, #18235c, #34d1c3)",
                }}
              >
                <div className="h-full flex flex-col justify-between p-4">
                  <div>
                    <p className="text-[8px] uppercase tracking-[0.2em] text-white/60">
                      Property Report
                    </p>
                    <p
                      className="text-[11px] font-bold text-white leading-tight mt-1"
                      style={{ fontFamily: selectedTheme?.displayFont }}
                    >
                      {property?.street_address || "Your Property"}
                    </p>
                    <p className="text-[8px] text-white/70 mt-0.5">
                      {property
                        ? `${property.city}, ${property.state} ${property.zip_code}`
                        : "City, ST"}
                    </p>
                  </div>

                  {property && (
                    <div className="flex gap-1.5 justify-center">
                      {[
                        { value: property.bedrooms, label: "Beds" },
                        { value: property.bathrooms, label: "Baths" },
                        {
                          value: property.sqft?.toLocaleString(),
                          label: "Sqft",
                        },
                      ].map((s) => (
                        <div
                          key={s.label}
                          className="bg-white/15 backdrop-blur rounded px-1.5 py-1 text-center"
                        >
                          <p className="text-[9px] font-bold text-white">
                            {s.value}
                          </p>
                          <p className="text-[6px] text-white/60">{s.label}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  <div>
                    <div
                      className="h-0.5 rounded-full"
                      style={{ backgroundColor: accentColor }}
                    />
                    <div className="mt-1.5 flex items-center gap-1.5">
                      <div className="w-4 h-4 rounded-full bg-white/20" />
                      <div>
                        <p className="text-[7px] font-medium text-white">
                          Your Name
                        </p>
                        <p className="text-[5px] text-white/50">
                          Your Brokerage
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Summary details */}
              <div className="mt-5 space-y-3">
                <SidebarItem
                  icon={<Home className="h-4 w-4" />}
                  label="Property"
                  value={property?.full_address || null}
                  completed={!!property}
                  onClick={property ? () => goToStep(0) : undefined}
                />
                <SidebarItem
                  icon={<BarChart3 className="h-4 w-4" />}
                  label="Comparables"
                  value={
                    selectedCompIds.length > 0
                      ? `${selectedCompIds.length} selected`
                      : null
                  }
                  completed={
                    selectedCompIds.length >= 4 && selectedCompIds.length <= 8
                  }
                  onClick={
                    selectedCompIds.length > 0 ? () => goToStep(1) : undefined
                  }
                />
                <SidebarItem
                  icon={<Palette className="h-4 w-4" />}
                  label="Theme"
                  value={
                    selectedTheme
                      ? `${selectedTheme.name} · ${selectedPageIds.length} pages`
                      : null
                  }
                  completed={!!selectedTheme}
                  onClick={selectedTheme ? () => goToStep(2) : undefined}
                />
              </div>

              {/* Page count */}
              <div className="mt-4 pt-3 border-t border-border">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <FileText className="h-3.5 w-3.5" />
                  <span>{selectedPageIds.length} pages in report</span>
                </div>
              </div>
            </div>
          </div>
        </aside>
      </div>

      {/* Footer Navigation */}
      {generationPhase !== "generating" && generationPhase !== "success" && (
        <div className="sticky bottom-0 border-t border-border bg-background/80 backdrop-blur-md px-4 sm:px-6 py-4 z-40">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <Button
              variant="ghost"
              onClick={back}
              disabled={step === 0}
              className="gap-1.5"
            >
              <ChevronLeft className="h-4 w-4" />
              Back
            </Button>
            {step < 3 && (
              <Button
                onClick={next}
                disabled={!canProceed(step)}
                className="bg-[#6366F1] text-white hover:bg-[#4F46E5] gap-1.5"
              >
                Continue
                <ChevronRight className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/* Sidebar Item */
function SidebarItem({
  icon,
  label,
  value,
  completed,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | null;
  completed: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      className={`flex items-start gap-3 w-full text-left rounded-lg p-2 -m-2 transition-colors ${
        onClick ? "hover:bg-muted cursor-pointer" : "cursor-default"
      }`}
      onClick={onClick}
    >
      <div
        className={`mt-0.5 ${
          completed ? "text-[#6366F1]" : "text-muted-foreground"
        }`}
      >
        {completed ? (
          <div className="w-4 h-4 rounded-full bg-[#6366F1] flex items-center justify-center">
            <Check className="h-2.5 w-2.5 text-white" />
          </div>
        ) : (
          icon
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-foreground">{label}</p>
        {value ? (
          <p className="text-[11px] text-muted-foreground truncate">{value}</p>
        ) : (
          <p className="text-[11px] text-muted-foreground italic">Not set</p>
        )}
      </div>
    </button>
  );
}

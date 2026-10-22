"use client";

import React from "react";
import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, ArrowRight, Check } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { StepProperty } from "./step-property";
import { StepComparables } from "./step-comparables";
import { StepTheme } from "./step-theme";
import { StepGenerate } from "./step-generate";
import { DEFAULT_THEME_ID, THEME_ID_TO_NAME } from "@/lib/themes.generated";
import type { PropertyData, Comparable } from "./types";
import { THEMES, COMPACT_PAGES, FULL_PAGES } from "./types";

/** Design's labels for the rail (Wizards v3). The step indices are unchanged. */
const STEP_LABELS = ["Address", "Comparables", "Look", "Generate"];

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
  // Search filter controls exposed to the agent in Step 2
  const [sqftTolerance, setSqftTolerance] = useState(0.20); // 0 = any
  const [radiusMiles, setRadiusMiles] = useState(1.0);
  const [fallbackLevel, setFallbackLevel] = useState<string | null>(null);

  // Step 3 — defaults overridden by account branding if available
  const [selectedThemeId, setSelectedThemeId] = useState(4);
  const [accentColor, setAccentColor] = useState("#34d1c3");
  const [selectedPageIds, setSelectedPageIds] = useState<string[]>(
    COMPACT_PAGES.map((p) => p.id)
  );

  // Cache account defaults so handleReset can reuse them without an extra API call
  const accountDefaultsRef = useRef({ themeId: 4, accentColor: "#34d1c3" });

  // Load account-level defaults (default theme + accent color sync)
  useEffect(() => {
    async function loadAccountDefaults() {
      try {
        const res = await fetch("/api/proxy/v1/account", { cache: "no-store" });
        if (!res.ok) return;
        const data = await res.json();
        // Was `themeId = 4` with a 1..5 range check, which accepted the two
        // ids the cut retired and would have asked the renderer for a
        // template that no longer exists.
        let themeId: number = DEFAULT_THEME_ID;
        let accent = "#34d1c3";
        if (data.default_theme_id && THEME_ID_TO_NAME[data.default_theme_id]) {
          themeId = data.default_theme_id;
          const theme = THEMES.find((t) => t.id === themeId);
          if (theme) accent = theme.accentDefault;
        }
        if (data.secondary_color) {
          accent = data.secondary_color;
        }
        setSelectedThemeId(themeId);
        setAccentColor(accent);
        accountDefaultsRef.current = { themeId, accentColor: accent };
      } catch { /* use defaults */ }
    }
    loadAccountDefaults();
  }, []);

  // Step 4
  const [generationPhase, setGenerationPhase] = useState<
    "idle" | "generating" | "success" | "error"
  >("idle");
  const [generationProgress, setGenerationProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState(0);

  const selectedTheme = useMemo(
    () => THEMES.find((t) => t.id === selectedThemeId) ||
          THEMES.find((t) => t.id === DEFAULT_THEME_ID)!,
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
          return !!THEME_ID_TO_NAME[selectedThemeId];
        case 3:
          return true;
        default:
          return false;
      }
    },
    [property, selectedCompIds.length, selectedThemeId]
  );

  // Fetch real comparables from API.
  // sqftVar / radiusVal can be passed explicitly (e.g. when filter controls change)
  // so we don't rely on stale closure values.
  const loadComparables = useCallback(async (
    status: "Active" | "Closed" = "Active",
    sqftVar: number = sqftTolerance,
    radiusVal: number = radiusMiles,
  ) => {
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
          sqft_variance: sqftVar,
          radius_miles: radiusVal,
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
      setFallbackLevel(data.comp_ladder_level || null);
      setCompsLoaded(true);
    } catch (err: any) {
      console.error("Failed to load comparables:", err);
      setCompsError(err.message || "Failed to load comparables");
    } finally {
      setCompsLoading(false);
    }
  }, [property, sqftTolerance, radiusMiles]);

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
    loadComparables(newStatus, sqftTolerance, radiusMiles);
  }

  function handleFiltersChange(newSqft: number, newRadius: number) {
    setSqftTolerance(newSqft);
    setRadiusMiles(newRadius);
    // Pass new values explicitly — don't rely on state update propagating first
    loadComparables(compsStatus, newSqft, newRadius);
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
    setSqftTolerance(0.20);
    setRadiusMiles(1.0);
    setFallbackLevel(null);
    setSelectedThemeId(accountDefaultsRef.current.themeId);
    setAccentColor(accountDefaultsRef.current.accentColor);
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
    setSqftTolerance(0.20);
    setRadiusMiles(1.0);
    setFallbackLevel(null);
  }

  return (
    <div className="flex min-h-screen flex-col bg-white text-[#0F172A]">
      {/* Header — back link, the step rail, exit. Design's Wizards v3. */}
      <header className="sticky top-0 z-50 flex h-[62px] items-center justify-between gap-6 border-b border-[#ECEAE3] bg-white px-4 md:px-7">
        <h1 className="sr-only">New Property Report</h1>
        <Link
          href="/app/property"
          className="flex items-center gap-2 text-sm font-semibold text-[#334155] hover:text-[#0F172A]"
        >
          <ArrowLeft className="h-4 w-4" />
          Property reports
        </Link>

        <nav aria-label="Steps" className="hidden items-center gap-1.5 md:flex">
          {STEP_LABELS.map((label, i) => {
            const current = step === i;
            const done = i < step;
            const clickable = i <= step;
            return (
              <button
                key={label}
                type="button"
                onClick={() => {
                  if (clickable) goToStep(i);
                }}
                disabled={!clickable}
                aria-current={current ? "step" : undefined}
                className={`flex items-center gap-2 rounded-full px-2.5 py-1.5 text-[13px] ${
                  current ? "font-bold text-[#0F172A]" : done ? "font-medium text-[#334155]" : "font-medium text-[#94A3B8]"
                } ${clickable && !current ? "cursor-pointer hover:text-[#0F172A]" : "cursor-default"}`}
              >
                <span
                  className={`flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-bold ${
                    current ? "bg-[#0F172A] text-white" : done ? "bg-[#D1FAE5] text-[#047857]" : "bg-[#ECEAE3] text-[#64748B]"
                  }`}
                >
                  {done ? <Check className="h-3 w-3" /> : i + 1}
                </span>
                {label}
              </button>
            );
          })}
        </nav>
        <span className="text-[13px] font-medium text-[#64748B] md:hidden">
          Step {step + 1} of 4: {STEP_LABELS[step]}
        </span>

        <button
          type="button"
          onClick={() => router.push("/app/property")}
          className="text-sm font-semibold text-[#64748B] hover:text-[#0F172A]"
        >
          Cancel
        </button>
      </header>

      <div className="grid flex-1 lg:grid-cols-[minmax(0,480px)_minmax(0,1fr)]">
        {/* Left — the step, then Back / Continue */}
        <section className="flex min-h-[calc(100vh-62px)] min-w-0 flex-col gap-7 border-[#ECEAE3] px-4 py-8 md:px-10 md:pt-10 lg:border-r">
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
                  onReload={() => loadComparables(compsStatus, sqftTolerance, radiusMiles)}
                  sqftTolerance={sqftTolerance}
                  radiusMiles={radiusMiles}
                  fallbackLevel={fallbackLevel}
                  onFiltersChange={handleFiltersChange}
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

          {/* Footer nav */}
          {generationPhase !== "generating" && generationPhase !== "success" && (
            <div className="sticky bottom-0 mt-auto flex items-center justify-between gap-3 bg-white pb-2 pt-3">
              <button
                type="button"
                onClick={back}
                disabled={step === 0}
                className="text-sm font-semibold text-[#64748B] hover:text-[#0F172A] disabled:invisible"
              >
                ← Back
              </button>
              {step < 3 && (
                <button
                  type="button"
                  onClick={next}
                  disabled={!canProceed(step)}
                  className="inline-flex h-12 items-center gap-2 rounded-[10px] bg-[#0F172A] px-[22px] text-[15px] font-semibold text-white disabled:bg-[#ECEAE3] disabled:text-[#94A3B8]"
                >
                  Continue
                  <ArrowRight className="h-4 w-4" />
                </button>
              )}
            </div>
          )}
        </section>

        {/* Right — the cover sketch and what is set, on Design's warm panel */}
        <aside
          aria-label="Report preview"
          className="sticky top-[62px] hidden h-[calc(100vh-62px)] min-w-0 flex-col items-center justify-center gap-5 overflow-y-auto bg-[#F4F3EE] px-8 py-10 lg:flex"
        >
          {/* Cover sketch */}
          <div
            className="aspect-[8.5/11] w-[300px] shrink-0 overflow-hidden rounded-md"
            style={{
              background: selectedTheme?.gradient || "linear-gradient(135deg, #18235c, #34d1c3)",
              boxShadow: "0 40px 80px -28px rgba(15,23,42,0.4), 0 0 0 1px rgba(15,23,42,0.06)",
            }}
          >
            <div className="flex h-full flex-col justify-between p-6">
              <div>
                <p className="text-[10px] uppercase tracking-[0.2em] text-white/60">Property Report</p>
                <p className="mt-1.5 text-lg font-bold leading-tight text-white" style={{ fontFamily: selectedTheme?.displayFont }}>
                  {property?.street_address || "Your Property"}
                </p>
                <p className="mt-0.5 text-[11px] text-white/70">
                  {property ? `${property.city}, ${property.state} ${property.zip_code}` : "City, ST"}
                </p>
              </div>
              {property && (
                <div className="flex justify-center gap-2">
                  {[
                    { value: property.bedrooms, label: "Beds" },
                    { value: property.bathrooms, label: "Baths" },
                    { value: property.sqft?.toLocaleString(), label: "Sqft" },
                  ].map((s) => (
                    <div key={s.label} className="rounded bg-white/15 px-2.5 py-1.5 text-center backdrop-blur">
                      <p className="text-[13px] font-bold text-white">{s.value}</p>
                      <p className="text-[9px] text-white/60">{s.label}</p>
                    </div>
                  ))}
                </div>
              )}
              <div>
                <div className="h-0.5 rounded-full" style={{ backgroundColor: accentColor }} />
                <div className="mt-2 flex items-center gap-2">
                  <div className="h-6 w-6 rounded-full bg-white/20" />
                  <div>
                    <p className="text-[10px] font-medium text-white">Your Name</p>
                    <p className="text-[8px] text-white/50">Your Brokerage</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <span className="text-[13px] text-[#64748B]">
            Sketch of the cover · the PDF uses the {selectedTheme?.name ?? "selected"} template
          </span>

          {/* What is set */}
          <div className="flex w-[300px] flex-col border-t-[1.5px] border-[#0F172A]">
            <SidebarItem
              label="Property"
              value={property?.full_address || null}
              completed={!!property}
              onClick={property ? () => goToStep(0) : undefined}
            />
            <SidebarItem
              label="Comparables"
              value={selectedCompIds.length > 0 ? `${selectedCompIds.length} selected` : null}
              completed={selectedCompIds.length >= 4 && selectedCompIds.length <= 8}
              onClick={selectedCompIds.length > 0 ? () => goToStep(1) : undefined}
            />
            <SidebarItem
              label="Look"
              value={selectedTheme ? `${selectedTheme.name} · ${selectedPageIds.length} pages` : null}
              completed={!!selectedTheme}
              onClick={selectedTheme ? () => goToStep(2) : undefined}
            />
          </div>
        </aside>
      </div>
    </div>
  );
}

/* What is set — one row per step, in Design's list style */
function SidebarItem({
  label,
  value,
  completed,
  onClick,
}: {
  label: string;
  value: string | null;
  completed: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!onClick}
      className="grid w-full items-center gap-3 border-b border-[#ECEAE3] py-3 text-left disabled:cursor-default"
      style={{ gridTemplateColumns: "20px minmax(0,1fr)" }}
    >
      <span
        className={`flex h-5 w-5 items-center justify-center rounded-full ${
          completed ? "bg-[#D1FAE5] text-[#047857]" : "border-[1.5px] border-[#CBD5E1]"
        }`}
      >
        {completed && <Check className="h-3 w-3" />}
      </span>
      <span className="flex min-w-0 flex-col">
        <span className="text-[13px] font-semibold text-[#0F172A]">{label}</span>
        <span className="truncate text-[12px] text-[#64748B]">{value ?? "Not set"}</span>
      </span>
    </button>
  );
}

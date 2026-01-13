"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Check,
  ChevronRight,
  Home,
  Map,
  Palette,
  FileText,
  ArrowLeft,
  Loader2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";

import { PropertySearchForm } from "@/components/property/PropertySearchForm";
import { ComparablesPicker } from "@/components/property/ComparablesPicker";
import { ComparablesMapModal } from "@/components/property/ComparablesMapModal";
import { ThemeSelector } from "@/components/property/ThemeSelector";

import {
  WizardState,
  initialWizardState,
  Comparable,
  SearchParams,
  defaultSearchParams,
  canProceedToStep,
  THEMES,
  ALL_PAGES,
  GeneratedReport,
  getDefaultPagesForTheme,
  getThemeById,
} from "@/lib/wizard-types";

import { apiFetch } from "@/lib/api";

// Wizard steps configuration
const STEPS = [
  { id: 1, name: "Property", icon: Home },
  { id: 2, name: "Comparables", icon: Map },
  { id: 3, name: "Theme", icon: Palette },
  { id: 4, name: "Generate", icon: FileText },
];

export default function NewPropertyReportPage() {
  const router = useRouter();

  // ============================================
  // STATE MANAGEMENT
  // ============================================

  // Current step
  const [currentStep, setCurrentStep] = useState(1);

  // Core wizard state
  const [state, setState] = useState<WizardState>(initialWizardState);

  // Step 1: Property Search
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Step 2: Comparables
  const [availableComps, setAvailableComps] = useState<Comparable[]>([]);
  const [compsLoading, setCompsLoading] = useState(false);
  const [searchParams, setSearchParams] = useState<SearchParams>(defaultSearchParams);
  const [showParamsModal, setShowParamsModal] = useState(false);
  const [showMapModal, setShowMapModal] = useState(false);

  // Step 4: Generation
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [generatedReport, setGeneratedReport] = useState<GeneratedReport | null>(null);

  // ============================================
  // STEP 1: Property Search
  // ============================================

  const handlePropertySearch = useCallback(async () => {
    if (!state.address.trim()) {
      setSearchError("Please enter an address");
      return;
    }

    setSearchLoading(true);
    setSearchError(null);

    try {
      const response = await apiFetch("/v1/property/search", {
        method: "POST",
        body: JSON.stringify({
          address: state.address.trim(),
          city_state_zip: state.cityStateZip.trim(),
        }),
      });

      if (response.success && response.data) {
        setState((prev) => ({ ...prev, property: response.data }));
      } else if (response.multiple_matches?.length > 0) {
        setSearchError(
          `Multiple properties found (${response.multiple_matches.length}). Please be more specific.`
        );
      } else {
        setSearchError(response.error || "Property not found. Please verify the address.");
      }
    } catch (err) {
      console.error("Property search error:", err);
      setSearchError("Failed to search property. Please try again.");
    } finally {
      setSearchLoading(false);
    }
  }, [state.address, state.cityStateZip]);

  // ============================================
  // STEP 2: Fetch Comparables
  // ============================================

  const fetchComparables = useCallback(async () => {
    if (!state.property) return;

    setCompsLoading(true);

    try {
      const response = await apiFetch("/v1/property/comparables", {
        method: "POST",
        body: JSON.stringify({
          address: state.property.full_address,
          city_state_zip: `${state.property.city}, ${state.property.state} ${state.property.zip_code}`,
          latitude: state.property.latitude,
          longitude: state.property.longitude,
          beds: state.property.bedrooms,
          baths: state.property.bathrooms,
          sqft: state.property.sqft,
          radius_miles: searchParams?.radius_miles ?? 0.5,
          sqft_variance: searchParams?.sqft_variance ?? 0.2,
          status: "Closed",
          limit: 20,
        }),
      });

      if (response.success && response.comparables) {
        // Normalize API response to Comparable interface (using camelCase for frontend)
        const normalized: Comparable[] = response.comparables.map((c: any) => ({
          id: c.mls_id || c.listingId || c.mlsId || c.id || String(Math.random()),
          address: c.address?.full || c.address || "Unknown Address",
          city: c.address?.city || c.city,
          price: c.list_price || c.close_price || c.listPrice || c.closePrice || c.price || 0,
          bedrooms: c.property?.bedrooms || c.bedrooms || 0,
          bathrooms: c.property?.bathsFull || c.bathrooms || 0,
          sqft: c.property?.area || c.sqft || 0,
          year_built: c.property?.yearBuilt || c.year_built,
          lat: c.geo?.lat || c.lat,
          lng: c.geo?.lng || c.lng,
          photo_url: c.photos?.[0] || c.photo_url,
          distance_miles: c.distance_miles,
          status: c.mls?.status || c.status || "Closed",
          days_on_market: c.mls?.daysOnMarket || c.days_on_market,
        } as Comparable));

        setAvailableComps(normalized);

        // Show params modal if < 4 comps found
        if (normalized.length < 4) {
          setShowParamsModal(true);
        }
      } else {
        setAvailableComps([]);
        setShowParamsModal(true);
      }
    } catch (err) {
      console.error("Comparables error:", err);
      setAvailableComps([]);
    } finally {
      setCompsLoading(false);
    }
  }, [state.property, searchParams]);

  // Auto-fetch comparables when entering Step 2
  useEffect(() => {
    if (currentStep === 2 && state.property && availableComps.length === 0 && !compsLoading) {
      fetchComparables();
    }
  }, [currentStep, state.property, availableComps.length, compsLoading, fetchComparables]);

  // ============================================
  // STEP 3: Theme Changes
  // ============================================

  // Update default pages when theme changes
  const handleThemeChange = useCallback((themeId: number) => {
    const newPages = getDefaultPagesForTheme(themeId as 1 | 2 | 3 | 4 | 5);
    setState((prev) => ({
      ...prev,
      theme: themeId as 1 | 2 | 3 | 4 | 5,
      accentColor: getThemeById(themeId as 1 | 2 | 3 | 4 | 5).defaultColor,
      selectedPages: newPages,
    }));
  }, []);

  // ============================================
  // STEP 4: Generate Report
  // ============================================

  const handleGenerate = useCallback(async () => {
    if (!state.property) return;

    setGenerating(true);
    setProgress(10);

    try {
      // Create the report
      const response = await apiFetch("/v1/property/reports", {
        method: "POST",
        body: JSON.stringify({
          report_type: "seller",
          theme: state.theme,
          accent_color: state.accentColor,
          property_address: state.property.full_address,
          property_city: state.property.city,
          property_state: state.property.state,
          property_zip: state.property.zip_code,
          apn: state.property.apn,
          owner_name: state.property.owner_name,
          selected_comp_ids: state.selectedCompIds,
          selected_pages: state.selectedPages,
          sitex_data: state.property,
        }),
      });

      if (!response.id) {
        throw new Error(response.error || "Failed to create report");
      }

      setProgress(30);
      setState((prev) => ({ ...prev, reportId: response.id }));

      // Poll for completion
      const reportId = response.id;
      let attempts = 0;

      while (attempts < 60) {
        await new Promise((r) => setTimeout(r, 2000));

        const statusResponse = await apiFetch(`/v1/property/reports/${reportId}`);

        if (statusResponse.status === "complete") {
          setProgress(100);
          setGeneratedReport({
            id: reportId,
            pdf_url: statusResponse.pdf_url,
            qr_code_url: statusResponse.qr_code_url,
            short_code: statusResponse.short_code,
          });
          return;
        } else if (statusResponse.status === "failed") {
          throw new Error(statusResponse.error_message || "Report generation failed");
        }

        setProgress(Math.min(90, 30 + attempts * 2));
        attempts++;
      }

      throw new Error("Report generation timed out. Please check the reports list.");
    } catch (err) {
      console.error("Generation error:", err);
      alert(err instanceof Error ? err.message : "Failed to generate report");
    } finally {
      setGenerating(false);
    }
  }, [state]);

  // Reset wizard
  const resetWizard = useCallback(() => {
    setState(initialWizardState);
    setAvailableComps([]);
    setGeneratedReport(null);
    setProgress(0);
    setCurrentStep(1);
  }, []);

  // ============================================
  // NAVIGATION
  // ============================================

  const goToStep = useCallback(
    (step: number) => {
      if (step < currentStep) {
        setCurrentStep(step);
        return;
      }

      // Validate before advancing
      for (let s = currentStep + 1; s <= step; s++) {
        const validator = canProceedToStep[s as keyof typeof canProceedToStep];
        if (validator && !validator(state)) {
          return;
        }
      }

      setCurrentStep(step);
    },
    [currentStep, state]
  );

  const canProceed = useCallback(() => {
    const nextStep = currentStep + 1;
    const validator = canProceedToStep[nextStep as keyof typeof canProceedToStep];
    return validator ? validator(state) : true;
  }, [currentStep, state]);

  // ============================================
  // RENDER
  // ============================================

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/app/property">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="w-5 h-5" />
          </Button>
        </Link>
        <div>
          <h1 className="font-bold text-2xl">Create Property Report</h1>
          <p className="text-muted-foreground text-sm">
            Generate a professional seller presentation
          </p>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="relative">
        <Progress value={(currentStep / 4) * 100} className="h-2" />
        <div className="flex justify-between mt-4">
          {STEPS.map((step, index) => {
            const Icon = step.icon;
            const isActive = currentStep === step.id;
            const isComplete = currentStep > step.id;
            const canClick = step.id < currentStep || (step.id === currentStep + 1 && canProceed());

            return (
              <div key={step.id} className="flex items-center">
                <button
                  onClick={() => canClick && goToStep(step.id)}
                  disabled={!canClick && step.id > currentStep}
                  className={`
                    flex flex-col items-center gap-2 transition-all
                    ${canClick || step.id <= currentStep ? "cursor-pointer" : "cursor-not-allowed opacity-50"}
                  `}
                >
                  <div
                    className={`
                      w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors
                      ${isComplete ? "bg-primary border-primary text-primary-foreground" : ""}
                      ${isActive ? "border-primary bg-background" : ""}
                      ${!isActive && !isComplete ? "border-muted-foreground/30 bg-background" : ""}
                    `}
                  >
                    {isComplete ? <Check className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                  </div>
                  <span
                    className={`text-xs font-medium hidden sm:block ${
                      isActive || isComplete ? "text-foreground" : "text-muted-foreground"
                    }`}
                  >
                    {step.name}
                  </span>
                </button>

                {index < STEPS.length - 1 && (
                  <ChevronRight className="w-5 h-5 text-muted-foreground/30 mx-2 hidden sm:block" />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Step Content */}
      <Card>
        <CardContent className="pt-6">
          {/* STEP 1: Property Search */}
          {currentStep === 1 && (
            <PropertySearchForm
              address={state.address}
              cityStateZip={state.cityStateZip}
              property={state.property}
              loading={searchLoading}
              error={searchError}
              onAddressChange={(address) => setState((prev) => ({ ...prev, address }))}
              onCityStateZipChange={(csz) => setState((prev) => ({ ...prev, cityStateZip: csz }))}
              onSearch={handlePropertySearch}
              onContinue={() => setCurrentStep(2)}
              canContinue={!!state.property}
            />
          )}

          {/* STEP 2: Comparables */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold mb-1">Select Comparables</h2>
                <p className="text-sm text-muted-foreground">
                  Choose 4-8 comparable properties to include in your report
                </p>
              </div>

              {compsLoading ? (
                <div className="text-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">Finding comparable properties...</p>
                  <p className="text-sm text-muted-foreground/70 mt-1">
                    Searching within {searchParams?.radius_miles ?? 0.5} miles, ±
                    {Math.round((searchParams?.sqft_variance ?? 0.2) * 100)}% sqft
                  </p>
                </div>
              ) : (
                <ComparablesPicker
                  availableComps={availableComps}
                  selectedIds={state.selectedCompIds}
                  onSelectionChange={(ids) =>
                    setState((prev) => ({ ...prev, selectedCompIds: ids }))
                  }
                  onOpenMap={() => setShowMapModal(true)}
                  minSelections={4}
                  maxSelections={8}
                  subjectProperty={
                    state.property
                      ? {
                          bedrooms: state.property.bedrooms,
                          bathrooms: state.property.bathrooms,
                          sqft: state.property.sqft,
                        }
                      : undefined
                  }
                  mapDisabled={!state.property?.latitude || !state.property?.longitude}
                />
              )}

              {/* Search params info */}
              {!compsLoading && availableComps.length > 0 && (
                <div className="flex items-center justify-between text-sm text-muted-foreground border-t pt-4">
                  <span>
                    Found {availableComps.length} properties within {searchParams?.radius_miles ?? 0.5} miles,
                    ±{Math.round((searchParams?.sqft_variance ?? 0.2) * 100)}% sqft
                  </span>
                  <button
                    onClick={() => setShowParamsModal(true)}
                    className="text-primary hover:underline"
                  >
                    Adjust Search
                  </button>
                </div>
              )}

              {/* Navigation */}
              <div className="flex justify-between pt-4 border-t">
                <Button variant="outline" onClick={() => setCurrentStep(1)}>
                  ← Back
                </Button>
                <Button
                  onClick={() => setCurrentStep(3)}
                  disabled={!canProceedToStep[3](state)}
                >
                  Continue →
                </Button>
              </div>

              {/* Map Modal */}
              {state.property?.latitude && state.property?.longitude && (
                <ComparablesMapModal
                  isOpen={showMapModal}
                  onClose={() => setShowMapModal(false)}
                  subjectProperty={{
                    lat: state.property.latitude,
                    lng: state.property.longitude,
                    address: state.property.full_address,
                    bedrooms: state.property.bedrooms,
                    bathrooms: state.property.bathrooms,
                    sqft: state.property.sqft,
                  }}
                  comparables={availableComps}
                  selectedIds={state.selectedCompIds}
                  onSelectionChange={(ids) =>
                    setState((prev) => ({ ...prev, selectedCompIds: ids }))
                  }
                  maxSelections={8}
                />
              )}

              {/* Params Adjustment Modal */}
              <Dialog open={showParamsModal} onOpenChange={setShowParamsModal}>
                <DialogContent className="max-w-md">
                  <DialogHeader>
                    <DialogTitle>Adjust Search Parameters</DialogTitle>
                    <DialogDescription>
                      {availableComps.length < 4
                        ? `Only ${availableComps.length} comparable(s) found. Expand your search.`
                        : "Refine your search parameters to find different comparables."}
                    </DialogDescription>
                  </DialogHeader>

                  <div className="space-y-6 py-4">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <Label>Search Radius</Label>
                        <span className="text-sm font-semibold text-primary">
                          {(searchParams?.radius_miles ?? 0.5).toFixed(2)} miles
                        </span>
                      </div>
                      <input
                        type="range"
                        min="0.25"
                        max="3.0"
                        step="0.25"
                        value={searchParams?.radius_miles ?? 0.5}
                        onChange={(e) =>
                          setSearchParams((prev) => ({
                            ...prev,
                            radius_miles: parseFloat(e.target.value),
                          }))
                        }
                        className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                      />
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>0.25 mi</span>
                        <span>1.5 mi</span>
                        <span>3.0 mi</span>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <Label>Square Footage Variance</Label>
                        <span className="text-sm font-semibold text-primary">
                          ±{Math.round((searchParams?.sqft_variance ?? 0.2) * 100)}%
                        </span>
                      </div>
                      <input
                        type="range"
                        min="0.10"
                        max="0.50"
                        step="0.05"
                        value={searchParams?.sqft_variance ?? 0.2}
                        onChange={(e) =>
                          setSearchParams((prev) => ({
                            ...prev,
                            sqft_variance: parseFloat(e.target.value),
                          }))
                        }
                        className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                      />
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>±10%</span>
                        <span>±30%</span>
                        <span>±50%</span>
                      </div>
                      {state.property?.sqft && (
                        <p className="text-xs text-muted-foreground text-center">
                          Range:{" "}
                          {Math.round(
                            state.property.sqft * (1 - (searchParams?.sqft_variance ?? 0.2))
                          ).toLocaleString()}{" "}
                          -{" "}
                          {Math.round(
                            state.property.sqft * (1 + (searchParams?.sqft_variance ?? 0.2))
                          ).toLocaleString()}{" "}
                          sqft
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={() => setShowParamsModal(false)}
                    >
                      Keep Current
                    </Button>
                    <Button
                      className="flex-1"
                      onClick={() => {
                        setShowParamsModal(false);
                        setState((prev) => ({ ...prev, selectedCompIds: [] }));
                        setAvailableComps([]);
                        fetchComparables();
                      }}
                      disabled={compsLoading}
                    >
                      Search Again
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          )}

          {/* STEP 3: Theme & Pages */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <ThemeSelector
                selectedTheme={state.theme}
                onThemeChange={handleThemeChange}
                accentColor={state.accentColor}
                onAccentColorChange={(color) =>
                  setState((prev) => ({ ...prev, accentColor: color }))
                }
                selectedPages={state.selectedPages}
                onPagesChange={(pages) =>
                  setState((prev) => ({ ...prev, selectedPages: pages }))
                }
                propertyAddress={state.property?.full_address || state.address}
              />

              {/* Navigation */}
              <div className="flex justify-between pt-4 border-t">
                <Button variant="outline" onClick={() => setCurrentStep(2)}>
                  ← Back
                </Button>
                <Button
                  onClick={() => setCurrentStep(4)}
                  disabled={!canProceedToStep[4](state)}
                >
                  Continue to Review →
                </Button>
              </div>
            </div>
          )}

          {/* STEP 4: Review & Generate */}
          {currentStep === 4 && (
            <div className="space-y-6">
              {!generatedReport ? (
                <>
                  {/* Review Summary */}
                  <div className="bg-muted/30 rounded-lg p-6">
                    <h3 className="font-semibold text-lg mb-4">Review Your Report</h3>

                    <div className="grid md:grid-cols-2 gap-6">
                      {/* Property Info */}
                      <div className="space-y-3">
                        <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
                          Property
                        </h4>
                        <div className="bg-background rounded-lg p-4 border">
                          <p className="font-semibold">
                            {state.property?.full_address || state.address}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {state.property?.city}, {state.property?.state}{" "}
                            {state.property?.zip_code}
                          </p>
                          <div className="flex gap-4 mt-2 text-sm text-muted-foreground">
                            <span>{state.property?.bedrooms} bed</span>
                            <span>{state.property?.bathrooms} bath</span>
                            <span>{state.property?.sqft?.toLocaleString()} sqft</span>
                          </div>
                        </div>
                      </div>

                      {/* Report Config */}
                      <div className="space-y-3">
                        <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
                          Report Settings
                        </h4>
                        <div className="bg-background rounded-lg p-4 border space-y-2">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Theme</span>
                            <span className="font-medium">
                              {getThemeById(state.theme).name}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-muted-foreground">Accent Color</span>
                            <div className="flex items-center gap-2">
                              <span
                                className="w-5 h-5 rounded-full border"
                                style={{ backgroundColor: state.accentColor }}
                              />
                              <span className="font-mono text-sm">{state.accentColor}</span>
                            </div>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Comparables</span>
                            <span className="font-medium">
                              {state.selectedCompIds.length} selected
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Pages</span>
                            <span className="font-medium">{state.selectedPages.length} pages</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Selected Pages Preview */}
                    <div className="mt-6">
                      <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide mb-3">
                        Included Pages
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {state.selectedPages.map((pageId, index) => {
                          const page = ALL_PAGES.find((p) => p.id === pageId);
                          return (
                            <span
                              key={pageId}
                              className="px-2 py-1 bg-background border rounded text-sm"
                            >
                              {index + 1}. {page?.name || pageId}
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  </div>

                  {/* Generation Progress or Button */}
                  {generating ? (
                    <div className="text-center py-8">
                      <div className="w-20 h-20 mx-auto mb-4 relative">
                        <svg className="animate-spin" viewBox="0 0 100 100">
                          <circle
                            className="text-muted stroke-current"
                            strokeWidth="8"
                            fill="transparent"
                            r="42"
                            cx="50"
                            cy="50"
                          />
                          <circle
                            className="text-primary stroke-current"
                            strokeWidth="8"
                            strokeDasharray={264}
                            strokeDashoffset={264 - (264 * progress) / 100}
                            strokeLinecap="round"
                            fill="transparent"
                            r="42"
                            cx="50"
                            cy="50"
                          />
                        </svg>
                        <span className="absolute inset-0 flex items-center justify-center text-sm font-semibold">
                          {progress}%
                        </span>
                      </div>
                      <p className="text-foreground font-medium">Generating your report...</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        This may take up to 30 seconds
                      </p>
                    </div>
                  ) : (
                    <div className="flex justify-between pt-4 border-t">
                      <Button variant="outline" onClick={() => setCurrentStep(3)}>
                        ← Back
                      </Button>
                      <Button
                        onClick={handleGenerate}
                        className="bg-green-600 hover:bg-green-700"
                      >
                        <FileText className="w-4 h-4 mr-2" />
                        Generate Report
                      </Button>
                    </div>
                  )}
                </>
              ) : (
                /* Success State */
                <div className="text-center py-8">
                  <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Check className="w-10 h-10 text-green-600" />
                  </div>

                  <h3 className="text-2xl font-semibold mb-2">Report Generated!</h3>
                  <p className="text-muted-foreground mb-8">
                    Your seller report for {state.property?.full_address} is ready.
                  </p>

                  <div className="grid md:grid-cols-2 gap-6 max-w-2xl mx-auto">
                    {/* PDF Download */}
                    <div className="bg-background border rounded-lg p-6 text-left">
                      <h4 className="font-semibold mb-3 flex items-center gap-2">
                        <FileText className="w-5 h-5" />
                        Download PDF
                      </h4>
                      {generatedReport.pdf_url ? (
                        <a
                          href={generatedReport.pdf_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block w-full px-4 py-3 bg-primary text-primary-foreground rounded-lg text-center hover:bg-primary/90 transition-colors"
                        >
                          Download Report
                        </a>
                      ) : (
                        <p className="text-sm text-muted-foreground">PDF is being generated...</p>
                      )}
                    </div>

                    {/* QR Code */}
                    <div className="bg-background border rounded-lg p-6 text-left">
                      <h4 className="font-semibold mb-3 flex items-center gap-2">
                        <Map className="w-5 h-5" />
                        QR Code
                      </h4>
                      {generatedReport.qr_code_url ? (
                        <>
                          <img
                            src={generatedReport.qr_code_url}
                            alt="QR Code"
                            className="w-32 h-32 mx-auto border rounded"
                          />
                          <p className="text-xs text-muted-foreground text-center mt-2">
                            Scan to view landing page
                          </p>
                        </>
                      ) : (
                        <div className="w-32 h-32 mx-auto bg-muted rounded flex items-center justify-center">
                          <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Landing Page Link */}
                  {generatedReport.short_code && (
                    <div className="mt-6 p-4 bg-muted/30 rounded-lg max-w-md mx-auto">
                      <p className="text-sm text-muted-foreground mb-2">Public Landing Page:</p>
                      <a
                        href={`https://trendyreports.io/p/${generatedReport.short_code}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline break-all font-medium"
                      >
                        trendyreports.io/p/{generatedReport.short_code}
                      </a>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex justify-center gap-4 mt-8">
                    <Button variant="outline" onClick={resetWizard}>
                      Create Another Report
                    </Button>
                    <Link href={`/app/property/${generatedReport.id}`}>
                      <Button>View Report Details</Button>
                    </Link>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

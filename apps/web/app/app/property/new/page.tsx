"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Home,
  Map,
  Palette,
  FileText,
  ArrowLeft,
  ArrowRight,
  Loader2,
  Check,
  CheckCircle2,
  XCircle,
  Download,
  Eye,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { apiFetch } from "@/lib/api";

// ============================================
// TYPES - All values have explicit defaults
// ============================================

interface PropertyData {
  full_address: string;
  street: string;
  city: string;
  state: string;
  zip_code: string;
  county: string;
  apn: string;
  owner_name: string;
  bedrooms: number;
  bathrooms: number;
  sqft: number;
  year_built: number | null;
  assessed_value: number | null;
  latitude: number;
  longitude: number;
}

interface Comparable {
  id: string;
  address: string;
  city: string;
  price: number;
  bedrooms: number;
  bathrooms: number;
  sqft: number;
  photo_url: string | null;
  distance_miles: number | null;
  status: string;
}

interface WizardState {
  // Step 1
  address: string;
  cityStateZip: string;
  property: PropertyData | null;
  
  // Step 2
  comparables: Comparable[];
  selectedCompIds: string[];
  
  // Step 3
  theme: number;
  accentColor: string;
  
  // Step 4
  reportId: string | null;
}

const initialState: WizardState = {
  address: "",
  cityStateZip: "",
  property: null,
  comparables: [],
  selectedCompIds: [],
  theme: 1,
  accentColor: "#0d294b",
  reportId: null,
};

// ============================================
// STEP CONFIGURATION
// ============================================

const STEPS = [
  { id: 1, name: "Property", icon: Home },
  { id: 2, name: "Comparables", icon: Map },
  { id: 3, name: "Theme", icon: Palette },
  { id: 4, name: "Generate", icon: FileText },
];

// ============================================
// VALIDATION
// ============================================

function validateStep(state: WizardState, step: number): { valid: boolean; error?: string } {
  switch (step) {
    case 1:
      return state.property !== null 
        ? { valid: true } 
        : { valid: false, error: "Please search and select a property" };
    case 2:
      const count = state.selectedCompIds.length;
      if (count < 4) return { valid: false, error: "Select at least 4 comparables" };
      if (count > 8) return { valid: false, error: "Maximum 8 comparables allowed" };
      return { valid: true };
    case 3:
      return state.theme >= 1 && state.theme <= 5 
        ? { valid: true } 
        : { valid: false, error: "Select a theme" };
    case 4:
      return { valid: true };
    default:
      return { valid: false };
  }
}

// ============================================
// MAIN COMPONENT
// ============================================

export default function NewPropertyReportPage() {
  const router = useRouter();
  
  // Core state
  const [currentStep, setCurrentStep] = useState(1);
  const [state, setState] = useState<WizardState>(initialState);
  const [error, setError] = useState<string | null>(null);
  
  // Loading states
  const [searchLoading, setSearchLoading] = useState(false);
  const [compsLoading, setCompsLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  
  // Generation result
  const [generationState, setGenerationState] = useState<"idle" | "generating" | "completed" | "failed">("idle");
  const [generatedReport, setGeneratedReport] = useState<{ id: string; pdf_url: string } | null>(null);

  // ============================================
  // NAVIGATION
  // ============================================

  const handleNext = () => {
    const validation = validateStep(state, currentStep);
    if (!validation.valid) {
      setError(validation.error || "Please complete this step");
      return;
    }
    setError(null);
    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    setError(null);
    setCurrentStep(Math.max(1, currentStep - 1));
  };

  // ============================================
  // STEP 1: Property Search
  // ============================================

  const handlePropertySearch = async () => {
    if (!state.address.trim()) {
      setError("Please enter an address");
      return;
    }

    setSearchLoading(true);
    setError(null);

    try {
      const response = await apiFetch("/v1/property/search", {
        method: "POST",
        body: JSON.stringify({
          address: state.address.trim(),
          city_state_zip: state.cityStateZip.trim(),
        }),
      });

      if (response.success && response.data) {
        setState(prev => ({ ...prev, property: response.data }));
      } else {
        setError(response.error || "Property not found");
      }
    } catch (err) {
      console.error("Property search error:", err);
      setError("Failed to search property");
    } finally {
      setSearchLoading(false);
    }
  };

  // ============================================
  // STEP 2: Fetch Comparables
  // ============================================

  const handleFetchComparables = async () => {
    if (!state.property) return;

    setCompsLoading(true);
    setError(null);

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
          radius_miles: 1.0,
          sqft_variance: 0.25,
          status: "Closed",
          limit: 20,
        }),
      });

      if (response.success && response.comparables) {
        // Normalize to simple objects with safe defaults
        const normalized: Comparable[] = response.comparables.map((c: any, index: number) => ({
          id: String(c.mls_id || c.listingId || c.mlsId || c.id || index),
          address: c.address?.full || c.address || "Unknown",
          city: c.address?.city || c.city || "",
          price: Number(c.list_price || c.close_price || c.listPrice || c.closePrice || c.price || 0),
          bedrooms: Number(c.property?.bedrooms || c.bedrooms || 0),
          bathrooms: Number(c.property?.bathsFull || c.bathrooms || 0),
          sqft: Number(c.property?.area || c.sqft || 0),
          photo_url: c.photos?.[0] || c.photo_url || null,
          distance_miles: c.distance_miles != null ? Number(c.distance_miles) : null,
          status: c.mls?.status || c.status || "Closed",
        }));

        setState(prev => ({ ...prev, comparables: normalized }));
      } else {
        setError("No comparables found. Try expanding search criteria.");
      }
    } catch (err) {
      console.error("Comparables error:", err);
      setError("Failed to fetch comparables");
    } finally {
      setCompsLoading(false);
    }
  };

  // ============================================
  // STEP 4: Generate Report
  // ============================================

  const handleGenerate = async () => {
    if (!state.property) return;

    setGenerationState("generating");
    setError(null);

    try {
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
          sitex_data: state.property,
        }),
      });

      if (!response.id) {
        throw new Error(response.error || "Failed to create report");
      }

      const reportId = response.id;

      // Poll for completion
      let attempts = 0;
      const poll = async () => {
        attempts++;
        const statusResponse = await apiFetch(`/v1/property/reports/${reportId}`);

        if (statusResponse.status === "complete") {
          setGenerationState("completed");
          setGeneratedReport({
            id: reportId,
            pdf_url: statusResponse.pdf_url,
          });
          return;
        }

        if (statusResponse.status === "failed" || attempts > 60) {
          setGenerationState("failed");
          setError(statusResponse.error_message || "Report generation failed");
          return;
        }

        setTimeout(poll, 2000);
      };
      poll();
    } catch (err) {
      console.error("Generation error:", err);
      setGenerationState("failed");
      setError(err instanceof Error ? err.message : "Failed to generate report");
    }
  };

  // ============================================
  // RENDER - STEP 1: Property Search
  // ============================================

  const renderStep1 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-2">Find Your Property</h2>
        <p className="text-muted-foreground">Enter the property address to get started</p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Property Address</label>
          <input
            type="text"
            placeholder="123 Main St"
            value={state.address}
            onChange={(e) => setState(prev => ({ ...prev, address: e.target.value }))}
            className="w-full px-4 py-3 rounded-lg border bg-background"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">City, State ZIP</label>
          <input
            type="text"
            placeholder="Anaheim, CA 92805"
            value={state.cityStateZip}
            onChange={(e) => setState(prev => ({ ...prev, cityStateZip: e.target.value }))}
            className="w-full px-4 py-3 rounded-lg border bg-background"
          />
        </div>

        {!state.property && (
          <Button
            onClick={handlePropertySearch}
            disabled={searchLoading || !state.address.trim()}
            className="w-full py-6"
          >
            {searchLoading ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                Searching...
              </>
            ) : (
              "Search Property"
            )}
          </Button>
        )}
      </div>

      {/* Property Result */}
      {state.property && (
        <div className="border-2 border-green-500 rounded-lg p-4 space-y-4">
          <div className="flex items-center gap-2 text-green-600">
            <CheckCircle2 className="w-5 h-5" />
            <span className="font-medium">Property Found</span>
          </div>
          
          <div>
            <p className="text-lg font-semibold">{state.property.full_address}</p>
            <p className="text-muted-foreground">
              {state.property.city}, {state.property.state} {state.property.zip_code}
            </p>
          </div>

          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Beds</p>
              <p className="font-medium">{state.property.bedrooms}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Baths</p>
              <p className="font-medium">{state.property.bathrooms}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Sqft</p>
              <p className="font-medium">{state.property.sqft.toLocaleString()}</p>
            </div>
          </div>

          <Button
            variant="outline"
            onClick={() => setState(prev => ({ ...prev, property: null }))}
          >
            Search Different Property
          </Button>
        </div>
      )}
    </div>
  );

  // ============================================
  // RENDER - STEP 2: Comparables
  // ============================================

  const renderStep2 = () => {
    // Pre-compute display values - NO inline calculations
    const selectedCount = state.selectedCompIds.length;
    const isMinMet = selectedCount >= 4;
    const statusText = isMinMet 
      ? `${selectedCount} selected` 
      : `Select ${4 - selectedCount} more`;

    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold mb-2">Select Comparables</h2>
          <p className="text-muted-foreground">Choose 4-8 comparable properties</p>
        </div>

        {/* Status Bar */}
        <div className={`p-3 rounded-lg ${isMinMet ? "bg-green-50 border-green-200" : "bg-amber-50 border-amber-200"} border`}>
          <span className={isMinMet ? "text-green-700" : "text-amber-700"}>
            {statusText}
          </span>
        </div>

        {/* Fetch Button */}
        {state.comparables.length === 0 && (
          <Button
            onClick={handleFetchComparables}
            disabled={compsLoading}
            className="w-full py-6"
          >
            {compsLoading ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                Finding Comparables...
              </>
            ) : (
              "Search for Comparables"
            )}
          </Button>
        )}

        {/* Comparables List */}
        {state.comparables.length > 0 && (
          <div className="grid gap-3 max-h-96 overflow-y-auto">
            {state.comparables.map((comp) => {
              const isSelected = state.selectedCompIds.includes(comp.id);
              // Pre-compute display strings
              const priceDisplay = `$${comp.price.toLocaleString()}`;
              const distanceDisplay = comp.distance_miles != null 
                ? `${comp.distance_miles.toFixed(1)} mi` 
                : "";
              const sqftDisplay = comp.sqft.toLocaleString();

              return (
                <div
                  key={comp.id}
                  onClick={() => {
                    if (isSelected) {
                      setState(prev => ({
                        ...prev,
                        selectedCompIds: prev.selectedCompIds.filter(id => id !== comp.id)
                      }));
                    } else if (state.selectedCompIds.length < 8) {
                      setState(prev => ({
                        ...prev,
                        selectedCompIds: [...prev.selectedCompIds, comp.id]
                      }));
                    }
                  }}
                  className={`
                    p-4 rounded-lg border-2 cursor-pointer transition-all
                    ${isSelected ? "border-green-500 bg-green-50" : "border-gray-200 hover:border-gray-400"}
                  `}
                >
                  <div className="flex items-start gap-4">
                    {/* Photo */}
                    <div className="w-20 h-16 rounded bg-gray-100 flex-shrink-0 overflow-hidden">
                      {comp.photo_url ? (
                        <img src={comp.photo_url} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Home className="w-6 h-6 text-gray-400" />
                        </div>
                      )}
                    </div>

                    {/* Details */}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{comp.address}</p>
                      <p className="text-lg font-bold text-primary">{priceDisplay}</p>
                      <div className="flex gap-4 text-sm text-muted-foreground">
                        <span>{comp.bedrooms} bd</span>
                        <span>{comp.bathrooms} ba</span>
                        <span>{sqftDisplay} sqft</span>
                        {distanceDisplay && <span>{distanceDisplay}</span>}
                      </div>
                    </div>

                    {/* Selection Indicator */}
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center ${isSelected ? "bg-green-500" : "bg-gray-200"}`}>
                      {isSelected && <Check className="w-4 h-4 text-white" />}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  // ============================================
  // RENDER - STEP 3: Theme Selection
  // ============================================

  const THEMES = [
    { id: 1, name: "Classic", color: "#0d294b" },
    { id: 2, name: "Modern", color: "#f2964a" },
    { id: 3, name: "Elegant", color: "#0d294b" },
    { id: 4, name: "Teal", color: "#16d3ba" },
    { id: 5, name: "Bold", color: "#d79547" },
  ];

  const renderStep3 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-2">Choose Theme</h2>
        <p className="text-muted-foreground">Select a design theme for your report</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {THEMES.map((theme) => {
          const isSelected = state.theme === theme.id;
          return (
            <button
              key={theme.id}
              onClick={() => setState(prev => ({ ...prev, theme: theme.id, accentColor: theme.color }))}
              className={`
                p-4 rounded-xl border-2 transition-all text-center
                ${isSelected ? "border-primary bg-primary/5" : "border-gray-200 hover:border-gray-400"}
              `}
            >
              <div
                className="w-12 h-12 rounded-full mx-auto mb-2"
                style={{ backgroundColor: theme.color }}
              />
              <p className="font-medium">{theme.name}</p>
              {isSelected && (
                <div className="mt-2">
                  <Check className="w-4 h-4 mx-auto text-primary" />
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );

  // ============================================
  // RENDER - STEP 4: Review & Generate
  // ============================================

  const renderStep4 = () => {
    // Pre-compute all display values
    const propertyAddress = state.property?.full_address || "Unknown";
    const propertyCity = state.property 
      ? `${state.property.city}, ${state.property.state} ${state.property.zip_code}`
      : "";
    const selectedTheme = THEMES.find(t => t.id === state.theme);
    const themeName = selectedTheme?.name || "Classic";
    const compCount = state.selectedCompIds.length;

    if (generationState === "generating") {
      return (
        <div className="text-center py-12">
          <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto mb-4" />
          <h3 className="text-lg font-semibold">Generating Report...</h3>
          <p className="text-muted-foreground">This may take up to 30 seconds</p>
        </div>
      );
    }

    if (generationState === "completed" && generatedReport) {
      return (
        <div className="text-center py-12">
          <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">Report Ready!</h3>
          <p className="text-muted-foreground mb-6">Your property report has been generated</p>
          
          <div className="flex flex-col gap-3 max-w-xs mx-auto">
            {generatedReport.pdf_url && (
              <a
                href={generatedReport.pdf_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary/90"
              >
                <Download className="w-5 h-5" />
                Download PDF
              </a>
            )}
            <Button
              variant="outline"
              onClick={() => router.push("/app/property")}
            >
              View All Reports
            </Button>
          </div>
        </div>
      );
    }

    if (generationState === "failed") {
      return (
        <div className="text-center py-12">
          <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">Generation Failed</h3>
          <p className="text-red-600 mb-6">{error || "An error occurred"}</p>
          <Button onClick={() => setGenerationState("idle")}>Try Again</Button>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold mb-2">Review & Generate</h2>
          <p className="text-muted-foreground">Review your selections before generating</p>
        </div>

        <div className="bg-muted/30 rounded-lg p-6 space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Property</p>
              <p className="font-semibold">{propertyAddress}</p>
              <p className="text-sm text-muted-foreground">{propertyCity}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Theme</p>
              <p className="font-semibold">{themeName}</p>
            </div>
          </div>
          
          <div>
            <p className="text-sm text-muted-foreground">Comparables</p>
            <p className="font-semibold">{compCount} properties selected</p>
          </div>
        </div>

        <Button
          onClick={handleGenerate}
          className="w-full py-6 bg-green-600 hover:bg-green-700"
        >
          <FileText className="w-5 h-5 mr-2" />
          Generate Report
        </Button>
      </div>
    );
  };

  // ============================================
  // MAIN RENDER
  // ============================================

  // Calculate progress percentage
  const progressPercent = (currentStep / STEPS.length) * 100;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/app/property">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="w-5 h-5" />
          </Button>
        </Link>
        <div>
          <h1 className="font-bold text-2xl">Create Property Report</h1>
          <p className="text-muted-foreground text-sm">Generate a professional seller presentation</p>
        </div>
      </div>

      {/* Progress */}
      <div>
        <Progress value={progressPercent} className="h-2" />
        <div className="flex justify-between mt-4">
          {STEPS.map((step) => {
            const Icon = step.icon;
            const isActive = currentStep === step.id;
            const isComplete = currentStep > step.id;

            return (
              <div key={step.id} className="flex flex-col items-center gap-2">
                <div
                  className={`
                    w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors
                    ${isComplete ? "bg-primary border-primary text-white" : ""}
                    ${isActive ? "border-primary" : ""}
                    ${!isActive && !isComplete ? "border-gray-300" : ""}
                  `}
                >
                  {isComplete ? <Check className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                </div>
                <span className={`text-xs ${isActive || isComplete ? "text-foreground" : "text-muted-foreground"}`}>
                  {step.name}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700">
          {error}
        </div>
      )}

      {/* Step Content */}
      <Card>
        <CardContent className="pt-6">
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
          {currentStep === 4 && renderStep4()}
        </CardContent>
      </Card>

      {/* Navigation */}
      {generationState === "idle" && (
        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={handleBack}
            disabled={currentStep === 1}
            className="gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </Button>

          {currentStep < STEPS.length ? (
            <Button onClick={handleNext} className="gap-2">
              Next
              <ArrowRight className="w-4 h-4" />
            </Button>
          ) : null}
        </div>
      )}
    </div>
  );
}


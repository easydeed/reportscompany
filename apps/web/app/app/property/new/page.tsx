"use client";

import { useState, useEffect, useRef, useCallback, Fragment } from "react";
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
  Search,
  MapPin,
  Calendar,
  DollarSign,
  User,
  Building,
  Eye,
  QrCode,
  ExternalLink,
  Sparkles,
  RotateCcw,
  Copy,
  Bed,
  Bath,
  Maximize,
  ChevronDown,
  X,
  BarChart3,
  AlertCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";

// Import our existing components
import { ThemeSelector } from "@/components/property/ThemeSelector";
import { ComparablesPicker } from "@/components/property/ComparablesPicker";
import { ComparablesMapModal } from "@/components/property/ComparablesMapModal";
import { useGooglePlaces, PlaceResult } from "@/hooks/useGooglePlaces";

// Import shared types
import { ALL_PAGES, THEMES, getDefaultPagesForTheme, getThemeById } from "@/lib/wizard-types";

// ============================================
// TYPES
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
  legal_description?: string;
  bedrooms: number;
  bathrooms: number;
  sqft: number;
  lot_size?: string;
  year_built?: number;
  assessed_value?: number;
  tax_amount?: number;
  latitude: number;
  longitude: number;
  property_type?: string;
}

interface Comparable {
  id: string;
  address: string;
  city?: string;
  price: number;
  bedrooms: number;
  bathrooms: number;
  sqft: number;
  year_built?: number;
  lat?: number;
  lng?: number;
  photo_url?: string;
  distance_miles?: number;
  status?: string;
  days_on_market?: number;
}

interface WizardState {
  address: string;
  cityStateZip: string;
  property: PropertyData | null;
  comparables: Comparable[];
  selectedCompIds: string[];
  theme: 1 | 2 | 3 | 4 | 5;
  accentColor: string;
  selectedPages: string[];
  reportId: string | null;
}

const initialState: WizardState = {
  address: "",
  cityStateZip: "",
  property: null,
  comparables: [],
  selectedCompIds: [],
  theme: 5, // Bold as default
  accentColor: "#15216E",
  selectedPages: ALL_PAGES.map(p => p.id),
  reportId: null,
};

// ============================================
// STEP CONFIG
// ============================================

const STEPS = [
  { id: 1, name: "Property", icon: Home },
  { id: 2, name: "Comparables", icon: Map },
  { id: 3, name: "Theme", icon: Palette },
  { id: 4, name: "Generate", icon: FileText },
];

// Theme data for preview
const THEME_GRADIENTS: Record<number, string> = {
  1: "linear-gradient(135deg, #1B365D 0%, #0f2040 100%)", // Classic
  2: "linear-gradient(135deg, #1A1F36 0%, #FF6B5B 100%)", // Modern
  3: "linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%)", // Elegant
  4: "linear-gradient(135deg, #18235c 0%, #34d1c3 100%)", // Teal
  5: "linear-gradient(135deg, #15216E 0%, #0a1145 100%)", // Bold
};

// Generation stages
const GENERATION_STAGES = [
  "Fetching property data...",
  "Analyzing comparables...",
  "Rendering report pages...",
  "Generating PDF...",
  "Finalizing...",
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
// HELPER FUNCTIONS
// ============================================

const formatCurrency = (value: number | null | undefined): string => {
  if (value == null) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
};

const formatNumber = (value: number | null | undefined): string => {
  if (value == null) return "—";
  return new Intl.NumberFormat("en-US").format(value);
};

// ============================================
// MAIN COMPONENT
// ============================================

export default function NewPropertyReportPage() {
  const router = useRouter();
  
  // Core state
  const [currentStep, setCurrentStep] = useState(1);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [state, setState] = useState<WizardState>(initialState);
  const [error, setError] = useState<string | null>(null);
  
  // Loading states
  const [searchLoading, setSearchLoading] = useState(false);
  const [compsLoading, setCompsLoading] = useState(false);
  const [compsFetched, setCompsFetched] = useState(false);
  
  // Generation state
  const [generationState, setGenerationState] = useState<"idle" | "generating" | "completed" | "failed">("idle");
  const [generationStage, setGenerationStage] = useState(0);
  const [generatedReport, setGeneratedReport] = useState<{ 
    id: string; 
    pdf_url: string | null;
    qr_code_url: string | null;
    short_code: string | null;
  } | null>(null);

  // Map modal
  const [showMapModal, setShowMapModal] = useState(false);
  
  // Copy state
  const [copied, setCopied] = useState(false);

  // Google Places for Step 1
  const addressInputRef = useRef<HTMLInputElement>(null);
  
  const handlePlaceSelect = useCallback((place: PlaceResult) => {
    const streetAddress = place.address;
    const cityStateZip = `${place.city}, ${place.state} ${place.zip}`;
    
    setState(prev => ({
      ...prev,
      address: streetAddress,
      cityStateZip: cityStateZip,
    }));

    requestAnimationFrame(() => {
      if (addressInputRef.current) {
        addressInputRef.current.value = streetAddress;
      }
    });
  }, []);

  const { isLoaded: googleLoaded, error: placesError } = useGooglePlaces(
    addressInputRef,
    { onPlaceSelect: handlePlaceSelect }
  );

  // ============================================
  // Auto-fetch comparables when entering Step 2
  // ============================================

  useEffect(() => {
    if (currentStep === 2 && state.property && !compsFetched && !compsLoading) {
      fetchComparables();
    }
  }, [currentStep, state.property, compsFetched, compsLoading]);

  // Update completed steps
  useEffect(() => {
    const newCompleted: number[] = [];
    if (state.property) newCompleted.push(1);
    if (state.selectedCompIds.length >= 4) newCompleted.push(2);
    if (state.theme >= 1 && state.theme <= 5) newCompleted.push(3);
    setCompletedSteps(newCompleted);
  }, [state.property, state.selectedCompIds, state.theme]);

  // ============================================
  // NAVIGATION
  // ============================================

  const canNavigateTo = (stepId: number): boolean => {
    if (stepId === 1) return true;
    if (stepId <= currentStep) return true;
    // Can only go forward if current step is complete
    for (let i = 1; i < stepId; i++) {
      if (!completedSteps.includes(i)) return false;
    }
    return true;
  };

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

  const goToStep = (stepId: number) => {
    if (canNavigateTo(stepId)) {
      setError(null);
      setCurrentStep(stepId);
    }
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
        setState(prev => ({ 
          ...prev, 
          property: response.data,
          comparables: [],
          selectedCompIds: [],
        }));
        setCompsFetched(false);
      } else {
        setError(response.error || "Property not found. Please verify the address.");
      }
    } catch (err) {
      console.error("Property search error:", err);
      setError("Failed to search property. Please try again.");
    } finally {
      setSearchLoading(false);
    }
  };

  const clearProperty = () => {
    setState(prev => ({ 
      ...prev, 
      property: null,
      address: "",
      cityStateZip: "",
      comparables: [],
      selectedCompIds: [],
    }));
    setCompsFetched(false);
  };

  // ============================================
  // STEP 2: Fetch Comparables
  // ============================================

  const fetchComparables = async () => {
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
        const normalized: Comparable[] = response.comparables.map((c: any, index: number) => ({
          id: String(c.mls_id || c.listingId || c.mlsId || c.id || `comp-${index}`),
          address: c.address?.full || c.address || "Unknown Address",
          city: c.address?.city || c.city || "",
          price: Number(c.list_price || c.close_price || c.listPrice || c.closePrice || c.price || 0),
          bedrooms: Number(c.property?.bedrooms || c.bedrooms || 0),
          bathrooms: Number(c.property?.bathsFull || c.bathrooms || 0),
          sqft: Number(c.property?.area || c.sqft || 0),
          year_built: c.property?.yearBuilt || c.year_built || null,
          lat: c.geo?.lat || c.lat || null,
          lng: c.geo?.lng || c.lng || null,
          photo_url: c.photos?.[0] || c.photo_url || null,
          distance_miles: c.distance_miles != null ? Number(c.distance_miles) : null,
          status: c.mls?.status || c.status || "Closed",
          days_on_market: c.mls?.daysOnMarket || c.days_on_market || null,
        }));

        setState(prev => ({ ...prev, comparables: normalized }));
        setCompsFetched(true);
      } else {
        setError("No comparables found. Try a different property or location.");
      }
    } catch (err) {
      console.error("Comparables error:", err);
      setError("Failed to fetch comparables");
    } finally {
      setCompsLoading(false);
    }
  };

  // ============================================
  // STEP 3: Theme Change Handler
  // ============================================

  const handleThemeChange = (themeId: number) => {
    const newPages = getDefaultPagesForTheme(themeId as 1 | 2 | 3 | 4 | 5);
    const theme = getThemeById(themeId as 1 | 2 | 3 | 4 | 5);
    setState(prev => ({
      ...prev,
      theme: themeId as 1 | 2 | 3 | 4 | 5,
      accentColor: theme.defaultColor,
      selectedPages: newPages,
    }));
  };

  // ============================================
  // STEP 4: Generate Report
  // ============================================

  const handleGenerate = async () => {
    if (!state.property) return;

    setGenerationState("generating");
    setGenerationStage(0);
    setError(null);

    // Simulate stage progression
    const stageInterval = setInterval(() => {
      setGenerationStage(prev => Math.min(prev + 1, GENERATION_STAGES.length - 1));
    }, 4000);

    try {
      const streetAddress = state.property.street || state.property.full_address.split(",")[0].trim();
      const selectedComparables = state.comparables.filter(c => 
        state.selectedCompIds.includes(c.id)
      );
      
      const response = await apiFetch("/v1/property/reports", {
        method: "POST",
        body: JSON.stringify({
          report_type: "seller",
          theme: state.theme,
          accent_color: state.accentColor,
          property_address: streetAddress,
          property_city: state.property.city,
          property_state: state.property.state,
          property_zip: state.property.zip_code,
          apn: state.property.apn || "",
          owner_name: state.property.owner_name || "",
          selected_comp_ids: state.selectedCompIds,
          comparables: selectedComparables,
          selected_pages: state.selectedPages,
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
        try {
          const statusResponse = await apiFetch(`/v1/property/reports/${reportId}`);

          if (statusResponse.status === "complete") {
            clearInterval(stageInterval);
            setGenerationStage(GENERATION_STAGES.length - 1);
            setTimeout(() => {
              setGenerationState("completed");
              setGeneratedReport({
                id: reportId,
                pdf_url: statusResponse.pdf_url || null,
                qr_code_url: statusResponse.qr_code_url || null,
                short_code: statusResponse.short_code || null,
              });
            }, 500);
            return;
          }

          if (statusResponse.status === "failed" || attempts > 60) {
            clearInterval(stageInterval);
            setGenerationState("failed");
            setError(statusResponse.error_message || "Report generation failed");
            return;
          }

          setTimeout(poll, 2000);
        } catch (pollErr) {
          console.error("Poll error:", pollErr);
          if (attempts < 5) {
            setTimeout(poll, 3000);
          } else {
            clearInterval(stageInterval);
            setGenerationState("failed");
            setError("Connection lost while generating. Check your reports list.");
          }
        }
      };
      poll();
    } catch (err) {
      clearInterval(stageInterval);
      console.error("Generation error:", err);
      setGenerationState("failed");
      setError(err instanceof Error ? err.message : "Failed to generate report");
    }
  };

  const handleRetry = () => {
    setGenerationState("idle");
    setGenerationStage(0);
    setError(null);
  };

  const copyUrl = async () => {
    if (!generatedReport?.short_code) return;
    const url = `https://trendyreports.io/p/${generatedReport.short_code}`;
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // ============================================
  // RENDER - STEP PROGRESS
  // ============================================

  const renderStepProgress = () => (
    <div className="bg-white rounded-xl border border-[var(--border)] p-4 shadow-[var(--shadow-card)]">
      <div className="flex items-center gap-2">
        {STEPS.map((step, index) => {
          const Icon = step.icon;
          const isActive = currentStep === step.id;
          const isComplete = completedSteps.includes(step.id);
          const isLast = index === STEPS.length - 1;

          return (
            <Fragment key={step.id}>
              <button
                onClick={() => canNavigateTo(step.id) && goToStep(step.id)}
                disabled={!canNavigateTo(step.id)}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-lg transition-all duration-200",
                  isActive && "bg-primary/10 ring-1 ring-primary/20",
                  isComplete && !isActive && "hover:bg-muted/50 cursor-pointer",
                  !isActive && !isComplete && "opacity-50 cursor-not-allowed"
                )}
              >
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300",
                  isComplete && "bg-emerald-500 text-white",
                  isActive && !isComplete && "bg-primary text-white",
                  !isActive && !isComplete && "bg-muted text-muted-foreground"
                )}>
                  {isComplete ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    <Icon className="w-4 h-4" />
                  )}
                </div>
                <span className={cn(
                  "text-sm font-medium hidden sm:block",
                  isActive && "text-primary",
                  isComplete && !isActive && "text-foreground",
                  !isActive && !isComplete && "text-muted-foreground"
                )}>
                  {step.name}
                </span>
              </button>

              {!isLast && (
                <div className={cn(
                  "h-px flex-1 transition-colors duration-300",
                  isComplete ? "bg-emerald-300" : "bg-border"
                )} />
              )}
            </Fragment>
          );
        })}
      </div>
    </div>
  );

  // ============================================
  // RENDER - STEP 1: Property Search
  // ============================================

  const renderStep1 = () => (
    <div className="space-y-4">
      {/* Search Card */}
      <div className="bg-white rounded-xl border border-[var(--border)] p-5 shadow-[var(--shadow-card)]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-semibold text-foreground">Find Property</h3>
            <p className="text-sm text-muted-foreground mt-0.5">Search by address to pull property records</p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <Search className="w-5 h-5 text-primary" />
          </div>
        </div>

        <div className="space-y-3">
          <div className="relative">
            <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              ref={addressInputRef}
              type="text"
              placeholder="Enter property address..."
              value={state.address}
              onChange={(e) => setState(prev => ({ ...prev, address: e.target.value }))}
              onKeyDown={(e) => e.key === "Enter" && e.preventDefault()}
              className="w-full pl-10 h-11 text-sm bg-muted/30 border border-border rounded-lg focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none"
              autoComplete="off"
            />
          </div>
          
          <input
            type="text"
            placeholder="City, State ZIP (e.g., Anaheim, CA 92805)"
            value={state.cityStateZip}
            onChange={(e) => setState(prev => ({ ...prev, cityStateZip: e.target.value }))}
            onKeyDown={(e) => e.key === "Enter" && handlePropertySearch()}
            className="w-full px-3 h-11 text-sm bg-muted/30 border border-border rounded-lg focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none"
          />
          
          <p className="text-xs text-muted-foreground">
            {!googleLoaded && !placesError && "Loading address suggestions..."}
            {googleLoaded && !placesError && "Start typing to see suggestions"}
            {placesError && <span className="text-amber-600">{placesError}</span>}
          </p>

          {!state.property && (
            <Button
              onClick={handlePropertySearch}
              disabled={searchLoading || !state.address.trim()}
              className="w-full h-11"
            >
              {searchLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4 mr-2" />
                  Search Property
                </>
              )}
            </Button>
          )}
        </div>
      </div>

      {/* Property Result Card */}
      {state.property && (
        <div className="bg-white rounded-xl border-2 border-emerald-500 overflow-hidden animate-in slide-in-from-bottom-2 duration-300 shadow-[var(--shadow-card)]">
          {/* Success Header */}
          <div className="bg-emerald-50 px-4 py-3 flex items-center justify-between border-b border-emerald-200">
            <div className="flex items-center gap-2 text-emerald-700">
              <CheckCircle2 className="w-5 h-5" />
              <span className="font-semibold text-sm">Property Found</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearProperty}
              className="text-emerald-700 hover:text-emerald-900 hover:bg-emerald-100"
            >
              <X className="w-4 h-4 mr-1" />
              Clear
            </Button>
          </div>

          <div className="p-5">
            {/* Address */}
            <div className="flex items-start gap-4 mb-4">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                <Home className="w-6 h-6 text-primary" />
              </div>
              <div>
                <p className="text-lg font-bold text-foreground">{state.property.full_address}</p>
                <p className="text-sm text-muted-foreground">
                  {state.property.city}, {state.property.state} {state.property.zip_code}
                </p>
              </div>
            </div>

            {/* Key Stats */}
            <div className="grid grid-cols-4 gap-3 mb-4">
              <StatBadge icon={Bed} label="Beds" value={state.property.bedrooms} />
              <StatBadge icon={Bath} label="Baths" value={state.property.bathrooms} />
              <StatBadge icon={Maximize} label="Sqft" value={formatNumber(state.property.sqft)} />
              <StatBadge icon={Calendar} label="Built" value={state.property.year_built} />
            </div>

            {/* Collapsible Details */}
            <Collapsible>
              <CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors w-full pt-3 border-t border-border">
                <ChevronDown className="w-4 h-4" />
                More property details
              </CollapsibleTrigger>
              <CollapsibleContent className="pt-3 mt-3 border-t border-border">
                <div className="grid grid-cols-2 gap-y-3 gap-x-4 text-sm">
                  <DetailRow label="Owner" value={state.property.owner_name} />
                  <DetailRow label="APN" value={state.property.apn} mono />
                  <DetailRow label="Assessed Value" value={formatCurrency(state.property.assessed_value)} />
                  <DetailRow label="Lot Size" value={state.property.lot_size} />
                  <DetailRow label="Property Type" value={state.property.property_type || "Residential"} />
                  {state.property.tax_amount && (
                    <DetailRow label="Annual Taxes" value={formatCurrency(state.property.tax_amount)} />
                  )}
                </div>
              </CollapsibleContent>
            </Collapsible>
          </div>
        </div>
      )}
    </div>
  );

  // ============================================
  // RENDER - STEP 2: Comparables
  // ============================================

  const renderStep2 = () => (
    <div className="space-y-4">
      {/* Header Card */}
      <div className="bg-white rounded-xl border border-[var(--border)] p-5 shadow-[var(--shadow-card)]">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-foreground">Select Comparables</h3>
            <p className="text-sm text-muted-foreground mt-0.5">
              Choose 4-8 comparable properties for your report
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className={cn(
              "text-sm font-medium px-2 py-1 rounded-full",
              state.selectedCompIds.length >= 4 
                ? "bg-emerald-100 text-emerald-700" 
                : "bg-amber-100 text-amber-700"
            )}>
              {state.selectedCompIds.length}/4+ selected
            </span>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {compsLoading && (
        <div className="bg-white rounded-xl border border-[var(--border)] p-12 text-center shadow-[var(--shadow-card)]">
          <Loader2 className="w-10 h-10 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Finding comparable properties...</p>
          <p className="text-sm text-muted-foreground/70 mt-1">
            Searching within 1 mile, ±25% sqft
          </p>
        </div>
      )}

      {/* Comparables Picker */}
      {!compsLoading && state.comparables.length > 0 && (
        <div className="bg-white rounded-xl border border-[var(--border)] p-5 shadow-[var(--shadow-card)]">
          <ComparablesPicker
            availableComps={state.comparables}
            selectedIds={state.selectedCompIds}
            onSelectionChange={(ids) => setState(prev => ({ ...prev, selectedCompIds: ids }))}
            onOpenMap={() => setShowMapModal(true)}
            minSelections={4}
            maxSelections={8}
            subjectProperty={state.property ? {
              bedrooms: state.property.bedrooms,
              bathrooms: state.property.bathrooms,
              sqft: state.property.sqft,
            } : undefined}
            mapDisabled={!state.property?.latitude || !state.property?.longitude}
          />
        </div>
      )}

      {/* No Results */}
      {!compsLoading && compsFetched && state.comparables.length === 0 && (
        <div className="bg-white rounded-xl border border-[var(--border)] p-12 text-center shadow-[var(--shadow-card)]">
          <Map className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <p className="font-medium">No comparables found</p>
          <p className="text-sm text-muted-foreground mt-1">
            Try a different property or expand the search area
          </p>
          <Button
            variant="outline"
            onClick={() => {
              setCompsFetched(false);
              fetchComparables();
            }}
            className="mt-4"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Try Again
          </Button>
        </div>
      )}

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
          comparables={state.comparables}
          selectedIds={state.selectedCompIds}
          onSelectionChange={(ids) => setState(prev => ({ ...prev, selectedCompIds: ids }))}
          maxSelections={8}
        />
      )}
    </div>
  );

  // ============================================
  // RENDER - STEP 3: Theme Selection
  // ============================================

  const renderStep3 = () => {
    const selectedComparables = state.comparables.filter(
      comp => state.selectedCompIds.includes(comp.id)
    );
    
    return (
      <div className="bg-white rounded-xl border border-[var(--border)] p-5 shadow-[var(--shadow-card)]">
        <ThemeSelector
          selectedTheme={state.theme}
          onThemeChange={handleThemeChange}
          accentColor={state.accentColor}
          onAccentColorChange={(color) => setState(prev => ({ ...prev, accentColor: color }))}
          selectedPages={state.selectedPages}
          onPagesChange={(pages) => setState(prev => ({ ...prev, selectedPages: pages }))}
          propertyAddress={state.property?.full_address}
          propertyData={state.property}
          comparables={selectedComparables}
        />
      </div>
    );
  };

  // ============================================
  // RENDER - STEP 4: Generate
  // ============================================

  const renderStep4 = () => {
    const selectedTheme = getThemeById(state.theme);

    // Generating state
    if (generationState === "generating") {
      return (
        <div className="bg-white rounded-xl border border-[var(--border)] p-8 text-center shadow-[var(--shadow-card)]">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
            <Loader2 className="w-8 h-8 text-primary animate-spin" />
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">Generating Your Report</h3>
          
          <div className="max-w-xs mx-auto space-y-2 mt-6 text-left">
            {GENERATION_STAGES.map((stage, i) => {
              const isActive = generationStage === i;
              const isComplete = generationStage > i;
              return (
                <div key={stage} className={cn(
                  "flex items-center gap-3 text-sm transition-all duration-300",
                  isComplete && "text-emerald-600",
                  isActive && "text-foreground font-medium",
                  !isActive && !isComplete && "text-muted-foreground/50"
                )}>
                  {isComplete ? (
                    <Check className="w-4 h-4 text-emerald-500" />
                  ) : isActive ? (
                    <Loader2 className="w-4 h-4 animate-spin text-primary" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-border" />
                  )}
                  {stage}
                </div>
              );
            })}
          </div>
        </div>
      );
    }

    // Completed state
    if (generationState === "completed" && generatedReport) {
      return (
        <div className="bg-white rounded-xl border border-[var(--border)] overflow-hidden shadow-[var(--shadow-card)]">
          {/* Success Header */}
          <div className="bg-gradient-to-r from-emerald-500 to-emerald-600 px-6 py-5 text-white">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                <Check className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-lg">Report Generated!</h3>
                <p className="text-sm text-emerald-100">Your property report is ready to share</p>
              </div>
            </div>
          </div>

          <div className="p-6 space-y-4">
            {/* Action Buttons */}
            <div className="grid grid-cols-2 gap-3">
              {generatedReport.pdf_url && (
                <a
                  href={generatedReport.pdf_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 h-12 border-2 border-border rounded-xl hover:bg-muted transition-colors font-medium"
                >
                  <Download className="w-4 h-4" />
                  Download PDF
                </a>
              )}
              <Button 
                className="h-12 bg-primary"
                onClick={() => router.push("/app/property")}
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                View All Reports
              </Button>
            </div>

            {/* QR Code + Short URL */}
            {generatedReport.short_code && (
              <div className="flex items-center gap-4 pt-4 border-t border-border">
                {generatedReport.qr_code_url && (
                  <img 
                    src={generatedReport.qr_code_url} 
                    alt="QR Code" 
                    className="w-20 h-20 rounded-lg border border-border" 
                  />
                )}
                <div className="flex-1">
                  <p className="text-sm font-medium text-foreground mb-1">Share Link</p>
                  <div className="flex items-center gap-2">
                    <code className="text-xs bg-muted px-3 py-1.5 rounded-md flex-1 truncate">
                      trendyreports.io/p/{generatedReport.short_code}
                    </code>
                    <Button variant="outline" size="sm" onClick={copyUrl}>
                      {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Create Another */}
            <Button
              variant="outline"
              className="w-full"
              onClick={() => {
                setState(initialState);
                setCurrentStep(1);
                setGenerationState("idle");
                setGeneratedReport(null);
                setCompsFetched(false);
              }}
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Create Another Report
            </Button>
          </div>
        </div>
      );
    }

    // Failed state
    if (generationState === "failed") {
      return (
        <div className="bg-white rounded-xl border border-destructive/20 p-6 text-center shadow-[var(--shadow-card)]">
          <div className="w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-3">
            <AlertCircle className="w-6 h-6 text-destructive" />
          </div>
          <h3 className="font-semibold text-foreground mb-1">Generation Failed</h3>
          <p className="text-sm text-muted-foreground mb-4">
            {error || "Something went wrong. Please try again."}
          </p>
          <Button onClick={handleRetry} variant="outline">
            <RotateCcw className="w-4 h-4 mr-2" />
            Try Again
          </Button>
        </div>
      );
    }

    // Review state (idle)
    return (
      <div className="space-y-4">
        {/* Summary Card */}
        <div className="bg-white rounded-xl border border-[var(--border)] p-5 shadow-[var(--shadow-card)]">
          <h3 className="text-base font-semibold text-foreground mb-4">Report Summary</h3>
          
          <div className="space-y-3">
            <SummaryRow 
              icon={Home} 
              label="Property" 
              value={state.property?.full_address || ""}
              action={<Button variant="ghost" size="sm" onClick={() => goToStep(1)}>Edit</Button>}
            />
            <SummaryRow 
              icon={BarChart3} 
              label="Comparables" 
              value={`${state.selectedCompIds.length} properties selected`}
              action={<Button variant="ghost" size="sm" onClick={() => goToStep(2)}>Edit</Button>}
            />
            <SummaryRow 
              icon={Palette} 
              label="Theme" 
              value={selectedTheme.name}
              extra={
                <div 
                  className="w-4 h-4 rounded-full border border-border" 
                  style={{ backgroundColor: state.accentColor }}
                />
              }
              action={<Button variant="ghost" size="sm" onClick={() => goToStep(3)}>Edit</Button>}
            />
            <SummaryRow 
              icon={FileText} 
              label="Pages" 
              value={`${state.selectedPages.length} pages included`}
            />
          </div>
        </div>

        {/* Generate CTA */}
        <div className="bg-gradient-to-br from-primary/5 to-amber-500/5 rounded-xl border border-primary/10 p-6 text-center">
          <Sparkles className="w-8 h-8 text-primary mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-foreground mb-1">Ready to Generate</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Your property report will be ready in about 30 seconds
          </p>
          <Button 
            onClick={handleGenerate}
            size="lg"
            className="bg-primary text-white hover:bg-primary/90 px-8"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            Generate Report
          </Button>
        </div>
      </div>
    );
  };

  // ============================================
  // RENDER - PREVIEW PANEL
  // ============================================

  const renderPreviewPanel = () => {
    const selectedTheme = getThemeById(state.theme);
    
    return (
      <div className="bg-white rounded-xl border border-[var(--border)] overflow-hidden shadow-[var(--shadow-card)]">
        {/* Preview Header */}
        <div className="px-5 py-3 border-b border-border flex items-center justify-between bg-muted/30">
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium text-foreground">Preview</span>
          </div>
          <span className="text-xs text-muted-foreground">Updates as you build</span>
        </div>

        {/* Preview Content */}
        <div className="p-5">
          {/* Mini Report Cover */}
          <div 
            className="aspect-[8.5/11] rounded-lg overflow-hidden shadow-lg mx-auto max-w-[240px] transition-all duration-500"
            style={{ background: THEME_GRADIENTS[state.theme] || THEME_GRADIENTS[5] }}
          >
            <div className="h-full p-5 flex flex-col justify-between text-white">
              {/* Top */}
              <div>
                <div className="text-[8px] uppercase tracking-widest text-white/60 mb-1">
                  Property Report
                </div>
                <div className="text-xs font-bold leading-tight">
                  {state.property?.full_address || 'Select a Property'}
                </div>
                <div className="text-[7px] text-white/70 mt-0.5">
                  {state.property?.city || 'City'}, {state.property?.state || 'ST'}
                </div>
              </div>

              {/* Middle: Stats */}
              {state.property && (
                <div className="flex gap-1.5 flex-wrap">
                  {state.property.bedrooms && (
                    <div className="bg-white/10 rounded px-1.5 py-0.5 text-[6px]">
                      {state.property.bedrooms} BD
                    </div>
                  )}
                  {state.property.bathrooms && (
                    <div className="bg-white/10 rounded px-1.5 py-0.5 text-[6px]">
                      {state.property.bathrooms} BA
                    </div>
                  )}
                  {state.property.sqft && (
                    <div className="bg-white/10 rounded px-1.5 py-0.5 text-[6px]">
                      {formatNumber(state.property.sqft)} SF
                    </div>
                  )}
                </div>
              )}

              {/* Bottom */}
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-white/20" />
                <div>
                  <div className="text-[7px] font-semibold">Your Name</div>
                  <div className="text-[5px] text-white/60">Company</div>
                </div>
              </div>
            </div>
          </div>

          {/* Details Under Preview */}
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-muted/50 rounded-full text-xs text-muted-foreground">
              <Palette className="w-3 h-3" />
              {selectedTheme.name}
            </div>
            {state.selectedCompIds.length > 0 && (
              <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-muted/50 rounded-full text-xs text-muted-foreground">
                <BarChart3 className="w-3 h-3" />
                {state.selectedCompIds.length} Comps
              </div>
            )}
          </div>

          {/* Page Thumbnails */}
          {currentStep >= 3 && state.selectedPages.length > 0 && (
            <div className="mt-4 pt-4 border-t border-border">
              <p className="text-xs text-muted-foreground mb-2 text-center">
                {state.selectedPages.length} pages
              </p>
              <div className="grid grid-cols-5 gap-1">
                {state.selectedPages.slice(0, 10).map((pageId, i) => (
                  <div 
                    key={pageId}
                    className="aspect-[8.5/11] bg-muted/50 rounded border border-border flex items-center justify-center"
                  >
                    <span className="text-[6px] text-muted-foreground font-medium">{i + 1}</span>
                  </div>
                ))}
                {state.selectedPages.length > 10 && (
                  <div className="aspect-[8.5/11] bg-muted/30 rounded border border-dashed border-border flex items-center justify-center">
                    <span className="text-[6px] text-muted-foreground">+{state.selectedPages.length - 10}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  // ============================================
  // RENDER - NAVIGATION
  // ============================================

  const renderNavigation = () => {
    if (currentStep === 4 && generationState !== 'idle') return null;

    return (
      <div className="flex items-center justify-between pt-2">
        <Button
          variant="ghost"
          onClick={handleBack}
          disabled={currentStep === 1}
          className="text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        
        {currentStep < STEPS.length && (
          <Button
            onClick={handleNext}
            disabled={!validateStep(state, currentStep).valid}
            className="bg-primary text-white hover:bg-primary/90 min-w-[120px]"
          >
            Continue
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        )}
      </div>
    );
  };

  // ============================================
  // MAIN RENDER
  // ============================================

  return (
    <div className="min-h-screen bg-[var(--background)]">
      {/* Sticky Header */}
      <header className="sticky top-0 z-10 bg-white/80 backdrop-blur-md border-b border-[var(--border)] px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/app/property" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
              <ArrowLeft className="w-4 h-4" />
              <span className="hidden sm:inline">Property Reports</span>
            </Link>
            <div className="h-4 w-px bg-border" />
            <h1 className="text-sm font-semibold text-foreground">New Property Report</h1>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/app/property">
              <Button variant="outline" size="sm">Cancel</Button>
            </Link>
            {currentStep === 4 && generationState === 'idle' && (
              <Button 
                onClick={handleGenerate}
                disabled={!validateStep(state, 4).valid}
                size="sm"
                className="bg-primary text-white hover:bg-primary/90"
              >
                <Sparkles className="w-4 h-4 mr-2" />
                Generate Report
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(400px,520px)_1fr] gap-8">
          {/* Left: Steps Panel */}
          <div className="space-y-5">
            {/* Step Progress */}
            {renderStepProgress()}
            
            {/* Error */}
            {error && (
              <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-3">
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}
            
            {/* Active Step Content */}
            <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
              {currentStep === 1 && renderStep1()}
              {currentStep === 2 && renderStep2()}
              {currentStep === 3 && renderStep3()}
              {currentStep === 4 && renderStep4()}
            </div>
            
            {/* Navigation */}
            {renderNavigation()}
          </div>

          {/* Right: Live Preview - Hidden on mobile, sticky on desktop */}
          <div className="hidden lg:block">
            <div className="sticky top-24 self-start">
              {renderPreviewPanel()}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

// ============================================
// HELPER COMPONENTS
// ============================================

function StatBadge({ icon: Icon, label, value }: { icon: any; label: string; value: string | number | null | undefined }) {
  return (
    <div className="text-center">
      <div className="w-9 h-9 rounded-lg bg-muted/50 flex items-center justify-center mx-auto mb-1.5">
        <Icon className="w-4 h-4 text-muted-foreground" />
      </div>
      <div className="text-sm font-semibold text-foreground">{value ?? '—'}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

function DetailRow({ label, value, mono }: { label: string; value: string | number | null | undefined; mono?: boolean }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={cn("text-sm font-medium", mono && "font-mono")}>{value || "—"}</p>
    </div>
  );
}

function SummaryRow({ 
  icon: Icon, 
  label, 
  value, 
  extra, 
  action 
}: { 
  icon: any; 
  label: string; 
  value: string; 
  extra?: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border last:border-0">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-muted/50 flex items-center justify-center">
          <Icon className="w-4 h-4 text-muted-foreground" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">{label}</p>
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium text-foreground">{value}</p>
            {extra}
          </div>
        </div>
      </div>
      {action}
    </div>
  );
}

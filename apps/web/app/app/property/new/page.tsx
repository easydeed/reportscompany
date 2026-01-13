"use client";

import { useState, useEffect, useRef, useCallback } from "react";
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
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api";

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
  theme: 1,
  accentColor: "#0d294b",
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
  const [compsFetched, setCompsFetched] = useState(false);
  
  // Generation state
  const [generationState, setGenerationState] = useState<"idle" | "generating" | "completed" | "failed">("idle");
  const [generatedReport, setGeneratedReport] = useState<{ 
    id: string; 
    pdf_url: string | null;
    qr_code_url: string | null;
    short_code: string | null;
  } | null>(null);

  // Map modal
  const [showMapModal, setShowMapModal] = useState(false);

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

    // Update input value after Google manipulates it
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
        setState(prev => ({ 
          ...prev, 
          property: response.data,
          // Reset comparables when property changes
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
    setError(null);

    try {
      // Use street address (not full_address which includes city/state/zip)
      const streetAddress = state.property.street || state.property.full_address.split(",")[0].trim();
      
      // Get the full comparable objects for the selected IDs
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
          comparables: selectedComparables,  // Send full comparable objects
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
            setGenerationState("completed");
            setGeneratedReport({
              id: reportId,
              pdf_url: statusResponse.pdf_url || null,
              qr_code_url: statusResponse.qr_code_url || null,
              short_code: statusResponse.short_code || null,
            });
            return;
          }

          if (statusResponse.status === "failed" || attempts > 60) {
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
            setGenerationState("failed");
            setError("Connection lost while generating. Check your reports list.");
          }
        }
      };
      poll();
    } catch (err) {
      console.error("Generation error:", err);
      setGenerationState("failed");
      setError(err instanceof Error ? err.message : "Failed to generate report");
    }
  };

  // ============================================
  // HELPER: Format Currency
  // ============================================

  const formatCurrency = (value: number | null | undefined): string => {
    if (value == null) return "N/A";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(value);
  };

  // ============================================
  // RENDER - STEP 1: Property Search
  // ============================================

  const renderStep1 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-2">Find Your Property</h2>
        <p className="text-muted-foreground">
          Enter the property address. We&apos;ll pull all the details from public records.
        </p>
      </div>

      {/* Search Form */}
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="address">Property Address</Label>
          <div className="relative">
            <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <input
              ref={addressInputRef}
              id="address"
              type="text"
              placeholder="Start typing an address..."
              value={state.address}
              onChange={(e) => setState(prev => ({ ...prev, address: e.target.value }))}
              onKeyDown={(e) => e.key === "Enter" && e.preventDefault()}
              className="w-full pl-10 pr-4 py-3 rounded-lg border bg-background text-base"
              autoComplete="off"
            />
          </div>
          <p className="text-xs text-muted-foreground">
            {!googleLoaded && !placesError && "Loading address suggestions..."}
            {googleLoaded && !placesError && "Start typing to see suggestions"}
            {placesError && <span className="text-amber-600">{placesError}</span>}
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="cityStateZip">City, State ZIP</Label>
          <input
            id="cityStateZip"
            type="text"
            placeholder="e.g., Anaheim, CA 92805"
            value={state.cityStateZip}
            onChange={(e) => setState(prev => ({ ...prev, cityStateZip: e.target.value }))}
            onKeyDown={(e) => e.key === "Enter" && handlePropertySearch()}
            className="w-full px-4 py-3 rounded-lg border bg-background"
          />
        </div>

        {/* Search Button - Only show when no property selected */}
        {!state.property && (
          <Button
            onClick={handlePropertySearch}
            disabled={searchLoading || !state.address.trim()}
            className="w-full py-6 text-base"
          >
            {searchLoading ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Search className="w-5 h-5 mr-2" />
                Search Property
              </>
            )}
          </Button>
        )}
      </div>

      {/* Property Result Card - Full SiteX Details */}
      {state.property && (
        <div className="border-2 border-green-500 rounded-xl overflow-hidden">
          {/* Success Header */}
          <div className="bg-green-50 dark:bg-green-950/30 px-4 py-3 flex items-center justify-between border-b border-green-200">
            <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
              <CheckCircle2 className="w-5 h-5" />
              <span className="font-semibold">Property Found</span>
            </div>
            <button
              onClick={() => {
                setState(prev => ({ 
                  ...prev, 
                  property: null,
                  comparables: [],
                  selectedCompIds: [],
                }));
                setCompsFetched(false);
              }}
              className="text-sm text-green-700 hover:text-green-900 hover:underline"
            >
              Search Different Property
            </button>
          </div>

          <div className="p-5 space-y-5">
            {/* Address */}
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                <Home className="w-6 h-6 text-primary" />
              </div>
              <div>
                <p className="text-xl font-bold">{state.property.full_address}</p>
                <p className="text-muted-foreground">
                  {state.property.city}, {state.property.state} {state.property.zip_code}
                </p>
                {state.property.county && (
                  <p className="text-sm text-muted-foreground">{state.property.county} County</p>
                )}
              </div>
            </div>

            {/* Key Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-muted/50 rounded-lg p-3">
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Beds</p>
                <p className="text-lg font-bold">{state.property.bedrooms ?? "N/A"}</p>
              </div>
              <div className="bg-muted/50 rounded-lg p-3">
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Baths</p>
                <p className="text-lg font-bold">{state.property.bathrooms ?? "N/A"}</p>
              </div>
              <div className="bg-muted/50 rounded-lg p-3">
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Sqft</p>
                <p className="text-lg font-bold">{state.property.sqft?.toLocaleString() ?? "N/A"}</p>
              </div>
              <div className="bg-muted/50 rounded-lg p-3">
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Year Built</p>
                <p className="text-lg font-bold">{state.property.year_built || "N/A"}</p>
              </div>
            </div>

            {/* Additional Details */}
            <div className="grid md:grid-cols-3 gap-4 pt-4 border-t">
              <div className="flex items-start gap-3">
                <User className="w-4 h-4 text-muted-foreground mt-1" />
                <div>
                  <p className="text-xs text-muted-foreground uppercase">Owner</p>
                  <p className="font-medium">{state.property.owner_name || "Not available"}</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <FileText className="w-4 h-4 text-muted-foreground mt-1" />
                <div>
                  <p className="text-xs text-muted-foreground uppercase">APN</p>
                  <p className="font-medium font-mono text-sm">{state.property.apn || "N/A"}</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <DollarSign className="w-4 h-4 text-muted-foreground mt-1" />
                <div>
                  <p className="text-xs text-muted-foreground uppercase">Assessed Value</p>
                  <p className="font-medium">{formatCurrency(state.property.assessed_value)}</p>
                </div>
              </div>
            </div>

            {/* Property Type & Lot */}
            <div className="grid md:grid-cols-2 gap-4 pt-4 border-t">
              <div className="flex items-start gap-3">
                <Building className="w-4 h-4 text-muted-foreground mt-1" />
                <div>
                  <p className="text-xs text-muted-foreground uppercase">Property Type</p>
                  <p className="font-medium">{state.property.property_type || "Residential"}</p>
                </div>
              </div>
              {state.property.lot_size && (
                <div className="flex items-start gap-3">
                  <MapPin className="w-4 h-4 text-muted-foreground mt-1" />
                  <div>
                    <p className="text-xs text-muted-foreground uppercase">Lot Size</p>
                    <p className="font-medium">{state.property.lot_size}</p>
                  </div>
                </div>
              )}
            </div>

            {/* Tax Info */}
            {state.property.tax_amount && (
              <div className="pt-4 border-t">
                <div className="flex items-start gap-3">
                  <Calendar className="w-4 h-4 text-muted-foreground mt-1" />
                  <div>
                    <p className="text-xs text-muted-foreground uppercase">Annual Taxes</p>
                    <p className="font-medium">{formatCurrency(state.property.tax_amount)}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );

  // ============================================
  // RENDER - STEP 2: Comparables
  // ============================================

  const renderStep2 = () => {
    const selectedCount = state.selectedCompIds.length;
    
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold mb-2">Select Comparables</h2>
          <p className="text-muted-foreground">
            Choose 4-8 comparable properties for your report
          </p>
        </div>

        {/* Loading State */}
        {compsLoading && (
          <div className="text-center py-12">
            <Loader2 className="w-10 h-10 animate-spin text-primary mx-auto mb-4" />
            <p className="text-muted-foreground">Finding comparable properties...</p>
            <p className="text-sm text-muted-foreground/70 mt-1">
              Searching within 1 mile, ±25% sqft
            </p>
          </div>
        )}

        {/* Comparables Picker */}
        {!compsLoading && state.comparables.length > 0 && (
          <>
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

            {/* Info bar */}
            <div className="text-sm text-muted-foreground flex items-center justify-between border-t pt-4">
              <span>
                Found {state.comparables.length} properties within search area
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setCompsFetched(false);
                  fetchComparables();
                }}
              >
                Refresh Search
              </Button>
            </div>
          </>
        )}

        {/* No Results */}
        {!compsLoading && compsFetched && state.comparables.length === 0 && (
          <div className="text-center py-12">
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
  };

  // ============================================
  // RENDER - STEP 3: Theme Selection
  // ============================================

  const renderStep3 = () => (
    <div className="space-y-6">
      <ThemeSelector
        selectedTheme={state.theme}
        onThemeChange={handleThemeChange}
        accentColor={state.accentColor}
        onAccentColorChange={(color) => setState(prev => ({ ...prev, accentColor: color }))}
        selectedPages={state.selectedPages}
        onPagesChange={(pages) => setState(prev => ({ ...prev, selectedPages: pages }))}
        propertyAddress={state.property?.full_address}
      />
    </div>
  );

  // ============================================
  // RENDER - STEP 4: Review & Generate
  // ============================================

  const renderStep4 = () => {
    const propertyAddress = state.property?.full_address || "Unknown";
    const propertyLocation = state.property 
      ? `${state.property.city}, ${state.property.state} ${state.property.zip_code}`
      : "";
    const selectedTheme = getThemeById(state.theme);
    const pageCount = state.selectedPages.length;
    const compCount = state.selectedCompIds.length;

    // Generating state
    if (generationState === "generating") {
      return (
        <div className="text-center py-16">
          <div className="relative inline-block mb-6">
            <div className="w-24 h-24 rounded-full border-4 border-primary/20" />
            <div className="absolute inset-0 w-24 h-24 rounded-full border-4 border-transparent border-t-primary animate-spin" />
            <div className="absolute inset-0 flex items-center justify-center">
              <FileText className="w-8 h-8 text-primary" />
            </div>
          </div>
          <h3 className="text-xl font-semibold mb-2">Generating Your Report</h3>
          <p className="text-muted-foreground">This usually takes 15-30 seconds...</p>
          <div className="mt-6 max-w-xs mx-auto">
            <Progress value={33} className="h-2" />
          </div>
        </div>
      );
    }

    // Success state
    if (generationState === "completed" && generatedReport) {
      return (
        <div className="text-center py-12">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 className="w-10 h-10 text-green-600" />
          </div>
          <h3 className="text-2xl font-bold mb-2">Report Ready!</h3>
          <p className="text-muted-foreground mb-8">
            Your seller report for {propertyAddress} is complete
          </p>

          {/* Download & View Actions */}
          <div className="grid sm:grid-cols-2 gap-4 max-w-lg mx-auto mb-8">
            {generatedReport.pdf_url && (
              <a
                href={generatedReport.pdf_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 px-6 py-4 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-colors"
              >
                <Download className="w-5 h-5" />
                Download PDF
              </a>
            )}
            {generatedReport.qr_code_url && (
              <a
                href={generatedReport.qr_code_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 px-6 py-4 border-2 border-border rounded-xl hover:bg-muted transition-colors"
              >
                <QrCode className="w-5 h-5" />
                View QR Code
              </a>
            )}
          </div>

          {/* Landing Page Link */}
          {generatedReport.short_code && (
            <div className="p-4 bg-muted/50 rounded-xl max-w-md mx-auto mb-8">
              <p className="text-sm text-muted-foreground mb-2">Public Landing Page:</p>
              <a
                href={`https://trendyreports.io/p/${generatedReport.short_code}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-primary hover:underline font-medium"
              >
                trendyreports.io/p/{generatedReport.short_code}
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Button variant="outline" onClick={() => router.push("/app/property")}>
              View All Reports
            </Button>
            <Button onClick={() => {
              setState(initialState);
              setCurrentStep(1);
              setGenerationState("idle");
              setGeneratedReport(null);
              setCompsFetched(false);
            }}>
              Create Another Report
            </Button>
          </div>
        </div>
      );
    }

    // Failed state
    if (generationState === "failed") {
      return (
        <div className="text-center py-12">
          <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <XCircle className="w-10 h-10 text-red-600" />
          </div>
          <h3 className="text-xl font-semibold mb-2">Generation Failed</h3>
          <p className="text-red-600 mb-6">{error || "An error occurred"}</p>
          <div className="flex justify-center gap-4">
            <Button variant="outline" onClick={() => router.push("/app/property")}>
              View Reports
            </Button>
            <Button onClick={() => setGenerationState("idle")}>
              Try Again
            </Button>
          </div>
        </div>
      );
    }

    // Review state (idle)
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold mb-2">Review & Generate</h2>
          <p className="text-muted-foreground">
            Review your selections before generating the report
          </p>
        </div>

        {/* Summary Card */}
        <div className="border-2 rounded-xl overflow-hidden">
          {/* Header */}
          <div className="p-4 border-b bg-muted/30 flex items-center gap-4">
            <div 
              className="w-14 h-14 rounded-xl flex items-center justify-center"
              style={{ backgroundColor: state.accentColor }}
            >
              <FileText className="w-7 h-7 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-lg">Seller Report</h3>
              <p className="text-sm text-muted-foreground">{selectedTheme.name} Theme</p>
            </div>
          </div>

          {/* Details Grid */}
          <div className="p-5 space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              {/* Property */}
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Property</p>
                <p className="font-semibold">{propertyAddress}</p>
                <p className="text-sm text-muted-foreground">{propertyLocation}</p>
              </div>

              {/* Configuration */}
              <div className="space-y-2">
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Configuration</p>
                <div className="flex flex-wrap gap-2">
                  <span className="px-2 py-1 bg-muted rounded text-sm">
                    {compCount} Comparables
                  </span>
                  <span className="px-2 py-1 bg-muted rounded text-sm">
                    {pageCount} Pages
                  </span>
                  <span 
                    className="px-2 py-1 rounded text-sm text-white"
                    style={{ backgroundColor: state.accentColor }}
                  >
                    {selectedTheme.name}
                  </span>
                </div>
              </div>
            </div>

            {/* Selected Pages Preview */}
            <div className="pt-4 border-t">
              <p className="text-xs text-muted-foreground uppercase tracking-wide mb-2">Pages Included</p>
              <div className="flex flex-wrap gap-1">
                {state.selectedPages.slice(0, 10).map((pageId) => {
                  const page = ALL_PAGES.find(p => p.id === pageId);
                  return (
                    <span key={pageId} className="px-2 py-0.5 bg-muted/50 rounded text-xs">
                      {page?.name || pageId}
                    </span>
                  );
                })}
                {state.selectedPages.length > 10 && (
                  <span className="px-2 py-0.5 bg-muted/50 rounded text-xs">
                    +{state.selectedPages.length - 10} more
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Generate Button */}
        <Button
          onClick={handleGenerate}
          className="w-full py-6 text-lg bg-green-600 hover:bg-green-700"
        >
          <FileText className="w-5 h-5 mr-2" />
          Generate Report
        </Button>

        <p className="text-xs text-center text-muted-foreground">
          Generation typically takes 15-30 seconds
        </p>
      </div>
    );
  };

  // ============================================
  // MAIN RENDER
  // ============================================

  const progressPercent = (currentStep / STEPS.length) * 100;

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
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
                    ${isComplete ? "bg-primary border-primary text-primary-foreground" : ""}
                    ${isActive ? "border-primary bg-primary/10" : ""}
                    ${!isActive && !isComplete ? "border-muted-foreground/30 bg-muted/30" : ""}
                  `}
                >
                  {isComplete ? <Check className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                </div>
                <span className={`text-xs font-medium hidden sm:block ${isActive || isComplete ? "text-foreground" : "text-muted-foreground"}`}>
                  {step.name}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400">
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

      {/* Navigation - Hide during generation */}
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

          {currentStep < STEPS.length && (
            <Button onClick={handleNext} className="gap-2">
              Continue
              <ArrowRight className="w-4 h-4" />
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

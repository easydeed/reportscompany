"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useGooglePlaces, PlaceResult } from "@/hooks/useGooglePlaces";
import {
  ArrowLeft,
  ArrowRight,
  Search,
  Check,
  Home,
  MapPin,
  Palette,
  FileText,
  Loader2,
  Plus,
  Minus,
  Map,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { apiFetch } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ComparablesMapModal, ComparablesPicker, ThemeSelector } from "@/components/property";

// Types
interface PropertyData {
  full_address: string;
  street: string;
  city: string;
  state: string;
  zip_code: string;
  county: string;
  apn: string;
  owner_name: string;
  legal_description: string;
  bedrooms: number | null;
  bathrooms: number | null;
  sqft: number | null;
  lot_size: number | null;
  year_built: number | null;
  property_type: string;
  assessed_value: number | null;
  latitude?: number;
  longitude?: number;
}

interface Comparable {
  mlsId: string;
  address: {
    full: string;
    city: string;
    state: string;
  };
  listPrice: number;
  property: {
    bedrooms: number;
    bathrooms: number;
    area: number;
    yearBuilt: number;
  };
  geo?: {
    lat: number;
    lng: number;
  };
  photos?: string[];
  distance?: number;
}

interface SearchParams {
  radius_miles: number;
  sqft_variance: number;
  sqft_range?: { min: number; max: number };
  beds_range?: { min: number; max: number };
  total_before_filter?: number;
}

interface WizardState {
  step: number;
  address: string;
  cityStateZip: string;
  property: PropertyData | null;
  availableComps: Comparable[];
  selectedComps: Comparable[];
  theme: number;
  accentColor: string;
  selectedPages: string[];
  // Search filters
  radiusMiles: number;
  sqftVariance: number;
  searchParams?: SearchParams;
}

const STEPS = [
  { id: 1, title: "Find Property", icon: Search },
  { id: 2, title: "Select Comparables", icon: MapPin },
  { id: 3, title: "Choose Theme", icon: Palette },
  { id: 4, title: "Review & Generate", icon: FileText },
];

// Theme names for review step display
const THEME_NAMES: Record<number, string> = {
  1: "Classic",
  2: "Modern",
  3: "Elegant",
  4: "Teal",
  5: "Bold",
};

// All available pages for review display
const ALL_PAGES = [
  { id: "cover", name: "Cover" },
  { id: "contents", name: "Table of Contents" },
  { id: "introduction", name: "Introduction" },
  { id: "aerial", name: "Aerial View" },
  { id: "property_details", name: "Property Details" },
  { id: "area_analysis", name: "Area Sales Analysis" },
  { id: "comparables", name: "Sales Comparables" },
  { id: "range_of_sales", name: "Range of Sales" },
  { id: "neighborhood", name: "Neighborhood Stats" },
  { id: "roadmap", name: "Selling Roadmap" },
  { id: "how_buyers_find", name: "How Buyers Find Homes" },
  { id: "pricing_correctly", name: "Pricing Strategy" },
  { id: "avg_days_market", name: "Days on Market" },
  { id: "marketing_online", name: "Digital Marketing" },
  { id: "marketing_print", name: "Print Marketing" },
  { id: "marketing_social", name: "Social Media" },
  { id: "analyze_optimize", name: "Analyze & Optimize" },
  { id: "negotiating", name: "Negotiating Offers" },
  { id: "typical_transaction", name: "Transaction Timeline" },
  { id: "promise", name: "Agent Promise" },
  { id: "back_cover", name: "Back Cover" },
];

// Initial wizard state for reset
const initialWizardState: WizardState = {
  step: 1,
  address: "",
  cityStateZip: "",
  property: null,
  availableComps: [],
  selectedComps: [],
  theme: 1,
  accentColor: "#0d294b",
  selectedPages: [],
  radiusMiles: 0.5,
  sqftVariance: 0.20,
  searchParams: undefined,
};

export default function NewPropertyReportPage() {
  const router = useRouter();
  const [state, setState] = useState<WizardState>({
    step: 1,
    address: "",
    cityStateZip: "",
    property: null,
    availableComps: [],
    selectedComps: [],
    theme: 1,
    accentColor: "#0d294b",
    selectedPages: [],
    // Search filter defaults
    radiusMiles: 0.5,
    sqftVariance: 0.20,
    searchParams: undefined,
  });

  const [searching, setSearching] = useState(false);
  const [loadingComps, setLoadingComps] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [generatedReport, setGeneratedReport] = useState<{
    id: string;
    pdf_url: string;
    qr_code_url: string;
    short_code: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mapModalOpen, setMapModalOpen] = useState(false);
  const [showParamsModal, setShowParamsModal] = useState(false);

  // Google Places autocomplete
  const addressInputRef = useRef<HTMLInputElement>(null);
  const searchTriggerRef = useRef<boolean>(false);
  
  // Handle place selection from Google Places autocomplete
  const handlePlaceSelect = useCallback((place: PlaceResult) => {
    setState((prev) => ({
      ...prev,
      address: place.address,
      cityStateZip: `${place.city}, ${place.state} ${place.zip}`,
    }));
    // Set flag to trigger search after state updates
    searchTriggerRef.current = true;
  }, []);

  const { place, isLoaded: googleMapsLoaded } = useGooglePlaces(addressInputRef, {
    onPlaceSelect: handlePlaceSelect,
  });

  // Auto-trigger property search when place is selected
  useEffect(() => {
    if (searchTriggerRef.current && state.address && state.cityStateZip) {
      searchTriggerRef.current = false;
      handleSearchPropertyInternal(state.address, state.cityStateZip);
    }
  }, [state.address, state.cityStateZip]);

  // Internal search function that takes address params directly
  const handleSearchPropertyInternal = async (address: string, cityStateZip: string) => {
    if (!address.trim() || !cityStateZip.trim()) {
      setError("Please enter both address and city/state/zip");
      return;
    }

    setSearching(true);
    setError(null);

    try {
      const response = await apiFetch("/v1/property/search", {
        method: "POST",
        body: JSON.stringify({
          address: address.trim(),
          city_state_zip: cityStateZip.trim(),
        }),
      });

      if (response.success && response.data) {
        setState((prev) => ({ ...prev, property: response.data }));
      } else if (response.multiple_matches && response.multiple_matches.length > 0) {
        setError(`Multiple properties found (${response.multiple_matches.length}). Please be more specific with the address.`);
      } else {
        setError(response.error || "Property not found. Please verify the address.");
      }
    } catch (e: any) {
      console.error("Property search error:", e);
      setError(e.message || "Failed to search property. Please try again.");
    } finally {
      setSearching(false);
    }
  };

  // Step 1: Search Property (called from button click)
  const handleSearchProperty = async () => {
    if (!state.address.trim() || !state.cityStateZip.trim()) {
      setError("Please enter both address and city/state/zip");
      return;
    }

    setSearching(true);
    setError(null);

    try {
      const response = await apiFetch("/v1/property/search", {
        method: "POST",
        body: JSON.stringify({
          address: state.address.trim(),
          city_state_zip: state.cityStateZip.trim(),
        }),
      });

      // API returns { success: boolean, data: PropertyData, error?: string }
      if (response.success && response.data) {
        setState((prev) => ({ ...prev, property: response.data }));
      } else if (response.multiple_matches && response.multiple_matches.length > 0) {
        // Handle multiple property matches
        setError(`Multiple properties found (${response.multiple_matches.length}). Please be more specific with the address.`);
      } else {
        setError(response.error || "Property not found. Please verify the address.");
      }
    } catch (e: any) {
      console.error("Property search error:", e);
      setError(e.message || "Failed to search property. Please try again.");
    } finally {
      setSearching(false);
    }
  };

  // Step 2: Load Comparables
  const loadComparables = async (radiusMiles?: number, sqftVariance?: number) => {
    if (!state.property) return;

    // Use provided values or current state values
    const radius = radiusMiles ?? state.radiusMiles;
    const variance = sqftVariance ?? state.sqftVariance;

    setLoadingComps(true);
    setError(null);

    try {
      const response = await apiFetch("/v1/property/comparables", {
        method: "POST",
        body: JSON.stringify({
          address: state.property.full_address,
          city_state_zip: `${state.property.city}, ${state.property.state} ${state.property.zip_code}`,
          // Pass subject property characteristics for better filtering
          latitude: state.property.latitude,
          longitude: state.property.longitude,
          beds: state.property.bedrooms,
          baths: state.property.bathrooms,
          sqft: state.property.sqft,
          property_type: state.property.property_type,
          // Search filters
          radius_miles: radius,
          sqft_variance: variance,
          status: "Closed",
          limit: 20,
        }),
      });

      // API returns { success, subject_property, comparables, search_params, total_found, error }
      // Transform API response to match frontend Comparable interface
      if (response.success && response.comparables) {
        const transformedComps: Comparable[] = response.comparables.map((comp: any) => ({
          mlsId: comp.mls_id,
          address: {
            full: comp.address,
            city: comp.city,
            state: comp.state,
          },
          listPrice: comp.list_price || comp.close_price || 0,
          property: {
            bedrooms: comp.bedrooms || 0,
            bathrooms: comp.bathrooms || 0,
            area: comp.sqft || 0,
            yearBuilt: comp.year_built || 0,
          },
          geo: comp.lat && comp.lng ? { lat: comp.lat, lng: comp.lng } : undefined,
          photos: comp.photo_url ? [comp.photo_url] : [],
          distance: comp.distance_miles,
        }));

        setState((prev) => ({
          ...prev,
          availableComps: transformedComps,
          selectedComps: [],
          radiusMiles: radius,
          sqftVariance: variance,
          searchParams: response.search_params,
        }));

        // Show adjustment modal if < 4 comps found
        if (transformedComps.length < 4 && transformedComps.length > 0) {
          setShowParamsModal(true);
        } else if (transformedComps.length === 0) {
          setShowParamsModal(true);
          setError("No comparable properties found. Try expanding the search radius or SQFT variance.");
        }
      } else {
        setError(response.error || "Failed to load comparables.");
        setState((prev) => ({
          ...prev,
          availableComps: [],
          selectedComps: [],
        }));
      }
    } catch (e: any) {
      console.error("Comparables loading error:", e);
      // Fallback: use empty comps if endpoint not available
      setState((prev) => ({
        ...prev,
        availableComps: [],
        selectedComps: [],
      }));
      setError("Failed to load comparable properties.");
    } finally {
      setLoadingComps(false);
    }
  };

  // When moving to step 2, load comparables
  useEffect(() => {
    if (state.step === 2 && state.property && state.availableComps.length === 0) {
      loadComparables();
    }
  }, [state.step, state.property]);

  // Move comp between columns
  const selectComp = (comp: Comparable) => {
    if (state.selectedComps.length >= 8) return;
    setState((prev) => ({
      ...prev,
      availableComps: prev.availableComps.filter((c) => c.mlsId !== comp.mlsId),
      selectedComps: [...prev.selectedComps, comp],
    }));
  };

  const deselectComp = (comp: Comparable) => {
    setState((prev) => ({
      ...prev,
      selectedComps: prev.selectedComps.filter((c) => c.mlsId !== comp.mlsId),
      availableComps: [...prev.availableComps, comp],
    }));
  };

  // Step 4: Generate Report with polling
  const handleGenerateReport = async () => {
    if (!state.property) return;

    setGenerating(true);
    setGenerationProgress(10);
    setError(null);

    try {
      // Create the report
      const response = await apiFetch("/v1/property/reports", {
        method: "POST",
        body: JSON.stringify({
          report_type: "seller",
          theme: state.theme,
          accent_color: state.accentColor,
          property_address: state.property.full_address || state.address,
          property_city: state.property.city,
          property_state: state.property.state || "CA",
          property_zip: state.property.zip_code,
          apn: state.property.apn,
          owner_name: state.property.owner_name,
          selected_comp_ids: state.selectedComps.map((c) => c.mlsId),
          selected_pages: state.selectedPages,
          sitex_data: state.property,
        }),
      });

      if (!response.success && !response.id) {
        throw new Error(response.error || "Failed to create report");
      }

      const reportId = response.id;
      setGenerationProgress(30);

      // Poll for completion
      let attempts = 0;
      const maxAttempts = 60; // 2 minutes max

      while (attempts < maxAttempts) {
        await new Promise((resolve) => setTimeout(resolve, 2000)); // 2 sec intervals

        const statusResponse = await apiFetch(`/v1/property/reports/${reportId}`);

        if (statusResponse.status === "complete") {
          setGenerationProgress(100);
          setGeneratedReport({
            id: reportId,
            pdf_url: statusResponse.pdf_url,
            qr_code_url: statusResponse.qr_code_url,
            short_code: statusResponse.short_code,
          });
          break;
        } else if (statusResponse.status === "failed") {
          throw new Error(statusResponse.error_message || "Report generation failed");
        }

        // Update progress (30-90% range during polling)
        setGenerationProgress(Math.min(90, 30 + attempts * 2));
        attempts++;
      }

      if (attempts >= maxAttempts) {
        throw new Error("Report generation timed out. Please check the reports list.");
      }
    } catch (e: any) {
      console.error("Generation error:", e);
      setError(e.message || "Failed to generate report");
    } finally {
      setGenerating(false);
    }
  };

  // Reset wizard to create another report
  const resetWizard = () => {
    setState(initialWizardState);
    setGeneratedReport(null);
    setGenerationProgress(0);
    setError(null);
  };

  // Navigation
  const canProceed = () => {
    switch (state.step) {
      case 1:
        return state.property !== null;
      case 2:
        return state.selectedComps.length >= 4 && state.selectedComps.length <= 8;
      case 3:
        return true;
      case 4:
        return true;
      default:
        return false;
    }
  };

  const goNext = () => {
    if (state.step < 4 && canProceed()) {
      setState((prev) => ({ ...prev, step: prev.step + 1 }));
    }
  };

  const goBack = () => {
    if (state.step > 1) {
      setState((prev) => ({ ...prev, step: prev.step - 1 }));
    }
  };

  // Format currency
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(price);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
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
            Generate a professional seller report with comparables
          </p>
        </div>
      </div>

      {/* Progress Stepper */}
      <div className="relative">
        <Progress value={(state.step / 4) * 100} className="h-2" />
        <div className="flex justify-between mt-4">
          {STEPS.map((step) => (
            <div
              key={step.id}
              className={`flex flex-col items-center gap-2 ${
                step.id <= state.step ? "text-primary" : "text-muted-foreground"
              }`}
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors ${
                  step.id < state.step
                    ? "bg-primary border-primary text-primary-foreground"
                    : step.id === state.step
                    ? "border-primary bg-background"
                    : "border-muted-foreground/30 bg-background"
                }`}
              >
                {step.id < state.step ? (
                  <Check className="w-5 h-5" />
                ) : (
                  <step.icon className="w-5 h-5" />
                )}
              </div>
              <span className="text-xs font-medium hidden sm:block">{step.title}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}

      {/* Step Content */}
      <Card>
        <CardContent className="pt-6">
          {/* STEP 1: Find Property */}
          {state.step === 1 && (
            <div className="space-y-6">
              <div>
                <CardTitle className="mb-2">Find Your Property</CardTitle>
                <CardDescription>
                  Enter the property address to search our database
                </CardDescription>
              </div>

              <div className="space-y-4">
                {/* Google Places Autocomplete Input */}
                <div className="space-y-2">
                  <Label htmlFor="address">Property Address</Label>
                  <div className="relative">
                    <Input
                      ref={addressInputRef}
                      id="address"
                      placeholder="Start typing an address..."
                      value={state.address}
                      onChange={(e) =>
                        setState((prev) => ({ ...prev, address: e.target.value }))
                      }
                      onKeyDown={(e) => e.key === "Enter" && handleSearchProperty()}
                      className="pr-10"
                    />
                    {googleMapsLoaded && (
                      <MapPin className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {googleMapsLoaded 
                      ? "Start typing to see address suggestions" 
                      : "Loading address autocomplete..."}
                  </p>
                </div>

                {/* City, State, ZIP - Auto-populated from Google Places */}
                <div className="space-y-2">
                  <Label htmlFor="cityStateZip">City, State ZIP</Label>
                  <Input
                    id="cityStateZip"
                    placeholder="Los Angeles, CA 90210"
                    value={state.cityStateZip}
                    onChange={(e) =>
                      setState((prev) => ({ ...prev, cityStateZip: e.target.value }))
                    }
                    onKeyDown={(e) => e.key === "Enter" && handleSearchProperty()}
                  />
                  {place && (
                    <p className="text-xs text-green-600">
                      ✓ Address auto-filled from selection
                    </p>
                  )}
                </div>
              </div>

              <Button onClick={handleSearchProperty} disabled={searching}>
                {searching ? (
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

              {/* Property Results */}
              {state.property && (
                <div className="border rounded-lg p-4 bg-muted/30 space-y-4">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Home className="w-6 h-6 text-primary" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold">{state.property.full_address}</h3>
                      <p className="text-sm text-muted-foreground">
                        {state.property.city}, {state.property.state} {state.property.zip_code}
                      </p>
                    </div>
                    <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                      Found
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Owner</p>
                      <p className="font-medium">{state.property.owner_name || "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Beds / Baths</p>
                      <p className="font-medium">
                        {state.property.bedrooms || "-"} / {state.property.bathrooms || "-"}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Sq Ft</p>
                      <p className="font-medium">
                        {state.property.sqft?.toLocaleString() || "N/A"}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Year Built</p>
                      <p className="font-medium">{state.property.year_built || "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">APN</p>
                      <p className="font-medium">{state.property.apn || "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">County</p>
                      <p className="font-medium">{state.property.county || "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Property Type</p>
                      <p className="font-medium">{state.property.property_type || "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Assessed Value</p>
                      <p className="font-medium">
                        {state.property.assessed_value
                          ? formatPrice(state.property.assessed_value)
                          : "N/A"}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* STEP 2: Select Comparables */}
          {state.step === 2 && (
            <div className="space-y-6">
              {/* Search Filters */}
              <div className="bg-muted/50 rounded-lg p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium text-sm">Search Filters</h4>
                  {state.searchParams && (
                    <span className="text-xs text-muted-foreground">
                      Found {state.searchParams.total_before_filter || 0} listings
                    </span>
                  )}
                </div>
                <div className="grid sm:grid-cols-3 gap-4">
                  {/* Radius */}
                  <div className="space-y-2">
                    <Label className="text-xs">Radius (miles)</Label>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-8 w-8 p-0"
                        onClick={() => {
                          const newRadius = Math.max(0.25, state.radiusMiles - 0.25);
                          setState((prev) => ({ ...prev, radiusMiles: newRadius }));
                        }}
                        disabled={state.radiusMiles <= 0.25 || loadingComps}
                      >
                        <Minus className="h-3 w-3" />
                      </Button>
                      <span className="text-sm font-medium min-w-[3rem] text-center">
                        {state.radiusMiles.toFixed(2)} mi
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-8 w-8 p-0"
                        onClick={() => {
                          const newRadius = Math.min(5, state.radiusMiles + 0.25);
                          setState((prev) => ({ ...prev, radiusMiles: newRadius }));
                        }}
                        disabled={state.radiusMiles >= 5 || loadingComps}
                      >
                        <Plus className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>

                  {/* SQFT Variance */}
                  <div className="space-y-2">
                    <Label className="text-xs">SQFT Variance</Label>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-8 w-8 p-0"
                        onClick={() => {
                          const newVariance = Math.max(0.05, state.sqftVariance - 0.05);
                          setState((prev) => ({ ...prev, sqftVariance: newVariance }));
                        }}
                        disabled={state.sqftVariance <= 0.05 || loadingComps}
                      >
                        <Minus className="h-3 w-3" />
                      </Button>
                      <span className="text-sm font-medium min-w-[3rem] text-center">
                        ±{Math.round(state.sqftVariance * 100)}%
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-8 w-8 p-0"
                        onClick={() => {
                          const newVariance = Math.min(0.50, state.sqftVariance + 0.05);
                          setState((prev) => ({ ...prev, sqftVariance: newVariance }));
                        }}
                        disabled={state.sqftVariance >= 0.50 || loadingComps}
                      >
                        <Plus className="h-3 w-3" />
                      </Button>
                    </div>
                    {state.searchParams?.sqft_range && (
                      <p className="text-xs text-muted-foreground">
                        {state.searchParams.sqft_range.min.toLocaleString()} - {state.searchParams.sqft_range.max.toLocaleString()} sqft
                      </p>
                    )}
                  </div>

                  {/* Refresh Button */}
                  <div className="space-y-2">
                    <Label className="text-xs">&nbsp;</Label>
                    <Button
                      variant="secondary"
                      size="sm"
                      className="w-full"
                      onClick={() => loadComparables()}
                      disabled={loadingComps}
                    >
                      {loadingComps ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      ) : (
                        <Search className="h-4 w-4 mr-2" />
                      )}
                      Refresh
                    </Button>
                  </div>
                </div>
              </div>

              {loadingComps ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">Finding comparable properties...</p>
                  <p className="text-sm text-muted-foreground/70 mt-1">
                    Searching within {state.radiusMiles} miles, ±{Math.round(state.sqftVariance * 100)}% sqft
                  </p>
                </div>
              ) : (
                <ComparablesPicker
                  availableComps={[...state.availableComps, ...state.selectedComps].map((c) => ({
                    id: c.mlsId,
                    address: c.address.full,
                    city: c.address.city,
                    price: c.listPrice,
                    bedrooms: c.property.bedrooms,
                    bathrooms: c.property.bathrooms,
                    sqft: c.property.area,
                    yearBuilt: c.property.yearBuilt,
                    lat: c.geo?.lat,
                    lng: c.geo?.lng,
                    photoUrl: c.photos?.[0],
                    distanceMiles: c.distance,
                    status: "Closed",
                  }))}
                  selectedIds={state.selectedComps.map((c) => c.mlsId)}
                  onSelectionChange={(newSelectedIds) => {
                    // Combine all comps to find by ID
                    const allComps = [...state.availableComps, ...state.selectedComps];
                    
                    // Find newly selected and deselected
                    const newSelected = allComps.filter((c) => newSelectedIds.includes(c.mlsId));
                    const newAvailable = allComps.filter((c) => !newSelectedIds.includes(c.mlsId));
                    
                    setState((prev) => ({
                      ...prev,
                      selectedComps: newSelected,
                      availableComps: newAvailable,
                    }));
                  }}
                  onOpenMap={() => setMapModalOpen(true)}
                  minSelections={4}
                  maxSelections={8}
                  subjectProperty={{
                    bedrooms: state.property?.bedrooms,
                    bathrooms: state.property?.bathrooms,
                    sqft: state.property?.sqft,
                  }}
                  mapDisabled={!state.property?.latitude || !state.property?.longitude}
                />
              )}

              {/* Comparables Map Modal */}
              {state.property?.latitude && state.property?.longitude && (
                <ComparablesMapModal
                  isOpen={mapModalOpen}
                  onClose={() => setMapModalOpen(false)}
                  subjectProperty={{
                    lat: state.property.latitude,
                    lng: state.property.longitude,
                    address: state.property.full_address,
                    bedrooms: state.property.bedrooms,
                    bathrooms: state.property.bathrooms,
                    sqft: state.property.sqft,
                  }}
                  comparables={[...state.availableComps, ...state.selectedComps].map((c) => ({
                    id: c.mlsId,
                    address: c.address.full,
                    city: c.address.city,
                    price: c.listPrice,
                    bedrooms: c.property.bedrooms,
                    bathrooms: c.property.bathrooms,
                    sqft: c.property.area,
                    yearBuilt: c.property.yearBuilt,
                    lat: c.geo?.lat || 0,
                    lng: c.geo?.lng || 0,
                    photoUrl: c.photos?.[0],
                    distanceMiles: c.distance,
                    status: "Closed",
                  }))}
                  selectedIds={state.selectedComps.map((c) => c.mlsId)}
                  onSelectionChange={(newSelectedIds) => {
                    // Combine all comps to find by ID
                    const allComps = [...state.availableComps, ...state.selectedComps];
                    
                    // Find newly selected and deselected
                    const newSelected = allComps.filter((c) => newSelectedIds.includes(c.mlsId));
                    const newAvailable = allComps.filter((c) => !newSelectedIds.includes(c.mlsId));
                    
                    setState((prev) => ({
                      ...prev,
                      selectedComps: newSelected,
                      availableComps: newAvailable,
                    }));
                  }}
                  maxSelections={8}
                />
              )}

              {/* Parameter Adjustment Modal */}
              <Dialog open={showParamsModal} onOpenChange={setShowParamsModal}>
                <DialogContent className="max-w-md">
                  <DialogHeader>
                    <DialogTitle>Adjust Search Parameters</DialogTitle>
                    <DialogDescription>
                      {state.availableComps.length === 0
                        ? "No comparable properties found."
                        : `Only ${state.availableComps.length} comparable ${state.availableComps.length === 1 ? "property" : "properties"} found.`}
                      {" "}Adjust the parameters below to find more matches.
                    </DialogDescription>
                  </DialogHeader>

                  <div className="space-y-6 py-4">
                    {/* Radius Slider */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm font-medium">Search Radius</Label>
                        <span className="text-sm font-semibold text-primary">
                          {state.radiusMiles.toFixed(2)} miles
                        </span>
                      </div>
                      <input
                        type="range"
                        min="0.25"
                        max="3.0"
                        step="0.25"
                        value={state.radiusMiles}
                        onChange={(e) =>
                          setState((prev) => ({
                            ...prev,
                            radiusMiles: parseFloat(e.target.value),
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

                    {/* SQFT Variance Slider */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm font-medium">Square Footage Variance</Label>
                        <span className="text-sm font-semibold text-primary">
                          ±{Math.round(state.sqftVariance * 100)}%
                        </span>
                      </div>
                      <input
                        type="range"
                        min="0.10"
                        max="0.50"
                        step="0.05"
                        value={state.sqftVariance}
                        onChange={(e) =>
                          setState((prev) => ({
                            ...prev,
                            sqftVariance: parseFloat(e.target.value),
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
                          Range: {Math.round(state.property.sqft * (1 - state.sqftVariance)).toLocaleString()} - {Math.round(state.property.sqft * (1 + state.sqftVariance)).toLocaleString()} sqft
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
                        loadComparables();
                      }}
                      disabled={loadingComps}
                    >
                      {loadingComps ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      ) : (
                        <Search className="h-4 w-4 mr-2" />
                      )}
                      Search Again
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          )}

          {/* STEP 3: Choose Theme */}
          {state.step === 3 && (
            <div className="space-y-6">
              <ThemeSelector
                selectedTheme={state.theme}
                onThemeChange={(theme) => setState((prev) => ({ ...prev, theme }))}
                accentColor={state.accentColor}
                onAccentColorChange={(accentColor) => setState((prev) => ({ ...prev, accentColor }))}
                selectedPages={state.selectedPages}
                onPagesChange={(selectedPages) => setState((prev) => ({ ...prev, selectedPages }))}
                propertyAddress={state.property?.full_address || state.address}
              />
            </div>
          )}

          {/* STEP 4: Review & Generate */}
          {state.step === 4 && (
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
                              {THEME_NAMES[state.theme] || `Theme ${state.theme}`}
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
                              {state.selectedComps.length} selected
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Pages</span>
                            <span className="font-medium">
                              {state.selectedPages.length} pages
                            </span>
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

                  {/* Generation Progress */}
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
                            strokeDashoffset={264 - (264 * generationProgress) / 100}
                            strokeLinecap="round"
                            fill="transparent"
                            r="42"
                            cx="50"
                            cy="50"
                          />
                        </svg>
                        <span className="absolute inset-0 flex items-center justify-center text-sm font-semibold">
                          {generationProgress}%
                        </span>
                      </div>
                      <p className="text-foreground font-medium">
                        Generating your report...
                      </p>
                      <p className="text-sm text-muted-foreground mt-1">
                        This may take up to 30 seconds
                      </p>
                    </div>
                  ) : (
                    /* Navigation buttons in non-generating state are handled by bottom bar */
                    null
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
                        <p className="text-sm text-muted-foreground">
                          PDF is being generated...
                        </p>
                      )}
                    </div>

                    {/* QR Code */}
                    <div className="bg-background border rounded-lg p-6 text-left">
                      <h4 className="font-semibold mb-3 flex items-center gap-2">
                        <MapPin className="w-5 h-5" />
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
                      <p className="text-sm text-muted-foreground mb-2">
                        Public Landing Page:
                      </p>
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

      {/* Navigation Buttons - Hidden when report is generated */}
      {!generatedReport && (
        <div className="flex justify-between">
          <Button 
            variant="outline" 
            onClick={goBack} 
            disabled={state.step === 1 || generating}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>

          {state.step < 4 ? (
            <Button onClick={goNext} disabled={!canProceed()}>
              Continue
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          ) : (
            <Button 
              onClick={handleGenerateReport} 
              disabled={generating}
              className="bg-green-600 hover:bg-green-700"
            >
              {generating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4 mr-2" />
                  Generate Report
                </>
              )}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

// Comparable Card Component
function CompCard({
  comp,
  action,
  onClick,
  disabled = false,
}: {
  comp: Comparable;
  action: "add" | "remove";
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <div
      className={`border rounded-lg p-3 flex items-center gap-3 transition-colors ${
        disabled ? "opacity-50" : "hover:bg-muted/50 cursor-pointer"
      }`}
      onClick={disabled ? undefined : onClick}
    >
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm truncate">{comp.address.full}</p>
        <p className="text-xs text-muted-foreground">
          {comp.address.city}, {comp.address.state}
        </p>
        <div className="flex gap-3 mt-1 text-xs text-muted-foreground">
          <span>{comp.property.bedrooms} bd</span>
          <span>{comp.property.bathrooms} ba</span>
          <span>{comp.property.area?.toLocaleString()} sqft</span>
          <span className="font-medium text-foreground">
            ${(comp.listPrice / 1000).toFixed(0)}K
          </span>
        </div>
      </div>
      <Button
        variant={action === "add" ? "outline" : "destructive"}
        size="icon"
        className="h-8 w-8 shrink-0"
        disabled={disabled}
      >
        {action === "add" ? <Plus className="w-4 h-4" /> : <Minus className="w-4 h-4" />}
      </Button>
    </div>
  );
}

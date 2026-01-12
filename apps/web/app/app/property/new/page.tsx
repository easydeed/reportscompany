"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
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

interface WizardState {
  step: number;
  address: string;
  cityStateZip: string;
  property: PropertyData | null;
  availableComps: Comparable[];
  selectedComps: Comparable[];
  theme: number;
  accentColor: string;
}

const STEPS = [
  { id: 1, title: "Find Property", icon: Search },
  { id: 2, title: "Select Comparables", icon: MapPin },
  { id: 3, title: "Choose Theme", icon: Palette },
  { id: 4, title: "Review & Generate", icon: FileText },
];

const THEMES = [
  { id: 1, name: "Classic", colors: ["#1e3a5f", "#f5f5f5", "#c9a227"] },
  { id: 2, name: "Modern", colors: ["#2563eb", "#ffffff", "#10b981"] },
  { id: 3, name: "Elegant", colors: ["#1f2937", "#faf5ef", "#a78bfa"] },
  { id: 4, name: "Warm", colors: ["#78350f", "#fffbeb", "#f59e0b"] },
  { id: 5, name: "Fresh", colors: ["#065f46", "#ecfdf5", "#34d399"] },
];

const PRESET_COLORS = [
  "#2563eb", // Blue
  "#10b981", // Green
  "#8b5cf6", // Purple
  "#f59e0b", // Amber
  "#ef4444", // Red
  "#ec4899", // Pink
  "#06b6d4", // Cyan
  "#1f2937", // Gray
];

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
    accentColor: "#2563eb",
  });

  const [searching, setSearching] = useState(false);
  const [loadingComps, setLoadingComps] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mapModalOpen, setMapModalOpen] = useState(false);

  // Step 1: Search Property
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
  const loadComparables = async () => {
    if (!state.property) return;

    setLoadingComps(true);
    setError(null);

    try {
      const response = await apiFetch("/v1/property/comparables", {
        method: "POST",
        body: JSON.stringify({
          address: state.property.full_address,
          city_state_zip: `${state.property.city}, ${state.property.state} ${state.property.zip_code}`,
          radius_miles: 1.0,
          status: "Closed",
          limit: 20,
        }),
      });

      // API returns { success, subject_property, comparables: ComparableProperty[], error }
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
          photos: comp.photo_url ? [comp.photo_url] : [],
          distance: comp.distance_miles,
        }));

        setState((prev) => ({
          ...prev,
          availableComps: transformedComps,
          selectedComps: [],
        }));

        if (transformedComps.length === 0) {
          setError("No comparable properties found in this area. Try expanding the search radius.");
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

  // Step 4: Generate Report
  const handleGenerateReport = async () => {
    if (!state.property) return;

    setGenerating(true);
    setError(null);

    try {
      const data = await apiFetch("/v1/property/reports", {
        method: "POST",
        body: JSON.stringify({
          address: state.property.street || state.address,
          city_state_zip: `${state.property.city}, ${state.property.state} ${state.property.zip_code}`,
          report_type: "seller",
          theme: state.theme,
          accent_color: state.accentColor,
          comparables: state.selectedComps.map((c) => c.mlsId),
        }),
      });

      // Redirect to the report detail page
      router.push(`/app/property/${data.id}?created=true`);
    } catch (e: any) {
      setError(e.message || "Failed to generate report");
      setGenerating(false);
    }
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

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="address">Street Address</Label>
                  <Input
                    id="address"
                    placeholder="123 Main St"
                    value={state.address}
                    onChange={(e) =>
                      setState((prev) => ({ ...prev, address: e.target.value }))
                    }
                    onKeyDown={(e) => e.key === "Enter" && handleSearchProperty()}
                  />
                </div>
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
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="mb-2">Select Comparables</CardTitle>
                  <CardDescription>
                    Choose 4-8 comparable properties for your report
                  </CardDescription>
                </div>
                <Button variant="outline" onClick={() => setMapModalOpen(true)}>
                  <Map className="w-4 h-4 mr-2" />
                  View on Map
                </Button>
              </div>

              {loadingComps ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Available Comps */}
                  <div className="space-y-3">
                    <h4 className="font-medium text-sm text-muted-foreground">
                      Available Comparables ({state.availableComps.length})
                    </h4>
                    <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
                      {state.availableComps.length === 0 ? (
                        <p className="text-sm text-muted-foreground text-center py-8">
                          No comparables available
                        </p>
                      ) : (
                        state.availableComps.map((comp) => (
                          <CompCard
                            key={comp.mlsId}
                            comp={comp}
                            action="add"
                            onClick={() => selectComp(comp)}
                            disabled={state.selectedComps.length >= 8}
                          />
                        ))
                      )}
                    </div>
                  </div>

                  {/* Selected Comps */}
                  <div className="space-y-3">
                    <h4 className="font-medium text-sm text-muted-foreground">
                      Selected Comparables ({state.selectedComps.length}/8)
                      {state.selectedComps.length < 4 && (
                        <span className="text-red-500 ml-2">Min 4 required</span>
                      )}
                    </h4>
                    <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
                      {state.selectedComps.length === 0 ? (
                        <p className="text-sm text-muted-foreground text-center py-8 border-2 border-dashed rounded-lg">
                          Click comparables to add them here
                        </p>
                      ) : (
                        state.selectedComps.map((comp) => (
                          <CompCard
                            key={comp.mlsId}
                            comp={comp}
                            action="remove"
                            onClick={() => deselectComp(comp)}
                          />
                        ))
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Map Modal Placeholder */}
              <Dialog open={mapModalOpen} onOpenChange={setMapModalOpen}>
                <DialogContent className="max-w-3xl">
                  <DialogHeader>
                    <DialogTitle>Comparables Map</DialogTitle>
                    <DialogDescription>
                      View comparable properties on a map
                    </DialogDescription>
                  </DialogHeader>
                  <div className="h-[400px] bg-muted rounded-lg flex items-center justify-center">
                    <p className="text-muted-foreground">Map view coming soon</p>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          )}

          {/* STEP 3: Choose Theme */}
          {state.step === 3 && (
            <div className="space-y-6">
              <div>
                <CardTitle className="mb-2">Choose Your Theme</CardTitle>
                <CardDescription>
                  Select a theme and accent color for your report
                </CardDescription>
              </div>

              <div className="space-y-4">
                <Label>Theme Style</Label>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
                  {THEMES.map((theme) => (
                    <button
                      key={theme.id}
                      onClick={() => setState((prev) => ({ ...prev, theme: theme.id }))}
                      className={`relative rounded-lg border-2 p-4 text-center transition-all ${
                        state.theme === theme.id
                          ? "border-primary ring-2 ring-primary/20"
                          : "border-muted hover:border-muted-foreground/30"
                      }`}
                    >
                      <div className="flex justify-center gap-1 mb-2">
                        {theme.colors.map((color, i) => (
                          <div
                            key={i}
                            className="w-6 h-6 rounded"
                            style={{ backgroundColor: color }}
                          />
                        ))}
                      </div>
                      <span className="text-sm font-medium">{theme.name}</span>
                      {state.theme === theme.id && (
                        <div className="absolute -top-2 -right-2 w-5 h-5 bg-primary rounded-full flex items-center justify-center">
                          <Check className="w-3 h-3 text-primary-foreground" />
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <Label>Accent Color</Label>
                <div className="flex flex-wrap gap-3">
                  {PRESET_COLORS.map((color) => (
                    <button
                      key={color}
                      onClick={() => setState((prev) => ({ ...prev, accentColor: color }))}
                      className={`w-10 h-10 rounded-lg border-2 transition-all ${
                        state.accentColor === color
                          ? "border-foreground scale-110"
                          : "border-transparent hover:scale-105"
                      }`}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                  <div className="flex items-center gap-2">
                    <Input
                      type="text"
                      placeholder="#hex"
                      value={state.accentColor}
                      onChange={(e) =>
                        setState((prev) => ({ ...prev, accentColor: e.target.value }))
                      }
                      className="w-24"
                    />
                    <div
                      className="w-10 h-10 rounded-lg border"
                      style={{ backgroundColor: state.accentColor }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 4: Review & Generate */}
          {state.step === 4 && (
            <div className="space-y-6">
              <div>
                <CardTitle className="mb-2">Review & Generate</CardTitle>
                <CardDescription>
                  Confirm your selections and generate the report
                </CardDescription>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="border rounded-lg p-4 space-y-3">
                  <h4 className="font-medium flex items-center gap-2">
                    <Home className="w-4 h-4" />
                    Property
                  </h4>
                  <div className="text-sm">
                    <p className="font-medium">{state.property?.full_address}</p>
                    <p className="text-muted-foreground">
                      {state.property?.city}, {state.property?.state}{" "}
                      {state.property?.zip_code}
                    </p>
                    <p className="text-muted-foreground mt-1">
                      {state.property?.bedrooms} bed • {state.property?.bathrooms} bath •{" "}
                      {state.property?.sqft?.toLocaleString()} sqft
                    </p>
                  </div>
                </div>

                <div className="border rounded-lg p-4 space-y-3">
                  <h4 className="font-medium flex items-center gap-2">
                    <MapPin className="w-4 h-4" />
                    Comparables
                  </h4>
                  <div className="text-sm">
                    <p className="font-medium">{state.selectedComps.length} properties selected</p>
                    <p className="text-muted-foreground">
                      {state.selectedComps.slice(0, 3).map((c) => c.address.city).join(", ")}
                      {state.selectedComps.length > 3 && "..."}
                    </p>
                  </div>
                </div>

                <div className="border rounded-lg p-4 space-y-3">
                  <h4 className="font-medium flex items-center gap-2">
                    <Palette className="w-4 h-4" />
                    Theme
                  </h4>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium">
                      {THEMES.find((t) => t.id === state.theme)?.name}
                    </span>
                    <div
                      className="w-6 h-6 rounded border"
                      style={{ backgroundColor: state.accentColor }}
                    />
                  </div>
                </div>

                <div className="border rounded-lg p-4 space-y-3">
                  <h4 className="font-medium flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    Report Type
                  </h4>
                  <div className="text-sm">
                    <Badge>Seller Report</Badge>
                  </div>
                </div>
              </div>

              {generating && (
                <div className="bg-muted/50 rounded-lg p-6 text-center space-y-3">
                  <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary" />
                  <p className="font-medium">Generating your report...</p>
                  <p className="text-sm text-muted-foreground">
                    This may take a few moments
                  </p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={goBack} disabled={state.step === 1 || generating}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>

        {state.step < 4 ? (
          <Button onClick={goNext} disabled={!canProceed()}>
            Continue
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        ) : (
          <Button onClick={handleGenerateReport} disabled={generating}>
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

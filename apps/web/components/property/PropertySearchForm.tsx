"use client";

import { useRef, useEffect, useCallback, useState } from "react";
import {
  Search,
  Home,
  MapPin,
  Loader2,
  CheckCircle,
  AlertCircle,
  Calendar,
  DollarSign,
  User,
  FileText,
  ChevronDown,
} from "lucide-react";
import { useGooglePlaces, PlaceResult } from "@/hooks/useGooglePlaces";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { PropertyData } from "@/lib/wizard-types";

interface PropertySearchFormProps {
  address: string;
  cityStateZip: string;
  property: PropertyData | null;
  loading: boolean;
  error: string | null;
  onAddressChange: (address: string) => void;
  onCityStateZipChange: (cityStateZip: string) => void;
  onSearch: () => void;
  onContinue: () => void;
  canContinue: boolean;
}

export function PropertySearchForm({
  address,
  cityStateZip,
  property,
  loading,
  error,
  onAddressChange,
  onCityStateZipChange,
  onSearch,
  onContinue,
  canContinue,
}: PropertySearchFormProps) {
  const addressInputRef = useRef<HTMLInputElement>(null);
  const searchTriggerRef = useRef(false);
  const [showLegalDesc, setShowLegalDesc] = useState(false);

  // Handle Google Places selection
  const handlePlaceSelect = useCallback(
    (placeResult: PlaceResult) => {
      const cityStateZipStr = `${placeResult.city}, ${placeResult.state} ${placeResult.zip}`;
      onAddressChange(placeResult.address);
      onCityStateZipChange(cityStateZipStr);

      // Trigger search after state updates
      searchTriggerRef.current = true;
    },
    [onAddressChange, onCityStateZipChange]
  );

  const { isLoaded: googleMapsLoaded, error: placesError } = useGooglePlaces(
    addressInputRef,
    {
      onPlaceSelect: handlePlaceSelect,
    }
  );

  // Auto-trigger search when place is selected via Google Places
  useEffect(() => {
    if (searchTriggerRef.current && address && cityStateZip) {
      searchTriggerRef.current = false;
      onSearch();
    }
  }, [address, cityStateZip, onSearch]);

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (address.trim()) {
      onSearch();
    }
  };

  // Reset to search another property
  const handleReset = () => {
    onAddressChange("");
    onCityStateZipChange("");
    setShowLegalDesc(false);
    // Focus the input after reset
    setTimeout(() => addressInputRef.current?.focus(), 100);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold mb-2">Find Your Property</h2>
        <p className="text-muted-foreground">
          Enter the property address to get started. We&apos;ll pull the property
          details automatically.
        </p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="address">Property Address</Label>
          <div className="relative">
            <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              ref={addressInputRef}
              id="address"
              placeholder="Start typing an address..."
              value={address}
              onChange={(e) => onAddressChange(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && e.preventDefault()}
              className="pl-10 pr-4 py-6 text-base"
              autoComplete="off"
            />
          </div>
          <p className="text-xs text-muted-foreground">
            {!googleMapsLoaded && !placesError && "Loading address suggestions..."}
            {googleMapsLoaded && !placesError && "Start typing to see address suggestions"}
            {placesError && (
              <span className="text-amber-600">{placesError}</span>
            )}
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="cityStateZip">City, State ZIP</Label>
          <Input
            id="cityStateZip"
            placeholder="e.g., Anaheim, CA 92805"
            value={cityStateZip}
            onChange={(e) => onCityStateZipChange(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit(e)}
            className="py-6"
          />
        </div>

        {/* Search Button - only show if no property found yet */}
        {!property && (
          <Button
            type="submit"
            disabled={loading || !address.trim()}
            className="w-full py-6 text-base"
          >
            {loading ? (
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
      </form>

      {/* Error Message */}
      {error && (
        <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-red-800">Property Not Found</p>
            <p className="text-sm text-red-600 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Property Results */}
      {property && (
        <div className="border-2 border-green-500 rounded-lg overflow-hidden">
          {/* Success Header */}
          <div className="bg-green-50 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <span className="font-medium text-green-800">Property Found</span>
            </div>
            <button
              onClick={handleReset}
              className="text-sm text-green-700 hover:text-green-900 hover:underline"
            >
              Search Different Property
            </button>
          </div>

          {/* Property Details */}
          <div className="p-4 space-y-4">
            {/* Address */}
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                <Home className="w-6 h-6 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xl font-semibold">
                  {property.full_address || property.street}
                </p>
                <p className="text-muted-foreground">
                  {property.city}, {property.state} {property.zip_code}
                </p>
                {property.county && (
                  <p className="text-sm text-muted-foreground">
                    {property.county} County
                  </p>
                )}
              </div>
            </div>

            {/* Key Details Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <DetailCard
                icon={<Home className="w-4 h-4" />}
                label="Beds / Baths"
                value={`${property.bedrooms || "-"} / ${property.bathrooms || "-"}`}
              />
              <DetailCard
                icon={<MapPin className="w-4 h-4" />}
                label="Square Feet"
                value={property.sqft?.toLocaleString() || "-"}
              />
              <DetailCard
                icon={<Calendar className="w-4 h-4" />}
                label="Year Built"
                value={property.year_built?.toString() || "-"}
              />
              <DetailCard
                icon={<DollarSign className="w-4 h-4" />}
                label="Assessed Value"
                value={
                  property.assessed_value
                    ? formatCurrency(property.assessed_value)
                    : "-"
                }
              />
            </div>

            {/* Additional Info */}
            <div className="grid md:grid-cols-3 gap-4 pt-4 border-t">
              <div className="flex items-start gap-3">
                <User className="w-4 h-4 text-muted-foreground mt-0.5" />
                <div>
                  <p className="text-sm text-muted-foreground">Owner</p>
                  <p className="font-medium">
                    {property.owner_name || "Not available"}
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <FileText className="w-4 h-4 text-muted-foreground mt-0.5" />
                <div>
                  <p className="text-sm text-muted-foreground">APN</p>
                  <p className="font-medium font-mono text-sm">
                    {property.apn || "Not available"}
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Home className="w-4 h-4 text-muted-foreground mt-0.5" />
                <div>
                  <p className="text-sm text-muted-foreground">Property Type</p>
                  <p className="font-medium">
                    {property.property_type || "Residential"}
                  </p>
                </div>
              </div>
            </div>

            {/* Legal Description (collapsible) */}
            {property.legal_description && (
              <div className="pt-4 border-t">
                <button
                  onClick={() => setShowLegalDesc(!showLegalDesc)}
                  className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  <ChevronDown
                    className={`w-4 h-4 transition-transform ${
                      showLegalDesc ? "rotate-180" : ""
                    }`}
                  />
                  {showLegalDesc ? "Hide" : "View"} Legal Description
                </button>
                {showLegalDesc && (
                  <p className="mt-2 text-sm text-muted-foreground bg-muted/50 p-3 rounded-lg">
                    {property.legal_description}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-end pt-4 border-t">
        <Button
          onClick={onContinue}
          disabled={!canContinue}
          size="lg"
          className="px-8"
        >
          Continue to Comparables →
        </Button>
      </div>
    </div>
  );
}

/**
 * Detail card for property stats
 */
function DetailCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="bg-muted/50 rounded-lg p-3">
      <div className="flex items-center gap-2 text-muted-foreground mb-1">
        {icon}
        <span className="text-xs font-medium uppercase tracking-wide">
          {label}
        </span>
      </div>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  );
}

export default PropertySearchForm;

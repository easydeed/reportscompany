"use client";

import { useRef, useEffect } from "react";
import { Search, Home, MapPin, Loader2 } from "lucide-react";
import { useGooglePlaces } from "@/hooks/useGooglePlaces";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import type { PropertyData } from "@/lib/wizard-types";

interface PropertySearchFormProps {
  address: string;
  cityStateZip: string;
  property: PropertyData | null;
  loading: boolean;
  error: string | null;
  onAddressChange: (address: string) => void;
  onCityStateZipChange: (cityStateZip: string) => void;
  onPlaceSelect?: (place: {
    address: string;
    cityStateZip: string;
  }) => void;
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
  onPlaceSelect,
  onSearch,
  onContinue,
  canContinue,
}: PropertySearchFormProps) {
  const addressInputRef = useRef<HTMLInputElement>(null);
  const searchTriggerRef = useRef(false);

  // Google Places autocomplete
  const handlePlaceSelectInternal = (place: {
    address: string;
    city: string;
    state: string;
    zip: string;
  }) => {
    const cityStateZipStr = `${place.city}, ${place.state} ${place.zip}`;
    onAddressChange(place.address);
    onCityStateZipChange(cityStateZipStr);
    
    if (onPlaceSelect) {
      onPlaceSelect({ address: place.address, cityStateZip: cityStateZipStr });
    }
    
    // Trigger search after state updates
    searchTriggerRef.current = true;
  };

  const { isLoaded: googleMapsLoaded } = useGooglePlaces(addressInputRef, {
    onPlaceSelect: handlePlaceSelectInternal,
  });

  // Auto-trigger search when place is selected via Google Places
  useEffect(() => {
    if (searchTriggerRef.current && address && cityStateZip) {
      searchTriggerRef.current = false;
      onSearch();
    }
  }, [address, cityStateZip, onSearch]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Find Your Property</h2>
        <p className="text-sm text-muted-foreground">
          Enter the property address to search our database
        </p>
      </div>

      {/* Address Input with Google Places */}
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="address">Property Address</Label>
          <div className="relative">
            <Input
              ref={addressInputRef}
              id="address"
              placeholder="Start typing an address..."
              value={address}
              onChange={(e) => onAddressChange(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && onSearch()}
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

        <div className="space-y-2">
          <Label htmlFor="cityStateZip">City, State ZIP</Label>
          <Input
            id="cityStateZip"
            placeholder="Los Angeles, CA 90210"
            value={cityStateZip}
            onChange={(e) => onCityStateZipChange(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onSearch()}
          />
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Search Button */}
      <Button onClick={onSearch} disabled={loading || !address.trim()}>
        {loading ? (
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
      {property && (
        <div className="border rounded-lg p-4 bg-muted/30 space-y-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
              <Home className="w-6 h-6 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold truncate">{property.full_address}</h3>
              <p className="text-sm text-muted-foreground">
                {property.city}, {property.state} {property.zip_code}
              </p>
            </div>
            <Badge
              variant="outline"
              className="bg-green-50 text-green-700 border-green-200 shrink-0"
            >
              Found
            </Badge>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Owner</p>
              <p className="font-medium truncate">{property.owner_name || "N/A"}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Beds / Baths</p>
              <p className="font-medium">
                {property.bedrooms || "-"} / {property.bathrooms || "-"}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Sq Ft</p>
              <p className="font-medium">
                {property.sqft?.toLocaleString() || "N/A"}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Year Built</p>
              <p className="font-medium">{property.year_built || "N/A"}</p>
            </div>
            <div>
              <p className="text-muted-foreground">APN</p>
              <p className="font-medium truncate">{property.apn || "N/A"}</p>
            </div>
            <div>
              <p className="text-muted-foreground">County</p>
              <p className="font-medium truncate">{property.county || "N/A"}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Property Type</p>
              <p className="font-medium truncate">{property.property_type || "N/A"}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Assessed Value</p>
              <p className="font-medium">
                {property.assessed_value
                  ? formatCurrency(property.assessed_value)
                  : "N/A"}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-end pt-4 border-t">
        <Button onClick={onContinue} disabled={!canContinue}>
          Continue to Comparables →
        </Button>
      </div>
    </div>
  );
}

export default PropertySearchForm;


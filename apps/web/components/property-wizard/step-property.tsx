"use client";

import { useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Home,
  Search,
  RotateCcw,
  Loader2,
  ChevronDown,
  ChevronUp,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useGooglePlaces, type PlaceResult } from "@/hooks/useGooglePlaces";
import type { PropertyData } from "./types";

interface StepPropertyProps {
  property: PropertyData | null;
  streetAddress: string;
  cityStateZip: string;
  searchLoading: boolean;
  searchError: string | null;
  onStreetAddressChange: (v: string) => void;
  onCityStateZipChange: (v: string) => void;
  onSearchLoading: (v: boolean) => void;
  onPropertyFound: (p: PropertyData) => void;
  onSearchError: (error: string | null) => void;
  onClear: () => void;
}

export function StepProperty({
  property,
  streetAddress,
  cityStateZip,
  searchLoading,
  searchError,
  onStreetAddressChange,
  onCityStateZipChange,
  onSearchLoading,
  onPropertyFound,
  onSearchError,
  onClear,
}: StepPropertyProps) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const addressInputRef = useRef<HTMLInputElement>(null);

  // Wire Google Places Autocomplete
  const handlePlaceSelect = useCallback(
    (place: PlaceResult) => {
      // Populate the address fields from Google Places
      onStreetAddressChange(place.address || place.fullAddress);
      const csz = [place.city, place.state, place.zip]
        .filter(Boolean)
        .join(", ");
      onCityStateZipChange(csz || "");

      // Auto-trigger property search after place selection
      if (place.address) {
        searchProperty(place.address);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const { isLoaded: googleLoaded, error: googleError } = useGooglePlaces(
    addressInputRef,
    { onPlaceSelect: handlePlaceSelect }
  );

  async function searchProperty(address?: string) {
    const searchAddr = address || streetAddress;
    if (!searchAddr.trim()) return;

    onSearchLoading(true);
    onSearchError(null);

    try {
      const res = await fetch("/api/proxy/v1/property/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ address: searchAddr }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(
          data.detail || data.message || "Property not found. Please check the address and try again."
        );
      }

      const propertyData = await res.json();

      // Map API response to our PropertyData interface
      const mapped: PropertyData = {
        street_address:
          propertyData.street_address || propertyData.address || searchAddr,
        city: propertyData.city || "",
        state: propertyData.state || "",
        zip_code: propertyData.zip_code || propertyData.zip || "",
        full_address:
          propertyData.full_address ||
          `${propertyData.street_address || propertyData.address || searchAddr}, ${propertyData.city || ""}, ${propertyData.state || ""} ${propertyData.zip_code || propertyData.zip || ""}`.trim(),
        bedrooms: propertyData.bedrooms || propertyData.beds || 0,
        bathrooms: propertyData.bathrooms || propertyData.baths || 0,
        sqft: propertyData.sqft || propertyData.square_feet || 0,
        lot_size: propertyData.lot_size || 0,
        year_built: propertyData.year_built || 0,
        owner_name: propertyData.owner_name || "N/A",
        apn: propertyData.apn || propertyData.APN || "",
        assessed_value: propertyData.assessed_value || 0,
        tax_amount: propertyData.tax_amount || 0,
        latitude: propertyData.latitude || 0,
        longitude: propertyData.longitude || 0,
        property_type: propertyData.property_type,
        county: propertyData.county,
        legal_description: propertyData.legal_description,
      };

      onPropertyFound(mapped);

      // Auto-populate city/state/zip if not already set
      if (!cityStateZip.trim()) {
        onCityStateZipChange(
          `${mapped.city}, ${mapped.state} ${mapped.zip_code}`
        );
      }
    } catch (err: any) {
      console.error("Property search failed:", err);
      onSearchError(
        err.message || "Property search failed. Please try again."
      );
    } finally {
      onSearchLoading(false);
    }
  }

  function handleSearch() {
    searchProperty();
  }

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Address Search Card */}
      <div className="rounded-2xl border border-border bg-card p-6">
        <div className="flex items-center gap-3 mb-1">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-[#EEF2FF]">
            <Home className="h-5 w-5 text-[#6366F1]" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">
              Find Your Property
            </h2>
            <p className="text-sm text-muted-foreground">
              Enter the property address to get started.
            </p>
          </div>
        </div>

        <div className="mt-5 space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              ref={addressInputRef}
              placeholder={
                googleLoaded
                  ? "Start typing an address..."
                  : "Enter property address..."
              }
              className="pl-10 h-12 text-base rounded-lg"
              value={streetAddress}
              onChange={(e) => onStreetAddressChange(e.target.value)}
              disabled={!!property}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleSearch();
                }
              }}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Input
              placeholder="City, State ZIP"
              className="rounded-lg"
              value={cityStateZip}
              onChange={(e) => onCityStateZipChange(e.target.value)}
              disabled={!!property}
            />
            <div className="text-xs text-muted-foreground flex items-center">
              {googleError && (
                <span className="text-amber-600">{googleError}</span>
              )}
              {!googleError &&
                cityStateZip &&
                !property &&
                "Auto-populated or edit manually"}
            </div>
          </div>

          {/* Error Message */}
          {searchError && (
            <div className="flex items-center gap-2 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{searchError}</span>
            </div>
          )}

          {!property && (
            <Button
              className="w-full bg-[#6366F1] text-white hover:bg-[#4F46E5] h-11"
              disabled={!streetAddress.trim() || searchLoading}
              onClick={handleSearch}
            >
              {searchLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4 mr-2" />
                  Search Property
                </>
              )}
            </Button>
          )}
        </div>
      </div>

      {/* Property Result Card */}
      <AnimatePresence>
        {property && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="rounded-2xl border border-border bg-card overflow-hidden"
          >
            {/* Gradient top border */}
            <div className="h-0.5 bg-gradient-to-r from-[#6366F1] to-[#818CF8]" />

            <div className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-6 h-6 rounded-full bg-emerald-100 flex items-center justify-center">
                  <svg
                    className="w-3.5 h-3.5 text-emerald-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={3}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
                <h3 className="text-base font-semibold text-foreground">
                  Property Found
                </h3>
              </div>

              <div className="rounded-xl border border-border p-5">
                <h4 className="text-xl font-bold text-foreground">
                  {property.street_address}
                </h4>
                <p className="text-sm text-muted-foreground mt-0.5">
                  {property.city}, {property.state} {property.zip_code}
                </p>

                {/* Stats */}
                <div className="flex flex-wrap gap-3 mt-4">
                  {[
                    { value: property.bedrooms, label: "beds" },
                    { value: property.bathrooms, label: "bath" },
                    {
                      value: property.sqft.toLocaleString(),
                      label: "sqft",
                    },
                    { value: property.year_built, label: "built" },
                  ].map((stat) => (
                    <div
                      key={stat.label}
                      className="rounded-lg bg-muted px-4 py-2.5 text-center min-w-[72px]"
                    >
                      <p className="text-lg font-bold text-foreground">
                        {stat.value}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {stat.label}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Collapsible Details */}
                <div className="mt-4">
                  <button
                    type="button"
                    className="flex items-center gap-1.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                    onClick={() => setDetailsOpen(!detailsOpen)}
                  >
                    {detailsOpen ? (
                      <ChevronUp className="h-4 w-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4" />
                    )}
                    Additional Details
                  </button>
                  <AnimatePresence>
                    {detailsOpen && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <div className="mt-3 space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Owner</span>
                            <span className="font-medium text-foreground">
                              {property.owner_name}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">APN</span>
                            <span className="font-medium text-foreground">
                              {property.apn || "N/A"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">
                              Lot Size
                            </span>
                            <span className="font-medium text-foreground">
                              {property.lot_size > 0
                                ? `${property.lot_size.toLocaleString()} sqft`
                                : "N/A"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">
                              Assessed Value
                            </span>
                            <span className="font-medium text-foreground">
                              {property.assessed_value > 0
                                ? `$${property.assessed_value.toLocaleString()}`
                                : "N/A"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">
                              Annual Taxes
                            </span>
                            <span className="font-medium text-foreground">
                              {property.tax_amount > 0
                                ? `$${property.tax_amount.toLocaleString()}`
                                : "N/A"}
                            </span>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>

              <Button
                variant="ghost"
                className="mt-4 text-muted-foreground"
                onClick={onClear}
              >
                <RotateCcw className="h-4 w-4 mr-1.5" />
                Clear & Search Again
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

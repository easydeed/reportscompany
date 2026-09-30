"use client";

import { useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Home,
  Search,
  RotateCcw,
  Loader2,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useGooglePlaces, type PlaceResult } from "@/hooks/useGooglePlaces";
import type { PropertyData } from "./types";

type UnitMatch = {
  fips: string;
  apn: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  unit_number: string;
  unit_type: string;
};

function buildingAddress(address: string): string {
  return address.replace(/\s+(?:#|unit|apt|apartment|ste|suite)\s*[A-Za-z0-9-]+\s*$/i, "").trim();
}

function parcelLabel(match: UnitMatch): string {
  const number = (match.unit_number || "").trim();
  if (!number) return match.apn || "Select";
  const kind = (match.unit_type || "Unit").trim();
  if (kind === "#") return `#${number}`;
  return `${kind} ${number}`;
}

function prettyPlace(value: string): string {
  return value
    .toLowerCase()
    .replace(/(^|[\s-])([a-z])/g, (_, lead, letter) => lead + letter.toUpperCase());
}

function withChosenUnit(property: PropertyData, match?: UnitMatch): PropertyData {
  const number = (match?.unit_number || property.unit_number || "").trim();
  if (!number) return property;
  const kind = (match?.unit_type || property.unit_type || "Unit").trim();
  const label = kind ? `${kind} ${number}` : number;
  const street = property.street_address || "";
  const streetNext = street.toUpperCase().includes(label.toUpperCase())
    ? street
    : `${street} ${label}`.trim();
  let full = property.full_address || "";
  if (street && full.includes(street)) {
    full = full.replace(street, streetNext);
  } else if (!full.toUpperCase().includes(label.toUpperCase())) {
    full = [streetNext, property.city, `${property.state} ${property.zip_code}`.trim()]
      .filter(Boolean)
      .join(", ");
  }
  let legal = property.legal_description || "";
  if (legal && !legal.toUpperCase().includes(number.toUpperCase())) {
    legal = `${legal} ${label}`.trim();
  }
  return {
    ...property,
    unit_number: number,
    unit_type: kind,
    street_address: streetNext,
    full_address: full,
    legal_description: legal,
  };
}

function mapSiteX(d: Record<string, any>, fallback: string): PropertyData {
  return {
    street_address: d.street || d.street_address || fallback,
    city: d.city || "",
    state: d.state || "",
    zip_code: d.zip_code || "",
    full_address:
      d.full_address ||
      `${d.street || fallback}, ${d.city || ""}, ${d.state || ""} ${d.zip_code || ""}`.trim(),
    bedrooms: d.bedrooms || 0,
    bathrooms: d.bathrooms || 0,
    sqft: d.sqft || 0,
    lot_size: d.lot_size || 0,
    year_built: d.year_built || 0,
    owner_name: d.owner_name || "N/A",
    apn: d.apn || "",
    assessed_value: d.assessed_value || 0,
    tax_amount: d.tax_amount || 0,
    latitude: d.latitude || 0,
    longitude: d.longitude || 0,
    property_type: d.property_type,
    county: d.county,
    legal_description: d.legal_description,
    unit_number: d.unit_number || "",
    unit_type: d.unit_type || "",
    // `?? undefined`, never `|| 0`: a missing sale must stay missing. `0`
    // would render as "$0" in the subject's price row, which is D-118 again
    // with a different wrong number.
    last_sale_price: d.last_sale_price ?? undefined,
    last_sale_date: d.last_sale_date ?? undefined,
    last_sale_price_per_sqft: d.last_sale_price_per_sqft ?? undefined,
  };
}

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
  const [unitMatches, setUnitMatches] = useState<UnitMatch[] | null>(null);
  const addressInputRef = useRef<HTMLInputElement>(null);

  // Wire Google Places Autocomplete
  const handlePlaceSelect = useCallback(
    (place: PlaceResult) => {
      // Populate the address fields from Google Places
      const addr = place.address || place.fullAddress;
      onStreetAddressChange(addr);
      const csz = [place.city, place.state, place.zip]
        .filter(Boolean)
        .join(", ");
      onCityStateZipChange(csz || "");

      // Auto-trigger property search — pass csz directly since React
      // state won't have updated yet when searchProperty reads props
      if (addr) {
        searchProperty(addr, csz);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const { isLoaded: googleLoaded, error: googleError } = useGooglePlaces(
    addressInputRef,
    { onPlaceSelect: handlePlaceSelect }
  );

  async function searchProperty(address?: string, csz?: string) {
    const searchAddr = address || streetAddress;
    if (!searchAddr.trim()) return;

    // Use the explicitly passed csz (from handlePlaceSelect) or fall back to the prop
    const searchCsz = csz ?? cityStateZip;

    onSearchLoading(true);
    onSearchError(null);
    setUnitMatches(null);

    try {
      const res = await fetch("/api/proxy/v1/property/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          address: buildingAddress(searchAddr),
          city_state_zip: searchCsz || "",
        }),
      });

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(
          errBody.detail || errBody.message || "Property not found. Please check the address and try again."
        );
      }

      const responseData = await res.json();

      const matches = Array.isArray(responseData.multiple_matches)
        ? (responseData.multiple_matches as UnitMatch[])
        : [];
      if (matches.length > 1) {
        setUnitMatches(matches);
        return;
      }

      if (!responseData.success || !responseData.data) {
        throw new Error(
          responseData.error || "Property not found. Please verify the address."
        );
      }

      const mapped = withChosenUnit(mapSiteX(responseData.data, searchAddr));
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

  async function selectUnit(match: UnitMatch) {
    onSearchLoading(true);
    onSearchError(null);
    try {
      const res = await fetch("/api/proxy/v1/property/search-by-apn", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fips: match.fips, apn: match.apn }),
      });
      const responseData = await res.json().catch(() => ({}));
      if (!res.ok || !responseData.success || !responseData.data) {
        throw new Error(
          responseData.error || "Could not open that unit. Pick another."
        );
      }
      onPropertyFound(withChosenUnit(mapSiteX(responseData.data, match.address), match));
      setUnitMatches(null);
      if (!cityStateZip.trim()) {
        const d = responseData.data;
        onCityStateZipChange(`${d.city || match.city}, ${d.state || match.state} ${d.zip_code || match.zip_code}`);
      }
    } catch (err: any) {
      onSearchError(err.message || "Could not open that unit.");
    } finally {
      onSearchLoading(false);
    }
  }

  function handleSearch() {
    searchProperty();
  }

  const unitRows = unitMatches || [];
  const firstUnit = unitRows[0];
  const unitPlace = [
    firstUnit?.address ? prettyPlace(firstUnit.address) : "",
    firstUnit?.city ? prettyPlace(firstUnit.city) : "",
    [firstUnit?.state, firstUnit?.zip_code].filter(Boolean).join(" "),
  ]
    .filter(Boolean)
    .join(", ");

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

          <Dialog
            open={!!unitMatches && unitMatches.length > 0 && !property}
            onOpenChange={(open) => {
              if (!open && !searchLoading) setUnitMatches(null);
            }}
          >
            <DialogContent
              className="z-[2000] max-w-lg gap-0 overflow-hidden p-0"
              overlayClassName="z-[2000] bg-black/60"
              onInteractOutside={(event) => event.preventDefault()}
            >
              <div className="border-b border-[#E0E7FF] bg-[#F5F3FF] px-6 pt-6 pb-5 pr-12">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#4F46E5]">
                  {unitRows.length} units at this address
                </p>
                <DialogHeader className="mt-2 gap-2 text-left">
                  <DialogTitle className="text-xl tracking-tight">
                    Choose a unit
                  </DialogTitle>
                  <DialogDescription className="text-[15px] leading-relaxed text-foreground/80">
                    {unitPlace || "This street has more than one parcel."} The report uses the unit you pick, and nothing continues until you do.
                  </DialogDescription>
                </DialogHeader>
              </div>
              <ul className="max-h-[min(24rem,60vh)] space-y-2 overflow-y-auto p-4">
                {unitRows.map((match) => (
                  <li key={`${match.fips}-${match.apn}-${match.unit_number}`}>
                    <button
                      type="button"
                      className="group flex w-full items-center justify-between gap-4 rounded-xl border border-border bg-card px-4 py-3.5 text-left transition hover:border-[#6366F1] hover:bg-[#F8F7FF] disabled:opacity-50"
                      disabled={searchLoading}
                      onClick={() => selectUnit(match)}
                    >
                      <span className="min-w-0">
                        <span className="block text-base font-semibold text-foreground">
                          {parcelLabel(match)}
                        </span>
                        {match.apn ? (
                          <span className="mt-0.5 block text-xs text-muted-foreground">
                            APN {match.apn}
                          </span>
                        ) : null}
                      </span>
                      <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground transition group-hover:translate-x-0.5 group-hover:text-[#4F46E5]" />
                    </button>
                  </li>
                ))}
              </ul>
            </DialogContent>
          </Dialog>

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

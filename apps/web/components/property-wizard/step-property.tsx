"use client";

import { useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  RotateCcw,
  Loader2,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  AlertCircle,
} from "lucide-react";
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
import { FieldLabel, StepHeader } from "@/components/unified-wizard/wizard-ui";

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

  const facts: { k: string; v: string | null }[] = property
    ? [
        { k: "Beds", v: property.bedrooms ? String(property.bedrooms) : null },
        { k: "Baths", v: property.bathrooms ? String(property.bathrooms) : null },
        { k: "Sq ft", v: property.sqft ? property.sqft.toLocaleString() : null },
        { k: "Lot", v: property.lot_size > 0 ? `${property.lot_size.toLocaleString()} sf` : null },
        { k: "Built", v: property.year_built ? String(property.year_built) : null },
        {
          k: "Last sale",
          v: property.last_sale_price
            ? `$${Math.round(property.last_sale_price / 1000).toLocaleString()}K${
                property.last_sale_date ? ` · ${property.last_sale_date.slice(0, 4)}` : ""
              }`
            : null,
        },
      ]
    : [];

  return (
    <div className="flex flex-col gap-[26px]">
      <StepHeader
        title="Which home?"
        sub="We pull the public record so you don't type it."
      />

      {!property && (
        <div className="flex flex-col gap-2.5">
          <div className="relative">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-[#94A3B8]" />
            <Input
              ref={addressInputRef}
              placeholder={googleLoaded ? "Start typing an address..." : "Enter property address..."}
              className="h-[52px] rounded-[10px] border-[1.5px] border-[#D6D3CB] pl-[46px] text-[17px]"
              value={streetAddress}
              onChange={(e) => onStreetAddressChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleSearch();
                }
              }}
            />
          </div>
          <div className="flex gap-2">
            <Input
              placeholder="City, State ZIP"
              className="h-[52px] flex-1 rounded-[10px] border-[1.5px] border-[#D6D3CB] text-[17px]"
              value={cityStateZip}
              onChange={(e) => onCityStateZipChange(e.target.value)}
            />
            <button
              type="button"
              disabled={!streetAddress.trim() || searchLoading}
              onClick={handleSearch}
              className="inline-flex h-[52px] items-center gap-2 rounded-[10px] bg-[#0F172A] px-[18px] text-sm font-semibold text-white disabled:opacity-40"
            >
              {searchLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {searchLoading ? "Looking up…" : "Look up"}
            </button>
          </div>
          <span className="text-[13px] text-[#64748B]">
            {googleError
              ? <span className="text-[#B45309]">{googleError}</span>
              : cityStateZip
              ? "Auto-populated or edit manually"
              : "Street first, then city, state and ZIP."}
          </span>

          {searchError && (
            <div className="flex items-center gap-2 rounded-[10px] bg-[#FEF2F2] px-4 py-3 text-sm text-[#B91C1C]">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{searchError}</span>
            </div>
          )}
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

      {/* The public record, once found */}
      <AnimatePresence>
        {property && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="flex flex-col gap-4"
          >
            <div className="flex flex-col gap-1">
              <FieldLabel>
                Public record{property.county ? ` · ${property.county} County` : ""}
                {property.apn ? ` · APN ${property.apn}` : ""}
              </FieldLabel>
              <span className="text-[22px] font-extrabold leading-tight tracking-[-0.02em] text-[#0F172A]">
                {property.street_address}
              </span>
              <span className="text-[15px] text-[#64748B]">
                {property.city}, {property.state} {property.zip_code}
              </span>
            </div>

            <div className="grid grid-cols-3 border-t-[1.5px] border-[#0F172A]">
              {facts.map((f) => (
                <div key={f.k} className="flex flex-col gap-0.5 border-b border-[#ECEAE3] py-3 pr-2">
                  <span className="text-xs text-[#64748B]">{f.k}</span>
                  <span className={`text-[17px] font-bold ${f.v ? "text-[#0F172A]" : "text-[#5E636B]"}`}>
                    {f.v ?? "—"}
                  </span>
                </div>
              ))}
            </div>

            <div>
              <button
                type="button"
                className="flex items-center gap-1.5 text-sm font-semibold text-[#475569] hover:text-[#0F172A]"
                onClick={() => setDetailsOpen(!detailsOpen)}
              >
                {detailsOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                Assessment and taxes
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
                    <div className="mt-3 flex flex-col text-sm">
                      {[
                        ["Assessed value", property.assessed_value > 0 ? `$${property.assessed_value.toLocaleString()}` : "N/A"],
                        ["Annual taxes", property.tax_amount > 0 ? `$${property.tax_amount.toLocaleString()}` : "N/A"],
                      ].map(([k, v]) => (
                        <div key={k} className="flex justify-between border-b border-[#ECEAE3] py-2">
                          <span className="text-[#64748B]">{k}</span>
                          <span className="font-semibold text-[#0F172A]">{v}</span>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <button
              type="button"
              className="flex items-center gap-1.5 self-start text-sm font-semibold text-[#64748B] hover:text-[#0F172A]"
              onClick={onClear}
            >
              <RotateCcw className="h-4 w-4" />
              Look up a different home
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

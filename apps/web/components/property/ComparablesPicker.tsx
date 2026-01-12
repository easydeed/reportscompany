"use client";

import { useState } from "react";
import {
  MapPin,
  ArrowLeft,
  Check,
  Home,
  Bed,
  Bath,
  Square,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";

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

interface ComparablesPickerProps {
  availableComps: Comparable[];
  selectedIds: string[];
  onSelectionChange: (selectedIds: string[]) => void;
  onOpenMap: () => void;
  minSelections?: number;
  maxSelections?: number;
  subjectProperty?: {
    bedrooms?: number | null;
    bathrooms?: number | null;
    sqft?: number | null;
  };
  mapDisabled?: boolean;
}

export function ComparablesPicker({
  availableComps,
  selectedIds,
  onSelectionChange,
  onOpenMap,
  minSelections = 4,
  maxSelections = 8,
  subjectProperty,
  mapDisabled = false,
}: ComparablesPickerProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const selectedComps = availableComps.filter((c) => selectedIds.includes(c.id));
  const unselectedComps = availableComps.filter((c) => !selectedIds.includes(c.id));

  const handleSelect = (compId: string) => {
    if (selectedIds.length >= maxSelections) {
      return;
    }
    onSelectionChange([...selectedIds, compId]);
  };

  const handleDeselect = (compId: string) => {
    onSelectionChange(selectedIds.filter((id) => id !== compId));
  };

  const handleClearAll = () => {
    onSelectionChange([]);
  };

  // Auto-select recommended (closest + most similar)
  const handleAutoSelect = () => {
    const scored = availableComps.map((comp) => {
      let score = 0;

      // Closer = better (invert distance)
      if (comp.distance_miles) {
        score += Math.max(0, 10 - comp.distance_miles * 5);
      }

      // Similar sqft = better
      if (subjectProperty?.sqft && comp.sqft) {
        const sqftDiff = Math.abs(comp.sqft - subjectProperty.sqft) / subjectProperty.sqft;
        score += Math.max(0, 10 - sqftDiff * 20);
      }

      // Same beds = better
      if (subjectProperty?.bedrooms && comp.bedrooms === subjectProperty.bedrooms) {
        score += 5;
      }

      // Same baths = better
      if (subjectProperty?.bathrooms && comp.bathrooms === subjectProperty.bathrooms) {
        score += 3;
      }

      return { ...comp, score };
    });

    const topComps = scored
      .sort((a, b) => b.score - a.score)
      .slice(0, 6)
      .map((c) => c.id);

    onSelectionChange(topComps);
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const CompCard = ({
    comp,
    isSelected,
    onAction,
    orderNumber,
  }: {
    comp: Comparable;
    isSelected: boolean;
    onAction: () => void;
    orderNumber?: number;
  }) => (
    <div
      className={`
        relative border rounded-lg p-3 cursor-pointer transition-all
        ${
          isSelected
            ? "border-green-500 bg-green-50/50 dark:bg-green-950/20"
            : "border-border hover:border-primary/50 hover:bg-muted/50"
        }
        ${hoveredId === comp.id ? "ring-2 ring-primary/40" : ""}
      `}
      onClick={onAction}
      onMouseEnter={() => setHoveredId(comp.id)}
      onMouseLeave={() => setHoveredId(null)}
    >
      {/* Selection indicator */}
      <div
        className={`
          absolute top-2 right-2 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
          ${
            isSelected
              ? "bg-green-500 text-white"
              : "bg-muted text-muted-foreground"
          }
        `}
      >
        {isSelected ? (
          <Check className="w-3.5 h-3.5" />
        ) : (
          "+"
        )}
      </div>

      {/* Order number badge for selected items */}
      {orderNumber !== undefined && (
        <div className="absolute -left-2 top-1/2 -translate-y-1/2 w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center text-xs font-bold shadow-sm z-10">
          {orderNumber}
        </div>
      )}

      {/* Photo and details */}
      <div className="flex gap-3">
        <div className="w-20 h-16 flex-shrink-0 rounded-md overflow-hidden bg-muted">
          {comp.photo_url ? (
            <img
              src={comp.photo_url}
              alt={comp.address}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-muted to-muted/50">
              <Home className="w-6 h-6 text-muted-foreground/50" />
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm truncate pr-6">{comp.address}</p>
          {comp.city && (
            <p className="text-xs text-muted-foreground truncate">{comp.city}</p>
          )}

          <p className="text-base font-bold text-primary mt-1">
            {formatPrice(comp.price)}
          </p>

          <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground mt-1">
            <span className="flex items-center gap-1">
              <Bed className="w-3 h-3" /> {comp.bedrooms}
            </span>
            <span className="flex items-center gap-1">
              <Bath className="w-3 h-3" /> {comp.bathrooms}
            </span>
            <span className="flex items-center gap-1">
              <Square className="w-3 h-3" /> {comp.sqft?.toLocaleString()}
            </span>
            {comp.distance_miles !== undefined && (
              <span className="flex items-center gap-1">
                <MapPin className="w-3 h-3" /> {comp.distance_miles.toFixed(2)} mi
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Status badge */}
      {comp.status && (
        <div className="absolute bottom-2 right-2">
          <span
            className={`
              text-[10px] px-1.5 py-0.5 rounded font-medium
              ${
                comp.status.toLowerCase() === "closed" ||
                comp.status.toLowerCase() === "sold"
                  ? "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300"
                  : "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300"
              }
            `}
          >
            {comp.status}
          </span>
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-4">
      {/* Header with actions */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-semibold text-lg">Select Comparables</h3>
          <p className="text-sm text-muted-foreground">
            Choose {minSelections}-{maxSelections} properties to include in your report
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleAutoSelect}
            disabled={availableComps.length === 0}
          >
            <Sparkles className="w-4 h-4 mr-1.5" />
            Auto-Select Best
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onOpenMap}
            disabled={mapDisabled || availableComps.length === 0}
          >
            <MapPin className="w-4 h-4 mr-1.5" />
            View on Map
          </Button>
        </div>
      </div>

      {/* Selection status bar */}
      <div
        className={`
          p-3 rounded-lg flex items-center justify-between
          ${
            selectedIds.length < minSelections
              ? "bg-amber-50 border border-amber-200 dark:bg-amber-950/20 dark:border-amber-800"
              : "bg-green-50 border border-green-200 dark:bg-green-950/20 dark:border-green-800"
          }
        `}
      >
        <div className="flex items-center gap-2">
          {selectedIds.length < minSelections ? (
            <>
              <span className="text-amber-600 dark:text-amber-400">⚠️</span>
              <span className="text-sm text-amber-800 dark:text-amber-200">
                Select at least{" "}
                {minSelections - selectedIds.length} more comparable
                {minSelections - selectedIds.length > 1 ? "s" : ""}
              </span>
            </>
          ) : (
            <>
              <span className="text-green-600 dark:text-green-400">✓</span>
              <span className="text-sm text-green-800 dark:text-green-200">
                {selectedIds.length} comparable
                {selectedIds.length > 1 ? "s" : ""} selected
              </span>
            </>
          )}
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={handleClearAll}
          disabled={selectedIds.length === 0}
          className="text-xs h-7"
        >
          Clear All
        </Button>
      </div>

      {/* Two-column layout */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* Available (Unselected) */}
        <div className="border rounded-lg overflow-hidden">
          <div className="p-3 border-b bg-muted/50">
            <h4 className="font-medium text-sm flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-orange-500"></span>
              Available ({unselectedComps.length})
            </h4>
            <p className="text-xs text-muted-foreground">Click to add to report</p>
          </div>

          <div className="p-3 space-y-3 max-h-[450px] overflow-y-auto">
            {unselectedComps.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                {availableComps.length === 0
                  ? "No comparables found"
                  : "All comparables selected"}
              </p>
            ) : (
              unselectedComps.map((comp) => (
                <CompCard
                  key={comp.id}
                  comp={comp}
                  isSelected={false}
                  onAction={() => handleSelect(comp.id)}
                />
              ))
            )}
          </div>
        </div>

        {/* Selected */}
        <div className="border rounded-lg overflow-hidden border-green-300 dark:border-green-800">
          <div className="p-3 border-b bg-green-50/50 dark:bg-green-950/20">
            <h4 className="font-medium text-sm flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-green-500"></span>
              In Report ({selectedComps.length}/{maxSelections})
            </h4>
            <p className="text-xs text-muted-foreground">
              Click to remove from report
            </p>
          </div>

          <div className="p-3 space-y-3 max-h-[450px] overflow-y-auto">
            {selectedComps.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-14 h-14 bg-muted rounded-full flex items-center justify-center mx-auto mb-3">
                  <ArrowLeft className="w-7 h-7 text-muted-foreground/50" />
                </div>
                <p className="text-sm text-muted-foreground">
                  Select comparables from the left
                </p>
                <p className="text-xs text-muted-foreground/70 mt-1">
                  or use "Auto-Select Best" above
                </p>
              </div>
            ) : (
              selectedComps.map((comp, index) => (
                <div key={comp.id} className="ml-3">
                  <CompCard
                    comp={comp}
                    isSelected={true}
                    onAction={() => handleDeselect(comp.id)}
                    orderNumber={index + 1}
                  />
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Capacity warning */}
      {selectedIds.length >= maxSelections && (
        <p className="text-xs text-amber-600 dark:text-amber-400 text-center">
          Maximum {maxSelections} comparables reached. Remove one to add another.
        </p>
      )}
    </div>
  );
}

export default ComparablesPicker;


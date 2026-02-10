"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BarChart3, Info, Loader2, Map, Check, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ComparableCard } from "./comparable-card";
import { MapModal } from "./map-modal";
import type { Comparable, PropertyData } from "./types";
import { autoSelectComps } from "./types";

interface StepComparablesProps {
  comps: Comparable[];
  selectedCompIds: string[];
  compsLoading: boolean;
  compsError: string | null;
  property: PropertyData;
  onSelectedChange: (ids: string[]) => void;
}

export function StepComparables({
  comps,
  selectedCompIds,
  compsLoading,
  compsError,
  property,
  onSelectedChange,
}: StepComparablesProps) {
  const [mapOpen, setMapOpen] = useState(false);
  const [autoSelectLoading, setAutoSelectLoading] = useState(false);

  const availableComps = comps.filter((c) => !selectedCompIds.includes(c.id));
  const selectedComps = comps.filter((c) => selectedCompIds.includes(c.id));

  const isValid = selectedCompIds.length >= 4 && selectedCompIds.length <= 8;

  function toggleComp(id: string) {
    if (selectedCompIds.includes(id)) {
      onSelectedChange(selectedCompIds.filter((cid) => cid !== id));
    } else {
      if (selectedCompIds.length >= 8) return;
      onSelectedChange([...selectedCompIds, id]);
    }
  }

  function handleAutoSelect() {
    setAutoSelectLoading(true);
    // Small delay for UX feedback
    setTimeout(() => {
      const best = autoSelectComps(comps, property);
      onSelectedChange(best);
      setAutoSelectLoading(false);
    }, 400);
  }

  if (compsLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-[#6366F1]" />
        <p className="mt-3 text-sm text-muted-foreground">
          Loading comparables...
        </p>
      </div>
    );
  }

  if (compsError) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="rounded-lg bg-red-50 px-6 py-4 text-sm text-red-600 text-center">
          <p className="font-medium">Failed to load comparables</p>
          <p className="mt-1 text-red-500">{compsError}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-1">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-[#EEF2FF]">
            <BarChart3 className="h-5 w-5 text-[#6366F1]" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">
              Select Comparables
            </h2>
            <p className="text-sm text-muted-foreground">
              Choose 4-8 comparable sales for the report.
            </p>
          </div>
        </div>
      </div>

      {/* Controls Bar */}
      <div className="flex flex-wrap items-center gap-3">
        <Button
          variant="outline"
          size="sm"
          onClick={handleAutoSelect}
          disabled={autoSelectLoading || comps.length === 0}
          className="gap-1.5 bg-transparent"
        >
          {autoSelectLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Zap className="h-4 w-4" />
              Auto-Select Best Matches
            </>
          )}
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setMapOpen(true)}
          className="gap-1.5"
        >
          <Map className="h-4 w-4" />
          Map View
        </Button>
        <div
          className={`ml-auto px-3 py-1 rounded-full text-sm font-semibold ${
            isValid
              ? "bg-emerald-50 text-emerald-700"
              : "bg-[#EEF2FF] text-[#4338CA]"
          }`}
        >
          {selectedCompIds.length} of 8 selected
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Available */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <h3 className="text-sm font-semibold text-foreground">
              Available ({availableComps.length})
            </h3>
          </div>
          <ScrollArea className="h-[500px] pr-2">
            <div className="space-y-3">
              <AnimatePresence mode="popLayout">
                {availableComps.map((comp) => (
                  <ComparableCard
                    key={comp.id}
                    comp={comp}
                    isSelected={false}
                    onToggle={toggleComp}
                  />
                ))}
              </AnimatePresence>
              {availableComps.length === 0 && comps.length > 0 && (
                <div className="text-center text-sm text-muted-foreground py-8">
                  All comparables are in your report
                </div>
              )}
            </div>
          </ScrollArea>
        </div>

        {/* Selected */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            {isValid && (
              <div className="w-2 h-2 rounded-full bg-emerald-500" />
            )}
            <h3 className="text-sm font-semibold text-foreground">
              In Report ({selectedComps.length})
            </h3>
          </div>
          <ScrollArea className="h-[500px] pr-2">
            <div className="space-y-3">
              <AnimatePresence mode="popLayout">
                {selectedComps.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex flex-col items-center justify-center py-12 text-center rounded-xl border-2 border-dashed border-border"
                  >
                    <BarChart3 className="h-8 w-8 text-muted-foreground/40 mb-2" />
                    <p className="text-sm text-muted-foreground">
                      No comparables selected yet
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Click cards on the left to add them
                    </p>
                  </motion.div>
                ) : (
                  selectedComps.map((comp) => (
                    <ComparableCard
                      key={comp.id}
                      comp={comp}
                      isSelected={true}
                      onToggle={toggleComp}
                    />
                  ))
                )}
              </AnimatePresence>
            </div>
          </ScrollArea>
        </div>
      </div>

      {/* Validation */}
      <motion.div
        layout
        className={`flex items-center gap-2 text-sm px-4 py-3 rounded-lg ${
          isValid
            ? "bg-emerald-50 text-emerald-700"
            : "bg-muted text-muted-foreground"
        }`}
      >
        {isValid ? (
          <>
            <Check className="h-4 w-4" />
            {selectedCompIds.length} comparables selected — ready to continue
          </>
        ) : (
          <>
            <Info className="h-4 w-4" />
            Select 4-8 comparables to continue
          </>
        )}
      </motion.div>

      {/* Map Modal */}
      <MapModal
        open={mapOpen}
        onOpenChange={setMapOpen}
        comps={comps}
        selectedCompIds={selectedCompIds}
        property={property}
      />
    </div>
  );
}

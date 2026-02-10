"use client";

import { useMemo } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Home, MapPin } from "lucide-react";
import type { Comparable, PropertyData } from "./types";

interface MapModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  comps: Comparable[];
  selectedCompIds: string[];
  property?: PropertyData | null;
}

export function MapModal({
  open,
  onOpenChange,
  comps,
  selectedCompIds,
  property,
}: MapModalProps) {
  const selectedComps = comps.filter((c) => selectedCompIds.includes(c.id));

  // Build Google Static Map URL if we have coordinates
  const mapUrl = useMemo(() => {
    const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
    if (!apiKey || !property?.latitude || !property?.longitude) return null;

    const markers = [
      `markers=color:red%7Clabel:S%7C${property.latitude},${property.longitude}`,
      ...comps
        .map((c, i) => {
          if (!c.lat || !c.lng) return "";
          const color = selectedCompIds.includes(c.id)
            ? "0x6366F1"
            : "0xCCCCCC";
          return `markers=color:${color}%7Clabel:${i + 1}%7C${c.lat},${c.lng}`;
        })
        .filter(Boolean),
    ].join("&");

    return `https://maps.googleapis.com/maps/api/staticmap?size=800x500&maptype=roadmap&${markers}&key=${apiKey}`;
  }, [property, comps, selectedCompIds]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MapPin className="h-5 w-5 text-[#6366F1]" />
            Comparable Sales Map
          </DialogTitle>
        </DialogHeader>

        <div className="aspect-video rounded-xl bg-gradient-to-br from-slate-100 to-slate-200 relative overflow-hidden">
          {mapUrl ? (
            <img
              src={mapUrl}
              alt="Map of comparable sales"
              className="w-full h-full object-cover rounded-xl"
            />
          ) : (
            <>
              <div
                className="absolute inset-0"
                style={{
                  backgroundImage:
                    "linear-gradient(rgba(0,0,0,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,0.03) 1px, transparent 1px)",
                  backgroundSize: "40px 40px",
                }}
              />
              {/* Subject marker */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center z-10">
                <div className="w-7 h-7 rounded-full bg-red-500 border-2 border-white shadow-lg flex items-center justify-center">
                  <Home className="h-3.5 w-3.5 text-white" />
                </div>
                <span className="mt-1 text-[10px] font-bold bg-white px-1.5 py-0.5 rounded shadow text-foreground">
                  Subject
                </span>
              </div>
              {/* Comp markers */}
              {comps.map((comp, i) => {
                const isSelected = selectedCompIds.includes(comp.id);
                return (
                  <div
                    key={comp.id}
                    className="absolute flex flex-col items-center"
                    style={{
                      top: `${25 + Math.sin(i * 1.5) * 22}%`,
                      left: `${12 + i * 7}%`,
                    }}
                  >
                    <div
                      className={`w-6 h-6 rounded-full border-2 border-white shadow text-[9px] font-bold flex items-center justify-center ${
                        isSelected
                          ? "bg-[#6366F1] text-white"
                          : "bg-white text-muted-foreground border-muted-foreground/30"
                      }`}
                    >
                      {i + 1}
                    </div>
                  </div>
                );
              })}
            </>
          )}
        </div>

        {selectedComps.length > 0 && (
          <div className="mt-2">
            <p className="text-xs font-semibold text-muted-foreground mb-2">
              Selected Comparables ({selectedComps.length})
            </p>
            <ScrollArea className="w-full">
              <div className="flex gap-3 pb-2">
                {selectedComps.map((comp) => (
                  <div
                    key={comp.id}
                    className="shrink-0 w-48 rounded-lg border border-border bg-card p-3"
                  >
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 rounded-full bg-[#6366F1] text-[9px] font-bold text-white flex items-center justify-center shrink-0">
                        {comps.indexOf(comp) + 1}
                      </div>
                      <p className="text-xs font-semibold truncate text-foreground">
                        {comp.address}
                      </p>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      ${comp.sale_price.toLocaleString()} {"·"}{" "}
                      {comp.sqft.toLocaleString()} sqft
                    </p>
                  </div>
                ))}
              </div>
              <ScrollBar orientation="horizontal" />
            </ScrollArea>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

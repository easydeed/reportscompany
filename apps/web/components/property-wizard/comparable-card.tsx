"use client";

import { motion } from "framer-motion";
import { Check, Home, MapPin, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Comparable } from "./types";

interface ComparableCardProps {
  comp: Comparable;
  isSelected: boolean;
  onToggle: (id: string) => void;
}

export function ComparableCard({
  comp,
  isSelected,
  onToggle,
}: ComparableCardProps) {
  const formattedDate = new Date(comp.sold_date).toLocaleDateString("en-US", {
    month: "2-digit",
    day: "2-digit",
    year: "numeric",
  });

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      whileHover={{ y: -2 }}
      transition={{ duration: 0.2 }}
      className={`rounded-xl border-2 p-4 transition-all duration-200 cursor-pointer ${
        isSelected
          ? "border-[#6366F1] bg-[#EEF2FF]/50 shadow-md"
          : "border-border bg-card hover:shadow-md"
      }`}
      onClick={() => onToggle(comp.id)}
    >
      <div className="flex gap-3">
        <div className="aspect-[4/3] w-20 shrink-0 rounded-lg bg-muted flex items-center justify-center overflow-hidden">
          {comp.photo_url ? (
            <img
              src={comp.photo_url}
              alt={comp.address}
              className="w-full h-full object-cover"
            />
          ) : (
            <Home className="h-6 w-6 text-muted-foreground/50" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-foreground truncate">
            {comp.address}
          </p>
          <p className="text-xs text-muted-foreground">
            {comp.city}, {comp.state} {comp.zip}
          </p>
          <div className="flex items-center gap-1.5 mt-1">
            <span className="text-sm font-bold text-foreground">
              ${comp.sale_price.toLocaleString()}
            </span>
            <span className="text-muted-foreground text-xs">{"·"}</span>
            <span className="text-xs text-muted-foreground">
              Sold {formattedDate}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
        <span>
          {comp.bedrooms} bed {"·"} {comp.bathrooms} bath {"·"}{" "}
          {comp.sqft.toLocaleString()} sqft
        </span>
      </div>
      <div className="flex items-center gap-x-2 text-xs text-muted-foreground mt-1">
        <MapPin className="h-3 w-3" />
        <span>{comp.distance_miles} mi away</span>
        <span>{"·"}</span>
        <span>${comp.price_per_sqft}/sqft</span>
      </div>

      <div className="mt-3">
        <Button
          variant={isSelected ? "default" : "outline"}
          size="sm"
          className={`w-full text-xs ${
            isSelected
              ? "bg-[#6366F1] text-white hover:bg-[#4F46E5]"
              : ""
          }`}
          onClick={(e) => {
            e.stopPropagation();
            onToggle(comp.id);
          }}
        >
          {isSelected ? (
            <>
              <Check className="h-3.5 w-3.5 mr-1" />
              In Report
            </>
          ) : (
            <>
              <Plus className="h-3.5 w-3.5 mr-1" />
              Add to Report
            </>
          )}
        </Button>
      </div>
    </motion.div>
  );
}

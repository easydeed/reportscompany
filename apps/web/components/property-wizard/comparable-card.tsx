"use client";

import { motion } from "framer-motion";
import { Check, Home, MapPin, Plus } from "lucide-react";
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
  const isActive = comp.status === "Active";
  const displayDate = isActive ? comp.list_date : comp.sold_date;
  const formattedDate = displayDate
    ? new Date(displayDate).toLocaleDateString("en-US", {
        month: "2-digit",
        day: "2-digit",
        year: "numeric",
      })
    : "N/A";
  const displayPrice = isActive ? comp.list_price || comp.sale_price : comp.sale_price;

  // Design's Wizards v3 comps row: a check, the home, the price. The whole row
  // is one button that toggles, which is what the card's click already did;
  // the separate "Add to Report" button inside it is gone because a button
  // inside a button is not valid and did the same thing.
  return (
    <motion.button
      type="button"
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2 }}
      aria-pressed={isSelected}
      onClick={() => onToggle(comp.id)}
      className={`grid w-full items-center gap-3 rounded-xl border-[1.5px] p-2.5 text-left transition-colors ${
        isSelected ? "border-[#0F172A] bg-[#FAFAF7]" : "border-[#ECEAE3] bg-white hover:border-[#0F172A]"
      }`}
      style={{ gridTemplateColumns: "20px 56px minmax(0,1fr) auto" }}
    >
      <span
        className={`flex h-5 w-5 items-center justify-center rounded-full ${
          isSelected ? "bg-[#0F172A] text-white" : "border-[1.5px] border-[#CBD5E1] text-transparent"
        }`}
        aria-hidden
      >
        {isSelected ? <Check className="h-3 w-3" /> : <Plus className="h-3 w-3" />}
      </span>
      <span className="flex aspect-[4/3] w-14 items-center justify-center overflow-hidden rounded-md bg-[#F6F5F1]">
        {comp.photo_url ? (
          <img src={comp.photo_url} alt="" className="h-full w-full object-cover" />
        ) : (
          <Home className="h-5 w-5 text-[#94A3B8]" />
        )}
      </span>
      <span className="flex min-w-0 flex-col">
        <span className="truncate text-sm font-semibold text-[#0F172A]">{comp.address}</span>
        <span className="truncate text-xs text-[#5E636B]">
          {comp.bedrooms} bd · {comp.bathrooms} ba · {comp.sqft.toLocaleString()} sf · ${comp.price_per_sqft}/sf
        </span>
        <span className="flex items-center gap-1 text-xs text-[#5E636B]">
          <MapPin className="h-3 w-3" />
          {comp.distance_miles} mi ·{" "}
          {isActive ? `Active${comp.dom > 0 ? ` · ${comp.dom} DOM` : ""}` : `Sold ${formattedDate}`}
        </span>
      </span>
      <span className="text-sm font-semibold tabular-nums text-[#0F172A]">
        ${displayPrice.toLocaleString()}
      </span>
    </motion.button>
  );
}

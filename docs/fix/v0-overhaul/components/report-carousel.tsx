"use client";

import React from "react"

import { useState, useEffect, useCallback } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface ReportCard {
  title: string;
  gradient: string;
  content: React.ReactNode;
}

interface ReportCarouselProps {
  cards: ReportCard[];
  aspect?: "portrait" | "landscape";
}

export function ReportCarousel({ cards, aspect = "portrait" }: ReportCarouselProps) {
  const [current, setCurrent] = useState(0);

  const next = useCallback(() => {
    setCurrent((prev) => (prev + 1) % cards.length);
  }, [cards.length]);

  const prev = useCallback(() => {
    setCurrent((p) => (p - 1 + cards.length) % cards.length);
  }, [cards.length]);

  useEffect(() => {
    const interval = setInterval(next, 4000);
    return () => clearInterval(interval);
  }, [next]);

  const aspectClass = aspect === "portrait" ? "aspect-[9/16] max-w-sm" : "aspect-[4/3] max-w-lg";

  return (
    <div className="flex flex-col items-center gap-6">
      <div className="relative w-full flex items-center justify-center">
        {/* Previous button */}
        <button
          type="button"
          onClick={prev}
          className="absolute left-0 z-10 flex h-10 w-10 items-center justify-center rounded-full border border-border bg-card shadow-sm transition-colors hover:bg-muted"
          aria-label="Previous report"
        >
          <ChevronLeft className="h-5 w-5 text-foreground" />
        </button>

        {/* Card */}
        <div
          className={`${aspectClass} mx-auto w-full overflow-hidden rounded-2xl border border-border bg-card shadow-xl`}
        >
          {/* Header gradient */}
          <div className={`${cards[current].gradient} px-6 py-5`}>
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-md bg-white/20 text-xs font-bold text-white">
                TR
              </div>
              <p className="text-base font-semibold text-white">
                {cards[current].title}
              </p>
            </div>
          </div>
          {/* Content area */}
          <div className="p-6">{cards[current].content}</div>
        </div>

        {/* Next button */}
        <button
          type="button"
          onClick={next}
          className="absolute right-0 z-10 flex h-10 w-10 items-center justify-center rounded-full border border-border bg-card shadow-sm transition-colors hover:bg-muted"
          aria-label="Next report"
        >
          <ChevronRight className="h-5 w-5 text-foreground" />
        </button>
      </div>

      {/* Dot indicators */}
      <div className="flex items-center gap-2">
        {cards.map((card, i) => (
          <button
            key={card.title}
            type="button"
            onClick={() => setCurrent(i)}
            className={`h-2 rounded-full transition-all ${
              i === current
                ? "w-6 bg-[#6366F1]"
                : "w-2 bg-foreground/20"
            }`}
            aria-label={`Go to slide ${i + 1}`}
          />
        ))}
      </div>
    </div>
  );
}

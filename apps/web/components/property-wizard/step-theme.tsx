"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Check, Eye, Lock, Palette } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { Theme, ReportPage } from "./types";
import { THEMES, ACCENT_PRESETS } from "./types";

interface StepThemeProps {
  selectedThemeId: number;
  accentColor: string;
  selectedPageIds: string[];
  pages: ReportPage[];
  onThemeChange: (id: number) => void;
  onAccentChange: (color: string) => void;
  onPagesChange: (ids: string[]) => void;
}

export function StepTheme({
  selectedThemeId,
  accentColor,
  selectedPageIds,
  pages,
  onThemeChange,
  onAccentChange,
  onPagesChange,
}: StepThemeProps) {
  const [previewOpen, setPreviewOpen] = useState(false);
  const selectedTheme = THEMES.find((t) => t.id === selectedThemeId);

  function togglePage(pageId: string) {
    const page = pages.find((p) => p.id === pageId);
    if (page?.required) return;
    if (selectedPageIds.includes(pageId)) {
      onPagesChange(selectedPageIds.filter((id) => id !== pageId));
    } else {
      onPagesChange([...selectedPageIds, pageId]);
    }
  }

  function selectAll() {
    onPagesChange(pages.map((p) => p.id));
  }

  function selectMinimum() {
    onPagesChange(pages.filter((p) => p.required).map((p) => p.id));
  }

  return (
    <div className="space-y-8">
      {/* Theme Gallery */}
      <div>
        <div className="flex items-center gap-3 mb-4">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-[#EEF2FF]">
            <Palette className="h-5 w-5 text-[#6366F1]" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">
              Choose Your Theme
            </h2>
            <p className="text-sm text-muted-foreground">
              Each theme creates a distinct personality for your report.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          {THEMES.map((theme) => {
            const isSelected = selectedThemeId === theme.id;
            return (
              <motion.button
                key={theme.id}
                type="button"
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={() => onThemeChange(theme.id)}
                className={`relative rounded-xl border-2 overflow-hidden transition-all duration-200 text-left ${
                  isSelected
                    ? "border-[#6366F1] ring-2 ring-[#6366F1]/20 scale-[1.02]"
                    : "border-border hover:border-[#C7D2FE]"
                }`}
              >
                {/* Theme preview */}
                <div
                  className="aspect-[8.5/11] relative overflow-hidden"
                  style={{ background: theme.gradient }}
                >
                  <div className="h-full flex flex-col justify-between p-3">
                    <div>
                      <p className="text-[7px] uppercase tracking-[0.2em] text-white/50">
                        Property Report
                      </p>
                      <p
                        className="text-[11px] font-bold text-white mt-0.5 leading-tight"
                        style={{ fontFamily: theme.displayFont }}
                      >
                        {theme.name}
                      </p>
                    </div>
                    {/* Decorative lines */}
                    <div className="space-y-1">
                      <div className="h-[1px] w-3/4 bg-white/20 rounded-full" />
                      <div className="h-[1px] w-1/2 bg-white/15 rounded-full" />
                      <div className="h-[1px] w-2/3 bg-white/10 rounded-full" />
                    </div>
                    <div
                      className="h-0.5 rounded-full"
                      style={{ backgroundColor: theme.accentDefault }}
                    />
                  </div>

                  {/* Selected check */}
                  {isSelected && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="absolute top-2 right-2 w-6 h-6 rounded-full bg-[#6366F1] flex items-center justify-center shadow-lg"
                    >
                      <Check className="h-3.5 w-3.5 text-white" />
                    </motion.div>
                  )}
                </div>

                {/* Info strip */}
                <div className="p-2.5 bg-card">
                  <p className="text-xs font-semibold text-foreground">
                    {theme.name}
                  </p>
                  <p className="text-[10px] text-muted-foreground">
                    {theme.style}
                  </p>
                  <p className="text-[10px] text-muted-foreground mt-0.5">
                    {theme.pageCount} pages
                  </p>
                </div>
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Accent Color Picker */}
      <div className="rounded-2xl border border-border bg-card p-5">
        <h3 className="text-sm font-semibold text-foreground mb-3">
          Accent Color
        </h3>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex gap-2">
            {ACCENT_PRESETS.map((color) => (
              <button
                key={color}
                type="button"
                className={`w-7 h-7 rounded-full transition-all duration-150 ${
                  accentColor === color
                    ? "ring-2 ring-offset-2 ring-[#6366F1]"
                    : "hover:scale-110"
                }`}
                style={{ backgroundColor: color }}
                onClick={() => onAccentChange(color)}
                aria-label={`Select color ${color}`}
              />
            ))}
          </div>
          <div className="flex items-center gap-2 ml-2">
            <Input
              value={accentColor}
              onChange={(e) => onAccentChange(e.target.value)}
              className="w-24 h-8 text-xs font-mono rounded-lg"
            />
            <div
              className="w-8 h-8 rounded-lg border border-border shrink-0"
              style={{ backgroundColor: accentColor }}
            />
          </div>
        </div>
      </div>

      {/* Report Pages */}
      <div className="rounded-2xl border border-border bg-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div>
            <h3 className="text-sm font-semibold text-foreground">
              Report Pages
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              {pages.length} pages available {"·"} {selectedPageIds.length}{" "}
              selected
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={selectAll}>
              Select All
            </Button>
            <Button variant="outline" size="sm" onClick={selectMinimum}>
              Minimum Only
            </Button>
          </div>
        </div>

        <TooltipProvider>
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-7 gap-3">
            {pages.map((page) => {
              const isSelected = selectedPageIds.includes(page.id);
              return (
                <Tooltip key={page.id}>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={() => togglePage(page.id)}
                      className={`relative aspect-[8.5/11] rounded-lg border-2 transition-all duration-200 flex flex-col items-center justify-center p-1.5 text-center ${
                        isSelected
                          ? "border-[#6366F1] bg-[#EEF2FF]"
                          : "border-border bg-card opacity-60 hover:opacity-100"
                      }`}
                    >
                      {/* Mini page decoration */}
                      <div className="space-y-1 w-full px-1 mb-1.5">
                        <div
                          className={`h-[2px] w-3/4 mx-auto rounded-full ${
                            isSelected
                              ? "bg-[#6366F1]/30"
                              : "bg-muted-foreground/20"
                          }`}
                        />
                        <div
                          className={`h-[2px] w-1/2 mx-auto rounded-full ${
                            isSelected
                              ? "bg-[#6366F1]/20"
                              : "bg-muted-foreground/15"
                          }`}
                        />
                        <div
                          className={`h-[2px] w-2/3 mx-auto rounded-full ${
                            isSelected
                              ? "bg-[#6366F1]/15"
                              : "bg-muted-foreground/10"
                          }`}
                        />
                      </div>

                      {/* Selected check */}
                      {isSelected && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="absolute top-1 right-1 w-4 h-4 rounded-full bg-[#6366F1] flex items-center justify-center"
                        >
                          <Check className="h-2.5 w-2.5 text-white" />
                        </motion.div>
                      )}

                      {/* Required lock */}
                      {page.required && (
                        <div className="absolute bottom-1 right-1">
                          <Lock className="h-2.5 w-2.5 text-muted-foreground" />
                        </div>
                      )}
                    </button>
                  </TooltipTrigger>
                  {page.required && (
                    <TooltipContent>
                      <p>This page is required</p>
                    </TooltipContent>
                  )}
                  <p className="text-[10px] font-medium text-center mt-1.5 text-foreground leading-tight">
                    {page.name}
                  </p>
                </Tooltip>
              );
            })}
          </div>
        </TooltipProvider>
      </div>

      {/* Live Preview Button */}
      <div className="flex justify-end">
        <Button
          variant="outline"
          className="gap-2 bg-transparent"
          onClick={() => setPreviewOpen(true)}
        >
          <Eye className="h-4 w-4" />
          Live Preview
        </Button>
      </div>

      {/* Preview Dialog */}
      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Report Preview</DialogTitle>
          </DialogHeader>
          <div
            className="aspect-[8.5/11] rounded-xl overflow-hidden"
            style={{
              background:
                selectedTheme?.gradient ||
                "linear-gradient(135deg, #18235c, #34d1c3)",
            }}
          >
            <div className="h-full flex flex-col items-center justify-center text-center p-8">
              <p className="text-xs uppercase tracking-[0.2em] text-white/60">
                Property Report
              </p>
              <p
                className="text-lg font-bold text-white mt-2"
                style={{ fontFamily: selectedTheme?.displayFont }}
              >
                {selectedTheme?.name} Theme
              </p>
              <div
                className="h-0.5 w-16 rounded-full mt-4"
                style={{ backgroundColor: accentColor }}
              />
              <p className="text-xs text-white/50 mt-4">
                Full preview available after generation
              </p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

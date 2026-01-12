"use client";

import { useState, useEffect } from "react";
import { Check, Eye, ChevronLeft, ChevronRight, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

// Theme definitions matching seller_report.jinja2
const THEMES = [
  {
    id: 1,
    name: "Classic",
    description: "Professional navy with elegant fonts",
    defaultColor: "#0d294b",
    previewBg: "bg-gradient-to-br from-slate-800 to-slate-900",
    fontStyle: "font-serif",
  },
  {
    id: 2,
    name: "Modern",
    description: "Bold orange accents, clean lines",
    defaultColor: "#f2964a",
    previewBg: "bg-gradient-to-br from-orange-400 to-orange-600",
    fontStyle: "font-sans",
  },
  {
    id: 3,
    name: "Elegant",
    description: "Sophisticated gradient overlays",
    defaultColor: "#0d294b",
    previewBg: "bg-gradient-to-br from-slate-700 to-indigo-900",
    fontStyle: "font-serif",
  },
  {
    id: 4,
    name: "Teal",
    description: "Modern minimal with teal accent",
    defaultColor: "#16d3ba",
    previewBg: "bg-gradient-to-br from-teal-400 to-cyan-600",
    fontStyle: "font-sans",
  },
  {
    id: 5,
    name: "Bold",
    description: "Navy & gold, strong typography",
    defaultColor: "#d79547",
    previewBg: "bg-gradient-to-br from-slate-800 to-amber-900",
    fontStyle: "font-bold",
  },
];

// All available pages in the seller report
const ALL_PAGES = [
  { id: "cover", name: "Cover", description: "Property photo, address, agent info", required: true },
  { id: "contents", name: "Table of Contents", description: "Report overview" },
  { id: "introduction", name: "Introduction", description: "Welcome message from agent" },
  { id: "aerial", name: "Aerial View", description: "Google Maps satellite view" },
  { id: "property_details", name: "Property Details", description: "Owner, APN, beds/baths, tax info", required: true },
  { id: "area_analysis", name: "Area Sales Analysis", description: "Market statistics chart" },
  { id: "comparables", name: "Sales Comparables", description: "Recently sold properties", required: true },
  { id: "range_of_sales", name: "Range of Sales", description: "Price range visualization" },
  { id: "neighborhood", name: "Neighborhood Stats", description: "Demographics and averages" },
  { id: "roadmap", name: "Selling Roadmap", description: "Process overview" },
  { id: "how_buyers_find", name: "How Buyers Find Homes", description: "Marketing channels pie chart" },
  { id: "pricing_correctly", name: "Pricing Strategy", description: "Pricing guidance" },
  { id: "avg_days_market", name: "Days on Market", description: "Market timing analysis" },
  { id: "marketing_online", name: "Digital Marketing", description: "Online marketing plan" },
  { id: "marketing_print", name: "Print Marketing", description: "Traditional marketing" },
  { id: "marketing_social", name: "Social Media", description: "Social proof and reach" },
  { id: "analyze_optimize", name: "Analyze & Optimize", description: "Ongoing strategy" },
  { id: "negotiating", name: "Negotiating Offers", description: "Offer handling process" },
  { id: "typical_transaction", name: "Transaction Timeline", description: "Escrow process flowchart" },
  { id: "promise", name: "Agent Promise", description: "Fiduciary commitment" },
  { id: "back_cover", name: "Back Cover", description: "Branded closing page", required: true },
];

// Compact page set (for themes 4 & 5)
const COMPACT_PAGES = [
  "cover", "introduction", "aerial", "property_details", "comparables",
  "pricing_correctly", "marketing_online", "promise", "back_cover"
];

interface ThemeSelectorProps {
  selectedTheme: number;
  onThemeChange: (theme: number) => void;
  accentColor: string;
  onAccentColorChange: (color: string) => void;
  selectedPages: string[];
  onPagesChange: (pages: string[]) => void;
  propertyAddress?: string;
}

export function ThemeSelector({
  selectedTheme,
  onThemeChange,
  accentColor,
  onAccentColorChange,
  selectedPages,
  onPagesChange,
  propertyAddress,
}: ThemeSelectorProps) {
  const [previewPage, setPreviewPage] = useState<string | null>(null);

  const currentTheme = THEMES.find((t) => t.id === selectedTheme) || THEMES[0];

  // Determine available pages based on theme
  const availablePages = selectedTheme >= 4
    ? ALL_PAGES.filter(p => COMPACT_PAGES.includes(p.id))
    : ALL_PAGES;

  // Initialize selected pages when theme changes
  useEffect(() => {
    if (selectedTheme >= 4) {
      // Compact themes default to compact pages
      onPagesChange(COMPACT_PAGES);
    } else if (selectedPages.length === 0 || selectedPages.length === COMPACT_PAGES.length) {
      // Full themes default to all pages
      onPagesChange(ALL_PAGES.map(p => p.id));
    }
  }, [selectedTheme]);

  const handlePageToggle = (pageId: string) => {
    const page = ALL_PAGES.find(p => p.id === pageId);
    if (page?.required) return; // Can't toggle required pages

    if (selectedPages.includes(pageId)) {
      onPagesChange(selectedPages.filter(id => id !== pageId));
    } else {
      onPagesChange([...selectedPages, pageId]);
    }
  };

  const handleSelectAll = () => {
    onPagesChange(availablePages.map(p => p.id));
  };

  const handleSelectMinimum = () => {
    onPagesChange(availablePages.filter(p => p.required).map(p => p.id));
  };

  // Preset accent colors
  const presetColors = [
    "#0d294b", // Navy
    "#1e40af", // Blue
    "#7c3aed", // Purple
    "#059669", // Green
    "#16d3ba", // Teal
    "#d97706", // Amber
    "#dc2626", // Red
    "#be185d", // Pink
    "#374151", // Gray
    "#000000", // Black
  ];

  return (
    <div className="space-y-8">
      {/* Theme Selection */}
      <div>
        <h3 className="font-semibold text-lg mb-4">Choose Your Theme</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {THEMES.map((theme) => (
            <button
              key={theme.id}
              onClick={() => onThemeChange(theme.id)}
              className={`
                relative rounded-lg overflow-hidden border-2 transition-all text-left
                ${selectedTheme === theme.id
                  ? "border-primary ring-2 ring-primary ring-offset-2"
                  : "border-border hover:border-muted-foreground/50"
                }
              `}
            >
              {/* Theme Preview */}
              <div className={`${theme.previewBg} h-32 p-3 flex flex-col justify-between`}>
                <div className="text-white text-left">
                  <div className={`text-xs opacity-75 ${theme.fontStyle}`}>Seller&apos;s Report</div>
                  <div className={`text-sm font-semibold ${theme.fontStyle}`}>123 Main St</div>
                </div>
                <div className="flex justify-between items-end">
                  <div
                    className="w-6 h-6 rounded-full border-2 border-white"
                    style={{ backgroundColor: theme.defaultColor }}
                  />
                  {theme.id >= 4 && (
                    <span className="text-[10px] bg-white/20 text-white px-1.5 py-0.5 rounded">
                      9 pages
                    </span>
                  )}
                </div>
              </div>

              {/* Theme Info */}
              <div className="p-2 bg-background">
                <p className="font-medium text-sm">{theme.name}</p>
                <p className="text-xs text-muted-foreground truncate">{theme.description}</p>
              </div>

              {/* Selected Checkmark */}
              {selectedTheme === theme.id && (
                <div className="absolute top-2 right-2 w-6 h-6 bg-primary rounded-full flex items-center justify-center">
                  <Check className="w-4 h-4 text-primary-foreground" />
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Accent Color */}
      <div>
        <h3 className="font-semibold text-lg mb-4">Accent Color</h3>
        <div className="flex flex-wrap items-center gap-3">
          {presetColors.map((color) => (
            <button
              key={color}
              onClick={() => onAccentColorChange(color)}
              className={`
                w-10 h-10 rounded-full border-2 transition-all
                ${accentColor === color
                  ? "border-foreground ring-2 ring-offset-2 ring-muted-foreground scale-110"
                  : "border-border hover:border-muted-foreground"
                }
              `}
              style={{ backgroundColor: color }}
              title={color}
            />
          ))}

          {/* Custom color input */}
          <div className="flex items-center gap-2 ml-4 pl-4 border-l">
            <Label className="text-sm text-muted-foreground">Custom:</Label>
            <input
              type="color"
              value={accentColor}
              onChange={(e) => onAccentColorChange(e.target.value)}
              className="w-10 h-10 rounded cursor-pointer border-0 bg-transparent"
            />
            <Input
              type="text"
              value={accentColor}
              onChange={(e) => onAccentColorChange(e.target.value)}
              placeholder="#000000"
              className="w-24 h-9 font-mono text-sm"
            />
          </div>
        </div>
      </div>

      {/* Page Selection */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-lg">Report Pages</h3>
            <p className="text-sm text-muted-foreground">
              {selectedPages.length} of {availablePages.length} pages selected
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={handleSelectAll}>
              Select All
            </Button>
            <span className="text-muted-foreground/30">|</span>
            <Button variant="ghost" size="sm" onClick={handleSelectMinimum}>
              Minimum Only
            </Button>
          </div>
        </div>

        {/* Page Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
          {availablePages.map((page, index) => {
            const isSelected = selectedPages.includes(page.id);
            const isRequired = page.required;

            return (
              <div
                key={page.id}
                onClick={() => !isRequired && handlePageToggle(page.id)}
                className={`
                  relative rounded-lg border-2 overflow-hidden transition-all
                  ${isRequired ? "cursor-default" : "cursor-pointer"}
                  ${isSelected
                    ? "border-green-500 bg-green-50 dark:bg-green-950/20"
                    : "border-border bg-muted/30 opacity-60"
                  }
                  ${!isRequired && !isSelected ? "hover:opacity-100 hover:border-muted-foreground/50" : ""}
                `}
              >
                {/* Page Preview Thumbnail */}
                <div
                  className={`
                    h-24 ${currentTheme.previewBg}
                    flex items-center justify-center relative
                  `}
                >
                  <span className="text-white text-2xl font-bold opacity-30">
                    {index + 1}
                  </span>

                  {/* Preview button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setPreviewPage(page.id);
                    }}
                    className="absolute top-1 right-1 p-1.5 bg-black/30 rounded hover:bg-black/50 transition-colors"
                    title="Preview page"
                  >
                    <Eye className="w-3 h-3 text-white" />
                  </button>
                </div>

                {/* Page Info */}
                <div className="p-2">
                  <div className="flex items-start justify-between gap-1">
                    <div className="min-w-0">
                      <p className="font-medium text-xs truncate">{page.name}</p>
                      <p className="text-[10px] text-muted-foreground truncate">{page.description}</p>
                    </div>

                    {/* Checkbox */}
                    <div className={`
                      flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center transition-colors
                      ${isSelected
                        ? "bg-green-500 border-green-500"
                        : "bg-background border-muted-foreground/30"
                      }
                      ${isRequired ? "opacity-50" : ""}
                    `}>
                      {isSelected && <Check className="w-3 h-3 text-white" />}
                    </div>
                  </div>

                  {isRequired && (
                    <span className="text-[9px] text-amber-600 dark:text-amber-400 font-medium">Required</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Theme note for compact themes */}
        {selectedTheme >= 4 && (
          <p className="text-sm text-amber-600 dark:text-amber-400 mt-4 p-3 bg-amber-50 dark:bg-amber-950/30 rounded-lg border border-amber-200 dark:border-amber-800">
            ℹ️ {currentTheme.name} theme uses a compact 9-page format.
            Switch to Classic, Modern, or Elegant for the full 21-page report.
          </p>
        )}
      </div>

      {/* Page Preview Modal */}
      {previewPage && (
        <PagePreviewModal
          pageId={previewPage}
          theme={currentTheme}
          accentColor={accentColor}
          propertyAddress={propertyAddress}
          onClose={() => setPreviewPage(null)}
          onPrevious={() => {
            const currentIndex = availablePages.findIndex(p => p.id === previewPage);
            if (currentIndex > 0) {
              setPreviewPage(availablePages[currentIndex - 1].id);
            }
          }}
          onNext={() => {
            const currentIndex = availablePages.findIndex(p => p.id === previewPage);
            if (currentIndex < availablePages.length - 1) {
              setPreviewPage(availablePages[currentIndex + 1].id);
            }
          }}
          hasPrevious={availablePages.findIndex(p => p.id === previewPage) > 0}
          hasNext={availablePages.findIndex(p => p.id === previewPage) < availablePages.length - 1}
        />
      )}
    </div>
  );
}

// Page Preview Modal Component
function PagePreviewModal({
  pageId,
  theme,
  accentColor,
  propertyAddress,
  onClose,
  onPrevious,
  onNext,
  hasPrevious,
  hasNext,
}: {
  pageId: string;
  theme: typeof THEMES[0];
  accentColor: string;
  propertyAddress?: string;
  onClose: () => void;
  onPrevious: () => void;
  onNext: () => void;
  hasPrevious: boolean;
  hasNext: boolean;
}) {
  const page = ALL_PAGES.find(p => p.id === pageId);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft" && hasPrevious) onPrevious();
      if (e.key === "ArrowRight" && hasNext) onNext();
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [hasPrevious, hasNext, onPrevious, onNext, onClose]);

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-background rounded-xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div>
            <h3 className="font-semibold">{page?.name}</h3>
            <p className="text-sm text-muted-foreground">{page?.description}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Preview Area */}
        <div className="flex-1 overflow-auto p-8 bg-muted/50 flex items-center justify-center">
          {/* Page Preview - Letter size aspect ratio (8.5 x 11) */}
          <div
            className="bg-white shadow-2xl relative rounded-sm"
            style={{
              width: "min(100%, 510px)",
              aspectRatio: "8.5 / 11",
            }}
          >
            {/* Simulated page content based on page type */}
            <div className={`absolute inset-0 ${theme.previewBg} opacity-5 rounded-sm`} />

            <div className="absolute inset-0 p-8 flex flex-col">
              {/* Header bar with accent color */}
              <div
                className="h-1 w-24 mb-4 rounded"
                style={{ backgroundColor: accentColor }}
              />

              {/* Page title */}
              <h2 className={`text-2xl mb-2 ${theme.fontStyle}`} style={{ color: accentColor }}>
                {page?.name}
              </h2>

              {/* Simulated content */}
              <div className="flex-1 space-y-4 mt-4">
                {pageId === "cover" && (
                  <>
                    <div className="h-48 bg-gray-200 rounded flex items-center justify-center">
                      <span className="text-gray-400">Property Photo</span>
                    </div>
                    <div className="text-center mt-4">
                      <p className="text-sm text-gray-400 tracking-widest">SELLER&apos;S REPORT</p>
                      <p className="text-xl font-semibold mt-2">{propertyAddress || "123 Main Street"}</p>
                    </div>
                  </>
                )}

                {pageId === "property_details" && (
                  <div className="grid grid-cols-2 gap-4">
                    {["Owner Info", "Location", "Beds/Baths", "Tax Info"].map((section) => (
                      <div key={section} className="border rounded p-3">
                        <p className="text-xs text-gray-400 uppercase">{section}</p>
                        <div className="h-4 bg-gray-200 rounded mt-2 w-3/4" />
                        <div className="h-4 bg-gray-100 rounded mt-1 w-1/2" />
                      </div>
                    ))}
                  </div>
                )}

                {pageId === "comparables" && (
                  <div className="grid grid-cols-2 gap-3">
                    {[1, 2, 3, 4].map((n) => (
                      <div key={n} className="border rounded p-2">
                        <div className="h-16 bg-gray-200 rounded mb-2" />
                        <div className="h-3 bg-gray-300 rounded w-3/4" />
                        <div className="h-3 bg-gray-200 rounded w-1/2 mt-1" />
                      </div>
                    ))}
                  </div>
                )}

                {pageId === "aerial" && (
                  <div className="h-48 bg-gradient-to-br from-green-200 to-blue-200 rounded flex items-center justify-center">
                    <span className="text-gray-500">Satellite Map View</span>
                  </div>
                )}

                {!["cover", "property_details", "comparables", "aerial"].includes(pageId) && (
                  <>
                    <div className="h-4 bg-gray-200 rounded w-full" />
                    <div className="h-4 bg-gray-200 rounded w-5/6" />
                    <div className="h-4 bg-gray-200 rounded w-4/6" />
                    <div className="h-32 bg-gray-100 rounded mt-4 flex items-center justify-center">
                      <span className="text-gray-400 text-sm">Content Area</span>
                    </div>
                    <div className="h-4 bg-gray-200 rounded w-full mt-4" />
                    <div className="h-4 bg-gray-200 rounded w-3/4" />
                  </>
                )}
              </div>

              {/* Footer */}
              <div className="flex justify-between items-end pt-4 border-t border-gray-200 mt-auto">
                <div className="h-8 w-8 rounded-full bg-gray-200" />
                <div className="text-xs text-gray-400">Page Preview</div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Navigation */}
        <div className="flex items-center justify-between p-4 border-t">
          <Button
            variant="ghost"
            onClick={onPrevious}
            disabled={!hasPrevious}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Previous
          </Button>

          <span className="text-sm text-muted-foreground">
            Press ← → to navigate
          </span>

          <Button
            variant="ghost"
            onClick={onNext}
            disabled={!hasNext}
          >
            Next
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      </div>
    </div>
  );
}

export default ThemeSelector;


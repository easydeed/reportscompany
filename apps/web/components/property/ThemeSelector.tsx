"use client";

import { useState, useEffect, useCallback } from "react";
import { Check, Eye, ChevronLeft, ChevronRight, X, ImageOff, Loader2, Maximize2, Minimize2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  THEMES,
  getTheme,
  getThemePages,
  getThemeCoverUrl,
  getPagePreviewUrl,
  isCompactTheme,
  type ThemeConfig,
  type PageConfig,
} from "@/lib/property-report-assets";

interface ThemeSelectorProps {
  selectedTheme: number;
  onThemeChange: (theme: number) => void;
  accentColor: string;
  onAccentColorChange: (color: string) => void;
  selectedPages: string[];
  onPagesChange: (pages: string[]) => void;
  propertyAddress?: string;
  // New props for live preview
  propertyData?: any;
  comparables?: any[];
}

export function ThemeSelector({
  selectedTheme,
  onThemeChange,
  accentColor,
  onAccentColorChange,
  selectedPages,
  onPagesChange,
  propertyAddress,
  propertyData,
  comparables,
}: ThemeSelectorProps) {
  const [previewPage, setPreviewPage] = useState<string | null>(null);
  const [imageErrors, setImageErrors] = useState<Record<string, boolean>>({});
  
  // Live preview state
  const [showLivePreview, setShowLivePreview] = useState(false);
  const [livePreviewHtml, setLivePreviewHtml] = useState<string | null>(null);
  const [livePreviewLoading, setLivePreviewLoading] = useState(false);
  const [livePreviewExpanded, setLivePreviewExpanded] = useState(false);

  const currentTheme = getTheme(selectedTheme) || THEMES[0];
  const availablePages = getThemePages(selectedTheme);
  
  // Fetch live preview HTML
  const fetchLivePreview = useCallback(async () => {
    if (!propertyData) return;
    
    setLivePreviewLoading(true);
    try {
      const response = await fetch('/api/proxy/v1/property/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          theme: selectedTheme,
          accent_color: accentColor,
          property_address: propertyData.full_address || propertyAddress || '',
          property_city: propertyData.city || '',
          property_state: propertyData.state || 'CA',
          property_zip: propertyData.zip_code || '',
          sitex_data: propertyData,
          comparables: comparables || [],
        }),
      });
      
      if (response.ok) {
        const html = await response.text();
        setLivePreviewHtml(html);
      } else {
        console.error('Preview failed:', response.status);
        setLivePreviewHtml(null);
      }
    } catch (error) {
      console.error('Preview error:', error);
      setLivePreviewHtml(null);
    } finally {
      setLivePreviewLoading(false);
    }
  }, [selectedTheme, accentColor, propertyData, propertyAddress, comparables]);
  
  // Refresh preview when theme or accent color changes
  useEffect(() => {
    if (showLivePreview && propertyData) {
      const debounce = setTimeout(() => {
        fetchLivePreview();
      }, 500); // Debounce to avoid too many requests
      return () => clearTimeout(debounce);
    }
  }, [selectedTheme, accentColor, showLivePreview, fetchLivePreview, propertyData]);

  // Initialize selected pages when theme changes
  useEffect(() => {
    const themePages = getThemePages(selectedTheme);
    if (isCompactTheme(selectedTheme)) {
      // Compact themes default to all their pages
      onPagesChange(themePages.map(p => p.id));
    } else if (selectedPages.length === 0 || selectedPages.length <= 9) {
      // Full themes default to all pages
      onPagesChange(themePages.map(p => p.id));
    }
  }, [selectedTheme]);

  const handlePageToggle = (pageId: string) => {
    const page = availablePages.find(p => p.id === pageId);
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

  // Track image load errors
  const handleImageError = (key: string) => {
    setImageErrors(prev => ({ ...prev, [key]: true }));
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
      {/* Theme Selection with Live Preview Toggle */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-lg">Choose Your Theme</h3>
          {propertyData && (
            <Button
              variant={showLivePreview ? "default" : "outline"}
              size="sm"
              onClick={() => setShowLivePreview(!showLivePreview)}
              className="gap-2"
            >
              <Eye className="w-4 h-4" />
              {showLivePreview ? "Hide Preview" : "Live Preview"}
            </Button>
          )}
        </div>
        
        {/* Live Preview Panel */}
        {showLivePreview && (
          <div className={`mb-6 border rounded-xl overflow-hidden bg-muted/30 transition-all ${
            livePreviewExpanded ? "fixed inset-4 z-50 bg-background" : ""
          }`}>
            <div className="flex items-center justify-between px-4 py-2 bg-muted border-b">
              <span className="text-sm font-medium">
                Live Preview - {currentTheme.name} Theme
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => fetchLivePreview()}
                  disabled={livePreviewLoading}
                >
                  {livePreviewLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => setLivePreviewExpanded(!livePreviewExpanded)}
                >
                  {livePreviewExpanded ? (
                    <Minimize2 className="w-4 h-4" />
                  ) : (
                    <Maximize2 className="w-4 h-4" />
                  )}
                </Button>
                {livePreviewExpanded && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => {
                      setLivePreviewExpanded(false);
                      setShowLivePreview(false);
                    }}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                )}
              </div>
            </div>
            
            <div className={`relative ${livePreviewExpanded ? "h-[calc(100%-44px)]" : "h-[500px]"}`}>
              {livePreviewLoading && !livePreviewHtml && (
                <div className="absolute inset-0 flex items-center justify-center bg-background/80">
                  <div className="text-center">
                    <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2 text-primary" />
                    <p className="text-sm text-muted-foreground">Generating preview...</p>
                  </div>
                </div>
              )}
              
              {livePreviewHtml ? (
                <iframe
                  srcDoc={livePreviewHtml}
                  className="w-full h-full border-0"
                  title="Report Preview"
                  sandbox="allow-same-origin"
                />
              ) : !livePreviewLoading && (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  <div className="text-center">
                    <Eye className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p>Click refresh to load preview</p>
                    <Button
                      variant="outline"
                      size="sm"
                      className="mt-3"
                      onClick={() => fetchLivePreview()}
                    >
                      Load Preview
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {THEMES.map((theme) => (
            <ThemeCard
              key={theme.id}
              theme={theme}
              isSelected={selectedTheme === theme.id}
              onSelect={() => onThemeChange(theme.id)}
              hasImageError={imageErrors[`theme-${theme.id}`]}
              onImageError={() => handleImageError(`theme-${theme.id}`)}
            />
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
            const isRequired = page.required ?? false;
            const imageKey = `page-${selectedTheme}-${page.previewNumber}`;
            const hasError = imageErrors[imageKey] ?? false;

            return (
              <PageCard
                key={page.id}
                page={page}
                index={index}
                themeId={selectedTheme}
                theme={currentTheme}
                isSelected={isSelected}
                isRequired={isRequired}
                hasImageError={hasError}
                onToggle={() => !isRequired && handlePageToggle(page.id)}
                onPreview={() => setPreviewPage(page.id)}
                onImageError={() => handleImageError(imageKey)}
              />
            );
          })}
        </div>

        {/* Theme note for compact themes */}
        {isCompactTheme(selectedTheme) && (
          <p className="text-sm text-amber-600 dark:text-amber-400 mt-4 p-3 bg-amber-50 dark:bg-amber-950/30 rounded-lg border border-amber-200 dark:border-amber-800">
            ℹ️ {currentTheme.name} theme uses a compact {currentTheme.pageCount}-page format.
            Switch to Classic, Modern, or Elegant for a full report.
          </p>
        )}
      </div>

      {/* Page Preview Modal */}
      {previewPage && (
        <PagePreviewModal
          pageId={previewPage}
          themeId={selectedTheme}
          theme={currentTheme}
          availablePages={availablePages}
          accentColor={accentColor}
          propertyAddress={propertyAddress}
          onClose={() => setPreviewPage(null)}
          onNavigate={setPreviewPage}
        />
      )}
    </div>
  );
}

// ============================================
// THEME CARD COMPONENT
// ============================================

interface ThemeCardProps {
  theme: ThemeConfig;
  isSelected: boolean;
  onSelect: () => void;
  hasImageError: boolean;
  onImageError: () => void;
}

function ThemeCard({ theme, isSelected, onSelect, hasImageError, onImageError }: ThemeCardProps) {
  return (
    <button
      onClick={onSelect}
      className={`
        relative rounded-lg overflow-hidden border-2 transition-all text-left
        ${isSelected
          ? "border-primary ring-2 ring-primary ring-offset-2"
          : "border-border hover:border-muted-foreground/50"
        }
      `}
    >
      {/* Theme Preview */}
      <div className="h-32 relative overflow-hidden">
        {!hasImageError ? (
          <img
            src={getThemeCoverUrl(theme.id)}
            alt={`${theme.name} theme preview`}
            className="w-full h-full object-cover object-top"
            onError={onImageError}
            loading="lazy"
          />
        ) : (
          // Fallback gradient when image fails to load
          <div className={`${theme.previewBg} h-full p-3 flex flex-col justify-between`}>
            <div className="text-white text-left">
              <div className={`text-xs opacity-75 ${theme.fontStyle}`}>Seller&apos;s Report</div>
              <div className={`text-sm font-semibold ${theme.fontStyle}`}>123 Main St</div>
            </div>
            <div className="flex justify-between items-end">
              <div
                className="w-6 h-6 rounded-full border-2 border-white"
                style={{ backgroundColor: theme.defaultColor }}
              />
            </div>
          </div>
        )}
        
        {/* Page count badge for compact themes */}
        {theme.pageCount <= 9 && (
          <span className="absolute bottom-2 right-2 text-[10px] bg-black/50 text-white px-1.5 py-0.5 rounded">
            {theme.pageCount} pages
          </span>
        )}
      </div>

      {/* Theme Info */}
      <div className="p-2 bg-background">
        <p className="font-medium text-sm">{theme.name}</p>
        <p className="text-xs text-muted-foreground truncate">{theme.description}</p>
      </div>

      {/* Selected Checkmark */}
      {isSelected && (
        <div className="absolute top-2 right-2 w-6 h-6 bg-primary rounded-full flex items-center justify-center">
          <Check className="w-4 h-4 text-primary-foreground" />
        </div>
      )}
    </button>
  );
}

// ============================================
// PAGE CARD COMPONENT
// ============================================

interface PageCardProps {
  page: PageConfig;
  index: number;
  themeId: number;
  theme: ThemeConfig;
  isSelected: boolean;
  isRequired: boolean;
  hasImageError: boolean;
  onToggle: () => void;
  onPreview: () => void;
  onImageError: () => void;
}

function PageCard({
  page,
  index,
  themeId,
  theme,
  isSelected,
  isRequired,
  hasImageError,
  onToggle,
  onPreview,
  onImageError,
}: PageCardProps) {
  return (
    <div
      onClick={onToggle}
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
      <div className="h-24 relative overflow-hidden bg-gray-100">
        {!hasImageError ? (
          <img
            src={getPagePreviewUrl(themeId, page.previewNumber)}
            alt={`${page.name} preview`}
            className="w-full h-full object-cover object-top"
            onError={onImageError}
            loading="lazy"
          />
        ) : (
          // Fallback gradient when image fails to load
          <div className={`h-full ${theme.previewBg} flex items-center justify-center`}>
            <span className="text-white text-2xl font-bold opacity-30">
              {index + 1}
            </span>
          </div>
        )}

        {/* Preview button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onPreview();
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
}

// ============================================
// PAGE PREVIEW MODAL
// ============================================

interface PagePreviewModalProps {
  pageId: string;
  themeId: number;
  theme: ThemeConfig;
  availablePages: PageConfig[];
  accentColor: string;
  propertyAddress?: string;
  onClose: () => void;
  onNavigate: (pageId: string) => void;
}

function PagePreviewModal({
  pageId,
  themeId,
  theme,
  availablePages,
  accentColor,
  propertyAddress,
  onClose,
  onNavigate,
}: PagePreviewModalProps) {
  const [imageError, setImageError] = useState(false);
  const currentIndex = availablePages.findIndex(p => p.id === pageId);
  const page = availablePages[currentIndex];
  const hasPrevious = currentIndex > 0;
  const hasNext = currentIndex < availablePages.length - 1;

  const handlePrevious = () => {
    if (hasPrevious) {
      setImageError(false);
      onNavigate(availablePages[currentIndex - 1].id);
    }
  };

  const handleNext = () => {
    if (hasNext) {
      setImageError(false);
      onNavigate(availablePages[currentIndex + 1].id);
    }
  };

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") handlePrevious();
      if (e.key === "ArrowRight") handleNext();
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentIndex, hasPrevious, hasNext]);

  if (!page) return null;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-background rounded-xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div>
            <h3 className="font-semibold">{page.name}</h3>
            <p className="text-sm text-muted-foreground">{page.description}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Preview Area */}
        <div className="flex-1 overflow-auto p-8 bg-muted/50 flex items-center justify-center">
          {/* Page Preview - Letter size aspect ratio (8.5 x 11) */}
          <div
            className="bg-white shadow-2xl relative rounded-sm overflow-hidden"
            style={{
              width: "min(100%, 510px)",
              aspectRatio: "8.5 / 11",
            }}
          >
            {!imageError ? (
              <img
                src={getPagePreviewUrl(themeId, page.previewNumber)}
                alt={`${page.name} full preview`}
                className="w-full h-full object-contain"
                onError={() => setImageError(true)}
              />
            ) : (
              // Fallback skeleton when image fails to load
              <FallbackPreview
                page={page}
                theme={theme}
                accentColor={accentColor}
                propertyAddress={propertyAddress}
              />
            )}
          </div>
        </div>

        {/* Footer Navigation */}
        <div className="flex items-center justify-between p-4 border-t">
          <Button
            variant="ghost"
            onClick={handlePrevious}
            disabled={!hasPrevious}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Previous
          </Button>

          <span className="text-sm text-muted-foreground">
            Page {currentIndex + 1} of {availablePages.length} • Press ← → to navigate
          </span>

          <Button
            variant="ghost"
            onClick={handleNext}
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

// ============================================
// FALLBACK PREVIEW (when images aren't available)
// ============================================

interface FallbackPreviewProps {
  page: PageConfig;
  theme: ThemeConfig;
  accentColor: string;
  propertyAddress?: string;
}

function FallbackPreview({ page, theme, accentColor, propertyAddress }: FallbackPreviewProps) {
  return (
    <div className="absolute inset-0 p-8 flex flex-col">
      {/* Background tint */}
      <div className={`absolute inset-0 ${theme.previewBg} opacity-5 rounded-sm`} />
      
      {/* Header bar with accent color */}
      <div
        className="h-1 w-24 mb-4 rounded relative z-10"
        style={{ backgroundColor: accentColor }}
      />

      {/* Page title */}
      <h2 className={`text-2xl mb-2 relative z-10 ${theme.fontStyle}`} style={{ color: accentColor }}>
        {page.name}
      </h2>

      {/* Simulated content based on page type */}
      <div className="flex-1 space-y-4 mt-4 relative z-10">
        {page.id === "cover" && (
          <>
            <div className="h-48 bg-gray-200 rounded flex items-center justify-center">
              <ImageOff className="w-12 h-12 text-gray-400" />
            </div>
            <div className="text-center mt-4">
              <p className="text-sm text-gray-400 tracking-widest">SELLER&apos;S REPORT</p>
              <p className="text-xl font-semibold mt-2">{propertyAddress || "123 Main Street"}</p>
            </div>
          </>
        )}

        {page.id === "property_details" && (
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

        {page.id === "comparables" && (
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

        {page.id === "aerial" && (
          <div className="h-48 bg-gradient-to-br from-green-200 to-blue-200 rounded flex items-center justify-center">
            <span className="text-gray-500">Satellite Map View</span>
          </div>
        )}

        {!["cover", "property_details", "comparables", "aerial"].includes(page.id) && (
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
      <div className="flex justify-between items-end pt-4 border-t border-gray-200 mt-auto relative z-10">
        <div className="h-8 w-8 rounded-full bg-gray-200" />
        <div className="text-xs text-gray-400">Preview unavailable</div>
      </div>
    </div>
  );
}

export default ThemeSelector;

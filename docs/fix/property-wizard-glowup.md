# Property Report Wizard — Glow-Up Implementation

## Context

The property report wizard (`app/app/property/new/page.tsx`) already works well functionally — 4-step flow (Property → Comparables → Theme → Generate) with Google Places search, comp selection, theme picker, and PDF generation. The goal is **visual elevation only** — make it feel premium and polished without changing any business logic, API calls, or data flow.

**Design direction reference:** The nuclear redesign blueprint established "Refined Authority" — indigo primary (#4F46E5), amber/gold accent (#D97706), slate neutrals, Plus Jakarta Sans typography. The wizard should align with this palette.

**Benchmark:** Our Report Builder wizard (`components/report-builder/index.tsx`) is the internal quality bar — it has a config + preview side-by-side layout, sticky header, section completion checkmarks, and real-time preview. The property wizard should feel at LEAST as premium, if not more so, because property reports are our premium product.

---

## Files to Modify

| File | What Changes |
|------|-------------|
| `app/app/property/new/page.tsx` | Main wizard layout, progress stepper, step rendering, navigation |
| `components/property/ThemeSelector.tsx` | Theme card grid, color picker, page toggles, preview |
| `components/property/ComparablesPicker.tsx` | Comparable selection table/cards |
| `components/property/ComparablesMapModal.tsx` | Map view modal for comps |
| `components/property/PropertySearchForm.tsx` | Address search (if this exists as separate component) |

**DO NOT modify:**
- Any API calls or data fetching logic
- State management or business logic
- The 4-step flow order
- Any backend/worker files

---

## 1. Layout Upgrade — Side-by-Side with Live Preview

**Current:** Single-column, card-wrapped steps with Back/Continue buttons below.

**New:** Match the Report Builder pattern — config panel on the left, live preview on the right.

```tsx
// NEW layout structure
<div className="min-h-screen bg-[var(--background)]">
  {/* Sticky Header */}
  <header className="sticky top-0 z-10 bg-white/80 backdrop-blur-md border-b border-[var(--border)] px-8 py-4">
    <div className="max-w-7xl mx-auto flex items-center justify-between">
      <div className="flex items-center gap-4">
        <Link href="/app/property" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Property Reports
        </Link>
        <div className="h-4 w-px bg-border" />
        <h1 className="text-sm font-semibold text-foreground">New Property Report</h1>
      </div>
      <div className="flex items-center gap-3">
        <Link href="/app/property">
          <Button variant="outline" size="sm">Cancel</Button>
        </Link>
        {/* Show generate button in header when on step 4 */}
        {currentStep === 4 && (
          <Button 
            onClick={handleGenerate}
            disabled={!canGenerate || generationState !== 'idle'}
            size="sm"
            className="bg-primary text-white hover:bg-primary/90"
          >
            {generationState === 'generating' ? (
              <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Generating...</>
            ) : (
              <><Sparkles className="w-4 h-4 mr-2" />Generate Report</>
            )}
          </Button>
        )}
      </div>
    </div>
  </header>

  {/* Main Content */}
  <main className="max-w-7xl mx-auto px-8 py-6">
    <div className="grid grid-cols-[minmax(400px,480px)_1fr] gap-8">
      {/* Left: Steps Panel */}
      <div className="space-y-5">
        {/* Step Progress */}
        {renderStepProgress()}
        
        {/* Active Step Content */}
        {renderCurrentStep()}
        
        {/* Navigation */}
        {renderNavigation()}
      </div>

      {/* Right: Live Preview */}
      <div className="sticky top-24 self-start">
        {renderPreviewPanel()}
      </div>
    </div>
  </main>
</div>
```

**On mobile (< 1024px):** Stack vertically — steps on top, preview below (or hidden behind a "Preview" toggle button).

```tsx
// Responsive grid
<div className="grid grid-cols-1 lg:grid-cols-[minmax(400px,480px)_1fr] gap-8">
```

---

## 2. Step Progress — Elevated Stepper

**Current:** Basic progress bar + circular step icons below it.

**New:** Vertical step indicator on the left side of the config panel — more compact, always visible, shows completion state.

```tsx
function StepProgress({ currentStep, completedSteps }: StepProgressProps) {
  return (
    <div className="bg-white rounded-xl border border-[var(--border)] p-4">
      <div className="flex items-center gap-3">
        {STEPS.map((step, index) => {
          const Icon = step.icon;
          const isActive = currentStep === step.id;
          const isComplete = completedSteps.includes(step.id);
          const isLast = index === STEPS.length - 1;

          return (
            <Fragment key={step.id}>
              {/* Step Indicator */}
              <button
                onClick={() => canNavigateTo(step.id) && setCurrentStep(step.id)}
                disabled={!canNavigateTo(step.id)}
                className={cn(
                  "flex items-center gap-2.5 px-3 py-2 rounded-lg transition-all duration-200",
                  isActive && "bg-primary/10 ring-1 ring-primary/20",
                  isComplete && !isActive && "hover:bg-muted/50 cursor-pointer",
                  !isActive && !isComplete && "opacity-50 cursor-not-allowed"
                )}
              >
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300",
                  isComplete && "bg-emerald-500 text-white",
                  isActive && !isComplete && "bg-primary text-white",
                  !isActive && !isComplete && "bg-muted text-muted-foreground"
                )}>
                  {isComplete ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    <Icon className="w-4 h-4" />
                  )}
                </div>
                <span className={cn(
                  "text-sm font-medium hidden sm:block",
                  isActive && "text-primary",
                  isComplete && !isActive && "text-foreground",
                  !isActive && !isComplete && "text-muted-foreground"
                )}>
                  {step.name}
                </span>
              </button>

              {/* Connector */}
              {!isLast && (
                <div className={cn(
                  "h-px flex-1 transition-colors duration-300",
                  isComplete ? "bg-emerald-300" : "bg-border"
                )} />
              )}
            </Fragment>
          );
        })}
      </div>
    </div>
  );
}
```

**Key improvements:**
- Steps are clickable (can jump back to completed steps)
- Emerald green for completion (not just primary color)
- Smooth transitions between states
- Compact horizontal layout inside a card

---

## 3. Step 1: Property Search — Premium Feel

**Current:** Basic Google Places autocomplete + property details display.

**New:** Elevated search experience with property card.

```tsx
function PropertySearchStep({ state, onPropertySelect }: Step1Props) {
  return (
    <div className="space-y-4">
      {/* Search Card */}
      <div className="bg-white rounded-xl border border-[var(--border)] p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-semibold text-foreground">Find Property</h3>
            <p className="text-sm text-muted-foreground mt-0.5">Search by address to pull property records</p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <Search className="w-5 h-5 text-primary" />
          </div>
        </div>

        {/* Search Input - elevated styling */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Enter property address..."
            className="pl-10 h-11 text-sm bg-muted/30 border-border focus:bg-white focus:ring-2 focus:ring-primary/20 transition-all"
            // ... existing Google Places integration
          />
        </div>
      </div>

      {/* Selected Property Card - only shows after selection */}
      {state.property && (
        <div className="bg-white rounded-xl border border-[var(--border)] overflow-hidden animate-in slide-in-from-bottom-2 duration-300">
          {/* Property Hero - if image available */}
          {state.property.photo_url && (
            <div className="h-40 bg-muted overflow-hidden">
              <img 
                src={state.property.photo_url} 
                alt={state.property.full_address}
                className="w-full h-full object-cover"
              />
            </div>
          )}
          
          <div className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <h4 className="font-semibold text-foreground">{state.property.full_address}</h4>
                <p className="text-sm text-muted-foreground mt-0.5">
                  {state.property.city}, {state.property.state} {state.property.zip}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearProperty}
                className="text-muted-foreground hover:text-destructive"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>

            {/* Property Stats Row */}
            <div className="grid grid-cols-4 gap-3 mt-4 pt-4 border-t border-border">
              <StatBadge icon={Bed} label="Beds" value={state.property.beds} />
              <StatBadge icon={Bath} label="Baths" value={state.property.baths} />
              <StatBadge icon={Maximize} label="Sqft" value={formatNumber(state.property.sqft)} />
              <StatBadge icon={Calendar} label="Built" value={state.property.year_built} />
            </div>

            {/* Additional Details - Collapsible */}
            <Collapsible className="mt-4">
              <CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
                <ChevronDown className="w-4 h-4" />
                Property details
              </CollapsibleTrigger>
              <CollapsibleContent className="pt-3 mt-3 border-t border-border">
                <div className="grid grid-cols-2 gap-y-2 gap-x-4 text-sm">
                  <DetailRow label="APN" value={state.property.APN} />
                  <DetailRow label="Owner" value={state.property.owner_name} />
                  <DetailRow label="Assessed Value" value={formatCurrency(state.property.assessed_value)} />
                  <DetailRow label="Lot Size" value={`${formatNumber(state.property.lot_size)} sqft`} />
                </div>
              </CollapsibleContent>
            </Collapsible>
          </div>
        </div>
      )}
    </div>
  );
}

// Reusable stat badge
function StatBadge({ icon: Icon, label, value }: { icon: any; label: string; value: string | number | null }) {
  return (
    <div className="text-center">
      <div className="w-9 h-9 rounded-lg bg-muted/50 flex items-center justify-center mx-auto mb-1.5">
        <Icon className="w-4 h-4 text-muted-foreground" />
      </div>
      <div className="text-sm font-semibold text-foreground">{value ?? '—'}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}
```

---

## 4. Step 2: Comparables — Interactive Cards

**Current:** Basic table with select/deselect checkboxes.

**New:** Rich comparable cards with photo thumbnails, key stats, and clear selection state.

```tsx
function ComparablesStep({ comparables, selected, onToggle }: Step2Props) {
  return (
    <div className="space-y-4">
      {/* Header Card */}
      <div className="bg-white rounded-xl border border-[var(--border)] p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-foreground">Select Comparables</h3>
            <p className="text-sm text-muted-foreground mt-0.5">
              Choose up to 4 comparable properties for your report
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-primary">
              {selected.length}/4 selected
            </span>
            {/* Map view toggle */}
            <Button variant="outline" size="sm" onClick={openMapModal}>
              <MapPin className="w-4 h-4 mr-1.5" />
              Map View
            </Button>
          </div>
        </div>
      </div>

      {/* Comparable Cards */}
      <div className="space-y-3">
        {comparables.map((comp, index) => {
          const isSelected = selected.some(s => s.address === comp.address);
          const isDisabled = !isSelected && selected.length >= 4;
          
          return (
            <button
              key={comp.address}
              onClick={() => !isDisabled && onToggle(comp)}
              disabled={isDisabled}
              className={cn(
                "w-full bg-white rounded-xl border-2 p-4 text-left transition-all duration-200",
                isSelected && "border-primary bg-primary/[0.02] shadow-sm shadow-primary/10",
                !isSelected && !isDisabled && "border-[var(--border)] hover:border-primary/30 hover:shadow-sm",
                isDisabled && "border-[var(--border)] opacity-50 cursor-not-allowed"
              )}
            >
              <div className="flex gap-4">
                {/* Comp Photo Thumbnail */}
                <div className="w-24 h-20 rounded-lg overflow-hidden bg-muted flex-shrink-0">
                  {comp.photo_url ? (
                    <img src={comp.photo_url} alt={comp.address} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Home className="w-6 h-6 text-muted-foreground/50" />
                    </div>
                  )}
                </div>

                {/* Comp Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-sm font-semibold text-foreground truncate">
                        {comp.address}
                      </h4>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {comp.distance_miles} mi away • Sold {comp.sold_date}
                      </p>
                    </div>
                    
                    {/* Selection indicator */}
                    <div className={cn(
                      "w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all",
                      isSelected ? "bg-primary border-primary" : "border-border"
                    )}>
                      {isSelected && <Check className="w-3.5 h-3.5 text-white" />}
                    </div>
                  </div>

                  {/* Stats Row */}
                  <div className="flex items-center gap-4 mt-2.5">
                    <span className="text-base font-bold text-foreground">
                      {formatCurrency(comp.price)}
                    </span>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{comp.beds} bd</span>
                      <span className="w-1 h-1 rounded-full bg-border" />
                      <span>{comp.baths} ba</span>
                      <span className="w-1 h-1 rounded-full bg-border" />
                      <span>{formatNumber(comp.sqft)} sqft</span>
                      <span className="w-1 h-1 rounded-full bg-border" />
                      <span>${Math.round(comp.price / comp.sqft)}/sqft</span>
                    </div>
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
```

---

## 5. Step 3: Theme Selection — Showpiece

This is where agents make the aesthetic choice for their brand. It should feel premium.

**Current:** Theme cards + color picker + page checkboxes.

**New:** Visual theme gallery with hover previews and smooth accent color picker.

```tsx
function ThemeStep({ selectedTheme, themeColor, pages, onThemeChange, onColorChange, onPageToggle }: Step3Props) {
  return (
    <div className="space-y-4">
      {/* Theme Gallery */}
      <div className="bg-white rounded-xl border border-[var(--border)] p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-semibold text-foreground">Choose a Theme</h3>
            <p className="text-sm text-muted-foreground mt-0.5">Each theme has a distinct personality</p>
          </div>
          <Palette className="w-5 h-5 text-muted-foreground" />
        </div>

        {/* Theme Cards - 5 in a row */}
        <div className="grid grid-cols-5 gap-3">
          {THEMES.map((theme) => {
            const isSelected = selectedTheme === theme.id;
            return (
              <button
                key={theme.id}
                onClick={() => onThemeChange(theme.id)}
                className={cn(
                  "group relative rounded-xl overflow-hidden border-2 transition-all duration-200",
                  isSelected 
                    ? "border-primary ring-2 ring-primary/20 scale-[1.02]" 
                    : "border-border hover:border-primary/30 hover:scale-[1.01]"
                )}
              >
                {/* Mini Cover Preview - aspect ratio matched to Letter */}
                <div 
                  className="aspect-[8.5/11] relative"
                  style={{ background: theme.coverGradient }}
                >
                  {/* Simplified preview showing theme personality */}
                  <div className="absolute inset-0 p-2 flex flex-col justify-between">
                    <div 
                      className="text-[6px] font-bold text-white leading-tight"
                      style={{ fontFamily: theme.displayFont }}
                    >
                      PROPERTY<br/>REPORT
                    </div>
                    <div className="space-y-0.5">
                      <div className="h-0.5 rounded-full bg-white/40 w-3/4" />
                      <div className="h-0.5 rounded-full bg-white/30 w-1/2" />
                    </div>
                  </div>
                </div>

                {/* Theme Name */}
                <div className={cn(
                  "px-2 py-1.5 text-center transition-colors",
                  isSelected ? "bg-primary/5" : "bg-white"
                )}>
                  <span className={cn(
                    "text-xs font-semibold",
                    isSelected ? "text-primary" : "text-foreground"
                  )}>
                    {theme.name}
                  </span>
                </div>

                {/* Selected checkmark overlay */}
                {isSelected && (
                  <div className="absolute top-1.5 right-1.5 w-5 h-5 rounded-full bg-primary text-white flex items-center justify-center shadow-sm">
                    <Check className="w-3 h-3" />
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Accent Color Picker */}
      <div className="bg-white rounded-xl border border-[var(--border)] p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-semibold text-foreground">Accent Color</h3>
            <p className="text-sm text-muted-foreground mt-0.5">Customize the theme to match your brand</p>
          </div>
        </div>

        {/* Preset Colors */}
        <div className="flex items-center gap-2 mb-3">
          {PRESET_COLORS.map((color) => (
            <button
              key={color.hex}
              onClick={() => onColorChange(color.hex)}
              className={cn(
                "w-8 h-8 rounded-full transition-all duration-200 hover:scale-110",
                themeColor === color.hex && "ring-2 ring-offset-2 ring-primary"
              )}
              style={{ backgroundColor: color.hex }}
              title={color.name}
            />
          ))}
        </div>

        {/* Custom Color Input */}
        <div className="flex items-center gap-3 pt-3 border-t border-border">
          <div 
            className="w-10 h-10 rounded-lg border border-border flex-shrink-0" 
            style={{ backgroundColor: themeColor }} 
          />
          <Input
            value={themeColor}
            onChange={(e) => onColorChange(e.target.value)}
            placeholder="#4F46E5"
            className="font-mono text-sm h-10"
            maxLength={7}
          />
        </div>
      </div>

      {/* Page Selection */}
      <div className="bg-white rounded-xl border border-[var(--border)] p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-semibold text-foreground">Include Pages</h3>
            <p className="text-sm text-muted-foreground mt-0.5">Toggle pages to include in the report</p>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-2">
          {REPORT_PAGES.map((page) => {
            const isIncluded = pages.includes(page.id);
            return (
              <button
                key={page.id}
                onClick={() => onPageToggle(page.id)}
                disabled={page.required}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-all text-left text-sm",
                  isIncluded 
                    ? "bg-primary/5 border-primary/20 text-foreground" 
                    : "bg-muted/30 border-transparent text-muted-foreground",
                  page.required && "opacity-70 cursor-not-allowed"
                )}
              >
                <div className={cn(
                  "w-5 h-5 rounded border flex items-center justify-center flex-shrink-0",
                  isIncluded ? "bg-primary border-primary text-white" : "border-border"
                )}>
                  {isIncluded && <Check className="w-3 h-3" />}
                </div>
                <span>{page.name}</span>
                {page.required && (
                  <span className="text-xs text-muted-foreground ml-auto">Required</span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// Theme data for the preview cards
const THEMES = [
  { 
    id: 5, name: 'Bold', 
    displayFont: 'Oswald, sans-serif',
    coverGradient: 'linear-gradient(135deg, #15216E 0%, #0a1145 100%)',
  },
  { 
    id: 1, name: 'Classic', 
    displayFont: 'Merriweather, serif',
    coverGradient: 'linear-gradient(135deg, #1B365D 0%, #0f2040 100%)',
  },
  { 
    id: 3, name: 'Elegant', 
    displayFont: 'Playfair Display, serif',
    coverGradient: 'linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%)',
  },
  { 
    id: 2, name: 'Modern', 
    displayFont: 'Space Grotesk, sans-serif',
    coverGradient: 'linear-gradient(135deg, #1A1F36 0%, #FF6B5B 100%)',
  },
  { 
    id: 4, name: 'Teal', 
    displayFont: 'Montserrat, sans-serif',
    coverGradient: 'linear-gradient(135deg, #18235c 0%, #34d1c3 100%)',
  },
];

const PRESET_COLORS = [
  { hex: '#4F46E5', name: 'Indigo' },
  { hex: '#1B365D', name: 'Navy' },
  { hex: '#0F766E', name: 'Teal' },
  { hex: '#B91C1C', name: 'Crimson' },
  { hex: '#7C3AED', name: 'Violet' },
  { hex: '#0369A1', name: 'Blue' },
  { hex: '#15803D', name: 'Forest' },
  { hex: '#1a1a1a', name: 'Black' },
];
```

---

## 6. Step 4: Generate — Confidence-Building

**Current:** Basic review summary + generate button + spinner.

**New:** Summary card with all selections visible, animated generation progress, and rich completion state.

```tsx
function GenerateStep({ state, generationState, reportUrl, qrCodeUrl, shortUrl }: Step4Props) {
  return (
    <div className="space-y-4">
      {generationState === 'idle' && (
        <>
          {/* Summary Card */}
          <div className="bg-white rounded-xl border border-[var(--border)] p-5">
            <h3 className="text-base font-semibold text-foreground mb-4">Report Summary</h3>
            
            <div className="space-y-3">
              {/* Property */}
              <SummaryRow 
                icon={Home} 
                label="Property" 
                value={state.property.full_address}
                action={<Button variant="ghost" size="sm" onClick={() => goToStep(1)}>Edit</Button>}
              />
              
              {/* Comparables */}
              <SummaryRow 
                icon={BarChart3} 
                label="Comparables" 
                value={`${state.selectedComps.length} properties selected`}
                action={<Button variant="ghost" size="sm" onClick={() => goToStep(2)}>Edit</Button>}
              />
              
              {/* Theme */}
              <SummaryRow 
                icon={Palette} 
                label="Theme" 
                value={getThemeName(state.theme)}
                extra={
                  <div 
                    className="w-4 h-4 rounded-full border border-border" 
                    style={{ backgroundColor: state.themeColor }}
                  />
                }
                action={<Button variant="ghost" size="sm" onClick={() => goToStep(3)}>Edit</Button>}
              />
              
              {/* Pages */}
              <SummaryRow 
                icon={FileText} 
                label="Pages" 
                value={`${state.selectedPages.length} pages included`}
              />
            </div>
          </div>

          {/* Generate CTA */}
          <div className="bg-gradient-to-br from-primary/5 to-amber-500/5 rounded-xl border border-primary/10 p-6 text-center">
            <Sparkles className="w-8 h-8 text-primary mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-foreground mb-1">Ready to Generate</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Your property report will be ready in about 30 seconds
            </p>
            <Button 
              onClick={handleGenerate}
              size="lg"
              className="bg-primary text-white hover:bg-primary/90 px-8"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Generate Report
            </Button>
          </div>
        </>
      )}

      {generationState === 'generating' && (
        <div className="bg-white rounded-xl border border-[var(--border)] p-8 text-center">
          {/* Animated Progress */}
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
            <Loader2 className="w-8 h-8 text-primary animate-spin" />
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">Generating Your Report</h3>
          
          {/* Stage indicators */}
          <div className="max-w-xs mx-auto space-y-2 mt-6 text-left">
            {GENERATION_STAGES.map((stage, i) => {
              const isActive = currentStage === i;
              const isComplete = currentStage > i;
              return (
                <div key={stage} className={cn(
                  "flex items-center gap-3 text-sm transition-all duration-300",
                  isComplete && "text-emerald-600",
                  isActive && "text-foreground font-medium",
                  !isActive && !isComplete && "text-muted-foreground/50"
                )}>
                  {isComplete ? (
                    <Check className="w-4 h-4 text-emerald-500" />
                  ) : isActive ? (
                    <Loader2 className="w-4 h-4 animate-spin text-primary" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-border" />
                  )}
                  {stage}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {generationState === 'completed' && (
        <div className="bg-white rounded-xl border border-[var(--border)] overflow-hidden">
          {/* Success Header */}
          <div className="bg-gradient-to-r from-emerald-500 to-emerald-600 px-6 py-5 text-white">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                <Check className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-lg">Report Generated!</h3>
                <p className="text-sm text-emerald-100">Your property report is ready to share</p>
              </div>
            </div>
          </div>

          <div className="p-6 space-y-4">
            {/* Action Buttons */}
            <div className="grid grid-cols-2 gap-3">
              <Button variant="outline" className="h-12" onClick={downloadPdf}>
                <Download className="w-4 h-4 mr-2" />
                Download PDF
              </Button>
              <Button className="h-12 bg-primary" onClick={viewReport}>
                <ExternalLink className="w-4 h-4 mr-2" />
                View Report
              </Button>
            </div>

            {/* QR Code + Short URL */}
            {(qrCodeUrl || shortUrl) && (
              <div className="flex items-center gap-4 pt-4 border-t border-border">
                {qrCodeUrl && (
                  <img src={qrCodeUrl} alt="QR Code" className="w-20 h-20 rounded-lg border border-border" />
                )}
                <div className="flex-1">
                  <p className="text-sm font-medium text-foreground mb-1">Share Link</p>
                  <div className="flex items-center gap-2">
                    <code className="text-xs bg-muted px-3 py-1.5 rounded-md flex-1 truncate">
                      {shortUrl}
                    </code>
                    <Button variant="outline" size="sm" onClick={copyUrl}>
                      <Copy className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {generationState === 'failed' && (
        <div className="bg-white rounded-xl border border-destructive/20 p-6 text-center">
          <div className="w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-3">
            <AlertCircle className="w-6 h-6 text-destructive" />
          </div>
          <h3 className="font-semibold text-foreground mb-1">Generation Failed</h3>
          <p className="text-sm text-muted-foreground mb-4">
            {state.errorMessage || "Something went wrong. Please try again."}
          </p>
          <Button onClick={handleRetry} variant="outline">
            <RotateCcw className="w-4 h-4 mr-2" />
            Try Again
          </Button>
        </div>
      )}
    </div>
  );
}

const GENERATION_STAGES = [
  "Fetching property data...",
  "Analyzing comparables...",
  "Rendering report pages...",
  "Generating PDF...",
  "Finalizing...",
];
```

---

## 7. Right-Side Preview Panel

The preview panel shows a real-time representation of what the report will look like as the agent configures it.

```tsx
function PreviewPanel({ state, currentStep }: PreviewPanelProps) {
  return (
    <div className="bg-white rounded-xl border border-[var(--border)] overflow-hidden">
      {/* Preview Header */}
      <div className="px-5 py-3 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Eye className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium text-foreground">Preview</span>
        </div>
        <span className="text-xs text-muted-foreground">Updates as you build</span>
      </div>

      {/* Preview Content */}
      <div className="p-5">
        {/* Mini Report Cover Preview */}
        <div 
          className="aspect-[8.5/11] rounded-lg overflow-hidden shadow-lg mx-auto max-w-[280px] transition-all duration-500"
          style={{ 
            background: state.theme 
              ? getThemeGradient(state.theme, state.themeColor) 
              : 'linear-gradient(135deg, #1a1a2e, #16213e)' 
          }}
        >
          <div className="h-full p-6 flex flex-col justify-between text-white">
            {/* Top: "Property Report" label */}
            <div>
              <div className="text-[8px] uppercase tracking-widest text-white/60 mb-1">
                Property Report
              </div>
              <div className="text-xs font-bold leading-tight">
                {state.property?.full_address || 'Property Address'}
              </div>
              <div className="text-[7px] text-white/70 mt-0.5">
                {state.property?.city || 'City'}, {state.property?.state || 'ST'}
              </div>
            </div>

            {/* Middle: Stats preview */}
            {state.property && (
              <div className="flex gap-2">
                {state.property.beds && (
                  <div className="bg-white/10 rounded px-1.5 py-0.5 text-[6px]">
                    {state.property.beds} BD
                  </div>
                )}
                {state.property.baths && (
                  <div className="bg-white/10 rounded px-1.5 py-0.5 text-[6px]">
                    {state.property.baths} BA
                  </div>
                )}
                {state.property.sqft && (
                  <div className="bg-white/10 rounded px-1.5 py-0.5 text-[6px]">
                    {formatNumber(state.property.sqft)} SF
                  </div>
                )}
              </div>
            )}

            {/* Bottom: Agent info */}
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-full bg-white/20" />
              <div>
                <div className="text-[7px] font-semibold">Agent Name</div>
                <div className="text-[5px] text-white/60">Company</div>
              </div>
            </div>
          </div>
        </div>

        {/* Report Details Under Preview */}
        <div className="mt-4 space-y-2 text-center">
          {state.theme && (
            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-muted/50 rounded-full text-xs text-muted-foreground">
              <Palette className="w-3 h-3" />
              {getThemeName(state.theme)} Theme
            </div>
          )}
          {state.selectedComps?.length > 0 && (
            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-muted/50 rounded-full text-xs text-muted-foreground ml-2">
              <BarChart3 className="w-3 h-3" />
              {state.selectedComps.length} Comparables
            </div>
          )}
        </div>

        {/* Page Thumbnails - shows when on step 3+ */}
        {currentStep >= 3 && state.selectedPages?.length > 0 && (
          <div className="mt-4 pt-4 border-t border-border">
            <p className="text-xs text-muted-foreground mb-2">Report pages ({state.selectedPages.length})</p>
            <div className="grid grid-cols-4 gap-1.5">
              {state.selectedPages.map((page) => (
                <div 
                  key={page}
                  className="aspect-[8.5/11] bg-muted/50 rounded border border-border flex items-center justify-center"
                >
                  <span className="text-[6px] text-muted-foreground font-medium">{getPageShortName(page)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## 8. Navigation — Polished Bottom Bar

```tsx
function WizardNavigation({ currentStep, canProceed, onBack, onNext }: NavProps) {
  if (currentStep === 4) return null; // Step 4 has its own CTA

  return (
    <div className="flex items-center justify-between pt-2">
      <Button
        variant="ghost"
        onClick={onBack}
        disabled={currentStep === 1}
        className="text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back
      </Button>
      
      <Button
        onClick={onNext}
        disabled={!canProceed}
        className="bg-primary text-white hover:bg-primary/90 min-w-[120px]"
      >
        Continue
        <ArrowRight className="w-4 h-4 ml-2" />
      </Button>
    </div>
  );
}
```

---

## 9. Animations & Micro-interactions

Add these subtle polish touches:

```tsx
// Step transitions - wrap each step in AnimatePresence
import { motion, AnimatePresence } from 'framer-motion'

<AnimatePresence mode="wait">
  <motion.div
    key={currentStep}
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -8 }}
    transition={{ duration: 0.2, ease: 'easeOut' }}
  >
    {renderCurrentStep()}
  </motion.div>
</AnimatePresence>
```

**Other animations to include:**
- Property card slides in from bottom when selected (`animate-in slide-in-from-bottom-2`)
- Comparable cards have subtle hover lift (`hover:shadow-sm hover:-translate-y-0.5 transition-all`)
- Theme selection has scale bump on select (`scale-[1.02]` transition)
- Generation stages fade in sequentially
- Success checkmark has a spring animation
- Preview panel transitions smoothly when data changes

---

## 10. Color Reference

Use the design system tokens — do NOT hardcode hex values for UI elements:

```
Primary actions:    bg-primary (indigo)
Accent/gold:        text-amber-600, bg-amber-500
Success states:     text-emerald-600, bg-emerald-500
Destructive:        text-destructive, bg-destructive
Borders:            border-[var(--border)]
Backgrounds:        bg-[var(--background)] (page), bg-white (cards)
Text primary:       text-foreground
Text secondary:     text-muted-foreground
Muted surfaces:     bg-muted, bg-muted/50
```

The ONLY place hardcoded colors should appear is in the theme preview cards (the THEMES array) — those represent the PDF template colors, not the UI.

---

## Summary Checklist

- [ ] Side-by-side layout (config panel + live preview) matching report builder pattern
- [ ] Responsive — stacks on mobile, side-by-side on desktop
- [ ] Sticky header with back link, title, and generate button (on step 4)
- [ ] Horizontal step progress with clickable completed steps
- [ ] Step 1: Elevated search with rich property card and collapsible details
- [ ] Step 2: Photo-rich comparable cards with clear selection state (not table rows)
- [ ] Step 3: Visual theme gallery, preset color swatches, page toggle grid
- [ ] Step 4: Summary card, animated generation stages, rich completion with QR/share
- [ ] Live preview panel showing cover mock-up that updates in real-time
- [ ] Framer Motion transitions between steps
- [ ] All colors use design system tokens (not hardcoded hex)
- [ ] Zero changes to API calls, state management, or business logic

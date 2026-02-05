# Wizard Sharpening Guide
> The structure is right. These are the detail-level refinements that take the wizards from "good" to "polished."

---

## What's Already Working (Don't Touch)

- ✅ 400px config / flexible preview split layout (Report Builder)
- ✅ Step-based flow with progress bar (Property Wizard)
- ✅ Section-based config with completion tracking
- ✅ Sticky header with back + primary action
- ✅ Touched state tracking
- ✅ Real-time preview updates

---

## 1. Sticky Header — Add Context & Scroll Shadow

**Current:** Flat white bar with back link and buttons. No title, no sense of where you are.

**Before:**
```tsx
<header className="sticky top-0 z-10 bg-white border-b border-gray-200 px-8 py-4">
  <div className="flex items-center justify-between">
    <Link href="/app/reports" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
      <ArrowLeft className="w-4 h-4" />
      Back to Reports
    </Link>
    <div className="flex items-center gap-3">
      <Button variant="outline">Cancel</Button>
      <Button className="bg-violet-600 text-white hover:bg-violet-700">
        Generate Report
      </Button>
    </div>
  </div>
</header>
```

**After:**
```tsx
// Add state for scroll shadow
const [scrolled, setScrolled] = useState(false)
useEffect(() => {
  const onScroll = () => setScrolled(window.scrollY > 8)
  window.addEventListener("scroll", onScroll)
  return () => window.removeEventListener("scroll", onScroll)
}, [])

<header className={cn(
  "sticky top-0 z-10 bg-white/95 backdrop-blur-sm border-b px-8 py-3 transition-shadow duration-200",
  scrolled ? "shadow-sm border-gray-200" : "border-transparent"
)}>
  <div className="flex items-center justify-between">
    {/* Left: Back + Title */}
    <div className="flex items-center gap-4">
      <Link
        href="/app/reports"
        className="flex items-center justify-center w-8 h-8 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
      </Link>
      <div>
        <h1 className="text-sm font-semibold text-gray-900">New Market Report</h1>
        <p className="text-xs text-gray-500">
          {completedCount} of {totalSections} sections complete
        </p>
      </div>
    </div>

    {/* Right: Actions */}
    <div className="flex items-center gap-3">
      <Button variant="ghost" size="sm" asChild>
        <Link href="/app/reports">Cancel</Link>
      </Button>
      <Button
        onClick={handleGenerate}
        disabled={!canGenerate || isGenerating}
        size="sm"
        className={cn(
          "transition-all",
          canGenerate && !isGenerating && "shadow-sm shadow-primary/25"
        )}
      >
        {isGenerating ? (
          <><Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />Generating...</>
        ) : (
          <>Generate Report</>
        )}
      </Button>
    </div>
  </div>
</header>
```

**What changed:**
- Backdrop blur for that modern frosted look
- Shadow appears only on scroll (not a permanent border)
- Back button is now an icon-only hover target (cleaner)
- Added wizard title + progress counter
- Generate button gets a subtle glow shadow when ready
- Slightly reduced vertical padding (py-4 → py-3) for tighter header

---

## 2. Section Cards — Add Depth & Active State

**Current:** Flat white cards, all look identical regardless of state.

**Before:**
```tsx
<section className="bg-white border border-gray-200 rounded-lg p-4">
  <div className="flex items-center justify-between mb-4">
    <h3 className="text-sm font-medium text-gray-900">Report Type</h3>
    {isComplete && (
      <div className="w-5 h-5 rounded-full bg-green-50 flex items-center justify-center">
        <Check className="w-3 h-3 text-green-500" />
      </div>
    )}
  </div>
  {/* content */}
</section>
```

**After:**
```tsx
<section className={cn(
  "bg-white rounded-xl border transition-all duration-200",
  isComplete
    ? "border-gray-200 shadow-sm"          // Completed: settled, subtle
    : "border-gray-200/80 shadow-sm"       // Active: same base
)}>
  {/* Section header — clickable to collapse */}
  <button
    onClick={() => toggleSection("reportType")}
    className="flex items-center justify-between w-full px-5 py-4 text-left"
  >
    <div className="flex items-center gap-3">
      {/* Step number / completion indicator */}
      <div className={cn(
        "w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold transition-colors",
        isComplete
          ? "bg-emerald-500 text-white"
          : "bg-gray-100 text-gray-500"
      )}>
        {isComplete ? <Check className="w-3.5 h-3.5" /> : stepNumber}
      </div>
      <h3 className="text-sm font-medium text-gray-900">Report Type</h3>
    </div>

    {/* Collapse chevron */}
    <ChevronDown className={cn(
      "w-4 h-4 text-gray-400 transition-transform duration-200",
      isExpanded && "rotate-180"
    )} />
  </button>

  {/* Collapsible content */}
  <AnimatePresence initial={false}>
    {isExpanded && (
      <motion.div
        initial={{ height: 0, opacity: 0 }}
        animate={{ height: "auto", opacity: 1 }}
        exit={{ height: 0, opacity: 0 }}
        transition={{ duration: 0.2, ease: "easeInOut" }}
        className="overflow-hidden"
      >
        <div className="px-5 pb-5 pt-0">
          {/* Section content */}
        </div>
      </motion.div>
    )}
  </AnimatePresence>
</section>
```

**What changed:**
- `rounded-lg` → `rounded-xl` (more modern)
- Added subtle `shadow-sm` for depth
- Step number badge that transforms into a green checkmark on completion
- Sections are now collapsible with smooth animation
- Chevron indicator for expand/collapse
- Padding adjusted: `p-4` → `px-5 py-4` header / `px-5 pb-5` content (more breathing room)

**Note:** Collapsibility is optional — if you prefer sections always open, just keep the visual refinements (rounded-xl, shadow, step badge) and skip the AnimatePresence.

---

## 3. Selection Cards — Add Micro-Interactions

**Current:** Color swap only, no depth or motion.

**Before:**
```tsx
<button
  className={cn(
    "flex flex-col items-center p-3 rounded-lg border transition-colors text-center",
    isSelected
      ? "bg-violet-50 border-2 border-violet-600"
      : "bg-white border-gray-200 hover:border-gray-300"
  )}
>
  <Icon className={cn("w-6 h-6 mb-2", isSelected ? "text-violet-600" : "text-gray-400")} />
  <span className={cn("text-sm font-medium", isSelected ? "text-gray-900" : "text-gray-700")}>
    {type.label}
  </span>
</button>
```

**After:**
```tsx
<button
  onClick={() => handleTypeSelect(type.id)}
  className={cn(
    "group relative flex flex-col items-center p-4 rounded-xl border-2 transition-all duration-150 text-center",
    isSelected
      ? "bg-primary/5 border-primary shadow-sm shadow-primary/10"
      : "bg-white border-transparent shadow-sm hover:shadow-md hover:-translate-y-0.5"
  )}
>
  {/* Icon with background */}
  <div className={cn(
    "w-10 h-10 rounded-lg flex items-center justify-center mb-2.5 transition-colors",
    isSelected ? "bg-primary/10" : "bg-gray-50 group-hover:bg-gray-100"
  )}>
    <Icon className={cn(
      "w-5 h-5 transition-colors",
      isSelected ? "text-primary" : "text-gray-400 group-hover:text-gray-600"
    )} />
  </div>

  <span className={cn(
    "text-sm font-medium transition-colors",
    isSelected ? "text-foreground" : "text-gray-600"
  )}>
    {type.label}
  </span>
  <span className="text-xs text-gray-400 mt-0.5 leading-tight">
    {type.description}
  </span>

  {/* Selected indicator dot */}
  {isSelected && (
    <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-primary" />
  )}
</button>
```

**What changed:**
- `rounded-lg` → `rounded-xl`
- `border` → `border-2`, unselected uses `border-transparent` with shadow instead (cleaner)
- Added `hover:-translate-y-0.5` lift effect on hover
- Added `hover:shadow-md` for depth on hover
- Icon now sits in a subtle background square
- `group` class enables icon color change on card hover
- Small colored dot in corner when selected (secondary confirmation)
- Slightly more padding: `p-3` → `p-4`

---

## 4. Audience/Filter Pills — Tighten Up

**Before:**
```tsx
<button className={cn(
  "inline-flex items-center gap-1 px-3 py-1.5 text-sm rounded-full transition-colors",
  isSelected
    ? "bg-violet-50 text-violet-700 border border-violet-200"
    : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
)}>
  {isSelected && <Check className="w-3 h-3" />}
  {preset.label}
</button>
```

**After:**
```tsx
<button className={cn(
  "inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full border transition-all duration-150",
  isSelected
    ? "bg-primary/10 text-primary border-primary/20 shadow-sm shadow-primary/5"
    : "bg-white text-gray-500 border-gray-200 hover:border-gray-300 hover:text-gray-700"
)}>
  {isSelected && (
    <Check className="w-3 h-3" strokeWidth={2.5} />
  )}
  {preset.label}
</button>
```

**What changed:**
- `text-sm` → `text-xs font-medium` (pills should be smaller than body text)
- Used design token `text-primary` instead of `text-violet-700`
- Added subtle shadow on selected state
- Thicker checkmark stroke for crispness
- `gap-1` → `gap-1.5` for better spacing around the checkmark

---

## 5. Preview Panel — Give It Visual Weight

**Current:** Same card treatment as config sections. Doesn't feel like the "output" side.

**Before:**
```tsx
<div className="sticky top-24">
  <div className="bg-white border border-gray-200 rounded-lg p-4">
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-sm font-medium text-gray-900">Preview</h3>
      <span className="text-xs text-gray-400">Updates as you build</span>
    </div>
    <ReportPreview state={state} branding={branding} profile={profile} />
  </div>
</div>
```

**After:**
```tsx
<div className="sticky top-20">
  <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
    {/* Preview header — slightly different treatment */}
    <div className="flex items-center justify-between px-5 py-3 border-b border-gray-100 bg-gray-50/50">
      <div className="flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
          Live Preview
        </h3>
      </div>
      <span className="text-xs text-gray-400">Updates as you build</span>
    </div>

    {/* Preview content */}
    <div className="p-4">
      <ReportPreview state={state} branding={branding} profile={profile} />
    </div>
  </div>
</div>
```

**What changed:**
- Separated header into its own bar with `bg-gray-50/50` — visually distinct from config cards
- "Live Preview" as an uppercase overline label (feels more like a tool)
- Green pulsing dot indicates it's reactive
- `rounded-lg` → `rounded-xl`
- Added `shadow-sm` + `overflow-hidden`
- Sticky offset adjusted: `top-24` → `top-20` (tighter to header)

---

## 6. Property Wizard Progress Steps — Refine

**Current:** Works but the step circles are heavy and the connecting line (Progress bar) is disconnected from the step icons.

**Before:**
```tsx
<div>
  <Progress value={progressPercent} className="h-2" />
  <div className="flex justify-between mt-4">
    {STEPS.map((step) => (
      <div className="flex flex-col items-center gap-2">
        <div className={cn(
          "w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors",
          isComplete ? "bg-primary border-primary text-primary-foreground" : "",
          isActive ? "border-primary bg-primary/10" : "",
          !isActive && !isComplete ? "border-muted-foreground/30 bg-muted/30" : ""
        )}>
          {isComplete ? <Check className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
        </div>
        <span className={cn("text-xs font-medium", ...)}>
          {step.name}
        </span>
      </div>
    ))}
  </div>
</div>
```

**After:**
```tsx
{/* Connected step indicator */}
<div className="relative">
  <div className="flex items-center justify-between">
    {STEPS.map((step, index) => {
      const Icon = step.icon
      const isActive = currentStep === step.id
      const isComplete = currentStep > step.id

      return (
        <div key={step.id} className="flex flex-col items-center gap-2 relative z-10">
          {/* Step circle */}
          <div className={cn(
            "w-9 h-9 rounded-full flex items-center justify-center transition-all duration-300",
            isComplete && "bg-primary text-white shadow-sm shadow-primary/25",
            isActive && "bg-primary/10 ring-2 ring-primary ring-offset-2",
            !isActive && !isComplete && "bg-gray-100 text-gray-400"
          )}>
            {isComplete ? (
              <Check className="w-4 h-4" strokeWidth={2.5} />
            ) : (
              <Icon className={cn("w-4 h-4", isActive && "text-primary")} />
            )}
          </div>

          {/* Label */}
          <span className={cn(
            "text-xs font-medium transition-colors",
            isActive ? "text-primary" : isComplete ? "text-foreground" : "text-muted-foreground"
          )}>
            {step.name}
          </span>
        </div>
      )
    })}
  </div>

  {/* Connecting line (behind circles) */}
  <div className="absolute top-[18px] left-[10%] right-[10%] h-0.5 bg-gray-200 -z-0" />
  <div
    className="absolute top-[18px] left-[10%] h-0.5 bg-primary transition-all duration-500 ease-out -z-0"
    style={{ width: `${((currentStep - 1) / (STEPS.length - 1)) * 80}%` }}
  />
</div>
```

**What changed:**
- Removed separate `<Progress>` bar — the connecting line between steps IS the progress
- Step circles: `w-10 h-10` → `w-9 h-9` (slightly smaller, less heavy)
- Active step uses `ring-2 ring-offset-2` instead of a border (cleaner, more modern)
- Completed steps get a subtle primary shadow
- Connecting line animates as you progress through steps
- Active step label is `text-primary` for clear "you are here"
- Thicker checkmark stroke

---

## 7. Generate/Submit Button — Make It Feel Important

When all sections are complete and the user is ready to generate, the button should feel like a moment.

**After (enhanced ready state):**
```tsx
<Button
  onClick={handleGenerate}
  disabled={!canGenerate || isGenerating}
  size="sm"
  className={cn(
    "relative transition-all duration-300",
    canGenerate && !isGenerating && [
      "shadow-md shadow-primary/20",
      "hover:shadow-lg hover:shadow-primary/30",
      "hover:-translate-y-0.5",
    ]
  )}
>
  {isGenerating ? (
    <span className="flex items-center gap-2">
      <Loader2 className="w-3.5 h-3.5 animate-spin" />
      Generating...
    </span>
  ) : (
    <span className="flex items-center gap-2">
      <Sparkles className="w-3.5 h-3.5" />
      Generate Report
    </span>
  )}
</Button>
```

**What changed:**
- Added `Sparkles` icon (from lucide) when ready — signals "this is the magic button"
- Elevated shadow that grows on hover
- Slight lift on hover (`-translate-y-0.5`)
- These effects only apply when `canGenerate` is true — disabled state stays flat

---

## 8. Section Dividers — Subtle Vertical Rhythm

Between config sections, add a subtle connector that hints at progression:

```tsx
{/* Between sections in the config panel */}
<div className="space-y-3">
  <ReportTypeSection {...} stepNumber={1} />

  {/* Connector */}
  <div className="flex justify-center">
    <div className="w-px h-3 bg-gray-200" />
  </div>

  <AreaSection {...} stepNumber={2} />

  <div className="flex justify-center">
    <div className="w-px h-3 bg-gray-200" />
  </div>

  <LookbackSection {...} stepNumber={3} />

  <div className="flex justify-center">
    <div className="w-px h-3 bg-gray-200" />
  </div>

  <DeliverySection {...} stepNumber={4} />
</div>
```

**Alternative — continuous left-side line:**
```tsx
<div className="relative">
  {/* Vertical progress line */}
  <div className="absolute left-[31px] top-8 bottom-8 w-px bg-gray-200" />
  <div
    className="absolute left-[31px] top-8 w-px bg-primary transition-all duration-500"
    style={{ height: `${progressPercent}%` }}
  />

  <div className="space-y-3 relative">
    <ReportTypeSection {...} stepNumber={1} />
    <AreaSection {...} stepNumber={2} />
    <LookbackSection {...} stepNumber={3} />
    <DeliverySection {...} stepNumber={4} />
  </div>
</div>
```

This creates a visual thread connecting sections, reinforcing the "flow" feeling.

---

## 9. Quick Refinement Summary

| Area | Change | Impact |
|------|--------|--------|
| **Header** | Scroll shadow, backdrop blur, title + progress counter | Feels grounded, modern |
| **Section cards** | rounded-xl, shadow-sm, step number badges | More depth, clear progression |
| **Selection cards** | Lift on hover, icon backgrounds, selected dot | More interactive, tactile |
| **Pills** | Smaller text, subtle shadow when selected | Tighter, more refined |
| **Preview panel** | Distinct header bar, "Live Preview" label, pulsing dot | Feels like a tool, not just another card |
| **Step progress** | Integrated connecting line, ring for active, animated progress | Connected, shows journey |
| **Generate button** | Sparkles icon, shadow glow, lift on hover when ready | Celebratory, rewarding |
| **Section spacing** | Vertical connectors between sections | Visual flow, progression |

---

## 10. Implementation Notes

**Dependencies already available (no installs needed):**
- `framer-motion` — already in your stack for AnimatePresence
- `lucide-react` — already used for all icons (Sparkles, ChevronDown, etc.)
- `cn()` utility — already using this everywhere

**Files to modify:**
- `components/report-builder/index.tsx` — Header, layout, section spacing
- `components/report-builder/sections/*.tsx` — All 4 section files
- `components/report-builder/report-preview.tsx` — Preview panel wrapper
- `components/schedule-builder/index.tsx` — Same header/section treatment
- `components/schedule-builder/sections/*.tsx` — All section files
- `app/app/property/new/page.tsx` — Step progress, navigation buttons

**Order of operations:**
1. Header refinement (applies to both Report + Schedule builders)
2. Section card pattern (template it once, apply to all sections)
3. Selection cards and pills (reusable pattern)
4. Preview panel
5. Progress steps (Property wizard)
6. Generate button (all wizards)
7. Section connectors (optional, nice-to-have)

**Estimated time:** These are all CSS/markup tweaks + one scroll listener. No logic changes, no API changes. A focused session should get through all of them.

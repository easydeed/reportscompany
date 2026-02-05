# Frontend UI Audit Report

> Generated read-only audit of TrendyReports frontend UI for design overhaul planning

---

## Part 1: File Structure Map

```
apps/web/
├── app/
│   ├── layout.tsx                    # Root layout (font, Google Maps script)
│   ├── app-layout.tsx               # Client-side layout with sidebar
│   ├── globals.css                   # CSS variables, theming, base styles
│   ├── page.tsx                      # Marketing home page
│   │
│   ├── app/                          # Protected app routes
│   │   ├── layout.tsx               # App shell (auth check, role detection)
│   │   ├── page.tsx                 # Dashboard overview
│   │   │
│   │   ├── reports/
│   │   │   ├── page.tsx             # Reports list
│   │   │   └── new/page.tsx         # Report builder wizard
│   │   │
│   │   ├── schedules/
│   │   │   ├── page.tsx             # Schedules list
│   │   │   ├── new/page.tsx         # Schedule builder wizard
│   │   │   └── [id]/
│   │   │       ├── page.tsx         # Schedule detail
│   │   │       └── edit/page.tsx    # Schedule edit
│   │   │
│   │   ├── property/
│   │   │   ├── page.tsx             # Property reports list
│   │   │   ├── new/page.tsx         # Property report wizard
│   │   │   └── [id]/page.tsx        # Property report detail
│   │   │
│   │   ├── settings/
│   │   │   ├── layout.tsx           # Settings layout (passthrough)
│   │   │   ├── page.tsx             # Settings redirect
│   │   │   ├── profile/page.tsx     # Profile settings
│   │   │   ├── security/page.tsx    # Security settings
│   │   │   ├── branding/page.tsx    # Branding settings
│   │   │   └── billing/page.tsx     # Billing settings
│   │   │
│   │   ├── lead-page/page.tsx       # My Leads page
│   │   ├── people/page.tsx          # My Contacts page
│   │   ├── affiliate/               # Affiliate dashboard routes
│   │   └── admin/                   # Admin routes
│   │
│   ├── login/page.tsx               # Login page
│   ├── register/page.tsx            # Registration page
│   └── [public routes...]           # About, privacy, terms, etc.
│
├── components/
│   ├── ui/                          # 57 shadcn/ui components
│   │   ├── accordion.tsx
│   │   ├── alert.tsx
│   │   ├── avatar.tsx
│   │   ├── badge.tsx
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── checkbox.tsx
│   │   ├── dialog.tsx
│   │   ├── drawer.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── input.tsx
│   │   ├── label.tsx
│   │   ├── popover.tsx
│   │   ├── progress.tsx
│   │   ├── select.tsx
│   │   ├── separator.tsx
│   │   ├── sheet.tsx
│   │   ├── sidebar.tsx              # Full sidebar component system
│   │   ├── skeleton.tsx
│   │   ├── spinner.tsx
│   │   ├── switch.tsx
│   │   ├── table.tsx
│   │   ├── tabs.tsx
│   │   ├── textarea.tsx
│   │   ├── toast.tsx
│   │   ├── toaster.tsx
│   │   ├── tooltip.tsx
│   │   └── ...
│   │
│   ├── report-builder/              # ⭐ DESIGN REFERENCE
│   │   ├── index.tsx               # Main wizard component
│   │   ├── report-preview.tsx
│   │   ├── types.ts
│   │   └── sections/
│   │       ├── report-type-section.tsx
│   │       ├── area-section.tsx
│   │       ├── lookback-section.tsx
│   │       └── delivery-section.tsx
│   │
│   ├── schedule-builder/            # ⭐ DESIGN REFERENCE
│   │   ├── index.tsx               # Main wizard component
│   │   ├── email-preview.tsx
│   │   ├── types.ts
│   │   └── sections/
│   │       ├── report-type-section.tsx
│   │       ├── area-section.tsx
│   │       ├── lookback-section.tsx
│   │       ├── cadence-section.tsx
│   │       └── recipients-section.tsx
│   │
│   ├── property/                    # ⭐ DESIGN REFERENCE
│   │   ├── ThemeSelector.tsx
│   │   ├── ComparablesPicker.tsx
│   │   ├── ComparablesMapModal.tsx
│   │   └── PropertySearchForm.tsx
│   │
│   ├── v0-styling/                  # Styled page shells
│   │   ├── SchedulesListShell.tsx
│   │   ├── PlanPageShell.tsx
│   │   └── AffiliateDashboardShell.tsx
│   │
│   ├── data-table.tsx              # Generic data table wrapper
│   ├── empty-state.tsx             # Empty state component
│   ├── metric-card.tsx             # Dashboard metric cards
│   ├── logo.tsx                    # Logo component
│   ├── navbar.tsx                  # Marketing navbar
│   ├── footer.tsx                  # Marketing footer
│   └── account-switcher.tsx        # Account switcher dropdown
│
├── lib/
│   ├── utils.ts                    # cn() utility
│   ├── api.ts                      # Client-side API fetch
│   ├── api-server.ts               # Server-side API fetch
│   ├── wizard-types.ts             # Shared wizard types
│   └── templates.ts                # Report templates
│
├── hooks/
│   ├── use-toast.ts                # Toast hook
│   └── useGooglePlaces.ts          # Google Places autocomplete
│
└── postcss.config.mjs              # PostCSS with Tailwind v4
```

---

## Part 2: Layout Components

### Root Layout (`app/layout.tsx`)

```tsx
import './globals.css';
import type { Metadata } from 'next';
import { Plus_Jakarta_Sans } from 'next/font/google';
import Script from 'next/script';

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-jakarta',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Market Reports',
  description: 'MLS data. Beautiful reports. Zero effort.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`antialiased ${plusJakarta.variable}`}>
      <head />
      <body className={`min-h-screen ${plusJakarta.className}`}>
        {/* Google Maps API for address autocomplete - load async */}
        {process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY && (
          <Script
            src={`https://maps.googleapis.com/maps/api/js?key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}&libraries=places&loading=async`}
            strategy="afterInteractive"
          />
        )}
        {children}
      </body>
    </html>
  );
}
```

### App Layout Client (`app/app-layout.tsx`)

```tsx
"use client"

import { Suspense, useState, useEffect, useMemo } from "react"
import {
  SidebarProvider,
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenuSub,
  SidebarMenuSubItem,
  SidebarMenuSubButton,
  SidebarFooter,
  SidebarInset,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  LayoutDashboard,
  FileText,
  ChevronRight,
  Shield,
  Calendar,
  Users,
  Settings,
  Building2,
  Building,
  Home,
  UserCheck,
  MessageSquare,
  Link2,
  User,
  Lock,
  Palette,
  CreditCard,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import Link from "next/link"
import { usePathname } from "next/navigation"
import NavAuth from "@/components/NavAuth"
import { AccountSwitcher } from "@/components/account-switcher"
import { Logo } from "@/components/logo"

// Routes where sidebar should be hidden (builder modes)
const BUILDER_ROUTES = [
  "/app/reports/new",
  "/app/schedules/new",
  "/app/schedules/", // Will check for /edit suffix
]

function isBuilderRoute(pathname: string | null): boolean {
  if (!pathname) return false
  if (BUILDER_ROUTES.includes(pathname)) return true
  if (pathname.startsWith("/app/schedules/") && pathname.endsWith("/edit")) return true
  return false
}

function DashboardSidebar({ isAdmin, isAffiliate }: { isAdmin: boolean; isAffiliate: boolean }) {
  const pathname = usePathname()
  const isInAdminSection = pathname?.startsWith("/app/admin")
  const isInSettingsSection = pathname?.startsWith("/app/settings")
  
  const navigation = isAffiliate
    ? [
        { name: "Affiliate Dashboard", href: "/app/affiliate", icon: LayoutDashboard },
        { name: "Market Reports", href: "/app/reports", icon: FileText },
        { name: "Property Reports", href: "/app/property", icon: Home },
        { name: "Scheduled Reports", href: "/app/schedules", icon: Calendar },
        { name: "My Leads", href: "/app/lead-page", icon: Link2 },
        { name: "My Contacts", href: "/app/people", icon: Users },
      ]
    : [
        { name: "Dashboard", href: "/app", icon: LayoutDashboard },
        { name: "Market Reports", href: "/app/reports", icon: FileText },
        { name: "Property Reports", href: "/app/property", icon: Home },
        { name: "Scheduled Reports", href: "/app/schedules", icon: Calendar },
        { name: "My Leads", href: "/app/lead-page", icon: Link2 },
        { name: "My Contacts", href: "/app/people", icon: Users },
      ]
  
  const settingsNavigation = [
    { name: "Profile", href: "/app/settings/profile", icon: User },
    { name: "Security", href: "/app/settings/security", icon: Lock },
    { name: "Branding", href: "/app/settings/branding", icon: Palette },
    { name: "Billing", href: "/app/settings/billing", icon: CreditCard },
  ]
  
  const adminNavigation = [
    { name: "Overview", href: "/app/admin", icon: LayoutDashboard },
    { name: "Title Companies", href: "/app/admin/affiliates", icon: Building2 },
    { name: "All Accounts", href: "/app/admin/accounts", icon: Building },
    { name: "All Users", href: "/app/admin/users", icon: Users },
    { name: "Property Reports", href: "/app/admin/property-reports", icon: Home },
    { name: "Leads", href: "/app/admin/leads", icon: UserCheck },
    { name: "SMS Management", href: "/app/admin/sms", icon: MessageSquare },
  ]

  return (
    <Sidebar>
      <SidebarHeader>
        <Link href="/app" className="flex items-center px-2 py-4">
          <Logo className="h-8" />
        </Link>
      </SidebarHeader>
      <SidebarContent>
        <SidebarMenu>
          {navigation.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/app" && pathname?.startsWith(item.href))
            return (
              <SidebarMenuItem key={item.name}>
                <SidebarMenuButton asChild isActive={isActive}>
                  <Link href={item.href}>
                    <item.icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            )
          })}
          
          {/* Settings Section with Collapsible Sub-menu */}
          <Collapsible defaultOpen={isInSettingsSection} className="group/collapsible-settings">
            <SidebarMenuItem>
              <CollapsibleTrigger asChild>
                <SidebarMenuButton isActive={isInSettingsSection}>
                  <Settings className="w-4 h-4" />
                  <span>Settings</span>
                  <ChevronRight className="ml-auto h-4 w-4 transition-transform group-data-[state=open]/collapsible-settings:rotate-90" />
                </SidebarMenuButton>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <SidebarMenuSub>
                  {settingsNavigation.map((item) => (
                    <SidebarMenuSubItem key={item.name}>
                      <SidebarMenuSubButton asChild isActive={pathname === item.href}>
                        <Link href={item.href}>
                          <item.icon className="w-4 h-4" />
                          <span>{item.name}</span>
                        </Link>
                      </SidebarMenuSubButton>
                    </SidebarMenuSubItem>
                  ))}
                </SidebarMenuSub>
              </CollapsibleContent>
            </SidebarMenuItem>
          </Collapsible>

          {/* Admin Section */}
          {isAdmin && (
            <Collapsible defaultOpen={isInAdminSection} className="group/collapsible-admin">
              {/* ... admin menu items ... */}
            </Collapsible>
          )}
        </SidebarMenu>
      </SidebarContent>
      <SidebarFooter>
        <div className="p-2">
          <div className="glass rounded-lg border border-border p-3">
            <p className="text-xs font-semibold mb-1">Professional Plan</p>
            <p className="text-xs text-muted-foreground mb-2">Ready to generate reports</p>
            <Link href="/app/reports/new">
              <Button size="sm" className="w-full">
                New Report
              </Button>
            </Link>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}

function DashboardTopbar({ accountType, isAdmin, isAffiliate }) {
  // ... user dropdown, account switcher, role badges
  return (
    <header className="flex h-12 shrink-0 items-center gap-4 border-b border-[var(--app-border)] bg-[var(--app-surface)] px-4">
      <SidebarTrigger />
      <div className="flex-1" />
      {/* Account Type Badge */}
      <AccountSwitcher />
      <NavAuth />
      {/* User Dropdown Menu */}
    </header>
  )
}

export default function AppLayoutClient({ children, isAdmin, isAffiliate, accountType }) {
  const pathname = usePathname()
  const inBuilderMode = useMemo(() => isBuilderRoute(pathname), [pathname])
  
  // Builder mode: Full-width layout without sidebar
  if (inBuilderMode) {
    return (
      <div className="min-h-screen w-full" style={{ backgroundColor: 'var(--app-bg)', color: 'var(--app-text)' }}>
        {children}
      </div>
    )
  }
  
  // Normal mode: With sidebar
  return (
    <SidebarProvider>
      <Suspense fallback={<div>Loading...</div>}>
        <div className="flex min-h-screen w-full" style={{ backgroundColor: 'var(--app-bg)', color: 'var(--app-text)' }}>
          <DashboardSidebar isAdmin={isAdmin} isAffiliate={isAffiliate} />
          <SidebarInset className="flex flex-col">
            <DashboardTopbar accountType={accountType} isAdmin={isAdmin} isAffiliate={isAffiliate} />
            <main className="flex-1 p-6 bg-[var(--app-bg)]">{children}</main>
          </SidebarInset>
        </div>
      </Suspense>
    </SidebarProvider>
  )
}
```

### Dashboard Page (`app/app/page.tsx`)

```tsx
import { DashboardOverview } from "@repo/ui"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle, AlertTriangle } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { redirect } from 'next/navigation'
import { DashboardOnboarding } from "@/components/onboarding"
import { createServerApi } from "@/lib/api-server"

export default async function Overview() {
  const api = await createServerApi()
  
  if (!api.isAuthenticated()) {
    redirect('/login')
  }

  const [meRes, dataRes, planUsageRes] = await Promise.all([
    api.get<any>("/v1/me"),
    api.get<any>("/v1/usage"),
    api.get<any>("/v1/account/plan-usage"),
  ])

  // ... data transformation ...

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Overview</h1>
        <p className="text-[var(--app-muted)] mt-1">
          Your account activity and key metrics
        </p>
      </div>

      {/* Onboarding Checklist & Wizard */}
      <DashboardOnboarding />

      {/* Usage Warning Banner */}
      {planUsage && planUsage.decision === 'ALLOW_WITH_WARNING' && (
        <Alert className="border-yellow-500/30 bg-yellow-500/10">
          {/* ... warning content ... */}
        </Alert>
      )}
      
      <DashboardOverview 
        kpis={kpis}
        reports30d={reports30d}
        emails30d={emails30d}
        recent={recent}
      />
    </div>
  )
}
```

### Profile Settings Page (`app/app/settings/profile/page.tsx`)

```tsx
"use client"

import { useEffect, useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Loader2, Save, X } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { ImageUpload } from "@/components/ui/image-upload"

export default function ProfilePage() {
  // ... state and handlers ...

  return (
    <div className="space-y-8 max-w-2xl">
      {/* Section Header */}
      <div>
        <h2 className="text-xl font-semibold">Profile</h2>
        <p className="text-muted-foreground text-sm mt-1">
          Your personal information. This appears on your reports and emails.
        </p>
      </div>

      {/* Photo Section */}
      <div className="bg-card border rounded-xl p-6">
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-4">
          Photo
        </h3>
        {/* Avatar + Upload */}
      </div>

      {/* Personal Information */}
      <div className="bg-card border rounded-xl p-6">
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-4">
          Personal Information
        </h3>
        {/* Form fields */}
      </div>

      {/* Contact Information */}
      <div className="bg-card border rounded-xl p-6">
        {/* Email (read-only), Phone, Website */}
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={saveProfile} disabled={saving} size="lg">
          {saving ? <><Loader2 className="w-4 h-4 animate-spin mr-2" />Saving...</> : <><Save className="w-4 h-4 mr-2" />Save Changes</>}
        </Button>
      </div>
    </div>
  )
}
```

---

## Part 3: The "Good" Wizards (Design Reference)

### Report Builder Wizard

**File:** `components/report-builder/index.tsx`

**Key patterns:**
- Fixed 400px config panel + flexible preview panel layout
- Sticky header with back link and primary action button
- Section-based configuration with completion checkmarks
- "Touched" state tracking for completion indicators
- Real-time preview that updates as user builds

```tsx
"use client"

import { useState, useEffect } from "react"
import { ArrowLeft, Loader2 } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ReportTypeSection } from "./sections/report-type-section"
import { AreaSection } from "./sections/area-section"
import { LookbackSection } from "./sections/lookback-section"
import { DeliverySection } from "./sections/delivery-section"
import { ReportPreview } from "./report-preview"

export function ReportBuilder() {
  const [state, setState] = useState<ReportBuilderState>(DEFAULT_STATE)
  const [branding, setBranding] = useState<BrandingContext>(DEFAULT_BRANDING)
  const [profile, setProfile] = useState<ProfileContext>(DEFAULT_PROFILE)
  const [isGenerating, setIsGenerating] = useState(false)
  
  // Track which sections user has interacted with
  const [touched, setTouched] = useState({
    reportType: false,
    area: false,
    lookback: false,
    delivery: false,
  })

  // ... data fetching, state updates, generation logic ...

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white border-b border-gray-200 px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/app/reports" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
              <ArrowLeft className="w-4 h-4" />
              Back to Reports
            </Link>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/app/reports">
              <Button variant="outline" className="bg-white border-gray-200 text-gray-700 hover:bg-gray-50">
                Cancel
              </Button>
            </Link>
            <Button 
              onClick={handleGenerate}
              disabled={!canGenerate || isGenerating}
              className="bg-violet-600 text-white hover:bg-violet-700 disabled:opacity-50"
            >
              {isGenerating ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Generating...</>
              ) : (
                "Generate Report"
              )}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content - 400px config / flexible preview */}
      <main className="px-8 py-6">
        <div className="grid grid-cols-[400px_1fr] gap-8">
          {/* Left: Config Panel (fixed 400px) */}
          <div className="space-y-4">
            <ReportTypeSection {...} isComplete={isReportTypeComplete} />
            <AreaSection {...} isComplete={isAreaComplete} />
            <LookbackSection {...} isComplete={isLookbackComplete} />
            <DeliverySection {...} hasOption={hasDeliveryOption} />
          </div>

          {/* Right: Preview Panel */}
          <div className="sticky top-24">
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-gray-900">Preview</h3>
                <span className="text-xs text-gray-400">Updates as you build</span>
              </div>
              <ReportPreview state={state} branding={branding} profile={profile} />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
```

### Section Component Pattern

**File:** `components/report-builder/sections/report-type-section.tsx`

```tsx
export function ReportTypeSection({
  reportType,
  audienceFilter,
  onChange,
  onAudienceChange,
  isComplete,
}: ReportTypeSectionProps) {
  return (
    <section className="bg-white border border-gray-200 rounded-lg p-4">
      {/* Section Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-900">Report Type</h3>
        {isComplete && (
          <div className="w-5 h-5 rounded-full bg-green-50 flex items-center justify-center">
            <Check className="w-3 h-3 text-green-500" />
          </div>
        )}
      </div>

      {/* 3 Report Type Cards */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        {REPORT_TYPES.map((type) => {
          const isSelected = reportType === type.id
          const Icon = type.icon
          return (
            <button
              key={type.id}
              onClick={() => handleTypeSelect(type.id)}
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
              <span className="text-xs text-gray-500 mt-0.5 leading-tight">
                {type.description}
              </span>
            </button>
          )
        })}
      </div>

      {/* Audience Pills - Conditional */}
      {showAudiencePills && (
        <div className="pt-3 border-t border-gray-100">
          <p className="text-xs text-gray-500 mb-2">Target audience (optional)</p>
          <div className="flex flex-wrap gap-2">
            {AUDIENCE_PRESETS.map((preset) => (
              <button
                key={preset.id}
                onClick={() => handleAudienceSelect(preset)}
                className={cn(
                  "inline-flex items-center gap-1 px-3 py-1.5 text-sm rounded-full transition-colors",
                  isSelected
                    ? "bg-violet-50 text-violet-700 border border-violet-200"
                    : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
                )}
              >
                {isSelected && <Check className="w-3 h-3" />}
                {preset.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
```

### Property Report Wizard

**File:** `app/app/property/new/page.tsx`

**Key patterns:**
- Step-based wizard with progress bar
- 4 steps: Property → Comparables → Theme → Generate
- Card-wrapped content with navigation buttons
- Status-aware rendering (generating, completed, failed)
- Google Places integration for address search

```tsx
const STEPS = [
  { id: 1, name: "Property", icon: Home },
  { id: 2, name: "Comparables", icon: Map },
  { id: 3, name: "Theme", icon: Palette },
  { id: 4, name: "Generate", icon: FileText },
];

export default function NewPropertyReportPage() {
  const [currentStep, setCurrentStep] = useState(1);
  const [state, setState] = useState<WizardState>(initialState);
  const [generationState, setGenerationState] = useState<"idle" | "generating" | "completed" | "failed">("idle");

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/app/property">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="w-5 h-5" />
          </Button>
        </Link>
        <div>
          <h1 className="font-bold text-2xl">Create Property Report</h1>
          <p className="text-muted-foreground text-sm">
            Generate a professional seller presentation
          </p>
        </div>
      </div>

      {/* Progress */}
      <div>
        <Progress value={progressPercent} className="h-2" />
        <div className="flex justify-between mt-4">
          {STEPS.map((step) => {
            const Icon = step.icon;
            const isActive = currentStep === step.id;
            const isComplete = currentStep > step.id;
            return (
              <div key={step.id} className="flex flex-col items-center gap-2">
                <div className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors",
                  isComplete ? "bg-primary border-primary text-primary-foreground" : "",
                  isActive ? "border-primary bg-primary/10" : "",
                  !isActive && !isComplete ? "border-muted-foreground/30 bg-muted/30" : ""
                )}>
                  {isComplete ? <Check className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                </div>
                <span className={cn("text-xs font-medium hidden sm:block", isActive || isComplete ? "text-foreground" : "text-muted-foreground")}>
                  {step.name}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Step Content */}
      <Card>
        <CardContent className="pt-6">
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
          {currentStep === 4 && renderStep4()}
        </CardContent>
      </Card>

      {/* Navigation */}
      {generationState === "idle" && (
        <div className="flex justify-between">
          <Button variant="outline" onClick={handleBack} disabled={currentStep === 1}>
            <ArrowLeft className="w-4 h-4" /> Back
          </Button>
          {currentStep < STEPS.length && (
            <Button onClick={handleNext}>
              Continue <ArrowRight className="w-4 h-4" />
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## Part 4: Component Library Inventory

### shadcn/ui Components (`components/ui/`)

```
accordion.tsx
alert-dialog.tsx
alert.tsx
aspect-ratio.tsx
avatar.tsx
badge.tsx
breadcrumb.tsx
button-group.tsx
button.tsx
calendar.tsx
card.tsx
carousel.tsx
chart.tsx
checkbox.tsx
collapsible.tsx
command.tsx
context-menu.tsx
dialog.tsx
drawer.tsx
dropdown-menu.tsx
empty.tsx
field.tsx
form.tsx
hover-card.tsx
image-upload.tsx
input-group.tsx
input-otp.tsx
input.tsx
item.tsx
kbd.tsx
label.tsx
menubar.tsx
navigation-menu.tsx
pagination.tsx
popover.tsx
progress.tsx
radio-group.tsx
resizable.tsx
scroll-area.tsx
select.tsx
separator.tsx
sheet.tsx
sidebar.tsx           # Full sidebar system with Provider, Menu, Sub-menu
skeleton.tsx
slider.tsx
sonner.tsx
spinner.tsx
switch.tsx
table.tsx
tabs.tsx
textarea.tsx
toast.tsx
toaster.tsx
toggle-group.tsx
toggle.tsx
tooltip.tsx
use-mobile.tsx
use-toast.ts
```

### Custom Components (Non-shadcn)

| Component | Location | Description |
|-----------|----------|-------------|
| `DataTable` | `components/data-table.tsx` | Generic table wrapper with glass styling |
| `EmptyState` | `components/empty-state.tsx` | Empty state with icon, title, description, action |
| `MetricCard` | `components/metric-card.tsx` | Dashboard KPI card with trend indicator |
| `Logo` | `components/logo.tsx` | Brand logo component |
| `AccountSwitcher` | `components/account-switcher.tsx` | Multi-account dropdown |
| `NavAuth` | `components/NavAuth.tsx` | Auth state in navbar |
| `ThemeSelector` | `components/property/ThemeSelector.tsx` | Property report theme picker |
| `ComparablesPicker` | `components/property/ComparablesPicker.tsx` | Comparable property selection |
| `ComparablesMapModal` | `components/property/ComparablesMapModal.tsx` | Map view for comparables |

---

## Part 5: Current Design Patterns

### 1. Color Palette

**CSS Variables (globals.css):**

```css
:root {
  /* Primary: Violet */
  --primary: oklch(0.55 0.25 290);           /* #7C3AED */
  --primary-foreground: oklch(1 0 0);

  /* Accent: Coral/Orange */
  --accent: oklch(0.68 0.18 35);             /* #F26B2B */
  --accent-foreground: oklch(1 0 0);

  /* Secondary accent: Bright Blue */
  --accent-blue: oklch(0.6 0.2 250);         /* #3B82F6 */

  /* Neutrals */
  --background: oklch(0.99 0 0);             /* Off-white */
  --foreground: oklch(0.15 0.01 264);        /* Dark slate */
  --card: oklch(1 0 0);                      /* White */
  --muted: oklch(0.97 0.005 264);
  --muted-foreground: oklch(0.48 0.01 264);

  /* Status */
  --success: oklch(0.65 0.18 150);           /* Green */
  --warning: oklch(0.75 0.16 65);            /* Amber */
  --destructive: oklch(0.62 0.25 27);        /* Red */

  /* Borders */
  --border: oklch(0.9 0.005 264);
  --ring: oklch(0.55 0.25 290);              /* Violet focus ring */

  /* App-specific tokens */
  --app-bg: #f5f5f7;
  --app-surface: #ffffff;
  --app-border: #e5e7eb;
  --app-text: #111827;
  --app-muted: #6b7280;
  --app-primary: #7c3aed;
  --app-accent: #f26b2b;
}
```

### 2. Typography

**Font:** Plus Jakarta Sans (loaded via next/font/google)

**Weights:** 400, 500, 600, 700, 800

**Configuration:**
```tsx
const plusJakarta = Plus_Jakarta_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-jakarta',
  display: 'swap',
});
```

**CSS:**
```css
@theme inline {
  --font-sans: "Plus Jakarta Sans", system-ui, sans-serif;
  --font-display: "Plus Jakarta Sans", system-ui, sans-serif;
}

body {
  font-size: 15px;
  line-height: 1.6;
}

h1, h2, h3, h4, h5, h6 {
  @apply font-display tracking-tight;
}
```

### 3. Spacing

Using **Tailwind defaults** with standard spacing scale.

Common patterns:
- Page padding: `px-8 py-6` or `p-6`
- Section spacing: `space-y-6` or `space-y-4`
- Card padding: `p-6` (via Card component)
- Gap in grids: `gap-4`, `gap-3`, `gap-8`

### 4. Card Patterns

**Standard Card (shadcn):**
```tsx
<Card>
  bg-[var(--app-surface)] 
  text-[var(--app-text)] 
  rounded-xl 
  border border-[var(--app-border)] 
  shadow-sm
</Card>
```

**Glass Card:**
```css
.glass {
  @apply bg-white/90 backdrop-blur-lg border border-border/40 shadow-sm;
}
```

**Wizard Section Card:**
```tsx
<section className="bg-white border border-gray-200 rounded-lg p-4">
```

### 5. Table Patterns

Using **shadcn Table** with custom DataTable wrapper:
```tsx
<div className="glass rounded-xl border border-border overflow-hidden">
  <Table>
    <TableHeader>
      <TableRow className="bg-secondary/50 hover:bg-secondary/50">
        <TableHead className="font-display font-semibold">...</TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      <TableRow className="hover:bg-secondary/30">...</TableRow>
    </TableBody>
  </Table>
</div>
```

### 6. Form Patterns

**Wizard Forms (good pattern):**
- Section cards with headers
- Completion checkmarks
- Selection cards (grid of clickable options)
- Pill buttons for presets

**Settings Forms:**
- Grouped sections with uppercase labels
- Standard Input + Label pairs
- Read-only fields with background

### 7. Empty States

```tsx
<EmptyState
  icon={<SomeIcon className="w-8 h-8" />}
  title="No data yet"
  description="Longer explanation text"
  action={{ label: "Add First", onClick: () => {} }}
/>
```

Pattern:
- Centered layout
- Icon in circular background
- Title + description
- Optional action button

### 8. Loading States

**Full page:**
```tsx
<div className="flex items-center justify-center py-24">
  <Loader2 className="w-8 h-8 animate-spin text-violet-600 mx-auto mb-4" />
  <p className="text-muted-foreground">Loading...</p>
</div>
```

**Button:**
```tsx
<Button disabled={loading}>
  {loading ? <><Loader2 className="animate-spin mr-2" />Saving...</> : "Save"}
</Button>
```

**Skeletons:** Available but not widely used.

### 9. Page Headers

**Dashboard pages:**
```tsx
<div className="flex items-center justify-between">
  <div>
    <h1 className="text-3xl font-bold tracking-tight">Title</h1>
    <p className="text-[var(--app-muted)] mt-1">Description</p>
  </div>
  <Button>Primary Action</Button>
</div>
```

**Settings pages:**
```tsx
<div>
  <h2 className="text-xl font-semibold">Section Title</h2>
  <p className="text-muted-foreground text-sm mt-1">Description</p>
</div>
```

### 10. Responsive Behavior

**Sidebar:**
- Uses shadcn sidebar with Sheet for mobile
- Collapsible via keyboard shortcut (Ctrl+B)
- `SIDEBAR_WIDTH = '16rem'` (desktop)
- `SIDEBAR_WIDTH_MOBILE = '18rem'` (mobile Sheet)

**Layout:**
- Builder mode: Full width, no sidebar
- Dashboard mode: Sidebar + content

**Breakpoints:** Using Tailwind defaults (sm, md, lg, xl)

---

## Part 6: Screenshots

> Not available - no running dev server access

---

## Summary: Areas Needing Design Overhaul

Based on this audit, the following areas need attention to match the wizard quality level:

### ✅ Good (Design Reference)
- Report Builder Wizard
- Schedule Builder Wizard
- Property Report Wizard
- Wizard section components

### ⚠️ Needs Work
1. **Dashboard page** - Uses external `DashboardOverview` component (from @repo/ui)
2. **Reports list page** - Basic table, minimal styling
3. **Schedules list page** - Better but inconsistent with wizards
4. **Settings pages** - Good structure but could be more polished
5. **Empty states** - Inconsistent usage

### 🔴 Missing/Incomplete
1. **No tailwind.config** - Using Tailwind v4 with postcss plugin
2. **Loading skeletons** - Available but rarely used
3. **Mobile responsiveness** - Needs testing
4. **Consistent page headers** - Varies by page

### Design System Tokens to Standardize
1. Unify `--app-*` tokens with semantic tokens
2. Standardize card styles (glass vs solid)
3. Consistent section header patterns
4. Unified completion indicator style

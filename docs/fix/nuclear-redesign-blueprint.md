# TrendyReports — Nuclear UI Redesign: Implementation Blueprint

> **For**: Cursor AI / Claude Code implementation
> **Scope**: Complete UI rebuild of all internal `/app/*` pages
> **Constraint**: ZERO functionality changes — same API calls, same state, same business logic. Only the visual layer changes.

---

## Table of Contents

1. [Design System Foundation](#1-design-system-foundation)
2. [Phase 1: globals.css Token Overhaul](#2-phase-1-globalscss)
3. [Phase 2: Sidebar Rebuild (Dark Mode)](#3-phase-2-sidebar)
4. [Phase 3: Top Bar Redesign](#4-phase-3-topbar)
5. [Phase 4: Shared Components Refresh](#5-phase-4-shared-components)
6. [Phase 5: Dashboard Redesign](#6-phase-5-dashboard)
7. [Phase 6: List Pages (Unified Table Pattern)](#7-phase-6-list-pages)
8. [Phase 7: Settings Pages](#8-phase-7-settings)
9. [Phase 8: Admin Pages](#9-phase-8-admin)
10. [Phase 9: Affiliate Pages](#10-phase-9-affiliate)
11. [Phase 10: Loading & Error States](#11-phase-10-loading-error)
12. [Phase 11: Polish & Micro-animations](#12-phase-11-polish)
13. [File-by-File Change Map](#13-file-change-map)

---

## 1. Design System Foundation

### Target Audience
- **Primary**: Title Representatives (Affiliates) — manage agent networks, need professional admin tools
- **Secondary**: Real Estate Agents — create reports, manage leads, need efficient workflows
- **Aesthetic**: "Premium productivity tool" — think Linear meets Stripe Dashboard. Not startup-flashy, not corporate-boring. Refined, authoritative, efficient.

### Design Direction: "Refined Authority"

| Principle | Execution |
|-----------|-----------|
| **Dark sidebar** | Slate 900 background — modern SaaS standard (Linear, Notion, Vercel) |
| **Indigo primary** | Deeper than violet, more sophisticated than blue — conveys trust |
| **Warm gold accent** | Real estate DNA — premium feel without being gaudy |
| **Clean content area** | White cards on light gray — data is the star |
| **Tight spacing** | Professional density without feeling cramped |

---

## 2. Phase 1: globals.css Token Overhaul

### File: `apps/web/app/globals.css`

Replace the ENTIRE `:root` and `.dark` blocks. Keep everything else (the `@theme inline`, `@layer base`, Google Places styles).

```css
@import "tailwindcss";

@custom-variant dark (&:is(.dark *));

html {
  scroll-behavior: smooth;
}

:root {
  /* ── Backgrounds ── */
  --background: #F8FAFC;            /* Slate-50: cooler, more professional */
  --card: #FFFFFF;
  --popover: #FFFFFF;
  --muted: #F1F5F9;                 /* Slate-100: subtle differentiation */

  /* ── Text ── */
  --foreground: #0F172A;            /* Slate-900: strongest contrast */
  --card-foreground: #0F172A;
  --popover-foreground: #0F172A;
  --muted-foreground: #64748B;      /* Slate-500: readable secondary */

  /* ── Brand ── */
  --primary: #4F46E5;               /* Indigo-600: authority + sophistication */
  --primary-foreground: #FFFFFF;
  --accent: #D97706;                /* Amber-600: warm gold, real estate DNA */
  --accent-foreground: #FFFFFF;
  --accent-blue: #3B82F6;           /* Blue-500: data viz accent */

  /* ── Secondary ── */
  --secondary: #F1F5F9;
  --secondary-foreground: #0F172A;

  /* ── Interactive ── */
  --ring: #4F46E5;
  --border: #E2E8F0;                /* Slate-200: softer than gray-200 */
  --input: #E2E8F0;

  /* ── Status ── */
  --success: #059669;               /* Emerald-600: professional green */
  --warning: #D97706;               /* Amber-600: consistent with accent */
  --destructive: #DC2626;           /* Red-600: clear danger */
  --destructive-foreground: #FFFFFF;

  /* ── Chart colors ── */
  --chart-1: #4F46E5;               /* Indigo */
  --chart-2: #D97706;               /* Amber */
  --chart-3: #3B82F6;               /* Blue */
  --chart-4: #059669;               /* Emerald */
  --chart-5: #8B5CF6;               /* Violet */

  /* ── Radius ── */
  --radius: 0.5rem;

  /* ── Sidebar (DARK) ── */
  --sidebar: #0F172A;               /* Slate-900 */
  --sidebar-foreground: #CBD5E1;    /* Slate-300 */
  --sidebar-border: #1E293B;        /* Slate-800 */
  --sidebar-accent: #1E293B;        /* Slate-800 hover */
  --sidebar-accent-foreground: #F1F5F9; /* Slate-100 */
  --sidebar-primary: #818CF8;       /* Indigo-400: bright on dark */
  --sidebar-primary-foreground: #FFFFFF;
  --sidebar-ring: #818CF8;
  --sidebar-muted: #475569;         /* Slate-600: section labels */

  /* ── Extended tokens ── */
  --shadow-sm: 0 1px 2px 0 rgba(0,0,0,0.03);
  --shadow-card: 0 1px 3px 0 rgba(0,0,0,0.04), 0 1px 2px -1px rgba(0,0,0,0.04);
  --shadow-elevated: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -2px rgba(0,0,0,0.05);
}

/* Dark mode - keep this for potential future use but sidebar is always dark */
.dark {
  --background: #0F172A;
  --card: #1E293B;
  --popover: #1E293B;
  --muted: #334155;
  --foreground: #F8FAFC;
  --card-foreground: #F8FAFC;
  --popover-foreground: #F8FAFC;
  --muted-foreground: #94A3B8;
  --primary: #818CF8;
  --primary-foreground: #0F172A;
  --accent: #FBBF24;
  --accent-foreground: #0F172A;
  --accent-blue: #60A5FA;
  --secondary: #334155;
  --secondary-foreground: #F8FAFC;
  --ring: #818CF8;
  --border: #334155;
  --input: #334155;
  --success: #34D399;
  --warning: #FBBF24;
  --destructive: #F87171;
  --destructive-foreground: #0F172A;
  --sidebar: #0F172A;
  --sidebar-foreground: #E2E8F0;
  --sidebar-border: #334155;
  --sidebar-accent: #334155;
  --sidebar-accent-foreground: #F8FAFC;
  --sidebar-primary: #818CF8;
  --sidebar-primary-foreground: #0F172A;
  --sidebar-ring: #818CF8;
}
```

### Update `@theme inline` block — add the new tokens:

Add after existing sidebar tokens:
```css
  --color-sidebar-muted: var(--sidebar-muted);
```

### Update `@layer base` — replace gradient classes:

```css
@layer base {
  * {
    @apply border-border;
  }

  body {
    @apply bg-background text-foreground;
    font-size: 14px;        /* Tighter than 15px for density */
    line-height: 1.6;
  }

  h1, h2, h3, h4, h5, h6 {
    @apply font-display;
  }

  h1 {
    @apply tracking-tight;
  }

  /* Brand gradient - updated to indigo */
  .gradient-trendy {
    background: linear-gradient(135deg, #4F46E5 0%, #D97706 100%);
  }

  .gradient-chart {
    background: linear-gradient(180deg, rgba(79, 70, 229, 0.08) 0%, transparent 100%);
  }

  *:focus-visible {
    @apply outline-none ring-2 ring-offset-2 ring-offset-background ring-primary;
  }

  @keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
  }

  .shimmer {
    animation: shimmer 2s infinite linear;
    background: linear-gradient(to right, transparent 0%, rgba(79, 70, 229, 0.06) 50%, transparent 100%);
    background-size: 1000px 100%;
  }

  .trend-up { @apply text-emerald-600; }
  .trend-down { @apply text-red-600; }
}
```

---

## 3. Phase 2: Sidebar Rebuild (Dark Mode)

### File: `apps/web/app/app-layout.tsx`

This is the biggest visual change. The sidebar goes from light to dark, gets tighter spacing, a refined nav structure, and a polished footer.

**Key changes:**
1. Dark sidebar background (handled by CSS tokens above — shadcn's Sidebar component reads `--sidebar` tokens)
2. Tighter nav items with refined icons
3. Section dividers with muted labels
4. Better plan usage display in footer
5. Refined top bar with breadcrumbs

Replace the `DashboardSidebar` component:

```tsx
function DashboardSidebar({ isAdmin, isAffiliate }: { isAdmin: boolean; isAffiliate: boolean }) {
  const pathname = usePathname()
  const [planInfo, setPlanInfo] = useState<{ plan_name: string; reports_used: number; reports_limit: number } | null>(null)
  
  useEffect(() => {
    fetch("/api/proxy/v1/account/plan-usage", { credentials: "include" })
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data?.plan) {
          setPlanInfo({
            plan_name: data.plan.plan_name || "Free",
            reports_used: data.info?.reports_this_period || 0,
            reports_limit: data.plan.monthly_reports_limit || 10,
          })
        }
      })
      .catch(() => {})
  }, [])
  
  const isInAdminSection = pathname?.startsWith("/app/admin")
  const isInSettingsSection = pathname?.startsWith("/app/settings")
  
  const usagePercent = planInfo ? Math.min((planInfo.reports_used / planInfo.reports_limit) * 100, 100) : 0

  const mainNavigation = isAffiliate
    ? [
        { name: "Dashboard", href: "/app/affiliate", icon: LayoutDashboard },
        { name: "Market Reports", href: "/app/reports", icon: FileText },
        { name: "Property Reports", href: "/app/property", icon: Home },
        { name: "Schedules", href: "/app/schedules", icon: Calendar },
      ]
    : [
        { name: "Dashboard", href: "/app", icon: LayoutDashboard },
        { name: "Market Reports", href: "/app/reports", icon: FileText },
        { name: "Property Reports", href: "/app/property", icon: Home },
        { name: "Schedules", href: "/app/schedules", icon: Calendar },
      ]
  
  const engageNavigation = [
    { name: "Lead Pages", href: "/app/lead-page", icon: Link2 },
    { name: "Contacts", href: "/app/people", icon: Users },
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
    { name: "Accounts", href: "/app/admin/accounts", icon: Building },
    { name: "Users", href: "/app/admin/users", icon: Users },
    { name: "Property Reports", href: "/app/admin/property-reports", icon: Home },
    { name: "Leads", href: "/app/admin/leads", icon: UserCheck },
    { name: "SMS", href: "/app/admin/sms", icon: MessageSquare },
  ]

  return (
    <Sidebar>
      <SidebarHeader>
        <Link href="/app" className="flex items-center px-3 py-4">
          <Logo className="h-7 invert brightness-200" />
        </Link>
      </SidebarHeader>

      <SidebarContent>
        {/* Quick Action */}
        <div className="px-3 mb-2">
          <Button size="sm" className="w-full bg-indigo-500 hover:bg-indigo-400 text-white shadow-sm" asChild>
            <Link href="/app/reports/new">
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              New Report
            </Link>
          </Button>
        </div>

        {/* Main Navigation */}
        <SidebarGroup>
          <SidebarGroupLabel className="text-[10px] uppercase tracking-[0.08em] font-semibold text-sidebar-muted px-3">
            Reports
          </SidebarGroupLabel>
          <SidebarMenu>
            {mainNavigation.map((item) => {
              const isActive = pathname === item.href || (item.href !== "/app" && item.href !== "/app/affiliate" && pathname?.startsWith(item.href))
              return (
                <SidebarMenuItem key={item.name}>
                  <SidebarMenuButton asChild isActive={isActive}>
                    <Link href={item.href} prefetch={true}>
                      <item.icon className="w-4 h-4" />
                      <span className="text-[13px]">{item.name}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              )
            })}
          </SidebarMenu>
        </SidebarGroup>

        {/* Engage */}
        <SidebarGroup>
          <SidebarGroupLabel className="text-[10px] uppercase tracking-[0.08em] font-semibold text-sidebar-muted px-3">
            Engage
          </SidebarGroupLabel>
          <SidebarMenu>
            {engageNavigation.map((item) => {
              const isActive = pathname === item.href || pathname?.startsWith(item.href)
              return (
                <SidebarMenuItem key={item.name}>
                  <SidebarMenuButton asChild isActive={isActive}>
                    <Link href={item.href} prefetch={true}>
                      <item.icon className="w-4 h-4" />
                      <span className="text-[13px]">{item.name}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              )
            })}
          </SidebarMenu>
        </SidebarGroup>

        {/* Settings */}
        <SidebarGroup>
          <SidebarGroupLabel className="text-[10px] uppercase tracking-[0.08em] font-semibold text-sidebar-muted px-3">
            Account
          </SidebarGroupLabel>
          <SidebarMenu>
            <Collapsible defaultOpen={isInSettingsSection} className="group/collapsible-settings">
              <SidebarMenuItem>
                <CollapsibleTrigger asChild>
                  <SidebarMenuButton isActive={isInSettingsSection}>
                    <Settings className="w-4 h-4" />
                    <span className="text-[13px]">Settings</span>
                    <ChevronRight className="ml-auto h-3.5 w-3.5 transition-transform group-data-[state=open]/collapsible-settings:rotate-90" />
                  </SidebarMenuButton>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <SidebarMenuSub>
                    {settingsNavigation.map((item) => (
                      <SidebarMenuSubItem key={item.name}>
                        <SidebarMenuSubButton asChild isActive={pathname === item.href}>
                          <Link href={item.href} prefetch={true}>
                            <item.icon className="w-3.5 h-3.5" />
                            <span className="text-[13px]">{item.name}</span>
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
                <SidebarMenuItem>
                  <CollapsibleTrigger asChild>
                    <SidebarMenuButton isActive={isInAdminSection}>
                      <Shield className="w-4 h-4" />
                      <span className="text-[13px]">Admin</span>
                      <ChevronRight className="ml-auto h-3.5 w-3.5 transition-transform group-data-[state=open]/collapsible-admin:rotate-90" />
                    </SidebarMenuButton>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <SidebarMenuSub>
                      {adminNavigation.map((item) => (
                        <SidebarMenuSubItem key={item.name}>
                          <SidebarMenuSubButton asChild isActive={pathname === item.href}>
                            <Link href={item.href} prefetch={true}>
                              <item.icon className="w-3.5 h-3.5" />
                              <span className="text-[13px]">{item.name}</span>
                            </Link>
                          </SidebarMenuSubButton>
                        </SidebarMenuSubItem>
                      ))}
                    </SidebarMenuSub>
                  </CollapsibleContent>
                </SidebarMenuItem>
              </Collapsible>
            )}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <div className="px-3 py-3">
          <div className="rounded-lg border border-sidebar-border bg-sidebar-accent/50 p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-sidebar-muted">
                {planInfo?.plan_name || "Free"} Plan
              </span>
              <span className="text-[11px] text-sidebar-foreground/70">
                {planInfo?.reports_used || 0}/{planInfo?.reports_limit || 10}
              </span>
            </div>
            <div className="h-1 bg-sidebar-border rounded-full overflow-hidden">
              <div 
                className="h-full bg-indigo-400 rounded-full transition-all duration-500"
                style={{ width: `${usagePercent}%` }}
              />
            </div>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
```

Replace the `DashboardTopbar` component:

```tsx
function DashboardTopbar({ accountType, isAdmin, isAffiliate }: { accountType?: string; isAdmin: boolean; isAffiliate: boolean }) {
  const [user, setUser] = useState<{ email: string; first_name?: string; last_name?: string } | null>(null)
  
  useEffect(() => {
    fetch("/api/proxy/v1/users/me", { credentials: "include" })
      .then(res => res.ok ? res.json() : null)
      .then(data => { if (data) setUser(data) })
      .catch(() => {})
  }, [])
  
  async function handleLogout() {
    try {
      await fetch("/api/proxy/v1/auth/logout", { method: "POST", credentials: "include" })
    } catch {}
    window.location.href = "/login"
  }
  
  const displayName = user?.first_name && user?.last_name 
    ? `${user.first_name} ${user.last_name}`
    : user?.first_name || user?.email?.split('@')[0] || "User"
  const displayEmail = user?.email || ""
  const initials = displayName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() || "U"
  
  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-border bg-white px-4">
      <SidebarTrigger className="text-muted-foreground hover:text-foreground" />
      
      <Separator orientation="vertical" className="h-5" />
      
      <div className="flex-1" />

      {/* Account Type Badge */}
      {accountType === "INDUSTRY_AFFILIATE" && (
        <span className="rounded-full bg-amber-50 text-amber-700 text-[11px] font-semibold px-2.5 py-0.5 border border-amber-200 flex items-center gap-1.5 uppercase tracking-wide">
          <Building2 className="h-3 w-3" />
          Title Rep
        </span>
      )}
      {accountType === "REGULAR" && (
        <span className="rounded-full bg-indigo-50 text-indigo-600 text-[11px] font-semibold px-2.5 py-0.5 border border-indigo-200 uppercase tracking-wide">
          Agent
        </span>
      )}

      <AccountSwitcher />

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="relative h-8 w-8 rounded-full">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-indigo-600 text-white text-xs font-semibold">{initials}</AvatarFallback>
            </Avatar>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel>
            <div className="flex flex-col space-y-0.5">
              <p className="text-sm font-semibold">{displayName}</p>
              <p className="text-xs text-muted-foreground">{displayEmail}</p>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem asChild>
            <Link href="/app/settings/profile">
              <User className="w-3.5 h-3.5 mr-2" />Profile
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href="/app/settings/branding">
              <Palette className="w-3.5 h-3.5 mr-2" />Branding
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href="/app/settings/billing">
              <CreditCard className="w-3.5 h-3.5 mr-2" />Billing
            </Link>
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-red-600 focus:text-red-600">
            Log out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  )
}
```

Also update the main content area padding:

```tsx
// In AppLayoutClient, change:
<main className="flex-1 p-6 bg-background">{children}</main>
// To:
<main className="flex-1 px-6 py-5 bg-background">{children}</main>
```

**NOTE**: The imports at the top of `app-layout.tsx` need `Building2` added if not already present (it is — confirmed in extraction).

---

## 4. Phase 3: Top Bar — Additional Imports

Add `Building2` import to the existing lucide-react import in `app-layout.tsx`. Ensure `User`, `Palette`, `CreditCard` are also imported (they already are).

---

## 5. Phase 4: Shared Components Refresh

### 5A. `components/page-header.tsx`

```tsx
"use client"

import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

interface PageHeaderProps {
  title: string
  description?: string
  action?: ReactNode
  className?: string
}

export function PageHeader({ title, description, action, className }: PageHeaderProps) {
  return (
    <div className={cn("flex items-center justify-between", className)}>
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-foreground">{title}</h1>
        {description && (
          <p className="text-[13px] text-muted-foreground mt-0.5">{description}</p>
        )}
      </div>
      {action && (
        <div className="flex items-center gap-2">
          {action}
        </div>
      )}
    </div>
  )
}
```

### 5B. `components/metric-card.tsx`

```tsx
"use client"

import { cn } from "@/lib/utils"
import type { ReactNode } from "react"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"

interface MetricCardProps {
  label: string
  value: string | number
  change?: number
  trend?: "up" | "down" | "neutral"
  icon?: ReactNode
  className?: string
  index?: number
}

export function MetricCard({ label, value, change, trend = "neutral", icon, className, index = 0 }: MetricCardProps) {
  return (
    <div
      className={cn(
        "bg-card border border-border rounded-xl p-4 shadow-[var(--shadow-card)] hover:shadow-[var(--shadow-elevated)] transition-shadow duration-200",
        className,
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.06em]">
          {label}
        </span>
        {icon && (
          <div className="w-8 h-8 rounded-lg bg-primary/8 flex items-center justify-center text-primary">
            {icon}
          </div>
        )}
      </div>
      <div className="text-2xl font-bold text-foreground tracking-tight">{value}</div>
      {change !== undefined && (
        <div className="flex items-center gap-1.5 mt-1.5">
          <div className={cn(
            "flex items-center gap-0.5 text-xs font-medium",
            trend === "up" ? "text-emerald-600" : trend === "down" ? "text-red-600" : "text-muted-foreground"
          )}>
            {trend === "up" ? <TrendingUp className="w-3 h-3" /> : trend === "down" ? <TrendingDown className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
            <span>{Math.abs(change)}%</span>
          </div>
          <span className="text-[11px] text-muted-foreground">vs last period</span>
        </div>
      )}
    </div>
  )
}
```

**Change**: Removed `framer-motion` dependency (the staggered animation was subtle and adds bundle weight). If you want to keep animation, wrap in `motion.div` with the existing import — but I recommend removing it for snappier page loads.

### 5C. `components/status-badge.tsx`

Find this file and update the color mappings to use the new indigo/amber palette:

```tsx
// Update status color mappings:
const statusStyles: Record<string, string> = {
  completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  complete: "bg-emerald-50 text-emerald-700 border-emerald-200",
  active: "bg-emerald-50 text-emerald-700 border-emerald-200",
  processing: "bg-amber-50 text-amber-700 border-amber-200",
  pending: "bg-slate-50 text-slate-600 border-slate-200",
  failed: "bg-red-50 text-red-700 border-red-200",
  draft: "bg-slate-50 text-slate-500 border-slate-200",
  new: "bg-indigo-50 text-indigo-700 border-indigo-200",
}
```

### 5D. `components/empty-state.tsx`

Update to use indigo instead of violet/purple:

```tsx
// Change any bg-purple-*, text-purple-* references to:
// bg-primary/10, text-primary (which will resolve to indigo via tokens)
// The existing EmptyState likely already uses token-based colors — verify and fix any hardcoded purple references.
```

---

## 6. Phase 5: Dashboard Redesign

### File: `apps/web/app/app/page.tsx`

The dashboard structure is already solid. Main changes:
1. Remove motion import dependency if present
2. Tighten spacing
3. Better activity feed styling

Replace the main return JSX — keep ALL the data fetching logic identical:

```tsx
  return (
    <div className="space-y-5">
      <PageHeader
        title="Overview"
        description="Your account activity and key metrics"
        action={
          <Button asChild size="sm">
            <Link href="/app/reports/new">
              <Plus className="w-4 h-4 mr-1.5" />
              New Report
            </Link>
          </Button>
        }
      />

      {/* Usage Warnings — keep existing Alert components exactly as-is */}
      {/* ... no changes to the warning banners ... */}

      {/* Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard label="Reports" value={data?.summary?.total_reports ?? 0} icon={<FileText className="w-4 h-4" />} index={0} />
        <MetricCard label="Emails Sent" value={data?.recent_emails?.length ?? 0} icon={<Mail className="w-4 h-4" />} index={1} />
        <MetricCard label="Active Schedules" value={data?.limits?.active_schedules ?? 0} icon={<Calendar className="w-4 h-4" />} index={2} />
        <MetricCard label="Avg. Render" value={data?.summary?.avg_ms ? `${Math.round(data.summary.avg_ms)}ms` : '—'} icon={<Clock className="w-4 h-4" />} index={3} />
      </div>

      {/* Two-column: Activity + Onboarding */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
          <div className="px-4 py-3 border-b border-border flex items-center justify-between">
            <h3 className="text-[13px] font-semibold text-foreground">Recent Activity</h3>
            <Link href="/app/reports" className="text-xs text-primary hover:text-primary/80 font-medium">
              View all →
            </Link>
          </div>
          {/* Keep existing activity list rendering exactly as-is */}
          {/* Just verify it uses token colors, not hardcoded purple */}
        </div>

        <div className="lg:col-span-1">
          <DashboardOnboarding initialStatus={onboardingStatus} />
        </div>
      </div>
    </div>
  )
```

---

## 7. Phase 6: List Pages (Unified Pattern)

All list pages follow the same pattern. Apply these changes consistently:

### Table Header Styling (all list pages)

```tsx
<TableRow className="bg-muted/40 hover:bg-muted/40 border-b border-border">
  <TableHead className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] py-2.5">
    Column Name
  </TableHead>
</TableRow>
```

### Table Row Styling

```tsx
<TableRow className="hover:bg-muted/30 transition-colors border-b border-border/50 last:border-0">
  <TableCell className="py-3">
    {/* content */}
  </TableCell>
</TableRow>
```

### Table Container

```tsx
<div className="bg-card border border-border rounded-xl overflow-hidden shadow-[var(--shadow-card)]">
  <Table>...</Table>
  <div className="flex items-center justify-between px-4 py-2.5 border-t border-border bg-muted/20">
    <p className="text-[11px] text-muted-foreground">
      Showing {items.length} items
    </p>
  </div>
</div>
```

### Pages to Update

Apply the unified table pattern to:
1. `app/app/reports/page.tsx` — Market Reports list
2. `app/app/property/page.tsx` — Property Reports list
3. `app/app/schedules/page.tsx` — Schedules list
4. `app/app/leads/page.tsx` — Leads list
5. `app/app/people/page.tsx` — Contacts list
6. `app/app/admin/accounts/page.tsx` — Admin accounts
7. `app/app/admin/users/page.tsx` — Admin users
8. `app/app/admin/property-reports/page.tsx` — Admin property reports
9. `app/app/admin/leads/page.tsx` — Admin leads

For each: keep ALL data fetching, state management, and business logic. Only update className strings.

### Key Search-and-Replace Patterns

Across all pages:
```
bg-purple-50  →  bg-indigo-50
text-purple-600  →  text-indigo-600
text-purple-700  →  text-indigo-700
border-purple-200  →  border-indigo-200
bg-purple-100  →  bg-indigo-100
from-purple-600  →  from-indigo-600
to-purple-700  →  to-indigo-700
to-purple-800  →  to-indigo-800
hover:from-purple-700  →  hover:from-indigo-700
hover:to-purple-800  →  hover:to-indigo-800
```

---

## 8. Phase 7: Settings Pages

### File: `app/app/settings/layout.tsx`

Currently a passthrough. Keep it that way — the sidebar already handles settings navigation.

### Files: `app/app/settings/profile/page.tsx`, `security/page.tsx`, `branding/page.tsx`, `billing/page.tsx`

Apply consistent form section styling across all settings pages:

```tsx
{/* Section card pattern */}
<div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
  <div className="px-5 py-3.5 border-b border-border bg-muted/20">
    <h3 className="text-[13px] font-semibold text-foreground">Section Title</h3>
    <p className="text-[12px] text-muted-foreground mt-0.5">Description text</p>
  </div>
  <div className="p-5 space-y-4">
    {/* Form fields */}
  </div>
</div>
```

For the Profile page specifically, update the Avatar section:
```tsx
<Avatar className="h-20 w-20 border-2 border-border">
  <AvatarImage src={formData.avatar_url || undefined} />
  <AvatarFallback className="bg-indigo-600 text-white text-lg font-semibold">
    {getInitials()}
  </AvatarFallback>
</Avatar>
```

---

## 9. Phase 8: Admin Pages

### Admin Overview: `app/app/admin/page.tsx`

Same card pattern as dashboard. Update metric cards and table styling. Search-and-replace all purple references.

### Admin List Pages

Apply the unified table pattern from Phase 6 to all admin list pages:
- `admin/accounts/page.tsx`
- `admin/users/page.tsx`
- `admin/affiliates/page.tsx`
- `admin/property-reports/page.tsx`
- `admin/leads/page.tsx`
- `admin/sms/page.tsx`

---

## 10. Phase 9: Affiliate Pages

### Files:
- `app/app/affiliate/page.tsx` — Affiliate dashboard
- `app/app/affiliate/accounts/[accountId]/page.tsx` — Account detail
- `app/app/affiliate/branding/page.tsx` — Affiliate branding
- `app/app/affiliate/property-reports/page.tsx` — Affiliate reports

### `components/v0-styling/AffiliateDashboardShell.tsx`

Update all hardcoded purple references to indigo. Keep all API calls and state logic identical.

---

## 11. Phase 10: Loading & Error States

### Skeleton Loading Patterns

All loading.tsx files should use consistent skeleton styling:

```tsx
// Pattern for list page loading
export default function Loading() {
  return (
    <div className="space-y-5">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div>
          <div className="h-6 w-40 bg-muted rounded-md animate-pulse" />
          <div className="h-3.5 w-64 bg-muted rounded-md animate-pulse mt-1.5" />
        </div>
        <div className="h-9 w-28 bg-muted rounded-lg animate-pulse" />
      </div>

      {/* Metric cards skeleton */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-card border border-border rounded-xl p-4 shadow-[var(--shadow-card)]">
            <div className="h-3 w-16 bg-muted rounded animate-pulse mb-3" />
            <div className="h-7 w-12 bg-muted rounded animate-pulse" />
          </div>
        ))}
      </div>

      {/* Table skeleton */}
      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-[var(--shadow-card)]">
        <div className="px-4 py-2.5 border-b border-border bg-muted/30">
          <div className="flex gap-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-3 w-20 bg-muted rounded animate-pulse" />
            ))}
          </div>
        </div>
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="px-4 py-3.5 border-b border-border/50 flex gap-4">
            {Array.from({ length: 5 }).map((_, j) => (
              <div key={j} className="h-4 w-24 bg-muted rounded animate-pulse" />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
```

### Error Page: `app/app/error.tsx`

Keep the existing error boundary logic. Update styling to use new tokens.

---

## 12. Phase 11: Polish & Micro-animations

### Button Hover States

The default shadcn button is fine. Just ensure the primary variant uses indigo:
```css
/* This should happen automatically via --primary token change */
```

### Card Hover

Already handled in metric-card via shadow transition. Apply to other interactive cards:
```
hover:shadow-[var(--shadow-elevated)] transition-shadow duration-200
```

### Focus States

Already handled via globals.css `*:focus-visible` rule with indigo ring.

### Transition Timing

The existing global transition in `@media (prefers-reduced-motion: no-preference)` is good. Keep it.

---

## 13. File-by-File Change Map

### Critical Path (do these first, in order):

| # | File | Change Type | Description |
|---|------|-------------|-------------|
| 1 | `app/globals.css` | **Full replace** | New color tokens, dark sidebar tokens |
| 2 | `app/app-layout.tsx` | **Major rewrite** | Dark sidebar, refined topbar, section groups |
| 3 | `components/page-header.tsx` | **Minor update** | Tighter sizing |
| 4 | `components/metric-card.tsx` | **Moderate update** | Remove motion, shadow tokens |
| 5 | `components/status-badge.tsx` | **Minor update** | Color mapping updates |
| 6 | `app/app/page.tsx` | **Moderate update** | Dashboard spacing, verify token usage |

### List Pages (apply unified pattern):

| # | File | Change Type |
|---|------|-------------|
| 7 | `app/app/reports/page.tsx` | Table styling, purple→indigo |
| 8 | `app/app/property/page.tsx` | Table styling, purple→indigo |
| 9 | `app/app/schedules/page.tsx` | Table styling, purple→indigo |
| 10 | `app/app/leads/page.tsx` | Table styling, purple→indigo |
| 11 | `app/app/people/page.tsx` | Table styling, purple→indigo |

### Settings Pages:

| # | File | Change Type |
|---|------|-------------|
| 12 | `app/app/settings/profile/page.tsx` | Form card sections, purple→indigo |
| 13 | `app/app/settings/security/page.tsx` | Form card sections, purple→indigo |
| 14 | `app/app/settings/branding/page.tsx` | Form card sections, purple→indigo |
| 15 | `app/app/settings/billing/page.tsx` | Form card sections, purple→indigo |

### Admin Pages:

| # | File | Change Type |
|---|------|-------------|
| 16 | `app/app/admin/page.tsx` | Cards + tables, purple→indigo |
| 17 | `app/app/admin/accounts/page.tsx` | Table styling |
| 18 | `app/app/admin/users/page.tsx` | Table styling |
| 19 | `app/app/admin/affiliates/page.tsx` | Table styling |
| 20 | `app/app/admin/affiliates/[id]/page.tsx` | Detail page styling |
| 21 | `app/app/admin/property-reports/page.tsx` | Table styling |
| 22 | `app/app/admin/leads/page.tsx` | Table styling |
| 23 | `app/app/admin/sms/page.tsx` | Table styling |

### Affiliate Pages:

| # | File | Change Type |
|---|------|-------------|
| 24 | `app/app/affiliate/page.tsx` | Dashboard styling |
| 25 | `app/app/affiliate/accounts/[accountId]/page.tsx` | Detail styling |
| 26 | `app/app/affiliate/branding/page.tsx` | Form styling |
| 27 | `app/app/affiliate/property-reports/page.tsx` | Table styling |
| 28 | `components/v0-styling/AffiliateDashboardShell.tsx` | purple→indigo |

### Loading States:

| # | File | Change Type |
|---|------|-------------|
| 29 | `app/app/loading.tsx` | Update skeleton pattern |
| 30 | `app/app/reports/loading.tsx` | Update skeleton pattern |
| 31 | `app/app/schedules/loading.tsx` | Update skeleton pattern |
| 32 | `app/app/property/loading.tsx` | Update skeleton pattern |
| 33 | `app/app/settings/loading.tsx` | Update skeleton pattern |
| 34 | `app/app/admin/loading.tsx` | Update skeleton pattern |
| 35 | `app/app/people/loading.tsx` | Update skeleton pattern |
| 36 | `app/app/lead-page/loading.tsx` | Update skeleton pattern |

### Components (search-and-replace purple→indigo):

| # | File | Change Type |
|---|------|-------------|
| 37 | `components/branding-form.tsx` | purple→indigo |
| 38 | `components/branding-preview.tsx` | purple→indigo |
| 39 | `components/checkout-status-banner.tsx` | purple→indigo |
| 40 | `components/onboarding/dashboard-onboarding.tsx` | purple→indigo |
| 41 | `components/onboarding/onboarding-checklist.tsx` | purple→indigo |
| 42 | `components/onboarding/setup-wizard.tsx` | purple→indigo |
| 43 | `components/onboarding/affiliate-onboarding.tsx` | purple→indigo |
| 44 | `components/v0/dashboard-overview.tsx` | purple→indigo |
| 45 | `components/v0-styling/PlanPageShell.tsx` | purple→indigo |
| 46 | `components/v0-styling/SchedulesListShell.tsx` | purple→indigo |
| 47 | `components/stripe-billing-actions.tsx` | purple→indigo |
| 48 | `components/invite-agent-modal.tsx` | purple→indigo |
| 49 | `components/lead-pages/ConsumerLandingWizard.tsx` | purple→indigo |
| 50 | `components/logo.tsx` | Verify works on dark sidebar |

### Wizard Components (lighter touch — these are already good):

| # | File | Change Type |
|---|------|-------------|
| 51 | `components/report-builder/index.tsx` | purple→indigo only |
| 52 | `components/schedule-builder/index.tsx` | purple→indigo only |
| 53 | `components/property/ThemeSelector.tsx` | purple→indigo only |
| 54 | `components/property/ComparablesPicker.tsx` | purple→indigo only |
| 55 | `components/property/PropertySearchForm.tsx` | purple→indigo only |

### Public Pages (lighter touch):

| # | File | Change Type |
|---|------|-------------|
| 56 | `app/page.tsx` (marketing home) | purple→indigo in gradients |
| 57 | `app/login/page.tsx` | purple→indigo |
| 58 | `app/register/page.tsx` | purple→indigo |
| 59 | `app/about/page.tsx` | purple→indigo |
| 60 | `components/navbar.tsx` | purple→indigo |
| 61 | `components/footer.tsx` | purple→indigo |
| 62 | `components/marketing-home.tsx` | purple→indigo |

---

## Global Search-and-Replace Commands

Run these across the ENTIRE `apps/web/` directory:

```bash
# Primary color: purple/violet → indigo
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/bg-purple-50/bg-indigo-50/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/bg-purple-100/bg-indigo-100/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/bg-purple-200/bg-indigo-200/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/bg-purple-600/bg-indigo-600/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/bg-purple-700/bg-indigo-700/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/bg-purple-800/bg-indigo-800/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/text-purple-50/text-indigo-50/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/text-purple-100/text-indigo-100/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/text-purple-200/text-indigo-200/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/text-purple-600/text-indigo-600/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/text-purple-700/text-indigo-700/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/text-purple-800/text-indigo-800/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/border-purple-200/border-indigo-200/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/border-purple-600/border-indigo-600/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/from-purple-600/from-indigo-600/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/from-purple-700/from-indigo-700/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/to-purple-700/to-indigo-700/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/to-purple-800/to-indigo-800/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/hover:from-purple-700/hover:from-indigo-700/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/hover:to-purple-800/hover:to-indigo-800/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/ring-purple-/ring-indigo-/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/focus:ring-purple-/focus:ring-indigo-/g'

# Also replace hex values in JSX/CSS
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/#7c3aed/#4F46E5/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/#a78bfa/#818CF8/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/#f26b2b/#D97706/g'

# Violet variants too
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/bg-violet-/bg-indigo-/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/text-violet-/text-indigo-/g'
find apps/web -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs sed -i 's/border-violet-/border-indigo-/g'
```

**IMPORTANT**: After running sed commands, do a manual review of the diff to catch any edge cases where purple/violet was used intentionally (e.g., in template theme colors for the Property Report ThemeSelector — those should remain as-is since they represent report template colors, not UI colors).

---

## Implementation Sequence for Cursor

Tell Cursor to follow this exact order:

### Batch 1: Foundation (do first, test immediately)
1. Replace `globals.css` tokens
2. Rewrite `app-layout.tsx` (sidebar + topbar)
3. Update `components/page-header.tsx`
4. Update `components/metric-card.tsx`

→ **Test**: App should load with dark sidebar, indigo accents, new topbar

### Batch 2: Global color sweep
5. Run the sed search-and-replace commands
6. Manually review and fix any issues in the git diff

→ **Test**: All purple should be gone, replaced with indigo

### Batch 3: Dashboard + List Pages
7. Polish `app/app/page.tsx` (dashboard)
8. Polish all list pages (reports, property, schedules, leads, people)

→ **Test**: All main pages should look cohesive

### Batch 4: Settings + Admin + Affiliate
9. Polish settings pages
10. Polish admin pages
11. Polish affiliate pages

→ **Test**: Settings and admin sections match main app

### Batch 5: Loading States + Polish
12. Update all loading.tsx files
13. Verify all error states
14. Final visual review

→ **Test**: Full walkthrough of every page

---

*This document is the single source of truth for the UI rebuild. Every change is additive to the visual layer only. No API calls, no state management, no business logic changes.*

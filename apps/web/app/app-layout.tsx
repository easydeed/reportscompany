"use client"

// App shell — App v3. Rail (light, 236px) + content. No topbar: the account
// row lives at the bottom of the rail, the "New report" button at the top.
// Under 1100px the rail becomes a 56px top bar with a menu button that opens
// the same rail in a Sheet.

import { Suspense, useMemo, useState, type ComponentType } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Logo } from "@/components/logo"
import {
  LayoutDashboard, FileText, Calendar, Users, Settings, Building2, Building, Home,
  UserCheck, MessageSquare, Link2, Palette, CreditCard, Plus, CircleHelp, Mail,
  BarChart3, Server, Shield, BookUser, Menu, LogOut, Lock,
} from "lucide-react"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet"
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { AccountSwitcher } from "@/components/account-switcher"
import { usePlanUsage, useMe, useAffiliateOverview, useBranding } from "@/hooks/use-api"
import { Toaster } from "@/components/ui/toaster"
import { Toaster as SonnerToaster } from "@/components/ui/sonner"
import { cn } from "@/lib/utils"

type Icon = ComponentType<{ className?: string }>
/** `also`: other route prefixes this item owns, so the rail stays on it there
 *  (People on the "All agents" overflow, Activity on the schedules feed). */
type NavItem = { name: string; href: string; icon: Icon; exact?: boolean; also?: string[] }
type NavGroup = { label: string; items: NavItem[] }

interface TierProps { isAdmin: boolean; isCompanyAdmin: boolean; isAffiliate: boolean; isSponsored: boolean }

const BUILDER_ROUTES = ["/app/get-started", "/app/property/new", "/app/schedules/new", "/app/reports/new"]
export function isBuilderRoute(pathname: string | null): boolean {
  if (!pathname) return false
  if (BUILDER_ROUTES.includes(pathname)) return true
  return /^\/app\/schedules\/[^/]+\/edit\/?$/.test(pathname)
}

// Design: three groups — Reports / Engage / Account. Settings is ONE page
// (/app/settings) in the design; until profile+security merge, Account links
// to Profile and the Settings page owns the rest. Branding and Plan & billing
// are top-level items, not a collapsible.
export function getNavGroups({ isAdmin, isCompanyAdmin, isAffiliate, isSponsored }: TierProps): NavGroup[] {
  const settings: NavItem = { name: "Settings", href: "/app/settings/profile", icon: Settings }
  if (isAdmin) {
    return [
      { label: "Platform", items: [{ name: "Admin", href: "/app/admin", icon: LayoutDashboard, exact: true }] },
      { label: "Manage", items: [
        { name: "Companies", href: "/app/admin/companies", icon: Building },
        { name: "Title reps", href: "/app/admin/affiliates", icon: Building2 },
        { name: "Accounts", href: "/app/admin/accounts", icon: Home },
        { name: "Users", href: "/app/admin/users", icon: Users },
        { name: "Market reports", href: "/app/admin/reports", icon: FileText },
        { name: "Schedules", href: "/app/admin/schedules", icon: Calendar },
        { name: "Property reports", href: "/app/admin/property-reports", icon: Home },
        { name: "Emails", href: "/app/admin/emails", icon: Mail },
        { name: "SMS", href: "/app/admin/sms", icon: MessageSquare },
        { name: "Lead pages", href: "/app/admin/lead-pages", icon: Link2 },
        { name: "Leads", href: "/app/admin/leads", icon: UserCheck },
        { name: "Analytics", href: "/app/admin/analytics", icon: BarChart3 },
        { name: "Plans", href: "/app/admin/plans", icon: CreditCard },
        { name: "Security", href: "/app/admin/security", icon: Shield },
        { name: "System", href: "/app/admin/system", icon: Server },
        { name: "Billing", href: "/app/admin/billing", icon: CreditCard },
      ] },
      { label: "Account", items: [settings, { name: "Sign in", href: "/app/settings/security", icon: Lock }] },
    ]
  }
  if (isCompanyAdmin) {
    // The rail Jerry approved (2026-10-28): Dashboard · People · Activity ·
    // Branding · Plan & Seats · Settings. Activity and Plan & Seats point at
    // the existing reports and billing pages until their own builds land.
    return [
      { label: "Company", items: [
        { name: "Dashboard", href: "/app/company", icon: Building, exact: true },
        { name: "People", href: "/app/company/reps", icon: Users, also: ["/app/company/agents"] },
        { name: "Activity", href: "/app/company/reports", icon: FileText, also: ["/app/company/schedules"] },
        { name: "Branding", href: "/app/company/branding", icon: Palette },
        { name: "Plan & Seats", href: "/app/settings/billing", icon: CreditCard },
        settings,
      ] },
    ]
  }
  const reports: NavItem[] = [
    { name: "Dashboard", href: "/app", icon: LayoutDashboard, exact: true },
    { name: "Market reports", href: "/app/reports", icon: FileText },
    { name: "Property reports", href: "/app/property", icon: Home },
    { name: "Schedules", href: "/app/schedules", icon: Calendar },
  ]
  if (isAffiliate) {
    return [
      { label: "My book", items: [
        { name: "My agents", href: "/app/affiliate", icon: Users, exact: true },
        { name: "Agent reports", href: "/app/affiliate/reports", icon: FileText },
        { name: "Agent schedules", href: "/app/affiliate/schedules", icon: Calendar },
      ] },
      { label: "My work", items: [...reports, { name: "Contacts", href: "/app/people", icon: BookUser }] },
      { label: "Account", items: [
        { name: "Branding", href: "/app/settings/branding", icon: Palette },
        { name: "Plan & billing", href: "/app/settings/billing", icon: CreditCard },
        settings,
      ] },
    ]
  }
  return [
    { label: "Reports", items: reports },
    { label: "Engage", items: [
      { name: "Home-value page", href: "/app/lead-page", icon: Link2 },
      { name: "Contacts", href: "/app/people", icon: Users },
    ] },
    { label: "Account", items: [
      ...(isSponsored ? [] : [{ name: "Branding", href: "/app/settings/branding", icon: Palette } as NavItem]),
      { name: "Plan & billing", href: "/app/settings/billing", icon: CreditCard },
      settings,
    ] },
  ]
}

export function isActivePath(pathname: string | null, item: NavItem) {
  if (!pathname) return false
  if (item.exact) return pathname === item.href
  if (item.also?.some((p) => pathname === p || pathname.startsWith(p + "/"))) return true
  // /app/settings/profile owns the whole settings tree except billing/branding
  if (item.href === "/app/settings/profile") return pathname.startsWith("/app/settings") && !pathname.startsWith("/app/settings/billing") && !pathname.startsWith("/app/settings/branding")
  return pathname === item.href || pathname.startsWith(item.href + "/")
}

function RailLink({ item, active, onNavigate }: { item: NavItem; active: boolean; onNavigate?: () => void }) {
  return (
    <Link
      href={item.href}
      prefetch={false}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
      className={cn(
        "flex h-[38px] items-center gap-[11px] rounded-lg px-[10px] text-[14px] transition-colors hover:bg-[var(--muted-hover)] hover:text-foreground",
        active ? "bg-[var(--muted)] font-bold text-foreground" : "font-medium text-[var(--body)]",
      )}
    >
      <item.icon className="size-[17px] shrink-0" />
      <span className="truncate">{item.name}</span>
    </Link>
  )
}

function UsageRow({ label, used, limit, brand }: { label: string; used: number; limit: number; brand: string }) {
  const unlimited = limit >= 999
  const ratio = unlimited ? 0 : used / Math.max(limit, 1)
  const fill = ratio >= 1 ? "var(--destructive)" : ratio >= 0.8 ? "var(--warning)" : brand
  return (
    <div className="flex flex-col gap-[5px]">
      <div className="flex justify-between text-[12px] text-muted-foreground">
        <span>{label}</span>
        <span className="font-semibold tabular-nums text-foreground">{unlimited ? `${used} · unlimited` : `${used} / ${limit}`}</span>
      </div>
      {/* Design: an unlimited plan shows no bar at all. */}
      {!unlimited && (
        <div className="h-1 overflow-hidden rounded-sm bg-[var(--border)]">
          <div className="h-full rounded-sm transition-[width] duration-500" style={{ width: `${Math.min(ratio * 100, 100)}%`, background: fill }} />
        </div>
      )}
    </div>
  )
}

function Rail({ tier, onNavigate }: { tier: TierProps; onNavigate?: () => void }) {
  const pathname = usePathname()
  const { data: planUsage } = usePlanUsage()
  const { data: user } = useMe()
  const { data: branding } = useBranding()
  const { data: affiliateData } = useAffiliateOverview({ enabled: tier.isAffiliate })
  const affiliateMetrics = (affiliateData as any)?.metrics as { total_agents: number; total_agent_reports: number; active_agents: number; active_agents_total: number } | undefined

  const groups = useMemo(() => getNavGroups(tier), [tier.isAdmin, tier.isCompanyAdmin, tier.isAffiliate, tier.isSponsored])
  const homeHref = tier.isAdmin ? "/app/admin" : tier.isCompanyAdmin ? "/app/company" : tier.isAffiliate ? "/app/affiliate" : "/app"
  const showNewReport = !tier.isAdmin && !tier.isCompanyAdmin
  const showUsage = !tier.isAdmin && !tier.isCompanyAdmin && !tier.isAffiliate && !!planUsage
  const brand = (branding as any)?.primary_color ?? "var(--agent-primary)"

  const displayName = user?.first_name && user?.last_name ? `${user.first_name} ${user.last_name}` : user?.first_name || user?.email?.split("@")[0] || "Account"
  const initials = displayName.split(" ").map((n: string) => n[0]).join("").slice(0, 2).toUpperCase() || "U"
  const roleLabel = tier.isAdmin ? "Platform admin" : tier.isCompanyAdmin ? "Company admin" : tier.isAffiliate ? "Title rep" : tier.isSponsored ? "Trial agent" : "Agent"
  const planName = planUsage?.plan?.plan_name
  const helpActive = pathname?.startsWith("/app/help") ?? false

  async function handleLogout() {
    try { await fetch("/api/proxy/v1/auth/logout", { method: "POST", credentials: "include" }) } catch {}
    window.location.href = "/login"
  }

  return (
    <div data-sidebar className="flex h-full flex-col gap-[22px] overflow-y-auto bg-[var(--sidebar)] px-[14px] pb-[18px] pt-[22px]">
      <Link href={homeHref} prefetch={false} onClick={onNavigate} className="ml-[10px] self-start">
        <Logo className="h-[26px]" />
      </Link>

      {showNewReport && (
        <Link
          href="/app/reports/new"
          prefetch={false}
          onClick={onNavigate}
          className="flex h-[42px] items-center justify-center gap-2 rounded-[9px] bg-primary text-[14px] font-semibold text-primary-foreground transition-colors hover:bg-[var(--primary-hover)] hover:text-primary-foreground"
        >
          <Plus className="size-[15px]" />
          New report
        </Link>
      )}

      <nav className="flex flex-col gap-5">
        {groups.map((g) => (
          <div key={g.label} className="flex flex-col gap-[2px]">
            <span className="px-[10px] pb-2 text-[11px] font-bold uppercase tracking-[0.1em] text-muted-foreground">{g.label}</span>
            {g.items.map((it) => (
              <RailLink key={it.href} item={it} active={isActivePath(pathname, it)} onNavigate={onNavigate} />
            ))}
          </div>
        ))}
      </nav>

      <div className="mt-auto flex flex-col gap-[14px]">
        <RailLink item={{ name: "Help", href: "/app/help", icon: CircleHelp }} active={helpActive} onNavigate={onNavigate} />

        {tier.isAffiliate && affiliateMetrics && (
          <div className="flex flex-col gap-[10px] border-t border-[var(--border)] px-[10px] pt-[14px]">
            <span className="text-[13px] font-bold">My agents</span>
            {[["Agents", String(affiliateMetrics.total_agents)], ["Reports this month", String(affiliateMetrics.total_agent_reports)], ["Active · 30d", `${affiliateMetrics.active_agents} / ${affiliateMetrics.active_agents_total}`]].map(([l, v]) => (
              <div key={l} className="flex justify-between text-[12px] text-muted-foreground"><span>{l}</span><span className="font-semibold tabular-nums text-foreground">{v}</span></div>
            ))}
          </div>
        )}

        {showUsage && planUsage && (
          <div className="flex flex-col gap-[10px] border-t border-[var(--border)] px-[10px] pt-[14px]">
            <div className="flex items-baseline justify-between">
              <span className="text-[13px] font-bold">{planName ? `${planName} plan` : "Your plan"}</span>
              {(planName ?? "").toLowerCase() === "free" && (
                <Link href="/app/settings/billing" prefetch={false} onClick={onNavigate} className="text-[12px] font-semibold text-[var(--link)] hover:text-[var(--link-hover)]">Upgrade</Link>
              )}
            </div>
            <UsageRow label="Market reports" used={planUsage.usage.market_reports_used} limit={planUsage.plan.market_reports_limit} brand={brand} />
            <UsageRow label="Schedules" used={planUsage.usage.schedules_active} limit={planUsage.plan.schedules_limit} brand={brand} />
            <UsageRow label="Property reports" used={planUsage.usage.property_reports_used} limit={planUsage.plan.property_reports_limit} brand={brand} />
          </div>
        )}

        <div className="flex flex-col gap-2 border-t border-[var(--border)] pt-2">
          <AccountSwitcher />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="flex w-full items-center gap-[10px] rounded-lg px-[10px] py-1 text-left transition-colors hover:bg-[var(--muted-hover)]">
                {/* The initials circle is the one sanctioned brand-on-chrome use: the circle IS the agent. */}
                <span className="flex size-8 shrink-0 items-center justify-center rounded-full text-[12px] font-bold text-white" style={{ background: brand }}>{initials}</span>
                <span className="flex min-w-0 flex-col leading-[1.25]">
                  <span className="truncate text-[13px] font-semibold">{displayName}</span>
                  <span className="text-[12px] text-muted-foreground">{roleLabel}</span>
                </span>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" side="top" className="w-56">
              <DropdownMenuLabel>
                <p className="text-sm font-semibold">{displayName}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild><Link href="/app/settings/profile" prefetch={false}>Settings</Link></DropdownMenuItem>
              <DropdownMenuItem onClick={handleLogout} className="cursor-pointer"><LogOut className="mr-2 size-3.5" />Log out</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </div>
  )
}

export default function AppLayoutClient({
  children, isAdmin, isCompanyAdmin = false, isAffiliate = false, isSponsored = false,
}: { children: React.ReactNode; isAdmin: boolean; isCompanyAdmin?: boolean; isAffiliate?: boolean; isSponsored?: boolean; accountType?: string }) {
  const pathname = usePathname()
  const inBuilderMode = useMemo(() => isBuilderRoute(pathname), [pathname])
  const [open, setOpen] = useState(false)
  const tier: TierProps = { isAdmin, isCompanyAdmin, isAffiliate, isSponsored }

  if (inBuilderMode) {
    return (
      <>
        <div className="min-h-screen w-full bg-background text-foreground">{children}</div>
        <Toaster /><SonnerToaster position="top-right" />
      </>
    )
  }

  return (
    <>
      <Suspense fallback={<div className="flex h-screen items-center justify-center text-muted-foreground">Loading…</div>}>
        <div className="flex min-h-screen w-full bg-background text-foreground">
          {/* ≥1100px: sticky rail */}
          <aside className="sticky top-0 hidden h-screen w-[236px] shrink-0 border-r border-[var(--border-subtle)] min-[1100px]:block">
            <Rail tier={tier} />
          </aside>

          <div className="flex min-w-0 flex-1 flex-col">
            {/* <1100px: top bar + sheet */}
            <header className="flex h-14 items-center gap-3 border-b border-[var(--border-subtle)] bg-[var(--sidebar)] px-4 min-[1100px]:hidden">
              <button aria-label="Menu" onClick={() => setOpen(true)} className="flex size-9 items-center justify-center rounded-lg hover:bg-[var(--muted)]"><Menu className="size-5" /></button>
              <Logo className="h-[26px]" />
              {!isAdmin && !isCompanyAdmin && (
                <Link href="/app/reports/new" prefetch={false} className="ml-auto flex h-9 items-center gap-1.5 rounded-[9px] bg-primary px-3 text-[13px] font-semibold text-primary-foreground hover:text-primary-foreground"><Plus className="size-4" />New</Link>
              )}
            </header>
            <Sheet open={open} onOpenChange={setOpen}>
              <SheetContent side="left" className="w-[236px] max-w-[236px] border-r border-[var(--border-subtle)] p-0 [&>button]:hidden">
                <SheetHeader className="sr-only"><SheetTitle>Navigation</SheetTitle><SheetDescription>App navigation</SheetDescription></SheetHeader>
                <Rail tier={tier} onNavigate={() => setOpen(false)} />
              </SheetContent>
            </Sheet>

            <main className="flex-1">
              <div className="mx-auto w-full max-w-[1120px] px-6 pb-20 pt-7 md:px-12 md:pt-11">{children}</div>
            </main>
          </div>
        </div>
      </Suspense>
      <Toaster /><SonnerToaster position="top-right" />
    </>
  )
}

"use client"

import { Suspense, useMemo } from "react"
import { QueryProvider } from "@/components/providers/query-provider"
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
  SidebarGroup,
  SidebarGroupLabel,
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
  Plus,
  HelpCircle,
  Mail,
  BarChart3,
  Server,
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
import { AccountSwitcher } from "@/components/account-switcher"

import { Separator } from "@/components/ui/separator"
import { usePlanUsage, useMe, useAffiliateOverview } from "@/hooks/use-api"
import { Toaster } from "@/components/ui/toaster"
import { Toaster as SonnerToaster } from "@/components/ui/sonner"

type NavItem = { name: string; href: string; icon: React.ComponentType<{ className?: string }> }

interface TierProps {
  isAdmin: boolean
  isCompanyAdmin: boolean
  isAffiliate: boolean
  isSponsored: boolean
}

// Routes where sidebar should be hidden (builder modes)
const BUILDER_ROUTES = [
  "/app/property/new",
  "/app/schedules/new",
  "/app/schedules/", // Will check for /edit suffix
]

function isBuilderRoute(pathname: string | null): boolean {
  if (!pathname) return false
  if (BUILDER_ROUTES.includes(pathname)) return true
  if (pathname.startsWith("/app/schedules/") && pathname.endsWith("/edit")) return true
  return false
}

function getNavigation({ isAdmin, isCompanyAdmin, isAffiliate, isSponsored }: TierProps) {
  // TIER 1 — Platform Admin: sees admin tools + own profile
  if (isAdmin) {
    return {
      main: [
        { name: "Admin Dashboard", href: "/app/admin", icon: LayoutDashboard },
      ] as NavItem[],
      admin: [
        { name: "Companies", href: "/app/admin/companies", icon: Building },
        { name: "Title Reps", href: "/app/admin/affiliates", icon: Building2 },
        { name: "Accounts", href: "/app/admin/accounts", icon: Home },
        { name: "Users", href: "/app/admin/users", icon: Users },
        { name: "Market Reports", href: "/app/admin/reports", icon: FileText },
        { name: "Schedules", href: "/app/admin/schedules", icon: Calendar },
        { name: "Property Reports", href: "/app/admin/property-reports", icon: Home },
        { name: "Emails", href: "/app/admin/emails", icon: Mail },
        { name: "SMS", href: "/app/admin/sms", icon: MessageSquare },
        { name: "Lead Pages", href: "/app/admin/lead-pages", icon: Link2 },
        { name: "Leads", href: "/app/admin/leads", icon: UserCheck },
        { name: "Analytics", href: "/app/admin/analytics", icon: BarChart3 },
        { name: "Plans", href: "/app/admin/plans", icon: CreditCard },
        { name: "Security", href: "/app/admin/security", icon: Shield },
        { name: "System", href: "/app/admin/system", icon: Server },
        { name: "Billing", href: "/app/admin/billing", icon: CreditCard },
      ] as NavItem[],
      settings: [
        { name: "Profile", href: "/app/settings/profile", icon: User },
        { name: "Security", href: "/app/settings/security", icon: Lock },
      ] as NavItem[],
    }
  }

  // TIER 2 — Company Admin: company overview, reps, agents, branding
  if (isCompanyAdmin) {
    return {
      main: [
        { name: "Company Dashboard", href: "/app/company", icon: Building },
        { name: "Title Reps", href: "/app/company/reps", icon: Users },
        { name: "All Agents", href: "/app/company/agents", icon: UserCheck },
      ] as NavItem[],
      settings: [
        { name: "Profile", href: "/app/settings/profile", icon: User },
        { name: "Security", href: "/app/settings/security", icon: Lock },
        { name: "Company Branding", href: "/app/company/branding", icon: Palette },
        { name: "Billing", href: "/app/settings/billing", icon: CreditCard },
      ] as NavItem[],
    }
  }

  // TIER 3 — Title Rep (Affiliate): agents + tools, no billing
  if (isAffiliate) {
    return {
      main: [
        { name: "My Agents", href: "/app/affiliate", icon: Users },
        { name: "Market Reports", href: "/app/reports", icon: FileText },
        { name: "Property Reports", href: "/app/property", icon: Home },
        { name: "Schedules", href: "/app/schedules", icon: Calendar },
      ] as NavItem[],
      engage: [
        { name: "Lead Pages", href: "/app/lead-page", icon: Link2 },
        { name: "Contacts", href: "/app/people", icon: Users },
      ] as NavItem[],
      settings: [
        { name: "Profile", href: "/app/settings/profile", icon: User },
        { name: "Security", href: "/app/settings/security", icon: Lock },
        { name: "Branding", href: "/app/settings/branding", icon: Palette },
      ] as NavItem[],
    }
  }

  // TIER 4 — Trial Agent (sponsored): full tools + own branding + billing
  if (isSponsored) {
    return {
      main: [
        { name: "Dashboard", href: "/app", icon: LayoutDashboard },
        { name: "Market Reports", href: "/app/reports", icon: FileText },
        { name: "Property Reports", href: "/app/property", icon: Home },
        { name: "Schedules", href: "/app/schedules", icon: Calendar },
      ] as NavItem[],
      engage: [
        { name: "Lead Pages", href: "/app/lead-page", icon: Link2 },
        { name: "Contacts", href: "/app/people", icon: Users },
      ] as NavItem[],
      settings: [
        { name: "Profile", href: "/app/settings/profile", icon: User },
        { name: "Security", href: "/app/settings/security", icon: Lock },
        { name: "Branding", href: "/app/settings/branding", icon: Palette },
        { name: "Billing", href: "/app/settings/billing", icon: CreditCard },
      ] as NavItem[],
    }
  }

  // TIER 5 — Regular Agent: full self-service
  return {
    main: [
      { name: "Dashboard", href: "/app", icon: LayoutDashboard },
      { name: "Market Reports", href: "/app/reports", icon: FileText },
      { name: "Property Reports", href: "/app/property", icon: Home },
      { name: "Schedules", href: "/app/schedules", icon: Calendar },
    ] as NavItem[],
    engage: [
      { name: "Lead Pages", href: "/app/lead-page", icon: Link2 },
      { name: "Contacts", href: "/app/people", icon: Users },
    ] as NavItem[],
    settings: [
      { name: "Profile", href: "/app/settings/profile", icon: User },
      { name: "Security", href: "/app/settings/security", icon: Lock },
      { name: "Branding", href: "/app/settings/branding", icon: Palette },
      { name: "Billing", href: "/app/settings/billing", icon: CreditCard },
    ] as NavItem[],
  }
}

function UsageBar({ label, used, limit }: { label: string; used: number; limit: number }) {
  const isUnlimited = limit >= 99999
  const pct = isUnlimited ? 0 : Math.min((used / Math.max(limit, 1)) * 100, 100)
  const color = pct >= 100 ? 'bg-red-500' : pct >= 80 ? 'bg-amber-500' : 'bg-indigo-400'

  return (
    <div className="space-y-0.5">
      <div className="flex justify-between text-[11px]">
        <span className="text-sidebar-foreground/60">{label}</span>
        <span className="font-medium text-sidebar-foreground/80">{isUnlimited ? '∞' : `${used}/${limit}`}</span>
      </div>
      {!isUnlimited && (
        <div className="h-1 bg-sidebar-border rounded-full overflow-hidden">
          <div className={`h-full ${color} rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
        </div>
      )}
    </div>
  )
}

function DashboardSidebar({ isAdmin, isCompanyAdmin, isAffiliate, isSponsored }: TierProps) {
  const pathname = usePathname()
  const { data: planUsage } = usePlanUsage()
  const { data: affiliateData } = useAffiliateOverview({ enabled: isAffiliate })
  const affiliateMetrics = (affiliateData as any)?.metrics as
    | { total_agents: number; total_agent_reports: number; active_agents: number; active_agents_total: number; agents_at_limit: number }
    | undefined

  const nav = useMemo(() => getNavigation({ isAdmin, isCompanyAdmin, isAffiliate, isSponsored }), [isAdmin, isCompanyAdmin, isAffiliate, isSponsored])

  const isInAdminSection = pathname?.startsWith("/app/admin")
  const isInSettingsSection = pathname?.startsWith("/app/settings")

  const homeHref = isAdmin ? "/app/admin" : isCompanyAdmin ? "/app/company" : isAffiliate ? "/app/affiliate" : "/app"
  const exactHomeHrefs = ["/app", "/app/affiliate", "/app/admin", "/app/company"]

  return (
    <Sidebar>
      <SidebarHeader>
        <Link href={homeHref} prefetch={false} className="flex items-center px-3 py-4">
          <img src="/indigo.png" alt="TrendyReports" className="h-7 w-auto" />
        </Link>
      </SidebarHeader>

      <SidebarContent>
        {/* Quick Action — hide for admin / company admin users */}
        {!isAdmin && !isCompanyAdmin && (
          <div className="px-3 mb-2">
            <Button size="sm" className="w-full bg-indigo-500 hover:bg-indigo-400 text-white shadow-sm" asChild>
              <Link href="/app/reports/new" prefetch={false}>
                <Plus className="w-3.5 h-3.5 mr-1.5" />
                New Report
              </Link>
            </Button>
          </div>
        )}

        {/* Main Navigation */}
        <SidebarGroup>
          <SidebarGroupLabel className="text-[10px] uppercase tracking-[0.08em] font-semibold text-sidebar-muted px-3">
            {isAdmin ? "Platform" : "Reports"}
          </SidebarGroupLabel>
          <SidebarMenu>
            {nav.main.map((item) => {
              const isActive = pathname === item.href || (!exactHomeHrefs.includes(item.href) && pathname?.startsWith(item.href))
              return (
                <SidebarMenuItem key={item.name}>
                  <SidebarMenuButton asChild isActive={isActive}>
                    <Link href={item.href}>
                      <item.icon className="w-4 h-4" />
                      <span className="text-[13px]">{item.name}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              )
            })}
          </SidebarMenu>
        </SidebarGroup>

        {/* Admin Section (Tier 1 only) */}
        {'admin' in nav && (nav as any).admin && (
          <SidebarGroup>
            <SidebarGroupLabel className="text-[10px] uppercase tracking-[0.08em] font-semibold text-sidebar-muted px-3">
              Manage
            </SidebarGroupLabel>
            <SidebarMenu>
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
                      {(nav as any).admin.map((item: NavItem) => (
                        <SidebarMenuSubItem key={item.name}>
                          <SidebarMenuSubButton asChild isActive={pathname === item.href}>
                            <Link href={item.href} prefetch={false}>
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
            </SidebarMenu>
          </SidebarGroup>
        )}

        {/* Engage Section (non-admin tiers) */}
        {'engage' in nav && (nav as any).engage && (
          <SidebarGroup>
            <SidebarGroupLabel className="text-[10px] uppercase tracking-[0.08em] font-semibold text-sidebar-muted px-3">
              Engage
            </SidebarGroupLabel>
            <SidebarMenu>
              {(nav as any).engage.map((item: NavItem) => {
                const isActive = pathname === item.href || pathname?.startsWith(item.href)
                return (
                  <SidebarMenuItem key={item.name}>
                    <SidebarMenuButton asChild isActive={isActive}>
                      <Link href={item.href}>
                        <item.icon className="w-4 h-4" />
                        <span className="text-[13px]">{item.name}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroup>
        )}

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
                    {nav.settings.map((item) => (
                      <SidebarMenuSubItem key={item.name}>
                        <SidebarMenuSubButton asChild isActive={pathname === item.href}>
                          <Link href={item.href} prefetch={false}>
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
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild isActive={pathname?.startsWith("/app/help")}>
              <Link href="/app/help">
                <HelpCircle className="w-4 h-4" />
                <span className="text-[13px]">Help Center</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>

        {/* Affiliate sidebar: agent-focused metrics */}
        {isAffiliate && affiliateMetrics && (
          <div className="px-3 py-3">
            <div className="rounded-lg border border-sidebar-border bg-sidebar-accent/50 p-3 space-y-1.5">
              <div className="text-[10px] font-semibold uppercase tracking-wider text-sidebar-foreground/50">
                My Agents
              </div>
              <div className="flex justify-between text-[11px]">
                <span className="text-sidebar-foreground/60">Agents</span>
                <span className="font-medium text-sidebar-foreground/80">{affiliateMetrics.total_agents}</span>
              </div>
              <div className="flex justify-between text-[11px]">
                <span className="text-sidebar-foreground/60">Reports (this month)</span>
                <span className="font-medium text-sidebar-foreground/80">{affiliateMetrics.total_agent_reports}</span>
              </div>
              <div className="flex justify-between text-[11px]">
                <span className="text-sidebar-foreground/60">Active (30d)</span>
                <span className="font-medium text-sidebar-foreground/80">{affiliateMetrics.active_agents}/{affiliateMetrics.active_agents_total}</span>
              </div>
              {affiliateMetrics.agents_at_limit > 0 && (
                <div className="text-[11px] text-amber-600 font-medium mt-1">
                  {affiliateMetrics.agents_at_limit} agent{affiliateMetrics.agents_at_limit > 1 ? 's' : ''} at limit
                </div>
              )}
            </div>
          </div>
        )}

        {/* Agent / sponsored agent sidebar: per-product usage bars */}
        {!isAdmin && !isCompanyAdmin && !isAffiliate && planUsage && (
          <div className="px-3 py-3">
            <div className="rounded-lg border border-sidebar-border bg-sidebar-accent/50 p-3 space-y-2">
              <div className="text-[10px] font-semibold uppercase tracking-wider text-sidebar-foreground/50">
                {planUsage.plan.plan_name} Plan
              </div>
              <UsageBar
                label="Market Reports"
                used={planUsage.usage.market_reports_used}
                limit={planUsage.plan.market_reports_limit}
              />
              <UsageBar
                label="Schedules"
                used={planUsage.usage.schedules_active}
                limit={planUsage.plan.schedules_limit}
              />
              <UsageBar
                label="Property Reports"
                used={planUsage.usage.property_reports_used}
                limit={planUsage.plan.property_reports_limit}
              />
            </div>
          </div>
        )}
      </SidebarFooter>
    </Sidebar>
  )
}

function DashboardTopbar({ accountType, isAdmin, isCompanyAdmin, isAffiliate, isSponsored }: { accountType?: string } & TierProps) {
  const { data: user } = useMe()

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
  const initials = displayName.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase() || "U"
  
  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-border bg-white px-4">
      <SidebarTrigger className="text-muted-foreground hover:text-foreground" />
      
      <Separator orientation="vertical" className="h-5" />
      
      <div className="flex-1" />

      {/* Account Type Badge */}
      {isAdmin && (
        <span className="rounded-full bg-red-50 text-red-700 text-[11px] font-semibold px-2.5 py-0.5 border border-red-200 flex items-center gap-1.5 uppercase tracking-wide">
          <Shield className="h-3 w-3" />
          Admin
        </span>
      )}
      {!isAdmin && isCompanyAdmin && (
        <span className="rounded-full bg-purple-50 text-purple-700 text-[11px] font-semibold px-2.5 py-0.5 border border-purple-200 flex items-center gap-1.5 uppercase tracking-wide">
          <Building2 className="h-3 w-3" />
          Company Admin
        </span>
      )}
      {!isAdmin && !isCompanyAdmin && accountType === "INDUSTRY_AFFILIATE" && (
        <span className="rounded-full bg-amber-50 text-amber-700 text-[11px] font-semibold px-2.5 py-0.5 border border-amber-200 flex items-center gap-1.5 uppercase tracking-wide">
          <Building2 className="h-3 w-3" />
          Title Rep
        </span>
      )}
      {!isAdmin && accountType === "REGULAR" && isSponsored && (
        <span className="rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-semibold px-2.5 py-0.5 border border-emerald-200 uppercase tracking-wide">
          Trial Agent
        </span>
      )}
      {!isAdmin && accountType === "REGULAR" && !isSponsored && (
        <span className="rounded-full bg-indigo-50 text-indigo-600 text-[11px] font-semibold px-2.5 py-0.5 uppercase tracking-wide">
          Agent
        </span>
      )}

      <AccountSwitcher />

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="relative h-8 w-8 rounded-full focus-visible:ring-0 focus-visible:ring-offset-0">
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
            <Link href="/app/settings/profile" prefetch={false}>
              <User className="w-3.5 h-3.5 mr-2" />Profile
            </Link>
          </DropdownMenuItem>
          {!isSponsored && !isAdmin && (
            <DropdownMenuItem asChild>
              <Link href={isCompanyAdmin ? "/app/company/branding" : "/app/settings/branding"} prefetch={false}>
                <Palette className="w-3.5 h-3.5 mr-2" />Branding
              </Link>
            </DropdownMenuItem>
          )}
          {!isAffiliate && !isAdmin && (
            <DropdownMenuItem asChild>
              <Link href="/app/settings/billing" prefetch={false}>
                <CreditCard className="w-3.5 h-3.5 mr-2" />Billing
              </Link>
            </DropdownMenuItem>
          )}
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-red-600 focus:text-red-600">
            Log out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  )
}

export default function AppLayoutClient({
  children,
  isAdmin,
  isCompanyAdmin = false,
  isAffiliate = false,
  isSponsored = false,
  accountType,
}: {
  children: React.ReactNode
  isAdmin: boolean
  isCompanyAdmin?: boolean
  isAffiliate?: boolean
  isSponsored?: boolean
  accountType?: string
}) {
  const pathname = usePathname()
  const inBuilderMode = useMemo(() => isBuilderRoute(pathname), [pathname])
  
  // Builder mode: Full-width layout without sidebar
  if (inBuilderMode) {
    return (
      <>
        <div className="min-h-screen w-full bg-background text-foreground">
          {children}
        </div>
        <Toaster />
        <SonnerToaster position="top-right" />
      </>
    )
  }
  
  // Normal mode: With sidebar
  return (
    <QueryProvider>
      <SidebarProvider>
        <Suspense fallback={<div className="flex items-center justify-center h-screen">Loading...</div>}>
          <div className="flex min-h-screen w-full bg-background text-foreground">
            <DashboardSidebar isAdmin={isAdmin} isCompanyAdmin={isCompanyAdmin} isAffiliate={isAffiliate} isSponsored={isSponsored} />
            <SidebarInset className="flex flex-col">
              <DashboardTopbar accountType={accountType} isAdmin={isAdmin} isCompanyAdmin={isCompanyAdmin} isAffiliate={isAffiliate} isSponsored={isSponsored} />
              <main className="flex-1 px-6 py-5 bg-background">{children}</main>
            </SidebarInset>
          </div>
        </Suspense>
      </SidebarProvider>
      <Toaster />
      <SonnerToaster position="top-right" />
    </QueryProvider>
  )
}

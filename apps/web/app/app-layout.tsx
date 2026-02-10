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
import { Logo } from "@/components/logo"
import { Separator } from "@/components/ui/separator"
import { usePlanUsage, useMe } from "@/hooks/use-api"

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

function DashboardSidebar({ isAdmin, isAffiliate }: { isAdmin: boolean; isAffiliate: boolean }) {
  const pathname = usePathname()
  const { data: planUsage } = usePlanUsage()

  const planInfo = useMemo(() => {
    if (!planUsage?.plan) return null
    return {
      plan_name: planUsage.plan.plan_name || "Free",
      reports_used: planUsage.info?.reports_this_period || 0,
      reports_limit: planUsage.plan.monthly_reports_limit || 10,
    }
  }, [planUsage])

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
        <Link href="/app" prefetch={false} className="flex items-center px-3 py-4">
          <Logo className="h-7 brightness-0 invert" />
        </Link>
      </SidebarHeader>

      <SidebarContent>
        {/* Quick Action */}
        <div className="px-3 mb-2">
          <Button size="sm" className="w-full bg-indigo-500 hover:bg-indigo-400 text-white shadow-sm" asChild>
            <Link href="/app/reports/new" prefetch={false}>
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
                    <Link href={item.href} prefetch={false}>
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
                    <Link href={item.href} prefetch={false}>
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

function DashboardTopbar({ accountType, isAdmin, isAffiliate }: { accountType?: string; isAdmin: boolean; isAffiliate: boolean }) {
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
            <Link href="/app/settings/profile" prefetch={false}>
              <User className="w-3.5 h-3.5 mr-2" />Profile
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href="/app/settings/branding" prefetch={false}>
              <Palette className="w-3.5 h-3.5 mr-2" />Branding
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href="/app/settings/billing" prefetch={false}>
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

export default function AppLayoutClient({
  children,
  isAdmin,
  isAffiliate = false,
  accountType,
}: {
  children: React.ReactNode
  isAdmin: boolean
  isAffiliate?: boolean
  accountType?: string
}) {
  const pathname = usePathname()
  const inBuilderMode = useMemo(() => isBuilderRoute(pathname), [pathname])
  
  // Builder mode: Full-width layout without sidebar
  if (inBuilderMode) {
    return (
      <div className="min-h-screen w-full bg-background text-foreground">
        {children}
      </div>
    )
  }
  
  // Normal mode: With sidebar
  return (
    <QueryProvider>
      <SidebarProvider>
        <Suspense fallback={<div className="flex items-center justify-center h-screen">Loading...</div>}>
          <div className="flex min-h-screen w-full bg-background text-foreground">
            <DashboardSidebar isAdmin={isAdmin} isAffiliate={isAffiliate} />
            <SidebarInset className="flex flex-col">
              <DashboardTopbar accountType={accountType} isAdmin={isAdmin} isAffiliate={isAffiliate} />
              <main className="flex-1 px-6 py-5 bg-background">{children}</main>
            </SidebarInset>
          </div>
        </Suspense>
      </SidebarProvider>
    </QueryProvider>
  )
}

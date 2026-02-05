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
import NavAuth from "@/components/NavAuth"
import { AccountSwitcher } from "@/components/account-switcher"
import { Logo } from "@/components/logo"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { SidebarGroup, SidebarGroupLabel } from "@/components/ui/sidebar"

// Routes where sidebar should be hidden (builder modes)
const BUILDER_ROUTES = [
  "/app/reports/new",
  "/app/schedules/new",
  "/app/schedules/", // Will check for /edit suffix
]

function isBuilderRoute(pathname: string | null): boolean {
  if (!pathname) return false
  
  // Check direct matches
  if (BUILDER_ROUTES.includes(pathname)) return true
  
  // Check for schedule edit routes: /app/schedules/[id]/edit
  if (pathname.startsWith("/app/schedules/") && pathname.endsWith("/edit")) return true
  
  return false
}

function DashboardSidebar({ isAdmin, isAffiliate }: { isAdmin: boolean; isAffiliate: boolean }) {
  const pathname = usePathname()
  const [planInfo, setPlanInfo] = useState<{ plan_name: string; reports_used: number; reports_limit: number } | null>(null)
  
  // Fetch plan usage
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
  
  // Check if we're in admin or settings section
  const isInAdminSection = pathname?.startsWith("/app/admin")
  const isInSettingsSection = pathname?.startsWith("/app/settings")
  
  // Build navigation based on user role (without Settings - it's now a collapsible section)
  const navigation = isAffiliate
    ? [
        // Affiliate navigation
        { name: "Affiliate Dashboard", href: "/app/affiliate", icon: LayoutDashboard },
        { name: "Market Reports", href: "/app/reports", icon: FileText },
        { name: "Property Reports", href: "/app/property", icon: Home },
        { name: "Scheduled Reports", href: "/app/schedules", icon: Calendar },
        { name: "My Leads", href: "/app/lead-page", icon: Link2 },
        { name: "My Contacts", href: "/app/people", icon: Users },
      ]
    : [
        // Agent navigation
        { name: "Dashboard", href: "/app", icon: LayoutDashboard },
        { name: "Market Reports", href: "/app/reports", icon: FileText },
        { name: "Property Reports", href: "/app/property", icon: Home },
        { name: "Scheduled Reports", href: "/app/schedules", icon: Calendar },
        { name: "My Leads", href: "/app/lead-page", icon: Link2 },
        { name: "My Contacts", href: "/app/people", icon: Users },
      ]
  
  // Settings sub-navigation
  const settingsNavigation = [
    { name: "Profile", href: "/app/settings/profile", icon: User },
    { name: "Security", href: "/app/settings/security", icon: Lock },
    { name: "Branding", href: "/app/settings/branding", icon: Palette },
    { name: "Billing", href: "/app/settings/billing", icon: CreditCard },
  ]
  
  // Admin sub-navigation
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
                  <Link href={item.href} prefetch={true}>
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
                  {settingsNavigation.map((item) => {
                    const isSubActive = pathname === item.href
                    return (
                      <SidebarMenuSubItem key={item.name}>
                        <SidebarMenuSubButton asChild isActive={isSubActive}>
                          <Link href={item.href} prefetch={true}>
                            <item.icon className="w-4 h-4" />
                            <span>{item.name}</span>
                          </Link>
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                    )
                  })}
                </SidebarMenuSub>
              </CollapsibleContent>
            </SidebarMenuItem>
          </Collapsible>

          {/* Admin Section with Collapsible Sub-menu */}
          {isAdmin && (
            <Collapsible defaultOpen={isInAdminSection} className="group/collapsible-admin">
              <SidebarMenuItem>
                <CollapsibleTrigger asChild>
                  <SidebarMenuButton isActive={isInAdminSection}>
                    <Shield className="w-4 h-4" />
                    <span>Admin</span>
                    <ChevronRight className="ml-auto h-4 w-4 transition-transform group-data-[state=open]/collapsible-admin:rotate-90" />
                  </SidebarMenuButton>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <SidebarMenuSub>
                    {adminNavigation.map((item) => {
                      const isSubActive = pathname === item.href
                      return (
                        <SidebarMenuSubItem key={item.name}>
                          <SidebarMenuSubButton asChild isActive={isSubActive}>
                            <Link href={item.href} prefetch={true}>
                              <item.icon className="w-4 h-4" />
                              <span>{item.name}</span>
                            </Link>
                          </SidebarMenuSubButton>
                        </SidebarMenuSubItem>
                      )
                    })}
                  </SidebarMenuSub>
                </CollapsibleContent>
              </SidebarMenuItem>
            </Collapsible>
          )}
        </SidebarMenu>
      </SidebarContent>
      <SidebarFooter>
        <div className="px-3 py-3">
          <div className="bg-muted rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="secondary" className="text-xs">
                {planInfo?.plan_name || "Free"} Plan
              </Badge>
              <span className="text-xs text-muted-foreground">
                {planInfo?.reports_used || 0}/{planInfo?.reports_limit || 10} reports
              </span>
            </div>
            <Progress 
              value={planInfo ? (planInfo.reports_used / planInfo.reports_limit) * 100 : 0} 
              className="h-1.5 mb-3" 
            />
            <Button size="sm" className="w-full" asChild>
              <Link href="/app/reports/new">
                <Plus className="w-3.5 h-3.5 mr-1.5" />
                New Report
              </Link>
            </Button>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}

function DashboardTopbar({ accountType, isAdmin, isAffiliate }: { accountType?: string; isAdmin: boolean; isAffiliate: boolean }) {
  const [user, setUser] = useState<{ email: string; first_name?: string; last_name?: string } | null>(null)
  
  useEffect(() => {
    // Fetch actual user info for the dropdown
    fetch("/api/proxy/v1/users/me", { credentials: "include" })
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data) setUser(data)
      })
      .catch(() => {})
  }, [])
  
  async function handleLogout() {
    try {
      await fetch("/api/proxy/v1/auth/logout", { 
        method: "POST",
        credentials: "include"
      })
    } catch {}
    window.location.href = "/login"
  }
  
  const displayName = user?.first_name && user?.last_name 
    ? `${user.first_name} ${user.last_name}`
    : user?.first_name || user?.email?.split('@')[0] || "User"
  
  const displayEmail = user?.email || ""
  const initials = displayName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() || "U"
  
  return (
    <header className="flex h-12 shrink-0 items-center gap-4 border-b border-border bg-card px-4">
      <SidebarTrigger />
      <div className="flex-1" />

      {/* Account Type Badge */}
      {accountType === "INDUSTRY_AFFILIATE" && (
        <span className="rounded-full bg-purple-50 text-purple-700 text-xs font-medium px-3 py-1 border border-purple-200 flex items-center gap-1.5">
          <Shield className="h-3 w-3" />
          Affiliate Account
        </span>
      )}
      {accountType === "REGULAR" && (
        <span className="rounded-full bg-slate-50 text-slate-600 text-xs font-medium px-3 py-1 border border-slate-200">
          Agent Account
        </span>
      )}

      <AccountSwitcher />
      <NavAuth />

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="relative h-9 w-9 rounded-full">
            <Avatar className="h-9 w-9">
              <AvatarFallback className="bg-primary text-primary-foreground">{initials}</AvatarFallback>
            </Avatar>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel>
            <div className="flex flex-col space-y-1">
              <p className="text-sm font-medium">{displayName}</p>
              <p className="text-xs text-muted-foreground">{displayEmail}</p>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem asChild>
            <Link href="/app/settings/profile">Profile</Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href="/app/settings/branding">Branding</Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href="/app/settings/billing">Billing</Link>
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
    <SidebarProvider>
      <Suspense fallback={<div>Loading...</div>}>
        <div className="flex min-h-screen w-full bg-background text-foreground">
          <DashboardSidebar isAdmin={isAdmin} isAffiliate={isAffiliate} />
          <SidebarInset className="flex flex-col">
            <DashboardTopbar accountType={accountType} isAdmin={isAdmin} isAffiliate={isAffiliate} />
            <main className="flex-1 p-6 bg-background">{children}</main>
          </SidebarInset>
        </div>
      </Suspense>
    </SidebarProvider>
  )
}

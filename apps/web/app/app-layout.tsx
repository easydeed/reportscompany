"use client"

import { Suspense, useState, useEffect } from "react"
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
  Palette,
  ChevronDown,
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

function DashboardSidebar({ isAdmin, isAffiliate }: { isAdmin: boolean; isAffiliate: boolean }) {
  const pathname = usePathname()
  
  // Check if we're in admin section
  const isInAdminSection = pathname?.startsWith("/app/admin")
  
  // Build navigation based on user role
  const navigation = isAffiliate
    ? [
        // Affiliate navigation
        { name: "Affiliate Dashboard", href: "/app/affiliate", icon: LayoutDashboard },
        { name: "Market Reports", href: "/app/reports", icon: FileText },
        { name: "Property Reports", href: "/app/property", icon: Home },
        { name: "Lead Page", href: "/app/lead-page", icon: Link2 },
        { name: "Leads", href: "/app/leads", icon: UserCheck },
        { name: "Scheduled Reports", href: "/app/schedules", icon: Calendar },
        { name: "Agents & Contacts", href: "/app/people", icon: Users },
        { name: "Affiliate Branding", href: "/app/branding", icon: Palette },
        { name: "Settings", href: "/app/account/settings", icon: Settings },
      ]
    : [
        // Agent navigation
        { name: "Dashboard", href: "/app", icon: LayoutDashboard },
        { name: "Market Reports", href: "/app/reports", icon: FileText },
        { name: "Property Reports", href: "/app/property", icon: Home },
        { name: "Lead Page", href: "/app/lead-page", icon: Link2 },
        { name: "Leads", href: "/app/leads", icon: UserCheck },
        { name: "Scheduled Reports", href: "/app/schedules", icon: Calendar },
        { name: "Contacts", href: "/app/people", icon: Users },
        { name: "Branding", href: "/app/branding", icon: Palette },
        { name: "Settings", href: "/app/account/settings", icon: Settings },
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
                  <Link href={item.href}>
                    <item.icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            )
          })}
          
          {/* Admin Section with Collapsible Sub-menu */}
          {isAdmin && (
            <Collapsible defaultOpen={isInAdminSection} className="group/collapsible">
              <SidebarMenuItem>
                <CollapsibleTrigger asChild>
                  <SidebarMenuButton isActive={isInAdminSection}>
                    <Shield className="w-4 h-4" />
                    <span>Admin</span>
                    <ChevronRight className="ml-auto h-4 w-4 transition-transform group-data-[state=open]/collapsible:rotate-90" />
                  </SidebarMenuButton>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <SidebarMenuSub>
                    {adminNavigation.map((item) => {
                      const isSubActive = pathname === item.href
                      return (
                        <SidebarMenuSubItem key={item.name}>
                          <SidebarMenuSubButton asChild isActive={isSubActive}>
                            <Link href={item.href}>
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
    <header className="flex h-12 shrink-0 items-center gap-4 border-b border-[var(--app-border)] bg-[var(--app-surface)] px-4">
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
            <Link href="/app/account/settings">Account Settings</Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href="/app/account/plan">Plan & Usage</Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href="/app/branding">Branding</Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href="/app/billing">Billing</Link>
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

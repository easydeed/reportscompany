"use client"

import { Suspense } from "react"
import {
  SidebarProvider,
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarFooter,
  SidebarInset,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import {
  LayoutDashboard,
  FileText,
  Palette,
  CreditCard,
  Search,
  ChevronDown,
  Shield,
  Calendar,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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

const baseNavigation = [
  { name: "Overview", href: "/app", icon: LayoutDashboard },
  { name: "Reports", href: "/app/reports", icon: FileText },
  { name: "Schedules", href: "/app/schedules", icon: Calendar },
  { name: "Branding", href: "/app/branding", icon: Palette },
  { name: "Billing", href: "/app/billing", icon: CreditCard },
]

function DashboardSidebar({ isAdmin, isAffiliate }: { isAdmin: boolean; isAffiliate: boolean }) {
  const pathname = usePathname()
  
  // Build navigation based on user role
  let navigation = [...baseNavigation]
  
  // Add Affiliate Dashboard for affiliate accounts
  if (isAffiliate) {
    navigation.push({ name: "Affiliate Dashboard", href: "/app/affiliate", icon: Shield })
    navigation.push({ name: "Affiliate Branding", href: "/app/affiliate/branding", icon: Palette })
  }
  
  // Add Admin link if user is admin
  if (isAdmin) {
    navigation.push({ name: "Admin", href: "/app/admin", icon: Shield })
  }

  return (
    <Sidebar>
      <SidebarHeader>
        <div className="flex items-center gap-2 px-2 py-4">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
            <FileText className="w-5 h-5 text-primary-foreground" />
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-sm">Market Reports</span>
            <span className="text-xs text-muted-foreground">Real Estate SaaS</span>
          </div>
        </div>
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
  return (
    <header className="flex h-12 shrink-0 items-center gap-4 border-b border-[var(--app-border)] bg-[var(--app-surface)] px-4">
      <SidebarTrigger />
      <div className="flex items-center gap-4 flex-1">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--app-muted)]" />
          <Input placeholder="Search reports..." className="pl-9 bg-slate-50 border-[var(--app-border)]" />
        </div>
      </div>

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
      
      {/* Build marker - for deployment verification */}
      <span className="text-[10px] text-slate-400">
        build: {process.env.NEXT_PUBLIC_BUILD_TAG || "local-dev"}
      </span>
      
      {/* Debug: show affiliate detection */}
      <span className="text-[10px] text-slate-400">
        role: {isAdmin ? "ADMIN" : "USER"} | affiliate: {isAffiliate ? "yes" : "no"} | type: {accountType || "unknown"}
      </span>

      <AccountSwitcher />
      <NavAuth />

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="relative h-9 w-9 rounded-full">
            <Avatar className="h-9 w-9">
              <AvatarFallback className="bg-primary text-primary-foreground">U</AvatarFallback>
            </Avatar>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel>
            <div className="flex flex-col space-y-1">
              <p className="text-sm font-medium">Demo User</p>
              <p className="text-xs text-muted-foreground">demo@example.com</p>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
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
          <DropdownMenuItem>Log out</DropdownMenuItem>
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

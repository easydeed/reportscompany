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

function DashboardTopbar() {
  return (
    <header className="flex h-16 shrink-0 items-center gap-4 border-b border-border bg-background px-6">
      <SidebarTrigger />
      <div className="flex items-center gap-4 flex-1">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input placeholder="Search reports..." className="pl-9 bg-muted/50" />
        </div>
      </div>

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
}: {
  children: React.ReactNode
  isAdmin: boolean
  isAffiliate?: boolean
}) {
  return (
    <div className="dark">
      <SidebarProvider>
        <Suspense fallback={<div>Loading...</div>}>
          <div className="flex min-h-screen w-full bg-background text-foreground">
            <DashboardSidebar isAdmin={isAdmin} isAffiliate={isAffiliate} />
            <SidebarInset className="flex flex-col">
              <DashboardTopbar />
              <main className="flex-1 p-6">{children}</main>
            </SidebarInset>
          </div>
        </Suspense>
      </SidebarProvider>
    </div>
  )
}

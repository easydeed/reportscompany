"use client"

import type React from "react"

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
  Calendar,
  Palette,
  Key,
  Webhook,
  CreditCard,
  Settings,
  Search,
  ChevronDown,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
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

const navigation = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "Reports", href: "/dashboard/reports", icon: FileText },
  { name: "Schedules", href: "/dashboard/schedules", icon: Calendar },
  { name: "Branding", href: "/dashboard/branding", icon: Palette },
  { name: "API Keys", href: "/dashboard/api-keys", icon: Key },
  { name: "Webhooks", href: "/dashboard/webhooks", icon: Webhook },
  { name: "Billing", href: "/dashboard/billing", icon: CreditCard },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
]

export function DashboardSidebar() {
  const pathname = usePathname()

  return (
    <Sidebar>
      <SidebarHeader>
        <div className="flex items-center gap-2 px-2 py-4">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
            <FileText className="w-5 h-5 text-primary-foreground" />
          </div>
          <div className="flex flex-col">
            <span className="font-display font-bold text-sm">RealtyInsight</span>
            <span className="text-xs text-muted-foreground">Market Reports</span>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarMenu>
          {navigation.map((item) => {
            const isActive = pathname === item.href
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
            <p className="text-xs text-muted-foreground mb-2">142 of 200 reports used</p>
            <div className="w-full bg-muted rounded-full h-1.5">
              <div className="bg-primary h-1.5 rounded-full" style={{ width: "71%" }} />
            </div>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}

export function DashboardTopbar() {
  return (
    <header className="flex h-16 shrink-0 items-center gap-4 border-b border-border bg-background px-6">
      <SidebarTrigger />
      <div className="flex items-center gap-4 flex-1">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="gap-2 bg-transparent">
              <span className="font-semibold">Acme Realty</span>
              <ChevronDown className="w-4 h-4 text-muted-foreground" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-64">
            <DropdownMenuLabel>Organizations</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center">
                  <span className="text-xs font-semibold text-primary">AR</span>
                </div>
                <div>
                  <p className="text-sm font-medium">Acme Realty</p>
                  <p className="text-xs text-muted-foreground">Current</p>
                </div>
              </div>
            </DropdownMenuItem>
            <DropdownMenuItem>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded bg-accent/10 flex items-center justify-center">
                  <span className="text-xs font-semibold text-accent">PT</span>
                </div>
                <div>
                  <p className="text-sm font-medium">Pacific Title Co.</p>
                  <p className="text-xs text-muted-foreground">Switch</p>
                </div>
              </div>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>Create new organization</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input placeholder="Search reports, locations..." className="pl-9 bg-muted/50" />
        </div>
      </div>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="relative h-9 w-9 rounded-full">
            <Avatar className="h-9 w-9">
              <AvatarImage src="/placeholder.svg?height=36&width=36" alt="User" />
              <AvatarFallback className="bg-primary text-primary-foreground">JD</AvatarFallback>
            </Avatar>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel>
            <div className="flex flex-col space-y-1">
              <p className="text-sm font-medium">John Doe</p>
              <p className="text-xs text-muted-foreground">john@acmerealty.com</p>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem>Profile</DropdownMenuItem>
          <DropdownMenuItem>Team</DropdownMenuItem>
          <DropdownMenuItem>Billing</DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem>Log out</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  )
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <Suspense fallback={<div>Loading...</div>}>
        <div className="flex min-h-screen w-full">
          <DashboardSidebar />
          <SidebarInset className="flex flex-col">
            <DashboardTopbar />
            <main className="flex-1 p-6">{children}</main>
          </SidebarInset>
        </div>
      </Suspense>
    </SidebarProvider>
  )
}

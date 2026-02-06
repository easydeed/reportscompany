import { redirect } from "next/navigation"
import Link from "next/link"
import Image from "next/image"
import {
  LayoutDashboard,
  Users,
  Building2,
  Building,
  CreditCard,
  FileText,
  Mail,
  Settings,
  LogOut,
  Calendar,
  Activity,
  Home,
  TrendingUp,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { createServerApi } from "@/lib/api-server"
import { AdminLogoutButton } from "./logout-button"

async function verifyAdmin(): Promise<{ admin: any; redirectTo: string | null }> {
  const api = await createServerApi()
  
  if (!api.isAuthenticated()) {
    return { admin: null, redirectTo: '/admin/login' }
  }

  const { data, error } = await api.get<any>('/v1/me')
  
  if (error || !data) {
    console.error('Admin verify failed:', error)
    return { admin: null, redirectTo: '/admin/login' }
  }

  // Check if user is a platform admin (NOT tenant role)
  // Platform admin is determined by users.is_platform_admin = TRUE
  if (!data.is_platform_admin) {
    console.log(`User ${data.email} is not a platform admin`)
    return { admin: null, redirectTo: '/access-denied' }
  }
  
  return { admin: data, redirectTo: null }
}

const navItems = [
  { href: "/admin", icon: LayoutDashboard, label: "Dashboard", exact: true },
  { href: "/admin/accounts", icon: Building, label: "Accounts" },
  { href: "/admin/users", icon: Users, label: "Users" },
  { href: "/admin/affiliates", icon: Building2, label: "Title Companies" },
  { href: "/admin/schedules", icon: Calendar, label: "Schedules" },
  { href: "/admin/property-reports", icon: Home, label: "Property Reports" },
  { href: "/admin/lead-pages", icon: TrendingUp, label: "Lead Pages" },
  { href: "/admin/plans", icon: CreditCard, label: "Plans & Pricing" },
  { href: "/admin/reports", icon: FileText, label: "Market Reports" },
  { href: "/admin/emails", icon: Mail, label: "Email Logs" },
  { href: "/admin/settings", icon: Settings, label: "Settings" },
]

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { admin, redirectTo } = await verifyAdmin()

  if (redirectTo) {
    redirect(redirectTo)
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col shadow-sm">
        {/* Logo/Brand */}
        <div className="p-6 border-b border-slate-200">
          <Link href="/admin" className="flex items-center gap-3">
            <Image
              src="/logo.svg"
              alt="TrendyReports"
              width={140}
              height={40}
              className="h-8 w-auto"
              priority
            />
          </Link>
          <p className="text-xs text-slate-500 mt-1 ml-1">Admin Console</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              )}
            >
              <item.icon className="w-5 h-5" />
              {item.label}
            </Link>
          ))}
        </nav>

        {/* User/Logout */}
        <div className="p-4 border-t border-slate-200">
          <div className="flex items-center gap-3 px-3 py-2 mb-2">
            <div className="w-8 h-8 bg-indigo-100 text-indigo-700 rounded-full flex items-center justify-center text-sm font-medium">
              {admin.first_name?.[0] || admin.email?.[0]?.toUpperCase() || 'A'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 truncate">
                {admin.first_name ? `${admin.first_name} ${admin.last_name || ''}` : 'Admin'}
              </p>
              <p className="text-xs text-slate-500 truncate">{admin.email}</p>
            </div>
          </div>
          <AdminLogoutButton />
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  )
}

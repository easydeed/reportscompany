import { redirect } from "next/navigation"
import Link from "next/link"
import {
  LayoutDashboard,
  Users,
  Building2,
  Building,
  CreditCard,
  FileText,
  Mail,
  Settings,
  Shield,
  ChevronRight,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { createServerApi } from "@/lib/api-server"

async function verifyAdmin() {
  const api = await createServerApi()
  
  if (!api.isAuthenticated()) {
    return null
  }

  const { data, error } = await api.get<any>('/v1/me')
  
  if (error || !data) {
    console.error('Admin verify failed:', error)
    return null
  }

  // Check if user has admin role
  if (data.role !== 'admin' && data.role !== 'ADMIN') {
    console.log(`User ${data.email} does not have ADMIN role, has: ${data.role}`)
    return null
  }
  
  return data
}

const navItems = [
  { href: "/admin", icon: LayoutDashboard, label: "Dashboard", exact: true },
  { href: "/admin/accounts", icon: Building, label: "Accounts" },
  { href: "/admin/users", icon: Users, label: "Users" },
  { href: "/admin/affiliates", icon: Building2, label: "Title Companies" },
  { href: "/admin/plans", icon: CreditCard, label: "Plans & Pricing" },
  { href: "/admin/reports", icon: FileText, label: "Reports" },
  { href: "/admin/emails", icon: Mail, label: "Email Logs" },
  { href: "/admin/settings", icon: Settings, label: "Settings" },
]

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const admin = await verifyAdmin()

  if (!admin) {
    redirect('/access-denied')
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col shadow-sm">
        {/* Logo/Brand */}
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg text-slate-900">TrendyReports</h1>
              <p className="text-xs text-slate-500">Admin Console</p>
            </div>
          </div>
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
            <div className="w-8 h-8 bg-violet-100 text-violet-700 rounded-full flex items-center justify-center text-sm font-medium">
              {admin.first_name?.[0] || admin.email?.[0]?.toUpperCase() || 'A'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 truncate">
                {admin.first_name ? `${admin.first_name} ${admin.last_name || ''}` : 'Admin'}
              </p>
              <p className="text-xs text-slate-500 truncate">{admin.email}</p>
            </div>
          </div>
          <Link href="/app">
            <Button variant="ghost" size="sm" className="w-full justify-start text-slate-600 hover:text-slate-900 hover:bg-slate-100">
              <ChevronRight className="w-4 h-4 mr-2 rotate-180" />
              Back to App
            </Button>
          </Link>
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

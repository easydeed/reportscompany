"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { User, Shield, Palette, CreditCard } from "lucide-react"

const settingsNav = [
  { name: "Profile", href: "/app/settings/profile", icon: User },
  { name: "Security", href: "/app/settings/security", icon: Shield },
  { name: "Branding", href: "/app/settings/branding", icon: Palette },
  { name: "Billing", href: "/app/settings/billing", icon: CreditCard },
]

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your account, branding, and subscription
        </p>
      </div>

      {/* Grid: Submenu + Content */}
      <div className="grid grid-cols-[200px,1fr] gap-8">
        {/* Sticky Submenu */}
        <nav className="sticky top-24 h-fit space-y-1">
          {settingsNav.map((item) => {
            const isActive = pathname === item.href || pathname?.startsWith(item.href + "/")
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                  isActive
                    ? "bg-violet-50 text-violet-700 dark:bg-violet-950/50 dark:text-violet-300"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800/50 dark:hover:text-gray-200"
                )}
              >
                <item.icon className="w-4 h-4" />
                {item.name}
              </Link>
            )
          })}
        </nav>

        {/* Content Area */}
        <main className="min-w-0">{children}</main>
      </div>
    </div>
  )
}


"use client"

import { Button } from "@/components/ui/button"
import { LogOut } from "lucide-react"

export function AdminLogoutButton() {
  async function handleLogout() {
    await fetch("/api/proxy/v1/auth/logout", { method: "POST", credentials: "include" })
    window.location.href = "/admin/login"
  }

  return (
    <Button 
      variant="ghost" 
      size="sm" 
      onClick={handleLogout}
      className="w-full justify-start text-slate-600 hover:text-red-600 hover:bg-red-50"
    >
      <LogOut className="w-4 h-4 mr-2" />
      Log Out
    </Button>
  )
}

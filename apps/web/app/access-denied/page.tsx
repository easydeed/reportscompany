"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Shield, LogIn, LogOut } from "lucide-react"

export default function AccessDeniedPage() {
  async function handleLoginAsAdmin() {
    // Clear the auth cookie by calling logout
    await fetch("/api/proxy/v1/auth/logout", { method: "POST", credentials: "include" })
    // Redirect to admin login page
    window.location.href = "/admin/login"
  }

  async function handleLogout() {
    // Clear the auth cookie by calling logout
    await fetch("/api/proxy/v1/auth/logout", { method: "POST", credentials: "include" })
    // Redirect to home
    window.location.href = "/"
  }

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-slate-800 border-slate-700">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mb-4">
            <Shield className="w-8 h-8 text-red-400" />
          </div>
          <CardTitle className="text-2xl text-white">Access Denied</CardTitle>
          <CardDescription className="text-slate-400">
            You don't have permission to access the Admin Console.
            <br />
            Please log in with an administrator account.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button
            onClick={handleLoginAsAdmin}
            className="w-full bg-violet-600 hover:bg-violet-700"
          >
            <LogIn className="w-4 h-4 mr-2" />
            Log in as Admin
          </Button>
          <Button
            onClick={handleLogout}
            variant="outline"
            className="w-full border-slate-600 text-slate-300 hover:bg-slate-700 hover:text-white"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Log Out
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

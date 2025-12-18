"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Shield, LogIn, ArrowLeft } from "lucide-react"

export default function AccessDeniedPage() {
  async function handleLogout() {
    // Clear the auth cookie by calling logout
    await fetch("/api/proxy/v1/auth/logout", { method: "POST", credentials: "include" })
    // Redirect to login with admin redirect
    window.location.href = "/login?next=/admin"
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-gray-900 border-gray-800">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mb-4">
            <Shield className="w-8 h-8 text-red-400" />
          </div>
          <CardTitle className="text-2xl text-white">Access Denied</CardTitle>
          <CardDescription className="text-gray-400">
            You don't have permission to access the Admin Console.
            <br />
            Please log in with an administrator account.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            onClick={handleLogout}
            className="w-full bg-violet-600 hover:bg-violet-700"
          >
            <LogIn className="w-4 h-4 mr-2" />
            Log in as Admin
          </Button>
          <Link href="/app">
            <Button variant="outline" className="w-full border-gray-700 text-gray-300 hover:bg-gray-800">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to App
            </Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  )
}

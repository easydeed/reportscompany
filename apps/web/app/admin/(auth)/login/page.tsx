"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, AlertCircle, Eye, EyeOff } from "lucide-react"
import { Logo } from "@/components/logo"

export default function AdminLoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const res = await fetch("/api/proxy/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        credentials: "include",
      })

      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || "Invalid credentials")
        setLoading(false)
        return
      }

      // Check if user is platform admin
      const meRes = await fetch("/api/proxy/v1/me", {
        credentials: "include",
      })

      if (meRes.ok) {
        const meData = await meRes.json()
        if (!meData.is_platform_admin) {
          setError("This account does not have admin access")
          // Logout since they're not admin
          await fetch("/api/proxy/v1/auth/logout", { method: "POST", credentials: "include" })
          setLoading(false)
          return
        }
      }

      // Success - redirect to admin dashboard
      router.push("/admin")
      router.refresh()
    } catch (err) {
      setError("An error occurred. Please try again.")
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-white border-slate-200 shadow-xl relative z-10">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto mb-4 flex justify-center">
            <Logo className="h-10" />
          </div>
          <CardTitle className="text-2xl font-bold text-slate-900">Admin Console</CardTitle>
          <CardDescription className="text-slate-500">
            Sign in to access the admin dashboard
          </CardDescription>
        </CardHeader>
        
        <CardContent className="pt-4">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200 text-red-600 text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="email" className="text-slate-700">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@example.com"
                required
                disabled={loading}
                className="bg-white border-slate-300 text-slate-900 placeholder:text-slate-400 focus:border-violet-500 focus:ring-violet-500/20"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password" className="text-slate-700">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  disabled={loading}
                  className="bg-white border-slate-300 text-slate-900 placeholder:text-slate-400 focus:border-violet-500 focus:ring-violet-500/20 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            
            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white font-medium py-2.5 shadow-lg shadow-violet-500/25 transition-all"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign In"
              )}
            </Button>
          </form>
          
          <div className="mt-6 pt-4 border-t border-slate-200">
            <p className="text-center text-sm text-slate-500">
              Only authorized administrators can access this console
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

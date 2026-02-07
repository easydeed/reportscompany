"use client"

import * as React from "react"
import { useState, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { Eye, EyeOff, ArrowRight, BarChart3, Mail, Shield, AlertCircle } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"

function LoginForm() {
  const searchParams = useSearchParams()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    const startTime = performance.now()
    console.log("[LOGIN] Starting login...")

    try {
      console.log("[LOGIN] Calling /api/proxy/v1/auth/login...")
      const fetchStart = performance.now()
      const res = await fetch("/api/proxy/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        credentials: "include",
      })
      console.log(
        `[LOGIN] API response received in ${(performance.now() - fetchStart).toFixed(0)}ms, status: ${res.status}`
      )

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setError(data?.detail || data?.message || "Invalid email or password")
        setLoading(false)
        return
      }

      // Parse the token from the response body
      const data = await res.json().catch(() => ({}))

      if (data.access_token) {
        const secure = window.location.protocol === "https:" ? "; Secure" : ""
        document.cookie = `mr_token=${data.access_token}; path=/; max-age=3600; SameSite=Lax${secure}`
        console.log("[LOGIN] Cookie set from JavaScript")
      } else {
        console.warn("[LOGIN] No access_token in response body:", Object.keys(data))
      }

      console.log(
        `[LOGIN] Success! Total login time: ${(performance.now() - startTime).toFixed(0)}ms`
      )

      // Use full page navigation to guarantee the cookie is sent
      window.location.href = "/app"
    } catch (err: unknown) {
      console.error("Login failed", err)
      setError("Something went wrong. Please try again.")
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen">
      {/* Left — Form panel */}
      <div className="flex flex-1 flex-col justify-center px-6 py-12 lg:px-16 xl:px-24">
        <div className="mx-auto w-full max-w-md">
          {/* Logo */}
          <Link href="/" className="text-2xl font-bold text-[#6366F1]">
            TrendyReports
          </Link>

          <h1 className="mt-10 text-3xl font-bold tracking-tight text-foreground">
            Welcome back
          </h1>
          <p className="mt-2 text-muted-foreground">
            Sign in to your account to continue creating beautiful market reports.
          </p>

          {/* Error Display */}
          {error && (
            <div className="mt-6 rounded-lg bg-red-50 border border-red-200 p-3 flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-900">Login failed</p>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          )}

          {/* Divider */}
          <div className="relative mt-8">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="bg-background px-4 text-muted-foreground">
                Sign in with email
              </span>
            </div>
          </div>

          {/* Form */}
          <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="email">Email address</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@company.com"
                className="h-12 rounded-lg"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <Link
                  href="/forgot-password"
                  className="text-sm font-medium text-[#6366F1] hover:text-[#4F46E5]"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  className="h-12 rounded-lg pr-12"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Checkbox id="remember" disabled={loading} />
              <Label htmlFor="remember" className="text-sm font-normal text-muted-foreground">
                Keep me signed in
              </Label>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#6366F1] px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#4F46E5] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Signing in..." : "Sign in"}
              {!loading && <ArrowRight className="h-4 w-4" />}
            </button>
          </form>

          <p className="mt-8 text-center text-sm text-muted-foreground">
            {"Don't have an account? "}
            <Link
              href="/register"
              className="font-semibold text-[#6366F1] hover:text-[#4F46E5]"
            >
              Start your free trial
            </Link>
          </p>
        </div>
      </div>

      {/* Right — Branded visual panel */}
      <div className="hidden flex-1 flex-col justify-between bg-[#1E293B] p-12 lg:flex xl:p-16">
        <div>
          <p className="text-sm font-medium uppercase tracking-widest text-[#818CF8]">
            Trusted by 2,000+ agents
          </p>
          <h2 className="mt-6 text-balance text-4xl font-bold leading-tight text-white">
            Market reports that
            <br />
            close deals faster.
          </h2>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-6">
          <div className="rounded-xl bg-white/5 p-5 backdrop-blur">
            <BarChart3 className="h-6 w-6 text-[#818CF8]" />
            <p className="mt-3 text-2xl font-bold text-white">8</p>
            <p className="mt-1 text-sm text-[#94A3B8]">Report types</p>
          </div>
          <div className="rounded-xl bg-white/5 p-5 backdrop-blur">
            <Mail className="h-6 w-6 text-[#818CF8]" />
            <p className="mt-3 text-2xl font-bold text-white">50K+</p>
            <p className="mt-1 text-sm text-[#94A3B8]">Emails sent monthly</p>
          </div>
          <div className="rounded-xl bg-white/5 p-5 backdrop-blur">
            <Shield className="h-6 w-6 text-[#818CF8]" />
            <p className="mt-3 text-2xl font-bold text-white">99.9%</p>
            <p className="mt-1 text-sm text-[#94A3B8]">Uptime SLA</p>
          </div>
        </div>

        {/* Testimonial */}
        <div>
          <blockquote className="rounded-xl bg-white/5 p-6 backdrop-blur">
            <p className="leading-relaxed text-[#E2E8F0]">
              {
                '"TrendyReports transformed how I communicate with clients. The automated market reports save me 5+ hours every week and my clients love them."'
              }
            </p>
            <footer className="mt-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#6366F1] text-sm font-bold text-white">
                SJ
              </div>
              <div>
                <p className="text-sm font-semibold text-white">Sarah Johnson</p>
                <p className="text-sm text-[#94A3B8]">Top Producer, Compass Austin</p>
              </div>
            </footer>
          </blockquote>
        </div>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-muted-foreground">Loading...</div>
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  )
}

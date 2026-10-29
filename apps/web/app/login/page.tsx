"use client"

// /login — App v3. Behaviour unchanged from the previous page (same endpoint,
// same cookie write, same full-page redirect). What changed:
// - AuthFrame replaces the two-panel layout (see components/auth/auth-frame.tsx).
// - "Keep me signed in" removed: the checkbox was never read, so it promised a
//   behaviour the app doesn't have. Restore when the API takes a remember flag.
// - console.log timing lines dropped.

import * as React from "react"
import { useState } from "react"
import Link from "next/link"
import { Eye, EyeOff } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AuthFrame, AuthError, AuthSubmit, authLabel, authInput, authLink } from "@/components/auth/auth-frame"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await fetch("/api/proxy/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        credentials: "include",
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setError(data?.detail || data?.message || "That email and password don't match.")
        setLoading(false)
        return
      }
      const data = await res.json().catch(() => ({}))
      if (data.access_token) {
        const secure = window.location.protocol === "https:" ? "; Secure" : ""
        document.cookie = `mr_token=${data.access_token}; path=/; max-age=3600; SameSite=Lax${secure}`
      }
      window.location.href = "/app"
    } catch {
      setError("Something went wrong. Please try again.")
      setLoading(false)
    }
  }

  return (
    <AuthFrame
      title="Welcome back"
      footer={<>Don&apos;t have an account? <Link href="/register" className={authLink}>Create one free</Link></>}
    >
      <form className="flex flex-col gap-5" onSubmit={handleSubmit} noValidate={false}>
        {error && <AuthError>{error}</AuthError>}

        <div className="flex flex-col gap-2">
          <Label htmlFor="email" className={authLabel}>Email</Label>
          <Input id="email" type="email" autoComplete="email" placeholder="you@example.com" className={authInput}
            value={email} onChange={(e) => setEmail(e.target.value)} required disabled={loading} autoFocus />
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex items-baseline justify-between">
            <Label htmlFor="password" className={authLabel}>Password</Label>
            <Link href="/forgot-password" className="text-[13px] font-medium text-[var(--link)] hover:text-[var(--link-hover)]">Forgot password?</Link>
          </div>
          <div className="relative">
            <Input id="password" type={showPassword ? "text" : "password"} autoComplete="current-password" className={`${authInput} pr-12`}
              value={password} onChange={(e) => setPassword(e.target.value)} required disabled={loading} />
            <button type="button" onClick={() => setShowPassword((v) => !v)} aria-label={showPassword ? "Hide password" : "Show password"}
              className="absolute right-3 top-1/2 flex size-8 -translate-y-1/2 items-center justify-center rounded-lg text-[var(--placeholder)] hover:bg-[var(--muted)] hover:text-foreground">
              {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </button>
          </div>
        </div>

        <AuthSubmit loading={loading} busy="Signing in…">Sign in</AuthSubmit>
      </form>
    </AuthFrame>
  )
}

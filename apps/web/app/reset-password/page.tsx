"use client"

// /reset-password — App v3. Same endpoint and payload
// ({ token, new_password }), same redirect to /app on success.
// AuthFrame replaces the slate card.

import * as React from "react"
import { useState, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import { Eye, EyeOff } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AuthFrame, AuthError, AuthSubmit, authLabel, authInput, authLink, authSubmitClass } from "@/components/auth/auth-frame"

function ResetPasswordForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get("token")

  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const back = <Link href="/login" className={authLink}>Back to sign in</Link>

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (password.length < 8) {
      setError("Password must be at least 8 characters long.")
      return
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.")
      return
    }
    setLoading(true)
    try {
      const res = await fetch("/api/proxy/v1/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ token, new_password: password }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setError(data?.detail || "Failed to reset password. Please try again.")
        setLoading(false)
        return
      }
      setSuccess(true)
      setTimeout(() => {
        router.push("/app")
      }, 2000)
    } catch {
      setError("Something went wrong. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <AuthFrame
        title="Invalid reset link"
        description="This password reset link is invalid or has expired."
        footer={back}
      >
        <Link href="/forgot-password" className={authSubmitClass}>Request a new link</Link>
      </AuthFrame>
    )
  }

  if (success) {
    return (
      <AuthFrame
        title="Password updated"
        description="Your password has been updated. Redirecting you to the dashboard…"
        footer={<Link href="/app" className={authLink}>Go to dashboard</Link>}
      >
        {null}
      </AuthFrame>
    )
  }

  return (
    <AuthFrame
      title="Set a new password"
      description="Enter your new password below."
      footer={back}
    >
      <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
        {error && <AuthError>{error}</AuthError>}

        <div className="flex flex-col gap-2">
          <Label htmlFor="password" className={authLabel}>New password</Label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              minLength={8}
              className={`${authInput} pr-12`}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
              autoFocus
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="absolute right-3 top-1/2 flex size-8 -translate-y-1/2 items-center justify-center rounded-lg text-[var(--placeholder)] hover:bg-[var(--muted)] hover:text-foreground"
            >
              {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </button>
          </div>
          <p className="text-[13px] text-muted-foreground">At least 8 characters.</p>
        </div>

        <div className="flex flex-col gap-2">
          <Label htmlFor="confirmPassword" className={authLabel}>Confirm new password</Label>
          <div className="relative">
            <Input
              id="confirmPassword"
              type={showConfirmPassword ? "text" : "password"}
              autoComplete="new-password"
              className={`${authInput} pr-12`}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              disabled={loading}
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword((v) => !v)}
              aria-label={showConfirmPassword ? "Hide password" : "Show password"}
              className="absolute right-3 top-1/2 flex size-8 -translate-y-1/2 items-center justify-center rounded-lg text-[var(--placeholder)] hover:bg-[var(--muted)] hover:text-foreground"
            >
              {showConfirmPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </button>
          </div>
        </div>

        <AuthSubmit loading={loading} busy="Resetting…">Reset password</AuthSubmit>
      </form>
    </AuthFrame>
  )
}

function ResetPasswordFallback() {
  return (
    <AuthFrame
      title="Set a new password"
      description="Loading…"
      footer={<Link href="/login" className={authLink}>Back to sign in</Link>}
    >
      {null}
    </AuthFrame>
  )
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<ResetPasswordFallback />}>
      <ResetPasswordForm />
    </Suspense>
  )
}

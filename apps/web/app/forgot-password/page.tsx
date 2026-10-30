"use client"

// /forgot-password — App v3. Same endpoint and payload ({ email }).
// AuthFrame replaces the slate card. Success stays on this page.

import * as React from "react"
import { useState } from "react"
import Link from "next/link"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AuthFrame, AuthError, AuthSubmit, authLabel, authInput, authLink } from "@/components/auth/auth-frame"

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("")
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await fetch("/api/proxy/v1/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setError(data?.detail || "Something went wrong. Please try again.")
        setLoading(false)
        return
      }
      setSuccess(true)
    } catch {
      setError("Something went wrong. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const back = <Link href="/login" className={authLink}>Back to sign in</Link>

  if (success) {
    return (
      <AuthFrame
        title="Check your email"
        description={<>If an account exists for <strong>{email}</strong>, you&apos;ll receive a password reset link shortly.</>}
        footer={back}
      >
        <p className="text-[14px] leading-relaxed text-muted-foreground [text-wrap:pretty]">
          Didn&apos;t receive the email? Check your spam folder or{" "}
          <button
            type="button"
            onClick={() => { setSuccess(false); setEmail("") }}
            className={authLink}
          >
            try again
          </button>
          .
        </p>
      </AuthFrame>
    )
  }

  return (
    <AuthFrame
      title="Forgot your password?"
      description="Enter your email and we'll send you a reset link."
      footer={back}
    >
      <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
        {error && <AuthError>{error}</AuthError>}
        <div className="flex flex-col gap-2">
          <Label htmlFor="email" className={authLabel}>Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            className={authInput}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
            autoFocus
          />
        </div>
        <AuthSubmit loading={loading} busy="Sending…">Send reset link</AuthSubmit>
      </form>
    </AuthFrame>
  )
}

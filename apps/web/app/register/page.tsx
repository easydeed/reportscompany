"use client"

// /register — App v3. Same endpoint and payload ({ name, email, password }),
// same router.push("/app") on success — which lands on the dashboard's
// first-run state (dashboard-content.tsx) and from there into onboarding.
//
// What changed:
// - AuthFrame replaces the two-panel layout. The benefits list and the dark
//   panel are gone: the person on this page has already decided; the landing
//   page made the case. The one line that matters ("Free plan, no time limit,
//   no card") is the description.
// - Terms checkbox → sentence under the button. The checkbox wasn't enforced
//   (unchecked still submitted), so it was a required-looking control that
//   wasn't required. Submitting IS the agreement; say so.
// - Password hint tells the truth: the only rule the code enforces is 8+
//   characters. The old hint demanded "a number and symbol" nothing checked.

import * as React from "react"
import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Eye, EyeOff } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AuthFrame, AuthError, AuthSubmit, authLabel, authInput, authLink } from "@/components/auth/auth-frame"

export default function RegisterPage() {
  const router = useRouter()
  const [firstName, setFirstName] = useState("")
  const [lastName, setLastName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (password.length < 8) { setError("Password needs at least 8 characters."); return }
    setLoading(true)
    try {
      const res = await fetch("/api/proxy/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ name: [firstName, lastName].filter(Boolean).join(" "), email, password }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setError(data?.detail || data?.message || "We couldn't create your account. Check your details and try again.")
        setLoading(false)
        return
      }
      router.push("/app")
    } catch {
      setError("Something went wrong. Please try again.")
      setLoading(false)
    }
  }

  return (
    <AuthFrame
      title="Create your account"
      description="Free plan, no time limit. No credit card."
      footer={<>Already have an account? <Link href="/login" className={authLink}>Sign in</Link></>}
    >
      <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
        {error && <AuthError>{error}</AuthError>}

        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-2">
            <Label htmlFor="first-name" className={authLabel}>First name</Label>
            <Input id="first-name" autoComplete="given-name" className={authInput} value={firstName} onChange={(e) => setFirstName(e.target.value)} required disabled={loading} autoFocus />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="last-name" className={authLabel}>Last name</Label>
            <Input id="last-name" autoComplete="family-name" className={authInput} value={lastName} onChange={(e) => setLastName(e.target.value)} required disabled={loading} />
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <Label htmlFor="reg-email" className={authLabel}>Email</Label>
          <Input id="reg-email" type="email" autoComplete="email" placeholder="you@example.com" className={authInput} value={email} onChange={(e) => setEmail(e.target.value)} required disabled={loading} />
        </div>

        <div className="flex flex-col gap-2">
          <Label htmlFor="reg-password" className={authLabel}>Password</Label>
          <div className="relative">
            <Input id="reg-password" type={showPassword ? "text" : "password"} autoComplete="new-password" minLength={8} className={`${authInput} pr-12`}
              value={password} onChange={(e) => setPassword(e.target.value)} required disabled={loading} />
            <button type="button" onClick={() => setShowPassword((v) => !v)} aria-label={showPassword ? "Hide password" : "Show password"}
              className="absolute right-3 top-1/2 flex size-8 -translate-y-1/2 items-center justify-center rounded-lg text-[var(--placeholder)] hover:bg-[var(--muted)] hover:text-foreground">
              {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </button>
          </div>
          <p className="text-[13px] text-muted-foreground">At least 8 characters.</p>
        </div>

        <div className="flex flex-col gap-3">
          <AuthSubmit loading={loading} busy="Creating account…">Create account</AuthSubmit>
          <p className="text-center text-[13px] leading-relaxed text-muted-foreground [text-wrap:pretty]">
            By creating an account you agree to the <Link href="/terms" className="font-medium text-[var(--link)] hover:text-[var(--link-hover)]">Terms</Link> and <Link href="/privacy" className="font-medium text-[var(--link)] hover:text-[var(--link-hover)]">Privacy Policy</Link>.
          </p>
        </div>
      </form>
    </AuthFrame>
  )
}

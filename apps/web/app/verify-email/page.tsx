"use client"

// /verify-email — App v3. Same endpoint and payload ({ token }),
// same redirect to /app on success. AuthFrame replaces the slate card.

import * as React from "react"
import { useState, useEffect, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import { Loader2 } from "lucide-react"
import { AuthFrame, authLink, authSubmitClass } from "@/components/auth/auth-frame"

function VerifyEmailContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get("token")

  const [status, setStatus] = useState<"loading" | "success" | "error" | "no-token">("loading")
  const [message, setMessage] = useState("")

  useEffect(() => {
    if (!token) {
      setStatus("no-token")
      return
    }

    let cancelled = false

    async function verifyEmail() {
      try {
        const res = await fetch("/api/proxy/v1/auth/verify-email", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token }),
        })
        const data = await res.json().catch(() => ({}))
        if (cancelled) return
        if (res.ok) {
          setStatus("success")
          setMessage(data.message || "Email verified successfully!")
          setTimeout(() => router.push("/app"), 3000)
        } else {
          setStatus("error")
          setMessage(data.detail || "Verification failed. Please try again.")
        }
      } catch {
        if (cancelled) return
        setStatus("error")
        setMessage("Something went wrong. Please try again.")
      }
    }

    verifyEmail()
    return () => { cancelled = true }
  }, [token, router])

  const signIn = <Link href="/login" className={authLink}>Sign in</Link>

  if (status === "loading") {
    return (
      <AuthFrame title="Verifying your email" description="Please wait a moment." footer={signIn}>
        <Loader2 className="size-5 animate-spin text-muted-foreground" aria-hidden />
      </AuthFrame>
    )
  }

  if (status === "no-token") {
    return (
      <AuthFrame
        title="No verification token"
        description="This link appears to be invalid. Please check your email for the correct link."
        footer={signIn}
      >
        {null}
      </AuthFrame>
    )
  }

  if (status === "success") {
    return (
      <AuthFrame
        title="Email verified"
        description={message}
        footer={signIn}
      >
        <div className="flex flex-col gap-4">
          <p className="text-[14px] text-muted-foreground">Redirecting you to the dashboard…</p>
          <Link href="/app" className={authSubmitClass}>Go to dashboard</Link>
        </div>
      </AuthFrame>
    )
  }

  return (
    <AuthFrame title="Verification failed" description={message} footer={signIn}>
      <Link href="/app" className={authSubmitClass}>Go to dashboard</Link>
    </AuthFrame>
  )
}

function VerifyEmailFallback() {
  return (
    <AuthFrame
      title="Verifying your email"
      description="Loading…"
      footer={<Link href="/login" className={authLink}>Sign in</Link>}
    >
      <Loader2 className="size-5 animate-spin text-muted-foreground" aria-hidden />
    </AuthFrame>
  )
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<VerifyEmailFallback />}>
      <VerifyEmailContent />
    </Suspense>
  )
}

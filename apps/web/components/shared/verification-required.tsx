"use client"

/**
 * D-019 — what an unverified account sees when it tries to send.
 *
 * The ticket's third requirement, and the one the other two are worthless
 * without: "the blocked action explains why and offers resend." A 403 that the
 * UI turns into "Something went wrong" is not enforcement anyone can act on —
 * it is the same dead end as an unreachable account, arriving one step later.
 *
 * Shared rather than inlined because two surfaces refuse the same way (the
 * unified wizard's send and schedule paths, and the schedule builder's save),
 * and a second copy is how the two would drift into saying different things
 * about the same refusal.
 *
 * Note what the resend button does NOT claim. `/v1/auth/resend-verification`
 * is deliberately non-committal about whether an address is registered
 * (auth.py:936), so the confirmation says we sent a link, not that one has
 * arrived — matching what the endpoint actually tells us.
 */

import { useState } from "react"
import { MailCheck, Loader2, Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { requestVerificationEmail, type VerificationRefusal } from "@/lib/verification"

export function VerificationRequired({
  refusal,
  onBack,
}: {
  refusal: VerificationRefusal
  onBack?: () => void
}) {
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)
  const [failed, setFailed] = useState(false)

  async function resend() {
    if (!refusal.email || sending) return
    setSending(true)
    setFailed(false)
    const ok = await requestVerificationEmail(refusal.email)
    setSending(false)
    if (ok) setSent(true)
    else setFailed(true)
  }

  return (
    <>
      <div className="w-16 h-16 rounded-full bg-amber-50 flex items-center justify-center mx-auto">
        <MailCheck className="w-8 h-8 text-amber-500" />
      </div>
      <div>
        <h2 className="text-lg font-semibold text-gray-900">
          Confirm your email first
        </h2>
        <p className="text-sm text-gray-600 mt-1">{refusal.message}</p>
        <p className="text-sm text-gray-500 mt-2">
          Your report is still here — you can keep building and previewing. Only
          sending is on hold until the address is confirmed.
        </p>
      </div>
      <div className="flex flex-col gap-2 pt-2">
        {refusal.email && !sent && (
          <Button onClick={resend} disabled={sending} className="gap-2">
            {sending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> Sending…
              </>
            ) : (
              <>
                <MailCheck className="w-4 h-4" /> Send me a new link
              </>
            )}
          </Button>
        )}
        {sent && (
          <p className="text-sm text-emerald-700 flex items-center justify-center gap-2">
            <Check className="w-4 h-4" />
            We sent a link to {refusal.email}. Check your inbox and spam folder.
          </p>
        )}
        {failed && (
          <p className="text-sm text-red-600">
            We couldn&apos;t send that link just now. Try again in a moment.
          </p>
        )}
        {onBack && (
          <Button variant="outline" onClick={onBack}>
            Go Back
          </Button>
        )}
      </div>
    </>
  )
}

/**
 * The same refusal as an inline strip, for surfaces that have no full-screen
 * state to switch into (the schedule builder saves in place).
 */
export function VerificationRequiredBanner({
  refusal,
}: {
  refusal: VerificationRefusal
}) {
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)

  async function resend() {
    if (!refusal.email || sending) return
    setSending(true)
    const ok = await requestVerificationEmail(refusal.email)
    setSending(false)
    if (ok) setSent(true)
  }

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 flex gap-3">
      <MailCheck className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
      <div className="text-sm">
        <p className="font-medium text-amber-900">Confirm your email first</p>
        <p className="text-amber-800 mt-1">{refusal.message}</p>
        {refusal.email && !sent && (
          <button
            type="button"
            onClick={resend}
            disabled={sending}
            className="mt-2 font-medium text-amber-900 underline underline-offset-2 disabled:opacity-60"
          >
            {sending ? "Sending…" : "Send me a new link"}
          </button>
        )}
        {sent && (
          <p className="mt-2 text-emerald-700">
            We sent a link to {refusal.email}. Check your inbox and spam folder.
          </p>
        )}
      </div>
    </div>
  )
}

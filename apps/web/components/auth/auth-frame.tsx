"use client"

// Auth frame — App v3. Login and register share it.
//
// Design: one column on the cream ground (--surface-cream), the same ground
// the rail and the landing page sit on. The dark #1E293B split panel is
// gone: it was the old chrome vocabulary, and with the primary now ink a
// dark half-page is the loudest thing on screen while the user is trying to
// type. The form sits in a white card (--card, 16px radius, --border, no
// shadow — cards have none), 420px wide, vertically centred on ≥720px tall
// viewports and top-aligned below that so the keyboard never pushes it off.
//
// The h1 is the app h1 (34 / 800 / -0.03em) — a sign-in page is a page.

import type { ReactNode } from "react"
import Link from "next/link"
import { AlertCircle } from "lucide-react"
import { Logo } from "@/components/logo"

export function AuthFrame({ title, description, children, footer }: {
  title: string
  description?: ReactNode
  children: ReactNode
  /** The "Don't have an account?" line. Rendered outside the card. */
  footer: ReactNode
}) {
  return (
    <div className="flex min-h-screen flex-col bg-[var(--surface-cream)] text-foreground">
      <header className="px-6 pt-7 md:px-10">
        <Link href="/" className="inline-block"><Logo className="h-[26px]" /></Link>
      </header>
      <main className="flex flex-1 flex-col items-center px-6 pb-16 pt-10 min-[720px]:justify-center min-[720px]:pt-0">
        <div className="flex w-full max-w-[420px] flex-col gap-6">
          <div className="flex flex-col gap-7 rounded-[16px] border border-[var(--border)] bg-card p-8 md:p-10">
            <div className="flex flex-col gap-1.5">
              <h1 className="text-[34px] font-extrabold leading-[1.1] tracking-[-0.03em] [text-wrap:balance]">{title}</h1>
              {description && <p className="text-[16px] text-muted-foreground [text-wrap:pretty]">{description}</p>}
            </div>
            {children}
          </div>
          <p className="text-center text-[14px] text-muted-foreground">{footer}</p>
        </div>
      </main>
    </div>
  )
}

// Error row — the destructive status pair, the only tinted fill allowed on
// chrome. One line, no title ("Login failed" above "Invalid email" said the
// same thing twice).
export function AuthError({ children }: { children: ReactNode }) {
  return (
    <div role="alert" className="flex items-start gap-2.5 rounded-[10px] bg-[var(--destructive-muted)] px-3.5 py-3 text-[14px] font-medium text-[var(--destructive-foreground)]">
      <AlertCircle className="mt-[1px] size-4 shrink-0" />
      <span>{children}</span>
    </div>
  )
}

// Primary button — ink, 46px (one step up from the rail's 42px "New report"
// because it's the only button on the page), 9px radius to match.
export function AuthSubmit({ loading, children, busy }: { loading: boolean; children: ReactNode; busy: string }) {
  return (
    <button
      type="submit"
      disabled={loading}
      className="flex h-[46px] w-full items-center justify-center rounded-[9px] bg-primary text-[15px] font-semibold text-primary-foreground transition-colors hover:bg-[var(--primary-hover)] disabled:cursor-not-allowed disabled:opacity-50"
    >
      {loading ? busy : children}
    </button>
  )
}

export const authLabel = "text-[13px] font-semibold text-foreground"
export const authInput = "h-[46px] rounded-[9px] border-[1.5px] border-[var(--border-strong)] bg-white px-3.5 text-[15px] md:text-[15px]"
export const authLink = "font-semibold text-[var(--link)] hover:text-[var(--link-hover)]"

"use client"

// Sponsor-view vocabulary shared by /app/company/* and /app/affiliate/*.
// Everything here is the App v3 list language (components/ui/list.tsx) plus
// the two things the sponsor views add: a status sentence with a dot, and a
// row menu whose items state their consequence.

import type { ReactNode } from "react"
import { MoreHorizontal } from "lucide-react"
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"

// ── Formatting ──────────────────────────────────────────────────────────────

export function initials(name: string) {
  return name.split(" ").filter(Boolean).map((w) => w[0]).join("").slice(0, 2).toUpperCase() || "?"
}

/** Deterministic avatar colour per name — the circle IS the person. */
const AVATARS = ["#4F46E5", "#0E7490", "#7C3AED", "#B45309", "#065F46", "#9F1239", "#1D4ED8", "#475569"]
export function avatarColor(seed: string) {
  let h = 0
  for (const c of seed) h = (h * 31 + c.charCodeAt(0)) >>> 0
  return AVATARS[h % AVATARS.length]
}

export function reportTypeLabel(slug: string) {
  const map: Record<string, string> = {
    market_snapshot: "market snapshot", new_listings: "new listings", closed: "closed sales", closed_sales: "closed sales",
    inventory: "inventory", price_bands: "price bands", featured_listings: "featured listings", open_houses: "open houses",
  }
  return map[slug] ?? slug.replace(/_/g, " ")
}

/** "Today" · "Yesterday" · "Monday" · "Oct 14" — never "3d ago". */
export function whenLabel(iso: string | null | undefined) {
  if (!iso) return ""
  const d = new Date(iso), now = new Date()
  const days = Math.floor((now.setHours(0, 0, 0, 0) - new Date(d).setHours(0, 0, 0, 0)) / 86_400_000)
  if (days <= 0) return "Today"
  if (days === 1) return "Yesterday"
  if (days < 7) return d.toLocaleDateString("en-US", { weekday: "long" })
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" })
}

/** "5 weeks" / "3 days" for "nothing sent in …". */
export function sinceLabel(iso: string | null | undefined) {
  if (!iso) return null
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000)
  if (days < 7) return `${days} day${days === 1 ? "" : "s"}`
  if (days < 60) return `${Math.floor(days / 7)} weeks`
  return `${Math.floor(days / 30)} months`
}

export const QUIET_DAYS = 30

// ── Atoms ────────────────────────────────────────────────────────────────────

export function Avatar({ name, size = 38, color, className }: { name: string; size?: number; color?: string; className?: string }) {
  return (
    <span
      className={cn("flex shrink-0 items-center justify-center rounded-full font-bold text-white", className)}
      style={{ width: size, height: size, fontSize: Math.round(size * 0.34), background: color ?? avatarColor(name) }}
    >
      {initials(name)}
    </span>
  )
}

export type Tone = "good" | "warn" | "off"
const DOT: Record<Tone, string> = { good: "var(--success)", warn: "var(--warning)", off: "var(--disabled)" }

/** Dot + one plain-English sentence. `off` greys the text as well. */
export function Sentence({ tone, children, size = 15 }: { tone: Tone; children: ReactNode; size?: 15 | 17 }) {
  return (
    <span className="flex min-w-0 items-center gap-[10px]">
      <span className="size-[9px] shrink-0 rounded-full" style={{ background: DOT[tone] }} />
      <span className={cn(tone === "off" ? "text-muted-foreground" : "text-foreground", size === 17 ? "text-[17px] font-semibold" : "text-[15px]")}>{children}</span>
    </span>
  )
}

/** Seat badge: the only mark on a row that says "trial agent". */
export function SeatBadge() {
  return (
    <svg aria-label="Has a seat" className="size-[14px] shrink-0 text-[var(--link)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z" /><path d="m9 12 2 2 4-4" />
    </svg>
  )
}

/** Outline 36px row action. */
export function RowButton({ children, onClick, href }: { children: ReactNode; onClick?: () => void; href?: string }) {
  const cls = "inline-flex h-9 items-center whitespace-nowrap rounded-[9px] border border-[var(--border)] bg-white px-[14px] text-[14px] font-semibold text-foreground transition-colors hover:bg-[var(--surface-cream)]"
  if (href) return <a href={href} className={cls}>{children}</a>
  return <button type="button" onClick={onClick} className={cls}>{children}</button>
}

export type MenuItem = { label: string; note: string; danger?: boolean; onSelect: () => void }

/** ⋯ menu where every item says what it does. Destructive items are red. */
export function ConsequenceMenu({ items, size = 36 }: { items: MenuItem[]; size?: 36 | 42 }) {
  if (items.length === 0) return null
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label="More"
          className={cn("flex items-center justify-center rounded-[9px] text-[var(--body)] transition-colors hover:bg-[var(--muted)]", size === 42 ? "size-[42px] border border-[var(--border)] bg-white hover:bg-[var(--surface-cream)]" : "size-9")}
        >
          <MoreHorizontal className="size-4" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[300px] rounded-xl p-1.5">
        {items.map((it) => (
          <DropdownMenuItem key={it.label} onSelect={it.onSelect} className="flex cursor-pointer flex-col items-start gap-0.5 rounded-lg px-3 py-2.5 focus:bg-[var(--surface-cream)]">
            <span className={cn("text-[14px] font-semibold", it.danger ? "text-[var(--destructive-foreground)]" : "text-foreground")}>{it.label}</span>
            <span className="text-[12.5px] leading-[1.4] text-muted-foreground">{it.note}</span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

/** One activity line: glyph · sentence · when. */
export function ActivityRow({ icon, text, when, tone = "default" }: { icon: ReactNode; text: ReactNode; when: string; tone?: "default" | "good" | "link" }) {
  const color = tone === "good" ? "text-[var(--success-foreground)]" : tone === "link" ? "text-[var(--link)]" : "text-[var(--body)]"
  return (
    <div className="grid grid-cols-[minmax(0,1fr)_110px] items-center gap-[18px] border-b border-[var(--border-subtle)] py-[13px]">
      <span className="flex min-w-0 items-center gap-3">
        <span className={cn("[&>svg]:size-4 shrink-0", color)}>{icon}</span>
        <span className="text-[15px] text-foreground">{text}</span>
      </span>
      <span className="whitespace-nowrap text-right text-[14px] text-muted-foreground">{when}</span>
    </div>
  )
}

/** Plain stat cell: label / big number / one sub-line. No icon, no tint. */
export function StatCell({ label, value, sub, subTone = "muted" }: { label: string; value: ReactNode; sub?: ReactNode; subTone?: "muted" | "good" | "warn" }) {
  const c = subTone === "good" ? "text-[var(--success-foreground)]" : subTone === "warn" ? "text-[var(--warning-foreground)]" : "text-muted-foreground"
  return (
    <div className="flex flex-col gap-1 rounded-xl border border-[var(--border)] px-5 py-[18px]">
      <span className="text-[13px] text-muted-foreground">{label}</span>
      <span className="text-[28px] font-extrabold leading-[1.1] tracking-[-0.03em] tabular-nums text-foreground">{value}</span>
      {sub && <span className={cn("text-[13px]", c)}>{sub}</span>}
    </div>
  )
}

/** 20px section heading with an optional trailing link. */
export function H2({ children, linkLabel, href, onClick }: { children: ReactNode; linkLabel?: string; href?: string; onClick?: () => void }) {
  return (
    <div className="flex items-baseline justify-between gap-4">
      <h2 className="text-[20px] font-bold tracking-[-0.02em] text-foreground">{children}</h2>
      {linkLabel && (href
        ? <a href={href} className="text-[14px] font-semibold text-[var(--link)] hover:text-[var(--link-hover)]">{linkLabel}</a>
        : <button type="button" onClick={onClick} className="text-[14px] font-semibold text-[var(--link)] hover:text-[var(--link-hover)]">{linkLabel}</button>)}
    </div>
  )
}

/** Inline add-by-email: 50px input + ink button. Submits on Enter. */
export function EmailInvite({ placeholder, button, onSubmit, busy }: { placeholder: string; button: string; onSubmit: (email: string) => void; busy?: boolean }) {
  return (
    <form
      className="flex flex-wrap items-center gap-[10px]"
      onSubmit={(e) => { e.preventDefault(); const f = e.currentTarget; const v = (f.elements.namedItem("email") as HTMLInputElement).value.trim(); if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) { onSubmit(v); f.reset() } }}
    >
      <input
        name="email" type="email" required placeholder={placeholder} disabled={busy}
        className="h-[50px] min-w-[260px] flex-1 rounded-[10px] border-[1.5px] border-[var(--border-strong)] bg-white px-4 text-[16px] text-foreground outline-none placeholder:text-[var(--placeholder)] focus:border-[var(--link)] focus:ring-[3px] focus:ring-[var(--link)]/20"
      />
      <button type="submit" disabled={busy} className="h-[50px] rounded-[10px] bg-primary px-[22px] text-[15px] font-semibold text-primary-foreground transition-colors hover:bg-[var(--primary-hover)] disabled:opacity-60">{button}</button>
    </form>
  )
}

/** Fetch helper with the proxy + JSON conventions the pages already use. */
export async function post(path: string, body?: unknown) {
  const res = await fetch(`/api/proxy${path}`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body) })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : data.detail?.message || `Request failed (${res.status})`)
  return data
}

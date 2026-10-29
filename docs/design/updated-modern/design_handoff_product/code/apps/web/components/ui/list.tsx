"use client"

// App v3 list primitives. Lists are NOT boxed cards: a 1.5px ink rule on top,
// an 11px uppercase header row, 1px rules between rows, no outer border, no
// shadow, no footer. These replace ui/table on Reports, Property, Schedules,
// Contacts, Leads, Admin runs.

import type { ReactNode, CSSProperties } from "react"
import Link from "next/link"
import { cn } from "@/lib/utils"

/** 12px uppercase section label with optional trailing link ("All reports →"). */
export function SectionLabel({ children, href, linkLabel, onClick }: { children: ReactNode; href?: string; linkLabel?: string; onClick?: () => void }) {
  return (
    <div className="flex items-baseline justify-between">
      <span className="text-[12px] font-bold uppercase tracking-[0.1em] text-muted-foreground">{children}</span>
      {linkLabel && (href ? (
        <Link href={href} prefetch={false} className="text-[14px] font-semibold text-[var(--link)] hover:text-[var(--link-hover)]">{linkLabel}</Link>
      ) : (
        <button onClick={onClick} className="text-[14px] font-semibold text-[var(--link)] hover:text-[var(--link-hover)]">{linkLabel}</button>
      ))}
    </div>
  )
}

/** The rule-topped list container. */
export function RuleList({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("flex flex-col border-t-[1.5px] border-foreground", className)}>{children}</div>
}

/** Grid header row. `columns` is a CSS grid-template-columns string shared with rows. */
export function ListHeader({ columns, cells }: { columns: string; cells: ReactNode[] }) {
  return (
    <div className="grid items-center gap-[18px] border-b border-[var(--border-subtle)] py-[10px] text-[11px] font-semibold uppercase tracking-[0.06em] text-muted-foreground" style={{ gridTemplateColumns: columns }}>
      {cells.map((c, i) => <span key={i}>{c}</span>)}
    </div>
  )
}

/** Grid row. Hover goes cream; pass `onClick` to make the whole row a target. */
export function ListRow({ columns, children, onClick, className, style }: { columns: string; children: ReactNode; onClick?: () => void; className?: string; style?: CSSProperties }) {
  const Comp: any = onClick ? "button" : "div"
  return (
    <Comp
      onClick={onClick}
      className={cn("grid w-full items-center gap-[18px] border-b border-[var(--border-subtle)] py-3 text-left transition-colors hover:bg-[var(--surface-cream)]", onClick && "cursor-pointer", className)}
      style={{ gridTemplateColumns: columns, ...style }}
    >
      {children}
    </Comp>
  )
}

/** Title + sub stacked, truncating. */
export function Cell({ title, sub, className }: { title: ReactNode; sub?: ReactNode; className?: string }) {
  return (
    <div className={cn("flex min-w-0 flex-col", className)}>
      <span className="truncate text-[15px] font-semibold text-foreground">{title}</span>
      {sub !== undefined && <span className="truncate text-[13px] text-muted-foreground">{sub}</span>}
    </div>
  )
}

/** Plain 15px body cell. Numbers get tabular figures. */
export function Text({ children, num, strong, muted, className }: { children: ReactNode; num?: boolean; strong?: boolean; muted?: boolean; className?: string }) {
  return <span className={cn("text-[15px]", num && "tabular-nums", strong ? "font-semibold text-foreground" : muted ? "text-muted-foreground" : "text-[var(--body)]", className)}>{children}</span>
}

/** 34px square icon button for row actions. `tone="link"` colours the glyph indigo; `tone="danger"` reds the hover. */
export function IconButton({ href, onClick, label, children, tone, external }: { href?: string; onClick?: () => void; label: string; children: ReactNode; tone?: "link" | "danger"; external?: boolean }) {
  const cls = cn(
    "flex size-[34px] items-center justify-center rounded-lg transition-colors [&>svg]:size-4",
    tone === "danger" ? "text-[var(--placeholder)] hover:bg-[var(--destructive-muted)] hover:text-[var(--destructive-foreground)]" : tone === "link" ? "text-[var(--link)] hover:bg-[var(--muted)] hover:text-[var(--link-hover)]" : "text-[var(--body)] hover:bg-[var(--muted)] hover:text-foreground",
  )
  if (href) return <a href={href} aria-label={label} title={label} className={cls} target={external ? "_blank" : undefined} rel={external ? "noopener noreferrer" : undefined}>{children}</a>
  return <button type="button" aria-label={label} title={label} onClick={onClick} className={cls}>{children}</button>
}

/** Filter pills: on = ink, off = white + border. */
export function FilterPills<T extends string>({ value, onChange, options, className }: { value: T; onChange: (v: T) => void; options: { value: T; label: string }[]; className?: string }) {
  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {options.map((o) => {
        const on = o.value === value
        return (
          <button
            key={o.value}
            type="button"
            onClick={() => onChange(o.value)}
            aria-pressed={on}
            className={cn("rounded-full border px-[14px] py-[7px] text-[13px] font-semibold transition-colors", on ? "border-foreground bg-foreground text-white" : "border-[var(--border)] bg-white text-[var(--secondary-foreground)] hover:border-[var(--border-strong)]")}
          >
            {o.label}
          </button>
        )
      })}
    </div>
  )
}

/** Inline empty state: one sentence + optional action, inside the list rule. */
export function ListEmpty({ children }: { children: ReactNode }) {
  return <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-[var(--border-subtle)] py-[14px] text-[14px] text-muted-foreground">{children}</div>
}

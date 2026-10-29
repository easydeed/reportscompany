"use client"

/**
 * The visual vocabulary of Design's `Wizards v3.dc.html` market flow, shared
 * by the four steps: one heading and one sentence per step, ink pills, radio
 * rows under a heavy rule, uppercase field labels.
 *
 * Presentation only. Every step still owns its handlers and passes them in.
 */
import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

export function StepHeader({ title, sub }: { title: string; sub: string }) {
  return (
    <div className="flex flex-col gap-2">
      <h2 className="m-0 text-[28px] font-extrabold leading-[1.1] tracking-[-0.03em] text-[#0F172A]">
        {title}
      </h2>
      <p className="m-0 text-[15px] text-[#64748B]">{sub}</p>
    </div>
  )
}

export function FieldLabel({ children }: { children: ReactNode }) {
  return (
    <span className="text-xs font-bold uppercase tracking-[0.1em] text-[#64748B]">{children}</span>
  )
}

/** A rounded pill: ink when on, outlined when off. */
export function Pill({
  on,
  onClick,
  children,
  className,
}: {
  on: boolean
  onClick: () => void
  children: ReactNode
  className?: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={on}
      className={cn(
        "rounded-full border px-3.5 py-[7px] text-[13px] font-semibold transition-colors",
        on
          ? "border-[#0F172A] bg-[#0F172A] text-white"
          : "border-[#E4E2DA] bg-white text-[#475569] hover:border-[#0F172A] hover:text-[#0F172A]",
        className,
      )}
    >
      {children}
    </button>
  )
}

/** The list a set of radio rows sits in: a heavy rule on top. */
export function RadioList({ children }: { children: ReactNode }) {
  return <div className="flex flex-col border-t-[1.5px] border-[#0F172A]">{children}</div>
}

export function RadioRow({
  on,
  onClick,
  label,
  desc,
  aside,
}: {
  on: boolean
  onClick: () => void
  label: string
  desc?: string
  aside?: string
}) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={on}
      onClick={onClick}
      className="grid items-start gap-3.5 border-b border-[#ECEAE3] py-[13px] text-left"
      style={{ gridTemplateColumns: aside ? "22px minmax(0,1fr) auto" : "22px minmax(0,1fr)" }}
    >
      <span
        className="mt-0.5 box-border h-5 w-5 rounded-full bg-white"
        style={{ border: on ? "6px solid #0F172A" : "1.5px solid #CBD5E1" }}
      />
      <span className="flex flex-col">
        <span className={cn("text-[15px] text-[#0F172A]", on ? "font-bold" : "font-medium")}>{label}</span>
        {desc && <span className="text-[13px] text-[#64748B]">{desc}</span>}
      </span>
      {aside && <span className="mt-0.5 whitespace-nowrap text-xs text-[#5E636B]">{aside}</span>}
    </button>
  )
}

/** Native select, styled to sit with the pills. */
export const selectClass =
  "h-11 rounded-lg border border-[#D6D3CB] bg-white px-3 text-[15px] font-medium text-[#0F172A] outline-none focus:border-[#0F172A]"

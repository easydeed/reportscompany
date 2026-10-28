import { cn } from "@/lib/utils"

interface LogoProps {
  className?: string
  /** full: light lockup. white: lockup for an ink surface. icon: bare triangle. */
  variant?: "full" | "icon" | "white"
}

/**
 * Ticker lockup, inlined so it uses the page's Plus Jakarta Sans
 * (an <img> of the SVG would not see next/font). The public SVG files
 * stay in /public for the favicon and direct URLs.
 *
 * The pill is 98 wide, not Design's 86: in Plus Jakarta Sans "Reports" ends
 * at x 237.7, past an 86-wide pill and the 236 viewBox, so the "s" was cut
 * off. 98 gives it the same 10 units on the right as the triangle has on the
 * left. Email cannot use this (no web font): it uses the outlined PNGs in
 * /public/email, made by scripts/outline_lockup.py.
 */
function Lockup({ dark, className }: { dark: boolean; className?: string }) {
  const ink = dark ? "#FFFFFF" : "#0F172A"
  const tag = dark ? "#065F46" : "#D1FAE5"
  const tagInk = dark ? "#D1FAE5" : "#065F46"
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 248 48"
      role="img"
      aria-label="Trendy Reports"
      className={cn("h-[26px] w-auto", className)}
      style={{ fontFamily: "var(--font-jakarta), sans-serif" }}
    >
      <text x="0" y="38" fontSize="44" fontWeight="800" letterSpacing="-2" fill={ink}>
        Trendy
      </text>
      <rect x="150" y="8" width="98" height="28" rx="6" fill={tag} />
      <g transform="translate(160 14) scale(1.15)">
        <path d="M7 2 L12 9 L2 9 Z" fill={tagInk} />
      </g>
      <text x="180" y="28" fontSize="15" fontWeight="700" fill={tagInk}>
        Reports
      </text>
    </svg>
  )
}

function Mark({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 32 32"
      role="img"
      aria-label="Trendy Reports"
      className={cn("h-8 w-auto", className)}
    >
      <path d="M16 5 L29 24 L3 24 Z" fill="#059669" />
    </svg>
  )
}

export function Logo({ className, variant = "full" }: LogoProps) {
  if (variant === "icon") return <Mark className={className} />
  return <Lockup dark={variant === "white"} className={className} />
}

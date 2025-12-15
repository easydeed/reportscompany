"use client"

import { cn } from "@/lib/utils"

interface LogoProps {
  className?: string
  variant?: "full" | "icon"
  showText?: boolean
  theme?: "light" | "dark"
}

export function Logo({ className, variant = "full", showText = true, theme = "light" }: LogoProps) {
  const IconMark = ({ size = 40 }: { size?: number }) => (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Rounded square container */}
      <rect x="4" y="4" width="32" height="32" rx="6" fill="#7C3AED" />

      {/* House roofline */}
      <path d="M20 11L28 17V18H12V17L20 11Z" fill="white" opacity="0.95" />

      {/* Chart bars - 3 vertical bars */}
      <rect x="13" y="21" width="3" height="11" rx="1.5" fill="white" opacity="0.9" />
      <rect x="18.5" y="18" width="3" height="14" rx="1.5" fill="white" opacity="0.95" />
      <rect x="24" y="23" width="3" height="9" rx="1.5" fill="#F26B2B" />
    </svg>
  )

  if (variant === "icon") {
    return (
      <div className={cn("flex items-center justify-center", className)}>
        <IconMark size={48} />
      </div>
    )
  }

  return (
    <div className={cn("flex items-center gap-1", className)}>
      <IconMark size={36} />

      {showText && (
        <span className="text-xl font-logo tracking-tight font-normal">
          <span className={cn(theme === "dark" ? "text-white" : "text-slate-900")}>TrendyReports</span>
        </span>
      )}
    </div>
  )
}

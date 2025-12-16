"use client"

import { cn } from "@/lib/utils"
import Image from "next/image"

interface LogoProps {
  className?: string
  variant?: "full" | "icon"
  showText?: boolean
}

export function Logo({ className, variant = "full", showText = true }: LogoProps) {
  if (variant === "icon") {
    // Icon-only version - just the lightning bolt "T"
    return (
      <div className={cn("flex items-center justify-center", className)}>
        <svg
          viewBox="0 0 230 290"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full"
        >
          <path
            d="M94.2,152.3l-21.5,42.7h43.9l-16,46.5,46-63.8h-37.6l24.5-49.7h-27l-12.3,24.4h0ZM88.9,127.9H28.6l27.6-56.1h174.5l-27.6,56.1h-52.1l-16.7,34h43.1l-92.2,127.9c-2.5,3.5-7.1,4.5-10.8,2.6-3.8-2-5.5-6.3-4.1-10.3l24.5-71.4h-47.3l29.4-58.4,12.3-24.4h0ZM193.4,112.2l12.1-24.6H66l-12.1,24.6h139.5Z"
            fill="#f26a21"
          />
        </svg>
      </div>
    )
  }

  // Full logo with text
  return (
    <div className={cn("flex items-center", className)}>
      <Image
        src="/logo.svg"
        alt="TrendyReports"
        width={160}
        height={48}
        className="h-8 w-auto"
        priority
      />
    </div>
  )
}

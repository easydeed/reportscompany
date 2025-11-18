"use client"

import { cn } from "@/lib/utils"

interface LogoProps {
  className?: string
  variant?: "full" | "icon"
  showText?: boolean
}

export function Logo({ className, variant = "full", showText = true }: LogoProps) {
  if (variant === "icon") {
    return (
      <div className={cn("flex items-center justify-center", className)}>
        <svg
          width="48"
          height="48"
          viewBox="0 0 48 48"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full"
        >
          
          
          {/* Main geometric shape - hexagon base */}
          <path
            d="M24 4 L38 12 L38 28 L24 36 L10 28 L10 12 Z"
            fill="url(#mainGradient)"
            className="drop-shadow-lg"
          />
          
          {/* Inner trend line - dynamic upward movement */}
          <path
            d="M14 28 L18 24 L22 26 L26 20 L30 22 L34 16"
            stroke="#F26B2B"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
            className="drop-shadow-md"
          />
          
          {/* Accent dots on trend line */}
          <circle cx="14" cy="28" r="2" fill="#F26B2B" />
          <circle cx="22" cy="26" r="2.5" fill="#F26B2B" />
          <circle cx="30" cy="22" r="2" fill="#F26B2B" />
          <circle cx="34" cy="16" r="3" fill="#F26B2B" className="animate-pulse" />
          
          {/* Geometric accent lines */}
          <path
            d="M24 10 L24 16"
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
            opacity="0.6"
          />
          
          {/* Inner glow effect */}
          <circle 
            cx="24" 
            cy="24" 
            r="16" 
            fill="url(#glowGradient)"
            opacity="0.15"
          />
          
          <defs>
            {/* Main gradient for hexagon */}
            <linearGradient id="mainGradient" x1="10" y1="4" x2="38" y2="36" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#9333EA" />
              <stop offset="50%" stopColor="#7C3AED" />
              <stop offset="100%" stopColor="#6D28D9" />
            </linearGradient>
            
            {/* Glow gradient */}
            <radialGradient id="glowGradient" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#F26B2B" />
              <stop offset="100%" stopColor="transparent" />
            </radialGradient>
          </defs>
        </svg>
      </div>
    )
  }

  return (
    <div className={cn("flex items-center gap-2", className)}>
      {/* Icon */}
      <Logo variant="icon" className="w-10 h-10" showText={false} />
      
      {/* Wordmark */}
      {showText && (
        <div className="flex flex-col leading-none">
          <span className="text-xl font-logo font-normal bg-gradient-to-r from-purple-600 via-purple-700 to-purple-800 bg-clip-text text-transparent tracking-tight">
            TrendyReports
          </span>
          <span className="text-[9px] text-muted-foreground/70 tracking-[0.2em] uppercase font-logo font-normal mt-0.5">
            Market Intelligence
          </span>
        </div>
      )}
    </div>
  )
}

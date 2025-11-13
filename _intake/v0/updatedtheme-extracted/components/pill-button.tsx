"use client"

import { cn } from "@/lib/utils"
import { Button, type ButtonProps } from "@/components/ui/button"
import { forwardRef } from "react"

interface PillButtonProps extends ButtonProps {
  variant?: "primary" | "ghost" | "danger"
}

export const PillButton = forwardRef<HTMLButtonElement, PillButtonProps>(
  ({ className, variant = "primary", children, ...props }, ref) => {
    const variantStyles = {
      primary: "bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm",
      ghost: "bg-transparent hover:bg-muted text-foreground border border-border",
      danger: "bg-destructive text-destructive-foreground hover:bg-destructive/90 shadow-sm",
    }

    return (
      <Button
        ref={ref}
        className={cn(
          "rounded-full px-6 h-10 font-medium transition-all duration-180",
          "focus-visible:ring-2 focus-visible:ring-accent/60 focus-visible:ring-offset-2",
          variantStyles[variant],
          className,
        )}
        {...props}
      >
        {children}
      </Button>
    )
  },
)

PillButton.displayName = "PillButton"

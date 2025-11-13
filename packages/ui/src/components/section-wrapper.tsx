import { cn } from "../lib/utils"
import type { ReactNode } from "react"

interface SectionWrapperProps {
  children: ReactNode
  className?: string
  id?: string
  background?: "default" | "muted" | "gradient"
}

export function SectionWrapper({ children, className, id, background = "default" }: SectionWrapperProps) {
  return (
    <section
      id={id}
      className={cn(
        "py-16 sm:py-24",
        background === "muted" && "bg-secondary/30",
        background === "gradient" && "bg-gradient-to-b from-background via-secondary/20 to-background",
        className,
      )}
    >
      <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8">{children}</div>
    </section>
  )
}

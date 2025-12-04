"use client"

import { cn } from "../lib/utils"
import { Check } from "lucide-react"
import { motion } from "framer-motion"

interface Step {
  id: string
  label: string
}

interface HorizontalStepperProps {
  steps: Step[]
  currentStep: number
  className?: string
}

export function HorizontalStepper({ steps, currentStep, className }: HorizontalStepperProps) {
  return (
    <div className={cn("w-full", className)}>
      <div className="mb-8">
        {/* Circles row - fixed height container for proper line centering */}
        <div className="relative h-10">
          {/* Background line - centered in the 40px (h-10) container */}
          <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-0.5 bg-border" />
          
          {/* Animated progress line */}
          <motion.div
            className="absolute left-0 top-1/2 -translate-y-1/2 h-0.5 bg-primary"
            initial={{ width: 0 }}
            animate={{
              width: `${(currentStep / (steps.length - 1)) * 100}%`,
            }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          />

          {/* Circles positioned on top of lines */}
          <div className="relative flex justify-between h-full">
            {steps.map((step, index) => {
              const isCompleted = index < currentStep
              const isCurrent = index === currentStep
              const isUpcoming = index > currentStep

              return (
                <motion.div
                  key={step.id}
                  initial={false}
                  animate={{
                    scale: isCurrent ? 1.1 : 1,
                  }}
                  className={cn(
                    "w-10 h-10 rounded-full border-2 flex items-center justify-center font-display font-bold text-sm transition-all duration-180 relative z-10",
                    isCompleted && "bg-primary border-primary text-primary-foreground shadow-sm",
                    isCurrent && "bg-primary border-primary text-primary-foreground shadow-lg shadow-primary/30",
                    isUpcoming && "bg-background border-border text-muted-foreground",
                  )}
                >
                  {isCompleted ? <Check className="w-5 h-5" /> : index + 1}
                </motion.div>
              )
            })}
          </div>
        </div>

        {/* Labels row - separate from circles */}
        <div className="flex justify-between mt-2">
          {steps.map((step, index) => {
            const isCompleted = index < currentStep
            const isCurrent = index === currentStep
            const isUpcoming = index > currentStep

            return (
              <span
                key={step.id}
                className={cn(
                  "text-sm font-medium transition-colors duration-180 text-center w-10",
                  isCurrent && "text-foreground",
                  (isCompleted || isUpcoming) && "text-muted-foreground",
                )}
              >
                {step.label}
              </span>
            )
          })}
        </div>
      </div>
    </div>
  )
}

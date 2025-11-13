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
      {/* Progress bar */}
      <div className="relative mb-8">
        <div className="absolute top-5 left-0 right-0 h-0.5 bg-border" />
        <motion.div
          className="absolute top-5 left-0 h-0.5 gradient-quantum"
          initial={{ width: 0 }}
          animate={{
            width: `${(currentStep / (steps.length - 1)) * 100}%`,
          }}
          transition={{ duration: 0.3, ease: "easeOut" }}
        />

        <div className="relative flex justify-between">
          {steps.map((step, index) => {
            const isCompleted = index < currentStep
            const isCurrent = index === currentStep
            const isUpcoming = index > currentStep

            return (
              <div key={step.id} className="flex flex-col items-center">
                <motion.div
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
                <span
                  className={cn(
                    "mt-2 text-sm font-medium transition-colors duration-180",
                    isCurrent && "text-foreground",
                    (isCompleted || isUpcoming) && "text-muted-foreground",
                  )}
                >
                  {step.label}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

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
  const progress = (currentStep / (steps.length - 1)) * 100

  return (
    <div className={cn("w-full", className)}>
      {/* Progress bar container */}
      <div className="relative mb-2">
        {/* Background track */}
        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
          {/* Animated progress fill */}
          <motion.div
            className="h-full bg-gradient-to-r from-primary to-primary/80 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.4, ease: "easeOut" }}
          />
        </div>

        {/* Step dots positioned on the track */}
        <div className="absolute inset-0 flex justify-between items-center">
          {steps.map((step, index) => {
            const isCompleted = index < currentStep
            const isCurrent = index === currentStep
            const isUpcoming = index > currentStep

            return (
              <motion.div
                key={step.id}
                initial={false}
                animate={{
                  scale: isCurrent ? 1 : 1,
                }}
                className="relative"
              >
                {/* Pulse ring for current step */}
                {isCurrent && (
                  <motion.div
                    className="absolute inset-0 rounded-full bg-primary/30"
                    initial={{ scale: 1, opacity: 0.5 }}
                    animate={{ scale: 1.8, opacity: 0 }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: "easeOut" }}
                    style={{ width: 28, height: 28, top: -6, left: -6 }}
                  />
                )}
                
                <div
                  className={cn(
                    "w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold transition-all duration-300 relative z-10",
                    isCompleted && "bg-primary text-primary-foreground shadow-sm",
                    isCurrent && "bg-primary text-primary-foreground shadow-lg shadow-primary/40 ring-4 ring-primary/20",
                    isUpcoming && "bg-muted border-2 border-border text-muted-foreground",
                  )}
                >
                  {isCompleted && <Check className="w-2.5 h-2.5" strokeWidth={3} />}
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* Labels row */}
      <div className="flex justify-between px-0">
        {steps.map((step, index) => {
          const isCompleted = index < currentStep
          const isCurrent = index === currentStep

          return (
            <div
              key={step.id}
              className={cn(
                "flex flex-col items-center",
                index === 0 && "items-start",
                index === steps.length - 1 && "items-end",
              )}
            >
              <span
                className={cn(
                  "text-sm font-medium transition-all duration-300",
                  isCurrent && "text-primary font-semibold",
                  isCompleted && "text-muted-foreground",
                  !isCurrent && !isCompleted && "text-muted-foreground/60",
                )}
              >
                {step.label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

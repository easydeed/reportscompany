"use client"

import { cn } from "@/lib/utils"
import { Check } from "lucide-react"
import { motion } from "framer-motion"

interface Step {
  title: string
  description: string
}

interface StepperProps {
  steps: Step[]
  currentStep?: number
  className?: string
}

export function Stepper({ steps, currentStep = 0, className }: StepperProps) {
  return (
    <div className={cn("space-y-8", className)}>
      {steps.map((step, index) => {
        const isCompleted = index < currentStep
        const isCurrent = index === currentStep
        const isUpcoming = index > currentStep

        return (
          <div key={index} className="flex gap-4">
            <div className="flex flex-col items-center">
              <motion.div
                initial={{ scale: 0 }}
                whileInView={{ scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.2, delay: index * 0.1 }}
                className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center font-display font-semibold transition-all duration-200",
                  isCompleted && "bg-primary text-primary-foreground",
                  isCurrent && "bg-primary text-primary-foreground ring-4 ring-primary/20",
                  isUpcoming && "bg-secondary text-muted-foreground border-2 border-border",
                )}
              >
                {isCompleted ? <Check className="w-5 h-5" /> : <span>{index + 1}</span>}
              </motion.div>
              {index < steps.length - 1 && (
                <div
                  className={cn(
                    "w-0.5 h-16 mt-2 transition-colors duration-200",
                    isCompleted ? "bg-primary" : "bg-border",
                  )}
                />
              )}
            </div>
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.2, delay: index * 0.1 }}
              className="flex-1 pb-8"
            >
              <h3 className={cn("font-display font-semibold text-lg mb-1", isCurrent && "text-primary")}>
                {step.title}
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{step.description}</p>
            </motion.div>
          </div>
        )
      })}
    </div>
  )
}

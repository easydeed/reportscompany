"use client"

import { Globe, FileText, Image, Mail, Check, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ReportBuilderState, EmailRecipient } from "../types"

interface DeliverySectionProps {
  viewInBrowser: boolean
  downloadPdf: boolean
  downloadSocialImage: boolean
  sendViaEmail: boolean
  emailRecipients: EmailRecipient[]
  onChange: (updates: Partial<ReportBuilderState>) => void
  hasOption: boolean
  stepNumber?: number
}

const DELIVERY_OPTIONS = [
  { 
    key: "viewInBrowser" as const, 
    label: "View in Browser", 
    description: "Open interactive web report",
    icon: Globe 
  },
  { 
    key: "downloadPdf" as const, 
    label: "Download PDF", 
    description: "High-quality for printing",
    icon: FileText 
  },
  { 
    key: "downloadSocialImage" as const, 
    label: "Social Image", 
    description: "Instagram/Facebook story",
    icon: Image 
  },
  { 
    key: "sendViaEmail" as const, 
    label: "Send via Email", 
    description: "Email to recipients",
    icon: Mail 
  },
]

export function DeliverySection({
  viewInBrowser,
  downloadPdf,
  downloadSocialImage,
  sendViaEmail,
  emailRecipients,
  onChange,
  hasOption,
  stepNumber = 4,
}: DeliverySectionProps) {
  const values = { viewInBrowser, downloadPdf, downloadSocialImage, sendViaEmail }

  const toggleOption = (key: keyof typeof values) => {
    onChange({ [key]: !values[key] })
  }

  return (
    <section className={cn(
      "bg-white rounded-xl border transition-all duration-200",
      hasOption ? "border-gray-200 shadow-sm" : "border-gray-200/80 shadow-sm"
    )}>
      {/* Section Header */}
      <div className="flex items-center gap-3 px-5 py-4">
        <div className={cn(
          "w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold transition-colors",
          hasOption
            ? "bg-emerald-500 text-white"
            : "bg-amber-100 text-amber-600"
        )}>
          {hasOption ? <Check className="w-3.5 h-3.5" /> : stepNumber}
        </div>
        <h3 className="text-sm font-medium text-gray-900">Delivery Options</h3>
      </div>

      <div className="px-5 pb-5">
        {/* Delivery Options */}
        <div className="space-y-2">
          {DELIVERY_OPTIONS.map((option) => {
            const isChecked = values[option.key]
            const Icon = option.icon
            return (
              <button
                key={option.key}
                onClick={() => toggleOption(option.key)}
                className={cn(
                  "flex items-center gap-3 w-full p-3 rounded-xl border transition-all duration-150 text-left",
                  isChecked
                    ? "bg-primary/5 border-primary/20 shadow-sm"
                    : "bg-white border-gray-200 hover:bg-gray-50 hover:border-gray-300"
                )}
              >
                <div className={cn(
                  "w-5 h-5 rounded border-2 flex items-center justify-center transition-all",
                  isChecked
                    ? "bg-primary border-primary"
                    : "bg-white border-gray-300"
                )}>
                  {isChecked && <Check className="w-3 h-3 text-white" strokeWidth={3} />}
                </div>
                <div className={cn(
                  "w-8 h-8 rounded-lg flex items-center justify-center transition-colors",
                  isChecked ? "bg-primary/10" : "bg-gray-50"
                )}>
                  <Icon className={cn(
                    "w-4 h-4",
                    isChecked ? "text-primary" : "text-gray-400"
                  )} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className={cn(
                    "text-sm font-medium",
                    isChecked ? "text-foreground" : "text-gray-700"
                  )}>
                    {option.label}
                  </p>
                  <p className="text-xs text-gray-500">{option.description}</p>
                </div>
              </button>
            )
          })}
        </div>

        {!hasOption && (
          <p className="text-xs text-amber-600 mt-3 flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5" />
            Select at least one delivery option
          </p>
        )}
      </div>
    </section>
  )
}

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
}: DeliverySectionProps) {
  const values = { viewInBrowser, downloadPdf, downloadSocialImage, sendViaEmail }

  const toggleOption = (key: keyof typeof values) => {
    onChange({ [key]: !values[key] })
  }

  return (
    <section className="bg-white border border-gray-200 rounded-lg p-4">
      {/* Section Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-900">Delivery Options</h3>
        {hasOption ? (
          <div className="w-5 h-5 rounded-full bg-green-50 flex items-center justify-center">
            <Check className="w-3 h-3 text-green-500" />
          </div>
        ) : (
          <div className="w-5 h-5 rounded-full bg-amber-50 flex items-center justify-center">
            <AlertCircle className="w-3 h-3 text-amber-500" />
          </div>
        )}
      </div>

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
                "flex items-center gap-3 w-full p-3 rounded-lg border transition-colors text-left",
                isChecked
                  ? "bg-violet-50 border-violet-200"
                  : "bg-white border-gray-200 hover:bg-gray-50"
              )}
            >
              <div className={cn(
                "w-5 h-5 rounded border flex items-center justify-center transition-colors",
                isChecked
                  ? "bg-violet-600 border-violet-600"
                  : "bg-white border-gray-300"
              )}>
                {isChecked && <Check className="w-3 h-3 text-white" />}
              </div>
              <Icon className={cn(
                "w-4 h-4",
                isChecked ? "text-violet-600" : "text-gray-400"
              )} />
              <div className="flex-1 min-w-0">
                <p className={cn(
                  "text-sm font-medium",
                  isChecked ? "text-gray-900" : "text-gray-700"
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
        <p className="text-xs text-amber-600 mt-2">Select at least one delivery option</p>
      )}
    </section>
  )
}

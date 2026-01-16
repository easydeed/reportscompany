"use client"

import type React from "react"

import { useState } from "react"
import { Search, X, User } from "lucide-react"
import { cn } from "@/lib/utils"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import type { ReportBuilderState, EmailRecipient } from "@/components/report-builder"

interface DeliverySectionProps {
  state: ReportBuilderState
  updateState: <K extends keyof ReportBuilderState>(key: K, value: ReportBuilderState[K]) => void
}

const deliveryOptions = [
  {
    key: "viewInBrowser" as const,
    label: "View in Browser",
    description: "Open the interactive web report",
    icon: "🌐",
  },
  {
    key: "downloadPdf" as const,
    label: "Download PDF",
    description: "High-quality PDF for printing or sharing",
    icon: "📄",
  },
  {
    key: "downloadSocialImage" as const,
    label: "Download Social Image",
    description: "Instagram/Facebook story-sized image",
    icon: "📱",
  },
  {
    key: "sendViaEmail" as const,
    label: "Send via Email",
    description: "Email the report to specific recipients",
    icon: "📧",
  },
]

// Mock contacts for autocomplete
const mockContacts = [
  { id: "1", name: "John Smith", email: "john@client.com" },
  { id: "2", name: "Sarah Johnson", email: "sarah@example.com" },
  { id: "3", name: "Michael Brown", email: "michael@company.com" },
  { id: "4", name: "Emily Davis", email: "emily@mail.com" },
]

export function DeliverySection({ state, updateState }: DeliverySectionProps) {
  const [emailSearch, setEmailSearch] = useState("")
  const [showSuggestions, setShowSuggestions] = useState(false)

  const filteredContacts = mockContacts.filter(
    (contact) =>
      (contact.name.toLowerCase().includes(emailSearch.toLowerCase()) ||
        contact.email.toLowerCase().includes(emailSearch.toLowerCase())) &&
      !state.emailRecipients.some((r) => r.type === "contact" && r.id === contact.id),
  )

  const isValidEmail = (email: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)

  const handleAddContact = (contact: (typeof mockContacts)[0]) => {
    const newRecipient: EmailRecipient = {
      type: "contact",
      id: contact.id,
      name: contact.name,
      email: contact.email,
    }
    updateState("emailRecipients", [...state.emailRecipients, newRecipient])
    setEmailSearch("")
    setShowSuggestions(false)
  }

  const handleAddManualEmail = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && isValidEmail(emailSearch)) {
      if (!state.emailRecipients.some((r) => r.email === emailSearch)) {
        const newRecipient: EmailRecipient = {
          type: "manual_email",
          email: emailSearch,
        }
        updateState("emailRecipients", [...state.emailRecipients, newRecipient])
      }
      setEmailSearch("")
    }
  }

  const handleRemoveRecipient = (email: string) => {
    updateState(
      "emailRecipients",
      state.emailRecipients.filter((r) => r.email !== email),
    )
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">How would you like to use this report?</p>

      <div className="divide-y rounded-lg border">
        {deliveryOptions.map((option) => {
          const isChecked = state[option.key]

          return (
            <label
              key={option.key}
              className={cn(
                "flex cursor-pointer items-center gap-3 px-4 py-3 transition-colors hover:bg-muted/50",
                isChecked && "bg-violet-50",
              )}
            >
              <Checkbox
                checked={isChecked}
                onCheckedChange={(checked) => updateState(option.key, !!checked)}
                className="border-violet-500 data-[state=checked]:bg-violet-500 data-[state=checked]:text-white"
              />
              <div className="flex-1">
                <p className={cn("font-medium text-sm", isChecked && "text-violet-900")}>
                  {option.icon} {option.label}
                </p>
                <p className="text-xs text-muted-foreground">{option.description}</p>
              </div>
            </label>
          )
        })}
      </div>

      {state.sendViaEmail && (
        <div className="space-y-3 border-t pt-4">
          <Label className="text-sm font-medium text-muted-foreground">Email Recipients</Label>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={emailSearch}
              onChange={(e) => {
                setEmailSearch(e.target.value)
                setShowSuggestions(true)
              }}
              onFocus={() => setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              onKeyDown={handleAddManualEmail}
              placeholder="Search contacts or enter email..."
              className="pl-10"
            />

            {showSuggestions && emailSearch && (
              <div className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-lg border bg-popover shadow-lg">
                {filteredContacts.map((contact) => (
                  <button
                    key={contact.id}
                    onClick={() => handleAddContact(contact)}
                    className="flex w-full items-center gap-3 px-4 py-2 text-left text-sm hover:bg-muted"
                  >
                    <User className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{contact.name}</p>
                      <p className="text-xs text-muted-foreground">{contact.email}</p>
                    </div>
                  </button>
                ))}
                {isValidEmail(emailSearch) && !filteredContacts.length && (
                  <button
                    onClick={() => {
                      if (!state.emailRecipients.some((r) => r.email === emailSearch)) {
                        const newRecipient: EmailRecipient = {
                          type: "manual_email",
                          email: emailSearch,
                        }
                        updateState("emailRecipients", [...state.emailRecipients, newRecipient])
                      }
                      setEmailSearch("")
                    }}
                    className="flex w-full items-center gap-3 px-4 py-2 text-left text-sm hover:bg-muted"
                  >
                    <span>Add &ldquo;{emailSearch}&rdquo;</span>
                  </button>
                )}
              </div>
            )}
          </div>

          {state.emailRecipients.length > 0 && (
            <div className="space-y-2">
              {state.emailRecipients.map((recipient) => (
                <div
                  key={recipient.email}
                  className="flex items-center justify-between rounded-lg border bg-muted/30 px-4 py-2"
                >
                  <div className="flex items-center gap-3">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <div>
                      {recipient.type === "contact" && recipient.name && (
                        <p className="font-medium text-sm">{recipient.name}</p>
                      )}
                      <p className="text-sm text-muted-foreground">{recipient.email}</p>
                    </div>
                  </div>
                  <button onClick={() => handleRemoveRecipient(recipient.email)} className="rounded p-1 hover:bg-muted">
                    <X className="h-4 w-4 text-muted-foreground" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

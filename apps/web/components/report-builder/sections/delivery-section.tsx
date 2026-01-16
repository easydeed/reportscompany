"use client"

import { useState, useEffect } from "react"
import { Search, X, User, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import type { ReportBuilderState, EmailRecipient } from "../types"
import { DELIVERY_OPTIONS } from "../types"

interface DeliverySectionProps {
  viewInBrowser: boolean
  downloadPdf: boolean
  downloadSocialImage: boolean
  sendViaEmail: boolean
  emailRecipients: EmailRecipient[]
  onChange: (updates: Partial<ReportBuilderState>) => void
}

interface ApiContact {
  id: string
  name: string
  email: string | null
}

export function DeliverySection({
  viewInBrowser,
  downloadPdf,
  downloadSocialImage,
  sendViaEmail,
  emailRecipients,
  onChange,
}: DeliverySectionProps) {
  const [emailSearch, setEmailSearch] = useState("")
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [contacts, setContacts] = useState<ApiContact[]>([])
  const [loading, setLoading] = useState(false)

  // Fetch contacts on mount
  useEffect(() => {
    async function fetchContacts() {
      setLoading(true)
      try {
        const res = await fetch("/api/proxy/v1/contacts", { credentials: "include" })
        if (res.ok) {
          const data = await res.json()
          setContacts(data.contacts || data || [])
        }
      } catch (err) {
        console.error("Failed to fetch contacts:", err)
      } finally {
        setLoading(false)
      }
    }
    fetchContacts()
  }, [])

  const deliveryState: Record<string, boolean> = {
    viewInBrowser,
    downloadPdf,
    downloadSocialImage,
    sendViaEmail,
  }

  const filteredContacts = contacts.filter(
    (contact) =>
      contact.email &&
      (contact.name.toLowerCase().includes(emailSearch.toLowerCase()) ||
        contact.email.toLowerCase().includes(emailSearch.toLowerCase())) &&
      !emailRecipients.some((r) => r.type === "contact" && r.id === contact.id),
  )

  const isValidEmail = (email: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)

  const handleAddContact = (contact: ApiContact) => {
    if (!contact.email) return
    const newRecipient: EmailRecipient = {
      type: "contact",
      id: contact.id,
      name: contact.name,
      email: contact.email,
    }
    onChange({ emailRecipients: [...emailRecipients, newRecipient] })
    setEmailSearch("")
    setShowSuggestions(false)
  }

  const handleAddManualEmail = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && isValidEmail(emailSearch)) {
      if (!emailRecipients.some((r) => r.email === emailSearch)) {
        const newRecipient: EmailRecipient = {
          type: "manual_email",
          email: emailSearch,
        }
        onChange({ emailRecipients: [...emailRecipients, newRecipient] })
      }
      setEmailSearch("")
    }
  }

  const handleRemoveRecipient = (email: string) => {
    onChange({
      emailRecipients: emailRecipients.filter((r) => r.email !== email),
    })
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">How would you like to use this report?</p>

      <div className="divide-y rounded-lg border">
        {DELIVERY_OPTIONS.map((option) => {
          const isChecked = deliveryState[option.key]

          return (
            <label
              key={option.key}
              className={cn(
                "flex cursor-pointer items-center gap-3 px-4 py-3 transition-colors hover:bg-muted/50",
                isChecked && "bg-violet-50 dark:bg-violet-950/30",
              )}
            >
              <Checkbox
                checked={isChecked}
                onCheckedChange={(checked) => onChange({ [option.key]: !!checked })}
                className="border-violet-500 data-[state=checked]:bg-violet-500 data-[state=checked]:text-white"
              />
              <div className="flex-1">
                <p className={cn("font-medium text-sm", isChecked && "text-violet-900 dark:text-violet-100")}>
                  {option.icon} {option.label}
                </p>
                <p className="text-xs text-muted-foreground">{option.description}</p>
              </div>
            </label>
          )
        })}
      </div>

      {sendViaEmail && (
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
            {loading && <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-muted-foreground" />}

            {showSuggestions && emailSearch && (
              <div className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-lg border bg-popover shadow-lg">
                {filteredContacts.slice(0, 5).map((contact) => (
                  <button
                    key={contact.id}
                    onMouseDown={(e) => e.preventDefault()}
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
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => {
                      if (!emailRecipients.some((r) => r.email === emailSearch)) {
                        const newRecipient: EmailRecipient = {
                          type: "manual_email",
                          email: emailSearch,
                        }
                        onChange({ emailRecipients: [...emailRecipients, newRecipient] })
                      }
                      setEmailSearch("")
                    }}
                    className="flex w-full items-center gap-3 px-4 py-2 text-left text-sm hover:bg-muted"
                  >
                    <span>Add &ldquo;{emailSearch}&rdquo;</span>
                  </button>
                )}
                {filteredContacts.length === 0 && !isValidEmail(emailSearch) && (
                  <div className="px-3 py-2 text-sm text-muted-foreground">No contacts found</div>
                )}
              </div>
            )}
          </div>

          {emailRecipients.length > 0 && (
            <div className="space-y-2">
              {emailRecipients.map((recipient) => (
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


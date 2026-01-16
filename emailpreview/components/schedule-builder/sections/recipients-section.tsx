"use client"

import { useState } from "react"
import { Search, Users, User, X, AlertCircle, Plus } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { AccordionSection } from "../accordion-section"
import type { Recipient } from "@/lib/schedule-types"

interface RecipientsSectionProps {
  recipients: Recipient[]
  includeAttachment: boolean
  onRecipientsChange: (recipients: Recipient[]) => void
  onIncludeAttachmentChange: (value: boolean) => void
}

const SAMPLE_CONTACTS: Recipient[] = [
  { type: "contact", id: "1", name: "John Smith", email: "john@client.com" },
  { type: "contact", id: "2", name: "Sarah Johnson", email: "sarah@buyer.com" },
  { type: "contact", id: "3", name: "Mike Wilson", email: "mike@seller.com" },
]

const SAMPLE_GROUPS: Recipient[] = [
  { type: "group", id: "g1", name: "VIP Clients", memberCount: 12 },
  { type: "group", id: "g2", name: "First-Time Buyers", memberCount: 28 },
  { type: "group", id: "g3", name: "Active Investors", memberCount: 8 },
]

export function RecipientsSection({
  recipients,
  includeAttachment,
  onRecipientsChange,
  onIncludeAttachmentChange,
}: RecipientsSectionProps) {
  const [search, setSearch] = useState("")
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [manualEmail, setManualEmail] = useState("")

  const status = recipients.length > 0 ? "complete" : "warning"

  const getTotalEmails = () => {
    let total = 0
    recipients.forEach((r) => {
      if (r.type === "group") {
        total += r.memberCount
      } else {
        total += 1
      }
    })
    return total
  }

  const summary =
    recipients.length > 0 ? `${recipients.length} recipients (${getTotalEmails()} emails total)` : undefined

  const filteredContacts = SAMPLE_CONTACTS.filter(
    (c) =>
      c.type === "contact" &&
      (c.name.toLowerCase().includes(search.toLowerCase()) || c.email.toLowerCase().includes(search.toLowerCase())) &&
      !recipients.some((r) => r.type === "contact" && r.id === c.id),
  )

  const filteredGroups = SAMPLE_GROUPS.filter(
    (g) =>
      g.type === "group" &&
      g.name.toLowerCase().includes(search.toLowerCase()) &&
      !recipients.some((r) => r.type === "group" && r.id === g.id),
  )

  const addRecipient = (recipient: Recipient) => {
    onRecipientsChange([...recipients, recipient])
    setSearch("")
    setShowSuggestions(false)
  }

  const removeRecipient = (recipient: Recipient) => {
    onRecipientsChange(
      recipients.filter((r) => {
        if (r.type === "manual_email" && recipient.type === "manual_email") {
          return r.email !== recipient.email
        }
        if (r.type !== "manual_email" && recipient.type !== "manual_email") {
          return r.id !== recipient.id
        }
        return true
      }),
    )
  }

  const addManualEmail = () => {
    const email = manualEmail.trim()
    if (
      email &&
      /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) &&
      !recipients.some((r) => r.type === "manual_email" && r.email === email)
    ) {
      onRecipientsChange([...recipients, { type: "manual_email", email }])
      setManualEmail("")
    }
  }

  return (
    <AccordionSection
      id="recipients"
      title="Recipients"
      status={status}
      summary={summary}
      summaryIcon={summary ? <Users className="h-3.5 w-3.5" /> : undefined}
    >
      <div className="space-y-4">
        <label className="text-sm text-muted-foreground block">Who should receive this report?</label>

        {recipients.length === 0 && (
          <div className="flex items-center gap-2 text-sm text-amber-600 bg-amber-50 rounded-md p-3">
            <AlertCircle className="h-4 w-4" />
            Add at least one recipient to activate this schedule
          </div>
        )}

        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setShowSuggestions(true)
            }}
            onFocus={() => setShowSuggestions(true)}
            placeholder="Search contacts, groups, or enter email..."
            className="pl-9"
          />

          {showSuggestions && search && (
            <div className="absolute z-10 w-full mt-1 bg-popover border rounded-md shadow-lg max-h-64 overflow-auto">
              {filteredContacts.length > 0 && (
                <div>
                  <div className="px-3 py-1.5 text-xs font-medium text-muted-foreground bg-muted">Contacts</div>
                  {filteredContacts.map((contact) => (
                    <button
                      key={contact.id}
                      onClick={() => addRecipient(contact)}
                      className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-muted transition-colors"
                    >
                      <User className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="text-sm font-medium">{contact.type === "contact" && contact.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {contact.type === "contact" && contact.email}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {filteredGroups.length > 0 && (
                <div>
                  <div className="px-3 py-1.5 text-xs font-medium text-muted-foreground bg-muted">Groups</div>
                  {filteredGroups.map((group) => (
                    <button
                      key={group.id}
                      onClick={() => addRecipient(group)}
                      className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-muted transition-colors"
                    >
                      <Users className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="text-sm font-medium">{group.type === "group" && group.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {group.type === "group" && `${group.memberCount} members`}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {filteredContacts.length === 0 && filteredGroups.length === 0 && (
                <div className="px-3 py-2 text-sm text-muted-foreground">No results found</div>
              )}
            </div>
          )}
        </div>

        {/* Recipients List */}
        {recipients.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="h-px flex-1 bg-border" />
              <span className="text-xs text-muted-foreground font-medium">Added Recipients ({recipients.length})</span>
              <div className="h-px flex-1 bg-border" />
            </div>

            <div className="border rounded-lg divide-y">
              {recipients.map((recipient, index) => (
                <div
                  key={recipient.type === "manual_email" ? recipient.email : recipient.id}
                  className="flex items-center justify-between p-3"
                >
                  <div className="flex items-center gap-3">
                    {recipient.type === "group" ? (
                      <Users className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <User className="h-4 w-4 text-muted-foreground" />
                    )}
                    <div>
                      <div className="text-sm font-medium">
                        {recipient.type === "contact"
                          ? recipient.name
                          : recipient.type === "group"
                            ? recipient.name
                            : recipient.email}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {recipient.type === "contact"
                          ? `${recipient.email} · Contact`
                          : recipient.type === "group"
                            ? `${recipient.memberCount} members · Group`
                            : "Manual email"}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => removeRecipient(recipient)}
                    className="p-1 hover:bg-muted rounded transition-colors"
                  >
                    <X className="h-4 w-4 text-muted-foreground" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick Add */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <div className="h-px flex-1 bg-border" />
            <span className="text-xs text-muted-foreground font-medium">Quick Add</span>
            <div className="h-px flex-1 bg-border" />
          </div>

          <div className="flex gap-2 mb-3">
            <Button
              variant="outline"
              size="sm"
              className="gap-1 bg-transparent"
              onClick={() => {
                const available = SAMPLE_CONTACTS.find(
                  (c) => !recipients.some((r) => r.type === "contact" && r.id === c.id),
                )
                if (available) addRecipient(available)
              }}
            >
              <Plus className="h-3 w-3" />
              Add Contact
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-1 bg-transparent"
              onClick={() => {
                const available = SAMPLE_GROUPS.find(
                  (g) => !recipients.some((r) => r.type === "group" && r.id === g.id),
                )
                if (available) addRecipient(available)
              }}
            >
              <Plus className="h-3 w-3" />
              Add Group
            </Button>
          </div>

          <div className="flex gap-2">
            <Input
              value={manualEmail}
              onChange={(e) => setManualEmail(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault()
                  addManualEmail()
                }
              }}
              placeholder="Enter email manually..."
              className="flex-1"
            />
            <Button variant="outline" size="sm" onClick={addManualEmail} disabled={!manualEmail.trim()}>
              Add
            </Button>
          </div>
        </div>

        {/* Attachment Toggle */}
        <div className="flex items-center gap-2 pt-2">
          <Checkbox
            id="attachment"
            checked={includeAttachment}
            onCheckedChange={(checked) => onIncludeAttachmentChange(checked === true)}
          />
          <label htmlFor="attachment" className="text-sm text-muted-foreground cursor-pointer">
            Include PDF attachment (in addition to email preview)
          </label>
        </div>
      </div>
    </AccordionSection>
  )
}

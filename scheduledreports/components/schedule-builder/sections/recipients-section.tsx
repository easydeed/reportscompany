"use client"

import { useState } from "react"
import { Search, X, User, Users, AlertCircle, Plus } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { AccordionSection } from "../accordion-section"
import type { Recipient, ScheduleBuilderState, SectionStatus } from "../types"

interface RecipientsSectionProps {
  recipients: Recipient[]
  includeAttachment: boolean
  onChange: (updates: Partial<ScheduleBuilderState>) => void
  isExpanded: boolean
  onToggle: () => void
}

// Mock data for demonstration
const mockContacts = [
  { id: "1", name: "John Smith", email: "john@client.com" },
  { id: "2", name: "Sarah Johnson", email: "sarah@buyer.com" },
  { id: "3", name: "Mike Williams", email: "mike@seller.com" },
  { id: "4", name: "Emily Brown", email: "emily@investor.com" },
]

const mockGroups = [
  { id: "g1", name: "VIP Clients", memberCount: 12 },
  { id: "g2", name: "Newsletter Subscribers", memberCount: 245 },
  { id: "g3", name: "Active Buyers", memberCount: 34 },
]

export function RecipientsSection({
  recipients,
  includeAttachment,
  onChange,
  isExpanded,
  onToggle,
}: RecipientsSectionProps) {
  const [search, setSearch] = useState("")
  const [showDropdown, setShowDropdown] = useState(false)
  const [manualEmail, setManualEmail] = useState("")

  const status: SectionStatus = recipients.length > 0 ? "complete" : "warning"

  const totalEmails = recipients.reduce((sum, r) => {
    if (r.type === "group") return sum + r.memberCount
    return sum + 1
  }, 0)

  const summary =
    recipients.length > 0
      ? `👥 ${recipients.length} recipient${recipients.length !== 1 ? "s" : ""} (${totalEmails} email${totalEmails !== 1 ? "s" : ""} total)`
      : undefined

  const filteredContacts = mockContacts.filter(
    (c) =>
      (c.name.toLowerCase().includes(search.toLowerCase()) || c.email.toLowerCase().includes(search.toLowerCase())) &&
      !recipients.some((r) => r.type === "contact" && r.id === c.id),
  )

  const filteredGroups = mockGroups.filter(
    (g) =>
      g.name.toLowerCase().includes(search.toLowerCase()) &&
      !recipients.some((r) => r.type === "group" && r.id === g.id),
  )

  const addContact = (contact: (typeof mockContacts)[0]) => {
    onChange({
      recipients: [...recipients, { type: "contact", id: contact.id, name: contact.name, email: contact.email }],
    })
    setSearch("")
    setShowDropdown(false)
  }

  const addGroup = (group: (typeof mockGroups)[0]) => {
    onChange({
      recipients: [...recipients, { type: "group", id: group.id, name: group.name, memberCount: group.memberCount }],
    })
    setSearch("")
    setShowDropdown(false)
  }

  const addManualEmail = () => {
    const email = manualEmail.trim()
    if (email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      if (!recipients.some((r) => r.type === "manual_email" && r.email === email)) {
        onChange({
          recipients: [...recipients, { type: "manual_email", email }],
        })
      }
      setManualEmail("")
    }
  }

  const removeRecipient = (index: number) => {
    onChange({ recipients: recipients.filter((_, i) => i !== index) })
  }

  return (
    <AccordionSection title="Recipients" summary={summary} status={status} isExpanded={isExpanded} onToggle={onToggle}>
      <div className="space-y-4">
        <label className="text-sm text-muted-foreground">Who should receive this report?</label>

        {recipients.length === 0 && (
          <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
            <AlertCircle className="h-4 w-4" />
            Add at least one recipient to activate this schedule
          </div>
        )}

        {/* Search Input */}
        <div className="relative">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setShowDropdown(true)
              }}
              onFocus={() => setShowDropdown(true)}
              placeholder="Search contacts, groups, or enter email..."
              className="pl-9"
            />
          </div>

          {showDropdown && search && (
            <div className="absolute z-10 mt-1 max-h-64 w-full overflow-auto rounded-lg border bg-background shadow-lg">
              {filteredContacts.length > 0 && (
                <div>
                  <div className="px-3 py-1.5 text-xs font-medium text-muted-foreground">Contacts</div>
                  {filteredContacts.map((contact) => (
                    <button
                      key={contact.id}
                      onClick={() => addContact(contact)}
                      className="flex w-full items-center gap-3 px-3 py-2 text-left hover:bg-muted"
                    >
                      <User className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="text-sm font-medium">{contact.name}</div>
                        <div className="text-xs text-muted-foreground">{contact.email}</div>
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {filteredGroups.length > 0 && (
                <div>
                  <div className="px-3 py-1.5 text-xs font-medium text-muted-foreground">Groups</div>
                  {filteredGroups.map((group) => (
                    <button
                      key={group.id}
                      onClick={() => addGroup(group)}
                      className="flex w-full items-center gap-3 px-3 py-2 text-left hover:bg-muted"
                    >
                      <Users className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="text-sm font-medium">{group.name}</div>
                        <div className="text-xs text-muted-foreground">{group.memberCount} members</div>
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {filteredContacts.length === 0 && filteredGroups.length === 0 && (
                <div className="px-3 py-2 text-sm text-muted-foreground">
                  No results found. Add as email manually below.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Added Recipients */}
        {recipients.length > 0 && (
          <div>
            <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
              <div className="h-px flex-1 bg-border" />
              <span>Added Recipients ({recipients.length})</span>
              <div className="h-px flex-1 bg-border" />
            </div>
            <div className="space-y-2">
              {recipients.map((recipient, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between rounded-lg border bg-background px-3 py-2"
                >
                  <div className="flex items-center gap-3">
                    {recipient.type === "group" ? (
                      <Users className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <User className="h-4 w-4 text-muted-foreground" />
                    )}
                    <div>
                      <div className="text-sm font-medium">
                        {recipient.type === "manual_email" ? recipient.email : recipient.name}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {recipient.type === "contact" && `${recipient.email} · Contact`}
                        {recipient.type === "group" && `${recipient.memberCount} members · Group`}
                        {recipient.type === "manual_email" && "Manual email"}
                      </div>
                    </div>
                  </div>
                  <button onClick={() => removeRecipient(index)} className="rounded p-1 hover:bg-muted">
                    <X className="h-4 w-4 text-muted-foreground" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick Add */}
        <div>
          <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
            <div className="h-px flex-1 bg-border" />
            <span>Quick Add</span>
            <div className="h-px flex-1 bg-border" />
          </div>
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Input
                value={manualEmail}
                onChange={(e) => setManualEmail(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && addManualEmail()}
                placeholder="Enter email address..."
                type="email"
              />
            </div>
            <Button variant="outline" size="sm" onClick={addManualEmail} disabled={!manualEmail.trim()}>
              <Plus className="mr-1 h-4 w-4" />
              Add
            </Button>
          </div>
        </div>

        {/* Attachment Toggle */}
        <div className="flex items-center gap-2 pt-2">
          <Checkbox
            id="attachment"
            checked={includeAttachment}
            onCheckedChange={(checked) => onChange({ includeAttachment: checked as boolean })}
          />
          <label htmlFor="attachment" className="text-sm text-muted-foreground cursor-pointer">
            Include PDF attachment (in addition to email preview)
          </label>
        </div>
      </div>
    </AccordionSection>
  )
}

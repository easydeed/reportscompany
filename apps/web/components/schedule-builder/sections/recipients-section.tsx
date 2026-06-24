"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Search, X, Users, Mail, AlertCircle, Check, AtSign, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"
import { Input } from "@/components/ui/input"
import type { Recipient } from "@/lib/types/recipients"

interface RecipientsSectionProps {
  recipients: Recipient[]
  onChange: (recipients: Recipient[]) => void
  hasRecipients: boolean
  stepNumber?: number
  title?: string
  emptyMessage?: string
}

const isValidEmail = (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)

export function RecipientsSection({
  recipients,
  onChange,
  hasRecipients,
  stepNumber = 6,
  title = "Recipients",
  emptyMessage = "Select at least one recipient",
}: RecipientsSectionProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [emailInput, setEmailInput] = useState("")
  const [emailError, setEmailError] = useState("")
  const [contacts, setContacts] = useState<any[]>([])
  const [groups, setGroups] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const [contactsRes, groupsRes] = await Promise.all([
          fetch("/api/proxy/v1/contacts"),
          fetch("/api/proxy/v1/contact-groups"),
        ])
        
        if (contactsRes.ok) {
          const data = await contactsRes.json()
          setContacts((data.contacts || []).filter((c: any) => c.email))
        }
        if (groupsRes.ok) {
          const data = await groupsRes.json()
          setGroups(data.groups || [])
        }
      } catch (error) {
        console.error("Failed to load contacts:", error)
      } finally {
        setIsLoading(false)
      }
    }
    loadData()
  }, [])

  const filteredContacts = contacts.filter(c =>
    !searchQuery || 
    c.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.email?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const isContactSelected = (id: string) => recipients.some(r => r.type === "contact" && r.id === id)
  const isGroupSelected = (id: string) => recipients.some(r => r.type === "group" && r.id === id)

  const toggleContact = (contact: any) => {
    if (isContactSelected(contact.id)) {
      onChange(recipients.filter(r => !(r.type === "contact" && r.id === contact.id)))
    } else {
      onChange([
        ...recipients,
        {
          type: "contact", 
          id: contact.id, 
          name: contact.name, 
          email: contact.email 
        },
      ])
    }
  }

  const toggleGroup = (group: any) => {
    if (isGroupSelected(group.id)) {
      onChange(recipients.filter(r => !(r.type === "group" && r.id === group.id)))
    } else {
      onChange([
        ...recipients,
        {
          type: "group", 
          id: group.id, 
          name: group.name, 
          memberCount: group.member_count || 0 
        },
      ])
    }
  }

  const removeRecipient = (recipient: Recipient) => {
    onChange(
      recipients.filter(r =>
        !(r.type === recipient.type && 
          ((r.type === "manual_email" && recipient.type === "manual_email" && r.email === recipient.email) ||
           ((r as any).id === (recipient as any).id)))
      )
    )
  }

  const isEmailAlreadyAdded = (email: string) =>
    recipients.some(r => r.type === "manual_email" && r.email === email) ||
    recipients.some(r => r.type === "contact" && r.email === email)

  const addManualEmail = () => {
    const trimmed = emailInput.trim().toLowerCase()
    if (!trimmed) return
    if (!isValidEmail(trimmed)) {
      setEmailError("Enter a valid email address")
      return
    }
    if (isEmailAlreadyAdded(trimmed)) {
      setEmailError("Already added")
      return
    }
    setEmailError("")
    onChange([...recipients, { type: "manual_email", email: trimmed }])
    setEmailInput("")
  }

  const contactCount = recipients.filter(r => r.type === "contact").length
  const groupCount = recipients.filter(r => r.type === "group").length
  const manualCount = recipients.filter(r => r.type === "manual_email").length

  // Show a sphere-building nudge when the user genuinely has nobody to send to
  // yet: no contacts at all, and any group(s) they have (e.g. a freshly-seeded
  // "My Sphere") are empty. Hides once they have a contact or a populated group.
  const hasPopulatedGroup = groups.some((g) => (g.member_count || 0) > 0)
  const showSphereNudge = !isLoading && contacts.length === 0 && !hasPopulatedGroup

  return (
    <section className={cn(
      "bg-white rounded-xl border transition-all duration-200",
      hasRecipients ? "border-gray-200 shadow-sm" : "border-gray-200/80 shadow-sm"
    )}>
      <div className="flex items-center gap-3 px-5 py-4">
        <div className={cn(
          "w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold transition-colors",
          hasRecipients
            ? "bg-emerald-500 text-white"
            : "bg-amber-100 text-amber-600"
        )}>
          {hasRecipients ? <Check className="w-3.5 h-3.5" /> : stepNumber}
        </div>
        <h3 className="text-sm font-medium text-gray-900">{title}</h3>
      </div>

      <div className="px-5 pb-5">
        {recipients.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {recipients.map((r, i) => (
              <span 
                key={i}
                className={cn(
                  "inline-flex items-center gap-1 px-2 py-1 rounded text-sm",
                  r.type === "manual_email"
                    ? "bg-indigo-50 text-indigo-600"
                    : "bg-primary/10 text-primary"
                )}
              >
                {r.type === "group" ? <Users className="w-3 h-3" /> : r.type === "manual_email" ? <AtSign className="w-3 h-3" /> : <Mail className="w-3 h-3" />}
                {r.type === "manual_email" ? r.email : r.name}
                {r.type === "group" && ` (${r.memberCount})`}
                <button onClick={() => removeRecipient(r)} className="opacity-60 hover:opacity-100">
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        )}

        <div className="mb-3 space-y-2">
          <div className="relative">
            <AtSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              value={emailInput}
              onChange={(e) => { setEmailInput(e.target.value); setEmailError("") }}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === ",") {
                  e.preventDefault()
                  addManualEmail()
                }
              }}
              placeholder="Type an email address and press Enter"
              className="pl-9 pr-16"
              type="email"
            />
            {emailInput.trim() && (
              <button
                onClick={addManualEmail}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-medium text-primary hover:text-primary/80 px-2 py-1"
              >
                Add
              </button>
            )}
          </div>
          {emailError && (
            <p className="text-xs text-red-500">{emailError}</p>
          )}

          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search contacts..."
              className="pl-9"
            />
          </div>
        </div>

        {isLoading ? (
          <div className="py-4 text-center text-sm text-gray-400">Loading...</div>
        ) : (
          <div className="space-y-3">
            {groups.length > 0 && (
              <div>
                <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
                  <Users className="w-3 h-3" />
                  Groups ({groupCount}/{groups.length})
                </p>
                <div className="max-h-24 overflow-auto border border-gray-200 rounded-lg divide-y divide-gray-100">
                  {groups.map((group) => {
                    const selected = isGroupSelected(group.id)
                    return (
                      <button
                        key={group.id}
                        onClick={() => toggleGroup(group)}
                        className={cn(
                          "flex items-center gap-2 w-full px-3 py-2 text-left transition-colors",
                          selected ? "bg-primary/5" : "hover:bg-gray-50"
                        )}
                      >
                        <div className={cn(
                          "w-4 h-4 rounded border-2 flex items-center justify-center",
                          selected ? "bg-primary border-primary" : "border-gray-300"
                        )}>
                          {selected && <Check className="w-2.5 h-2.5 text-white" />}
                        </div>
                        <Users className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-700 flex-1">{group.name}</span>
                        <span className="text-xs text-gray-400">{group.member_count || 0}</span>
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            {filteredContacts.length > 0 && (
              <div>
                <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
                  <Mail className="w-3 h-3" />
                  Contacts ({contactCount}/{contacts.length})
                </p>
                <div className="max-h-32 overflow-auto border border-gray-200 rounded-lg divide-y divide-gray-100">
                  {filteredContacts.slice(0, 20).map((contact) => {
                    const selected = isContactSelected(contact.id)
                    return (
                      <button
                        key={contact.id}
                        onClick={() => toggleContact(contact)}
                        className={cn(
                          "flex items-center gap-2 w-full px-3 py-2 text-left transition-colors",
                          selected ? "bg-primary/5" : "hover:bg-gray-50"
                        )}
                      >
                        <div className={cn(
                          "w-4 h-4 rounded border-2 flex items-center justify-center",
                          selected ? "bg-primary border-primary" : "border-gray-300"
                        )}>
                          {selected && <Check className="w-2.5 h-2.5 text-white" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-gray-700 truncate">{contact.name}</p>
                          <p className="text-xs text-gray-400 truncate">{contact.email}</p>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            {showSphereNudge && (
              <div className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-3">
                <p className="text-sm font-medium text-gray-900">
                  Build your sphere once, reach them every time.
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Add your people or import them from a file, then send to your whole sphere in one click.
                </p>
                <Link
                  href="/app/people"
                  className="inline-flex items-center gap-1 mt-2 text-sm font-medium text-primary hover:text-primary/80"
                >
                  Add people to My Sphere
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            )}

            {!showSphereNudge && filteredContacts.length === 0 && groups.length === 0 && (
              <p className="py-4 text-center text-sm text-gray-400">No contacts found</p>
            )}
          </div>
        )}

        {!hasRecipients && (
          <p className="text-xs text-amber-600 mt-3 flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5" />
            {emptyMessage}
          </p>
        )}
      </div>
    </section>
  )
}

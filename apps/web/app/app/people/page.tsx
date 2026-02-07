"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import {
  UserPlus,
  Mail,
  Trash2,
  Users,
  Shield,
  Pencil,
  Search,
  Upload,
  FolderPlus,
  Building2,
  UserCheck,
  MoreHorizontal,
  ChevronRight,
  Sparkles,
  Filter,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useContacts, useContactGroups, useAffiliateOverview, useInvalidate } from "@/hooks/use-api"
import { cn } from "@/lib/utils"
import { PageHeader } from "@/components/page-header"

type Contact = {
  id: string
  name: string
  email: string | null
  type: "client" | "list" | "agent" | "group"
  phone?: string | null
  notes?: string | null
  created_at: string
  groups?: Array<{ id: string; name: string }>
}

type SponsoredAccount = {
  account_id: string
  name: string
  plan_slug: string
  reports_this_month: number
  last_report_at: string | null
  groups?: Array<{ id: string; name: string }>
}

type Person = {
  id: string
  name: string
  email: string
  type: string
  displayType: string
  lastActivity?: string
  reportsThisMonth?: number
  groups?: Array<{ id: string; name: string }>
  kind: "contact" | "sponsored_agent"
}

type ContactGroup = {
  id: string
  name: string
  description?: string | null
  member_count: number
  created_at?: string
  updated_at?: string
}

export default function PeoplePage() {
  // React Query hooks for data fetching
  const { data: contactsData, isLoading: contactsLoading } = useContacts()
  const { data: groupsData, isLoading: groupsLoading } = useContactGroups()
  const { data: affiliateData, isError: affiliateError } = useAffiliateOverview()
  const invalidate = useInvalidate()

  // Derive state from React Query data
  const contacts: Contact[] = contactsData?.contacts || []
  const groups: ContactGroup[] = groupsData?.groups || []
  const sponsoredAccounts: SponsoredAccount[] = affiliateData?.sponsored_accounts || []
  const isAffiliate = !affiliateError && !!affiliateData
  const loading = contactsLoading

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [editingContact, setEditingContact] = useState<Contact | null>(null)
  const [editSponsoredDialogOpen, setEditSponsoredDialogOpen] = useState(false)
  const [editingSponsoredAgent, setEditingSponsoredAgent] = useState<SponsoredAccount | null>(null)
  const [sponsoredEditForm, setSponsoredEditForm] = useState({
    phone: "",
    notes: "",
    isSponsored: true,
  })
  const [groupDialogOpen, setGroupDialogOpen] = useState(false)
  const [groupForm, setGroupForm] = useState({ name: "", description: "" })
  const [addToGroupDialogOpen, setAddToGroupDialogOpen] = useState(false)
  const [selectedPersonForGroup, setSelectedPersonForGroup] = useState<Person | null>(null)
  const [selectedGroupIds, setSelectedGroupIds] = useState<string[]>([])
  const [importDialogOpen, setImportDialogOpen] = useState(false)
  const [importing, setImporting] = useState(false)
  const [importSummary, setImportSummary] = useState<{
    created_contacts: number
    created_groups: number
    errors: { row: number; reason: string }[]
  } | null>(null)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [filterType, setFilterType] = useState<"all" | "agents" | "groups" | "sponsored_agents">("all")
  const [selectedPeopleIds, setSelectedPeopleIds] = useState<string[]>([])
  const [activeGroup, setActiveGroup] = useState<ContactGroup | null>(null)
  const [groupDetailMembers, setGroupDetailMembers] = useState<any[]>([])
  const [loadingMembers, setLoadingMembers] = useState(false)
  const [addMembersOpen, setAddMembersOpen] = useState(false)
  const [selectedMemberIds, setSelectedMemberIds] = useState<string[]>([])
  const [manageGroupsContact, setManageGroupsContact] = useState<Contact | null>(null)
  const [manageGroupsDialogOpen, setManageGroupsDialogOpen] = useState(false)
  const { toast} = useToast()

  // Form state
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    type: "" as "" | "client" | "list" | "agent" | "group",
    phone: "",
    notes: "",
  })

  const [editFormData, setEditFormData] = useState({
    name: "",
    email: "",
    type: "client" as "client" | "list" | "agent" | "group",
    phone: "",
    notes: "",
  })

  /** Invalidate both contacts and groups to refresh all data */
  function refreshAll() {
    invalidate.contacts()
  }

  async function handleAddContact() {
    // Validate based on type
    if (!formData.type) {
      toast({
        title: "Error",
        description: "Please select a contact type",
        variant: "destructive",
      })
      return
    }
    
    if (!formData.name) {
      toast({
        title: "Error",
        description: "Name is required",
        variant: "destructive",
      })
      return
    }
    
    if (formData.type === "agent" && !formData.email) {
      toast({
        title: "Error",
        description: "Email is required for agent contacts",
        variant: "destructive",
      })
      return
    }

    try {
      // Build payload based on type
      const payload: any = {
        name: formData.name,
        type: formData.type,
        notes: formData.notes || null,
      }
      
      // Add email if provided (required for agent)
      if (formData.email) {
        payload.email = formData.email
      }
      
      // Add phone if provided (for agent)
      if (formData.phone) {
        payload.phone = formData.phone
      }
      
      const res = await fetch("/api/proxy/v1/contacts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || "Failed to create contact")
      }

      toast({
        title: "Success",
        description: `Added ${formData.name} to your contacts`,
      })

      setDialogOpen(false)
      setFormData({ name: "", email: "", type: "", phone: "", notes: "" })
      refreshAll()
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to add contact",
        variant: "destructive",
      })
    }
  }

  async function handleUpdateContact() {
    if (!editingContact) return

    if (!editFormData.name || !editFormData.email) {
      toast({
        title: "Error",
        description: "Name and email are required",
        variant: "destructive",
      })
      return
    }

    try {
      const res = await fetch(`/api/proxy/v1/contacts/${editingContact.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editFormData),
      })

      if (!res.ok) {
        const error = await res.json().catch(() => null)
        throw new Error(error?.detail || "Failed to update contact")
      }

      toast({
        title: "Success",
        description: `Updated ${editFormData.name}`,
      })

      setEditDialogOpen(false)
      setEditingContact(null)
      refreshAll()
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update contact",
        variant: "destructive",
      })
    }
  }

  async function handleDeleteContact(id: string, name: string) {
    if (!confirm(`Delete ${name}?`)) return

    try {
      const res = await fetch(`/api/proxy/v1/contacts/${id}`, { method: "DELETE" })
      if (!res.ok) throw new Error("Failed to delete contact")

      toast({
        title: "Success",
        description: `Deleted ${name}`,
      })
      refreshAll()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete contact",
        variant: "destructive",
      })
    }
  }

  async function handleUnsponsorAgent() {
    if (!editingSponsoredAgent) return
    
    if (!confirm(
      `Remove sponsorship from ${editingSponsoredAgent.name}? They will become an independent account with a free plan.`
    )) return

    try {
      const res = await fetch(
        `/api/proxy/v1/affiliate/accounts/${editingSponsoredAgent.account_id}/unsponsor`,
        { method: "POST" }
      )
      
      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || "Failed to unsponsor agent")
      }

      toast({
        title: "Success",
        description: `${editingSponsoredAgent.name} is now independent`,
      })
      
      setEditSponsoredDialogOpen(false)
      setEditingSponsoredAgent(null)
      refreshAll()
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to unsponsor agent",
        variant: "destructive",
      })
    }
  }

  async function handleCreateGroup() {
    if (!groupForm.name.trim()) {
      toast({
        title: "Error",
        description: "Group name is required",
        variant: "destructive",
      })
      return
    }

    try {
      const res = await fetch("/api/proxy/v1/contact-groups", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: groupForm.name.trim(),
          description: groupForm.description.trim() || null,
        }),
      })

      if (!res.ok) {
        const error = await res.json().catch(() => null)
        throw new Error(error?.detail || "Failed to create group")
      }

      toast({
        title: "Success",
        description: `Created group "${groupForm.name}"`,
      })

      setGroupDialogOpen(false)
      setGroupForm({ name: "", description: "" })
      refreshAll()
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create group",
        variant: "destructive",
      })
    }
  }

  async function handleAddPersonToGroups() {
    if (!selectedPersonForGroup || selectedGroupIds.length === 0) {
      toast({
        title: "Error",
        description: "Select at least one group",
        variant: "destructive",
      })
      return
    }

    const member_type = selectedPersonForGroup.type === "sponsored_agent" ? "sponsored_agent" : "contact"
    const member_id = selectedPersonForGroup.id

    try {
      for (const groupId of selectedGroupIds) {
        await fetch(`/api/proxy/v1/contact-groups/${groupId}/members`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            members: [{ member_type, member_id }],
          }),
        })
      }

      toast({
        title: "Success",
        description: `${selectedPersonForGroup.name} added to ${selectedGroupIds.length} group(s)`,
      })

      setAddToGroupDialogOpen(false)
      setSelectedPersonForGroup(null)
      setSelectedGroupIds([])
      refreshAll()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to add to group(s)",
        variant: "destructive",
      })
    }
  }

  async function handleImportContacts() {
    if (!importFile) {
      toast({
        title: "Error",
        description: "Please select a CSV file to import",
        variant: "destructive",
      })
      return
    }

    const formData = new FormData()
    formData.append("file", importFile)

    setImporting(true)
    try {
      const res = await fetch("/api/proxy/v1/contacts/import", {
        method: "POST",
        body: formData,
      })

      if (!res.ok) {
        const text = await res.text().catch(() => "")
        throw new Error(text || "Import failed")
      }

      const summary = await res.json()
      setImportSummary(summary)

      toast({
        title: "Import completed",
        description: `Created ${summary.created_contacts} contacts and ${summary.created_groups} groups`,
      })

      refreshAll()
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to import contacts",
        variant: "destructive",
      })
    } finally {
      setImporting(false)
    }
  }

  // Group Detail Functions
  async function loadGroupMembers(groupId: string) {
    setLoadingMembers(true)
    try {
      const res = await fetch(`/api/proxy/v1/contact-groups/${groupId}`, { cache: "no-store" })
      if (res.ok) {
        const data = await res.json()
        setGroupDetailMembers(data.members || [])
      }
    } catch (error) {
      console.error("Failed to load group members:", error)
      toast({
        title: "Error",
        description: "Failed to load group members",
        variant: "destructive",
      })
    } finally {
      setLoadingMembers(false)
    }
  }

  async function handleRemoveMemberFromGroup(groupId: string, memberType: string, memberId: string, memberName: string) {
    if (!confirm(`Remove ${memberName} from this group?`)) return

    try {
      const res = await fetch(`/api/proxy/v1/contact-groups/${groupId}/members`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ member_type: memberType, member_id: memberId }),
      })

      if (!res.ok) throw new Error("Failed to remove member")

      toast({
        title: "Success",
        description: `${memberName} removed from group`,
      })

      await loadGroupMembers(groupId)
      refreshAll()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to remove member from group",
        variant: "destructive",
      })
    }
  }

  async function handleAddMembersToGroup(groupId: string) {
    if (selectedMemberIds.length === 0) {
      toast({
        title: "Error",
        description: "Please select at least one person to add",
        variant: "destructive",
      })
      return
    }

    try {
      // Build members array from selected IDs
      const members = selectedMemberIds.map((id) => {
        // Check if it's a contact
        const contact = contacts.find((c) => c.id === id)
        if (contact) {
          return { member_type: "contact", member_id: id }
        }
        // Otherwise it's a sponsored agent
        return { member_type: "sponsored_agent", member_id: id }
      })

      const res = await fetch(`/api/proxy/v1/contact-groups/${groupId}/members`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ members }),
      })

      if (!res.ok) throw new Error("Failed to add members")

      toast({
        title: "Success",
        description: `Added ${selectedMemberIds.length} member(s) to group`,
      })

      setAddMembersOpen(false)
      setSelectedMemberIds([])
      await loadGroupMembers(groupId)
      refreshAll()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to add members to group",
        variant: "destructive",
      })
    }
  }

  // Manage Groups Per Contact Functions
  async function handleRemoveContactFromGroup(contactId: string, groupId: string, groupName: string) {
    if (!confirm(`Remove this contact from "${groupName}"?`)) return

    try {
      const res = await fetch(`/api/proxy/v1/contact-groups/${groupId}/members`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ member_type: "contact", member_id: contactId }),
      })

      if (!res.ok) throw new Error("Failed to remove from group")

      toast({
        title: "Success",
        description: `Removed from ${groupName}`,
      })

      refreshAll()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to remove from group",
        variant: "destructive",
      })
    }
  }

  async function handleAddContactToGroupsFromManage(contactId: string) {
    if (selectedGroupIds.length === 0) {
      toast({
        title: "Error",
        description: "Please select at least one group",
        variant: "destructive",
      })
      return
    }

    try {
      for (const groupId of selectedGroupIds) {
        await fetch(`/api/proxy/v1/contact-groups/${groupId}/members`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            members: [{ member_type: "contact", member_id: contactId }],
          }),
        })
      }

      toast({
        title: "Success",
        description: `Added to ${selectedGroupIds.length} group(s)`,
      })

      setSelectedGroupIds([])
      refreshAll()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to add to groups",
        variant: "destructive",
      })
    }
  }

  // Combine contacts and sponsored accounts into unified list
  const allPeople: Person[] = [
    ...contacts.map((c) => ({
      id: c.id,
      name: c.name,
      email: c.email || "",
      type: c.type,
      displayType: 
        c.type === "client" ? "Client" : 
        c.type === "list" ? "List" : 
        c.type === "group" ? "Group" :
        "Agent",
      lastActivity: undefined,
      reportsThisMonth: undefined,
      groups: c.groups || [],
      kind: "contact" as const,
    })),
    ...sponsoredAccounts.map((s) => ({
      id: s.account_id,
      name: s.name,
      email: "", // Sponsored accounts don't have a direct email in this view
      type: "sponsored_agent",
      displayType: "Agent (Sponsored)",
      lastActivity: s.last_report_at || undefined,
      reportsThisMonth: s.reports_this_month,
      groups: s.groups || [],
      kind: "sponsored_agent" as const,
    })),
  ]

  // Apply search filter
  const searchFiltered = allPeople.filter((person) => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      person.name.toLowerCase().includes(query) ||
      person.email.toLowerCase().includes(query)
    )
  })

  // Apply type filter
  const people = searchFiltered.filter((person) => {
    if (filterType === "all") return true
    if (filterType === "agents") return person.type === "agent" || person.kind === "sponsored_agent"
    if (filterType === "groups") return person.type === "group"
    if (filterType === "sponsored_agents") return person.kind === "sponsored_agent"
    return true
  })

  // Badge color helper
  function getTypeBadgeClasses(type: string, kind: string) {
    if (kind === "sponsored_agent") return "bg-primary/10 text-primary border-primary/20"
    switch (type) {
      case "agent": return "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/30 dark:text-blue-400 dark:border-blue-800"
      case "client": return "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:border-emerald-800"
      case "group": return "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/30 dark:text-purple-400 dark:border-purple-800"
      case "list": return "bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-950/30 dark:text-orange-400 dark:border-orange-800"
      default: return "bg-muted text-muted-foreground"
    }
  }

  // Avatar initial helper
  function getInitials(name: string) {
    return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2)
  }

  function getAvatarColor(name: string) {
    const colors = [
      "bg-blue-500", "bg-emerald-500", "bg-purple-500", "bg-orange-500",
      "bg-pink-500", "bg-indigo-500", "bg-cyan-500", "bg-rose-500"
    ]
    const index = name.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0) % colors.length
    return colors[index]
  }

  return (
    <div className="space-y-5">
      {/* Modern Header */}
      <PageHeader
        title="My Contacts"
        description={
          isAffiliate
            ? "Manage your sponsored agents and client contacts"
            : "Manage your client contacts and recipients"
        }
        action={
          <div className="flex gap-2">
            <Dialog open={importDialogOpen} onOpenChange={setImportDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="gap-1.5">
                  <Upload className="h-3.5 w-3.5" />
                  Import
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Import Contacts from CSV</DialogTitle>
                  <DialogDescription>
                    Upload a CSV file with columns: <code className="px-1 py-0.5 bg-muted rounded text-xs">name</code>, <code className="px-1 py-0.5 bg-muted rounded text-xs">email</code>, optional{" "}
                    <code className="px-1 py-0.5 bg-muted rounded text-xs">type</code>, and optional <code className="px-1 py-0.5 bg-muted rounded text-xs">group</code>.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="import-file">CSV File</Label>
                    <Input
                      id="import-file"
                      type="file"
                      accept=".csv"
                      onChange={(e) => {
                        const file = e.target.files?.[0]
                        if (file) {
                          setImportFile(file)
                          setImportSummary(null)
                        }
                      }}
                    />
                  </div>
                  {importSummary && (
                    <div className="space-y-2 rounded-xl border p-4 bg-muted/20">
                      <h4 className="text-sm font-semibold">Import Summary</h4>
                      <p className="text-sm text-muted-foreground">
                        Created {importSummary.created_contacts} contact(s), {importSummary.created_groups} group(s)
                      </p>
                      {importSummary.errors.length > 0 && (
                        <div className="text-sm text-destructive">
                          <p className="font-semibold">Errors:</p>
                          <ul className="list-disc list-inside">
                            {importSummary.errors.map((err, i) => (
                              <li key={i}>
                                Row {err.row}: {err.reason}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setImportDialogOpen(false)
                      setImportFile(null)
                      setImportSummary(null)
                    }}
                  >
                    Close
                  </Button>
                  <Button onClick={handleImportContacts} disabled={!importFile || importing}>
                    {importing ? "Importing..." : "Import"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button size="sm" className="gap-1.5 shadow-sm">
                  <UserPlus className="h-3.5 w-3.5" />
                  Add Contact
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add New Contact</DialogTitle>
                  <DialogDescription>
                    Select a type first, then fill in the required details
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  {/* Type - FIRST */}
                  <div className="space-y-2">
                    <Label htmlFor="type" className="text-xs font-medium">Type *</Label>
                    <Select
                      value={formData.type}
                      onValueChange={(value: "client" | "list" | "agent" | "group") =>
                        setFormData({ ...formData, type: value })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select a type..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="agent">Agent (External)</SelectItem>
                        <SelectItem value="group">Group (Office/Company)</SelectItem>
                        <SelectItem value="client">Client (Individual)</SelectItem>
                        <SelectItem value="list">List (Recipients)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Conditional fields based on type */}
                  {formData.type && (
                    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-200">
                      {/* Name - Required for all */}
                      <div className="space-y-2">
                        <Label htmlFor="name" className="text-xs font-medium">Name *</Label>
                        <Input
                          id="name"
                          placeholder={
                            formData.type === "group"
                              ? "e.g. ABC Realty - La Verne"
                              : formData.type === "agent"
                                ? "e.g. John Doe"
                                : "e.g. Jane Smith"
                          }
                          value={formData.name}
                          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        />
                      </div>

                      {/* Email - Required for agent, optional for others */}
                      {formData.type === "agent" && (
                        <div className="space-y-2">
                          <Label htmlFor="email" className="text-xs font-medium">Email *</Label>
                          <Input
                            id="email"
                            type="email"
                            placeholder="john@example.com"
                            value={formData.email}
                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                          />
                        </div>
                      )}

                      {/* Email - Optional for others except group */}
                      {formData.type !== "agent" && formData.type !== "group" && (
                        <div className="space-y-2">
                          <Label htmlFor="email" className="text-xs font-medium">Email</Label>
                          <Input
                            id="email"
                            type="email"
                            placeholder="email@example.com (optional)"
                            value={formData.email}
                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                          />
                        </div>
                      )}

                      {/* Phone - Show for agent only */}
                      {formData.type === "agent" && (
                        <div className="space-y-2">
                          <Label htmlFor="phone" className="text-xs font-medium">Phone</Label>
                          <Input
                            id="phone"
                            type="tel"
                            placeholder="(555) 123-4567 (optional)"
                            value={formData.phone}
                            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                          />
                        </div>
                      )}

                      {/* Notes - Always optional */}
                      <div className="space-y-2">
                        <Label htmlFor="notes" className="text-xs font-medium">
                          {formData.type === "group" ? "Description" : "Notes"}
                        </Label>
                        <Input
                          id="notes"
                          placeholder={
                            formData.type === "group"
                              ? "e.g. Real estate office in La Verne..."
                              : "Any additional notes..."
                          }
                          value={formData.notes}
                          onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                        />
                      </div>
                    </div>
                  )}
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => {
                    setDialogOpen(false)
                    setFormData({ name: "", email: "", type: "", phone: "", notes: "" })
                  }}>
                    Cancel
                  </Button>
                  <Button onClick={handleAddContact} disabled={!formData.type || !formData.name}>
                    Add Contact
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        }
      />

      {/* Create Group Dialog */}
      <Dialog open={groupDialogOpen} onOpenChange={setGroupDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New Group</DialogTitle>
            <DialogDescription>
              Create a group to organize your contacts and sponsored agents.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="group-name" className="text-xs font-medium">Group Name</Label>
              <Input
                id="group-name"
                placeholder="Top Clients"
                value={groupForm.name}
                onChange={(e) => setGroupForm({ ...groupForm, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="group-description" className="text-xs font-medium">Description (Optional)</Label>
              <Input
                id="group-description"
                placeholder="E.g., Clients receiving monthly market reports"
                value={groupForm.description}
                onChange={(e) => setGroupForm({ ...groupForm, description: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setGroupDialogOpen(false)
                setGroupForm({ name: "", description: "" })
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleCreateGroup}>Create Group</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Person to Group(s) Dialog */}
      <Dialog
        open={addToGroupDialogOpen}
        onOpenChange={(open) => {
          setAddToGroupDialogOpen(open)
          if (!open) {
            setSelectedPersonForGroup(null)
            setSelectedGroupIds([])
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add to Group</DialogTitle>
            <DialogDescription>
              Choose one or more groups to add{" "}
              <span className="font-semibold">
                {selectedPersonForGroup?.name || "this person"}
              </span>{" "}
              to.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {groupsLoading ? (
              <div className="text-sm text-muted-foreground">Loading groups...</div>
            ) : groups.length === 0 ? (
              <div className="text-sm text-muted-foreground">
                You don&apos;t have any groups yet. Create one first.
              </div>
            ) : (
              <div className="space-y-2">
                <Label className="text-xs font-medium">Groups</Label>
                <div className="max-h-60 overflow-y-auto border rounded-xl p-2 space-y-1.5">
                  {groups.map((group) => {
                    const checked = selectedGroupIds.includes(group.id)
                    return (
                      <button
                        key={group.id}
                        type="button"
                        onClick={() => {
                          setSelectedGroupIds((prev) =>
                            checked ? prev.filter((id) => id !== group.id) : [...prev, group.id],
                          )
                        }}
                        className={cn(
                          "w-full text-left px-3 py-2.5 rounded-lg border text-sm transition-all duration-150",
                          checked
                            ? "border-primary bg-primary/5 shadow-sm"
                            : "border-border hover:border-primary/40 hover:bg-muted/40"
                        )}
                      >
                        <div className="font-medium">{group.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {group.description || "No description"} • {group.member_count} members
                        </div>
                      </button>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setAddToGroupDialogOpen(false)
                setSelectedPersonForGroup(null)
                setSelectedGroupIds([])
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleAddPersonToGroups} disabled={groups.length === 0}>
              Add to Group{selectedGroupIds.length > 1 ? "s" : ""}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Contact Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={(open) => {
        setEditDialogOpen(open)
        if (!open) {
          setEditingContact(null)
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Contact</DialogTitle>
            <DialogDescription>Update this contact&apos;s details.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name" className="text-xs font-medium">Name</Label>
              <Input
                id="edit-name"
                placeholder="John Doe"
                value={editFormData.name}
                onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-email" className="text-xs font-medium">Email</Label>
              <Input
                id="edit-email"
                type="email"
                placeholder="john@example.com"
                value={editFormData.email}
                onChange={(e) => setEditFormData({ ...editFormData, email: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-type" className="text-xs font-medium">Type</Label>
              <Select
                value={editFormData.type}
                onValueChange={(value: "client" | "list" | "agent") =>
                  setEditFormData({ ...editFormData, type: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="client">Client (Individual)</SelectItem>
                  <SelectItem value="list">List (Group)</SelectItem>
                  <SelectItem value="agent">Agent (External)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-notes" className="text-xs font-medium">Notes (Optional)</Label>
              <Input
                id="edit-notes"
                placeholder="Any additional notes..."
                value={editFormData.notes}
                onChange={(e) => setEditFormData({ ...editFormData, notes: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setEditDialogOpen(false)
                setEditingContact(null)
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleUpdateContact}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Sponsored Agent Dialog */}
      <Dialog open={editSponsoredDialogOpen} onOpenChange={(open) => {
        setEditSponsoredDialogOpen(open)
        if (!open) {
          setEditingSponsoredAgent(null)
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Sponsored Agent</DialogTitle>
            <DialogDescription>
              Manage {editingSponsoredAgent?.name || "this agent"}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {/* Name (readonly) */}
            <div className="space-y-2">
              <Label className="text-xs font-medium">Name</Label>
              <Input
                value={editingSponsoredAgent?.name || ""}
                disabled
                className="bg-muted"
              />
            </div>
            
            {/* Account ID (readonly) */}
            <div className="space-y-2">
              <Label className="text-xs font-medium">Account ID</Label>
              <Input
                value={editingSponsoredAgent?.account_id || ""}
                disabled
                className="bg-muted text-xs"
              />
            </div>
            
            {/* Phone (optional) */}
            <div className="space-y-2">
              <Label htmlFor="sponsored-phone" className="text-xs font-medium">Phone (Optional)</Label>
              <Input
                id="sponsored-phone"
                type="tel"
                placeholder="(555) 123-4567"
                value={sponsoredEditForm.phone}
                onChange={(e) => setSponsoredEditForm({ ...sponsoredEditForm, phone: e.target.value })}
              />
            </div>
            
            {/* Notes (optional) */}
            <div className="space-y-2">
              <Label htmlFor="sponsored-notes" className="text-xs font-medium">Notes (Optional)</Label>
              <Input
                id="sponsored-notes"
                placeholder="Any notes about this agent..."
                value={sponsoredEditForm.notes}
                onChange={(e) => setSponsoredEditForm({ ...sponsoredEditForm, notes: e.target.value })}
              />
            </div>
            
            {/* Sponsorship Toggle */}
            <div className="space-y-2 pt-4 border-t">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-sm font-semibold">Sponsored by your account</Label>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Remove sponsorship to make them independent
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={sponsoredEditForm.isSponsored}
                  onChange={(e) => {
                    if (!e.target.checked) {
                      // User is turning OFF sponsorship
                      handleUnsponsorAgent()
                    }
                    setSponsoredEditForm({ ...sponsoredEditForm, isSponsored: e.target.checked })
                  }}
                  className="h-5 w-5 rounded border-gray-300"
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setEditSponsoredDialogOpen(false)
                setEditingSponsoredAgent(null)
              }}
            >
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modern Summary Cards */}
      {!loading && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            {
              label: "Total Contacts",
              value: contacts.length,
              icon: Users,
              color: "bg-blue-500/10 text-blue-600",
            },
            {
              label: "Agent Contacts",
              value: contacts.filter((c) => c.type === "agent").length,
              icon: UserCheck,
              color: "bg-emerald-500/10 text-emerald-600",
            },
            {
              label: "Group Contacts",
              value: contacts.filter((c) => c.type === "group").length,
              icon: Building2,
              color: "bg-purple-500/10 text-purple-600",
            },
            isAffiliate
              ? {
                  label: "Sponsored Agents",
                  value: sponsoredAccounts.length,
                  icon: Shield,
                  color: "bg-primary/10 text-primary",
                }
              : {
                  label: "Total Groups",
                  value: groups.length,
                  icon: FolderPlus,
                  color: "bg-orange-500/10 text-orange-600",
                },
          ].map((card, i) => (
            <div
              key={i}
              className="bg-card border border-border rounded-xl p-4 shadow-[var(--shadow-card)] hover:shadow-[var(--shadow-elevated)] transition-all duration-200"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.06em]">
                  {card.label}
                </span>
                <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center", card.color)}>
                  <card.icon className="w-4 h-4" />
                </div>
              </div>
              <div className="text-2xl font-bold text-foreground tracking-tight">{card.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* People & Groups Tabs - Modernized */}
      <Tabs defaultValue="people">
        <TabsList className="h-9">
          <TabsTrigger value="people" className="text-xs gap-1.5">
            <Users className="w-3.5 h-3.5" />
            People
          </TabsTrigger>
          <TabsTrigger value="groups" className="text-xs gap-1.5">
            <FolderPlus className="w-3.5 h-3.5" />
            Groups
          </TabsTrigger>
        </TabsList>

        <TabsContent value="people" className="mt-3">
          <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
            {/* Card header */}
            <div className="px-5 py-4 border-b border-border">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="text-sm font-semibold text-foreground">All People</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {isAffiliate
                      ? "Your sponsored agents and contacts in one place"
                      : "Your client contacts and recipients"}
                  </p>
                </div>
              </div>

              {/* Search & Filter Bar - Enhanced */}
              <div className="flex items-center gap-3">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by name or email..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9 h-9 max-w-md"
                  />
                </div>
                <Select value={filterType} onValueChange={(val: any) => setFilterType(val)}>
                  <SelectTrigger className="w-44 h-9">
                    <Filter className="w-3.5 h-3.5 mr-1.5 text-muted-foreground" />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All People</SelectItem>
                    <SelectItem value="agents">Agents</SelectItem>
                    <SelectItem value="groups">Groups</SelectItem>
                    {isAffiliate && <SelectItem value="sponsored_agents">Sponsored Agents</SelectItem>}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {loading ? (
              <div className="text-center py-12 text-muted-foreground">
                <div className="w-8 h-8 rounded-lg bg-muted animate-pulse mx-auto mb-3" />
                <p className="text-sm">Loading contacts...</p>
              </div>
            ) : people.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-14 h-14 rounded-2xl bg-muted/50 flex items-center justify-center mx-auto mb-4">
                  <Users className="h-7 w-7 text-muted-foreground/50" />
                </div>
                <h4 className="text-sm font-semibold mb-1">No people found</h4>
                <p className="text-xs text-muted-foreground max-w-xs mx-auto">
                  {searchQuery || filterType !== "all"
                    ? "No results found. Try adjusting your search or filter."
                    : "No people yet. Add your first contact to get started."}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent">
                      <TableHead className="w-12 pl-5">
                        <input
                          type="checkbox"
                          checked={selectedPeopleIds.length === people.length && people.length > 0}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedPeopleIds(people.map((p) => p.id))
                            } else {
                              setSelectedPeopleIds([])
                            }
                          }}
                          className="rounded border-gray-300"
                        />
                      </TableHead>
                      <TableHead className="text-xs font-semibold">Name</TableHead>
                      <TableHead className="text-xs font-semibold">Email</TableHead>
                      <TableHead className="text-xs font-semibold">Type</TableHead>
                      <TableHead className="text-xs font-semibold">Groups</TableHead>
                      {isAffiliate && <TableHead className="text-xs font-semibold">Reports</TableHead>}
                      {isAffiliate && <TableHead className="text-xs font-semibold">Last Activity</TableHead>}
                      <TableHead className="text-xs font-semibold text-right pr-5">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {people.map((person) => (
                      <TableRow key={person.id} className="group/row">
                        <TableCell className="pl-5">
                          <input
                            type="checkbox"
                            checked={selectedPeopleIds.includes(person.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedPeopleIds([...selectedPeopleIds, person.id])
                              } else {
                                setSelectedPeopleIds(selectedPeopleIds.filter((id) => id !== person.id))
                              }
                            }}
                            className="rounded border-gray-300"
                          />
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <div className={cn(
                              "w-8 h-8 rounded-lg flex items-center justify-center text-white text-[11px] font-bold flex-shrink-0",
                              getAvatarColor(person.name)
                            )}>
                              {getInitials(person.name)}
                            </div>
                            <span className="font-medium text-sm">{person.name}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">{person.email || "—"}</TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={cn("text-[10px] font-semibold px-2 py-0.5", getTypeBadgeClasses(person.type, person.kind))}
                          >
                            {person.displayType}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {person.groups && person.groups.length > 0 ? (
                            <div className="flex gap-1 flex-wrap">
                              {person.groups.map((group) => (
                                <Badge key={group.id} variant="secondary" className="text-[10px] px-1.5 py-0 font-normal">
                                  {group.name}
                                </Badge>
                              ))}
                            </div>
                          ) : (
                            <span className="text-muted-foreground text-xs">—</span>
                          )}
                        </TableCell>
                        {isAffiliate && (
                          <TableCell className="text-sm tabular-nums">{person.reportsThisMonth ?? "—"}</TableCell>
                        )}
                        {isAffiliate && (
                          <TableCell className="text-sm text-muted-foreground">
                            {person.lastActivity
                              ? new Date(person.lastActivity).toLocaleDateString()
                              : "—"}
                          </TableCell>
                        )}
                        <TableCell className="text-right pr-5">
                          <div className="flex items-center justify-end gap-0.5 opacity-60 group-hover/row:opacity-100 transition-opacity">
                            {/* Edit for contacts */}
                            {person.kind === "contact" && (
                              <>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-7 w-7"
                                  onClick={() => {
                                    const contact = contacts.find((c) => c.id === person.id)
                                    if (!contact) return
                                    setEditingContact(contact)
                                    setEditFormData({
                                      name: contact.name,
                                      email: contact.email || "",
                                      type: contact.type,
                                      phone: contact.phone || "",
                                      notes: contact.notes || "",
                                    })
                                    setEditDialogOpen(true)
                                  }}
                                >
                                  <Pencil className="h-3.5 w-3.5" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-7 w-7"
                                  onClick={() => {
                                    const contact = contacts.find((c) => c.id === person.id)
                                    if (!contact) return
                                    setManageGroupsContact(contact)
                                    setManageGroupsDialogOpen(true)
                                  }}
                                >
                                  <Users className="h-3.5 w-3.5" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-7 w-7 text-destructive/70 hover:text-destructive"
                                  onClick={() => handleDeleteContact(person.id, person.name)}
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                </Button>
                              </>
                            )}
                            
                            {/* Edit for sponsored agents */}
                            {person.kind === "sponsored_agent" && (
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-7 w-7"
                                onClick={() => {
                                  const agent = sponsoredAccounts.find((a) => a.account_id === person.id)
                                  if (!agent) return
                                  setEditingSponsoredAgent(agent)
                                  setSponsoredEditForm({
                                    phone: "",
                                    notes: "",
                                    isSponsored: true,
                                  })
                                  setEditSponsoredDialogOpen(true)
                                }}
                              >
                                <Pencil className="h-3.5 w-3.5" />
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="groups" className="mt-3">
          <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
            <div className="px-5 py-4 border-b border-border flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-foreground">Groups</h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Create and manage groups of contacts for easy scheduling.
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5"
                onClick={() => {
                  setGroupDialogOpen(true)
                }}
              >
                <FolderPlus className="h-3.5 w-3.5" />
                New Group
              </Button>
            </div>

            {groupsLoading ? (
              <div className="text-center py-12 text-muted-foreground">
                <div className="w-8 h-8 rounded-lg bg-muted animate-pulse mx-auto mb-3" />
                <p className="text-sm">Loading groups...</p>
              </div>
            ) : groups.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-14 h-14 rounded-2xl bg-muted/50 flex items-center justify-center mx-auto mb-4">
                  <FolderPlus className="h-7 w-7 text-muted-foreground/50" />
                </div>
                <h4 className="text-sm font-semibold mb-1">No groups yet</h4>
                <p className="text-xs text-muted-foreground max-w-xs mx-auto">
                  Create a group to start organizing your people.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-border">
                {groups.map((group) => (
                  <div
                    key={group.id}
                    className="px-5 py-3.5 flex items-center justify-between hover:bg-muted/30 transition-colors cursor-pointer group/item"
                    onClick={async () => {
                      setActiveGroup(group)
                      await loadGroupMembers(group.id)
                    }}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg bg-purple-500/10 flex items-center justify-center flex-shrink-0">
                        <Users className="w-4 h-4 text-purple-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">{group.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {group.description || "No description"} • {group.member_count ?? 0} member{(group.member_count ?? 0) !== 1 ? "s" : ""}
                        </p>
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover/item:opacity-100 transition-opacity" />
                  </div>
                ))}
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* Group Detail Dialog */}
      <Dialog open={!!activeGroup} onOpenChange={(open) => !open && setActiveGroup(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{activeGroup?.name || "Group Details"}</DialogTitle>
            <DialogDescription>
              {activeGroup?.description || "Manage group members"}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {/* Add Members Button */}
            <div className="flex justify-between items-center">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Members ({groupDetailMembers.length})</h4>
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5"
                onClick={() => setAddMembersOpen(true)}
              >
                <UserPlus className="h-3.5 w-3.5" />
                Add Members
              </Button>
            </div>

            {/* Members List */}
            {loadingMembers ? (
              <div className="text-center py-8 text-muted-foreground text-sm">Loading members...</div>
            ) : groupDetailMembers.length === 0 ? (
              <div className="text-center py-8">
                <div className="w-12 h-12 rounded-xl bg-muted/50 flex items-center justify-center mx-auto mb-3">
                  <Users className="h-6 w-6 text-muted-foreground/50" />
                </div>
                <p className="text-sm text-muted-foreground">No members yet. Click &quot;Add Members&quot; to get started.</p>
              </div>
            ) : (
              <div className="space-y-1.5">
                {groupDetailMembers.map((member: any) => (
                  <div
                    key={`${member.member_type}-${member.member_id}`}
                    className="flex items-center justify-between p-3 rounded-xl border border-border/50 hover:bg-muted/30 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        "w-8 h-8 rounded-lg flex items-center justify-center text-white text-[11px] font-bold",
                        getAvatarColor(member.name || "?")
                      )}>
                        {getInitials(member.name || "?")}
                      </div>
                      <div>
                        <p className="text-sm font-medium">{member.name}</p>
                        <p className="text-xs text-muted-foreground">{member.email || "No email"}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className={cn(
                          "text-[10px] font-semibold px-2 py-0.5",
                          member.member_type === "sponsored_agent"
                            ? "bg-primary/10 text-primary border-primary/20"
                            : "bg-muted text-muted-foreground"
                        )}
                      >
                        {member.member_type === "contact" ? "Contact" : "Sponsored Agent"}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-destructive/70 hover:text-destructive"
                        onClick={() =>
                          handleRemoveMemberFromGroup(
                            activeGroup!.id,
                            member.member_type,
                            member.member_id,
                            member.name
                          )
                        }
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setActiveGroup(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Members to Group Dialog */}
      <Dialog open={addMembersOpen} onOpenChange={setAddMembersOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Members to {activeGroup?.name}</DialogTitle>
            <DialogDescription>
              Select contacts and sponsored agents to add to this group.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-xs font-medium">Available People</Label>
              <div className="max-h-60 overflow-y-auto border rounded-xl p-2 space-y-1.5">
                {/* Contacts */}
                {contacts.map((contact) => {
                  const isAlreadyMember = groupDetailMembers.some(
                    (m: any) => m.member_type === "contact" && m.member_id === contact.id
                  )
                  if (isAlreadyMember) return null

                  const checked = selectedMemberIds.includes(contact.id)
                  return (
                    <button
                      key={contact.id}
                      type="button"
                      onClick={() => {
                        setSelectedMemberIds((prev) =>
                          checked ? prev.filter((id) => id !== contact.id) : [...prev, contact.id]
                        )
                      }}
                      className={cn(
                        "w-full text-left px-3 py-2.5 rounded-lg border text-sm transition-all duration-150",
                        checked
                          ? "border-primary bg-primary/5 shadow-sm"
                          : "border-border hover:border-primary/40 hover:bg-muted/40"
                      )}
                    >
                      <div className="font-medium">{contact.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {contact.email || "No email"} • {contact.type}
                      </div>
                    </button>
                  )
                })}

                {/* Sponsored Agents (if affiliate) */}
                {isAffiliate &&
                  sponsoredAccounts.map((agent) => {
                    const isAlreadyMember = groupDetailMembers.some(
                      (m: any) => m.member_type === "sponsored_agent" && m.member_id === agent.account_id
                    )
                    if (isAlreadyMember) return null

                    const checked = selectedMemberIds.includes(agent.account_id)
                    return (
                      <button
                        key={agent.account_id}
                        type="button"
                        onClick={() => {
                          setSelectedMemberIds((prev) =>
                            checked
                              ? prev.filter((id) => id !== agent.account_id)
                              : [...prev, agent.account_id]
                          )
                        }}
                        className={cn(
                          "w-full text-left px-3 py-2.5 rounded-lg border text-sm transition-all duration-150",
                          checked
                            ? "border-primary bg-primary/5 shadow-sm"
                            : "border-border hover:border-primary/40 hover:bg-muted/40"
                        )}
                      >
                        <div className="font-medium">{agent.name}</div>
                        <div className="text-xs text-muted-foreground">Sponsored Agent</div>
                      </button>
                    )
                  })}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setAddMembersOpen(false)
                setSelectedMemberIds([])
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={() => activeGroup && handleAddMembersToGroup(activeGroup.id)}
              disabled={selectedMemberIds.length === 0}
            >
              Add {selectedMemberIds.length} Member{selectedMemberIds.length !== 1 ? "s" : ""}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Manage Groups Dialog (Per Contact) */}
      <Dialog open={manageGroupsDialogOpen} onOpenChange={(open) => {
        setManageGroupsDialogOpen(open)
        if (!open) {
          setManageGroupsContact(null)
          setSelectedGroupIds([])
        }
      }}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Manage Groups for {manageGroupsContact?.name}</DialogTitle>
            <DialogDescription>
              View and manage which groups this contact belongs to.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {/* Current Memberships */}
            <div className="space-y-2">
              <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Current Groups</Label>
              {manageGroupsContact?.groups && manageGroupsContact.groups.length > 0 ? (
                <div className="space-y-1.5">
                  {manageGroupsContact.groups.map((group) => (
                    <div
                      key={group.id}
                      className="flex items-center justify-between px-3 py-2.5 border rounded-xl hover:bg-muted/30 transition-colors"
                    >
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-lg bg-purple-500/10 flex items-center justify-center">
                          <Users className="w-3.5 h-3.5 text-purple-600" />
                        </div>
                        <span className="font-medium text-sm">{group.name}</span>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-destructive/70 hover:text-destructive"
                        onClick={() =>
                          manageGroupsContact &&
                          handleRemoveContactFromGroup(manageGroupsContact.id, group.id, group.name)
                        }
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground py-4 text-center">
                  Not in any groups yet.
                </p>
              )}
            </div>

            {/* Add to New Groups */}
            <div className="space-y-2 pt-4 border-t">
              <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Add to Groups</Label>
              <div className="max-h-48 overflow-y-auto border rounded-xl p-2 space-y-1.5">
                {groups
                  .filter(
                    (g) =>
                      !manageGroupsContact?.groups?.some((mg) => mg.id === g.id)
                  )
                  .map((group) => {
                    const checked = selectedGroupIds.includes(group.id)
                    return (
                      <button
                        key={group.id}
                        type="button"
                        onClick={() => {
                          setSelectedGroupIds((prev) =>
                            checked
                              ? prev.filter((id) => id !== group.id)
                              : [...prev, group.id]
                          )
                        }}
                        className={cn(
                          "w-full text-left px-3 py-2.5 rounded-lg border text-sm transition-all duration-150",
                          checked
                            ? "border-primary bg-primary/5 shadow-sm"
                            : "border-border hover:border-primary/40 hover:bg-muted/40"
                        )}
                      >
                        <div className="font-medium">{group.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {group.description || "No description"} • {group.member_count} members
                        </div>
                      </button>
                    )
                  })}
              </div>
              {selectedGroupIds.length > 0 && (
                <Button
                  className="w-full mt-2"
                  onClick={() =>
                    manageGroupsContact &&
                    handleAddContactToGroupsFromManage(manageGroupsContact.id)
                  }
                >
                  Add to {selectedGroupIds.length} Group{selectedGroupIds.length !== 1 ? "s" : ""}
                </Button>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setManageGroupsDialogOpen(false)
              setManageGroupsContact(null)
              setSelectedGroupIds([])
            }}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

"use client"

import { useEffect, useState } from "react"
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
import { UserPlus, Mail, Trash2, Users, Shield, Pencil } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

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
  const [contacts, setContacts] = useState<Contact[]>([])
  const [sponsoredAccounts, setSponsoredAccounts] = useState<SponsoredAccount[]>([])
  const [isAffiliate, setIsAffiliate] = useState(false)
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [editingContact, setEditingContact] = useState<Contact | null>(null)
  const [groups, setGroups] = useState<ContactGroup[]>([])
  const [groupsLoading, setGroupsLoading] = useState(false)
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
  const { toast } = useToast()

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

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      // Fetch user info
      const meRes = await fetch("/api/proxy/v1/me", { cache: "no-store" })
      const me = meRes.ok ? await meRes.json() : {}
      const isAff = me.account_type === "INDUSTRY_AFFILIATE"
      setIsAffiliate(isAff)

      // Fetch contacts
      const contactsRes = await fetch("/api/proxy/v1/contacts", { cache: "no-store" })
      if (contactsRes.ok) {
        const data = await contactsRes.json()
        setContacts(data.contacts || [])
      }

      // If affiliate, fetch sponsored accounts
      if (isAff) {
        const overviewRes = await fetch("/api/proxy/v1/affiliate/overview", { cache: "no-store" })
        if (overviewRes.ok) {
          const overview = await overviewRes.json()
          setSponsoredAccounts(overview.sponsored_accounts || [])
        }
      }
      // Load groups for this account
      await loadGroups()
    } catch (error) {
      console.error("Failed to load people:", error)
      toast({
        title: "Error",
        description: "Failed to load people data",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  async function loadGroups() {
    setGroupsLoading(true)
    try {
      const res = await fetch("/api/proxy/v1/contact-groups", { cache: "no-store" })
      if (res.ok) {
        const data = await res.json()
        setGroups(data.groups || [])
      }
    } catch (error) {
      console.error("Failed to load groups:", error)
    } finally {
      setGroupsLoading(false)
    }
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
      loadData()
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
      await loadData()
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
      loadData()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete contact",
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
      await loadGroups()
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
      await loadGroups()
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

      await loadData()
      await loadGroups()
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">People</h1>
          <p className="text-muted-foreground mt-1">
            {isAffiliate
              ? "Manage your sponsored agents and client contacts"
              : "Manage your client contacts and recipients"}
          </p>
        </div>
        <div className="flex gap-2">
          <Dialog open={importDialogOpen} onOpenChange={setImportDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Mail className="h-4 w-4 mr-2" />
                Import CSV
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Import Contacts from CSV</DialogTitle>
                <DialogDescription>
                  Upload a CSV file with columns: <code>name</code>, <code>email</code>, optional{" "}
                  <code>type</code> (client/agent/list), and optional <code>group</code> (group name).
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
                  <div className="space-y-2 rounded-md border p-4">
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
              <Button>
                <UserPlus className="h-4 w-4 mr-2" />
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
                <Label htmlFor="type">Type *</Label>
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
                <>
                  {/* Name - Required for all */}
                  <div className="space-y-2">
                    <Label htmlFor="name">Name *</Label>
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
                      <Label htmlFor="email">Email *</Label>
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
                      <Label htmlFor="email">Email</Label>
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
                      <Label htmlFor="phone">Phone</Label>
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
                    <Label htmlFor="notes">
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
                </>
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
                <Label htmlFor="group-name">Group Name</Label>
                <Input
                  id="group-name"
                  placeholder="Top Clients"
                  value={groupForm.name}
                  onChange={(e) => setGroupForm({ ...groupForm, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="group-description">Description (Optional)</Label>
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
                  <Label>Groups</Label>
                  <div className="max-h-60 overflow-y-auto border rounded-md p-2 space-y-1">
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
                          className={`w-full text-left px-3 py-2 rounded-md border text-sm ${
                            checked
                              ? "border-primary bg-primary/5"
                              : "border-border hover:border-primary/40 hover:bg-muted/40"
                          }`}
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
              <DialogDescription>Update this contact’s details.</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="edit-name">Name</Label>
                <Input
                  id="edit-name"
                  placeholder="John Doe"
                  value={editFormData.name}
                  onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-email">Email</Label>
                <Input
                  id="edit-email"
                  type="email"
                  placeholder="john@example.com"
                  value={editFormData.email}
                  onChange={(e) => setEditFormData({ ...editFormData, email: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-type">Type</Label>
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
                <Label htmlFor="edit-notes">Notes (Optional)</Label>
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
      </div>

      {/* Stats Card (for affiliates) */}
      {isAffiliate && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Sponsored Agents</CardTitle>
              <Shield className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{sponsoredAccounts.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Contacts</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{contacts.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total People</CardTitle>
              <Mail className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{people.length}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* People & Groups Tabs */}
      <Tabs defaultValue="people">
        <TabsList>
          <TabsTrigger value="people">People</TabsTrigger>
          <TabsTrigger value="groups">Groups</TabsTrigger>
        </TabsList>
        <TabsContent value="people" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>All People</CardTitle>
              <CardDescription>
                {isAffiliate
                  ? "Your sponsored agents and contacts in one place"
                  : "Your client contacts and recipients"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Search & Filter Bar */}
              <div className="flex items-center gap-4 mb-4">
                <div className="flex-1">
                  <Input
                    placeholder="Search by name or email..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="max-w-md"
                  />
                </div>
                <Select value={filterType} onValueChange={(val: any) => setFilterType(val)}>
                  <SelectTrigger className="w-48">
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

              {loading ? (
                <div className="text-center py-8 text-muted-foreground">Loading...</div>
              ) : people.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>
                    {searchQuery || filterType !== "all"
                      ? "No results found. Try adjusting your search or filter."
                      : "No people yet. Add your first contact to get started."}
                  </p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">
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
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Groups</TableHead>
                      {isAffiliate && <TableHead>Reports This Month</TableHead>}
                      {isAffiliate && <TableHead>Last Activity</TableHead>}
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {people.map((person) => (
                      <TableRow key={person.id}>
                        <TableCell>
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
                        <TableCell className="font-medium">{person.name}</TableCell>
                        <TableCell>{person.email || "—"}</TableCell>
                        <TableCell>
                          <Badge
                            variant={person.type === "sponsored_agent" ? "default" : "outline"}
                          >
                            {person.displayType}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {person.groups && person.groups.length > 0 ? (
                            <div className="flex gap-1 flex-wrap">
                              {person.groups.map((group) => (
                                <Badge key={group.id} variant="secondary" className="text-xs">
                                  {group.name}
                                </Badge>
                              ))}
                            </div>
                          ) : (
                            <span className="text-muted-foreground text-sm">—</span>
                          )}
                        </TableCell>
                        {isAffiliate && (
                          <TableCell>{person.reportsThisMonth ?? "—"}</TableCell>
                        )}
                        {isAffiliate && (
                          <TableCell>
                            {person.lastActivity
                              ? new Date(person.lastActivity).toLocaleDateString()
                              : "—"}
                          </TableCell>
                        )}
                        <TableCell className="text-right space-x-1">
                          {/* Add to Group (contacts and sponsored agents) */}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedPersonForGroup(person)
                              setSelectedGroupIds([])
                              setAddToGroupDialogOpen(true)
                            }}
                          >
                            <Users className="h-4 w-4" />
                          </Button>

                          {/* Edit/Delete only for contacts */}
                          {person.type !== "sponsored_agent" && (
                            <>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  const contact = contacts.find((c) => c.id === person.id)
                                  if (!contact) return
                                  setEditingContact(contact)
                                  setEditFormData({
                                    name: contact.name,
                                    email: contact.email,
                                    type: contact.type,
                                    notes: contact.notes || "",
                                  })
                                  setEditDialogOpen(true)
                                }}
                              >
                                <Pencil className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDeleteContact(person.id, person.name)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="groups" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Groups</CardTitle>
                <CardDescription>
                  Create and manage groups of contacts and sponsored agents for easy scheduling.
                </CardDescription>
              </div>
              <Button
                variant="outline"
                onClick={() => {
                  setGroupDialogOpen(true)
                }}
              >
                <Users className="h-4 w-4 mr-2" />
                New Group
              </Button>
            </CardHeader>
            <CardContent>
              {groupsLoading ? (
                <div className="text-center py-8 text-muted-foreground">Loading groups...</div>
              ) : groups.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No groups yet. Create a group to start organizing your people.</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Members</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {groups.map((group) => (
                      <TableRow key={group.id}>
                        <TableCell className="font-medium">{group.name}</TableCell>
                        <TableCell>{group.description || "—"}</TableCell>
                        <TableCell>{group.member_count ?? 0}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}


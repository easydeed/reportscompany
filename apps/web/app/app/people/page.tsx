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
import { UserPlus, Mail, Trash2, Users, Shield } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"

type Contact = {
  id: string
  name: string
  email: string
  type: "client" | "list" | "agent"
  notes?: string
  created_at: string
}

type SponsoredAccount = {
  account_id: string
  name: string
  plan_slug: string
  reports_this_month: number
  last_report_at: string | null
}

type Person = {
  id: string
  name: string
  email: string
  type: string
  displayType: string
  lastActivity?: string
  reportsThisMonth?: number
}

export default function PeoplePage() {
  const [contacts, setContacts] = useState<Contact[]>([])
  const [sponsoredAccounts, setSponsoredAccounts] = useState<SponsoredAccount[]>([])
  const [isAffiliate, setIsAffiliate] = useState(false)
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const { toast } = useToast()

  // Form state
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    type: "client" as "client" | "list" | "agent",
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

  async function handleAddContact() {
    if (!formData.name || !formData.email) {
      toast({
        title: "Error",
        description: "Name and email are required",
        variant: "destructive",
      })
      return
    }

    try {
      const res = await fetch("/api/proxy/v1/contacts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
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
      setFormData({ name: "", email: "", type: "client", notes: "" })
      loadData()
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to add contact",
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

  // Combine contacts and sponsored accounts into unified list
  const people: Person[] = [
    ...contacts.map((c) => ({
      id: c.id,
      name: c.name,
      email: c.email,
      type: c.type,
      displayType: c.type === "client" ? "Client" : c.type === "list" ? "List" : "Agent",
      lastActivity: undefined,
      reportsThisMonth: undefined,
    })),
    ...sponsoredAccounts.map((s) => ({
      id: s.account_id,
      name: s.name,
      email: "", // Sponsored accounts don't have a direct email in this view
      type: "sponsored_agent",
      displayType: "Agent (Sponsored)",
      lastActivity: s.last_report_at || undefined,
      reportsThisMonth: s.reports_this_month,
    })),
  ]

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
                Add a client, recipient list, or external agent to your contacts
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  placeholder="John Doe"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="john@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="type">Type</Label>
                <Select
                  value={formData.type}
                  onValueChange={(value: "client" | "list" | "agent") =>
                    setFormData({ ...formData, type: value })
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
                <Label htmlFor="notes">Notes (Optional)</Label>
                <Input
                  id="notes"
                  placeholder="Any additional notes..."
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddContact}>Add Contact</Button>
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

      {/* People Table */}
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
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : people.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No people yet. Add your first contact to get started.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Type</TableHead>
                  {isAffiliate && <TableHead>Reports This Month</TableHead>}
                  {isAffiliate && <TableHead>Last Activity</TableHead>}
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {people.map((person) => (
                  <TableRow key={person.id}>
                    <TableCell className="font-medium">{person.name}</TableCell>
                    <TableCell>{person.email || "—"}</TableCell>
                    <TableCell>
                      <Badge
                        variant={person.type === "sponsored_agent" ? "default" : "outline"}
                      >
                        {person.displayType}
                      </Badge>
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
                    <TableCell className="text-right">
                      {person.type !== "sponsored_agent" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteContact(person.id, person.name)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}


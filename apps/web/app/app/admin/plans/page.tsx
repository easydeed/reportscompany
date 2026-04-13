"use client"

import { useEffect, useState, useCallback } from "react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  ArrowLeft,
  CreditCard,
  Plus,
  Pencil,
  Loader2,
  CheckCircle,
  XCircle,
  Building,
  Users,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"

interface Plan {
  plan_slug: string
  plan_name: string
  monthly_report_limit: number
  allow_overage: boolean
  overage_price_cents: number
  stripe_price_id: string | null
  description: string | null
  is_active: boolean
  created_at: string | null
  updated_at: string | null
  account_count: number
}

interface PlanFormData {
  plan_slug: string
  plan_name: string
  monthly_report_limit: number
  allow_overage: boolean
  overage_price_cents: number
  stripe_price_id: string
  description: string
  is_active: boolean
}

const EMPTY_FORM: PlanFormData = {
  plan_slug: "",
  plan_name: "",
  monthly_report_limit: 10,
  allow_overage: false,
  overage_price_cents: 0,
  stripe_price_id: "",
  description: "",
  is_active: true,
}

function formatPrice(cents: number): string {
  if (cents === 0) return "Free"
  return `$${(cents / 100).toFixed(2)}`
}

export default function AdminPlansPage() {
  const { toast } = useToast()

  const [plans, setPlans] = useState<Plan[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const [editOpen, setEditOpen] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [editSlug, setEditSlug] = useState<string | null>(null)
  const [form, setForm] = useState<PlanFormData>(EMPTY_FORM)

  const fetchPlans = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch("/api/proxy/v1/admin/plans", { credentials: "include" })
      if (res.ok) {
        const data = await res.json()
        setPlans(data?.plans || [])
      }
    } catch (err) {
      console.error("Failed to fetch plans:", err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchPlans()
  }, [fetchPlans])

  function openEdit(plan: Plan) {
    setEditSlug(plan.plan_slug)
    setForm({
      plan_slug: plan.plan_slug,
      plan_name: plan.plan_name,
      monthly_report_limit: plan.monthly_report_limit,
      allow_overage: plan.allow_overage,
      overage_price_cents: plan.overage_price_cents,
      stripe_price_id: plan.stripe_price_id || "",
      description: plan.description || "",
      is_active: plan.is_active,
    })
    setEditOpen(true)
  }

  function openCreate() {
    setForm(EMPTY_FORM)
    setCreateOpen(true)
  }

  async function handleSave() {
    setSaving(true)
    try {
      const res = await fetch(`/api/proxy/v1/admin/plans/${editSlug}`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan_name: form.plan_name,
          monthly_report_limit: form.monthly_report_limit,
          allow_overage: form.allow_overage,
          overage_price_cents: form.overage_price_cents,
          stripe_price_id: form.stripe_price_id || null,
          description: form.description || null,
          is_active: form.is_active,
        }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || "Failed to update plan")
      }

      toast({ title: "Plan updated" })
      setEditOpen(false)
      fetchPlans()
    } catch (err) {
      toast({
        title: "Failed to update plan",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      })
    } finally {
      setSaving(false)
    }
  }

  async function handleCreate() {
    if (!form.plan_slug || !form.plan_name) {
      toast({ title: "Slug and name are required", variant: "destructive" })
      return
    }

    setSaving(true)
    try {
      const res = await fetch("/api/proxy/v1/admin/plans", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan_slug: form.plan_slug,
          plan_name: form.plan_name,
          monthly_report_limit: form.monthly_report_limit,
          allow_overage: form.allow_overage,
          overage_price_cents: form.overage_price_cents,
          stripe_price_id: form.stripe_price_id || null,
          description: form.description || null,
        }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || "Failed to create plan")
      }

      toast({ title: "Plan created" })
      setCreateOpen(false)
      fetchPlans()
    } catch (err) {
      toast({
        title: "Failed to create plan",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      })
    } finally {
      setSaving(false)
    }
  }

  const totalAccounts = plans.reduce((sum, p) => sum + p.account_count, 0)
  const activePlans = plans.filter((p) => p.is_active).length

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded" />
          <div>
            <Skeleton className="h-9 w-48 mb-2" />
            <Skeleton className="h-5 w-72" />
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="pt-6"><Skeleton className="h-8 w-16" /></CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardContent className="pt-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="py-3 flex gap-4">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-5 w-16 rounded-full" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/app/admin">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-display font-bold text-foreground">
              Subscription Plans
            </h1>
            <p className="text-muted-foreground mt-1">
              Manage pricing plans and report limits
            </p>
          </div>
        </div>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4 mr-2" />
          Create Plan
        </Button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Plans</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{plans.length}</div>
            <p className="text-xs text-muted-foreground">{activePlans} active</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Accounts</CardTitle>
            <Building className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalAccounts}</div>
            <p className="text-xs text-muted-foreground">Across all plans</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Plans</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activePlans}</div>
            <p className="text-xs text-muted-foreground">Available to assign</p>
          </CardContent>
        </Card>
      </div>

      {/* Plans Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Plans ({plans.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {plans.length === 0 ? (
            <div className="text-center py-12">
              <CreditCard className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No plans found</h3>
              <p className="text-muted-foreground mb-4">Create your first subscription plan</p>
              <Button onClick={openCreate}>
                <Plus className="h-4 w-4 mr-2" />
                Create Plan
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-[11px] uppercase tracking-wider">Plan Name</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Slug</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider text-right">Report Limit</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Overage</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Stripe Price ID</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Status</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider text-right">Accounts</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {plans.map((plan) => (
                  <TableRow key={plan.plan_slug} className={!plan.is_active ? "opacity-60" : ""}>
                    <TableCell>
                      <div>
                        <p className="font-medium text-sm">{plan.plan_name}</p>
                        {plan.description && (
                          <p className="text-xs text-muted-foreground truncate max-w-[200px]">{plan.description}</p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">{plan.plan_slug}</code>
                    </TableCell>
                    <TableCell className="text-right font-medium text-sm">
                      {plan.monthly_report_limit.toLocaleString()}
                    </TableCell>
                    <TableCell>
                      {plan.allow_overage ? (
                        <div>
                          <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50">Allowed</Badge>
                          {plan.overage_price_cents > 0 && (
                            <p className="text-xs text-muted-foreground mt-0.5">{formatPrice(plan.overage_price_cents)}/ea</p>
                          )}
                        </div>
                      ) : (
                        <Badge variant="outline" className="text-muted-foreground">No</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {plan.stripe_price_id ? (
                        <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono truncate max-w-[160px] block">
                          {plan.stripe_price_id}
                        </code>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {plan.is_active ? (
                        <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Active
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-red-600 border-red-200 bg-red-50">
                          <XCircle className="h-3 w-3 mr-1" />
                          Inactive
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Users className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="font-medium text-sm">{plan.account_count}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm" onClick={() => openEdit(plan)} className="h-8 w-8 p-0">
                        <Pencil className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Plan</DialogTitle>
            <DialogDescription>
              Update plan settings for <code className="font-mono text-xs bg-muted px-1 py-0.5 rounded">{editSlug}</code>
            </DialogDescription>
          </DialogHeader>
          <PlanForm form={form} setForm={setForm} isEdit />
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditOpen(false)} disabled={saving}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Create Plan</DialogTitle>
            <DialogDescription>Add a new subscription plan</DialogDescription>
          </DialogHeader>
          <PlanForm form={form} setForm={setForm} isEdit={false} />
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)} disabled={saving}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={saving}>
              {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Plus className="h-4 w-4 mr-2" />}
              Create Plan
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function PlanForm({
  form,
  setForm,
  isEdit,
}: {
  form: PlanFormData
  setForm: React.Dispatch<React.SetStateAction<PlanFormData>>
  isEdit: boolean
}) {
  return (
    <div className="space-y-4 py-2">
      {!isEdit && (
        <div className="space-y-2">
          <Label htmlFor="plan_slug">Slug</Label>
          <Input
            id="plan_slug"
            placeholder="e.g. enterprise"
            value={form.plan_slug}
            onChange={(e) => setForm((f) => ({ ...f, plan_slug: e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, "_") }))}
          />
          <p className="text-xs text-muted-foreground">Unique identifier, cannot be changed later</p>
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="plan_name">Name</Label>
        <Input
          id="plan_name"
          placeholder="e.g. Enterprise"
          value={form.plan_name}
          onChange={(e) => setForm((f) => ({ ...f, plan_name: e.target.value }))}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="monthly_report_limit">Monthly Report Limit</Label>
          <Input
            id="monthly_report_limit"
            type="number"
            min="0"
            value={form.monthly_report_limit}
            onChange={(e) => setForm((f) => ({ ...f, monthly_report_limit: parseInt(e.target.value) || 0 }))}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="overage_price_cents">Overage Price (cents)</Label>
          <Input
            id="overage_price_cents"
            type="number"
            min="0"
            value={form.overage_price_cents}
            onChange={(e) => setForm((f) => ({ ...f, overage_price_cents: parseInt(e.target.value) || 0 }))}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="stripe_price_id">Stripe Price ID</Label>
        <Input
          id="stripe_price_id"
          placeholder="price_..."
          value={form.stripe_price_id}
          onChange={(e) => setForm((f) => ({ ...f, stripe_price_id: e.target.value }))}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Input
          id="description"
          placeholder="Brief description"
          value={form.description}
          onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
        />
      </div>

      <div className="flex items-center justify-between pt-2">
        <div className="flex items-center gap-3">
          <Switch
            id="allow_overage"
            checked={form.allow_overage}
            onCheckedChange={(v) => setForm((f) => ({ ...f, allow_overage: v }))}
          />
          <Label htmlFor="allow_overage" className="cursor-pointer">Allow Overage</Label>
        </div>

        {isEdit && (
          <div className="flex items-center gap-3">
            <Switch
              id="is_active"
              checked={form.is_active}
              onCheckedChange={(v) => setForm((f) => ({ ...f, is_active: v }))}
            />
            <Label htmlFor="is_active" className="cursor-pointer">Active</Label>
          </div>
        )}
      </div>
    </div>
  )
}

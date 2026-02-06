"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
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
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  CreditCard,
  Edit,
  Plus,
  Save,
  Loader2,
  Check,
  X,
} from "lucide-react"

interface Plan {
  plan_slug: string
  plan_name: string
  monthly_report_limit: number
  allow_overage: boolean
  overage_price_cents: number
  stripe_price_id: string | null
  description: string | null
  is_active: boolean
  account_count: number
  created_at: string | null
  updated_at: string | null
}

export default function PlansPage() {
  const [plans, setPlans] = useState<Plan[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<string | null>(null)
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [newPlan, setNewPlan] = useState({
    plan_slug: "",
    plan_name: "",
    monthly_report_limit: 10,
    allow_overage: false,
    overage_price_cents: 0,
    description: "",
  })

  useEffect(() => {
    fetchPlans()
  }, [])

  async function fetchPlans() {
    try {
      const res = await fetch("/api/v1/admin/plans", { credentials: "include" })
      if (res.ok) {
        const data = await res.json()
        // Filter out any null/undefined plans and ensure required fields exist
        const validPlans = (data.plans || data || []).filter(
          (p: any) => p && typeof p.monthly_report_limit === 'number'
        )
        setPlans(validPlans)
      }
    } catch (error) {
      console.error("Failed to fetch plans:", error)
    } finally {
      setLoading(false)
    }
  }

  async function updatePlan(planSlug: string, updates: Partial<Plan>) {
    setSaving(planSlug)
    try {
      const res = await fetch(`/api/v1/admin/plans/${planSlug}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(updates),
      })
      if (res.ok) {
        fetchPlans()
        setEditingPlan(null)
      }
    } catch (error) {
      console.error("Failed to update plan:", error)
    } finally {
      setSaving(null)
    }
  }

  async function createPlan() {
    setSaving("new")
    try {
      const res = await fetch("/api/v1/admin/plans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(newPlan),
      })
      if (res.ok) {
        fetchPlans()
        setShowCreateDialog(false)
        setNewPlan({
          plan_slug: "",
          plan_name: "",
          monthly_report_limit: 10,
          allow_overage: false,
          overage_price_cents: 0,
          description: "",
        })
      }
    } catch (error) {
      console.error("Failed to create plan:", error)
    } finally {
      setSaving(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Plans & Pricing</h1>
          <p className="text-slate-500 mt-1">Manage subscription plans and pricing tiers</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-indigo-600 hover:bg-indigo-700 text-white">
              <Plus className="h-4 w-4 mr-2" />
              Create Plan
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-white border-slate-200">
            <DialogHeader>
              <DialogTitle className="text-slate-900">Create New Plan</DialogTitle>
              <DialogDescription className="text-slate-500">
                Add a new subscription plan to your platform
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-700">Plan Slug</Label>
                  <Input
                    value={newPlan.plan_slug}
                    onChange={(e) => setNewPlan({ ...newPlan, plan_slug: e.target.value })}
                    placeholder="e.g., enterprise"
                    className="bg-white border-slate-300 text-slate-900"
                  />
                </div>
                <div>
                  <Label className="text-slate-700">Plan Name</Label>
                  <Input
                    value={newPlan.plan_name}
                    onChange={(e) => setNewPlan({ ...newPlan, plan_name: e.target.value })}
                    placeholder="e.g., Enterprise"
                    className="bg-white border-slate-300 text-slate-900"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-700">Monthly Report Limit</Label>
                  <Input
                    type="number"
                    value={newPlan.monthly_report_limit}
                    onChange={(e) => setNewPlan({ ...newPlan, monthly_report_limit: parseInt(e.target.value) || 0 })}
                    className="bg-white border-slate-300 text-slate-900"
                  />
                </div>
                <div>
                  <Label className="text-slate-700">Overage Price (cents)</Label>
                  <Input
                    type="number"
                    value={newPlan.overage_price_cents}
                    onChange={(e) => setNewPlan({ ...newPlan, overage_price_cents: parseInt(e.target.value) || 0 })}
                    className="bg-white border-slate-300 text-slate-900"
                  />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  checked={newPlan.allow_overage}
                  onCheckedChange={(checked) => setNewPlan({ ...newPlan, allow_overage: checked })}
                />
                <Label className="text-slate-700">Allow overage (pay per extra report)</Label>
              </div>
              <div>
                <Label className="text-slate-700">Description</Label>
                <Input
                  value={newPlan.description}
                  onChange={(e) => setNewPlan({ ...newPlan, description: e.target.value })}
                  placeholder="Brief description of the plan"
                  className="bg-white border-slate-300 text-slate-900"
                />
              </div>
              <Button
                onClick={createPlan}
                disabled={saving === "new" || !newPlan.plan_slug || !newPlan.plan_name}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                {saving === "new" ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <Plus className="h-4 w-4 mr-2" />
                )}
                Create Plan
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Plans Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {plans.map((plan) => (
          <Card key={plan.plan_slug} className={`bg-white border-slate-200 shadow-sm ${!plan.is_active ? 'opacity-50' : ''}`}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg text-slate-900">{plan.plan_name}</CardTitle>
                <Badge className={plan.is_active ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"}>
                  {plan.is_active ? "Active" : "Inactive"}
                </Badge>
              </div>
              <CardDescription className="text-slate-400">{plan.plan_slug}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500 text-sm">Reports/mo</span>
                  <span className="text-slate-900 font-bold">{plan.monthly_report_limit}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500 text-sm">Accounts</span>
                  <span className="text-indigo-600 font-medium">{plan.account_count}</span>
                </div>
                {plan.allow_overage && (
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 text-sm">Overage</span>
                    <span className="text-emerald-600 font-medium">${(plan.overage_price_cents / 100).toFixed(2)}/ea</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Plans Table */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-slate-900">Plan Configuration</CardTitle>
          <CardDescription className="text-slate-500">
            Edit plan limits, pricing, and availability
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow className="border-slate-200 hover:bg-transparent">
                <TableHead className="text-slate-500">Plan</TableHead>
                <TableHead className="text-slate-500">Reports/Month</TableHead>
                <TableHead className="text-slate-500">Overage</TableHead>
                <TableHead className="text-slate-500">Overage Price</TableHead>
                <TableHead className="text-slate-500">Stripe ID</TableHead>
                <TableHead className="text-slate-500">Status</TableHead>
                <TableHead className="text-slate-500">Accounts</TableHead>
                <TableHead className="text-slate-500 w-20">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {plans.map((plan) => (
                <TableRow key={plan.plan_slug} className="border-slate-100">
                  <TableCell>
                    <div>
                      <p className="text-slate-900 font-medium">{plan.plan_name}</p>
                      <p className="text-xs text-slate-400">{plan.plan_slug}</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    {editingPlan?.plan_slug === plan.plan_slug ? (
                      <Input
                        type="number"
                        value={editingPlan.monthly_report_limit}
                        onChange={(e) => setEditingPlan({
                          ...editingPlan,
                          monthly_report_limit: parseInt(e.target.value) || 0
                        })}
                        className="w-24 bg-white border-slate-300 text-slate-900"
                      />
                    ) : (
                      <span className="text-slate-700">{plan.monthly_report_limit}</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {editingPlan?.plan_slug === plan.plan_slug ? (
                      <Switch
                        checked={editingPlan.allow_overage}
                        onCheckedChange={(checked) => setEditingPlan({
                          ...editingPlan,
                          allow_overage: checked
                        })}
                      />
                    ) : (
                      plan.allow_overage ? (
                        <Check className="h-4 w-4 text-emerald-500" />
                      ) : (
                        <X className="h-4 w-4 text-slate-300" />
                      )
                    )}
                  </TableCell>
                  <TableCell>
                    {editingPlan?.plan_slug === plan.plan_slug ? (
                      <Input
                        type="number"
                        value={editingPlan.overage_price_cents}
                        onChange={(e) => setEditingPlan({
                          ...editingPlan,
                          overage_price_cents: parseInt(e.target.value) || 0
                        })}
                        className="w-24 bg-white border-slate-300 text-slate-900"
                      />
                    ) : (
                      <span className="text-slate-700">
                        {plan.overage_price_cents > 0 ? `$${(plan.overage_price_cents / 100).toFixed(2)}` : '-'}
                      </span>
                    )}
                  </TableCell>
                  <TableCell>
                    <span className="text-xs text-slate-400 font-mono">
                      {plan.stripe_price_id || '-'}
                    </span>
                  </TableCell>
                  <TableCell>
                    {editingPlan?.plan_slug === plan.plan_slug ? (
                      <Switch
                        checked={editingPlan.is_active}
                        onCheckedChange={(checked) => setEditingPlan({
                          ...editingPlan,
                          is_active: checked
                        })}
                      />
                    ) : (
                      <Badge className={plan.is_active ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"}>
                        {plan.is_active ? "Active" : "Inactive"}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <span className="text-indigo-600 font-medium">{plan.account_count}</span>
                  </TableCell>
                  <TableCell>
                    {editingPlan?.plan_slug === plan.plan_slug ? (
                      <div className="flex gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            updatePlan(plan.plan_slug, {
                              monthly_report_limit: editingPlan.monthly_report_limit,
                              allow_overage: editingPlan.allow_overage,
                              overage_price_cents: editingPlan.overage_price_cents,
                              is_active: editingPlan.is_active,
                            })
                          }}
                          disabled={saving === plan.plan_slug}
                          className="text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                        >
                          {saving === plan.plan_slug ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Save className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setEditingPlan(null)}
                          className="text-slate-500 hover:text-slate-700 hover:bg-slate-100"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ) : (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setEditingPlan(plan)}
                        className="text-slate-500 hover:text-slate-900 hover:bg-slate-100"
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

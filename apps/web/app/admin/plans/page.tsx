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
  Users,
  FileText,
  DollarSign,
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
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Plans & Pricing</h1>
          <p className="text-gray-400 mt-1">Manage subscription plans and pricing tiers</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-violet-600 hover:bg-violet-700">
              <Plus className="h-4 w-4 mr-2" />
              Create Plan
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-gray-900 border-gray-800">
            <DialogHeader>
              <DialogTitle className="text-white">Create New Plan</DialogTitle>
              <DialogDescription className="text-gray-400">
                Add a new subscription plan to your platform
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gray-300">Plan Slug</Label>
                  <Input
                    value={newPlan.plan_slug}
                    onChange={(e) => setNewPlan({ ...newPlan, plan_slug: e.target.value })}
                    placeholder="e.g., enterprise"
                    className="bg-gray-800 border-gray-700 text-white"
                  />
                </div>
                <div>
                  <Label className="text-gray-300">Plan Name</Label>
                  <Input
                    value={newPlan.plan_name}
                    onChange={(e) => setNewPlan({ ...newPlan, plan_name: e.target.value })}
                    placeholder="e.g., Enterprise"
                    className="bg-gray-800 border-gray-700 text-white"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gray-300">Monthly Report Limit</Label>
                  <Input
                    type="number"
                    value={newPlan.monthly_report_limit}
                    onChange={(e) => setNewPlan({ ...newPlan, monthly_report_limit: parseInt(e.target.value) || 0 })}
                    className="bg-gray-800 border-gray-700 text-white"
                  />
                </div>
                <div>
                  <Label className="text-gray-300">Overage Price (cents)</Label>
                  <Input
                    type="number"
                    value={newPlan.overage_price_cents}
                    onChange={(e) => setNewPlan({ ...newPlan, overage_price_cents: parseInt(e.target.value) || 0 })}
                    className="bg-gray-800 border-gray-700 text-white"
                  />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  checked={newPlan.allow_overage}
                  onCheckedChange={(checked) => setNewPlan({ ...newPlan, allow_overage: checked })}
                />
                <Label className="text-gray-300">Allow overage (pay per extra report)</Label>
              </div>
              <div>
                <Label className="text-gray-300">Description</Label>
                <Input
                  value={newPlan.description}
                  onChange={(e) => setNewPlan({ ...newPlan, description: e.target.value })}
                  placeholder="Brief description of the plan"
                  className="bg-gray-800 border-gray-700 text-white"
                />
              </div>
              <Button
                onClick={createPlan}
                disabled={saving === "new" || !newPlan.plan_slug || !newPlan.plan_name}
                className="w-full bg-violet-600 hover:bg-violet-700"
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
          <Card key={plan.plan_slug} className={`bg-gray-900 border-gray-800 ${!plan.is_active ? 'opacity-50' : ''}`}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg text-white">{plan.plan_name}</CardTitle>
                <Badge variant={plan.is_active ? "default" : "secondary"} className={plan.is_active ? "bg-green-500/20 text-green-400" : ""}>
                  {plan.is_active ? "Active" : "Inactive"}
                </Badge>
              </div>
              <CardDescription className="text-gray-500">{plan.plan_slug}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-400 text-sm">Reports/mo</span>
                  <span className="text-white font-bold">{plan.monthly_report_limit}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400 text-sm">Accounts</span>
                  <span className="text-violet-400 font-medium">{plan.account_count}</span>
                </div>
                {plan.allow_overage && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400 text-sm">Overage</span>
                    <span className="text-green-400 font-medium">${(plan.overage_price_cents / 100).toFixed(2)}/ea</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Plans Table */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white">Plan Configuration</CardTitle>
          <CardDescription className="text-gray-400">
            Edit plan limits, pricing, and availability
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow className="border-gray-800 hover:bg-transparent">
                <TableHead className="text-gray-400">Plan</TableHead>
                <TableHead className="text-gray-400">Reports/Month</TableHead>
                <TableHead className="text-gray-400">Overage</TableHead>
                <TableHead className="text-gray-400">Overage Price</TableHead>
                <TableHead className="text-gray-400">Stripe ID</TableHead>
                <TableHead className="text-gray-400">Status</TableHead>
                <TableHead className="text-gray-400">Accounts</TableHead>
                <TableHead className="text-gray-400 w-20">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {plans.map((plan) => (
                <TableRow key={plan.plan_slug} className="border-gray-800">
                  <TableCell>
                    <div>
                      <p className="text-white font-medium">{plan.plan_name}</p>
                      <p className="text-xs text-gray-500">{plan.plan_slug}</p>
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
                        className="w-24 bg-gray-800 border-gray-700 text-white"
                      />
                    ) : (
                      <span className="text-gray-300">{plan.monthly_report_limit}</span>
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
                        <Check className="h-4 w-4 text-green-400" />
                      ) : (
                        <X className="h-4 w-4 text-gray-600" />
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
                        className="w-24 bg-gray-800 border-gray-700 text-white"
                      />
                    ) : (
                      <span className="text-gray-300">
                        {plan.overage_price_cents > 0 ? `$${(plan.overage_price_cents / 100).toFixed(2)}` : '-'}
                      </span>
                    )}
                  </TableCell>
                  <TableCell>
                    <span className="text-xs text-gray-500 font-mono">
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
                      <Badge className={plan.is_active ? "bg-green-500/20 text-green-400 border-green-500/30" : "bg-gray-500/20 text-gray-400"}>
                        {plan.is_active ? "Active" : "Inactive"}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <span className="text-violet-400 font-medium">{plan.account_count}</span>
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
                          className="text-green-400 hover:text-green-300"
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
                          className="text-gray-400 hover:text-gray-300"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ) : (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setEditingPlan(plan)}
                        className="text-gray-400 hover:text-white"
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

"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  ArrowLeft,
  Building,
  Users,
  FileText,
  Save,
  Loader2,
  AlertTriangle,
  CheckCircle,
} from "lucide-react"
import { planLimitLabel } from "@/lib/plan-limit-label"

interface AccountDetail {
  account: {
    id: string
    name: string
    slug: string
    account_type: string
    plan_slug: string
    monthly_report_limit_override: number | null
    sponsor_account_id: string | null
    created_at: string
  }
  plan: {
    plan_name: string
    plan_slug: string
    monthly_report_limit: number
    /** The enforced market-report limit for this account, overrides included. */
    market_reports_limit: number
    allow_overage: boolean
    overage_price_cents: number
  }
  usage: {
    reports_this_month: number
    schedule_runs_this_month: number
  }
  decision: string
  info: {
    ratio: number
    message: string
    can_proceed: boolean
    overage_count: number
  }
}

interface PlanRow {
  plan_slug: string
  plan_name: string
  is_active: boolean
  /** What the gate enforces (`plans.market_reports_limit`). */
  market_reports_limit: number | null
}

export default function AccountDetailPage() {
  const params = useParams()
  const router = useRouter()
  const accountId = params.id as string

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [account, setAccount] = useState<AccountDetail | null>(null)
  const [plans, setPlans] = useState<PlanRow[]>([])

  // Form state
  const [planSlug, setPlanSlug] = useState("")
  const [limitOverride, setLimitOverride] = useState("")
  const [isActive, setIsActive] = useState(true)

  useEffect(() => {
    fetch("/api/v1/admin/plans", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : { plans: [] }))
      .then((d) => setPlans(d.plans || []))
      .catch(() => setPlans([]))
  }, [])

  useEffect(() => {
    fetchAccount()
  }, [accountId])

  async function fetchAccount() {
    try {
      setLoading(true)
      const res = await fetch(`/api/v1/admin/accounts/${accountId}/plan-usage`, {
        credentials: "include",
      })
      if (!res.ok) throw new Error("Failed to fetch account")
      const data = await res.json()
      setAccount(data)
      setPlanSlug(data.account.plan_slug)
      setLimitOverride(data.account.monthly_report_limit_override?.toString() || "")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load account")
    } finally {
      setLoading(false)
    }
  }

  async function handleSave() {
    try {
      setSaving(true)
      setError(null)
      setSuccess(null)

      const params = new URLSearchParams()

      if (planSlug !== account?.account.plan_slug) {
        params.set("plan_slug", planSlug)
      }

      const newLimit = limitOverride ? parseInt(limitOverride, 10) : 0
      const oldLimit = account?.account.monthly_report_limit_override || 0
      if (newLimit !== oldLimit) {
        params.set("monthly_report_limit_override", String(newLimit))
      }

      if (params.toString() === "") {
        setSuccess("No changes to save")
        return
      }

      const res = await fetch(`/api/v1/admin/accounts/${accountId}?${params.toString()}`, {
        method: "PATCH",
        credentials: "include",
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || "Failed to update account")
      }

      setSuccess("Account updated successfully")
      fetchAccount()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save changes")
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    )
  }

  if (!account) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 mx-auto text-red-500 mb-4" />
        <h3 className="text-lg font-semibold text-slate-900 mb-2">Account not found</h3>
        <Link href="/admin/accounts">
          <Button variant="outline" className="border-slate-300">Back to Accounts</Button>
        </Link>
      </div>
    )
  }

  const effectiveLimit = account.plan.market_reports_limit
  const usagePercent = Math.round((account.usage.reports_this_month / effectiveLimit) * 100)

  return (
    <div className="max-w-4xl space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/admin/accounts">
          <Button variant="ghost" size="icon" className="text-slate-600 hover:text-slate-900">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-slate-900">{account.account.name}</h1>
          <p className="text-slate-500 mt-1">{account.account.slug}</p>
        </div>
        <Badge
          variant="outline"
          className={
            account.account.account_type === "INDUSTRY_AFFILIATE"
              ? "border-violet-300 text-violet-700 bg-violet-50"
              : "border-slate-300 text-slate-600"
          }
        >
          {account.account.account_type === "INDUSTRY_AFFILIATE" ? "Affiliate" : "Regular"}
        </Badge>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          {error}
        </div>
      )}

      {success && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-3 rounded-lg flex items-center gap-2">
          <CheckCircle className="h-4 w-4" />
          {success}
        </div>
      )}

      {/* Usage Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Reports This Month</p>
                <p className="text-2xl font-bold text-slate-900">{account.usage.reports_this_month}</p>
                <p className="text-xs text-slate-400">of {effectiveLimit} ({usagePercent}%)</p>
              </div>
              <FileText className="h-8 w-8 text-violet-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Plan Limit</p>
                <p className="text-2xl font-bold text-slate-900">{account.plan.market_reports_limit}</p>
                <p className="text-xs text-slate-400">{account.plan.plan_name}</p>
              </div>
              <Building className="h-8 w-8 text-blue-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Override</p>
                <p className="text-2xl font-bold text-slate-900">
                  {account.account.monthly_report_limit_override || "-"}
                </p>
                <p className="text-xs text-slate-400">
                  {account.account.monthly_report_limit_override ? "Custom limit" : "Using plan"}
                </p>
              </div>
              <Users className="h-8 w-8 text-emerald-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Status</p>
                <p className={`text-2xl font-bold ${
                  account.decision === "ALLOW" ? "text-emerald-600" :
                  account.decision === "ALLOW_WITH_WARNING" ? "text-amber-600" :
                  "text-red-600"
                }`}>
                  {account.decision === "ALLOW" ? "OK" :
                   account.decision === "ALLOW_WITH_WARNING" ? "Warning" : "Blocked"}
                </p>
                <p className="text-xs text-slate-400">{account.info.message || "Within limits"}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Usage Progress */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-slate-900">Usage Progress</CardTitle>
          <CardDescription className="text-slate-500">Monthly report usage for this account</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">{account.usage.reports_this_month} / {effectiveLimit} reports</span>
              <span className={
                usagePercent >= 100 ? "text-red-600 font-semibold" :
                usagePercent >= 80 ? "text-amber-600" : "text-emerald-600"
              }>
                {usagePercent}%
              </span>
            </div>
            <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  usagePercent >= 100 ? "bg-red-500" :
                  usagePercent >= 80 ? "bg-amber-500" : "bg-emerald-500"
                }`}
                style={{ width: `${Math.min(usagePercent, 100)}%` }}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Edit Settings */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-slate-900">Account Settings</CardTitle>
          <CardDescription className="text-slate-500">Modify plan and limits for this account</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label className="text-slate-700">Plan</Label>
              <Select value={planSlug} onValueChange={setPlanSlug}>
                <SelectTrigger className="bg-white border-slate-300 text-slate-900">
                  <SelectValue placeholder="Select plan" />
                </SelectTrigger>
                <SelectContent className="bg-white border-slate-200">
                  {plans
                    .filter((p) => p.is_active || p.plan_slug === planSlug)
                    .map((p) => (
                      <SelectItem key={p.plan_slug} value={p.plan_slug}>
                        {p.plan_name} ({planLimitLabel(p.market_reports_limit)})
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-slate-400">Current: {account.plan.plan_name}</p>
            </div>

            <div className="space-y-2">
              <Label className="text-slate-700">Monthly Report Limit Override</Label>
              <Input
                type="number"
                min="0"
                placeholder={`Plan default: ${plans.find((p) => p.plan_slug === planSlug)?.market_reports_limit ?? account.plan.market_reports_limit}`}
                value={limitOverride}
                onChange={(e) => setLimitOverride(e.target.value)}
                className="bg-white border-slate-300 text-slate-900"
              />
              <p className="text-xs text-slate-400">Leave empty for plan default. Set 0 to remove.</p>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-200">
            <Button variant="outline" onClick={() => router.back()} className="border-slate-300 text-slate-700">
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving} className="bg-violet-600 hover:bg-violet-700">
              {saving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save Changes
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

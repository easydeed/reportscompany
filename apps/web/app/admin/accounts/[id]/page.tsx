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

export default function AccountDetailPage() {
  const params = useParams()
  const router = useRouter()
  const accountId = params.id as string

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [account, setAccount] = useState<AccountDetail | null>(null)

  // Form state
  const [planSlug, setPlanSlug] = useState("")
  const [limitOverride, setLimitOverride] = useState("")
  const [isActive, setIsActive] = useState(true)

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
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    )
  }

  if (!account) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 mx-auto text-red-500 mb-4" />
        <h3 className="text-lg font-semibold text-white mb-2">Account not found</h3>
        <Link href="/admin/accounts">
          <Button variant="outline" className="border-gray-700">Back to Accounts</Button>
        </Link>
      </div>
    )
  }

  const effectiveLimit = account.account.monthly_report_limit_override || account.plan.monthly_report_limit
  const usagePercent = Math.round((account.usage.reports_this_month / effectiveLimit) * 100)

  return (
    <div className="max-w-4xl space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/admin/accounts">
          <Button variant="ghost" size="icon" className="text-gray-400 hover:text-white">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-white">{account.account.name}</h1>
          <p className="text-gray-400 mt-1">{account.account.slug}</p>
        </div>
        <Badge
          variant="outline"
          className={
            account.account.account_type === "INDUSTRY_AFFILIATE"
              ? "border-violet-500/50 text-violet-400"
              : "border-gray-700 text-gray-400"
          }
        >
          {account.account.account_type === "INDUSTRY_AFFILIATE" ? "Affiliate" : "Regular"}
        </Badge>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-500/10 border border-green-500/30 text-green-400 px-4 py-3 rounded-lg flex items-center gap-2">
          <CheckCircle className="h-4 w-4" />
          {success}
        </div>
      )}

      {/* Usage Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Reports This Month</p>
                <p className="text-2xl font-bold text-white">{account.usage.reports_this_month}</p>
                <p className="text-xs text-gray-500">of {effectiveLimit} ({usagePercent}%)</p>
              </div>
              <FileText className="h-8 w-8 text-violet-400/30" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Plan Limit</p>
                <p className="text-2xl font-bold text-white">{account.plan.monthly_report_limit}</p>
                <p className="text-xs text-gray-500">{account.plan.plan_name}</p>
              </div>
              <Building className="h-8 w-8 text-blue-400/30" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Override</p>
                <p className="text-2xl font-bold text-white">
                  {account.account.monthly_report_limit_override || "-"}
                </p>
                <p className="text-xs text-gray-500">
                  {account.account.monthly_report_limit_override ? "Custom limit" : "Using plan"}
                </p>
              </div>
              <Users className="h-8 w-8 text-green-400/30" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Status</p>
                <p className={`text-2xl font-bold ${
                  account.decision === "ALLOW" ? "text-green-400" :
                  account.decision === "ALLOW_WITH_WARNING" ? "text-yellow-400" :
                  "text-red-400"
                }`}>
                  {account.decision === "ALLOW" ? "OK" :
                   account.decision === "ALLOW_WITH_WARNING" ? "Warning" : "Blocked"}
                </p>
                <p className="text-xs text-gray-500">{account.info.message || "Within limits"}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Usage Progress */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white">Usage Progress</CardTitle>
          <CardDescription className="text-gray-400">Monthly report usage for this account</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">{account.usage.reports_this_month} / {effectiveLimit} reports</span>
              <span className={
                usagePercent >= 100 ? "text-red-400 font-semibold" :
                usagePercent >= 80 ? "text-yellow-400" : "text-green-400"
              }>
                {usagePercent}%
              </span>
            </div>
            <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  usagePercent >= 100 ? "bg-red-500" :
                  usagePercent >= 80 ? "bg-yellow-500" : "bg-green-500"
                }`}
                style={{ width: `${Math.min(usagePercent, 100)}%` }}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Edit Settings */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white">Account Settings</CardTitle>
          <CardDescription className="text-gray-400">Modify plan and limits for this account</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label className="text-gray-300">Plan</Label>
              <Select value={planSlug} onValueChange={setPlanSlug}>
                <SelectTrigger className="bg-gray-800 border-gray-700 text-white">
                  <SelectValue placeholder="Select plan" />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  <SelectItem value="free">Free (5 reports/month)</SelectItem>
                  <SelectItem value="pro">Pro (300 reports/month)</SelectItem>
                  <SelectItem value="team">Team (1,000 reports/month)</SelectItem>
                  <SelectItem value="affiliate">Affiliate (5,000 reports/month)</SelectItem>
                  <SelectItem value="sponsored_free">Sponsored Free (10 reports/month)</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-500">Current: {account.plan.plan_name}</p>
            </div>

            <div className="space-y-2">
              <Label className="text-gray-300">Monthly Report Limit Override</Label>
              <Input
                type="number"
                min="0"
                placeholder={`Plan default: ${account.plan.monthly_report_limit}`}
                value={limitOverride}
                onChange={(e) => setLimitOverride(e.target.value)}
                className="bg-gray-800 border-gray-700 text-white"
              />
              <p className="text-xs text-gray-500">Leave empty for plan default. Set 0 to remove.</p>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-800">
            <Button variant="outline" onClick={() => router.back()} className="border-gray-700 text-gray-300">
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

"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
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
  Calendar,
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

export default function AdminAccountDetailPage() {
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
      const res = await fetch(`/api/proxy/v1/admin/accounts/${accountId}/plan-usage`, {
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

      const updates: Record<string, unknown> = {}

      if (planSlug !== account?.account.plan_slug) {
        updates.plan_slug = planSlug
      }

      const newLimit = limitOverride ? parseInt(limitOverride, 10) : 0
      const oldLimit = account?.account.monthly_report_limit_override || 0
      if (newLimit !== oldLimit) {
        updates.monthly_report_limit_override = newLimit
      }

      if (Object.keys(updates).length === 0) {
        setSuccess("No changes to save")
        return
      }

      const queryParams = new URLSearchParams()
      Object.entries(updates).forEach(([key, value]) => {
        queryParams.set(key, String(value))
      })

      const res = await fetch(`/api/proxy/v1/admin/accounts/${accountId}?${queryParams.toString()}`, {
        method: "PATCH",
        credentials: "include",
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || "Failed to update account")
      }

      setSuccess("Account updated successfully")
      fetchAccount() // Refresh data
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save changes")
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!account) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 mx-auto text-red-500 mb-4" />
        <h3 className="text-lg font-semibold mb-2">Account not found</h3>
        <Link href="/app/admin/accounts">
          <Button variant="outline">Back to Accounts</Button>
        </Link>
      </div>
    )
  }

  const effectiveLimit = account.account.monthly_report_limit_override || account.plan.monthly_report_limit
  const usagePercent = Math.round((account.usage.reports_this_month / effectiveLimit) * 100)

  return (
    <div className="max-w-4xl">
      <div className="flex items-center gap-4 mb-6">
        <Link href="/app/admin/accounts">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-display font-bold text-foreground">{account.account.name}</h1>
          <p className="text-muted-foreground mt-1">{account.account.slug}</p>
        </div>
        <div className="ml-auto flex gap-2">
          <Badge variant={account.account.account_type === "INDUSTRY_AFFILIATE" ? "default" : "secondary"}>
            {account.account.account_type === "INDUSTRY_AFFILIATE" ? "Affiliate" : "Regular"}
          </Badge>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6 flex items-center gap-2">
          <CheckCircle className="h-4 w-4" />
          {success}
        </div>
      )}

      {/* Usage Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reports This Month</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{account.usage.reports_this_month}</div>
            <p className="text-xs text-muted-foreground">
              of {effectiveLimit} ({usagePercent}%)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Plan Limit</CardTitle>
            <Building className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{account.plan.monthly_report_limit}</div>
            <p className="text-xs text-muted-foreground">
              {account.plan.plan_name} plan
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Override</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {account.account.monthly_report_limit_override || "-"}
            </div>
            <p className="text-xs text-muted-foreground">
              {account.account.monthly_report_limit_override ? "Custom limit" : "Using plan limit"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${
              account.decision === "ALLOW" ? "text-green-600" :
              account.decision === "ALLOW_WITH_WARNING" ? "text-yellow-600" :
              "text-red-600"
            }`}>
              {account.decision === "ALLOW" ? "OK" :
               account.decision === "ALLOW_WITH_WARNING" ? "Warning" : "Blocked"}
            </div>
            <p className="text-xs text-muted-foreground">
              {account.info.message || "Within limits"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Usage Progress */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Usage Progress</CardTitle>
          <CardDescription>Monthly report usage for this account</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>{account.usage.reports_this_month} / {effectiveLimit} reports</span>
              <span className={
                usagePercent >= 100 ? "text-red-600 font-semibold" :
                usagePercent >= 80 ? "text-yellow-600" : "text-green-600"
              }>
                {usagePercent}%
              </span>
            </div>
            <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  usagePercent >= 100 ? "bg-red-500" :
                  usagePercent >= 80 ? "bg-yellow-500" : "bg-green-500"
                }`}
                style={{ width: `${Math.min(usagePercent, 100)}%` }}
              />
            </div>
            {usagePercent > 100 && (
              <p className="text-sm text-red-600">
                {account.info.overage_count} reports over limit
                {account.plan.allow_overage && (
                  <span> (${(account.plan.overage_price_cents / 100).toFixed(2)} each)</span>
                )}
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Edit Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Account Settings</CardTitle>
          <CardDescription>Modify plan and limits for this account</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label htmlFor="plan">Plan</Label>
              <Select value={planSlug} onValueChange={setPlanSlug}>
                <SelectTrigger id="plan">
                  <SelectValue placeholder="Select plan" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="free">Free (5 reports/month)</SelectItem>
                  <SelectItem value="pro">Pro (300 reports/month)</SelectItem>
                  <SelectItem value="team">Team (1,000 reports/month)</SelectItem>
                  <SelectItem value="affiliate">Affiliate (5,000 reports/month)</SelectItem>
                  <SelectItem value="sponsored_free">Sponsored Free (10 reports/month)</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Current: {account.plan.plan_name}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="limit">Monthly Report Limit Override</Label>
              <Input
                id="limit"
                type="number"
                min="0"
                placeholder={`Plan default: ${account.plan.monthly_report_limit}`}
                value={limitOverride}
                onChange={(e) => setLimitOverride(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Leave empty to use plan default. Set 0 to remove override.
              </p>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button variant="outline" onClick={() => router.back()}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving}>
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

      {/* Account Info */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Account Information</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-muted-foreground">Account ID</dt>
              <dd className="font-mono text-xs">{account.account.id}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Created</dt>
              <dd>{new Date(account.account.created_at).toLocaleDateString()}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Type</dt>
              <dd>{account.account.account_type}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Overage Allowed</dt>
              <dd>{account.plan.allow_overage ? "Yes" : "No"}</dd>
            </div>
            {account.account.sponsor_account_id && (
              <div className="col-span-2">
                <dt className="text-muted-foreground">Sponsor Account</dt>
                <dd className="font-mono text-xs">{account.account.sponsor_account_id}</dd>
              </div>
            )}
          </dl>
        </CardContent>
      </Card>
    </div>
  )
}

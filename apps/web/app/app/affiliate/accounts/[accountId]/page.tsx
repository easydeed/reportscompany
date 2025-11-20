"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Building2, TrendingUp, FileText, ArrowLeft, Ban, Check } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"

type AccountDetail = {
  account: {
    account_id: string
    name: string
    plan_slug: string
    is_active: boolean
    created_at: string
  }
  metrics: {
    reports_this_month: number
    total_reports: number
    last_report_at: string | null
  }
}

export default function SponsoredAccountDetailPage() {
  const params = useParams()
  const router = useRouter()
  const { toast } = useToast()
  const accountId = params.accountId as string

  const [data, setData] = useState<AccountDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    loadData()
  }, [accountId])

  async function loadData() {
    setLoading(true)
    try {
      const res = await fetch(`/api/proxy/v1/affiliate/accounts/${accountId}`, {
        cache: "no-store",
      })

      if (!res.ok) {
        throw new Error("Failed to load account details")
      }

      const json = await res.json()
      setData(json)
    } catch (error) {
      console.error("Failed to load account:", error)
      toast({
        title: "Error",
        description: "Failed to load account details",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  async function handleSuspend() {
    setActionLoading(true)
    try {
      const res = await fetch(`/api/proxy/v1/affiliate/accounts/${accountId}/deactivate`, {
        method: "POST",
      })

      if (!res.ok) {
        throw new Error("Failed to suspend account")
      }

      toast({
        title: "Success",
        description: `${data?.account.name} has been suspended`,
      })
      loadData()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to suspend account",
        variant: "destructive",
      })
    } finally {
      setActionLoading(false)
    }
  }

  async function handleReactivate() {
    setActionLoading(true)
    try {
      const res = await fetch(`/api/proxy/v1/affiliate/accounts/${accountId}/reactivate`, {
        method: "POST",
      })

      if (!res.ok) {
        throw new Error("Failed to reactivate account")
      }

      toast({
        title: "Success",
        description: `${data?.account.name} has been reactivated`,
      })
      loadData()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to reactivate account",
        variant: "destructive",
      })
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading account details...</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">Account not found or not accessible</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const { account, metrics } = data

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.push("/app/affiliate")}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Button>
        </div>
        {account.is_active ? (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" disabled={actionLoading}>
                <Ban className="h-4 w-4 mr-2" />
                Suspend Agent
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Suspend {account.name}?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will mark the account as inactive. Scheduled reports may stop being sent.
                  You can reactivate them later.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleSuspend}>Suspend</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        ) : (
          <Button onClick={handleReactivate} disabled={actionLoading}>
            <Check className="h-4 w-4 mr-2" />
            Reactivate Agent
          </Button>
        )}
      </div>

      {/* Account Info Card */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-violet-100 p-3">
                <Building2 className="h-6 w-6 text-violet-600" />
              </div>
              <div>
                <CardTitle className="text-2xl">{account.name}</CardTitle>
                <CardDescription className="mt-1">
                  Sponsored Agent Account
                </CardDescription>
              </div>
            </div>
            <Badge variant={account.is_active ? "default" : "secondary"}>
              {account.is_active ? "Active" : "Suspended"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-sm text-muted-foreground">Plan</p>
              <p className="text-lg font-semibold capitalize">{account.plan_slug}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Created</p>
              <p className="text-lg font-semibold">
                {new Date(account.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metrics Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reports This Month</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.reports_this_month}</div>
            <p className="text-xs text-muted-foreground">Current billing period</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Reports</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.total_reports}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Activity</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics.last_report_at
                ? new Date(metrics.last_report_at).toLocaleDateString()
                : "—"}
            </div>
            <p className="text-xs text-muted-foreground">Most recent report</p>
          </CardContent>
        </Card>
      </div>

      {!account.is_active && (
        <Card className="border-orange-200 bg-orange-50/50">
          <CardHeader>
            <CardTitle className="text-orange-900">Account Suspended</CardTitle>
            <CardDescription className="text-orange-700">
              This account is currently inactive. Scheduled reports may not be sent.
              Reactivate the account to resume normal operation.
            </CardDescription>
          </CardHeader>
        </Card>
      )}
    </div>
  )
}


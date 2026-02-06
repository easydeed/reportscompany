"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  CreditCard,
  Loader2,
  Check,
  Zap,
  BarChart3,
  Calendar,
  FileText,
  Mail,
  Download,
  ExternalLink,
  Sparkles,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { useRouter } from "next/navigation"
import { cn } from "@/lib/utils"

type PlanUsageData = {
  account: {
    id: string
    name: string
    account_type: string
    plan_slug: string
    billing_status?: string | null
  }
  plan: {
    plan_name: string
    plan_slug: string
    monthly_report_limit: number
  }
  usage: {
    report_count: number
  }
  stripe_billing?: {
    stripe_price_id: string
    amount: number
    currency: string
    interval: string
    interval_count: number
    nickname?: string | null
    current_period_end?: string
  } | null
}

const plans = [
  {
    name: "Free",
    slug: "free",
    price: 0,
    features: ["5 reports / month", "6 report types", "PDF export", "Email support"],
  },
  {
    name: "Solo Agent",
    slug: "solo",
    price: 29,
    popular: true,
    features: [
      "Unlimited reports",
      "All report types",
      "Custom branding",
      "Scheduled reports",
      "Email delivery",
      "Priority support",
    ],
  },
]

export default function BillingPage() {
  const [loading, setLoading] = useState(true)
  const [billingLoading, setBillingLoading] = useState(false)
  const { toast } = useToast()
  const router = useRouter()

  const [billingData, setBillingData] = useState<PlanUsageData | null>(null)

  useEffect(() => {
    loadBilling()
  }, [])

  async function loadBilling() {
    setLoading(true)
    try {
      const res = await fetch("/api/proxy/v1/account/plan-usage", {
        cache: "no-store",
        credentials: "include",
      })

      if (res.ok) {
        const data = await res.json()
        setBillingData(data)
      }
    } catch (error) {
      console.error("Failed to load billing:", error)
      toast({
        title: "Error",
        description: "Failed to load billing information",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  async function checkout(planSlug: string) {
    setBillingLoading(true)
    try {
      const res = await fetch("/api/proxy/v1/billing/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan: planSlug }),
      })
      const data = await res.json()
      if (res.ok && data.url) {
        router.push(data.url)
      } else {
        toast({
          title: "Error",
          description: data.detail || "Failed to start checkout",
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to start checkout",
        variant: "destructive",
      })
    } finally {
      setBillingLoading(false)
    }
  }

  async function openBillingPortal() {
    setBillingLoading(true)
    try {
      const res = await fetch("/api/proxy/v1/billing/portal", { method: "POST" })
      const data = await res.json()
      if (res.ok && data.url) {
        router.push(data.url)
      } else {
        toast({
          title: "Error",
          description: data.detail || "Failed to open billing portal",
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to open billing portal",
        variant: "destructive",
      })
    } finally {
      setBillingLoading(false)
    }
  }

  function getNextBillingDate(): string {
    if (!billingData?.stripe_billing?.current_period_end) return ""
    const date = new Date(billingData.stripe_billing.current_period_end)
    return date.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    })
  }

  function getUsagePercentage(): number {
    if (!billingData) return 0
    const limit = billingData.plan.monthly_report_limit
    if (limit === 0 || limit === null) return 0 // Unlimited
    return Math.min(100, (billingData.usage.report_count / limit) * 100)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mx-auto mb-4" />
          <p className="text-muted-foreground">Loading billing information...</p>
        </div>
      </div>
    )
  }

  const currentPlanSlug = billingData?.account.plan_slug || "free"
  const isUnlimited = billingData?.plan.monthly_report_limit === 0 || billingData?.plan.monthly_report_limit === null

  return (
    <div className="space-y-8 max-w-2xl">
      {/* Section Header */}
      <div>
        <h2 className="text-lg font-semibold">Billing</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Manage your subscription and view usage.
        </p>
      </div>

      {/* Current Plan Card */}
      <div className="bg-card border rounded-xl p-6">
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-4">
          Current Plan
        </h3>

        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-2xl font-bold">
                {billingData?.plan.plan_name || currentPlanSlug}
              </h4>
              {currentPlanSlug !== "free" && (
                <Badge className="bg-indigo-100 text-indigo-700 border-0">Active</Badge>
              )}
            </div>
            {billingData?.stripe_billing && (
              <p className="text-muted-foreground mt-1">
                ${(billingData.stripe_billing.amount / 100).toFixed(0)}/
                {billingData.stripe_billing.interval}
              </p>
            )}
          </div>

          {billingData?.stripe_billing && (
            <Button onClick={openBillingPortal} variant="outline" disabled={billingLoading}>
              <CreditCard className="w-4 h-4 mr-2" />
              Manage Subscription
              <ExternalLink className="w-3 h-3 ml-2" />
            </Button>
          )}
        </div>

        {/* Plan features */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          {currentPlanSlug === "free" ? (
            <>
              <div className="flex items-center gap-2 text-sm">
                <Check className="w-4 h-4 text-green-500" />5 reports / month
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Check className="w-4 h-4 text-green-500" />6 report types
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Check className="w-4 h-4 text-green-500" />PDF export
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Check className="w-4 h-4 text-green-500" />Email support
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center gap-2 text-sm">
                <Check className="w-4 h-4 text-green-500" />Unlimited reports
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Check className="w-4 h-4 text-green-500" />Custom branding
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Check className="w-4 h-4 text-green-500" />Scheduled reports
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Check className="w-4 h-4 text-green-500" />Email delivery
              </div>
            </>
          )}
        </div>

        {getNextBillingDate() && (
          <p className="text-sm text-muted-foreground">
            Next billing: {getNextBillingDate()}
          </p>
        )}
      </div>

      {/* Usage Card */}
      <div className="bg-card border rounded-xl p-6">
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-4">
          Usage This Month
        </h3>

        <div className="space-y-4">
          {/* Reports Generated */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-sm font-medium">
                <FileText className="w-4 h-4 text-muted-foreground" />
                Reports Generated
              </div>
              <span className="text-sm">
                {billingData?.usage.report_count || 0}
                {isUnlimited ? " of ∞" : ` of ${billingData?.plan.monthly_report_limit}`}
              </span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-indigo-600 rounded-full transition-all"
                style={{ width: isUnlimited ? "15%" : `${getUsagePercentage()}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Available Plans */}
      <div className="bg-card border rounded-xl p-6">
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-4">
          Available Plans
        </h3>

        <div className="grid sm:grid-cols-2 gap-4">
          {plans.map((plan) => {
            const isCurrent = currentPlanSlug === plan.slug
            return (
              <div
                key={plan.slug}
                className={cn(
                  "border rounded-xl p-5 relative",
                  plan.popular && "border-indigo-300 ring-1 ring-violet-200 dark:border-violet-700 dark:ring-violet-800",
                  isCurrent && "bg-muted/30"
                )}
              >
                {plan.popular && (
                  <Badge className="absolute -top-2.5 right-4 bg-indigo-600 text-white border-0">
                    <Sparkles className="w-3 h-3 mr-1" />
                    Popular
                  </Badge>
                )}

                <div className="mb-4">
                  <h4 className="font-semibold text-lg">{plan.name}</h4>
                  <div className="mt-1">
                    <span className="text-3xl font-bold">${plan.price}</span>
                    <span className="text-muted-foreground">/month</span>
                  </div>
                </div>

                <ul className="space-y-2 mb-5">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm">
                      <Check className="w-4 h-4 text-green-500 flex-shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>

                <Button
                  onClick={() => checkout(plan.slug)}
                  disabled={billingLoading || isCurrent}
                  variant={isCurrent ? "secondary" : plan.popular ? "default" : "outline"}
                  className="w-full"
                >
                  {isCurrent ? (
                    <>
                      <Check className="w-4 h-4 mr-2" />
                      Current Plan
                    </>
                  ) : plan.price > 0 ? (
                    <>
                      <Zap className="w-4 h-4 mr-2" />
                      Upgrade
                    </>
                  ) : (
                    "Downgrade"
                  )}
                </Button>
              </div>
            )
          })}
        </div>
      </div>

      {/* Payment Method */}
      {billingData?.stripe_billing && (
        <div className="bg-card border rounded-xl p-6">
          <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-4">
            Payment Method
          </h3>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-muted rounded-lg">
                <CreditCard className="w-5 h-5" />
              </div>
              <div>
                <p className="font-medium">Card on file</p>
                <p className="text-sm text-muted-foreground">
                  Managed through Stripe
                </p>
              </div>
            </div>

            <Button onClick={openBillingPortal} variant="ghost" disabled={billingLoading}>
              Update
              <ExternalLink className="w-3 h-3 ml-2" />
            </Button>
          </div>
        </div>
      )}

      {/* Billing History Link */}
      {billingData?.stripe_billing && (
        <div className="bg-card border rounded-xl p-6">
          <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-4">
            Billing History
          </h3>

          <p className="text-sm text-muted-foreground mb-4">
            View and download your past invoices in the Stripe billing portal.
          </p>

          <Button onClick={openBillingPortal} variant="outline" disabled={billingLoading}>
            <Download className="w-4 h-4 mr-2" />
            View All Invoices
            <ExternalLink className="w-3 h-3 ml-2" />
          </Button>
        </div>
      )}
    </div>
  )
}


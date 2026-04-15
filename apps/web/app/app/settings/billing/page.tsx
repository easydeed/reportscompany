"use client"

import { useState, useEffect } from "react"
import { usePlanUsage } from "@/hooks/use-api"
import type { PlanUsage } from "@/lib/types/plan"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  CreditCard,
  Loader2,
  Check,
  Zap,
  ExternalLink,
  Sparkles,
  Receipt,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { useRouter, useSearchParams } from "next/navigation"
import { cn } from "@/lib/utils"

type BillingData = PlanUsage & {
  account: {
    id: string
    name: string
    account_type: string
    plan_slug: string
    billing_status?: string | null
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

function UsageBar({ label, used, limit }: { label: string; used: number; limit: number }) {
  const isUnlimited = limit >= 99999
  const pct = isUnlimited ? 0 : Math.min((used / Math.max(limit, 1)) * 100, 100)
  const color = pct >= 100 ? "bg-red-500" : pct >= 80 ? "bg-amber-500" : "bg-indigo-500"

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[12px]">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">{isUnlimited ? "∞" : `${used} / ${limit}`}</span>
      </div>
      {!isUnlimited && (
        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className={cn("h-full rounded-full transition-all", color)}
            style={{ width: `${pct}%` }}
          />
        </div>
      )}
    </div>
  )
}

const plans = [
  {
    name: "Free",
    slug: "free",
    price: 0,
    features: [
      "3 Market Reports / month",
      "1 Automated Schedule",
      "1 Property Report / month",
      "CMA Lead Page",
    ],
  },
  {
    name: "Starter",
    slug: "starter",
    price: 29,
    popular: true,
    features: [
      "25 Market Reports / month",
      "3 Automated Schedules",
      "5 Property Reports / month",
      "CMA Lead Page",
      "AI Market Insights",
      "CSV Contact Import",
    ],
  },
  {
    name: "Pro",
    slug: "pro",
    price: 59,
    features: [
      "Unlimited Market Reports",
      "Unlimited Schedules",
      "25 Property Reports / month",
      "CMA Lead Page",
      "AI Market Insights",
      "Priority Generation",
    ],
  },
]

export default function BillingPage() {
  const { data: planData, isLoading } = usePlanUsage()
  const billingData = (planData as unknown as BillingData) ?? null
  const [billingLoading, setBillingLoading] = useState(false)
  const { toast } = useToast()
  const router = useRouter()
  const searchParams = useSearchParams()

  useEffect(() => {
    const checkoutStatus = searchParams.get("checkout")
    if (checkoutStatus === "success") {
      toast({ title: "Subscription activated", description: "Your plan has been upgraded successfully." })
      router.replace("/app/settings/billing")
    } else if (checkoutStatus === "cancelled") {
      toast({ title: "Checkout cancelled", description: "No changes were made to your plan.", variant: "destructive" })
      router.replace("/app/settings/billing")
    }
  }, [searchParams, toast, router])

  async function checkout(planSlug: string) {
    setBillingLoading(true)
    try {
      const res = await fetch("/api/proxy/v1/billing/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_slug: planSlug }),
      })
      const data = await res.json()
      if (res.ok && data.url) {
        router.push(data.url)
      } else {
        toast({
          title: "Error",
          description: typeof data.detail === "string"
            ? data.detail
            : data.detail?.message || "Failed to start checkout",
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
      const res = await fetch("/api/proxy/v1/billing/portal", { method: "GET" })
      const data = await res.json()
      if (res.ok && data.url) {
        router.push(data.url)
      } else {
        toast({
          title: "Error",
          description: typeof data.detail === "string"
            ? data.detail
            : data.detail?.message || "Failed to open billing portal",
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mx-auto mb-4" />
          <p className="text-muted-foreground text-sm">Loading billing information...</p>
        </div>
      </div>
    )
  }

  const currentPlanSlug = billingData?.account?.plan_slug || "free"
  const accountType = billingData?.account?.account_type || "REGULAR"
  const showStripeActions = accountType === "REGULAR" && currentPlanSlug !== "free"

  return (
    <div className="max-w-3xl">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">Billing</h1>
        <p className="text-[13px] text-muted-foreground mt-0.5">
          Manage your subscription and view usage.
        </p>
      </div>

      <div className="space-y-5">
        {/* Current Plan + Usage Row */}
        <div className="grid sm:grid-cols-2 gap-4">
          {/* Current Plan Card */}
          <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
            <div className="px-5 py-3 border-b border-border bg-muted/30">
              <h3 className="text-[13px] font-semibold text-foreground uppercase tracking-wide">Current Plan</h3>
            </div>
            <div className="p-5">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="text-xl font-bold text-foreground">
                      {billingData?.plan?.plan_name || currentPlanSlug}
                    </h4>
                    {currentPlanSlug !== "free" && (
                      <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200 text-[10px]">Active</Badge>
                    )}
                  </div>
                  {billingData?.stripe_billing && (
                    <p className="text-sm text-muted-foreground mt-0.5">
                      ${(billingData.stripe_billing.amount / 100).toFixed(0)}/{billingData.stripe_billing.interval}
                    </p>
                  )}
                </div>
              </div>

              {/* Plan features */}
              <div className="space-y-1.5 mb-4">
                {(plans.find(p => p.slug === currentPlanSlug)?.features || plans[0].features).map((feature, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Check className="w-3.5 h-3.5 text-emerald-500" />
                    {feature}
                  </div>
                ))}
              </div>

              {getNextBillingDate() && (
                <p className="text-[11px] text-muted-foreground">
                  Next billing: {getNextBillingDate()}
                </p>
              )}

              {billingData?.stripe_billing && (
                <Button onClick={openBillingPortal} variant="outline" size="sm" className="w-full mt-3" disabled={billingLoading}>
                  <CreditCard className="w-4 h-4 mr-1.5" />
                  Manage Subscription
                  <ExternalLink className="w-3 h-3 ml-1.5" />
                </Button>
              )}
            </div>
          </div>

          {/* Usage Card */}
          <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
            <div className="px-5 py-3 border-b border-border bg-muted/30">
              <h3 className="text-[13px] font-semibold text-foreground uppercase tracking-wide">Current Usage</h3>
            </div>
            <div className="p-5 space-y-3">
              {billingData?.limits ? (
                <>
                  <UsageBar
                    label="Market Reports"
                    used={billingData.limits.market_reports.used}
                    limit={billingData.limits.market_reports.limit}
                  />
                  <UsageBar
                    label="Active Schedules"
                    used={billingData.limits.schedules.used}
                    limit={billingData.limits.schedules.limit}
                  />
                  <UsageBar
                    label="Property Reports"
                    used={billingData.limits.property_reports.used}
                    limit={billingData.limits.property_reports.limit}
                  />
                </>
              ) : (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Sparkles className="w-4 h-4 text-emerald-500" />
                  Usage data loading…
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Available Plans Card — only for regular accounts */}
        {accountType === "REGULAR" && (
          <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
            <div className="px-5 py-3 border-b border-border bg-muted/30">
              <h3 className="text-[13px] font-semibold text-foreground uppercase tracking-wide">Available Plans</h3>
            </div>
            <div className="p-5">
              <div className="grid sm:grid-cols-3 gap-4">
                {plans.map((plan) => {
                  const isCurrent = currentPlanSlug === plan.slug
                  const isDowngrade = plan.price < (billingData?.stripe_billing?.amount ?? 0) / 100
                  return (
                    <div
                      key={plan.slug}
                      className={cn(
                        "border rounded-xl p-4 relative transition-all",
                        plan.popular && !isCurrent && "border-indigo-300 ring-1 ring-indigo-100",
                        isCurrent && "bg-muted/30 border-border"
                      )}
                    >
                      {plan.popular && !isCurrent && (
                        <Badge className="absolute -top-2 right-3 bg-indigo-600 text-white border-0 text-[10px]">
                          <Sparkles className="w-3 h-3 mr-0.5" />
                          Popular
                        </Badge>
                      )}

                      <div className="mb-3">
                        <h4 className="font-semibold text-foreground">{plan.name}</h4>
                        <div className="mt-0.5">
                          <span className="text-2xl font-bold text-foreground">${plan.price}</span>
                          <span className="text-sm text-muted-foreground">/mo</span>
                        </div>
                      </div>

                      <ul className="space-y-1.5 mb-4">
                        {plan.features.map((feature, i) => (
                          <li key={i} className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Check className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                            {feature}
                          </li>
                        ))}
                      </ul>

                      <Button
                        onClick={() => checkout(plan.slug)}
                        disabled={billingLoading || isCurrent || plan.price === 0}
                        variant={isCurrent ? "secondary" : plan.popular ? "default" : "outline"}
                        size="sm"
                        className="w-full"
                      >
                        {isCurrent ? (
                          <>
                            <Check className="w-4 h-4 mr-1.5" />
                            Current Plan
                          </>
                        ) : plan.price > 0 ? (
                          <>
                            <Zap className="w-4 h-4 mr-1.5" />
                            {isDowngrade ? "Change Plan" : "Upgrade"}
                          </>
                        ) : (
                          "Free Plan"
                        )}
                      </Button>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        )}

        {accountType === "INDUSTRY_AFFILIATE" && (
          <div className="bg-muted/30 border border-border rounded-xl p-6 text-center">
            <p className="text-sm text-muted-foreground">
              Your affiliate plan is managed by TrendyReports. Contact support to make changes.
            </p>
            <a href="mailto:support@trendyreports.io" className="text-sm text-primary hover:underline mt-2 inline-block">
              support@trendyreports.io
            </a>
          </div>
        )}

        {/* Payment & Invoices Row — only for paying Stripe customers */}
        {showStripeActions && billingData?.stripe_billing && (
          <div className="grid sm:grid-cols-2 gap-4">
            {/* Payment Method */}
            <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
              <div className="px-5 py-3 border-b border-border bg-muted/30">
                <h3 className="text-[13px] font-semibold text-foreground uppercase tracking-wide">Payment Method</h3>
              </div>
              <div className="p-5">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                    <CreditCard className="w-5 h-5 text-slate-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">Card on file</p>
                    <p className="text-xs text-muted-foreground">Managed through Stripe</p>
                  </div>
                </div>
                <Button onClick={openBillingPortal} variant="outline" size="sm" className="w-full" disabled={billingLoading}>
                  Update Card
                  <ExternalLink className="w-3 h-3 ml-1.5" />
                </Button>
              </div>
            </div>

            {/* Billing History */}
            <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
              <div className="px-5 py-3 border-b border-border bg-muted/30">
                <h3 className="text-[13px] font-semibold text-foreground uppercase tracking-wide">Billing History</h3>
              </div>
              <div className="p-5">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                    <Receipt className="w-5 h-5 text-slate-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">Invoices</p>
                    <p className="text-xs text-muted-foreground">View past invoices in Stripe</p>
                  </div>
                </div>
                <Button onClick={openBillingPortal} variant="outline" size="sm" className="w-full" disabled={billingLoading}>
                  View Invoices
                  <ExternalLink className="w-3 h-3 ml-1.5" />
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

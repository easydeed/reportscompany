"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CreditCard, Check, Shield } from "lucide-react"
import { useRouter } from "next/navigation"

type PlanUsageData = {
  account: {
    id: string
    name: string
    account_type: string
    plan_slug: string
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
    amount: number // cents
    currency: string
    interval: string
    interval_count: number
    nickname?: string | null
  } | null
}

// Helper to format price display from Stripe billing data
function getPlanDisplay(data: PlanUsageData) {
  const sb = data.stripe_billing
  let planName = data.plan.plan_name || data.account.plan_slug
  let priceDisplay = ""

  if (sb && sb.amount != null && sb.currency && sb.interval) {
    const dollars = (sb.amount / 100).toFixed(2)
    const interval = sb.interval // 'month'
    planName = sb.nickname || planName
    priceDisplay = `$${dollars} / ${interval}`
  }

  return { planName, priceDisplay }
}

const plans = [
  {
    name: "Starter",
    slug: "free",
    price: "$0",
    period: "/month",
    description: "Perfect for individual agents",
    features: ["10 reports / month", "6 report types", "PDF export", "Email support"],
  },
  {
    name: "Professional",
    slug: "pro",
    price: "$99",
    period: "/month",
    description: "For growing teams",
    features: ["500 reports / month", "All report types", "API access", "Custom branding", "Priority support"],
    popular: true,
  },
  {
    name: "Team",
    slug: "team",
    price: "$299",
    period: "/month",
    description: "For large organizations",
    features: ["Unlimited reports", "White-label", "Dedicated support", "Custom integrations", "SLA guarantee"],
  },
]

export default function BillingPage() {
  const [data, setData] = useState<PlanUsageData | null>(null)
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  useEffect(() => {
    async function loadData() {
      const res = await fetch("/api/proxy/v1/account/plan-usage", { cache: "no-store" })
      if (res.ok) {
        const json = await res.json()
        setData(json)
      }
    }
    loadData()
  }, [])

  async function checkout(planSlug: string) {
    setLoading(true)
    try {
      const res = await fetch("/api/proxy/v1/billing/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan: planSlug }),
      })
      const j = await res.json()
      if (res.ok && j.url) {
        router.push(j.url)
      } else {
        console.error("Checkout failed:", j.detail || "Unknown error")
      }
    } catch (error) {
      console.error("Error during checkout:", error)
    } finally {
      setLoading(false)
    }
  }

  async function openBillingPortal() {
    setLoading(true)
    try {
      const res = await fetch("/api/proxy/v1/billing/portal", { method: "POST" })
      const j = await res.json()
      if (res.ok && j.url) {
        router.push(j.url)
      } else {
        console.error("Billing portal failed:", j.detail || "Unknown error")
      }
    } catch (error) {
      console.error("Error opening billing portal:", error)
    } finally {
      setLoading(false)
    }
  }

  if (!data) {
    return (
      <div className="space-y-6">
        <h1 className="font-bold text-3xl mb-2">Billing</h1>
        <p className="text-muted-foreground">Loading billing information...</p>
      </div>
    )
  }

  const isAffiliate = data.account.account_type === "INDUSTRY_AFFILIATE"
  const { planName, priceDisplay } = getPlanDisplay(data)

  // Affiliate billing UI
  if (isAffiliate) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="font-bold text-3xl mb-2">Billing</h1>
          <p className="text-muted-foreground">Manage your affiliate plan</p>
        </div>

        <Card className="border-purple-200 bg-purple-50/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-purple-600" />
              Your Affiliate Plan
            </CardTitle>
            <CardDescription>
              Manage or cancel your affiliate subscription in the billing portal.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground mb-1">Current plan</p>
              <p className="text-lg font-semibold">{planName}</p>
              {priceDisplay && (
                <p className="text-sm text-slate-600 mt-1">
                  Billing: <strong>{priceDisplay}</strong>
                </p>
              )}
            </div>
            <div className="pt-4 border-t">
              <Button onClick={openBillingPortal} disabled={loading}>
                <CreditCard className="w-4 h-4 mr-2" />
                {loading ? "Loading..." : "Manage billing"}
              </Button>
              <p className="text-xs text-slate-500 mt-2">
                You can update your payment method or cancel your subscription in the Stripe billing portal.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Agent billing UI
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-bold text-3xl mb-2">Billing</h1>
        <p className="text-muted-foreground">Manage your subscription and billing details</p>
      </div>

      {data.account.plan_slug && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="w-5 h-5" />
              Current Plan
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <p className="text-sm text-muted-foreground">Plan</p>
                <p className="text-lg font-semibold">{planName}</p>
                {priceDisplay && (
                  <p className="text-sm text-slate-600">
                    {priceDisplay}
                  </p>
                )}
              </div>
              <div className="flex-1">
                <p className="text-sm text-muted-foreground">Usage</p>
                <p className="text-lg font-semibold">
                  {data.usage.report_count} / {data.plan.monthly_report_limit} reports
                </p>
                <p className="text-xs text-slate-500">This month</p>
              </div>
            </div>
            {data.stripe_billing && (
              <Button onClick={openBillingPortal} variant="outline" disabled={loading}>
                {loading ? "Loading..." : "Manage Billing"}
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      <div>
        <h2 className="text-2xl font-semibold mb-4">Available Plans</h2>
        <div className="grid gap-6 md:grid-cols-3">
          {plans.map((plan) => (
            <Card key={plan.slug} className={plan.popular ? "border-primary shadow-lg" : ""}>
              <CardHeader>
                {plan.popular && (
                  <Badge className="w-fit mb-2" variant="default">
                    Most Popular
                  </Badge>
                )}
                <CardTitle>{plan.name}</CardTitle>
                <CardDescription>{plan.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <span className="text-4xl font-bold">{plan.price}</span>
                  <span className="text-muted-foreground">{plan.period}</span>
                </div>

                <ul className="space-y-3">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <Check className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>

                <Button
                  onClick={() => checkout(plan.slug)}
                  disabled={loading || data.account.plan_slug === plan.slug}
                  className="w-full"
                  variant={plan.popular ? "default" : "outline"}
                >
                  {data.account.plan_slug === plan.slug ? "Current Plan" : "Choose " + plan.name}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}

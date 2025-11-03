"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { API_BASE, DEMO_ACC } from "@/lib/api"
import { CreditCard, Check } from "lucide-react"

type BillingState = { plan_slug?: string; billing_status?: string; stripe_customer_id?: string | null }

async function fetchAccount(): Promise<BillingState> {
  const r = await fetch(`${API_BASE}/v1/account`, { headers: { "X-Demo-Account": DEMO_ACC } })
  return r.ok ? r.json() : {}
}

const plans = [
  {
    name: "Starter",
    slug: "starter",
    price: "$29",
    period: "/month",
    description: "Perfect for individual agents",
    features: ["100 reports / month", "6 report types", "PDF export", "Email support"],
  },
  {
    name: "Professional",
    slug: "professional",
    price: "$99",
    period: "/month",
    description: "For growing teams",
    features: ["500 reports / month", "All report types", "API access", "Custom branding", "Priority support"],
    popular: true,
  },
  {
    name: "Enterprise",
    slug: "enterprise",
    price: "$299",
    period: "/month",
    description: "For large organizations",
    features: ["Unlimited reports", "White-label", "Dedicated support", "Custom integrations", "SLA guarantee"],
  },
]

export default function BillingPage() {
  const [acct, setAcct] = useState<BillingState>({})
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchAccount().then(setAcct)
  }, [])

  async function checkout(plan: "starter" | "professional" | "enterprise") {
    setLoading(true)
    const r = await fetch(`${API_BASE}/v1/billing/checkout`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Demo-Account": DEMO_ACC },
      body: JSON.stringify({ plan }),
    })
    const j = await r.json()
    setLoading(false)
    if (j.url) window.location.href = j.url
  }

  async function portal() {
    const r = await fetch(`${API_BASE}/v1/billing/portal`, { headers: { "X-Demo-Account": DEMO_ACC } })
    const j = await r.json()
    if (j.url) window.location.href = j.url
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-bold text-3xl mb-2">Billing</h1>
        <p className="text-muted-foreground">Manage your subscription and billing details</p>
      </div>

      {acct.plan_slug && (
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
                <p className="text-lg font-semibold capitalize">{acct.plan_slug || "—"}</p>
              </div>
              <div className="flex-1">
                <p className="text-sm text-muted-foreground">Status</p>
                <Badge variant={acct.billing_status === "active" ? "default" : "outline"}>
                  {acct.billing_status || "—"}
                </Badge>
              </div>
            </div>
            <Button onClick={portal} variant="outline">
              Open Billing Portal
            </Button>
          </CardContent>
        </Card>
      )}

      <div>
        <h2 className="text-2xl font-semibold mb-4">Plans</h2>
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
                  onClick={() => checkout(plan.slug as any)}
                  disabled={loading}
                  className="w-full"
                  variant={plan.popular ? "default" : "outline"}
                >
                  {acct.plan_slug === plan.slug ? "Current Plan" : "Choose " + plan.name}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}

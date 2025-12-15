"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckCircle2, ExternalLink, CreditCard, Download } from "lucide-react"
import { cn } from "@/lib/utils"

const plans = [
  {
    name: "Starter",
    price: "$99",
    features: ["50 reports/month", "Basic branding", "PDF export", "Email support"],
    current: false,
  },
  {
    name: "Professional",
    price: "$299",
    features: ["200 reports/month", "Full branding control", "All report types", "API access", "Priority support"],
    current: true,
  },
  {
    name: "Enterprise",
    price: "$999",
    features: ["Unlimited reports", "Team management", "Custom templates", "Advanced analytics", "Dedicated support"],
    current: false,
  },
]

const invoices = [
  { id: "inv_001", date: "2024-01-01", amount: "$299.00", status: "Paid" },
  { id: "inv_002", date: "2023-12-01", amount: "$299.00", status: "Paid" },
  { id: "inv_003", date: "2023-11-01", amount: "$299.00", status: "Paid" },
]

export default function BillingPage() {
  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h1 className="font-display font-bold text-3xl mb-2 text-balance">Billing</h1>
        <p className="text-muted-foreground text-pretty">Manage your subscription and billing information</p>
      </div>

      <Card className="border-border/50 bg-card hover:shadow-lg transition-shadow">
        <CardHeader>
          <CardTitle className="font-display">Current Plan</CardTitle>
          <CardDescription>You are currently on the Professional plan</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-2xl font-display font-bold mb-1">Professional</p>
              <p className="text-muted-foreground">$299/month • Renews on February 1, 2024</p>
            </div>
            <Button variant="outline" className="gap-2 bg-transparent">
              <ExternalLink className="w-4 h-4" />
              Open Portal
            </Button>
          </div>
        </CardContent>
      </Card>

      <div>
        <h2 className="font-display font-semibold text-xl mb-4">Available Plans</h2>
        <div className="grid md:grid-cols-3 gap-4">
          {plans.map((plan) => (
            <Card
              key={plan.name}
              className={cn(
                "border-border/50 bg-card hover:shadow-lg transition-all",
                plan.current && "border-primary border-2 shadow-lg shadow-primary/10",
              )}
            >
              <CardHeader>
                <CardTitle className="font-display">{plan.name}</CardTitle>
                <div className="text-3xl font-pricing font-bold text-primary">{plan.price}</div>
                <CardDescription>/month</CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 mb-6">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-sm">
                      <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
                {plan.current ? (
                  <Button variant="outline" className="w-full bg-transparent" disabled>
                    Current Plan
                  </Button>
                ) : (
                  <Button variant="outline" className="w-full bg-transparent">
                    {plan.price === "$999" ? "Contact Sales" : "Upgrade"}
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      <Card className="border-border/50 bg-card hover:shadow-lg transition-shadow">
        <CardHeader>
          <CardTitle className="font-display">Payment Method</CardTitle>
          <CardDescription>Manage your payment information</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between rounded-xl border border-border/50 p-4 bg-muted/30">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded bg-primary/10 flex items-center justify-center">
                <CreditCard className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="font-semibold text-sm">•••• •••• •••• 4242</p>
                <p className="text-xs text-muted-foreground">Expires 12/2025</p>
              </div>
            </div>
            <Button variant="outline" size="sm">
              Update
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="border-border/50 bg-card hover:shadow-lg transition-shadow">
        <CardHeader>
          <CardTitle className="font-display">Billing History</CardTitle>
          <CardDescription>View and download your invoices</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {invoices.map((invoice) => (
              <div
                key={invoice.id}
                className="flex items-center justify-between py-3 border-b border-border last:border-0"
              >
                <div>
                  <p className="font-semibold text-sm">{invoice.date}</p>
                  <p className="text-xs text-muted-foreground">{invoice.id}</p>
                </div>
                <div className="flex items-center gap-4">
                  <span className="font-semibold text-sm">{invoice.amount}</span>
                  <span className="text-xs px-2 py-1 rounded-full bg-primary/10 text-primary">{invoice.status}</span>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <Download className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

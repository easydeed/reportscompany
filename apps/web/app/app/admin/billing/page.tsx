"use client"

import { useEffect, useState, useMemo } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  ArrowLeft,
  DollarSign,
  Building,
  Users,
  TrendingUp,
  ExternalLink,
  Search,
  X,
} from "lucide-react"

interface RevenueStats {
  mrr: number
  total_paid_accounts: number
  total_free_accounts: number
  avg_revenue_per_account: number
  plan_distribution: PlanDistribution[]
  accounts: BillingAccount[]
}

interface PlanDistribution {
  plan_slug: string
  plan_name: string
  count: number
  mrr: number
  price_cents: number
}

interface BillingAccount {
  account_id: string
  name: string
  plan_slug: string
  plan_name: string
  is_active: boolean
  stripe_status: string | null
  created_at: string
  user_count: number
}

const PLAN_PRICES: Record<string, number> = {
  free: 0,
  pro: 29,
  team: 99,
  affiliate: 0,
  sponsored_free: 0,
}

const PLAN_LABELS: Record<string, string> = {
  free: "Free",
  pro: "Pro ($29/mo)",
  team: "Team ($99/mo)",
  affiliate: "Affiliate",
  sponsored_free: "Trial",
}

function formatCurrency(cents: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(cents / 100)
}

function formatCurrencyDollars(dollars: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(dollars)
}

export default function AdminBillingPage() {
  const searchParams = useSearchParams()
  const router = useRouter()

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState<RevenueStats | null>(null)

  const [search, setSearch] = useState(searchParams.get("search") || "")
  const [planFilter, setPlanFilter] = useState(searchParams.get("plan") || "all")

  useEffect(() => {
    async function fetchRevenue() {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch("/api/proxy/v1/admin/stats/revenue", {
          credentials: "include",
        })
        if (!res.ok) throw new Error("Failed to fetch revenue data")
        const data = await res.json()
        setStats(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load")
      } finally {
        setLoading(false)
      }
    }
    fetchRevenue()
  }, [])

  const mrr = stats?.mrr ?? 0
  const totalPaid = stats?.total_paid_accounts ?? 0
  const totalFree = stats?.total_free_accounts ?? 0
  const avgRevenue = stats?.avg_revenue_per_account ?? 0
  const planDist = stats?.plan_distribution ?? []
  const accounts = stats?.accounts ?? []

  const maxPlanCount = useMemo(
    () => Math.max(...planDist.map((p) => p.count), 1),
    [planDist]
  )

  const filteredAccounts = useMemo(() => {
    let list = accounts
    const s = searchParams.get("search")?.toLowerCase()
    const p = searchParams.get("plan")

    if (s) {
      list = list.filter(
        (a) =>
          a.name.toLowerCase().includes(s) ||
          a.plan_slug.toLowerCase().includes(s)
      )
    }
    if (p && p !== "all") {
      list = list.filter((a) => a.plan_slug === p)
    }
    return list
  }, [accounts, searchParams])

  function handleFilter(e: React.FormEvent) {
    e.preventDefault()
    const params = new URLSearchParams()
    if (search) params.set("search", search)
    if (planFilter !== "all") params.set("plan", planFilter)
    router.push(`/app/admin/billing?${params.toString()}`)
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded" />
          <div>
            <Skeleton className="h-9 w-48 mb-2" />
            <Skeleton className="h-5 w-64" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <Skeleton className="h-8 w-24" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardContent className="pt-6">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="py-3 flex gap-4">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-5 w-16 rounded-full" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <DollarSign className="h-12 w-12 mx-auto text-red-500 mb-4" />
        <h3 className="text-lg font-semibold mb-2">Failed to load billing data</h3>
        <p className="text-muted-foreground mb-4">{error}</p>
        <Button variant="outline" onClick={() => window.location.reload()}>
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/app/admin">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-display font-bold text-foreground">
            Billing &amp; Revenue
          </h1>
          <p className="text-muted-foreground mt-1">
            MRR, plan distribution, and account billing health
          </p>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">MRR</CardTitle>
            <DollarSign className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrencyDollars(mrr)}
            </div>
            <p className="text-xs text-muted-foreground">Monthly recurring revenue</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Paid Accounts</CardTitle>
            <Building className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalPaid}</div>
            <p className="text-xs text-muted-foreground">Accounts on paid plans</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Free Accounts</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalFree}</div>
            <p className="text-xs text-muted-foreground">Free &amp; trial accounts</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Revenue / Acct</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrencyDollars(avgRevenue)}
            </div>
            <p className="text-xs text-muted-foreground">Across paid accounts</p>
          </CardContent>
        </Card>
      </div>

      {/* Plan Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Plan Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          {planDist.length === 0 ? (
            <p className="text-muted-foreground text-center py-6">No plan data available</p>
          ) : (
            <div className="space-y-4">
              {planDist.map((plan) => {
                const label =
                  PLAN_LABELS[plan.plan_slug] || plan.plan_name || plan.plan_slug
                const pct = Math.round((plan.count / maxPlanCount) * 100)
                const price = plan.price_cents
                  ? formatCurrency(plan.price_cents)
                  : PLAN_PRICES[plan.plan_slug]
                    ? `$${PLAN_PRICES[plan.plan_slug]}/mo`
                    : "Free"

                return (
                  <div key={plan.plan_slug} className="space-y-1.5">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{label}</span>
                        <span className="text-muted-foreground">·</span>
                        <span className="text-muted-foreground">{price}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-muted-foreground">
                          {plan.count} {plan.count === 1 ? "account" : "accounts"}
                        </span>
                        {plan.mrr > 0 && (
                          <Badge
                            variant="outline"
                            className="text-green-600 border-green-200 bg-green-50"
                          >
                            {formatCurrencyDollars(plan.mrr)}/mo
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-indigo-500 transition-all"
                        style={{ width: `${Math.max(pct, 2)}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Accounts Table */}
      <Card>
        <CardHeader>
          <CardTitle>Accounts by Plan</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Filters */}
          <form onSubmit={handleFilter} className="flex flex-wrap gap-3">
            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search accounts..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={planFilter} onValueChange={setPlanFilter}>
              <SelectTrigger className="w-44">
                <SelectValue placeholder="All Plans" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Plans</SelectItem>
                <SelectItem value="free">Free</SelectItem>
                <SelectItem value="pro">Pro</SelectItem>
                <SelectItem value="team">Team</SelectItem>
                <SelectItem value="affiliate">Affiliate</SelectItem>
                <SelectItem value="sponsored_free">Trial</SelectItem>
              </SelectContent>
            </Select>
            <Button type="submit" variant="secondary">
              Filter
            </Button>
            {(searchParams.get("search") || searchParams.get("plan")) && (
              <Link href="/app/admin/billing">
                <Button variant="ghost" type="button" className="gap-1">
                  <X className="h-3.5 w-3.5" />
                  Clear
                </Button>
              </Link>
            )}
          </form>

          {filteredAccounts.length === 0 ? (
            <div className="text-center py-12">
              <Building className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No accounts found</h3>
              <p className="text-muted-foreground">
                {searchParams.toString()
                  ? "No accounts match your filters"
                  : "No billing data available"}
              </p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Account</TableHead>
                    <TableHead>Plan</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Stripe Status</TableHead>
                    <TableHead>Users</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAccounts.map((acct) => {
                    const planLabel =
                      PLAN_LABELS[acct.plan_slug] ||
                      acct.plan_name ||
                      acct.plan_slug
                    const isPaid =
                      acct.plan_slug === "pro" || acct.plan_slug === "team"

                    return (
                      <TableRow
                        key={acct.account_id}
                        className="cursor-pointer hover:bg-muted/50"
                        onClick={() =>
                          router.push(`/app/admin/accounts/${acct.account_id}`)
                        }
                      >
                        <TableCell className="font-medium">{acct.name}</TableCell>
                        <TableCell>
                          <Badge
                            variant={isPaid ? "default" : "secondary"}
                            className={
                              isPaid
                                ? "bg-indigo-100 text-indigo-700 border-indigo-200"
                                : ""
                            }
                          >
                            {planLabel}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {acct.is_active ? (
                            <Badge
                              variant="outline"
                              className="text-green-600 border-green-200 bg-green-50"
                            >
                              Active
                            </Badge>
                          ) : (
                            <Badge
                              variant="outline"
                              className="text-red-600 border-red-200 bg-red-50"
                            >
                              Churned
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          {acct.stripe_status ? (
                            <StripeStatusBadge status={acct.stripe_status} />
                          ) : (
                            <span className="text-muted-foreground text-sm">-</span>
                          )}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {acct.user_count}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {new Date(acct.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <Link
                            href={`/app/admin/accounts/${acct.account_id}`}
                            onClick={(e) => e.stopPropagation()}
                          >
                            <Button variant="ghost" size="sm">
                              <ExternalLink className="h-3.5 w-3.5" />
                            </Button>
                          </Link>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
              <p className="text-sm text-muted-foreground text-right">
                Showing {filteredAccounts.length} of {accounts.length} accounts
              </p>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function StripeStatusBadge({ status }: { status: string }) {
  const map: Record<string, { className: string; label: string }> = {
    active: {
      className: "text-green-600 border-green-200 bg-green-50",
      label: "Active",
    },
    trialing: {
      className: "text-blue-600 border-blue-200 bg-blue-50",
      label: "Trialing",
    },
    past_due: {
      className: "text-yellow-600 border-yellow-200 bg-yellow-50",
      label: "Past Due",
    },
    canceled: {
      className: "text-red-600 border-red-200 bg-red-50",
      label: "Canceled",
    },
    unpaid: {
      className: "text-red-600 border-red-200 bg-red-50",
      label: "Unpaid",
    },
    incomplete: {
      className: "text-yellow-600 border-yellow-200 bg-yellow-50",
      label: "Incomplete",
    },
  }

  const s = map[status.toLowerCase()] || {
    className: "",
    label: status,
  }

  return (
    <Badge variant="outline" className={s.className}>
      {s.label}
    </Badge>
  )
}

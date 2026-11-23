"use client"

// LR-027 slice 4: operator alerts. Platform admins request a test alert (the
// closure evidence path of design section 7), see open incidents, and record
// whether alerts whose delivery is uncertain actually arrived.

import { useEffect, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Loader2, RefreshCw, Send } from "lucide-react"

interface OpenAlert {
  id: string
  key: string
  opened_at: string
  member_count: number
  members_truncated: boolean
}

interface Notification {
  id: number
  key: string
  event: string
  channel: "email" | "sms"
  state: "pending" | "claimed" | "accepted" | "not_sent" | "unknown"
  attempts: number
  created_at: string
  outcome_at: string | null
  provider_message_id: string | null
  last_error_class: string | null
  resolution: "received" | "not_received" | null
}

interface AlertsResponse {
  open_alerts: OpenAlert[]
  needs_reconciliation: Notification[]
  recent: Notification[]
}

const STATE_STYLE: Record<Notification["state"], string> = {
  accepted: "bg-emerald-50 text-emerald-700 border-emerald-200",
  unknown: "bg-amber-50 text-amber-800 border-amber-200",
  not_sent: "bg-red-50 text-red-700 border-red-200",
  claimed: "bg-blue-50 text-blue-700 border-blue-200",
  pending: "bg-slate-50 text-slate-600 border-slate-200",
}

function when(iso: string | null) {
  return iso ? new Date(iso).toLocaleString() : "—"
}

export default function OperatorAlertsPage() {
  const [data, setData] = useState<AlertsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)

  useEffect(() => {
    load()
  }, [])

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch("/api/proxy/v1/admin/ops/alerts", {
        credentials: "include",
        cache: "no-store",
      })
      const body = await res.json()
      if (!res.ok) throw new Error(body.detail || body.error || `HTTP ${res.status}`)
      setData(body)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load alerts")
    } finally {
      setLoading(false)
    }
  }

  async function requestTest() {
    setBusy("test")
    setNotice(null)
    setError(null)
    try {
      const res = await fetch("/api/proxy/v1/admin/ops/test-alert", {
        method: "POST",
        credentials: "include",
      })
      const body = await res.json()
      if (!res.ok) throw new Error(body.detail || body.error || `HTTP ${res.status}`)
      setNotice(body.detail)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not request a test alert")
    } finally {
      setBusy(null)
    }
  }

  async function resolve(n: Notification, resolution: "received" | "not_received") {
    const label = resolution === "received" ? "received" : "NOT received"
    const evidence = window.prompt(
      `Record that this ${n.channel} alert was ${label}. Evidence (for example the time you checked, ` +
        `or the message ID you saw), never the address or number:`,
    )
    if (!evidence || !evidence.trim()) return
    setBusy(`n${n.id}`)
    setError(null)
    try {
      const res = await fetch(`/api/proxy/v1/admin/ops/notifications/${n.id}/resolution`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resolution, evidence }),
      })
      const body = await res.json()
      if (!res.ok) throw new Error(body.detail || body.error || `HTTP ${res.status}`)
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not record the resolution")
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Operator Alerts</h1>
          <p className="text-slate-500 mt-1">
            Incidents the monitor has open, and alerts whose delivery needs confirming
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={load} className="border-slate-300 text-slate-600 hover:bg-slate-50">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button onClick={requestTest} disabled={busy === "test"}>
            {busy === "test" ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Send className="h-4 w-4 mr-2" />}
            Send test alert
          </Button>
        </div>
      </div>

      <p className="text-sm text-slate-500 max-w-3xl">
        A test alert opens a labelled incident on the monitor&rsquo;s next run (within 5 minutes) and resolves it on the
        run after, through the same code as a real alert. It is delivered only when sending is switched on and a
        destination is set for the channel. If an earlier test is still open, a new one waits for it to resolve, then
        runs its own open and resolve.
      </p>

      {notice && (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {notice}
        </div>
      )}
      {error && (
        <div role="alert" className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && !data ? (
        <div className="flex items-center gap-2 text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading
        </div>
      ) : data ? (
        <>
          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-slate-900">Open incidents ({data.open_alerts.length})</h2>
            <Card className="bg-white border-slate-200 shadow-sm">
              <CardContent className="p-0 overflow-x-auto">
                {data.open_alerts.length === 0 ? (
                  <p className="p-6 text-sm text-slate-500">No open incidents.</p>
                ) : (
                  <>
                    <ul className="divide-y divide-slate-100 md:hidden">
                      {data.open_alerts.map((a) => (
                        <li key={a.id} className="p-4">
                          <div className="font-mono text-sm">{a.key}</div>
                          <div className="text-xs text-slate-500">
                            {a.member_count}
                            {a.members_truncated ? "+" : ""} outstanding · opened {when(a.opened_at)}
                          </div>
                        </li>
                      ))}
                    </ul>
                    <div className="hidden md:block">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Signal</TableHead>
                            <TableHead>Outstanding</TableHead>
                            <TableHead>Opened</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {data.open_alerts.map((a) => (
                            <TableRow key={a.id}>
                              <TableCell className="font-mono text-sm">{a.key}</TableCell>
                              <TableCell>
                                {a.member_count}
                                {a.members_truncated ? "+" : ""}
                              </TableCell>
                              <TableCell className="text-sm text-slate-500">{when(a.opened_at)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-slate-900">
              Delivery uncertain ({data.needs_reconciliation.length})
            </h2>
            <p className="text-sm text-slate-500 max-w-3xl">
              The provider may have received these, so they are never resent automatically. Check the inbox or phone and
              record what you found.
            </p>
            <Card className="bg-white border-slate-200 shadow-sm">
              <CardContent className="p-0 overflow-x-auto">
                {data.needs_reconciliation.length === 0 ? (
                  <p className="p-6 text-sm text-slate-500">Nothing to reconcile.</p>
                ) : (
                  <NotificationTable rows={data.needs_reconciliation} busy={busy} onResolve={resolve} />
                )}
              </CardContent>
            </Card>
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-slate-900">Recent notifications</h2>
            <Card className="bg-white border-slate-200 shadow-sm">
              <CardContent className="p-0 overflow-x-auto">
                {data.recent.length === 0 ? (
                  <p className="p-6 text-sm text-slate-500">
                    No alert has been queued. With sending switched off, the monitor records incidents and sends
                    nothing.
                  </p>
                ) : (
                  <NotificationTable rows={data.recent} busy={busy} onResolve={resolve} />
                )}
              </CardContent>
            </Card>
          </section>
        </>
      ) : null}
    </div>
  )
}

type ResolveFn = (n: Notification, r: "received" | "not_received") => void

function ReceiptButtons({ n, busy, onResolve }: { n: Notification; busy: string | null; onResolve: ResolveFn }) {
  return (
    <div className="flex flex-wrap gap-2">
      <Button size="sm" variant="outline" disabled={busy === `n${n.id}`} onClick={() => onResolve(n, "received")}>
        Received
      </Button>
      <Button size="sm" variant="outline" disabled={busy === `n${n.id}`} onClick={() => onResolve(n, "not_received")}>
        Not received
      </Button>
    </div>
  )
}

function Receipt({ n, busy, onResolve }: { n: Notification; busy: string | null; onResolve: ResolveFn }) {
  if (n.resolution) {
    return <span className="text-sm">{n.resolution === "received" ? "Received" : "Not received"}</span>
  }
  if (n.state === "unknown" || n.state === "accepted") {
    return <ReceiptButtons n={n} busy={busy} onResolve={onResolve} />
  }
  return <span className="text-sm text-slate-400">—</span>
}

function StateBadge({ n, showError = true }: { n: Notification; showError?: boolean }) {
  return (
    <>
      <Badge variant="outline" className={STATE_STYLE[n.state]}>
        {n.state.replace("_", " ")}
      </Badge>
      {showError && n.last_error_class && <div className="mt-1 text-xs text-slate-500">{n.last_error_class}</div>}
    </>
  )
}

function NotificationTable({
  rows,
  busy,
  onResolve,
}: {
  rows: Notification[]
  busy: string | null
  onResolve: ResolveFn
}) {
  return (
    <>
      {/* Phones: one card per alert, so the state and receipt buttons are never off-screen. */}
      <ul className="divide-y divide-slate-100 md:hidden">
        {rows.map((n) => (
          <li key={n.id} className="space-y-2 p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="truncate font-mono text-sm">{n.key}</div>
                <div className="text-xs text-slate-500">
                  <span className="font-mono">{n.event}</span> · {n.channel === "sms" ? "SMS" : "Email"} · {n.attempts}{" "}
                  attempt
                  {n.attempts === 1 ? "" : "s"}
                </div>
              </div>
              <div className="shrink-0 text-right">
                <StateBadge n={n} showError={false} />
              </div>
            </div>
            <div className="text-xs text-slate-500">
              Outcome at {when(n.outcome_at)}
              {n.last_error_class ? ` · ${n.last_error_class}` : ""}
            </div>
            <Receipt n={n} busy={busy} onResolve={onResolve} />
          </li>
        ))}
      </ul>
      <div className="hidden md:block">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Signal</TableHead>
              <TableHead>Event</TableHead>
              <TableHead>Channel</TableHead>
              <TableHead>State</TableHead>
              <TableHead>Attempts</TableHead>
              <TableHead>Outcome at</TableHead>
              <TableHead>Receipt</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((n) => (
              <TableRow key={n.id}>
                <TableCell className="font-mono text-sm">{n.key}</TableCell>
                <TableCell className="font-mono text-xs">{n.event}</TableCell>
                <TableCell>{n.channel === "sms" ? "SMS" : "Email"}</TableCell>
                <TableCell>
                  <StateBadge n={n} />
                </TableCell>
                <TableCell>{n.attempts}</TableCell>
                <TableCell className="text-sm text-slate-500">{when(n.outcome_at)}</TableCell>
                <TableCell className="min-w-[220px]">
                  <Receipt n={n} busy={busy} onResolve={onResolve} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </>
  )
}

"use client"

// /app/affiliate/agents/[agentId] — one person. Activity, not content: the
// rep sees that a report went out, never the report. No tabs, no PDF links,
// no usage bars — usage is three plain numbers.

import { useEffect, useState } from "react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { useQueryClient } from "@tanstack/react-query"
import { ArrowLeft, Send, Calendar, BadgeCheck } from "lucide-react"
import { RuleList } from "@/components/ui/list"
import { useAffiliateOverview, queryKeys } from "@/hooks/use-api"
import { useToast } from "@/components/ui/use-toast"
import {
  Avatar, Sentence, StatCell, ActivityRow, RowButton, ConsequenceMenu, H2, post,
  reportTypeLabel, whenLabel, sinceLabel, QUIET_DAYS, type Tone, type MenuItem,
} from "@/components/sponsor/shared"

type Usage = { agent?: { id: string; name: string; email: string; phone?: string | null; status: "active" | "pending" | "deactivated"; plan_slug: string }; limits?: { market_reports: { used: number; limit: number } }; plan?: { market_reports_limit: number }; usage?: { market_reports_used: number } }
type Report = { id: string; report_type: string; status: string; generated_at: string | null; city: string; is_scheduled: boolean }
type Schedule = { id: string; name: string; report_type: string; area: string; cadence: string; active: boolean; next_run_at: string | null; recipient_count: number }

export default function PersonPage() {
  const { agentId } = useParams<{ agentId: string }>()
  const router = useRouter()
  const qc = useQueryClient()
  const { toast } = useToast()
  const { data: aff } = useAffiliateOverview()
  const [usage, setUsage] = useState<Usage | null>(null)
  const [reports, setReports] = useState<Report[] | null>(null)
  const [schedules, setSchedules] = useState<Schedule[] | null>(null)
  const [denied, setDenied] = useState(false)

  useEffect(() => {
    const get = (p: string) => fetch(`/api/proxy/v1/affiliate/agents/${agentId}/${p}`, { credentials: "include" })
    get("usage").then(async (r) => { if (r.status === 403) setDenied(true); else setUsage(await r.json()) })
    get("reports").then(async (r) => r.ok && setReports((await r.json()).reports ?? []))
    get("schedules").then(async (r) => r.ok && setSchedules((await r.json()).schedules ?? []))
  }, [agentId])

  // The overview row carries status + email; /usage carries limits. Use both.
  const row = (aff?.sponsored_accounts ?? []).find((s: any) => s.account_id === agentId)
  const name: string = row?.name ?? usage?.agent?.name ?? ""
  const first = name.split(" ")[0]
  const email: string = row?.email ?? usage?.agent?.email ?? ""
  const status: "active" | "pending" | "deactivated" = row?.status ?? usage?.agent?.status ?? "active"
  const companyName: string = aff?.account?.parent_company_name || ""

  const used = usage?.limits?.market_reports?.used ?? usage?.usage?.market_reports_used ?? row?.reports_this_month ?? 0
  const limit = usage?.limits?.market_reports?.limit ?? usage?.plan?.market_reports_limit ?? 10
  const lastAt: string | null = row?.last_report_at ?? reports?.[0]?.generated_at ?? null
  const quietDays = lastAt ? (Date.now() - new Date(lastAt).getTime()) / 86_400_000 : Infinity

  let tone: Tone = "good", sentence = `Has a seat · ${used} report${used === 1 ? "" : "s"} this month`
  if (status === "pending") { tone = "off"; sentence = "Offered a seat, hasn't taken it yet" }
  else if (status === "deactivated") { tone = "off"; sentence = "Seat paused" }
  else if (used >= limit) { sentence = `Has a seat · used all ${limit} this month` }
  else if (quietDays > QUIET_DAYS) { tone = "warn"; sentence = lastAt ? `Has a seat · nothing sent in ${sinceLabel(lastAt)}` : "Has a seat · nothing sent yet" }

  async function act(label: string, fn: () => Promise<unknown>, back = false) {
    try { await fn(); toast({ title: label }); qc.invalidateQueries({ queryKey: queryKeys.affiliate.overview }); if (back) router.push("/app/affiliate") }
    catch (e) { toast({ title: "That didn't go through", description: e instanceof Error ? e.message : undefined, variant: "destructive" }) }
  }
  const menu: MenuItem[] =
    status === "pending" ? [{ label: "Cancel the offer", note: "The invite link stops working. They stay in your book and keep getting your reports.", danger: true, onSelect: () => act("Offer withdrawn", () => post(`/v1/affiliate/accounts/${agentId}/deactivate`), true) }]
    : status === "deactivated" ? [{ label: "Take the seat back", note: "They keep their account and reports, on the Free plan (3 a month), on their own. You can't undo this from here.", danger: true, onSelect: () => act("Seat removed", () => post(`/v1/affiliate/accounts/${agentId}/unsponsor`), true) }]
    : [{ label: "Pause their seat", note: "They're locked out of their account until you turn it back on. Nothing is deleted.", danger: true, onSelect: () => act("Seat paused", () => post(`/v1/affiliate/accounts/${agentId}/deactivate`)) }]

  if (denied) {
    return <div className="flex flex-col gap-4"><p className="text-[16px] text-muted-foreground">This agent isn't in your book.</p><Link href="/app/affiliate" className="text-[14px] font-semibold text-[var(--link)]">← My agents</Link></div>
  }

  // Reports become sentences. Scheduled sends read differently from one-offs.
  const activity = (reports ?? []).filter((r) => r.status === "completed" || r.status === "complete" || r.status === "processing").map((r) => ({
    id: r.id, when: whenLabel(r.generated_at),
    icon: r.is_scheduled ? <Calendar /> : <Send />,
    text: `${r.is_scheduled ? "Their schedule sent" : "Sent"} ${r.city === "Unknown" ? "a" : `${r.city}`} ${reportTypeLabel(r.report_type)}`,
  }))

  return (
    <div className="flex flex-col gap-9">
      <div className="flex flex-col gap-[18px]">
        <Link href="/app/affiliate" className="inline-flex items-center gap-1.5 self-start text-[14px] font-semibold text-[var(--link)] hover:text-[var(--link-hover)]"><ArrowLeft className="size-[15px]" />My agents</Link>
        <div className="flex flex-wrap items-end justify-between gap-6">
          <div className="flex items-center gap-[18px]">
            <Avatar name={name || "?"} size={56} />
            <div className="flex flex-col gap-1.5">
              <h1 className="text-[34px] font-extrabold leading-[1.1] tracking-[-0.03em] text-foreground">{name}</h1>
              <p className="text-[16px] text-muted-foreground">{email}</p>
            </div>
          </div>
          <div className="flex gap-2">
            {email && <RowButton href={`mailto:${email}`}>Email {first}</RowButton>}
            {status === "deactivated" && <RowButton onClick={() => act("Seat back on", () => post(`/v1/affiliate/accounts/${agentId}/reactivate`))}>Turn back on</RowButton>}
            {status === "pending" && email && <RowButton onClick={() => act("Invite resent", () => post("/v1/affiliate/resend-invite", { email }))}>Resend invite</RowButton>}
            <ConsequenceMenu items={menu} size={42} />
          </div>
        </div>
      </div>

      <div className="rounded-xl bg-[var(--surface-cream)] px-5 py-[18px]"><Sentence tone={tone} size={17}>{sentence}</Sentence></div>

      {status !== "pending" && (
        <div className="grid grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-4">
          <StatCell label="Sent this month" value={String(used)} sub={`of ${limit} on the seat`} subTone={used >= limit ? "warn" : "muted"} />
          <StatCell label="Last sent" value={lastAt ? whenLabel(lastAt) : "—"} sub={lastAt ? undefined : "Nothing yet"} />
          <StatCell label="Seat" value={companyName ? "Paid" : "Trial"} sub={companyName ? `by ${companyName}` : `${limit} reports a month`} />
        </div>
      )}

      <div className="flex flex-col gap-[14px]">
        <H2>What {first} has been doing</H2>
        <RuleList>
          {status !== "pending" && row?.created_at && activity.length === 0 && reports && (
            <ActivityRow icon={<BadgeCheck />} tone="link" text="Took the seat" when={whenLabel(row.created_at)} />
          )}
          {activity.map((a) => <ActivityRow key={a.id} icon={a.icon} text={a.text} when={a.when} />)}
          {status !== "pending" && row?.created_at && activity.length > 0 && (
            <ActivityRow icon={<BadgeCheck />} tone="link" text="Took the seat" when={whenLabel(row.created_at)} />
          )}
          {reports && reports.length === 0 && status !== "pending" && <p className="border-b border-[var(--border-subtle)] py-[14px] text-[14px] text-muted-foreground">Nothing sent yet.</p>}
        </RuleList>
        <p className="text-[14px] text-muted-foreground">You see that reports went out. The reports themselves belong to {first}.</p>
      </div>

      {schedules && schedules.length > 0 && (
        <div className="flex flex-col gap-[14px]">
          <H2>Going out on its own</H2>
          <RuleList>
            {schedules.map((s) => (
              <div key={s.id} className="grid grid-cols-[minmax(0,1.4fr)_130px] items-center gap-[18px] border-b border-[var(--border-subtle)] py-[14px]">
                <span className="flex min-w-0 flex-col leading-[1.3]">
                  <span className="text-[15px] text-foreground">{s.area} · {reportTypeLabel(s.report_type)}</span>
                  <span className="text-[13px] text-muted-foreground">{s.cadence} · to {s.recipient_count} {s.recipient_count === 1 ? "person" : "people"}</span>
                </span>
                <span className={`whitespace-nowrap text-right text-[14px] ${s.active ? "text-[var(--body)]" : "text-[var(--warning-foreground)]"}`}>{s.active ? `Next ${whenLabel(s.next_run_at) || "—"}` : "Paused"}</span>
              </div>
            ))}
          </RuleList>
        </div>
      )}
    </div>
  )
}

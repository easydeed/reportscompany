"use client"

// /app/affiliate — "My agents". One book: everyone the rep sends to
// (contacts) plus the agents who hold a seat (sponsored accounts). Replaces
// AffiliateDashboardShell. No metric tiles, no "Your reports" card, no
// onboarding card above the list — the sentence under the title carries
// the numbers, and the rows carry the status.

import { useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { useQueryClient } from "@tanstack/react-query"
import { PageHeader } from "@/components/page-header"
import { FilterPills, RuleList, ListRow, ListEmpty } from "@/components/ui/list"
import { useAffiliateOverview, useContacts, queryKeys } from "@/hooks/use-api"
import { useToast } from "@/components/ui/use-toast"
import {
  Avatar, Sentence, SeatBadge, RowButton, ConsequenceMenu, EmailInvite, post,
  sinceLabel, whenLabel, QUIET_DAYS, type Tone, type MenuItem,
} from "@/components/sponsor/shared"

type Sponsored = {
  account_id: string; name: string; email?: string; plan_slug: string
  reports_this_month: number; last_report_at: string | null; created_at: string
  status?: "pending" | "active" | "deactivated"; last_invite_sent?: string | null
}
type Contact = { id: string; first_name?: string; last_name?: string; name?: string; email: string; company?: string | null }

type Row = {
  key: string; name: string; sub: string; email: string
  seat: boolean; kind: "pending" | "active" | "limit" | "quiet" | "paused" | "contact"
  tone: Tone; sentence: string; href?: string
  primary?: { label: string; run: () => void }
  menu: MenuItem[]
}

const COLS = "minmax(0,1.1fr) minmax(0,1.4fr) 190px"
type Filter = "all" | "seat" | "noseat" | "quiet" | "waiting"

export default function MyAgentsPage() {
  const router = useRouter()
  const qc = useQueryClient()
  const { toast } = useToast()
  const { data: aff, isLoading } = useAffiliateOverview()
  const { data: contactsData } = useContacts()
  const [filter, setFilter] = useState<Filter>("all")
  const [busy, setBusy] = useState(false)
  const [justAdded, setJustAdded] = useState<string | null>(null)

  const companyName: string = aff?.account?.parent_company_name || ""
  const seatLimit = 10 // sponsored_free market_reports_limit — read from plans if it moves

  async function act(label: string, fn: () => Promise<unknown>) {
    setBusy(true)
    try { await fn(); toast({ title: label }); qc.invalidateQueries({ queryKey: queryKeys.affiliate.overview }); qc.invalidateQueries({ queryKey: queryKeys.contacts.all }) }
    catch (e) { toast({ title: "That didn't go through", description: e instanceof Error ? e.message : undefined, variant: "destructive" }) }
    finally { setBusy(false) }
  }

  // Invite = give a seat. The API needs `name`; until /v1/affiliate/invite-agent
  // accepts email alone (AFFILIATE_INVENTORY §6b), derive a display name from the address.
  function giveSeat(email: string, name?: string) {
    const guessed = name || email.split("@")[0].replace(/[._-]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
    return act(`Seat offered to ${email}`, () => post("/v1/affiliate/invite-agent", { name: guessed, email }))
  }

  const rows = useMemo<Row[]>(() => {
    const sponsored: Sponsored[] = aff?.sponsored_accounts ?? []
    const sponsoredEmails = new Set(sponsored.map((s) => (s.email || "").toLowerCase()))
    const seatRows: Row[] = sponsored.map((s) => {
      const status = s.status ?? "pending"
      const since = sinceLabel(s.last_report_at)
      const quietDays = s.last_report_at ? (Date.now() - new Date(s.last_report_at).getTime()) / 86_400_000 : Infinity
      const base = { key: s.account_id, name: s.name, sub: s.email ?? "", email: s.email ?? "", href: `/app/affiliate/agents/${s.account_id}` }
      const deactivate = () => act(status === "pending" ? "Offer withdrawn" : "Seat paused", () => post(`/v1/affiliate/accounts/${s.account_id}/deactivate`))
      const reactivate = () => act("Seat back on", () => post(`/v1/affiliate/accounts/${s.account_id}/reactivate`))
      const unsponsor = () => act("Seat removed", () => post(`/v1/affiliate/accounts/${s.account_id}/unsponsor`))
      const resend = () => act("Invite resent", () => post("/v1/affiliate/resend-invite", { email: s.email }))

      if (status === "pending") {
        const stale = s.last_invite_sent && (Date.now() - new Date(s.last_invite_sent).getTime()) > 7 * 86_400_000
        return { ...base, seat: false, kind: "pending", tone: stale ? "warn" : "off", href: undefined,
          sentence: stale ? `Offered a seat ${whenLabel(s.last_invite_sent).toLowerCase()}, hasn't taken it` : `Offered a seat ${whenLabel(s.last_invite_sent ?? s.created_at).toLowerCase()}`,
          primary: { label: "Resend invite", run: resend },
          // Code truth: this calls /deactivate on the pending account (is_active = FALSE). The invite link stops working.
          menu: [{ label: "Cancel the offer", note: "The invite link stops working. They stay in your book and keep getting your reports.", danger: true, onSelect: deactivate }] }
      }
      if (status === "deactivated") {
        return { ...base, seat: true, kind: "paused", tone: "off", sentence: `Seat paused${since ? ` · last sent ${since} ago` : ""}`,
          primary: { label: "Turn back on", run: reactivate },
          // Code truth: sponsor_account_id = NULL, sponsored_free → free. Irreversible from the rep's side.
          menu: [{ label: "Take the seat back", note: "They keep their account and reports, on the Free plan (3 a month), on their own. You can't undo this from here.", danger: true, onSelect: unsponsor }] }
      }
      const pause: MenuItem = { label: "Pause their seat", note: "They're locked out of their account until you turn it back on. Nothing is deleted.", danger: true, onSelect: deactivate }
      if (s.reports_this_month >= seatLimit) return { ...base, seat: true, kind: "limit", tone: "good", sentence: `Has a seat · used all ${seatLimit} this month`, menu: [pause] }
      if (quietDays > QUIET_DAYS) return { ...base, seat: true, kind: "quiet", tone: "warn", sentence: since ? `Has a seat · nothing sent in ${since}` : "Has a seat · nothing sent yet",
        primary: { label: "Check in", run: () => { if (s.email) window.location.href = `mailto:${s.email}` } }, menu: [pause] }
      const paid = s.plan_slug && s.plan_slug !== "sponsored_free" ? ` · pays for ${s.plan_slug.replace(/_/g, " ")}` : ""
      return { ...base, seat: true, kind: "active", tone: "good", sentence: `Has a seat · ${s.reports_this_month} report${s.reports_this_month === 1 ? "" : "s"} this month${paid}`, menu: [pause] }
    })

    const contacts: Contact[] = contactsData?.contacts ?? contactsData ?? []
    const contactRows: Row[] = (Array.isArray(contacts) ? contacts : [])
      .filter((c) => c.email && !sponsoredEmails.has(c.email.toLowerCase()))
      .map((c) => {
        const name = c.name || [c.first_name, c.last_name].filter(Boolean).join(" ") || c.email
        return { key: `c-${c.id}`, name, sub: c.company || c.email, email: c.email, seat: false, kind: "contact", tone: "off",
          // Contacts carry no send/open history in /v1/contacts — see README "What the API doesn't return".
          sentence: "In your book · gets what you send",
          primary: { label: "Give a seat", run: () => giveSeat(c.email, name) }, menu: [] }
      })
    return [...seatRows, ...contactRows]
  }, [aff, contactsData]) // eslint-disable-line react-hooks/exhaustive-deps

  const seated = rows.filter((r) => r.seat)
  const quiet = rows.filter((r) => r.kind === "quiet")
  const waiting = rows.filter((r) => r.kind === "pending")
  const sending = rows.filter((r) => r.kind === "active" || r.kind === "limit").length
  const shown = filter === "seat" ? seated : filter === "noseat" ? rows.filter((r) => !r.seat) : filter === "quiet" ? quiet : filter === "waiting" ? waiting : rows

  const description = isLoading ? undefined : rows.length === 0
    ? "Nobody yet. Add the first agent below."
    : `${rows.length} ${rows.length === 1 ? "person" : "people"} in your book. ${seated.length} ${seated.length === 1 ? "has" : "have"} a seat; ${sending} sent something this month.`

  return (
    <div className="flex flex-col gap-8">
      <PageHeader title="My agents" description={description} />

      <div className="flex flex-col gap-[10px]">
        <EmailInvite placeholder="Give someone a seat — type their email" button="Invite" busy={busy} onSubmit={(e) => { setJustAdded(e); giveSeat(e) }} />
        {justAdded
          ? <p className="text-[14px] font-medium text-[var(--success-foreground)]">{justAdded} has been offered a seat — their own account, {seatLimit} reports a month{companyName ? `, paid by ${companyName}` : ""}.</p>
          : <p className="text-[14px] text-muted-foreground">A seat is the agent's own account with {seatLimit} reports a month{companyName ? `, paid by ${companyName}` : ""}. <a href="/app/affiliate/bulk-invite" className="font-semibold text-[var(--link)] hover:text-[var(--link-hover)]">Whole office? Paste a list.</a></p>}
      </div>

      <div className="flex flex-col gap-[14px]">
        <FilterPills<Filter>
          value={filter} onChange={setFilter}
          options={[
            { value: "all", label: `Everyone ${rows.length}` },
            { value: "seat", label: `Trial agents ${seated.length}` },
            { value: "noseat", label: `No seat yet ${rows.length - seated.length}` },
            { value: "quiet", label: `Gone quiet ${quiet.length}` },
            { value: "waiting", label: `Waiting ${waiting.length}` },
          ]}
        />
        <RuleList>
          {shown.map((r) => (
            <ListRow key={r.key} columns={COLS} className="py-[14px]">
              <button type="button" onClick={() => r.href && router.push(r.href)} disabled={!r.href} className="flex min-w-0 items-center gap-3 text-left disabled:cursor-default">
                <Avatar name={r.name} />
                <span className="flex min-w-0 flex-col leading-[1.3]">
                  <span className="flex items-center gap-1.5"><span className="truncate text-[16px] font-semibold text-foreground">{r.name}</span>{r.seat && <SeatBadge />}</span>
                  <span className="truncate text-[13px] text-muted-foreground">{r.sub}</span>
                </span>
              </button>
              <Sentence tone={r.tone}>{r.sentence}</Sentence>
              <span className="flex items-center justify-end gap-1.5">
                {r.primary && <RowButton onClick={r.primary.run}>{r.primary.label}</RowButton>}
                <ConsequenceMenu items={r.menu} />
              </span>
            </ListRow>
          ))}
          {!isLoading && shown.length === 0 && <ListEmpty>Nobody here right now.</ListEmpty>}
        </RuleList>
      </div>
    </div>
  )
}

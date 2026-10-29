"use client"

// /app/company/reps — People. Design's "Reps & agents" (Sponsor v4): one
// surface, two levels; a rep row opens to its agents. Invite is inline.
//
// Adopted with these changes, each to what the API does:
//   * the seat line under the header reads GET /v1/company/seats (#224);
//   * invite asks for a name as well as the email — the invite email greets
//     the person by it, and Design's version guessed one from the address;
//   * agents join their rep by `rep_id` (D-276), not by name;
//   * the row menu is the seat API: "Cancel the invite" (POST
//     /reps/{id}/cancel-invite) for a rep who has not joined and has no
//     agents, "Replace this rep" (POST /reps/{id}/reassign) for any rep holding
//     a seat. Each item states what the server does. The old table's
//     Deactivate / Remove had no handler and no endpoint (D-302): gone.

import { useMemo, useState } from "react"
import Link from "next/link"
import { useQueryClient } from "@tanstack/react-query"
import { ChevronDown, ChevronRight } from "lucide-react"
import { PageHeader } from "@/components/page-header"
import { RuleList, ListEmpty } from "@/components/ui/list"
import { useCompanyReps, useCompanyAgents, useCompanyBranding, useCompanySeats, queryKeys } from "@/hooks/use-api"
import { useToast } from "@/components/ui/use-toast"
import { Avatar, Sentence, RowButton, ConsequenceMenu, post, type MenuItem } from "@/components/sponsor/shared"
import {
  AGENT_STATUS, agentSentence, agentsByRep, repActions, repSentence, seatLine, splitName,
  type Agent, type Rep, type SeatSummary,
} from "@/lib/company-people"

const SHOW = 6

const field = "h-[46px] rounded-[10px] border-[1.5px] border-[var(--border-strong)] bg-white px-4 text-[15px] text-foreground outline-none placeholder:text-[var(--placeholder)] focus:border-[var(--link)] focus:ring-[3px] focus:ring-[var(--link)]/20"
const inkButton = "h-[46px] rounded-[10px] bg-primary px-[20px] text-[15px] font-semibold text-primary-foreground transition-colors hover:bg-[var(--primary-hover)] disabled:opacity-60"

function errorText(e: unknown) {
  return e instanceof Error ? e.message : "That didn't go through."
}

export default function PeoplePage() {
  const qc = useQueryClient()
  const { toast } = useToast()
  const { data: repsData, isLoading, error } = useCompanyReps()
  const { data: agentsData } = useCompanyAgents()
  const { data: seatsData } = useCompanySeats()
  const { data: brandingData } = useCompanyBranding()
  const primary: string = brandingData?.branding?.primary_color || "var(--agent-primary)"
  const [open, setOpen] = useState<Record<string, boolean>>({})
  const [replacing, setReplacing] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)

  const reps: Rep[] = repsData?.reps ?? []
  const seats: SeatSummary | null = seatsData?.seats ?? null
  const byRep = useMemo(() => agentsByRep((agentsData?.agents ?? []) as Agent[]), [agentsData])
  const totalAgents = reps.reduce((n, r) => n + r.agent_count, 0)

  function refresh() {
    qc.invalidateQueries({ queryKey: ["company"] })
  }

  async function run(label: string, fn: () => Promise<unknown>, done: string) {
    setBusy(true)
    try {
      await fn()
      setNotice(done)
      refresh()
      return true
    } catch (e) {
      toast({ title: `${label} didn't go through`, description: errorText(e), variant: "destructive" })
      return false
    } finally {
      setBusy(false)
    }
  }

  async function invite(form: HTMLFormElement) {
    const data = new FormData(form)
    const names = splitName(String(data.get("name") || ""))
    const email = String(data.get("email") || "").trim()
    if (!names || !email) return
    const ok = await run("The invite", () => post("/v1/company/invite-rep", { ...names, email }),
      `Invite sent to ${names.name} at ${email}.`)
    if (ok) form.reset()
  }

  function menuFor(r: Rep): MenuItem[] {
    const first = r.name.split(" ")[0] || r.name
    const items: MenuItem[] = []
    for (const action of repActions(r)) {
      if (action === "cancel") {
        items.push({
          label: "Cancel the invite",
          note: "The invite link stops working and the seat is free for someone else.",
          danger: true,
          onSelect: () => void run("Cancelling", () => post(`/v1/company/reps/${r.id}/cancel-invite`),
            `${r.name}'s invite is cancelled and the seat is free.`),
        })
      }
      if (action === "replace") {
        items.push({
          label: "Replace this rep",
          note: `Invite someone into ${first}'s seat. ${first}'s agents and scheduled sends move over, ${first} can no longer sign in, and each agent is told who their rep is now.`,
          danger: true,
          onSelect: () => setReplacing(r.id),
        })
      }
    }
    return items
  }

  if (error) {
    return <p className="text-[16px] text-muted-foreground">{String(error).includes("403") ? "This account isn't a title-company admin." : "Couldn't load your people right now."}</p>
  }

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="People"
        description={isLoading ? undefined : `${reps.length} rep${reps.length === 1 ? "" : "s"} · ${totalAgents} agent${totalAgents === 1 ? "" : "s"}. Open a rep to see their agents.`}
      />

      <div className="flex flex-col gap-[10px]">
        <form className="flex flex-wrap items-center gap-[10px]" onSubmit={(e) => { e.preventDefault(); void invite(e.currentTarget) }}>
          <input name="name" required placeholder="Their name" autoComplete="off" disabled={busy} className={`${field} min-w-[200px] flex-1`} />
          <input name="email" type="email" required placeholder="Their email" autoComplete="off" disabled={busy} className={`${field} min-w-[240px] flex-[1.4]`} />
          <button type="submit" disabled={busy} className={inkButton}>Invite a rep</button>
        </form>
        {notice
          ? <p className="text-[14px] font-medium text-[var(--success-foreground)]">{notice}</p>
          : <p className="text-[14px] text-muted-foreground">They get your logo and colour on day one and start inviting their own agents.{seatLine(seats) ? ` ${seatLine(seats)}.` : ""}</p>}
      </div>

      <RuleList>
        {reps.map((r) => {
          const s = repSentence(r)
          const agents = byRep[r.id] ?? []
          const isOpen = !!open[r.id]
          const Chev = isOpen ? ChevronDown : ChevronRight
          const actions = repActions(r)
          return (
            <div key={r.id} className="flex flex-col border-b border-[var(--border-subtle)]">
              <div className="grid grid-cols-[minmax(0,1.1fr)_minmax(0,1.5fr)_auto] items-center gap-5 py-[14px]">
                <button type="button" onClick={() => setOpen((o) => ({ ...o, [r.id]: !isOpen }))} className="flex min-w-0 items-center gap-3 text-left" aria-expanded={isOpen}>
                  <Chev className="size-4 shrink-0 text-muted-foreground" />
                  <Avatar name={r.name} color={primary} />
                  <span className="flex min-w-0 flex-col leading-[1.3]">
                    <span className="truncate text-[16px] font-semibold text-foreground">{r.name}</span>
                    <span className="truncate text-[13px] text-muted-foreground">{r.email}{r.agent_count === 0 ? " · no agents yet" : ` · ${r.agent_count} agent${r.agent_count === 1 ? "" : "s"}`}</span>
                  </span>
                </button>
                <Sentence tone={s.tone}>{s.text}</Sentence>
                <span className="flex items-center justify-end gap-2">
                  {actions.includes("resend") && (
                    <RowButton onClick={() => void run("Resending", () => post("/v1/company/resend-rep-invite", { email: r.email }), `Invite resent to ${r.email}.`)}>Resend invite</RowButton>
                  )}
                  <ConsequenceMenu items={menuFor(r)} />
                </span>
              </div>

              {replacing === r.id && (
                <ReplacePanel
                  rep={r}
                  others={reps.filter((o) => o.id !== r.id && o.holds_seat && o.status === "active")}
                  busy={busy}
                  onCancel={() => setReplacing(null)}
                  onSubmit={async (body) => {
                    setBusy(true)
                    try {
                      const res = await post(`/v1/company/reps/${r.id}/reassign`, body)
                      setReplacing(null)
                      setNotice(`${r.name}'s seat is now ${body.name}'s. ${res.agents_moved} agent${res.agents_moved === 1 ? "" : "s"} and ${res.schedules_moved} scheduled send${res.schedules_moved === 1 ? "" : "s"} moved; ${res.notices_queued} agent${res.notices_queued === 1 ? " was" : "s were"} told.`)
                      refresh()
                    } catch (e) {
                      toast({ title: "The replacement didn't go through", description: errorText(e), variant: "destructive" })
                    } finally {
                      setBusy(false)
                    }
                  }}
                />
              )}

              {isOpen && (
                <div className="flex flex-col pb-[10px] pl-7">
                  {agents.slice(0, SHOW).map((a) => (
                    <div key={a.agent_id} className="grid grid-cols-[minmax(0,1.2fr)_110px_minmax(0,1fr)] items-center gap-5 border-l-2 border-[var(--border-subtle)] py-[9px] pl-[22px]">
                      <span className="flex min-w-0 items-center gap-[10px]">
                        <Avatar name={a.agent_name} size={28} />
                        <span className="flex min-w-0 flex-col leading-[1.25]"><span className="truncate text-[14px] font-semibold text-foreground">{a.agent_name}</span><span className="truncate text-[12.5px] text-muted-foreground">{a.email}</span></span>
                      </span>
                      <span className={`text-[13px] font-semibold ${AGENT_STATUS[a.status].cls}`}>{AGENT_STATUS[a.status].label}</span>
                      <span className="text-[14px] text-[var(--body)]">{agentSentence(a)}</span>
                    </div>
                  ))}
                  {agents.length > SHOW && <Link href={`/app/company/agents?rep=${r.id}`} className="border-l-2 border-[var(--border-subtle)] py-2 pl-[22px] text-[13px] font-semibold text-[var(--link)]">All {agents.length} of {r.name.split(" ")[0]}'s agents →</Link>}
                  {agents.length === 0 && <p className="border-l-2 border-[var(--border-subtle)] py-2 pl-[22px] text-[14px] text-muted-foreground">No agents yet.</p>}
                </div>
              )}
            </div>
          )
        })}
        {!isLoading && reps.length === 0 && <ListEmpty>No reps yet. Invite the first one above.</ListEmpty>}
      </RuleList>

      {totalAgents > 0 && <Link href="/app/company/agents" className="self-start text-[14px] font-semibold text-[var(--link)]">All {totalAgents} agents →</Link>}
    </div>
  )
}

type ReassignBody = { name: string; first_name: string; last_name: string; email: string; agents_to_rep_id?: string }

function ReplacePanel({ rep, others, busy, onCancel, onSubmit }: {
  rep: Rep
  others: Rep[]
  busy: boolean
  onCancel: () => void
  onSubmit: (body: ReassignBody) => void
}) {
  const first = rep.name.split(" ")[0] || rep.name
  const [to, setTo] = useState("")
  return (
    <form
      className="mb-[14px] flex flex-col gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface-cream)] p-5"
      onSubmit={(e) => {
        e.preventDefault()
        const data = new FormData(e.currentTarget)
        const names = splitName(String(data.get("name") || ""))
        const email = String(data.get("email") || "").trim()
        if (!names || !email) return
        onSubmit({ ...names, email, ...(to ? { agents_to_rep_id: to } : {}) })
      }}
    >
      <p className="text-[15px] font-semibold text-foreground">Who takes {first}&rsquo;s seat?</p>
      <div className="flex flex-wrap gap-[10px]">
        <input name="name" required placeholder="Their name" autoComplete="off" disabled={busy} className={`${field} min-w-[200px] flex-1`} />
        <input name="email" type="email" required placeholder="Their email" autoComplete="off" disabled={busy} className={`${field} min-w-[240px] flex-[1.4]`} />
      </div>
      {rep.agent_count > 0 && (
        <label className="flex flex-wrap items-center gap-3 text-[14px] text-[var(--body)]">
          {first}&rsquo;s {rep.agent_count} agent{rep.agent_count === 1 ? "" : "s"} go to
          <select value={to} onChange={(e) => setTo(e.target.value)} disabled={busy} className={`${field} h-[40px]`}>
            <option value="">the new rep</option>
            {others.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
          </select>
        </label>
      )}
      <p className="text-[13px] leading-[1.5] text-muted-foreground">
        The new rep gets an invite. {first}&rsquo;s scheduled sends go where the agents go, {first} can no longer sign in, and each agent is told who their rep is now. Agents keep their own plans.
      </p>
      <div className="flex gap-[10px]">
        <button type="submit" disabled={busy} className={inkButton}>Replace {first}</button>
        <button type="button" onClick={onCancel} disabled={busy} className="h-[46px] rounded-[10px] px-[16px] text-[15px] font-semibold text-[var(--body)] hover:bg-[var(--muted)]">Keep {first}</button>
      </div>
    </form>
  )
}

"use client"

// /app/company/reps — "Reps & agents". One surface, two levels: a rep row
// expands to its agents. Replaces the reps table + the separate /agents
// page's reason to exist (keep the route; link to it from "All N agents →").
// Invite is inline, by email. No stat tiles, no search, no export, no
// pagination.

import { useMemo, useState } from "react"
import Link from "next/link"
import { useQueryClient } from "@tanstack/react-query"
import { ChevronDown, ChevronRight } from "lucide-react"
import { PageHeader } from "@/components/page-header"
import { RuleList, ListEmpty } from "@/components/ui/list"
import { useCompanyReps, useCompanyAgents, useCompanyBranding, queryKeys } from "@/hooks/use-api"
import { useToast } from "@/components/ui/use-toast"
import { Avatar, Sentence, RowButton, EmailInvite, post, whenLabel, reportTypeLabel } from "@/components/sponsor/shared"
import { repSentence } from "../page"

type Rep = { id: string; name: string; email: string; office: string; agent_count: number; reports_this_month: number; last_active: string | null; status: "active" | "pending" | "deactivated" }
type Agent = { agent_id: string; agent_name: string; email: string; rep_name: string; status: "active" | "pending" | "deactivated"; plan: string; reports_this_month: number; last_activity: string | null }

const STATUS: Record<Agent["status"], { label: string; cls: string }> = {
  active: { label: "Active", cls: "text-[var(--success-foreground)]" },
  pending: { label: "Invited", cls: "text-muted-foreground" },
  deactivated: { label: "Lapsed", cls: "text-[var(--warning-foreground)]" },
}
const SHOW = 6

export default function RepsAndAgentsPage() {
  const qc = useQueryClient()
  const { toast } = useToast()
  const { data: repsData, isLoading } = useCompanyReps()
  const { data: agentsData } = useCompanyAgents()
  const { data: brandingData } = useCompanyBranding()
  const primary: string = brandingData?.branding?.primary_color || "var(--agent-primary)"
  const [open, setOpen] = useState<Record<string, boolean>>({})
  const [busy, setBusy] = useState(false)
  const [justInvited, setJustInvited] = useState<string | null>(null)

  const reps: Rep[] = (repsData?.reps ?? []).map((r: any) => ({ id: r.id, name: r.name ?? "", email: r.email ?? "", office: r.office ?? "", agent_count: r.agent_count ?? 0, reports_this_month: r.reports_this_month ?? 0, last_active: r.last_active ?? null, status: r.status ?? "pending" }))
  // /v1/company/agents keys agents by rep_name, not rep_id (README → "What the API doesn't return").
  const agentsByRep = useMemo(() => {
    const m: Record<string, Agent[]> = {}
    for (const a of (agentsData?.agents ?? []) as Agent[]) (m[a.rep_name] ||= []).push(a)
    return m
  }, [agentsData])

  // The API requires name/first/last; design is email-only (AFFILIATE_INVENTORY §6b). Derive until /v1/company/invite-rep relaxes.
  async function invite(email: string) {
    const guess = email.split("@")[0].replace(/[._-]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
    const [first_name, ...rest] = guess.split(" ")
    setBusy(true)
    try {
      await post("/v1/company/invite-rep", { name: guess, email, first_name, last_name: rest.join(" ") || "—" })
      setJustInvited(email); qc.invalidateQueries({ queryKey: queryKeys.company.reps() }); qc.invalidateQueries({ queryKey: queryKeys.company.overview })
    } catch (e) { toast({ title: "That didn't go through", description: e instanceof Error ? e.message : undefined, variant: "destructive" }) }
    finally { setBusy(false) }
  }
  async function resend(rep: Rep) {
    try { await post("/v1/company/resend-rep-invite", { email: rep.email }); toast({ title: "Invite resent" }) }
    catch (e) { toast({ title: "That didn't go through", description: e instanceof Error ? e.message : undefined, variant: "destructive" }) }
  }

  const totalAgents = reps.reduce((n, r) => n + r.agent_count, 0)

  return (
    <div className="flex flex-col gap-8">
      <PageHeader title="Reps & agents" description={isLoading ? undefined : `${reps.length} rep${reps.length === 1 ? "" : "s"} · ${totalAgents} agents. Open a rep to see their agents.`} />

      <div className="flex flex-col gap-[10px]">
        <EmailInvite placeholder="Invite a title rep — type their email" button="Send invite" busy={busy} onSubmit={invite} />
        {justInvited
          ? <p className="text-[14px] font-medium text-[var(--success-foreground)]">Invite sent to {justInvited}.</p>
          : <p className="text-[14px] text-muted-foreground">They get your logo and colour on day one and start inviting their own agents.</p>}
      </div>

      <RuleList>
        {reps.map((r) => {
          const s = repSentence(r)
          const agents = agentsByRep[r.name] ?? []
          const isOpen = !!open[r.id]
          const Chev = isOpen ? ChevronDown : ChevronRight
          return (
            <div key={r.id} className="flex flex-col border-b border-[var(--border-subtle)]">
              <div className="grid grid-cols-[minmax(0,1.1fr)_minmax(0,1.5fr)_auto] items-center gap-5 py-[14px] transition-colors hover:bg-[var(--surface-cream)]">
                <button type="button" onClick={() => setOpen((o) => ({ ...o, [r.id]: !isOpen }))} className="flex min-w-0 items-center gap-3 text-left">
                  <Chev className="size-4 shrink-0 text-muted-foreground" />
                  <Avatar name={r.name} color={primary} />
                  <span className="flex min-w-0 flex-col leading-[1.3]">
                    <span className="whitespace-nowrap text-[16px] font-semibold text-foreground">{r.name}</span>
                    <span className="text-[13px] text-muted-foreground">{r.office ? `${r.office} · ` : ""}{r.agent_count === 0 ? "no agents yet" : `${r.agent_count} agent${r.agent_count === 1 ? "" : "s"}`}</span>
                  </span>
                </button>
                <Sentence tone={s.tone}>{s.text}</Sentence>
                <span className="flex justify-end">{r.status === "pending" && <RowButton onClick={() => resend(r)}>Resend invite</RowButton>}</span>
              </div>
              {isOpen && (
                <div className="flex flex-col pb-[10px] pl-7">
                  {agents.slice(0, SHOW).map((a) => (
                    <div key={a.agent_id} className="grid grid-cols-[minmax(0,1.2fr)_110px_minmax(0,1fr)] items-center gap-5 border-l-2 border-[var(--border-subtle)] py-[9px] pl-[22px]">
                      <span className="flex min-w-0 items-center gap-[10px]">
                        <Avatar name={a.agent_name} size={28} />
                        <span className="flex min-w-0 flex-col leading-[1.25]"><span className="truncate text-[14px] font-semibold text-foreground">{a.agent_name}</span><span className="truncate text-[12.5px] text-muted-foreground">{a.email}</span></span>
                      </span>
                      <span className={`text-[13px] font-semibold ${STATUS[a.status].cls}`}>{STATUS[a.status].label}</span>
                      <span className="text-[14px] text-[var(--body)]">{a.status === "pending" ? "Hasn't taken the seat" : a.last_activity ? `Last sent ${whenLabel(a.last_activity).toLowerCase()}` : "Nothing sent yet"}</span>
                    </div>
                  ))}
                  {agents.length > SHOW && <Link href={`/app/company/agents?rep=${r.id}`} className="border-l-2 border-[var(--border-subtle)] py-2 pl-[22px] text-[13px] font-semibold text-[var(--link)]">All {r.agent_count} of {r.name.split(" ")[0]}'s agents →</Link>}
                  {agents.length === 0 && <p className="border-l-2 border-[var(--border-subtle)] py-2 pl-[22px] text-[14px] text-muted-foreground">No agents yet.</p>}
                </div>
              )}
            </div>
          )
        })}
        {!isLoading && reps.length === 0 && <ListEmpty>No reps yet. Invite the first one above.</ListEmpty>}
      </RuleList>
    </div>
  )
}

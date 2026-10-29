"use client"

// /app/company/activity — Activity. What the company's reps and their agents
// have made, and what is set to go out on its own. One page, two views
// (?view=schedules), on the rule-list and sentence vocabulary of People.
//
// Replaces /app/company/reports and /app/company/schedules, which typed their
// rows by hand against fields the API never returned: every report read
// "Generating" with no name, date or PDF, and schedules counted nothing
// (D-317). Those paths now redirect here.
//
// Read-only for everyone on the account: the schedules are the reps' and
// agents' own, and there is no company endpoint that changes them. A finished
// report keeps the PDF link the old page had.

import { Suspense, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { PageHeader } from "@/components/page-header"
import { FilterPills, ListEmpty, RuleList } from "@/components/ui/list"
import { useCompanyBranding, useCompanyReports, useCompanyReps, useCompanySchedules } from "@/hooks/use-api"
import { Avatar, Sentence, whenLabel } from "@/components/sponsor/shared"
import type { Rep } from "@/lib/company-people"
import {
  byWho, pdfFor, reportState, reportWhat, scheduleNext, scheduleWhat, scheduleWhen, who,
  type ActivityReport, type ActivitySchedule, type WhoFilter,
} from "@/lib/company-activity"

type View = "reports" | "schedules"
const PAGE = 50

function Person({ row, color }: { row: ActivityReport | ActivitySchedule; color?: string }) {
  const w = who(row)
  return (
    <span className="flex min-w-0 items-center gap-3">
      <Avatar name={w.name} size={34} color={row.user_type === "Rep" ? color : undefined} />
      <span className="flex min-w-0 flex-col leading-[1.3]"><span className="truncate text-[15px] font-semibold text-foreground">{w.name}</span><span className="truncate text-[13px] text-muted-foreground">{w.sub}</span></span>
    </span>
  )
}

function Activity() {
  const params = useSearchParams()
  const router = useRouter()
  const view: View = params.get("view") === "schedules" ? "schedules" : "reports"
  const rep = params.get("rep")
  const [whoFilter, setWho] = useState<WhoFilter>("everyone")
  const [limit, setLimit] = useState(PAGE)

  const { data: repsData } = useCompanyReps()
  const { data: brandingData } = useCompanyBranding()
  const reportsQ = useCompanyReports(rep, limit)
  const schedulesQ = useCompanySchedules(rep)
  const primary: string = brandingData?.branding?.primary_color || "var(--agent-primary)"
  const reps: Rep[] = repsData?.reps ?? []

  const go = (next: { view?: View; rep?: string | null }) => {
    const q = new URLSearchParams()
    const v = next.view ?? view
    const r = next.rep === undefined ? rep : next.rep
    if (v === "schedules") q.set("view", "schedules")
    if (r) q.set("rep", r)
    setLimit(PAGE)
    router.replace(`/app/company/activity${q.size ? `?${q}` : ""}`)
  }

  const error = view === "reports" ? reportsQ.error : schedulesQ.error
  if (error) {
    return <p className="text-[16px] text-muted-foreground">{String(error).includes("403") ? "This account isn't on a title company." : "Couldn't load the activity right now."}</p>
  }

  const reports = byWho<ActivityReport>(reportsQ.data?.reports ?? [], whoFilter)
  const total: number = reportsQ.data?.total ?? 0
  const loaded: number = reportsQ.data?.reports?.length ?? 0
  const schedules = byWho<ActivitySchedule>(schedulesQ.data?.schedules ?? [], whoFilter)
  const repName = rep ? reps.find((r) => r.id === rep)?.name : null

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="Activity"
        description={`What ${repName ? `${repName} and their agents have` : "your reps and their agents have"} made, and what's set to go out on its own.`}
      />

      <div className="flex flex-wrap items-center justify-between gap-4">
        <FilterPills<View> value={view} onChange={(v) => go({ view: v })} options={[{ value: "reports", label: "Reports" }, { value: "schedules", label: "Schedules" }]} />
        <div className="flex flex-wrap items-center gap-3">
          <FilterPills<WhoFilter> value={whoFilter} onChange={setWho} options={[{ value: "everyone", label: "Everyone" }, { value: "Rep", label: "Reps" }, { value: "Agent", label: "Agents" }]} />
          <select
            aria-label="Rep"
            value={rep ?? ""}
            onChange={(e) => go({ rep: e.target.value || null })}
            className="h-9 rounded-[9px] border border-[var(--border)] bg-white px-3 text-[14px] text-foreground"
          >
            <option value="">All reps</option>
            {reps.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
          </select>
        </div>
      </div>

      {view === "reports" ? (
        <div className="flex flex-col gap-4">
          <RuleList>
            {reports.map((r) => { const s = reportState(r.status); const pdf = pdfFor(r); return (
              <div key={r.id} className="grid grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)_minmax(0,0.8fr)_90px_48px] items-center gap-5 border-b border-[var(--border-subtle)] py-[13px]">
                <Person row={r} color={primary} />
                <span className="truncate text-[15px] text-[var(--body)]">{reportWhat(r)}</span>
                <Sentence tone={s.tone}>{s.text}</Sentence>
                <span className="whitespace-nowrap text-right text-[14px] text-muted-foreground">{whenLabel(r.generated_at)}</span>
                <span className="text-right">{pdf && <a href={pdf} target="_blank" rel="noopener noreferrer" className="text-[14px] font-semibold text-[var(--link)] hover:text-[var(--link-hover)]">PDF</a>}</span>
              </div>
            )})}
            {!reportsQ.isLoading && reports.length === 0 && <ListEmpty>{loaded ? "No one matches that filter." : "No reports yet."}</ListEmpty>}
          </RuleList>
          {loaded < total && (
            <button type="button" onClick={() => setLimit((n) => n + PAGE)} disabled={reportsQ.isFetching} className="self-start text-[14px] font-semibold text-[var(--link)] hover:text-[var(--link-hover)] disabled:opacity-60">
              {reportsQ.isFetching ? "Loading…" : `Show more · ${loaded} of ${total}`}
            </button>
          )}
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <RuleList>
            {schedules.map((s) => { const n = scheduleNext(s); return (
              <div key={s.id} className="grid grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)_minmax(0,1.1fr)_130px] items-center gap-5 border-b border-[var(--border-subtle)] py-[13px]">
                <Person row={s} color={primary} />
                <span className="flex min-w-0 flex-col leading-[1.3]"><span className="truncate text-[15px] text-foreground">{scheduleWhat(s)}</span><span className="truncate text-[13px] text-muted-foreground">{s.name}</span></span>
                <span className="text-[14px] text-[var(--body)]">{scheduleWhen(s)}</span>
                <Sentence tone={n.tone}>{n.text}</Sentence>
              </div>
            )})}
            {!schedulesQ.isLoading && schedules.length === 0 && <ListEmpty>{(schedulesQ.data?.schedules ?? []).length ? "No one matches that filter." : "No schedules yet."}</ListEmpty>}
          </RuleList>
          <p className="text-[14px] text-muted-foreground">These are your reps&apos; and agents&apos; own schedules — you can see them, not change them.</p>
        </div>
      )}
    </div>
  )
}

export default function ActivityPage() {
  // useSearchParams needs a Suspense boundary in the app router.
  return <Suspense fallback={null}><Activity /></Suspense>
}

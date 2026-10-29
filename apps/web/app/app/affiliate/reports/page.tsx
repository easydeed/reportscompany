"use client"

// /app/affiliate/reports — the rep's Reports feed. Design's rep Reports
// (Sponsor v4): pills My agents' · Mine · Everything (from `source`), a row
// per report — who, what and where, whether it finished, when.
//
// The page it replaces typed its rows against fields GET
// /v1/affiliate/all-reports never returned, so every report read
// "Generating" with no agent or date (D-324). Read-only; a finished report
// keeps the PDF link reps had (Jerry: keep). Leads are on their own page:
// market reports capture none, so there is no per-report lead count to show.

import { useState } from "react"
import Link from "next/link"
import { PageHeader } from "@/components/page-header"
import { FilterPills, ListEmpty, RuleList } from "@/components/ui/list"
import { useRepReports } from "@/hooks/use-api"
import { Avatar, Sentence, whenLabel } from "@/components/sponsor/shared"
import { bySource, pdfFor, reportState, reportWhat, type RepReport, type SourceFilter } from "@/lib/rep-book"

const PAGE = 50

export default function RepReportsPage() {
  const [filter, setFilter] = useState<SourceFilter>("agents")
  const [limit, setLimit] = useState(PAGE)
  const { data, isLoading, isFetching, error } = useRepReports(limit)

  if (error) return <p className="text-[16px] text-muted-foreground">{String(error).includes("403") ? "This account isn't a rep's." : "Couldn't load the reports right now."}</p>

  const all: RepReport[] = data?.reports ?? []
  const rows = bySource(all, filter)
  const total: number = data?.total ?? 0

  return (
    <div className="flex flex-col gap-8">
      <PageHeader title="Reports" description="What your agents have made, and what you've made yourself, newest first." />
      <FilterPills<SourceFilter> value={filter} onChange={setFilter} options={[
        { value: "agents", label: "My agents'" }, { value: "mine", label: "Mine" }, { value: "all", label: "Everything" },
      ]} />
      <div className="flex flex-col gap-4">
        <RuleList>
          {rows.map((r) => { const s = reportState(r.status); const pdf = pdfFor(r); const name = r.source === "You" ? "You" : r.user_name || "An agent"; return (
            <div key={r.id} className="grid grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)_minmax(0,0.8fr)_90px_48px] items-center gap-5 border-b border-[var(--border-subtle)] py-[13px]">
              <span className="flex min-w-0 items-center gap-3">
                <Avatar name={name} size={34} />
                {r.source === "Agent"
                  ? <Link href={`/app/affiliate/agents/${r.agent_account_id}`} className="truncate text-[15px] font-semibold text-foreground hover:text-[var(--link)]">{name}</Link>
                  : <span className="truncate text-[15px] font-semibold text-foreground">{name}</span>}
              </span>
              <span className="truncate text-[15px] text-[var(--body)]">{reportWhat(r)}</span>
              <Sentence tone={s.tone}>{s.text}</Sentence>
              <span className="whitespace-nowrap text-right text-[14px] text-muted-foreground">{whenLabel(r.generated_at)}</span>
              <span className="text-right">{pdf && <a href={pdf} target="_blank" rel="noopener noreferrer" className="text-[14px] font-semibold text-[var(--link)] hover:text-[var(--link-hover)]">PDF</a>}</span>
            </div>
          )})}
          {!isLoading && rows.length === 0 && <ListEmpty>{all.length ? "Nothing here under that filter." : "No reports yet."}</ListEmpty>}
        </RuleList>
        {all.length < total && (
          <button type="button" onClick={() => setLimit((k) => k + PAGE)} disabled={isFetching} className="self-start text-[14px] font-semibold text-[var(--link)] hover:text-[var(--link-hover)] disabled:opacity-60">
            {isFetching ? "Loading…" : `Show more · ${all.length} of ${total}`}
          </button>
        )}
        <p className="text-[14px] text-muted-foreground">You see that reports went out. The reports themselves belong to the agents who made them.</p>
      </div>
    </div>
  )
}

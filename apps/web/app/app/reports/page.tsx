"use client"

import { useState } from "react"
import Link from "next/link"
import { Plus, Download, Eye, Share2 } from "lucide-react"
import { PageHeader } from "@/components/page-header"
import { Skeleton } from "@/components/ui/skeleton"
import { StatusBadge } from "@/components/status-badge"
import { RuleList, ListHeader, ListRow, Cell, Text, IconButton, FilterPills, ListEmpty } from "@/components/ui/list"
import { ReportThumb } from "@/components/shared/report-thumb"
import { useReports, usePlanUsage, useBranding } from "@/hooks/use-api"
import type { PreviewReportType } from "@/components/shared/email-preview/sample-data"

type Report = { id: string; report_type: string; city?: string; status: "completed" | "processing" | "pending" | "failed"; html_url?: string; pdf_url?: string; generated_at: string; schedule_name?: string | null }
type Filter = "all" | "scheduled" | "manual" | "market_snapshot" | "closed" | "new_listings"

const KIND: Record<string, string> = { market_snapshot: "Market Snapshot", closed: "Closed Sales", new_listings: "New Listings", new_listings_gallery: "New Listings", inventory: "Active Inventory", price_bands: "Price Bands", featured_listings: "Featured Listings", open_houses: "Open Houses" }
const COLS = "72px minmax(0,1.6fr) minmax(0,1fr) minmax(0,1fr) auto 112px"

export default function ReportsPage() {
  const { data, isLoading, error } = useReports()
  const { data: planUsage } = usePlanUsage()
  const { data: branding } = useBranding() as { data: any }
  const [filter, setFilter] = useState<Filter>("all")

  const all: Report[] = data?.reports || []
  const reports = all.filter((r) => filter === "all" ? true : filter === "scheduled" ? !!r.schedule_name : filter === "manual" ? !r.schedule_name : r.report_type === filter || (filter === "new_listings" && r.report_type === "new_listings_gallery"))

  // Sub-line: derived or absent.
  const month = new Date(); month.setDate(1); month.setHours(0, 0, 0, 0)
  const thisMonth = all.filter((r) => new Date(r.generated_at) >= month).length
  const limit = planUsage?.plan?.market_reports_limit, used = planUsage?.usage?.market_reports_used, plan = planUsage?.plan?.plan_name
  const left = typeof limit === "number" && typeof used === "number" && limit < 999 ? Math.max(limit - used, 0) : null
  const sub = isLoading ? undefined : [`${thisMonth} this month`, left !== null && plan ? `${left} left on ${plan}` : null].filter(Boolean).join(" · ")

  const preview = { primaryColor: branding?.primary_color, accentColor: branding?.accent_color, lookbackDays: 30 }

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="Market reports"
        description={sub}
        action={
          <Link href="/app/reports/new" prefetch={false} className="inline-flex h-[42px] items-center gap-2 rounded-[9px] bg-primary px-[18px] text-[14px] font-semibold text-primary-foreground hover:bg-[var(--primary-hover)] hover:text-primary-foreground"><Plus className="size-[15px]" />New report</Link>
        }
      />

      <FilterPills value={filter} onChange={setFilter} options={[
        { value: "all", label: "All" }, { value: "scheduled", label: "Sent to contacts" }, { value: "manual", label: "Downloaded only" },
        { value: "market_snapshot", label: "Snapshot" }, { value: "closed", label: "Closed" }, { value: "new_listings", label: "Listings" },
      ]} />

      {error && <p className="text-[14px] text-[var(--destructive-foreground)]">Reports aren't loading right now. Try again in a moment.</p>}

      <RuleList>
        <ListHeader columns={COLS} cells={["", "Report", "Area", "Created", "Status", ""]} />
        {isLoading ? [0, 1, 2, 3].map((i) => (
          <div key={i} className="grid items-center gap-[18px] border-b border-[var(--border-subtle)] py-3" style={{ gridTemplateColumns: COLS }}>
            <Skeleton className="h-[94px] w-[72px] rounded-[3px]" /><Skeleton className="h-4 w-40" /><Skeleton className="h-4 w-24" /><Skeleton className="h-4 w-20" /><Skeleton className="h-5 w-14 rounded-full" /><span />
          </div>
        )) : reports.length === 0 ? (
          <ListEmpty>
            {all.length === 0 ? "No reports yet." : "Nothing matches that filter."}
            {all.length === 0 && <Link href="/app/reports/new" prefetch={false} className="font-semibold">Make your first one →</Link>}
          </ListEmpty>
        ) : reports.map((r) => (
          <ListRow key={r.id} columns={COLS}>
            <ReportThumb width={72} shadow="thumb" {...preview} reportType={(r.report_type in KIND ? r.report_type : "market_snapshot") as PreviewReportType} areaName={r.city ?? ""} />
            <Cell title={KIND[r.report_type] ?? r.report_type.replace(/_/g, " ")} sub={r.schedule_name ? `Schedule · ${r.schedule_name}` : "Manual"} />
            <Text>{r.city || "—"}</Text>
            <Text>{new Date(r.generated_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</Text>
            <StatusBadge status={r.status} />
            <div className="flex w-[112px] justify-end gap-1">
              {r.html_url && <IconButton href={r.html_url} external label="Preview"><Eye /></IconButton>}
              {r.pdf_url && <IconButton href={r.pdf_url} external label="Download PDF"><Download /></IconButton>}
              {r.status === "completed" && <IconButton href={`/social/${r.id}`} external label="Share" tone="link"><Share2 /></IconButton>}
            </div>
          </ListRow>
        ))}
      </RuleList>
    </div>
  )
}

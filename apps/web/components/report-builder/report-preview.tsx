"use client"

import { Eye } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { 
  ReportBuilderState, 
  ReportType, 
  BrandingContext, 
  ProfileContext 
} from "./types"
import { REPORT_TYPE_CONFIG, getAreaDisplay, getReportTitle } from "./types"

interface ReportPreviewProps {
  state: ReportBuilderState
  branding: BrandingContext
  profile: ProfileContext
  onPreview?: () => void
}

export function ReportPreview({ state, branding, profile, onPreview }: ReportPreviewProps) {
  const config = REPORT_TYPE_CONFIG[state.reportType]
  const Icon = config.icon
  const areaDisplay = getAreaDisplay(state)
  const reportTitle = getReportTitle(state)

  return (
    <div className="space-y-4 rounded-xl border bg-card p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Report Preview</span>
        <span className="text-xs text-muted-foreground">Updates as you build</span>
      </div>

      {/* Report Mockup */}
      <div className="overflow-hidden rounded-lg border bg-white shadow-sm">
        {/* Header */}
        <div 
          className="px-4 py-6 text-center text-white"
          style={{
            background: `linear-gradient(135deg, ${branding.primaryColor} 0%, ${branding.accentColor} 100%)`,
          }}
        >
          {branding.pdfHeaderLogoUrl ? (
            <img 
              src={branding.pdfHeaderLogoUrl} 
              alt={branding.displayName || "Logo"}
              className="mx-auto mb-3 h-6 w-auto"
            />
          ) : (
            <div className="mb-2 text-xs font-medium opacity-80">
              {branding.displayName || "TrendyReports"}
            </div>
          )}
          <h2 className="text-lg font-bold">{reportTitle}</h2>
          {areaDisplay && <p className="mt-1 text-sm opacity-90">{areaDisplay}</p>}
          <p className="text-xs opacity-75">Last {state.lookbackDays} Days</p>
        </div>

        {/* Content based on report type */}
        <div className="p-4">
          <ReportContent reportType={state.reportType} primaryColor={branding.primaryColor} />
        </div>

        {/* Footer */}
        <div className="border-t bg-muted/30 px-4 py-3">
          <div className="flex items-center gap-3">
            <div 
              className="h-8 w-8 rounded-full flex items-center justify-center text-xs font-medium text-white overflow-hidden"
              style={{ backgroundColor: branding.primaryColor }}
            >
              {profile.avatarUrl ? (
                <img src={profile.avatarUrl} alt={profile.name} className="w-full h-full object-cover" />
              ) : (
                profile.name?.charAt(0) || "?"
              )}
            </div>
            <div className="text-xs min-w-0">
              <p className="font-medium truncate">{profile.name}</p>
              <p className="text-muted-foreground truncate">
                {[profile.phone, profile.email].filter(Boolean).join(" · ")}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Info Badge */}
      <div className="flex items-center gap-2 rounded-lg bg-muted/50 px-3 py-2">
        <Icon className="h-4 w-4 shrink-0" style={{ color: branding.primaryColor }} />
        <div className="text-xs min-w-0">
          <span className="font-medium">{config.label}</span>
          {areaDisplay && (
            <span className="text-muted-foreground">
              {" "}· 📍 {areaDisplay} · Last {state.lookbackDays} days
            </span>
          )}
        </div>
      </div>

      {/* Preview Button */}
      <Button variant="outline" className="w-full gap-2 bg-transparent" onClick={onPreview}>
        <Eye className="h-4 w-4" />
        Preview Full Report
      </Button>
    </div>
  )
}

function ReportContent({ reportType, primaryColor }: { reportType: ReportType; primaryColor: string }) {
  switch (reportType) {
    case "market_snapshot":
      return (
        <div className="space-y-4">
          <div className="text-center">
            <p className="text-xs uppercase text-muted-foreground">Median Sale Price</p>
            <p className="text-2xl font-bold" style={{ color: primaryColor }}>$1.15M</p>
          </div>
          <div className="grid grid-cols-4 gap-2 text-center">
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="text-lg font-semibold">42</p>
              <p className="text-[10px] text-muted-foreground">Closed</p>
            </div>
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="text-lg font-semibold">24</p>
              <p className="text-[10px] text-muted-foreground">Avg DOM</p>
            </div>
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="text-lg font-semibold">2.4</p>
              <p className="text-[10px] text-muted-foreground">MOI</p>
            </div>
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="text-lg font-semibold">18</p>
              <p className="text-[10px] text-muted-foreground">Pending</p>
            </div>
          </div>
          <div className="h-16 rounded-lg" style={{ background: `linear-gradient(to right, ${primaryColor}20, ${primaryColor}10)` }} />
        </div>
      )

    case "new_listings_gallery":
      return (
        <div className="space-y-4">
          <div className="text-center">
            <p className="text-xs uppercase text-muted-foreground">New Listings</p>
            <p className="text-2xl font-bold" style={{ color: primaryColor }}>127</p>
          </div>
          <div className="grid grid-cols-2 gap-1.5 text-center">
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="font-semibold">$985K</p>
              <p className="text-[10px] text-muted-foreground">Median</p>
            </div>
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="font-semibold">$425K</p>
              <p className="text-[10px] text-muted-foreground">Starting</p>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-1.5">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="aspect-square rounded bg-muted/70" />
            ))}
          </div>
        </div>
      )

    case "closed":
      return (
        <div className="space-y-4">
          <div className="text-center">
            <p className="text-xs uppercase text-muted-foreground">Total Closed</p>
            <p className="text-2xl font-bold" style={{ color: primaryColor }}>42</p>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="font-semibold">$1.08M</p>
              <p className="text-[10px] text-muted-foreground">Median</p>
            </div>
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="font-semibold">18</p>
              <p className="text-[10px] text-muted-foreground">Avg DOM</p>
            </div>
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="font-semibold">98.2%</p>
              <p className="text-[10px] text-muted-foreground">Close-List</p>
            </div>
          </div>
          <div className="space-y-1">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex justify-between rounded bg-muted/30 px-2 py-1.5 text-xs">
                <span>123 Oak St</span>
                <span className="font-medium">$1.2M</span>
              </div>
            ))}
          </div>
        </div>
      )

    case "inventory":
      return (
        <div className="space-y-4">
          <div className="text-center">
            <p className="text-xs uppercase text-muted-foreground">Active Listings</p>
            <p className="text-2xl font-bold" style={{ color: primaryColor }}>127</p>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="font-semibold">23</p>
              <p className="text-[10px] text-muted-foreground">New</p>
            </div>
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="font-semibold">24</p>
              <p className="text-[10px] text-muted-foreground">Median DOM</p>
            </div>
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="font-semibold">2.4</p>
              <p className="text-[10px] text-muted-foreground">MOI</p>
            </div>
          </div>
          <div className="space-y-1">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex justify-between rounded bg-muted/30 px-2 py-1.5 text-xs">
                <span>456 Maple Ave</span>
                <span className="font-medium">$985K</span>
              </div>
            ))}
          </div>
        </div>
      )

    case "price_bands":
      return (
        <div className="space-y-4">
          <div className="text-center">
            <p className="text-xs uppercase text-muted-foreground">Total Listings</p>
            <p className="text-2xl font-bold" style={{ color: primaryColor }}>127</p>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="font-semibold">$985K</p>
              <p className="text-[10px] text-muted-foreground">Median</p>
            </div>
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="font-semibold">24</p>
              <p className="text-[10px] text-muted-foreground">Avg DOM</p>
            </div>
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="font-semibold text-xs">$400K-2.5M</p>
              <p className="text-[10px] text-muted-foreground">Range</p>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs">
              <div className="h-2 flex-1 rounded-full bg-emerald-200">
                <div className="h-full w-1/4 rounded-full bg-emerald-500" />
              </div>
              <span className="w-20 text-muted-foreground">Entry: 12</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div className="h-2 flex-1 rounded-full" style={{ backgroundColor: `${primaryColor}30` }}>
                <div className="h-full w-1/2 rounded-full" style={{ backgroundColor: primaryColor }} />
              </div>
              <span className="w-20 text-muted-foreground">Move-Up: 28</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div className="h-2 flex-1 rounded-full bg-amber-200">
                <div className="h-full w-1/5 rounded-full bg-amber-500" />
              </div>
              <span className="w-20 text-muted-foreground">Luxury: 10</span>
            </div>
          </div>
        </div>
      )

    case "open_houses":
      return (
        <div className="space-y-4">
          <div className="text-center">
            <p className="text-xs uppercase text-muted-foreground">Open Houses This Weekend</p>
            <p className="text-2xl font-bold" style={{ color: primaryColor }}>15</p>
          </div>
          <div className="grid grid-cols-2 gap-2 text-center">
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="text-lg font-semibold">8</p>
              <p className="text-[10px] text-muted-foreground">Saturday</p>
            </div>
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="text-lg font-semibold">7</p>
              <p className="text-[10px] text-muted-foreground">Sunday</p>
            </div>
          </div>
          <div className="space-y-1">
            <div className="flex justify-between rounded bg-muted/30 px-2 py-1.5 text-xs">
              <span>123 Oak St</span>
              <span className="text-muted-foreground">Sat 1-4pm</span>
              <span className="font-medium">$1.2M</span>
            </div>
            <div className="flex justify-between rounded bg-muted/30 px-2 py-1.5 text-xs">
              <span>456 Maple</span>
              <span className="text-muted-foreground">Sun 2-5pm</span>
              <span className="font-medium">$985K</span>
            </div>
          </div>
        </div>
      )

    default:
      return null
  }
}


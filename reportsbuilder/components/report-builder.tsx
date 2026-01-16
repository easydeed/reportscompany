"use client"

import type React from "react"

import { useState } from "react"
import {
  ArrowLeft,
  BarChart3,
  Camera,
  Home,
  Package,
  DollarSign,
  DoorOpen,
  MapPin,
  Check,
  AlertCircle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { ReportTypeSection } from "./report-builder/report-type-section"
import { AreaSection } from "./report-builder/area-section"
import { AudienceSection } from "./report-builder/audience-section"
import { DeliverySection } from "./report-builder/delivery-section"
import { ReportPreview } from "./report-builder/report-preview"

export type ReportType =
  | "market_snapshot"
  | "new_listings_gallery"
  | "closed"
  | "inventory"
  | "price_bands"
  | "open_houses"

export type LookbackDays = 7 | 14 | 30 | 60 | 90

export type AreaType = "city" | "zip"

export type AudienceFilter = "all" | "first_time" | "luxury" | "families" | "condo" | "investors" | null

export interface EmailRecipient {
  type: "contact" | "manual_email"
  id?: string
  name?: string
  email: string
}

export interface ReportBuilderState {
  reportType: ReportType
  lookbackDays: LookbackDays
  areaType: AreaType
  city: string | null
  zipCodes: string[]
  audienceFilter: AudienceFilter
  viewInBrowser: boolean
  downloadPdf: boolean
  downloadSocialImage: boolean
  sendViaEmail: boolean
  emailRecipients: EmailRecipient[]
}

const initialState: ReportBuilderState = {
  reportType: "market_snapshot",
  lookbackDays: 30,
  areaType: "city",
  city: null,
  zipCodes: [],
  audienceFilter: null,
  viewInBrowser: true,
  downloadPdf: true,
  downloadSocialImage: false,
  sendViaEmail: false,
  emailRecipients: [],
}

export const reportTypeConfig: Record<ReportType, { label: string; description: string; icon: React.ElementType }> = {
  market_snapshot: { label: "Market Snapshot", description: "Stats & trends", icon: BarChart3 },
  new_listings_gallery: { label: "New Listings", description: "Photo gallery", icon: Camera },
  closed: { label: "Closed Sales", description: "Recently sold", icon: Home },
  inventory: { label: "Inventory Report", description: "Available now", icon: Package },
  price_bands: { label: "Price Analysis", description: "Price distribution", icon: DollarSign },
  open_houses: { label: "Open Houses", description: "Upcoming events", icon: DoorOpen },
}

export function ReportBuilder() {
  const [state, setState] = useState<ReportBuilderState>(initialState)
  const [openSections, setOpenSections] = useState<string[]>(["report-type"])

  const updateState = <K extends keyof ReportBuilderState>(key: K, value: ReportBuilderState[K]) => {
    setState((prev) => ({ ...prev, [key]: value }))
  }

  // Validation
  const isAreaValid = state.areaType === "city" ? !!state.city : state.zipCodes.length > 0
  const hasDeliveryOption = state.viewInBrowser || state.downloadPdf || state.downloadSocialImage || state.sendViaEmail
  const isEmailValid = !state.sendViaEmail || state.emailRecipients.length > 0
  const isValid = isAreaValid && hasDeliveryOption && isEmailValid

  // Section statuses
  const getAreaStatus = () => {
    if (isAreaValid) return "complete"
    return "warning"
  }

  const getAudienceStatus = () => {
    if (state.audienceFilter && state.audienceFilter !== "all") return "complete"
    return "optional"
  }

  const getDeliveryStatus = () => {
    if (!hasDeliveryOption) return "warning"
    if (state.sendViaEmail && state.emailRecipients.length === 0) return "warning"
    return "complete"
  }

  const getAreaDisplay = () => {
    if (state.areaType === "city" && state.city) {
      return state.city
    }
    if (state.areaType === "zip" && state.zipCodes.length > 0) {
      return `${state.zipCodes.length} ZIP codes`
    }
    return null
  }

  const handleGenerate = () => {
    if (!isValid) return

    // Mock generation behavior
    const actions: string[] = []
    if (state.viewInBrowser) actions.push("Opening report in browser...")
    if (state.downloadPdf) actions.push("Downloading PDF...")
    if (state.downloadSocialImage) actions.push("Downloading social image...")
    if (state.sendViaEmail) actions.push(`Sending email to ${state.emailRecipients.length} recipient(s)...`)

    alert(actions.join("\n"))
  }

  return (
    <div className="min-h-screen bg-muted/30">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <button className="flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground">
            <ArrowLeft className="h-4 w-4" />
            Back to Reports
          </button>
          <div className="flex items-center gap-3">
            <Button variant="ghost">Cancel</Button>
            <Button
              onClick={handleGenerate}
              disabled={!isValid}
              className="bg-violet-600 hover:bg-violet-700 text-white"
            >
              Generate Report
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="grid grid-cols-[1fr,420px] gap-8">
          {/* Left Panel - Configuration */}
          <div className="space-y-4">
            <Accordion type="multiple" value={openSections} onValueChange={setOpenSections} className="space-y-4">
              {/* Section 1: Report Type */}
              <AccordionSection
                value="report-type"
                title="Report Type"
                status="complete"
                summary={
                  !openSections.includes("report-type") ? (
                    <span className="flex items-center gap-2 text-sm text-muted-foreground">
                      {(() => {
                        const Icon = reportTypeConfig[state.reportType].icon
                        return <Icon className="h-4 w-4" />
                      })()}
                      {reportTypeConfig[state.reportType].label} · Last {state.lookbackDays} days
                    </span>
                  ) : null
                }
              >
                <ReportTypeSection state={state} updateState={updateState} />
              </AccordionSection>

              {/* Section 2: Area */}
              <AccordionSection
                value="area"
                title="Area"
                status={getAreaStatus()}
                summary={
                  !openSections.includes("area") && getAreaDisplay() ? (
                    <span className="flex items-center gap-2 text-sm text-muted-foreground">
                      <MapPin className="h-4 w-4" />
                      {getAreaDisplay()}
                    </span>
                  ) : null
                }
              >
                <AreaSection state={state} updateState={updateState} />
              </AccordionSection>

              {/* Section 3: Audience Filter (Conditional) */}
              {state.reportType === "new_listings_gallery" && (
                <AccordionSection
                  value="audience"
                  title="Audience Filter"
                  status={getAudienceStatus()}
                  summary={
                    !openSections.includes("audience") && state.audienceFilter && state.audienceFilter !== "all" ? (
                      <span className="flex items-center gap-2 text-sm text-muted-foreground">
                        🎯 {audienceLabels[state.audienceFilter]}
                      </span>
                    ) : null
                  }
                >
                  <AudienceSection state={state} updateState={updateState} />
                </AccordionSection>
              )}

              {/* Section 4: Delivery Options */}
              <AccordionSection
                value="delivery"
                title="Delivery Options"
                status={getDeliveryStatus()}
                summary={
                  !openSections.includes("delivery") ? (
                    <span className="flex items-center gap-2 text-sm text-muted-foreground">
                      {[
                        state.viewInBrowser && "🌐 Browser",
                        state.downloadPdf && "📄 PDF",
                        state.downloadSocialImage && "📱 Social",
                        state.sendViaEmail && "📧 Email",
                      ]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                  ) : null
                }
              >
                <DeliverySection state={state} updateState={updateState} />
              </AccordionSection>
            </Accordion>
          </div>

          {/* Right Panel - Preview */}
          <div className="sticky top-24 h-fit">
            <ReportPreview state={state} getAreaDisplay={getAreaDisplay} />
          </div>
        </div>
      </main>
    </div>
  )
}

const audienceLabels: Record<Exclude<AudienceFilter, null>, string> = {
  all: "All Listings",
  first_time: "First-Time Buyers",
  luxury: "Luxury Clients",
  families: "Families",
  condo: "Condo Buyers",
  investors: "Investors",
}

interface AccordionSectionProps {
  value: string
  title: string
  status: "complete" | "warning" | "optional"
  summary?: React.ReactNode
  children: React.ReactNode
}

function AccordionSection({ value, title, status, summary, children }: AccordionSectionProps) {
  return (
    <AccordionItem value={value} className="rounded-xl border bg-card shadow-sm">
      <AccordionTrigger className="px-6 py-4 hover:no-underline [&[data-state=open]>div>svg]:rotate-180">
        <div className="flex flex-1 items-center gap-3">
          <StatusIndicator status={status} />
          <span className="font-medium">{title}</span>
          {summary && <div className="ml-auto mr-4">{summary}</div>}
        </div>
      </AccordionTrigger>
      <AccordionContent className="px-6 pb-6">{children}</AccordionContent>
    </AccordionItem>
  )
}

function StatusIndicator({ status }: { status: "complete" | "warning" | "optional" }) {
  if (status === "complete") {
    return (
      <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500 text-white">
        <Check className="h-3 w-3" />
      </div>
    )
  }
  if (status === "warning") {
    return (
      <div className="flex h-5 w-5 items-center justify-center rounded-full bg-amber-500 text-white">
        <AlertCircle className="h-3 w-3" />
      </div>
    )
  }
  return <div className="h-5 w-5 rounded-full border-2 border-muted-foreground/30" />
}

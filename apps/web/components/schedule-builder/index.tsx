"use client"

import { useState, useCallback, useEffect } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Loader2 } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ConfigurationPanel } from "./configuration-panel"
import { EmailPreviewPanel } from "./email-preview-panel"
import type { 
  ScheduleBuilderState, 
  ScheduleApiPayload, 
  Recipient, 
  BrandingContext, 
  ProfileContext 
} from "./types"
import { AUDIENCE_FILTER_PRESETS, AUDIENCE_FILTERS } from "./types"

const initialState: ScheduleBuilderState = {
  name: "",
  reportType: "market_snapshot",
  lookbackDays: 30,
  areaType: "city",
  city: null,
  zipCodes: [],
  audienceFilter: null,
  audienceFilterName: null,
  cadence: "weekly",
  weeklyDow: 1,
  monthlyDom: 1,
  sendHour: 9,
  sendMinute: 0,
  timezone: "America/Los_Angeles",
  recipients: [],
  includeAttachment: false,
}

const defaultBranding: BrandingContext = {
  primaryColor: "#6366f1",
  accentColor: "#8b5cf6",
  emailLogoUrl: null,
  displayName: null,
}

const defaultProfile: ProfileContext = {
  name: "Your Name",
  jobTitle: "Real Estate Agent",
  avatarUrl: null,
  phone: null,
  email: "you@example.com",
}

interface ScheduleBuilderProps {
  scheduleId?: string // For edit mode
}

export function ScheduleBuilder({ scheduleId }: ScheduleBuilderProps) {
  const router = useRouter()
  const [state, setState] = useState<ScheduleBuilderState>(initialState)
  const [expandedSection, setExpandedSection] = useState<string>("name")
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(!!scheduleId)
  const [error, setError] = useState<string | null>(null)
  
  // Branding and profile for email preview
  const [branding, setBranding] = useState<BrandingContext>(defaultBranding)
  const [profile, setProfile] = useState<ProfileContext>(defaultProfile)
  const [sendingTest, setSendingTest] = useState(false)

  const isEditMode = !!scheduleId

  // Load branding and profile data for email preview
  useEffect(() => {
    async function loadContextData() {
      try {
        // Fetch branding
        const brandingRes = await fetch("/api/proxy/v1/account/branding", {
          credentials: "include"
        })
        if (brandingRes.ok) {
          const brandingData = await brandingRes.json()
          setBranding({
            primaryColor: brandingData.primary_color || defaultBranding.primaryColor,
            accentColor: brandingData.secondary_color || defaultBranding.accentColor,
            emailLogoUrl: brandingData.email_logo_url || null,
            displayName: brandingData.name || null,
          })
        }

        // Fetch profile
        const profileRes = await fetch("/api/proxy/v1/users/me", {
          credentials: "include"
        })
        if (profileRes.ok) {
          const profileData = await profileRes.json()
          const fullName = [profileData.first_name, profileData.last_name]
            .filter(Boolean)
            .join(" ") || "Your Name"
          setProfile({
            name: fullName,
            jobTitle: profileData.job_title || null,
            avatarUrl: profileData.avatar_url || null,
            phone: profileData.phone || null,
            email: profileData.email || "you@example.com",
          })
        }
      } catch (err) {
        console.error("Failed to load branding/profile:", err)
      }
    }

    loadContextData()
  }, [])

  // Load existing schedule for edit mode
  useEffect(() => {
    if (!scheduleId) return

    async function loadSchedule() {
      try {
        const res = await fetch(`/api/proxy/v1/schedules/${scheduleId}`, {
          credentials: "include"
        })

        if (!res.ok) {
          throw new Error("Failed to load schedule")
        }

        const data = await res.json()
        
        // Map API response to UI state
        const audienceFilter = mapFiltersToAudienceFilter(data.filters)
        const audienceFilterName = audienceFilter && audienceFilter !== "all"
          ? AUDIENCE_FILTERS.find(f => f.id === audienceFilter)?.name || null
          : null

        setState({
          name: data.name || "",
          reportType: data.report_type || "market_snapshot",
          lookbackDays: data.lookback_days || 30,
          areaType: data.city ? "city" : "zip",
          city: data.city || null,
          zipCodes: data.zip_codes || [],
          audienceFilter,
          audienceFilterName,
          cadence: data.cadence || "weekly",
          weeklyDow: data.weekly_dow ?? 1,
          monthlyDom: data.monthly_dom ?? 1,
          sendHour: data.send_hour ?? 9,
          sendMinute: data.send_minute ?? 0,
          timezone: data.timezone || "America/Los_Angeles",
          recipients: mapApiRecipientsToState(data.recipients || []),
          includeAttachment: data.include_attachment || false,
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load schedule")
      } finally {
        setLoading(false)
      }
    }

    loadSchedule()
  }, [scheduleId])

  const updateState = useCallback((updates: Partial<ScheduleBuilderState>) => {
    setState((prev) => ({ ...prev, ...updates }))
  }, [])

  const isValid =
    state.name.trim().length > 0 &&
    (state.areaType === "city" ? state.city !== null : state.zipCodes.length > 0) &&
    state.recipients.length > 0

  const handleSave = async () => {
    if (!isValid) return

    setSaving(true)
    setError(null)

    try {
      // Build filters from audience filter selection
      const filters = state.audienceFilter && state.audienceFilter !== "all"
        ? AUDIENCE_FILTER_PRESETS[state.audienceFilter]
        : null

      // Map UI state to API payload
      const payload: ScheduleApiPayload = {
        name: state.name,
        report_type: state.reportType,
        city: state.areaType === "city" ? state.city : null,
        zip_codes: state.areaType === "zip" ? state.zipCodes : null,
        lookback_days: state.lookbackDays,
        cadence: state.cadence,
        weekly_dow: state.cadence === "weekly" ? state.weeklyDow : null,
        monthly_dom: state.cadence === "monthly" ? state.monthlyDom : null,
        send_hour: state.sendHour,
        send_minute: state.sendMinute,
        timezone: state.timezone,
        recipients: mapRecipientsToApi(state.recipients),
        include_attachment: state.includeAttachment,
        active: true,
        filters: filters,
      }

      const url = isEditMode 
        ? `/api/proxy/v1/schedules/${scheduleId}`
        : "/api/proxy/v1/schedules"
      
      const method = isEditMode ? "PATCH" : "POST"

      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to ${isEditMode ? "update" : "create"} schedule`)
      }

      router.push("/app/schedules")
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred")
    } finally {
      setSaving(false)
    }
  }

  const handleSendTest = async () => {
    setSendingTest(true)
    try {
      // TODO: Implement test email endpoint
      // For now, just show a brief loading state
      await new Promise(resolve => setTimeout(resolve, 1500))
      // Could call: POST /api/proxy/v1/schedules/test-email with current state
      alert("Test email feature coming soon!")
    } catch (err) {
      console.error("Failed to send test email:", err)
    } finally {
      setSendingTest(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-violet-600 mx-auto mb-4" />
          <p className="text-muted-foreground">Loading schedule...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-muted/30">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b bg-background">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link 
            href="/app/schedules" 
            className="flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Schedules
          </Link>
          <div className="flex items-center gap-3">
            <Button variant="ghost" onClick={() => router.push("/app/schedules")}>
              Cancel
            </Button>
            <Button 
              onClick={handleSave} 
              disabled={!isValid || saving} 
              className="bg-violet-600 hover:bg-violet-700 text-white"
            >
              {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isEditMode ? "Update Schedule" : "Save Schedule"}
            </Button>
          </div>
        </div>
      </header>

      {/* Error Display */}
      {error && (
        <div className="mx-auto max-w-7xl px-6 pt-4">
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
            {error}
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="grid grid-cols-[1fr,420px] gap-8">
          <ConfigurationPanel
            state={state}
            updateState={updateState}
            expandedSection={expandedSection}
            setExpandedSection={setExpandedSection}
          />
          <EmailPreviewPanel 
            state={state} 
            branding={branding} 
            profile={profile}
            onSendTest={handleSendTest}
            sendingTest={sendingTest}
          />
        </div>
      </main>
    </div>
  )
}

// Helper: Map UI recipients to API format
function mapRecipientsToApi(recipients: Recipient[]): ScheduleApiPayload["recipients"] {
  return recipients.map((r) => {
    if (r.type === "manual_email") {
      return { type: "manual_email", email: r.email }
    } else if (r.type === "group") {
      return { type: "group", id: r.id }
    } else {
      return { type: "contact", id: r.id }
    }
  })
}

// Helper: Map API recipients to UI state
function mapApiRecipientsToState(apiRecipients: any[]): Recipient[] {
  return apiRecipients.map((r) => {
    if (typeof r === "string") {
      // Legacy email string
      return { type: "manual_email", email: r }
    }
    if (r.type === "manual_email") {
      return { type: "manual_email", email: r.email }
    }
    if (r.type === "group") {
      return { 
        type: "group", 
        id: r.id, 
        name: r.name || "Group", 
        memberCount: r.member_count || 0 
      }
    }
    // contact
    return { 
      type: "contact", 
      id: r.id, 
      name: r.name || "Contact", 
      email: r.email || "" 
    }
  })
}

// Helper: Map API filters back to audience filter selection
function mapFiltersToAudienceFilter(filters: any): ScheduleBuilderState["audienceFilter"] {
  if (!filters || !filters.preset_display_name) return null

  const displayName = filters.preset_display_name.toLowerCase()
  
  if (displayName.includes("first-time") || displayName.includes("first time")) return "first_time"
  if (displayName.includes("luxury")) return "luxury"
  if (displayName.includes("family") || displayName.includes("families")) return "families"
  if (displayName.includes("condo")) return "condo"
  if (displayName.includes("investor")) return "investors"
  
  return "all"
}

// Re-export types for convenience
export type { ScheduleBuilderState, ScheduleApiPayload, Recipient, BrandingContext, ProfileContext }

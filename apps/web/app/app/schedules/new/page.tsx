"use client"

import { useState } from "react"
import dynamic from "next/dynamic"

const ScheduleWizard = dynamic(() => import("@repo/ui").then((m) => m.ScheduleWizard), { ssr: false })

export default function NewSchedulePage() {
  const [err, setErr] = useState<string | null>(null)

  async function onSubmit(payload: any) {
    setErr(null)

    try {
      // Map frontend state to API format
      // Detect user's timezone for accurate scheduling
      const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC"
      
      // Build filters with preset_display_name for PDF headers
      const filters = payload.filters || {};
      if (payload.preset_key) {
        // Map preset_key to display name for PDF headers
        const presetNames: Record<string, string> = {
          "first_time_buyer": "First-Time Buyer",
          "condo_watch": "Condo Watch",
          "luxury_showcase": "Luxury Showcase",
          "family_homes": "Family Homes",
          "investor_deals": "Investor Deals",
        };
        filters.preset_display_name = presetNames[payload.preset_key] || null;
      }
      
      const apiPayload = {
        name: payload.name,
        report_type: payload.report_type,
        city: payload.area_mode === 'city' ? payload.city : null,
        zip_codes: payload.area_mode === 'zips' ? payload.zips : null,
        lookback_days: payload.lookback_days,
        cadence: payload.cadence,
        weekly_dow: payload.cadence === 'weekly' ? weekdayToNumber(payload.weekday) : null,
        monthly_dom: payload.cadence === 'monthly' ? payload.monthly_day : null,
        send_hour: parseInt(payload.time.split(':')[0], 10),
        send_minute: parseInt(payload.time.split(':')[1], 10),
        timezone: userTimezone,  // Use detected timezone for correct scheduling
        // Use typedRecipients if available, otherwise fall back to plain recipients
        recipients: payload.typedRecipients || payload.recipients,
        include_attachment: false,
        active: true,
        // NEW: Include filters for Smart Presets (with preset_display_name for PDF headers)
        filters: filters,
      }

      const res = await fetch(`/api/proxy/v1/schedules`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(apiPayload),
      })

      if (!res.ok) {
        const text = await res.text().catch(() => "")
        setErr(text || "Create failed")
        return
      }

      window.location.href = "/app/schedules"
    } catch (error: any) {
      setErr(error.message || "Unknown error")
    }
  }

  // Helper to convert weekday string to number (0=Sunday, 6=Saturday)
  function weekdayToNumber(weekday: string): number {
    const map: Record<string, number> = {
      'sunday': 0,
      'monday': 1,
      'tuesday': 2,
      'wednesday': 3,
      'thursday': 4,
      'friday': 5,
      'saturday': 6,
    }
    return map[weekday.toLowerCase()] ?? 1
  }

  function onCancel() {
    window.history.back()
  }

  return (
    <div className="space-y-6">
      <ScheduleWizard onSubmit={onSubmit} onCancel={onCancel} />
      {err && <p className="text-sm text-red-400">{err}</p>}
    </div>
  )
}


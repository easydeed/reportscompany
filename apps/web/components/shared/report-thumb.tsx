"use client"

// A market report's first page at a fixed pixel width — the one component
// every report image in the app and on the landing page goes through.
//
// The page is the worker's own render (`GET /v1/report-preview/{kind}`, the
// template production sends, on canned sample data), framed at its natural
// letter width and SCALED with a transform — never reflowed (Design
// constraint #2). It replaced `SharedPDFPreview`, a React redraw of the report
// that had kept the page seven kinds left on 2026-10-07/08.
//
// `sandbox` is empty on purpose: no scripts, no same-origin. The route also
// forbids scripts in its CSP; this does not rely on that.

import type { PreviewReportType } from "@/components/shared/email-preview/sample-data"
import { getApiBase } from "@/lib/get-api-base"

/** Letter at 96 dpi — the width the worker's page is laid out for. */
const NATURAL_W = 816
const NATURAL_H = 1056

export interface ReportThumbProps {
  reportType: PreviewReportType
  width: number
  primaryColor?: string | null
  accentColor?: string | null
  /** Shown in the page's heading. Empty falls back to the sample's city. */
  areaName?: string | null
  lookbackDays?: number
  tilt?: number
  shadow?: "page" | "thumb" | "none"
  className?: string
}

// The route's own two checks, so a value it would refuse is left off instead
// of framing a 422: a half-typed city falls back to the sample's for a moment.
const HEX = /^#[0-9a-fA-F]{6}$/
const CITY = /^(?:\p{L}+(?:[ .'\-]+\p{L}+)*\.?|\d{5}(?:, ?\d{5}){0,4})$/u

export function reportPreviewUrl({
  reportType,
  primaryColor,
  accentColor,
  areaName,
  lookbackDays,
}: Pick<ReportThumbProps, "reportType" | "primaryColor" | "accentColor" | "areaName" | "lookbackDays">) {
  const q = new URLSearchParams()
  // The route rejects anything that is not #rrggbb; a short or named colour
  // from an account falls back to the default rather than breaking the page.
  if (primaryColor && HEX.test(primaryColor)) q.set("primary", primaryColor)
  if (accentColor && HEX.test(accentColor)) q.set("accent", accentColor)
  const city = areaName?.trim() ?? ""
  if (city.length <= 40 && CITY.test(city)) q.set("city", city)
  if (lookbackDays && [7, 14, 30, 60, 90].includes(lookbackDays)) q.set("days", String(lookbackDays))
  const qs = q.toString()
  return `${getApiBase()}/v1/report-preview/${reportType}${qs ? `?${qs}` : ""}`
}

export function ReportThumb({
  width,
  tilt = 0,
  shadow = "page",
  className,
  ...page
}: ReportThumbProps) {
  const s = width / NATURAL_W
  const h = Math.round(NATURAL_H * s)
  const box =
    shadow === "page"
      ? "0 30px 60px -20px rgba(15,23,42,0.32), 0 0 0 1px rgba(15,23,42,0.06)"
      : shadow === "thumb"
        ? "0 0 0 1px rgba(15,23,42,0.08), 0 6px 14px -8px rgba(15,23,42,0.4)"
        : "none"
  return (
    <div
      className={className}
      style={{
        width,
        height: h,
        overflow: "hidden",
        borderRadius: shadow === "thumb" ? 3 : 6,
        background: "#fff",
        boxShadow: box,
        transform: tilt ? `rotate(${tilt}deg)` : undefined,
      }}
      aria-hidden
    >
      <iframe
        src={reportPreviewUrl(page)}
        title=""
        sandbox=""
        loading="lazy"
        tabIndex={-1}
        scrolling="no"
        style={{
          width: NATURAL_W,
          height: NATURAL_H,
          border: 0,
          transform: `scale(${s})`,
          transformOrigin: "0 0",
          pointerEvents: "none",
        }}
      />
    </div>
  )
}

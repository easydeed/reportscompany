"use client"

// A market-report page at a fixed pixel width. Design constraint #2: the page
// is rendered at its natural size and SCALED with a transform — never reflowed.
// SharedPDFPreview lays out at 480px wide with an 8.5/11 aspect; we pin it to
// 480 and scale to `width`.

import { SharedPDFPreview, type SharedPDFPreviewProps } from "@/components/shared/pdf-preview"

const NATURAL_W = 480
const NATURAL_H = NATURAL_W * (11 / 8.5)

export function ReportThumb({ width, tilt = 0, shadow = "page", className, ...preview }: Omit<SharedPDFPreviewProps, "scale"> & { width: number; tilt?: number; shadow?: "page" | "thumb" | "none"; className?: string }) {
  const s = width / NATURAL_W
  const h = Math.round(NATURAL_H * s)
  const box = shadow === "page"
    ? "0 30px 60px -20px rgba(15,23,42,0.32), 0 0 0 1px rgba(15,23,42,0.06)"
    : shadow === "thumb" ? "0 0 0 1px rgba(15,23,42,0.08), 0 6px 14px -8px rgba(15,23,42,0.4)" : "none"
  return (
    <div className={className} style={{ width, height: h, overflow: "hidden", borderRadius: shadow === "thumb" ? 3 : 6, background: "#fff", boxShadow: box, transform: tilt ? `rotate(${tilt}deg)` : undefined }}>
      <div style={{ width: NATURAL_W, transform: `scale(${s})`, transformOrigin: "0 0" }} className="[&_.shadow-lg]:shadow-none [&_.border-stone-300]:border-0">
        <SharedPDFPreview {...preview} />
      </div>
    </div>
  )
}

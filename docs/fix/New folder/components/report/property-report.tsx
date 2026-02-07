"use client"

import { useState } from "react"
import { themes, type ThemeKey } from "@/lib/themes"
import { CoverPage } from "./cover-page"
import { TocPage } from "./toc-page"
import { AerialPage } from "./aerial-page"
import { DetailsPage } from "./details-page"
import { AnalysisPage } from "./analysis-page"
import { ComparablesPage } from "./comparables-page"
import { RangePage } from "./range-page"

export function PropertyReport() {
  const [activeTheme, setActiveTheme] = useState<ThemeKey>("bold")
  const theme = themes[activeTheme]

  const themeColors: Record<ThemeKey, { bg: string; text: string; activeBg: string; activeText: string }> = {
    bold: { bg: "#f3f4f6", text: "#0F1629", activeBg: "#0F1629", activeText: "#C9A227" },
    classic: { bg: "#f3f4f6", text: "#1B365D", activeBg: "#1B365D", activeText: "#FFFFFF" },
    elegant: { bg: "#f3f4f6", text: "#1A1A1A", activeBg: "#1A1A1A", activeText: "#B8977E" },
    modern: { bg: "#f3f4f6", text: "#1A1F36", activeBg: "#FF6B5B", activeText: "#FFFFFF" },
    teal: { bg: "#f3f4f6", text: "#18235C", activeBg: "#18235C", activeText: "#34D1C3" },
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: "#E5E7EB" }}>
      {/* Theme Switcher */}
      <div
        className="sticky top-0 flex items-center justify-center gap-2"
        style={{
          padding: "16px 20px",
          backgroundColor: "rgba(255,255,255,0.95)",
          backdropFilter: "blur(8px)",
          borderBottom: "1px solid #E5E7EB",
          zIndex: 50,
        }}
      >
        <span
          style={{
            fontSize: "13px",
            fontWeight: 600,
            color: "#374151",
            marginRight: "8px",
          }}
        >
          Theme:
        </span>
        {(Object.keys(themes) as ThemeKey[]).map((key) => {
          const isActive = key === activeTheme
          const colors = themeColors[key]
          return (
            <button
              key={key}
              type="button"
              onClick={() => setActiveTheme(key)}
              style={{
                padding: "8px 20px",
                borderRadius: "6px",
                border: isActive ? "none" : "1px solid #D1D5DB",
                backgroundColor: isActive ? colors.activeBg : colors.bg,
                color: isActive ? colors.activeText : colors.text,
                fontSize: "13px",
                fontWeight: isActive ? 700 : 500,
                cursor: "pointer",
                transition: "all 150ms ease",
                letterSpacing: "0.5px",
              }}
            >
              {themes[key].label}
            </button>
          )
        })}
      </div>

      {/* Pages */}
      <div className="flex flex-col items-center gap-8 py-8">
        <CoverPage theme={theme} />
        <TocPage theme={theme} />
        <AerialPage theme={theme} />
        <DetailsPage theme={theme} />
        <AnalysisPage theme={theme} />
        <ComparablesPage theme={theme} />
        <RangePage theme={theme} />
      </div>
    </div>
  )
}

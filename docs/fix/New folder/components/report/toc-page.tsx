"use client"

import type { Theme } from "@/lib/themes"
import { tocItems } from "@/lib/report-data"
import { PageWrapper, PageHeader } from "./page-wrapper"

export function TocPage({ theme }: { theme: Theme }) {
  return (
    <PageWrapper theme={theme}>
      <div className="flex h-full">
        {/* Sidebar accent */}
        <div
          style={{
            width: theme.key === "modern" ? "0" : "3px",
            backgroundColor: theme.key === "bold" ? theme.colors.accent : theme.key === "teal" ? theme.colors.primary : theme.colors.accent,
            marginRight: theme.key === "modern" ? "0" : "24px",
            opacity: 0.4,
            borderRadius: "2px",
          }}
        />

        <div className="flex-1 flex flex-col">
          <PageHeader theme={theme} title="Contents" subtitle="Property Report Overview" />

          <div className="flex flex-col" style={{ gap: theme.key === "modern" ? "10px" : "0" }}>
            {tocItems.map((item, i) => (
              <TocItem key={item.num} theme={theme} item={item} isLast={i === tocItems.length - 1} />
            ))}
          </div>
        </div>
      </div>
    </PageWrapper>
  )
}

function TocItem({
  theme,
  item,
  isLast,
}: {
  theme: Theme
  item: { num: number; title: string; subtitle: string }
  isLast: boolean
}) {
  if (theme.key === "bold") {
    return (
      <div
        className="flex items-center gap-4"
        style={{
          padding: "14px 0",
          borderBottom: isLast ? "none" : `2px solid ${theme.colors.primary}`,
        }}
      >
        <div
          style={{
            fontFamily: theme.fonts.display,
            fontSize: "32px",
            fontWeight: 700,
            color: theme.colors.accent,
            minWidth: "44px",
            lineHeight: 1,
          }}
        >
          {String(item.num).padStart(2, "0")}
        </div>
        <div className="flex-1">
          <div
            style={{
              fontFamily: theme.fonts.display,
              fontSize: "14px",
              fontWeight: 700,
              color: theme.colors.primary,
              textTransform: "uppercase",
              letterSpacing: "2px",
            }}
          >
            {item.title}
          </div>
          <div
            style={{
              fontFamily: theme.fonts.body,
              fontSize: "10px",
              color: theme.colors.muted,
              marginTop: "2px",
            }}
          >
            {item.subtitle}
          </div>
        </div>
      </div>
    )
  }

  if (theme.key === "classic") {
    return (
      <div
        className="flex items-baseline gap-4"
        style={{
          padding: "14px 0",
          borderBottom: isLast ? "none" : `1px dotted ${theme.colors.border}`,
        }}
      >
        <div
          style={{
            fontFamily: theme.fonts.display,
            fontSize: "36px",
            fontWeight: 400,
            color: theme.colors.accent,
            minWidth: "44px",
            lineHeight: 1,
            opacity: 0.7,
          }}
        >
          {item.num}
        </div>
        <div className="flex-1">
          <div
            style={{
              fontFamily: theme.fonts.display,
              fontSize: "15px",
              fontWeight: 600,
              color: theme.colors.primary,
            }}
          >
            {item.title}
          </div>
          <div
            style={{
              fontFamily: theme.fonts.body,
              fontSize: "10px",
              color: theme.colors.muted,
              marginTop: "2px",
            }}
          >
            {item.subtitle}
          </div>
        </div>
      </div>
    )
  }

  if (theme.key === "elegant") {
    return (
      <div
        className="flex items-baseline gap-5"
        style={{
          padding: "16px 0",
          borderBottom: isLast ? "none" : `1px solid ${theme.colors.border}`,
        }}
      >
        <div
          style={{
            fontFamily: theme.fonts.display,
            fontSize: "40px",
            fontWeight: 400,
            fontStyle: "italic",
            color: theme.colors.accent,
            minWidth: "48px",
            lineHeight: 1,
            opacity: 0.6,
          }}
        >
          {item.num}
        </div>
        <div className="flex-1">
          <div
            style={{
              fontFamily: theme.fonts.display,
              fontSize: "16px",
              fontWeight: 500,
              fontStyle: "italic",
              color: theme.colors.primary,
            }}
          >
            {item.title}
          </div>
          <div
            style={{
              fontFamily: theme.fonts.body,
              fontSize: "10px",
              color: theme.colors.muted,
              marginTop: "3px",
              fontWeight: 400,
            }}
          >
            {item.subtitle}
          </div>
        </div>
      </div>
    )
  }

  if (theme.key === "modern") {
    return (
      <div
        className="flex items-center gap-4"
        style={{
          padding: "12px 16px",
          backgroundColor: "#F8FAFC",
          borderRadius: theme.radiusLg,
        }}
      >
        <div
          className="flex items-center justify-center"
          style={{
            width: "36px",
            height: "36px",
            borderRadius: "50%",
            backgroundColor: theme.colors.primary,
            color: "white",
            fontFamily: theme.fonts.display,
            fontSize: "14px",
            fontWeight: 700,
            flexShrink: 0,
          }}
        >
          {item.num}
        </div>
        <div className="flex-1">
          <div
            style={{
              fontFamily: theme.fonts.display,
              fontSize: "14px",
              fontWeight: 600,
              color: theme.colors.accent,
            }}
          >
            {item.title}
          </div>
          <div
            style={{
              fontFamily: theme.fonts.body,
              fontSize: "10px",
              color: theme.colors.muted,
              marginTop: "1px",
            }}
          >
            {item.subtitle}
          </div>
        </div>
      </div>
    )
  }

  // Teal
  return (
    <div
      className="flex items-center gap-4"
      style={{
        padding: "12px 0",
        borderBottom: isLast ? "none" : `2px solid ${theme.colors.border}`,
      }}
    >
      <div
        className="flex items-center justify-center"
        style={{
          width: "36px",
          height: "36px",
          borderRadius: theme.radius,
          backgroundColor: theme.colors.primary,
          color: theme.colors.accent,
          fontFamily: theme.fonts.display,
          fontSize: "14px",
          fontWeight: 900,
          flexShrink: 0,
        }}
      >
        {String(item.num).padStart(2, "0")}
      </div>
      <div className="flex-1">
        <div
          style={{
            fontFamily: theme.fonts.display,
            fontSize: "14px",
            fontWeight: 800,
            color: theme.colors.accent,
            textTransform: "uppercase",
            letterSpacing: "1px",
          }}
        >
          {item.title}
        </div>
        <div
          style={{
            fontFamily: theme.fonts.body,
            fontSize: "10px",
            color: theme.colors.muted,
            marginTop: "1px",
          }}
        >
          {item.subtitle}
        </div>
      </div>
    </div>
  )
}

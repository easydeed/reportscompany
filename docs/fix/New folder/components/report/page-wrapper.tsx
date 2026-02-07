"use client"

import React from "react"

import type { Theme } from "@/lib/themes"
import { agent } from "@/lib/report-data"

export function PageWrapper({
  theme,
  children,
  noFooter = false,
  noPadding = false,
}: {
  theme: Theme
  children: React.ReactNode
  noFooter?: boolean
  noPadding?: boolean
}) {
  return (
    <div
      className="relative overflow-hidden bg-white"
      style={{
        width: "8.5in",
        height: "11in",
        fontFamily: theme.fonts.body,
        boxShadow: "0 4px 24px rgba(0,0,0,0.12)",
      }}
    >
      <div
        className="flex flex-col"
        style={{
          height: "100%",
          padding: noPadding ? 0 : "0.5in 0.6in",
        }}
      >
        <div className="flex-1 overflow-hidden">{children}</div>
        {!noFooter && <PageFooter theme={theme} />}
      </div>
    </div>
  )
}

export function PageFooter({ theme }: { theme: Theme }) {
  return (
    <div
      className="flex items-center justify-between"
      style={{
        borderTop: `1px solid ${theme.colors.border}`,
        paddingTop: "8px",
        marginTop: "12px",
        fontFamily: theme.fonts.body,
        fontSize: "9px",
        color: theme.colors.muted,
      }}
    >
      <div className="flex items-center gap-2">
        <img
          src={agent.photo || "/placeholder.svg"}
          alt={agent.name}
          className="object-cover"
          style={{
            width: "22px",
            height: "22px",
            borderRadius: "50%",
          }}
        />
        <span style={{ fontWeight: 600, color: theme.colors.primary }}>
          {agent.name}
        </span>
        <span>{agent.phone}</span>
      </div>
      <div
        style={{
          fontWeight: 700,
          color: theme.colors.primary,
          fontFamily: theme.fonts.display,
          fontSize: "10px",
          letterSpacing: theme.key === "bold" || theme.key === "teal" ? "1px" : "0.5px",
          textTransform: theme.key === "bold" || theme.key === "teal" ? "uppercase" : undefined,
        }}
      >
        {agent.company}
      </div>
    </div>
  )
}

export function PageHeader({
  theme,
  title,
  subtitle,
}: {
  theme: Theme
  title: string
  subtitle?: string
}) {
  const isItalic = theme.key === "elegant"
  return (
    <div style={{ marginBottom: "20px" }}>
      <h2
        style={{
          fontFamily: theme.fonts.display,
          fontSize: "26px",
          fontWeight: 700,
          color: theme.colors.primary,
          margin: 0,
          lineHeight: 1.2,
          fontStyle: isItalic ? "italic" : "normal",
          textTransform: theme.key === "bold" || theme.key === "teal" ? "uppercase" : undefined,
          letterSpacing: theme.key === "bold" ? "2px" : theme.key === "teal" ? "1px" : "0",
        }}
      >
        {title}
      </h2>
      {subtitle && (
        <p
          style={{
            fontFamily: theme.fonts.body,
            fontSize: "11px",
            color: theme.colors.muted,
            margin: "4px 0 0",
            fontWeight: 400,
          }}
        >
          {subtitle}
        </p>
      )}
      <div
        style={{
          width: theme.key === "modern" ? "60px" : "40px",
          height: theme.key === "bold" ? "4px" : "3px",
          backgroundColor: theme.key === "modern" ? theme.colors.primary : theme.colors.accent,
          marginTop: "10px",
          borderRadius: theme.key === "modern" ? "4px" : theme.key === "elegant" ? "0" : "2px",
        }}
      />
    </div>
  )
}

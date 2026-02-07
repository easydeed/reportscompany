"use client"

import type { Theme } from "@/lib/themes"
import { property, agent } from "@/lib/report-data"

export function CoverPage({ theme }: { theme: Theme }) {
  return (
    <div
      className="relative overflow-hidden"
      style={{
        width: "8.5in",
        height: "11in",
        fontFamily: theme.fonts.body,
        boxShadow: "0 4px 24px rgba(0,0,0,0.12)",
      }}
    >
      {/* Top accent bar */}
      <div
        className="absolute top-0 left-0 right-0"
        style={{
          height: theme.key === "bold" ? "6px" : "4px",
          backgroundColor: theme.key === "modern" ? theme.colors.primary : theme.colors.accent,
          zIndex: 10,
        }}
      />

      {/* Hero Image with overlay */}
      <div className="absolute inset-0">
        <img
          src="/images/cover-hero.jpg"
          alt="Property exterior"
          className="w-full h-full object-cover"
        />
        <div
          className="absolute inset-0"
          style={{
            background: "linear-gradient(to bottom, rgba(0,0,0,0.2) 0%, rgba(0,0,0,0.55) 60%, rgba(0,0,0,0.8) 100%)",
          }}
        />
      </div>

      {/* Theme-specific decorative elements */}
      {theme.key === "bold" && (
        <div
          className="absolute bottom-0 right-0"
          style={{
            width: 0,
            height: 0,
            borderLeft: "120px solid transparent",
            borderBottom: `120px solid ${theme.colors.accent}`,
            zIndex: 5,
            opacity: 0.7,
          }}
        />
      )}

      {theme.key === "elegant" && (
        <>
          {/* Top-left corner flourish */}
          <div className="absolute" style={{ top: "30px", left: "30px", zIndex: 10 }}>
            <div style={{ width: "50px", height: "2px", backgroundColor: theme.colors.accent, opacity: 0.6 }} />
            <div style={{ width: "2px", height: "50px", backgroundColor: theme.colors.accent, opacity: 0.6 }} />
          </div>
          {/* Bottom-right corner flourish */}
          <div className="absolute" style={{ bottom: "100px", right: "30px", zIndex: 10 }}>
            <div style={{ width: "50px", height: "2px", backgroundColor: theme.colors.accent, opacity: 0.6, marginLeft: "auto" }} />
            <div style={{ width: "2px", height: "50px", backgroundColor: theme.colors.accent, opacity: 0.6, marginLeft: "auto" }} />
          </div>
        </>
      )}

      {theme.key === "modern" && (
        <>
          <div
            className="absolute"
            style={{
              top: "60px",
              right: "40px",
              width: "80px",
              height: "80px",
              borderRadius: "50%",
              backgroundColor: theme.colors.primary,
              opacity: 0.15,
              zIndex: 5,
            }}
          />
          <div
            className="absolute"
            style={{
              top: "180px",
              right: "100px",
              width: "40px",
              height: "40px",
              borderRadius: "50%",
              backgroundColor: theme.colors.primary,
              opacity: 0.1,
              zIndex: 5,
            }}
          />
          <div
            className="absolute"
            style={{
              top: "120px",
              right: "20px",
              width: "24px",
              height: "24px",
              borderRadius: "50%",
              backgroundColor: theme.colors.primary,
              opacity: 0.2,
              zIndex: 5,
            }}
          />
        </>
      )}

      {theme.key === "teal" && (
        <>
          {/* Diagonal stripe */}
          <div
            className="absolute"
            style={{
              top: "40px",
              right: "-20px",
              width: "200px",
              height: "6px",
              backgroundColor: theme.colors.primary,
              transform: "rotate(-30deg)",
              opacity: 0.6,
              zIndex: 5,
            }}
          />
          {/* Mini vertical bars */}
          <div className="absolute flex gap-1" style={{ top: "50px", left: "30px", zIndex: 10 }}>
            {[16, 24, 12].map((h, i) => (
              <div
                key={i}
                style={{
                  width: "3px",
                  height: `${h}px`,
                  backgroundColor: theme.colors.primary,
                  opacity: 0.7,
                }}
              />
            ))}
          </div>
        </>
      )}

      {/* Top bar: Company Logo + Badge */}
      <div
        className="relative flex items-center justify-between"
        style={{
          padding: "24px 40px 0",
          zIndex: 10,
        }}
      >
        <div
          style={{
            fontFamily: theme.fonts.body,
            fontSize: "10px",
            color: "rgba(255,255,255,0.7)",
            letterSpacing: "2px",
            textTransform: "uppercase",
            fontWeight: 500,
            padding: "6px 14px",
            border: "1px solid rgba(255,255,255,0.3)",
            borderRadius: theme.radius,
          }}
        >
          Property Report
        </div>
        <div
          style={{
            fontFamily: theme.fonts.display,
            fontSize: "14px",
            color: "white",
            fontWeight: 700,
            letterSpacing: theme.key === "bold" || theme.key === "teal" ? "2px" : "1px",
            textTransform: theme.key === "bold" || theme.key === "teal" ? "uppercase" : undefined,
          }}
        >
          {agent.company}
        </div>
      </div>

      {/* Center-bottom content */}
      <div
        className="absolute flex flex-col justify-end"
        style={{
          bottom: "90px",
          left: "40px",
          right: "40px",
          zIndex: 10,
        }}
      >
        <div
          style={{
            fontFamily: theme.fonts.body,
            fontSize: "11px",
            color: theme.key === "modern" ? theme.colors.primary : theme.colors.accent,
            letterSpacing: "3px",
            textTransform: "uppercase",
            fontWeight: 600,
            marginBottom: "8px",
          }}
        >
          {property.type}
        </div>
        <h1
          style={{
            fontFamily: theme.fonts.display,
            fontSize: theme.key === "elegant" ? "44px" : "42px",
            fontWeight: theme.key === "elegant" ? 500 : 700,
            fontStyle: theme.key === "elegant" ? "italic" : "normal",
            color: "white",
            lineHeight: 1.1,
            margin: 0,
            letterSpacing: theme.key === "bold" ? "2px" : "0",
            textTransform: theme.key === "bold" ? "uppercase" : undefined,
          }}
        >
          {property.address}
        </h1>
        <p
          style={{
            fontFamily: theme.fonts.body,
            fontSize: "16px",
            color: "rgba(255,255,255,0.8)",
            margin: "6px 0 0",
            fontWeight: 400,
            letterSpacing: "1px",
          }}
        >
          {property.city}, {property.state} {property.zip}
        </p>

        {/* Accent line */}
        <div
          style={{
            width: "50px",
            height: theme.key === "bold" ? "4px" : "3px",
            backgroundColor: theme.key === "modern" ? theme.colors.primary : theme.colors.accent,
            margin: "16px 0",
            borderRadius: theme.key === "modern" ? "4px" : "0",
          }}
        />

        {/* Stats row */}
        <div className="flex items-center gap-6">
          {[
            { value: property.beds, label: "Beds" },
            { value: property.baths, label: "Baths" },
            { value: property.sqft.toLocaleString(), label: "Sq Ft" },
            { value: property.yearBuilt, label: "Built" },
          ].map((stat, i) => (
            <div key={i} className="flex items-baseline gap-1.5">
              <span
                style={{
                  fontFamily: theme.fonts.display,
                  fontSize: "28px",
                  fontWeight: 700,
                  color: "white",
                  lineHeight: 1,
                  fontStyle: theme.key === "elegant" ? "italic" : "normal",
                }}
              >
                {stat.value}
              </span>
              <span
                style={{
                  fontFamily: theme.fonts.body,
                  fontSize: "10px",
                  color: "rgba(255,255,255,0.6)",
                  textTransform: "uppercase",
                  letterSpacing: "1px",
                }}
              >
                {stat.label}
              </span>
              {i < 3 && (
                <span
                  style={{
                    color: "rgba(255,255,255,0.3)",
                    fontSize: "20px",
                    fontWeight: 300,
                    marginLeft: "8px",
                  }}
                >
                  |
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Bottom agent bar */}
      <div
        className="absolute bottom-0 left-0 right-0 flex items-center justify-between"
        style={{
          backgroundColor: "white",
          padding: "12px 40px",
          zIndex: 10,
        }}
      >
        <div className="flex items-center gap-3">
          <img
            src={agent.photo || "/placeholder.svg"}
            alt={agent.name}
            className="object-cover"
            style={{
              width: "44px",
              height: "44px",
              borderRadius: "50%",
              border: `2px solid ${theme.colors.accent}`,
            }}
          />
          <div>
            <div
              style={{
                fontFamily: theme.fonts.display,
                fontSize: "13px",
                fontWeight: 700,
                color: theme.colors.primary,
                letterSpacing: theme.key === "bold" ? "1px" : "0",
                textTransform: theme.key === "bold" ? "uppercase" : undefined,
                fontStyle: theme.key === "elegant" ? "italic" : "normal",
              }}
            >
              {agent.name}
            </div>
            <div
              style={{
                fontFamily: theme.fonts.body,
                fontSize: "9px",
                color: theme.colors.muted,
                marginTop: "1px",
              }}
            >
              {agent.title}
            </div>
            <div
              style={{
                fontFamily: theme.fonts.body,
                fontSize: "9px",
                color: theme.colors.muted,
              }}
            >
              {agent.phone} &middot; {agent.email}
            </div>
          </div>
        </div>
        <div
          style={{
            fontFamily: theme.fonts.display,
            fontSize: "13px",
            fontWeight: 700,
            color: theme.colors.primary,
            letterSpacing: theme.key === "bold" || theme.key === "teal" ? "2px" : "1px",
            textTransform: theme.key === "bold" || theme.key === "teal" ? "uppercase" : undefined,
          }}
        >
          {agent.company}
        </div>
      </div>
    </div>
  )
}

"use client";

/**
 * Shared pieces of the landing page, ported from Design's `Landing v4.dc.html`
 * (docs/design-claude/new_package/design_handoff_product/).
 *
 * The deck drives every mock on the page from one `primary`/`accent` pair that
 * the hero's "Your colors" swatches change, and from the city typed into the
 * hero. Both live in `LandingTheme` so the swatches recolour the phone, the
 * property card, the lead page and the closing band at once, as they do in
 * the deck.
 *
 * Report previews are `SharedPDFPreview` — the same component the report
 * wizard renders — rather than images. The deck imports its own "Report Page"
 * file at those points; the product's equivalent is the real preview, which
 * recolours with the swatches the way the deck's does.
 */
import { createContext, useContext, type CSSProperties, type ReactNode } from "react";
import { SharedPDFPreview } from "@/components/shared/pdf-preview";
import type { PreviewReportType } from "@/components/shared/email-preview/sample-data";
import { DEMO_AGENT, DEMO_MARKET } from "@/lib/demo-data";

/** Design's four "Your colors" pairs, primary then accent. */
export const LANDING_THEMES: readonly (readonly [string, string])[] = [
  ["#18235c", "#0d9488"],
  ["#4F46E5", "#D97706"],
  ["#14532D", "#CA8A04"],
  ["#7F1D1D", "#DB2777"],
];

export interface LandingThemeValue {
  primary: string;
  accent: string;
  /** What the city box holds, verbatim. */
  city: string;
  /** The city if one was typed, else the fixture's market. */
  area: string;
}

export const LandingTheme = createContext<LandingThemeValue>({
  primary: LANDING_THEMES[0][0],
  accent: LANDING_THEMES[0][1],
  city: "",
  area: DEMO_MARKET.city,
});

export function useLandingTheme() {
  return useContext(LandingTheme);
}

export const INK = "#0F172A";
export const RULE = "#ECEAE3";

/** The section frame every split block on the page shares. */
export function SplitSection({
  children,
  white = false,
  id,
  align = "center",
}: {
  children: ReactNode;
  white?: boolean;
  id?: string;
  align?: "center" | "start";
}) {
  return (
    <section
      id={id}
      className="border-t border-[#ECEAE3]"
      style={{ background: white ? "#fff" : undefined }}
    >
      <div
        className="mx-auto grid max-w-[1200px] gap-12 px-4 py-16 md:px-8 md:py-24"
        style={{
          gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 440px), 1fr))",
          alignItems: align,
        }}
      >
        {children}
      </div>
    </section>
  );
}

export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <span className="text-[13px] font-semibold uppercase tracking-[0.12em] text-[#4F46E5]">
      {children}
    </span>
  );
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <h2
      className="m-0 font-extrabold text-[#0F172A]"
      style={{
        fontSize: "clamp(34px, 4vw, 52px)",
        lineHeight: 1.02,
        letterSpacing: "-0.035em",
        textWrap: "balance",
      } as CSSProperties}
    >
      {children}
    </h2>
  );
}

export function Lede({ children }: { children: ReactNode }) {
  return (
    <p
      className="m-0 max-w-[420px] text-[19px] text-[#475569]"
      style={{ textWrap: "pretty" } as CSSProperties}
    >
      {children}
    </p>
  );
}

/** Eyebrow, title and lede — the text half of each split section. */
export function SectionCopy({
  eyebrow,
  title,
  lede,
}: {
  eyebrow: string;
  title: string;
  lede: string;
}) {
  return (
    <div className="flex flex-col gap-5">
      <Eyebrow>{eyebrow}</Eyebrow>
      <SectionTitle>{title}</SectionTitle>
      <Lede>{lede}</Lede>
    </div>
  );
}

/** The soft brand-coloured halo behind a mock. */
export function Glow() {
  const { primary } = useLandingTheme();
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute rounded-full"
      style={{
        inset: "-8% -12%",
        background: `radial-gradient(closest-side, color-mix(in oklch, ${primary} 16%, transparent), transparent 72%)`,
      }}
    />
  );
}

/** The dotted field behind the two phone mocks. */
export function DotField() {
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute"
      style={{
        inset: "-6% -10%",
        backgroundImage: "radial-gradient(#C9C6BC 1.1px, transparent 1.1px)",
        backgroundSize: "22px 22px",
        maskImage: "radial-gradient(closest-side, #000 40%, transparent 100%)",
        WebkitMaskImage: "radial-gradient(closest-side, #000 40%, transparent 100%)",
      }}
    />
  );
}

/** A phone: ink bezel, notch, white screen. */
export function PhoneFrame({ children, tilt }: { children: ReactNode; tilt: number }) {
  return (
    <div
      className="absolute left-1/2 top-5 w-[300px] rounded-[46px] bg-[#0F172A] p-3.5 sm:w-[340px]"
      style={{
        transform: `translateX(-50%) rotate(${tilt}deg)`,
        boxShadow: "0 40px 80px -24px rgba(15,23,42,0.45)",
      }}
    >
      <div className="flex h-[540px] flex-col overflow-hidden rounded-[34px] bg-white sm:h-[580px]">
        <div className="flex justify-center pb-2 pt-3">
          <div className="h-7 w-[100px] rounded-full bg-[#0F172A]" />
        </div>
        {children}
      </div>
    </div>
  );
}

/** Initials in a brand-coloured disc. */
export function AgentDisc({ size = 40 }: { size?: number }) {
  const { primary } = useLandingTheme();
  return (
    <div
      className="flex shrink-0 items-center justify-center rounded-full font-bold text-white"
      style={{ width: size, height: size, background: primary, fontSize: size * 0.32 }}
    >
      {DEMO_AGENT.initials}
    </div>
  );
}

/**
 * A report's first page at a given width. `SharedPDFPreview` lays out at
 * 480px wide on an 8.5×11 page, so it is drawn at that size and scaled — a
 * transform does not change layout, so the outer box carries the real size.
 */
export function ReportSheet({
  kind,
  width,
  className = "",
  style,
}: {
  kind: PreviewReportType;
  width: number;
  className?: string;
  style?: CSSProperties;
}) {
  const { primary, accent, area } = useLandingTheme();
  const scale = width / 480;
  return (
    <div
      className={`overflow-hidden rounded-md bg-white ${className}`}
      style={{
        width,
        height: Math.round(width * (11 / 8.5)),
        boxShadow: "0 30px 60px -20px rgba(15,23,42,0.28), 0 0 0 1px rgba(15,23,42,0.06)",
        ...style,
      }}
    >
      <div style={{ width: 480, transform: `scale(${scale})`, transformOrigin: "0 0" }}>
        <SharedPDFPreview
          primaryColor={primary}
          accentColor={accent}
          headerLogoUrl={null}
          displayName={DEMO_AGENT.brokerage}
          agentName={DEMO_AGENT.name}
          agentTitle={DEMO_AGENT.title}
          agentPhone={null}
          agentEmail="agent@example.com"
          agentPhotoUrl={null}
          reportType={kind}
          audienceLabel={null}
          areaName={area}
          lookbackDays={30}
        />
      </div>
    </div>
  );
}

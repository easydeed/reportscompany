"use client";

/**
 * Shared pieces of the landing page — Design's `Landing v13.dc.html`
 * (docs/design-claude/design_handoff_landing/).
 *
 * Unchanged from the v4 port: `LandingTheme` (one `primary`/`accent` pair and
 * the typed city drive every mock on the page), `ReportSheet` (the worker's
 * own render through `ReportThumb`), `Glow`, `DotField`, `AgentDisc`.
 *
 * New in v13:
 * - `DotGrid`    the brand-to-accent dotted field behind the hero and the
 *                property templates, drifting a little on scroll.
 * - `Drift`      scroll parallax for the two hero pages.
 * - `Steps`      the numbered 01/02/03 list every section now explains itself
 *                with (a row under the hero, a column elsewhere).
 * - `FloatCard`  the tilted white cards around the phones.
 * - `SplitSection` alternates white with a cool tint (#F5F6FB) instead of the
 *                page's old warm ground; `PhoneFrame` takes an `x`.
 *
 * Both motions stop under `prefers-reduced-motion`.
 */
import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import { ReportThumb } from "@/components/shared/report-thumb";
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
/** The cool tint every other section sits on, and the hairline between sections. */
export const TINT = "#F5F6FB";
export const SECTION_RULE = "#E6E8F0";

const FLOAT_SHADOW = "0 24px 48px -16px rgba(15,23,42,0.35), 0 0 0 1px rgba(15,23,42,0.06)";

/**
 * Runs `fn` once now and then at most once a frame while the page scrolls or
 * resizes. Returns the cleanup. Does nothing under reduced motion.
 */
function onScrollFrame(fn: () => void): () => void {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return () => {};
  let raf = 0;
  const on = () => {
    if (raf) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      fn();
    });
  };
  on();
  window.addEventListener("scroll", on, { passive: true });
  window.addEventListener("resize", on);
  return () => {
    if (raf) cancelAnimationFrame(raf);
    window.removeEventListener("scroll", on);
    window.removeEventListener("resize", on);
  };
}

/**
 * The dotted field: a `from`→`to` gradient seen through a 26px dot mask that
 * fades out around `focus`. Its parent must be `relative overflow-hidden`,
 * and anything that should sit above it must be positioned (`relative`).
 * Decorative only: 32% opacity, 1.3px dots.
 */
export function DotGrid({
  from,
  to,
  focus = "72% 45%",
}: {
  from: string;
  to: string;
  focus?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(
    () =>
      onScrollFrame(() => {
        const el = ref.current;
        const host = el?.parentElement;
        if (!el || !host) return;
        const r = host.getBoundingClientRect();
        const fromCentre = r.top + r.height / 2 - window.innerHeight / 2;
        const y = Math.round(Math.max(-90, Math.min(90, -fromCentre * 0.1)));
        el.style.transform = `translateY(${y}px)`;
      }),
    [],
  );
  const mask = `radial-gradient(circle, #000 1.3px, transparent 1.7px), radial-gradient(ellipse 85% 85% at ${focus}, #000 25%, transparent 90%)`;
  return (
    <div
      ref={ref}
      aria-hidden
      className="pointer-events-none absolute inset-x-0"
      style={{
        top: "-12%",
        bottom: "-12%",
        background: `linear-gradient(120deg, ${from}, ${to})`,
        opacity: 0.32,
        WebkitMaskImage: mask,
        WebkitMaskSize: "26px 26px, 100% 100%",
        WebkitMaskComposite: "source-in",
        maskImage: mask,
        maskSize: "26px 26px, 100% 100%",
        maskComposite: "intersect",
        willChange: "transform",
      }}
    />
  );
}

/** Moves its box by `rate` × the scroll position. Put the tilt on the child. */
export function Drift({
  rate,
  className = "",
  children,
}: {
  rate: number;
  className?: string;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(
    () =>
      onScrollFrame(() => {
        if (ref.current) {
          ref.current.style.transform = `translateY(${Math.round(window.scrollY * rate)}px)`;
        }
      }),
    [rate],
  );
  return (
    <div ref={ref} className={className} style={{ willChange: "transform" }}>
      {children}
    </div>
  );
}

/** The section frame every split block on the page shares. */
export function SplitSection({
  children,
  white = false,
  id,
  align = "center",
}: {
  children: ReactNode;
  /** White ground. Without it the section sits on the cool tint. */
  white?: boolean;
  id?: string;
  align?: "center" | "start";
}) {
  return (
    <section
      id={id}
      className="border-t border-[#E6E8F0]"
      style={{ background: white ? "#fff" : TINT }}
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

/** A numbered step: title, then one plain sentence. */
export type Step = readonly [title: string, body: string];

/**
 * 01 / 02 / 03. `row` lays the steps side by side under one rule (the strip
 * under the hero); the default stacks them, a rule above each.
 */
export function Steps({ items, row = false }: { items: readonly Step[]; row?: boolean }) {
  const num = (i: number) => (
    <span className="text-[13px] font-bold tabular-nums text-[#4F46E5]">
      {String(i + 1).padStart(2, "0")}
    </span>
  );
  const text = ([title, body]: Step) => (
    <div className="flex min-w-0 flex-col gap-0.5">
      <span className="text-[17px] font-bold text-[#0F172A]">{title}</span>
      <span className="text-[15px] text-[#475569]" style={{ textWrap: "pretty" } as CSSProperties}>
        {body}
      </span>
    </div>
  );
  if (row) {
    return (
      <ol
        className="m-0 grid list-none border-t border-[#DDE1EE] p-0"
        style={{ gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))" }}
      >
        {items.map((s, i) => (
          <li key={s[0]} className="flex items-baseline gap-3.5 pr-6 pt-[22px]">
            {num(i)}
            {text(s)}
          </li>
        ))}
      </ol>
    );
  }
  return (
    <ol className="m-0 mt-2 flex max-w-[440px] list-none flex-col p-0">
      {items.map((s, i) => (
        <li
          key={s[0]}
          className="grid items-baseline gap-2 border-t border-[#DDE1EE] py-3.5"
          style={{ gridTemplateColumns: "32px minmax(0, 1fr)" }}
        >
          {num(i)}
          {text(s)}
        </li>
      ))}
    </ol>
  );
}

/** Eyebrow, title, lede and (v13) the steps — the text half of each split section. */
export function SectionCopy({
  eyebrow,
  title,
  lede,
  steps,
}: {
  eyebrow: string;
  title: string;
  lede: string;
  steps?: readonly Step[];
}) {
  return (
    <div className="flex flex-col gap-5">
      <Eyebrow>{eyebrow}</Eyebrow>
      <SectionTitle>{title}</SectionTitle>
      <Lede>{lede}</Lede>
      {steps && <Steps items={steps} />}
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

/**
 * A phone: ink bezel, notch, white screen. `x` is where its centre sits across
 * the stage, in percent, from `sm` up — v13 moves each phone off-centre to
 * make room for the cards beside it. Below `sm` it is always centred.
 */
export function PhoneFrame({
  children,
  tilt,
  x = 50,
}: {
  children: ReactNode;
  tilt: number;
  x?: number;
}) {
  return (
    <div
      className="absolute left-1/2 top-5 z-[1] w-[300px] rounded-[46px] bg-[#0F172A] p-3.5 sm:left-[var(--phone-x)] sm:w-[340px]"
      style={
        {
          "--phone-x": `${x}%`,
          transform: `translateX(-50%) rotate(${tilt}deg)`,
          boxShadow: "0 40px 80px -24px rgba(15,23,42,0.45)",
        } as CSSProperties
      }
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

/** A tilted white card floating over a mock. Position it with `className`. */
export function FloatCard({
  tilt,
  className = "",
  children,
}: {
  tilt: number;
  className?: string;
  children: ReactNode;
}) {
  return (
    <div
      className={`absolute z-[2] rounded-[14px] bg-white ${className}`}
      style={{ transform: `rotate(${tilt}deg)`, boxShadow: FLOAT_SHADOW }}
    >
      {children}
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
 * A report's first page at a given width, in the landing theme's colours and
 * city. The city waits for typing to pause: every change is a new render on
 * the API, and the hero holds three pages and the carousel seven.
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
  const [city, setCity] = useState(area);
  useEffect(() => {
    const t = setTimeout(() => setCity(area), 500);
    return () => clearTimeout(t);
  }, [area]);
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
      <ReportThumb
        reportType={kind}
        width={width}
        shadow="none"
        primaryColor={primary}
        accentColor={accent}
        areaName={city}
        lookbackDays={30}
      />
    </div>
  );
}

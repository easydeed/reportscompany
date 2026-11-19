"use client";

/**
 * "Property reports & CMAs" — Design's `Landing v13`, the template showcase.
 *
 * Replaces v4's hand-drawn seller card with the report itself: the three
 * templates, six pages each, as a fanned stage. Tabs pick the template, the
 * numbered buttons (or a click on any page) turn the pages.
 *
 * NOTHING HERE IS DRAWN OR NAMED BY THE DECK.
 * - Templates are the wizard's `THEMES` (name, style line, accent), so this
 *   section cannot offer a template the wizard does not. The deck calls them
 *   Elegant / Modern / Bold; the product calls them Harbor / Linen / Atlas,
 *   and the product's names are the ones shown.
 * - Pages are the wizard's `REPORT_PAGES`, in document order.
 * - Page images are the renders the wizard's theme step already ships:
 *   `/previews/pages/{theme.id}/{page.id}.jpg`. Each template therefore keeps
 *   its own colours and does not follow the hero's "Your colors" swatches —
 *   that is v13's decision, not a limitation.
 * - "Six-page" and "Three templates" in the copy are counted from those lists.
 *
 * The copy says "the range of comparable sales", never "estimate" or "value":
 * the report estimates nothing (LR-025, D-383).
 *
 * The page images are 510×660. The centre page is shown at 476 wide, so it is
 * 1:1 on a standard display and soft on a 2× one — see the handoff README.
 */
import { useState, type CSSProperties } from "react";
import Image from "next/image";
import { REPORT_PAGES, THEMES } from "@/components/property-wizard/types";
import { DotGrid, Eyebrow, SectionTitle, useLandingTheme } from "./landing-primitives";

const WORDS = ["No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"];
const word = (n: number) => WORDS[n] ?? String(n);

const PAGE_SHADOW = "0 40px 80px -24px rgba(15,23,42,0.45), 0 0 0 1px rgba(15,23,42,0.06)";

/** One page of one template, as a button that turns to it. */
function Sheet({
  themeId,
  page,
  onClick,
  className,
  style,
}: {
  themeId: number;
  page: number;
  onClick: () => void;
  className: string;
  style?: CSSProperties;
}) {
  const p = REPORT_PAGES[page];
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={`Page ${page + 1}: ${p.name}`}
      className={`absolute cursor-pointer overflow-hidden rounded-md border-0 bg-white p-0 ${className}`}
      style={{ aspectRatio: "510 / 660", boxShadow: PAGE_SHADOW, ...style }}
    >
      <Image
        src={`/previews/pages/${themeId}/${p.id}.jpg`}
        alt=""
        width={510}
        height={660}
        sizes="(min-width: 640px) 476px, 300px"
        className="block h-full w-full"
      />
    </button>
  );
}

export function PropertyReports() {
  const { primary } = useLandingTheme();
  const [tpl, setTpl] = useState(0);
  const [page, setPage] = useState(0);
  const theme = THEMES[tpl];
  const n = REPORT_PAGES.length;
  const at = (i: number) => (page + i) % n;

  return (
    <section
      id="property-reports"
      className="relative flex flex-col gap-10 overflow-hidden border-t border-[#E6E8F0] bg-white pb-[88px] pt-16 md:pt-24"
    >
      <DotGrid from={theme.accentDefault} to={primary} focus="50% 55%" />

      <div className="relative mx-auto flex w-full max-w-[1200px] flex-wrap items-end justify-between gap-6 px-4 md:px-8">
        <div className="flex flex-col gap-3">
          <Eyebrow>Property reports &amp; CMAs</Eyebrow>
          <div className="max-w-[640px]">
            <SectionTitle>Type an address. Walk in with a seller report.</SectionTitle>
          </div>
          <p
            className="m-0 max-w-[560px] text-[19px] text-[#475569]"
            style={{ textWrap: "pretty" } as CSSProperties}
          >
            A {word(n).toLowerCase()}-page report on any home: the range of comparable sales, every
            sale behind it and the local market. {word(THEMES.length)} templates, in your colors,
            ready before the listing appointment.
          </p>
          <span className="text-[15px] font-semibold text-[#0F172A]" aria-live="polite">
            {theme.name} · {theme.style}
          </span>
        </div>

        <div className="flex flex-wrap gap-2" role="group" aria-label="Template">
          {THEMES.map((t, i) => {
            const on = i === tpl;
            return (
              <button
                key={t.id}
                type="button"
                aria-pressed={on}
                onClick={() => setTpl(i)}
                className="flex h-12 cursor-pointer items-center gap-2.5 whitespace-nowrap rounded-full border pl-4 pr-5 text-base font-bold"
                style={{
                  background: on ? "#0F172A" : "#fff",
                  color: on ? "#fff" : "#0F172A",
                  borderColor: on ? "#0F172A" : "#C9CEDF",
                }}
              >
                <span
                  aria-hidden
                  className="h-3.5 w-3.5 shrink-0 rounded-full"
                  style={{ background: t.accentDefault, boxShadow: "0 0 0 2px #fff" }}
                />
                {t.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* The stage: this page in front, the next two fanned behind it from 1080px. */}
      <div className="relative h-[460px] w-full sm:h-[680px]">
        <div
          aria-hidden
          className="pointer-events-none absolute left-1/2 top-1/2 h-[660px] max-h-full w-[min(980px,100%)] -translate-x-1/2 -translate-y-1/2 rounded-full"
          style={{
            background: `radial-gradient(closest-side, color-mix(in oklch, ${theme.accentDefault} 30%, transparent), transparent)`,
            transition: "background 0.4s",
          }}
        />
        <Sheet
          themeId={theme.id}
          page={at(1)}
          onClick={() => setPage(at(1))}
          className="top-[120px] z-[1] hidden w-[340px] min-[1080px]:block"
          style={{ left: "calc(50% - 510px)", transform: "rotate(-6deg)" }}
        />
        <Sheet
          themeId={theme.id}
          page={at(2)}
          onClick={() => setPage(at(2))}
          className="top-[120px] z-[1] hidden w-[340px] min-[1080px]:block"
          style={{ left: "calc(50% + 170px)", transform: "rotate(6deg)" }}
        />
        <Sheet
          themeId={theme.id}
          page={page}
          onClick={() => setPage(at(1))}
          className="left-1/2 top-8 z-[2] w-[300px] -translate-x-1/2 sm:w-[476px]"
        />
      </div>

      <div
        className="relative flex flex-wrap items-center justify-center gap-2 px-4 md:px-8"
        role="group"
        aria-label="Page"
      >
        {REPORT_PAGES.map((p, i) => {
          const on = i === page;
          return (
            <button
              key={p.id}
              type="button"
              aria-label={`Page ${i + 1}: ${p.name}`}
              aria-pressed={on}
              onClick={() => setPage(i)}
              className="h-11 w-11 cursor-pointer rounded-full border text-[15px] font-bold tabular-nums"
              style={{
                background: on ? "#0F172A" : "#fff",
                color: on ? "#fff" : "#0F172A",
                borderColor: on ? "#0F172A" : "#C9CEDF",
              }}
            >
              {i + 1}
            </button>
          );
        })}
      </div>
    </section>
  );
}

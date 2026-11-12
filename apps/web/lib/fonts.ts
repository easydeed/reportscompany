/**
 * Every web font the app uses, self-hosted.
 *
 * These were `next/font/google` imports, which fetch from fonts.googleapis.com
 * at BUILD time. On Vercel that fetch broke under Turbopack (Node 26, and then
 * on Node 22 for Plus Jakarta Sans), and every production build failed on it.
 * A build should not depend on a third-party host being reachable, so the
 * files now live in the repository (apps/web/fonts/) and load through
 * `next/font/local`.
 *
 * Same families, same weights, `display: swap`, and the same CSS variable for
 * Plus Jakarta Sans. Each file is byte-identical (SHA-256) to the `latin`
 * woff2 Google Fonts served for that family and weight on 2026-11-12, so the
 * glyphs cannot differ. Each family's licence (SIL OFL 1.1) is beside its files.
 */
import localFont from "next/font/local"

export const barlowCondensed = localFont({
  src: [
    { path: "../fonts/barlow-condensed/barlow-condensed-latin-600-normal.woff2", weight: "600", style: "normal" },
    { path: "../fonts/barlow-condensed/barlow-condensed-latin-700-normal.woff2", weight: "700", style: "normal" },
  ],
  display: "swap",
})

export const barlow = localFont({
  src: [
    { path: "../fonts/barlow/barlow-latin-400-normal.woff2", weight: "400", style: "normal" },
    { path: "../fonts/barlow/barlow-latin-500-normal.woff2", weight: "500", style: "normal" },
    { path: "../fonts/barlow/barlow-latin-600-normal.woff2", weight: "600", style: "normal" },
    { path: "../fonts/barlow/barlow-latin-700-normal.woff2", weight: "700", style: "normal" },
  ],
  display: "swap",
})

export const cormorant = localFont({
  src: [
    { path: "../fonts/cormorant-garamond/cormorant-garamond-latin-500-normal.woff2", weight: "500", style: "normal" },
    { path: "../fonts/cormorant-garamond/cormorant-garamond-latin-600-normal.woff2", weight: "600", style: "normal" },
  ],
  display: "swap",
  adjustFontFallback: "Times New Roman",
})

export const geist = localFont({
  src: [
    { path: "../fonts/geist/geist-latin-400-normal.woff2", weight: "400", style: "normal" },
    { path: "../fonts/geist/geist-latin-500-normal.woff2", weight: "500", style: "normal" },
    { path: "../fonts/geist/geist-latin-600-normal.woff2", weight: "600", style: "normal" },
    { path: "../fonts/geist/geist-latin-700-normal.woff2", weight: "700", style: "normal" },
  ],
  display: "swap",
})

export const manrope = localFont({
  src: [
    { path: "../fonts/manrope/manrope-latin-400-normal.woff2", weight: "400", style: "normal" },
    { path: "../fonts/manrope/manrope-latin-500-normal.woff2", weight: "500", style: "normal" },
    { path: "../fonts/manrope/manrope-latin-600-normal.woff2", weight: "600", style: "normal" },
    { path: "../fonts/manrope/manrope-latin-700-normal.woff2", weight: "700", style: "normal" },
    { path: "../fonts/manrope/manrope-latin-800-normal.woff2", weight: "800", style: "normal" },
  ],
  display: "swap",
})

export const plusJakarta = localFont({
  src: [
    { path: "../fonts/plus-jakarta-sans/plus-jakarta-sans-latin-400-normal.woff2", weight: "400", style: "normal" },
    { path: "../fonts/plus-jakarta-sans/plus-jakarta-sans-latin-500-normal.woff2", weight: "500", style: "normal" },
    { path: "../fonts/plus-jakarta-sans/plus-jakarta-sans-latin-600-normal.woff2", weight: "600", style: "normal" },
    { path: "../fonts/plus-jakarta-sans/plus-jakarta-sans-latin-700-normal.woff2", weight: "700", style: "normal" },
    { path: "../fonts/plus-jakarta-sans/plus-jakarta-sans-latin-800-normal.woff2", weight: "800", style: "normal" },
  ],
  variable: "--font-jakarta",
  display: "swap",
})

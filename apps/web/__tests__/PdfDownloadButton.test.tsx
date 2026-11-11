/**
 * LR-022: the homeowner's PDF button, rendered (Codex, #283).
 *
 * - Once ready, "Open your PDF report" points at the open route (which signs a
 *   new link on every open; see PdfOpen.route.test.ts), never at the signed
 *   URL the first request returned, which expires while the page stays open.
 * - Leaving the page cancels the request in flight.
 * - The cancel state survives an effect re-run: the button marks itself
 *   mounted in its effect's setup and unmounted in its cleanup, and the tests
 *   render it under StrictMode, which runs setup, cleanup, setup.
 */
import React from "react"
import fs from "fs"
import path from "path"
import { act, fireEvent, render, screen } from "@testing-library/react"
import { PdfDownloadButton } from "@/components/mobile-report/PdfDownloadButton"
import { DEADLINE_MS, PDF_COPY, pdfOpenHref } from "@/lib/pdf-download"

const SIGNED = "https://acct.r2.cloudflarestorage.com/market-reports/k.pdf?X-Amz-Expires=3600&X-Amz-Signature=s"
const VIEWER = fs.readFileSync(path.join(__dirname, "../components/mobile-report/MobileReportViewer.tsx"), "utf8")

function respond(body: Record<string, unknown>) {
  return jest.fn(async () => ({ json: async () => body }) as unknown as Response)
}

afterEach(() => jest.useRealTimers())

it("once ready, the link re-signs on every open instead of holding the first signed URL", async () => {
  const fetchFn = respond({ status: "ready", pdf_url: SIGNED })
  const openWindow = jest.fn()
  render(<React.StrictMode><PdfDownloadButton reportId="r1" fetchFn={fetchFn} openWindow={openWindow} /></React.StrictMode>)
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: /Download Full PDF Report/ })) })
  const link = screen.getByRole("link", { name: /Open your PDF report/ })
  expect(link.getAttribute("href")).toBe(pdfOpenHref("r1"))
  expect(link.getAttribute("href")).not.toContain("X-Amz")
  expect(openWindow).toHaveBeenCalledWith(SIGNED)
  expect(fetchFn).toHaveBeenCalledTimes(1)
  // An hour later the href is the same open route: nothing on the page has expired.
  fireEvent.click(link)
  expect(fetchFn).toHaveBeenCalledTimes(1)
})

it("the open link's route exists where the page points", () => {
  const route = path.join(__dirname, "../app", pdfOpenHref("[id]").replace(/^\//, ""), "route.ts")
  expect(fs.existsSync(route)).toBe(true)
})

it("leaving the page cancels the request in flight", async () => {
  const signals: AbortSignal[] = []
  const fetchFn = jest.fn((_: string, init?: RequestInit) => {
    if (init?.signal) signals.push(init.signal)
    return new Promise<Response>(() => {})
  })
  const { unmount } = render(<PdfDownloadButton reportId="r1" fetchFn={fetchFn} />)
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: /Download Full PDF Report/ })) })
  expect(screen.getByText(PDF_COPY.loading)).toBeTruthy()
  unmount()
  expect(signals[0].aborted).toBe(true)
})

it("a request that never answers ends at the deadline with Try again", async () => {
  jest.useFakeTimers()
  const fetchFn = jest.fn(() => new Promise<Response>(() => {}))
  render(<React.StrictMode><PdfDownloadButton reportId="r1" fetchFn={fetchFn} /></React.StrictMode>)
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: /Download Full PDF Report/ })) })
  await act(async () => { await jest.advanceTimersByTimeAsync(DEADLINE_MS) })
  expect(screen.getByRole("button", { name: /Try again/ })).toBeTruthy()
  expect(screen.getByText(PDF_COPY.expired)).toBeTruthy()
})

it("is what the viewer uses, with no polling of its own left in it", () => {
  expect(VIEWER).toMatch(/<PdfDownloadButton reportId=\{reportId\} \/>/)
  expect(VIEWER).not.toMatch(/requestPdf\(|setTimeout\(checkPdf|pdf_url/)
})

/**
 * LR-022 (D-380): the homeowner's "Download PDF" button.
 *
 * The page used to poll every second with no deadline: a report whose PDF had
 * failed spun forever, and nothing stopped the loop when the page closed.
 *
 * Now: one POST (which returns a freshly signed link for an existing PDF, or
 * queues ONE generation job), then a bounded poll of the status. Every way it
 * ends is a state the page can show with something the person can do.
 */

export type PdfStatus = "idle" | "loading" | "ready" | "failed" | "expired"

export interface PdfState {
  status: PdfStatus
  url?: string
  message?: string
}

export const POLL_MS = 2000
export const DEADLINE_MS = 90_000

export const PDF_COPY = {
  loading: "Preparing your PDF…",
  failed: "We couldn't prepare your PDF. Please try again in a minute.",
  expired: "Your PDF is taking longer than usual. Please try again in a minute.",
  offline: "We couldn't reach the server. Check your connection and try again.",
} as const

interface Deps {
  fetchFn: (input: string, init?: RequestInit) => Promise<Response>
  sleep: (ms: number) => Promise<void>
  now: () => number
  /** True once the page has gone away: stop without touching state. */
  cancelled: () => boolean
}

async function readStatus(res: Response): Promise<{ status?: string; pdf_url?: string; message?: string }> {
  try {
    return await res.json()
  } catch {
    return {}
  }
}

function settled(body: { status?: string; pdf_url?: string; message?: string }): PdfState | null {
  if (body.status === "ready" && body.pdf_url) return { status: "ready", url: body.pdf_url }
  if (body.status === "generating") return null
  // failed, missing, unavailable, rate_limited, or anything unexpected.
  return { status: "failed", message: body.message || PDF_COPY.failed }
}

/** Ask for the PDF and wait, within the deadline. Returns the final state, or null if cancelled. */
export async function requestPdf(reportId: string, deps: Deps): Promise<PdfState | null> {
  const base = `/api/proxy/v1/r/${reportId}/pdf`
  const started = deps.now()
  try {
    const first = settled(await readStatus(await deps.fetchFn(base, { method: "POST" })))
    if (deps.cancelled()) return null
    if (first) return first
    while (deps.now() - started < DEADLINE_MS) {
      await deps.sleep(POLL_MS)
      if (deps.cancelled()) return null
      // GET on the pdf proxy is the status check (D-314).
      const next = settled(await readStatus(await deps.fetchFn(base)))
      if (deps.cancelled()) return null
      if (next) return next
    }
    return { status: "expired", message: PDF_COPY.expired }
  } catch {
    if (deps.cancelled()) return null
    return { status: "failed", message: PDF_COPY.offline }
  }
}

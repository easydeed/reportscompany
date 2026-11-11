/**
 * LR-022 (D-380): the homeowner's "Download PDF" button.
 *
 * The page used to poll every second with no deadline: a report whose PDF had
 * failed spun forever, and nothing stopped the loop when the page closed.
 *
 * Now: one POST (which returns a freshly signed link for an existing PDF, or
 * queues ONE generation job), then a bounded poll of the status. Every way it
 * ends is a state the page can show with something the person can do.
 *
 * The deadline bounds the WHOLE operation, including a request or a response
 * body that never arrives (Codex, #283): every wait races one AbortController,
 * which the deadline or the page going away aborts, and the abort is passed to
 * fetch so the request itself is cancelled too.
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

/** Where "Open your PDF report" goes: the server signs a new link on every open. */
export const pdfOpenHref = (reportId: string) => `/api/proxy/v1/r/${reportId}/pdf/open`

export interface PdfRequestOptions {
  fetchFn?: (input: string, init?: RequestInit) => Promise<Response>
  /** Aborted when the page goes away: stop at once, settle to null, cancel the request. */
  signal?: AbortSignal
  pollMs?: number
  deadlineMs?: number
}

type Body = { status?: string; pdf_url?: string; message?: string }

async function readStatus(res: Response): Promise<Body> {
  try {
    return await res.json()
  } catch {
    return {}
  }
}

function settled(body: Body): PdfState | null {
  if (body.status === "ready" && body.pdf_url) return { status: "ready", url: body.pdf_url }
  if (body.status === "generating") return null
  // failed, missing, unavailable, rate_limited, or anything unexpected.
  return { status: "failed", message: body.message || PDF_COPY.failed }
}

/** Ask for the PDF and wait, within the deadline. Returns the final state, or null if cancelled. */
export async function requestPdf(reportId: string, opts: PdfRequestOptions = {}): Promise<PdfState | null> {
  const fetchFn = opts.fetchFn ?? ((input, init) => fetch(input, init))
  const pollMs = opts.pollMs ?? POLL_MS
  const base = `/api/proxy/v1/r/${reportId}/pdf`

  const run = new AbortController()
  let ended: "deadline" | "cancelled" | null = null
  const stop = (why: "deadline" | "cancelled") => {
    if (ended) return
    ended = why
    run.abort()
  }
  const halted = new Promise<never>((_, reject) => {
    run.signal.addEventListener("abort", () => reject(new Error("halted")))
  })
  halted.catch(() => {})
  const within = <T,>(p: Promise<T>): Promise<T> => Promise.race([p, halted])

  const deadline = setTimeout(() => stop("deadline"), opts.deadlineMs ?? DEADLINE_MS)
  const onCancel = () => stop("cancelled")
  if (opts.signal?.aborted) onCancel()
  else opts.signal?.addEventListener("abort", onCancel)

  // GET on the pdf proxy is the status check (D-314); it never queues anything.
  const ask = async (init?: RequestInit) =>
    settled(await within(readStatus(await within(fetchFn(base, { ...init, signal: run.signal })))))

  try {
    if (ended) throw new Error("halted")
    const first = await ask({ method: "POST" })
    if (first) return first
    for (;;) {
      await within(new Promise((resolve) => setTimeout(resolve, pollMs)))
      const next = await ask()
      if (next) return next
    }
  } catch {
    if (ended === "cancelled") return null
    if (ended === "deadline") return { status: "expired", message: PDF_COPY.expired }
    return { status: "failed", message: PDF_COPY.offline }
  } finally {
    clearTimeout(deadline)
    opts.signal?.removeEventListener("abort", onCancel)
  }
}

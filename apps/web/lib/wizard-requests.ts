/**
 * LR-024 (D-382, D-330, D-329): what the report wizard does with each answer.
 *
 * - A submit's outcome is classified once, the same for "Generate" and
 *   "Create Schedule", so a schedule failure is no longer silent (D-330).
 * - The plan-limit numbers are read from `detail`, where the API puts them
 *   (D-329).
 * - One Idempotency-Key per payload: a retry after a lost response or a 5xx
 *   replays the request instead of creating a second report or schedule; an
 *   edit, or a success, starts a new one.
 * - A safe retry is promised only when the API says it honours keys
 *   (`capabilities.idempotent_create` on /v1/account) and the key was first
 *   sent 0–6 days ago; the server replays for 7. Otherwise the page says it
 *   can't tell, and a new request is an explicit choice (design rev 2).
 * - The report-status wait is bounded and every way it ends is a state the
 *   page can show (D-382): ready, failed, slow, can't check, session expired,
 *   not found. One AbortController stops it on unmount and on retry.
 */
import { readVerificationRefusal, type VerificationRefusal } from "@/lib/verification"

export type SubmitOutcome =
  | { kind: "created"; body: Record<string, unknown> }
  | { kind: "verification"; refusal: VerificationRefusal }
  | { kind: "limit"; title: string; detail: string }
  | { kind: "invalid"; message: string }
  | { kind: "session_expired" }
  | { kind: "server_error" }
  | { kind: "offline" }
  // 410s from the key's replay (design rev 2): the key is past its window, or
  // what it created has since been deleted. Neither creates anything.
  | { kind: "key_expired" }
  | { kind: "gone" }

export type ReportOutcome =
  | { kind: "complete"; pdfUrl: string | null }
  | { kind: "failed" }
  | { kind: "slow" }
  | { kind: "unreachable" }
  | { kind: "session_expired" }
  | { kind: "not_found" }

export type Product = "market_reports" | "schedules"

const PRODUCT_LABELS: Record<string, string> = {
  market_reports: "Market Report",
  schedules: "Schedule",
  property_reports: "Property Report",
}

type Json = Record<string, unknown>

/** FastAPI's HTTPException puts a dict under `detail`; older answers are flat. */
function refusalFields(body: Json): Json {
  const detail = body.detail
  return detail && typeof detail === "object" && !Array.isArray(detail) ? { ...body, ...(detail as Json) } : body
}

function messageFrom(body: Json): string | null {
  const fields = refusalFields(body)
  for (const value of [fields.message, body.detail, fields.error]) {
    if (typeof value === "string" && value.trim()) return value
  }
  // FastAPI validation errors: a list of {msg}.
  if (Array.isArray(body.detail)) {
    const msgs = body.detail.map((d) => (d && typeof d === "object" ? (d as Json).msg : null)).filter(Boolean)
    if (msgs.length) return msgs.join(" ")
  }
  return null
}

/** The limit card's title and line, from a 429 (D-329: the numbers live in `detail`). */
export function limitMessage(body: Json, fallback: Product): { title: string; detail: string } {
  const fields = refusalFields(body)
  const label = PRODUCT_LABELS[(fields.product as string) || fallback] || "Report"
  const used = typeof fields.used === "number" ? fields.used : null
  const limit = typeof fields.limit === "number" ? fields.limit : null
  const period = fallback === "market_reports" ? " this month" : ""
  const detail = used !== null && limit !== null
    ? `You've used ${used} of ${limit} ${label.toLowerCase()}s${period}.`
    : `You've reached your ${label.toLowerCase()} limit.`
  return { title: `${label} limit reached`, detail }
}

/** One answer from POST /v1/reports or /v1/schedules (or the error fetch threw). */
export async function classifySubmit(res: Response | null, product: Product): Promise<SubmitOutcome> {
  if (!res) return { kind: "offline" }
  const body: Json = await res.json().catch(() => ({}))
  if (res.ok) return { kind: "created", body }
  if (res.status === 401) return { kind: "session_expired" }
  // D-019: checked before the 429 branch; a 403 never carries limit fields.
  const refusal = readVerificationRefusal(body)
  if (refusal) return { kind: "verification", refusal }
  if (res.status === 429) return { kind: "limit", ...limitMessage(body, product) }
  if (res.status === 410) {
    const code = refusalFields(body).error
    if (code === "idempotent_resource_gone") return { kind: "gone" }
    if (code === "idempotency_key_expired") return { kind: "key_expired" }
  }
  if (res.status >= 500) return { kind: "server_error" }
  return { kind: "invalid", message: messageFrom(body) || "This request couldn't be accepted. Please check your choices." }
}

/** Outcomes after which the same request may safely be sent again with the same key. */
export const UNKNOWN_OUTCOME: ReadonlySet<SubmitOutcome["kind"]> = new Set(["offline", "server_error", "session_expired"])

/**
 * One key per payload. The same payload sent again (a retry) reuses its key,
 * so the API replays it; a different payload, or anything after `release`,
 * gets a new one.
 */
export const SAFE_RETRY_MAX_AGE_MS = 6 * 24 * 60 * 60 * 1000

/** The API honours Idempotency-Key (rev 2). An older API omits the flag. */
export function idempotencyCapable(account: unknown): boolean {
  const caps = account && typeof account === "object" ? (account as Json).capabilities : null
  return !!caps && typeof caps === "object" && (caps as Json).idempotent_create === true
}

export class IdempotencyKeys {
  private current: { payload: string; key: string; firstSentAt: number } | null = null
  constructor(private readonly make: () => string = newKey, private readonly clock: () => number = Date.now) {}

  keyFor(payload: string): string {
    if (!this.current || this.current.payload !== payload) {
      this.current = { payload, key: this.make(), firstSentAt: this.clock() }
    }
    return this.current.key
  }

  /**
   * May the page promise that sending the current key again cannot create a
   * second one? Only if the API honours keys and the key is 0–6 days old by
   * the wall clock; a clock that went backwards counts as unknown.
   */
  retryIsSafe(capable: boolean): boolean {
    if (!capable || !this.current) return false
    const age = this.clock() - this.current.firstSentAt
    return age >= 0 && age <= SAFE_RETRY_MAX_AGE_MS
  }

  /** After a success, once the request's resource exists, or on an explicit new request. */
  release() {
    this.current = null
  }
}

function newKey(): string {
  const c = typeof globalThis !== "undefined" ? globalThis.crypto : undefined
  if (c && typeof c.randomUUID === "function") return c.randomUUID()
  // Older browsers: 32 hex characters from getRandomValues.
  const bytes = new Uint8Array(16)
  c?.getRandomValues(bytes)
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("")
}

export const STATUS_INTERVAL_MS = 3000
export const SLOW_AFTER_MS = 120_000
export const MAX_STATUS_ERRORS = 3

export interface WatchOptions {
  fetchFn?: (input: string, init?: RequestInit) => Promise<Response>
  signal?: AbortSignal
  intervalMs?: number
  slowAfterMs?: number
  maxErrors?: number
}

/**
 * Watch a report until it settles, for at most `slowAfterMs`. Returns null if
 * the signal aborts (the page went away, or a retry started).
 */
export async function watchReport(reportId: string, opts: WatchOptions = {}): Promise<ReportOutcome | null> {
  const fetchFn = opts.fetchFn ?? ((input, init) => fetch(input, init))
  const intervalMs = opts.intervalMs ?? STATUS_INTERVAL_MS
  const maxErrors = opts.maxErrors ?? MAX_STATUS_ERRORS
  const run = new AbortController()
  let ended: "slow" | "cancelled" | null = null
  const stop = (why: "slow" | "cancelled") => {
    if (ended) return
    ended = why
    run.abort()
  }
  const halted = new Promise<never>((_, reject) => {
    run.signal.addEventListener("abort", () => reject(new Error("halted")))
  })
  halted.catch(() => {})
  const within = <T,>(p: Promise<T>): Promise<T> => Promise.race([p, halted])
  const deadline = setTimeout(() => stop("slow"), opts.slowAfterMs ?? SLOW_AFTER_MS)
  const onCancel = () => stop("cancelled")
  if (opts.signal?.aborted) onCancel()
  else opts.signal?.addEventListener("abort", onCancel)

  let errors = 0
  try {
    if (ended) throw new Error("halted")
    for (;;) {
      await within(new Promise((resolve) => setTimeout(resolve, intervalMs)))
      let res: Response
      try {
        res = await within(fetchFn(`/api/proxy/v1/reports/${encodeURIComponent(reportId)}`, { signal: run.signal, cache: "no-store" }))
      } catch (e) {
        if (ended) throw e
        if (++errors >= maxErrors) return { kind: "unreachable" }
        continue
      }
      if (res.status === 401) return { kind: "session_expired" }
      if (res.status === 404) return { kind: "not_found" }
      if (!res.ok) {
        if (++errors >= maxErrors) return { kind: "unreachable" }
        continue
      }
      const data: Json = await within(res.json().catch(() => ({})))
      errors = 0
      if (data.status === "completed" || data.status === "complete") {
        return { kind: "complete", pdfUrl: typeof data.pdf_url === "string" ? data.pdf_url : null }
      }
      if (data.status === "failed") return { kind: "failed" }
    }
  } catch {
    if (ended === "slow") return { kind: "slow" }
    return null
  } finally {
    clearTimeout(deadline)
    opts.signal?.removeEventListener("abort", onCancel)
  }
}

/** What each problem says and offers. Copy only; the component wires the actions. */
export type ProblemKind =
  | "offline" | "server_error" | "session_expired" | "invalid" | "unknown" | "gone"
  | "failed" | "slow" | "unreachable" | "status_session_expired" | "not_found"

export type ProblemAction =
  | "retry_submit" | "edit" | "sign_in" | "keep_waiting" | "check_again" | "go_reports" | "new_report"
  | "go_list" | "send_new"

export const PROBLEMS: Record<ProblemKind, { title: string; sub: string; actions: ProblemAction[] }> = {
  offline: {
    title: "We couldn't reach the server",
    sub: "Check your connection and try again. Your choices are kept.",
    actions: ["edit", "retry_submit"],
  },
  server_error: {
    title: "Something went wrong on our side",
    sub: "Please try again. Trying again won't create a second one.",
    actions: ["edit", "retry_submit"],
  },
  session_expired: {
    title: "Your session has expired",
    sub: "Sign in again in a new tab, then come back and try again. Your choices are kept.",
    actions: ["sign_in", "retry_submit"],
  },
  invalid: {
    title: "This couldn't be accepted",
    sub: "",
    actions: ["edit"],
  },
  // Rev 2: an unknown outcome when a retry can't be promised safe (no API
  // capability, or the key is too old), or the server's 410 expired.
  unknown: {
    title: "We can't tell whether your earlier request went through",
    sub: "Check your list before sending it again: if it went through, it's there. If you were signed out, sign in again in a new tab first.",
    actions: ["go_list", "send_new"],
  },
  gone: {
    title: "It was created, then deleted",
    sub: "Your earlier request went through, and what it created has since been deleted. Nothing new was created.",
    actions: ["go_list", "send_new"],
  },
  failed: {
    title: "We couldn't generate this report",
    sub: "Something went wrong while building it. You can try again.",
    actions: ["edit", "new_report"],
  },
  slow: {
    title: "This is taking longer than usual",
    sub: "Your report is still being made. It will appear in Reports when it's ready.",
    actions: ["go_reports", "keep_waiting"],
  },
  unreachable: {
    title: "We can't check on your report right now",
    sub: "It's still being made and will appear in Reports when it's ready.",
    actions: ["go_reports", "check_again"],
  },
  status_session_expired: {
    title: "Your session has expired",
    sub: "Sign in again in a new tab, then check again. Your report is still being made.",
    actions: ["sign_in", "check_again"],
  },
  not_found: {
    title: "We can't find this report",
    sub: "It may have been removed. Your other reports are in Reports.",
    actions: ["go_reports"],
  },
}

export const ACTION_LABELS: Record<ProblemAction, string> = {
  retry_submit: "Try again",
  edit: "Back to edit",
  sign_in: "Sign in",
  keep_waiting: "Keep waiting",
  check_again: "Check again",
  go_reports: "Go to Reports",
  new_report: "Try again",
  go_list: "Go to Reports",
  send_new: "Send as a new request",
}

/**
 * D-019 — reading the "confirm your email first" refusal off any API response.
 *
 * The backend refuses a send with 403 and a structured body:
 *
 *   { "detail": { "error": "email_not_verified",
 *                 "message": "Confirm you@example.com before you send this report. …",
 *                 "action": "send this report",
 *                 "email": "you@example.com",
 *                 "resend_endpoint": "/v1/auth/resend-verification" } }
 *
 * Switch on `error`, never on the prose. The message is written for a person
 * and will be reworded; the code is the contract.
 *
 * `detail` is where FastAPI puts an HTTPException body, and the Next proxy
 * routes pass it through untouched along with the status. The unwrapping here
 * tolerates both shapes anyway, because not every proxy in this app is
 * guaranteed to keep doing that and a banner that silently stops appearing is
 * worse than one that is generous about where it looks.
 */

export const EMAIL_NOT_VERIFIED = "email_not_verified"

export type VerificationRefusal = {
  /** What they were trying to do, as a verb phrase: "send this report". */
  action: string
  /** Ready-to-show sentence from the API. */
  message: string
  /** The address to offer a new link for. May be absent. */
  email: string | null
}

/**
 * Returns the refusal if this response body is one, otherwise null.
 *
 * Takes the parsed body rather than the Response so it can be used after a
 * `res.json().catch(() => ({}))`, which is how every call site in this app
 * already reads error bodies.
 */
export function readVerificationRefusal(body: unknown): VerificationRefusal | null {
  if (!body || typeof body !== "object") return null
  const outer = body as Record<string, unknown>
  const candidates = [outer.detail, outer]
  for (const candidate of candidates) {
    if (!candidate || typeof candidate !== "object") continue
    const d = candidate as Record<string, unknown>
    if (d.error !== EMAIL_NOT_VERIFIED) continue
    return {
      action: typeof d.action === "string" ? d.action : "do this",
      message:
        typeof d.message === "string" && d.message
          ? d.message
          : "Confirm your email address before you send.",
      email: typeof d.email === "string" && d.email ? d.email : null,
    }
  }
  return null
}

/**
 * Ask for another verification link.
 *
 * Resolves to true when the request was accepted. The endpoint is deliberately
 * non-committal about whether the address is registered (auth.py:936), so a
 * `true` here means "we asked", not "a mail is on its way" — the UI wording
 * needs to match that and not promise delivery.
 */
export async function requestVerificationEmail(email: string): Promise<boolean> {
  try {
    const res = await fetch("/api/proxy/v1/auth/resend-verification", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    })
    return res.ok
  } catch {
    return false
  }
}

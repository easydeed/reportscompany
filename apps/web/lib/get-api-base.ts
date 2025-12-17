/**
 * Returns a safe API base URL for server + edge runtime.
 *
 * Handles these common misconfigs:
 * - missing env var → default to Render API
 * - env var set without scheme (e.g. "reportscompany.onrender.com") → prepend https://
 * - trailing slash → removed
 */
export function getApiBase() {
  let base = (process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com").trim()

  // If someone configured without scheme, make it a valid absolute URL.
  if (!/^https?:\/\//i.test(base)) {
    base = `https://${base}`
  }

  // Strip trailing slashes to avoid double-slash URLs.
  base = base.replace(/\/+$/, "")

  return base
}


/**
 * API Base URL - used for server-side calls only.
 * Client-side calls go through the proxy to avoid CORS.
 */
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

/**
 * Determines if code is running in browser (client-side).
 */
function isBrowser(): boolean {
  return typeof window !== 'undefined';
}

/**
 * Client-side API fetch utility.
 * 
 * Routes all requests through Next.js proxy routes to avoid CORS issues.
 * The proxy routes forward requests to the actual API server-side.
 * 
 * Path format: /v1/reports -> /api/proxy/v1/reports (browser)
 *              /v1/reports -> {API_BASE}/v1/reports (server)
 */
export async function apiFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  
  // In browser: use proxy routes to avoid CORS
  // On server: call API directly
  const url = isBrowser() 
    ? `/api/proxy${path}`  // Browser: /api/proxy/v1/reports
    : `${API_BASE}${path}`; // Server: https://api.../v1/reports

  let lastErr: any = null;
  for (let i = 0; i < 3; i++) {
    try {
      const res = await fetch(url, { 
        ...init, 
        headers, 
        credentials: 'include', // Send cookies for authentication
        cache: "no-store" 
      });
      if (!res.ok) {
        const t = await res.text().catch(() => "");
        throw new Error(`API ${res.status} ${res.statusText}: ${t}`);
      }
      return res.json();
    } catch (e: any) {
      lastErr = e;
      // transient network errors often say "fetch failed" or contain ECONNREFUSED
      const msg = String(e?.message || "");
      const code = (e as any)?.cause?.code || "";
      if (msg.includes("fetch failed") || code === "ECONNREFUSED") {
        await sleep(250 * (i + 1)); // 250ms, 500ms, 750ms
        continue;
      }
      throw e;
    }
  }
  throw lastErr;
}


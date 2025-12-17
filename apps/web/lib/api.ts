export const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

/**
 * Client-side API fetch utility.
 * 
 * IMPORTANT: Always includes credentials to send auth cookies (mr_token).
 * Do NOT use X-Demo-Account header in production - it bypasses real auth.
 */
export async function apiFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  
  const url = `${API_BASE}${path}`;

  let lastErr: any = null;
  for (let i = 0; i < 3; i++) {
    try {
      const res = await fetch(url, { 
        ...init, 
        headers, 
        credentials: 'include', // CRITICAL: Send cookies for authentication
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


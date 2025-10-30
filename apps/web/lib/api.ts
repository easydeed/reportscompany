export const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;
export const DEMO_ACC = process.env.NEXT_PUBLIC_DEMO_ACCOUNT_ID!;

export async function apiFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (DEMO_ACC) headers.set("X-Demo-Account", DEMO_ACC);
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers, cache: "no-store" });
  if (!res.ok) {
    const t = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${res.statusText}: ${t}`);
  }
  return res.json();
}


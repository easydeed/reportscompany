import { NextRequest, NextResponse } from "next/server";
import { getApiBase } from "@/lib/get-api-base";
import { publicLookupVisitor } from "@/lib/public-lookup-visitor";

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ code: string }> }
) {
  const resolvedParams = await params;
  const body = await req.json();
  const API_BASE = getApiBase();

  const path = `/v1/cma/${encodeURIComponent(resolvedParams.code)}/search`;
  const visitor = publicLookupVisitor(req, path);
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: visitor.headers,
    redirect: visitor.headers.has("X-TR-Proxy-Sig") ? "error" : "follow",
    body: JSON.stringify(body),
  });

  const data = await res.json().catch(() => ({}));
  const response = NextResponse.json(data, { status: res.status });
  for (const name of ["Retry-After", "RateLimit-Limit", "RateLimit-Remaining", "RateLimit-Reset"]) {
    const value = res.headers.get(name);
    if (value !== null) response.headers.set(name, value);
  }
  if (visitor.newCookie) {
    response.cookies.set("tr_v", visitor.newCookie, {
      httpOnly: true, secure: true, sameSite: "lax", path: "/", maxAge: 30 * 24 * 60 * 60,
    });
    response.headers.set("Cache-Control", "private, no-store");
  }
  return response;
}


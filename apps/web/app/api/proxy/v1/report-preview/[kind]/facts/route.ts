import { NextResponse } from "next/server";
import { getApiBase } from "@/lib/get-api-base";

// The landing page's Snapshot figures. Public on the API; proxied because the
// browser does not call the API's origin for data (CORS), only frames its pages.
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ kind: string }> }
) {
  const { kind } = await params;
  const res = await fetch(`${getApiBase()}/v1/report-preview/${encodeURIComponent(kind)}/facts`, {
    next: { revalidate: 3600 },
  });
  const data = await res.json().catch(() => ({}));
  return NextResponse.json(data, { status: res.status });
}

import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com";

/**
 * POST /api/proxy/v1/upload/branding/{assetType}/import
 *
 * LR-007: import a pasted image link. The API fetches it through a guarded
 * fetcher, checks and re-encodes it like an upload, and returns OUR copy's URL.
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ assetType: string }> }
) {
  const { assetType } = await params;
  const cookieStore = await cookies();
  const token = cookieStore.get("mr_token")?.value;

  if (!token) {
    return NextResponse.json(
      { error: "Unauthorized", detail: "Please log in to import images" },
      { status: 401 }
    );
  }
  if (!["logo", "headshot"].includes(assetType)) {
    return NextResponse.json(
      { error: "Invalid asset type", detail: "asset_type must be 'logo' or 'headshot'" },
      { status: 400 }
    );
  }

  try {
    const body = await request.json();
    const response = await fetch(`${API_BASE}/v1/upload/branding/${assetType}/import`, {
      method: "POST",
      headers: { Cookie: `mr_token=${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ url: typeof body?.url === "string" ? body.url : "" }),
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("[Upload Proxy] Import error:", error);
    return NextResponse.json({ error: "Import failed", detail: "The image couldn't be imported" }, { status: 500 });
  }
}

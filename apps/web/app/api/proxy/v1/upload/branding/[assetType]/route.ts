import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com";

/**
 * POST /api/proxy/v1/upload/branding/{assetType}
 * 
 * Proxy for uploading branding assets (logo, headshot).
 * Forwards multipart/form-data to the backend API.
 * 
 * Pass B1.5: Frontend Proxy Route
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
      { error: "Unauthorized", detail: "Please log in to upload files" },
      { status: 401 }
    );
  }

  // Validate asset type
  if (!["logo", "headshot"].includes(assetType)) {
    return NextResponse.json(
      { error: "Invalid asset type", detail: "asset_type must be 'logo' or 'headshot'" },
      { status: 400 }
    );
  }

  try {
    // Get the form data from the request
    const formData = await request.formData();

    // Forward to backend API
    const response = await fetch(`${API_BASE}/v1/upload/branding/${assetType}`, {
      method: "POST",
      headers: {
        Cookie: `mr_token=${token}`,
      },
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      console.error(`[Upload Proxy] Backend error: ${response.status}`, data);
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error("[Upload Proxy] Error:", error);
    return NextResponse.json(
      { error: "Upload failed", detail: String(error) },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/proxy/v1/upload/branding/{assetType}
 * 
 * Proxy for deleting branding assets.
 * Note: assetType is ignored for delete, URL is passed in query params.
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ assetType: string }> }
) {
  const cookieStore = await cookies();
  const token = cookieStore.get("mr_token")?.value;

  if (!token) {
    return NextResponse.json(
      { error: "Unauthorized", detail: "Please log in to delete files" },
      { status: 401 }
    );
  }

  try {
    const { searchParams } = new URL(request.url);
    const url = searchParams.get("url");

    if (!url) {
      return NextResponse.json(
        { error: "Missing URL", detail: "url query parameter is required" },
        { status: 400 }
      );
    }

    const response = await fetch(`${API_BASE}/v1/upload/branding?url=${encodeURIComponent(url)}`, {
      method: "DELETE",
      headers: {
        Cookie: `mr_token=${token}`,
      },
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("[Upload Proxy] Delete error:", error);
    return NextResponse.json(
      { error: "Delete failed", detail: String(error) },
      { status: 500 }
    );
  }
}


import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com";

/**
 * POST /api/proxy/v1/branding/sample-jpg
 * 
 * Proxy for generating sample branded social media image (1080x1920 JPG).
 * Returns JPG as blob for download.
 * 
 * Perfect for Instagram Stories, TikTok, LinkedIn Stories.
 */
export async function POST(request: NextRequest) {
  const cookieStore = await cookies();
  const token = cookieStore.get("mr_token")?.value;

  if (!token) {
    return NextResponse.json(
      { error: "Unauthorized", detail: "Please log in" },
      { status: 401 }
    );
  }

  try {
    const body = await request.json();

    const response = await fetch(`${API_BASE}/v1/branding/sample-jpg`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Cookie: `mr_token=${token}`,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error(`[Sample JPG Proxy] Backend error: ${response.status}`, errorData);
      return NextResponse.json(
        { error: errorData.detail || "Failed to generate image" },
        { status: response.status }
      );
    }

    // Get the JPG blob
    const jpgBlob = await response.blob();
    const contentDisposition = response.headers.get("content-disposition") || 'attachment; filename="sample-social.jpg"';

    // Return the JPG
    return new NextResponse(jpgBlob, {
      status: 200,
      headers: {
        "Content-Type": "image/jpeg",
        "Content-Disposition": contentDisposition,
      },
    });
  } catch (error) {
    console.error("[Sample JPG Proxy] Error:", error);
    return NextResponse.json(
      { error: "Image generation failed", detail: String(error) },
      { status: 500 }
    );
  }
}


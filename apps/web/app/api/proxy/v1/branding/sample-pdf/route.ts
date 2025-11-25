import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com";

/**
 * POST /api/proxy/v1/branding/sample-pdf
 * 
 * Proxy for generating sample branded PDF.
 * Returns PDF as blob for download.
 * 
 * Pass B4.1: Sample PDF Proxy
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

    const response = await fetch(`${API_BASE}/v1/branding/sample-pdf`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Cookie: `mr_token=${token}`,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error(`[Sample PDF Proxy] Backend error: ${response.status}`, errorData);
      return NextResponse.json(
        { error: errorData.detail || "Failed to generate PDF" },
        { status: response.status }
      );
    }

    // Get the PDF blob
    const pdfBlob = await response.blob();
    const contentDisposition = response.headers.get("content-disposition") || 'attachment; filename="sample-report.pdf"';

    // Return the PDF
    return new NextResponse(pdfBlob, {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": contentDisposition,
      },
    });
  } catch (error) {
    console.error("[Sample PDF Proxy] Error:", error);
    return NextResponse.json(
      { error: "PDF generation failed", detail: String(error) },
      { status: 500 }
    );
  }
}


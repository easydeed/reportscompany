import { NextResponse } from "next/server"
import { cookies } from "next/headers"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE

// Generic handler for all admin metrics endpoints
async function handleAdminMetricsRequest(
  request: Request,
  endpoint: string
) {
  const cookieStore = await cookies()
  const token = cookieStore.get("mr_token")?.value

  if (!token) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 })
  }

  // Forward query parameters
  const { searchParams } = new URL(request.url)
  const queryString = searchParams.toString()
  const url = `${API_BASE}/v1/admin/metrics/${endpoint}${queryString ? `?${queryString}` : ''}`

  try {
    const response = await fetch(url, {
      headers: {
        Cookie: `mr_token=${token}`,
      },
    })

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error(`Admin metrics proxy error (${endpoint}):`, error)
    return NextResponse.json(
      { error: `Failed to fetch ${endpoint}` },
      { status: 500 }
    )
  }
}

// This route handles the base /admin/metrics endpoint
// For subpaths like /overview, /daily, etc., we use [...path] route
export async function GET(request: Request) {
  // Get the path after /metrics from the URL
  const url = new URL(request.url)
  const fullPath = url.pathname
  const metricsPath = fullPath.replace('/api/proxy/v1/admin/metrics', '')
  const endpoint = metricsPath.replace(/^\//, '') // Remove leading slash
  
  if (!endpoint) {
    return NextResponse.json({ error: "Endpoint required" }, { status: 400 })
  }
  
  return handleAdminMetricsRequest(request, endpoint)
}


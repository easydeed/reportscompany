import { NextRequest, NextResponse } from "next/server"
import { cookies } from "next/headers"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ accountId: string }> }
) {
  const { accountId } = await context.params
  const cookieStore = await cookies()
  const token = cookieStore.get("mr_token")

  const res = await fetch(
    `${API_URL}/v1/affiliate/accounts/${accountId}/unsponsor`,
    {
      method: "POST",
      headers: {
        Cookie: `mr_token=${token?.value || ""}`,
      },
    }
  )

  const data = await res.json()

  return NextResponse.json(data, { status: res.status })
}


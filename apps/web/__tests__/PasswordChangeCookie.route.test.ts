/** @jest-environment node */
import { NextRequest } from "next/server"
import { POST } from "@/app/api/proxy/v1/users/me/password/route"

it("forwards the replacement session cookie to the initiating browser", async () => {
  const cookie = "mr_token=replacement; Path=/; HttpOnly; Secure; SameSite=Lax"
  const upstream = jest.spyOn(global, "fetch").mockResolvedValue(new Response("{}", {
    status: 200, headers: { "Set-Cookie": cookie, "Content-Type": "application/json" },
  }))
  try {
    const response = await POST(new NextRequest("https://example.test/api/proxy/v1/users/me/password", {
      method: "POST", headers: { cookie: "mr_token=previous", "Content-Type": "application/json" },
      body: JSON.stringify({ current_password: "old-test-password", new_password: "new-test-password" }),
    }))
    expect(upstream.mock.calls[0][1]?.headers).toEqual(expect.objectContaining({ cookie: "mr_token=previous" }))
    expect(response.status).toBe(200)
    expect(response.headers.get("set-cookie")).toBe(cookie)
  } finally {
    upstream.mockRestore()
  }
})

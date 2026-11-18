/** @jest-environment node */
import { NextRequest } from "next/server"
import { POST } from "@/app/api/proxy/v1/contacts/import/route"

it("forwards a readable upload, cookie and upstream validation response", async () => {
  const bytes = new Uint8Array([0xef, 0xbb, 0xbf, ...new TextEncoder().encode("name,email\r\nPat,pat@example.test")])
  const form = new FormData()
  form.append("file", new Blob([bytes], { type: "text/csv" }), "contacts.csv")
  const spy = jest.spyOn(global, "fetch").mockImplementation(async (url, init) => {
    const forwarded = new Request(url, init)
    expect(forwarded.headers.get("cookie")).toBe("mr_token=test")
    const file = (await forwarded.formData()).get("file") as File
    expect(file.name).toBe("contacts.csv")
    expect(new Uint8Array(await file.arrayBuffer())).toEqual(bytes)
    return Response.json({ detail: "validation response" }, { status: 422 })
  })
  try {
    const req = new NextRequest("https://example.test/api/proxy/v1/contacts/import", {
      method: "POST", body: form, headers: { cookie: "mr_token=test" },
    })
    const response = await POST(req)
    expect(response.status).toBe(422)
    expect(await response.json()).toEqual({ detail: "validation response" })
  } finally {
    spy.mockRestore()
  }
})
